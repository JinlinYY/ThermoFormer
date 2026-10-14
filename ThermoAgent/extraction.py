"""Three-component crossflow material balances for SI Section S7.4.

Internal component order is heptane, furfural, benzene (H, S, B).
Model endpoints are tabulated at their own feeds; they are never borrowed
from the experimental reference or extrapolated to a different feed.
"""

from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq

Array = NDArray[np.float64]
FEED = np.array([11 / 15, 0.0, 4 / 15])
SOLVENT = np.array([0.0, 1.0, 0.0])


def composition(values: Any) -> Array:
    """Validate a three-component mole-fraction vector without renormalizing."""
    x = np.asarray(values, dtype=float)
    if x.shape != (3,) or not np.isfinite(x).all() or np.any(x < 0):
        raise ValueError("Invalid three-component composition")
    if abs(x.sum() - 1) > 1e-8:
        raise ValueError("Composition does not sum to unity")
    return x


def lever_rule(z: Array, extract: Array, raffinate: Array) -> float:
    """Return extract fraction; check all three component balances."""
    z, extract, raffinate = [composition(v) for v in (z, extract, raffinate)]
    direction = extract - raffinate
    if direction @ direction < 1e-12:
        raise ValueError("Degenerate tie line")
    beta = float((z - raffinate) @ direction / (direction @ direction))
    if not 0 < beta < 1:
        raise ValueError("Feed is outside the two-phase segment")
    if np.max(abs(z - beta * extract - (1 - beta) * raffinate)) > 1e-8:
        raise ValueError("Three-component lever-rule balance does not close")
    return beta


def experimental_split(
    pairs: Array, z: Array, method: str = "linear"
) -> tuple[Array, Array]:
    """Interpolate measured endpoints, restricted to their measured interval."""
    z = composition(z)
    candidates: list[tuple[Array, Array]] = []

    def cross(a, b):
        return float(a[0] * b[1] - a[1] * b[0])

    if method == "linear":
        pairs = pairs[np.argsort(pairs[:, 0, 2])]
        for first, last in zip(pairs[:-1], pairs[1:]):
            a, b = first
            da, db = last - first
            d, dd, v = a - b, da - db, z - b
            poly = np.trim_zeros(
                [-cross(db, dd), cross(v, dd) - cross(db, d), cross(v, d)], "f"
            )
            for root in np.roots(poly):
                if abs(root.imag) > 1e-9 or not -1e-9 <= root.real <= 1 + 1e-9:
                    continue
                t = np.clip(root.real, 0, 1)
                ends = (1 - t) * first + t * last
                try:
                    lever_rule(z, *ends)
                    candidates.append((ends[0], ends[1]))
                except ValueError:
                    continue
    elif method == "pchip":
        pairs = pairs[np.argsort(pairs[:, 1, 2])]
        q = pairs[:, 1, 2]
        curves = [
            PchipInterpolator(q, pairs[:, i, k], extrapolate=False)
            for i, k in [(0, 0), (0, 2), (1, 0)]
        ]

        def endpoints(v: float) -> tuple[Array, Array]:
            eh, eb, rh = [float(f(v)) for f in curves]
            return np.array([eh, 1 - eh - eb, eb]), np.array([rh, 1 - rh - v, v])

        def residual(v: float) -> float:
            a, b = endpoints(v)
            return cross(z - b, a - b)

        grid = np.unique(np.r_[np.linspace(q[0], q[-1], 301), q])
        roots = [v for v in grid if abs(residual(v)) < 1e-13]
        for lo, hi in zip(grid[:-1], grid[1:]):
            if residual(lo) * residual(hi) < 0:
                roots.append(brentq(residual, lo, hi, xtol=1e-13))
        for root in roots:
            ends = endpoints(root)
            try:
                lever_rule(z, *ends)
                candidates.append(ends)
            except ValueError:
                continue
    else:
        raise ValueError("Interpolation must be linear or pchip")
    if not candidates:
        raise ValueError("Feed is outside measured tie-line interpolation coverage")
    if any(np.max(abs(np.asarray(c) - candidates[0])) > 1e-6 for c in candidates):
        raise ValueError("Nonunique experimental reference split")
    return candidates[0]


class RecordedEndpoints:
    """Exact-state lookup of archived model results, not a new LLE predictor."""

    def __init__(self, rows: Sequence[dict[str, Any]], model: str, temperature: float):
        self.rows = [
            r
            for r in rows
            if r["model"] == model and r["T"] == temperature and r["status"] == "valid"
        ]

    def __call__(self, z: Array) -> tuple[Array, Array]:
        matches = []
        for row in self.rows:
            feed = np.asarray(row.get("feed_component_flows", FEED))
            inlet = feed + row["S"] * SOLVENT
            if np.max(abs(inlet / inlet.sum() - z)) < 2e-8:
                matches.append((np.asarray(row["xE"]), np.asarray(row["xR"])))
        if not matches:
            raise ValueError(
                "No archived model endpoints for this feed; fresh inference is required"
            )
        if any(np.max(abs(np.asarray(v) - matches[0])) > 1e-6 for v in matches):
            raise ValueError("Inconsistent archived endpoints for the same feed")
        return matches[0]


def cascade(
    allocation: Sequence[float], split: Callable[[Array], tuple[Array, Array]]
) -> dict[str, Any]:
    """Propagate this equilibrium source's own full raffinate at each stage."""
    if not allocation or not np.isfinite(allocation).all() or min(allocation) <= 0:
        raise ValueError("Positive finite fresh-solvent flows are required")
    current, combined = FEED.copy(), np.zeros(3)
    stages = []
    for stage, solvent in enumerate(allocation, 1):
        inlet = current + solvent * SOLVENT
        total = float(inlet.sum())
        z = inlet / total
        xe, xr = split(z)
        beta = lever_rule(z, xe, xr)
        e, r = total * beta, total * (1 - beta)
        current = r * xr
        combined += e * xe
        stages.append(
            dict(
                stage=stage,
                S=solvent,
                z=z.tolist(),
                E=e,
                R=r,
                xE=xe.tolist(),
                xR=xr.tolist(),
                component_balance_error_mol_s=float(
                    np.max(abs(inlet - e * xe - current))
                ),
            )
        )
    error = float(np.max(abs(FEED + sum(allocation) * SOLVENT - current - combined)))
    if error > 1e-7:
        raise ValueError("Cascade material balance does not close")
    return dict(
        benzene_recovery=1 - current[2] / FEED[2],
        heptane_retention=current[0] / FEED[0],
        R_final=float(current.sum()),
        E_total=float(combined.sum()),
        R_final_x=(current / current.sum()).tolist(),
        E_combined_x=(combined / combined.sum()).tolist(),
        overall_component_balance_error=error,
        stages=stages,
    )
