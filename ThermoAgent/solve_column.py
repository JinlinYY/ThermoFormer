"""Re-solve the published 182/183-stage columns with direct bubble refinement."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
from scipy.interpolate import RectBivariateSpline

import column
from inference import ThermoFormerBubble, UnifacBubble
from reproduce import ROOT, check_close, load, verify_manifest, write


class Surface:
    """Smooth grid surface used for the inner material-balance solve."""

    def __init__(self, path: Path):
        record = load(path)
        axis = np.asarray(record["axis"])
        n = len(axis)
        logk = np.log(np.asarray(record["y"]) / np.asarray(record["x"]))
        self.curves = [
            RectBivariateSpline(axis, axis, logk[:, k].reshape(n, n)) for k in range(3)
        ]
        self.temperature = RectBivariateSpline(
            axis, axis, np.asarray(record["T"]).reshape(n, n)
        )
        self.delta: Any = 0.0
        self.dt: Any = 0.0

    def state(self, rs: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        x = column.xs(rs)
        r, s = rs.T
        logk = np.array([curve.ev(r, s) for curve in self.curves]).T
        y = x * np.exp(logk + self.delta)
        y /= y.sum(axis=1)[:, None]
        return x, y, self.temperature.ev(r, s) + self.dt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=["thermoformer", "unifac"], required=True)
    parser.add_argument("--stages", type=int, choices=[182, 183], default=183)
    parser.add_argument("--repository", type=Path, default=ROOT.parent)
    parser.add_argument("--output", type=Path, default=ROOT / "generated")
    args = parser.parse_args()
    if args.model == "unifac" and args.stages != 183:
        parser.error("The reported common-column UNIFAC result uses 183 stages")
    verify_manifest()
    case = ROOT / "cases/extractive_distillation"
    name = f"{args.model}_{args.stages}"
    published = load(case / "data" / f"{name}.json")
    surface = Surface(case / "data" / f"{args.model}_surface.json")
    bubble = (
        ThermoFormerBubble("extractive_distillation", args.repository)
        if args.model == "thermoformer"
        else UnifacBubble("extractive_distillation")
    )
    initial = column.rs_from_x(np.asarray(published["x"]))
    # Published trajectories provide a continuation initial guess. The final
    # acceptance check always uses fresh bubble evaluations at all local x.
    for _ in range(15):
        result = column.solve(
            surface,
            args.stages,
            published["nf"],
            published["ns"],
            published["R"],
            published["S"],
            published["D"],
            init=initial,
        )
        initial = np.asarray(result["rs"])
        x, grid_y, grid_t = surface.state(initial)
        t, y = bubble(x)
        surface.delta += np.log(y / grid_y)
        surface.dt += t - grid_t
        balance, _, _, _ = column.residual(
            initial,
            surface,
            args.stages,
            published["nf"],
            published["ns"],
            published["R"],
            published["S"],
            published["D"],
            True,
        )
        if np.max(abs(balance)) < 1e-8:
            result.update(
                x=x.tolist(),
                y=y.tolist(),
                T=t.tolist(),
                xD=y[0].tolist(),
                xB=x[-1].tolist(),
                recovery=published["D"] * y[0, 1] / 0.5,
                mass_residual=float(abs(balance).max()),
                success=True,
                direct_bubble_refinement=True,
            )
            check_close(result["xD"], published["xD"], 2e-6)
            check_close(result["recovery"], published["recovery"], 2e-6)
            if (result["xD"][1] >= 0.995 and result["recovery"] >= 0.98) != (
                args.model == "thermoformer" and args.stages == 183
            ):
                raise ValueError(
                    "Re-solved column changes the reported threshold outcome"
                )
            write(args.output / f"{name}_resolved.json", result)
            print(
                f"{name}: direct stage balance {result['mass_residual']:.3g} mol/s; agrees with paper."
            )
            return
    raise RuntimeError("Direct bubble refinement did not converge")


if __name__ == "__main__":
    main()
