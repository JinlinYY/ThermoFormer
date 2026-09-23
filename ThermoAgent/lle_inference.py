"""Fresh feed-specific LLE calculations for the published furfural study.

The ThermoFormer branch is conditional on the learned two-liquid domain.
Failure is not evidence of a single phase. Stability tests are finite-grid
and local numerical diagnostics, not global proofs over the simplex.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import least_squares, linprog, minimize
from scipy.special import expit, logit, softmax

from extraction import cascade, composition, lever_rule
from reproduce import ROOT, check_close, load, verify_manifest, write


def branch_values(qgrid: Any, a: Any, b: Any, q: Any) -> tuple[Any, Any]:
    """Same Hermite center/log-gap interpolation as HybridBinodalLLE.well."""
    import torch

    query = torch.maximum(qgrid[:, :1], torch.minimum(q, qgrid[:, -1:]))
    index = torch.searchsorted(
        qgrid.contiguous(), query.contiguous(), right=True
    ).clamp(1, qgrid.shape[1] - 1)
    left = index - 1
    ql, qr = qgrid.gather(1, left), qgrid.gather(1, index)
    f = (query - ql) / (qr - ql).clamp_min(1e-12)

    def interpolate(values: Any) -> Any:
        slopes = torch.cat(
            [
                torch.zeros_like(values[:, :1]),
                (values[:, 2:] - values[:, :-2]) / (qgrid[:, 2:] - qgrid[:, :-2]),
                torch.zeros_like(values[:, :1]),
            ],
            1,
        )
        return (
            (2 * f**3 - 3 * f**2 + 1) * values.gather(1, left)
            + (f**3 - 2 * f**2 + f) * (qr - ql) * slopes.gather(1, left)
            + (-2 * f**3 + 3 * f**2) * values.gather(1, index)
            + (f**3 - f**2) * (qr - ql) * slopes.gather(1, index)
        )

    center = interpolate((a + b) / 2)
    gap = interpolate((b - a).clamp_min(1e-12).log()).exp()
    return center - gap / 2, center + gap / 2


class ThermoFormerSplit:
    """Compute endpoints from molecular representations and the feed's q coordinate."""

    def __init__(self, repository: Path):
        import torch
        from rdkit import Chem

        sys.path.insert(0, str(repository / "src"))
        from thermoformer.lle_tp.checkpoint_model_v2 import build_model
        from thermoformer.lle_tp.model import repeat_context
        from thermoformer.lle_tp.solver import simplex_grid

        provenance = load(ROOT / "provenance.json")["crossflow_extraction"]
        checkpoint = repository / provenance["checkpoint"]
        if (
            hashlib.sha256(checkpoint.read_bytes()).hexdigest()
            != provenance["checkpoint_sha256"]
        ):
            raise ValueError("Registered LLE checkpoint checksum mismatch")
        payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
        self.model = build_model(payload["spec"]).double()
        self.model.load_state_dict(payload["model"], strict=True)
        self.model.eval()
        torch.set_num_threads(1)
        smiles = ["CCCCCCC", "O=Cc1ccco1", "c1ccccc1"]
        canon = [
            Chem.MolToSmiles(Chem.MolFromSmiles(s), canonical=True, isomericSmiles=True)
            for s in smiles
        ]
        self.order = np.argsort(canon)
        self.inverse = np.argsort(self.order)
        features = {k: v.numpy() for k, v in payload["feature_map"].items()}
        matrix = np.stack([features[canon[i]] for i in self.order]).astype(np.float32)[
            None
        ]
        self.matrix = torch.as_tensor(matrix, dtype=torch.float64)
        self.torch, self.repeat_context, self.simplex_grid = (
            torch,
            repeat_context,
            simplex_grid,
        )
        self.contexts: dict[float, Any] = {}

    def split(self, temperature: float, z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        torch = self.torch
        z = composition(z)
        if temperature not in self.contexts:
            with torch.no_grad():
                self.contexts[temperature] = self.model.context(
                    self.matrix,
                    torch.tensor([[temperature]], dtype=torch.float64),
                    torch.tensor([[101.3]], dtype=torch.float64),
                    torch.ones((1, 3), dtype=torch.float64),
                )
        ctx = self.contexts[temperature]
        qgrid, a, b, d, normal = ctx[4:9]
        ordered = z[self.order]
        q = (torch.tensor(ordered[None], dtype=torch.float64) * normal).sum(
            -1, keepdim=True
        )
        if float(q) < float(qgrid.min()) or float(q) > float(qgrid.max()):
            raise ValueError("Feed outside learned tie-line range")
        with torch.no_grad():
            ua, ub = branch_values(qgrid, a, b, q)
            ends = torch.stack(
                [1 / 3 + q * normal + ua * d, 1 / 3 + q * normal + ub * d], 1
            )[0]
        pairs = ends.numpy()
        lever_rule(ordered, *pairs)
        _, _, mu, _ = self.model.thermo(self.repeat_context(ctx, 2), ends, False)
        mu = mu.detach()
        rms = float((mu[0] - mu[1]).square().mean().sqrt())
        grid = torch.tensor(
            np.vstack([self.simplex_grid(3), pairs, ordered]), dtype=torch.float64
        )
        _, _, _, g = self.model.thermo(self.repeat_context(ctx, len(grid)), grid, False)
        minimum = float((g.detach().flatten()[None] - mu @ grid.T).min())
        if rms > 1e-3 or minimum < -1e-4 or abs(pairs[0] - pairs[1]).sum() <= 0.005:
            raise ValueError(
                "LLE chemical-potential or finite-grid TPD validation failed"
            )
        pairs = pairs[:, self.inverse]
        pairs = pairs[np.argsort(-pairs[:, 1])]
        return pairs[0], pairs[1]


class UnifacSplit:
    """Original UNIFAC equations with the LLE-specific subgroup/interaction tables."""

    def __init__(self, temperature: float):
        from importlib.metadata import version
        from thermo import unifac

        if version("thermo") != "0.6.1":
            raise ValueError("The LLE reference requires thermo==0.6.1")
        unifac.load_unifac_ip()
        groups = [{1: 2, 2: 5}, {22: 1}, {9: 6}]
        names = {1: "CH3", 2: "CH2", 22: "Furfural", 9: "ACH"}
        if any(unifac.LLEUFSG[k].group != v for k, v in names.items()):
            raise ValueError("LLE-specific subgroup table mismatch")
        main = {unifac.LLEUFSG[k].main_group_id for group in groups for k in group}
        if any(
            j not in unifac.LLEUFIP.get(i, {}) for i in main for j in main if i != j
        ):
            raise ValueError("Missing directed LLE interaction parameter")
        self.temperature = temperature
        self.model = unifac.UNIFAC.from_subgroups(
            T=temperature,
            xs=[1 / 3] * 3,
            chemgroups=groups,
            subgroups=unifac.LLEUFSG,
            interaction_data=unifac.LLEUFIP,
            version=0,
        )
        grid = (
            np.array(
                [[i, j, 60 - i - j] for i in range(61) for j in range(61 - i)], float
            )
            / 60
        )
        grid = np.maximum(grid, 1e-12)
        self.grid = grid / grid.sum(axis=1, keepdims=True)
        self.g = np.array([x @ self.mu(x) for x in self.grid])

    def mu(self, x: np.ndarray) -> np.ndarray:
        return np.log(x) + np.asarray(
            self.model.to_T_xs(T=self.temperature, xs=x.tolist()).lngammas()
        )

    def __call__(self, z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        z = composition(z)
        grid = np.vstack([self.grid, z])
        g = np.r_[self.g, z @ self.mu(z)]
        hull = linprog(
            g,
            A_eq=np.vstack([np.ones(len(grid)), grid[:, :-1].T]),
            b_eq=np.r_[1, z[:-1]],
            bounds=(0, None),
            method="highs",
        )
        if not hull.success:
            raise ValueError("Gibbs-grid initialization failed")
        active = np.flatnonzero(hull.x > 1e-8)
        seeds = [(grid[i], grid[j]) for i, j in combinations(active, 2)]
        corners = np.eye(3) * 0.97 + np.full((3, 3), 0.01)
        seeds.extend(combinations(corners, 2))
        seeds.sort(key=lambda ab: float(np.linalg.norm(ab[0] - ab[1])), reverse=True)

        def decode(v: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
            return (
                softmax(np.r_[v[:2], 0]),
                softmax(np.r_[v[2:4], 0]),
                float(expit(v[-1])),
            )

        def residual(v: np.ndarray) -> np.ndarray:
            a, b, beta = decode(v)
            return np.r_[self.mu(a) - self.mu(b), (beta * a + (1 - beta) * b - z)[:-1]]

        for a0, b0 in seeds:
            beta0 = float(
                np.clip((z - b0) @ (a0 - b0) / sum((a0 - b0) ** 2), 0.01, 0.99)
            )
            initial = np.r_[
                np.log(a0[:-1] / a0[-1]), np.log(b0[:-1] / b0[-1]), logit(beta0)
            ]
            solved = least_squares(
                residual,
                np.clip(initial, -29, 29),
                bounds=(-30, 30),
                xtol=1e-12,
                ftol=1e-12,
                gtol=1e-12,
                max_nfev=600,
            )
            a, b, beta = decode(solved.x)
            if (
                not solved.success
                or max(abs(residual(solved.x))) > 1e-7
                or sum(abs(a - b)) <= 0.005
                or not 1e-7 < beta < 1 - 1e-7
            ):
                continue
            tangent = self.mu(a)
            tpd = g - grid @ tangent
            minimum = min(
                tpd.min(), a @ self.mu(a) - a @ tangent, b @ self.mu(b) - b @ tangent
            )
            for x0 in [*grid[np.argsort(tpd)[:8]], a, b]:

                def objective(v: np.ndarray) -> float:
                    x = softmax(np.r_[v, 0])
                    return float(x @ (self.mu(x) - tangent))

                check = minimize(
                    objective,
                    np.clip(np.log(x0[:-1] / x0[-1]), -29, 29),
                    method="L-BFGS-B",
                    bounds=[(-30, 30)] * 2,
                )
                minimum = min(minimum, float(check.fun))
            if minimum < -1e-6:
                continue
            lever_rule(z, a, b)
            return (a, b) if a[1] > b[1] else (b, a)
        raise ValueError("No nontrivial validated UNIFAC two-liquid split found")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=["thermoformer", "unifac"], required=True)
    parser.add_argument("--repository", type=Path, default=ROOT.parent)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Recalculate all reported designs, allocations and single-stage scans for this model",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "generated")
    args = parser.parse_args()
    verify_manifest()
    data = ROOT / "cases/crossflow_extraction/data"
    model = "ThermoFormer" if args.model == "thermoformer" else "UNIFAC-LLE"
    rows = load(data / "cascade_designs.json")
    if args.all:
        rows += load(data / "allocation_designs.json") + load(data / "scan.json")
    else:
        rows = [r for r in rows if r["T"] == 303.15 and r["N"] == 3]
    rows = [r for r in rows if r["model"] == model]
    tf = ThermoFormerSplit(args.repository) if args.model == "thermoformer" else None
    unifac: dict[float, UnifacSplit] = {}
    output = []
    for row in rows:
        temperature = row["T"]
        if tf is not None:

            def split(z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
                return tf.split(temperature, z)
        else:
            if temperature not in unifac:
                unifac[temperature] = UnifacSplit(temperature)
            split = unifac[temperature]
        allocation = row.get("allocation")
        if allocation is None:
            allocation = (
                [row["total_S"] / row["N"]] * row["N"] if "N" in row else [row["S"]]
            )
        result = cascade(allocation, split)
        for key in ["benzene_recovery", "heptane_retention"]:
            check_close(result[key], row[key], 2e-6)
        output.append(dict(T=temperature, model=model, allocation=allocation, **result))
    write(args.output / f"crossflow_{args.model}_inference.json", output)
    print(
        f"{model}: {len(output)} independently recalculated process configurations agree with the paper records."
    )


if __name__ == "__main__":
    main()
