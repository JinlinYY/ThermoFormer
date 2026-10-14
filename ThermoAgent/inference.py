"""Re-evaluate the paper's VLE states using repository weights or original UNIFAC.

The bundled molecular vectors are the exact feature-cache rows for these
components. The checkpoint's descriptor scaler is applied before inference.
No experimental temperature is supplied to the bubble-point calculation.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import brentq

from reproduce import ROOT, check_close, load, read_csv, verify_manifest, write


class ThermoFormerBubble:
    """Batched fixed-pressure bubble calculation for the two published VLE cases."""

    def __init__(self, case: str, repository: Path):
        import torch

        sys.path.insert(0, str(repository / "src"))
        from thermoformer.models import ThermoFormer, ThermoFormerConfig
        from thermoformer.thermodynamics.vle_solver import equilibrium_at_tp

        inputs = load(ROOT / "cases" / case / "data/model_inputs.json")
        checkpoint = repository / inputs["checkpoint"]
        if (
            hashlib.sha256(checkpoint.read_bytes()).hexdigest()
            != inputs["checkpoint_sha256"]
        ):
            raise ValueError(
                "Checkpoint checksum mismatch; retrieve the registered Git LFS weight"
            )
        payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
        for key in ["feature_cache_sha256", "pure_property_catalog_sha256"]:
            if inputs[key] != payload[key]:
                raise ValueError(f"Checkpoint/input provenance mismatch: {key}")
        features = np.asarray(inputs["raw_molecular_features"], dtype=np.float32)
        scaler = payload["molecular_feature_preprocessing"]["rdkit_scaler"]
        features[:, :24] = (
            features[:, :24] - np.asarray(scaler["mean"], dtype=np.float32)
        ) / np.asarray(scaler["std"], dtype=np.float32)
        self.features = torch.tensor(features, dtype=torch.float64)[None]
        self.pure = torch.tensor(inputs["pure_parameters"], dtype=torch.float64)[None]
        self.model = ThermoFormer(ThermoFormerConfig(**payload["model_config"]))
        self.model.load_state_dict(payload["model"], strict=True)
        self.model = self.model.double().eval()
        self.evaluate = equilibrium_at_tp
        self.torch = torch
        torch.set_num_threads(1)

    def state(self, x: np.ndarray, temperature: np.ndarray) -> Any:
        torch = self.torch
        n, k = x.shape
        return self.evaluate(
            self.model,
            self.features.expand(n, -1, -1),
            torch.tensor(temperature, dtype=torch.float64).reshape(-1, 1),
            torch.full((n, 1), 101.3, dtype=torch.float64),
            torch.tensor(x, dtype=torch.float64),
            torch.ones((n, k), dtype=torch.bool),
            self.pure.expand(n, -1, -1),
        )

    def __call__(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        temperatures, vapors = [], []
        for start in range(0, len(x), 96):
            batch = np.asarray(x[start : start + 96], dtype=float)
            lo, hi = np.full(len(batch), 340.0), np.full(len(batch), 460.0)

            def residual(t):
                return (
                    self.state(batch, t).pressure_residual_kpa.detach().numpy().ravel()
                )

            if np.any(residual(lo) >= 0) or np.any(residual(hi) <= 0):
                raise ValueError(
                    "Bubble point is not bracketed in the case temperature interval"
                )
            for _ in range(40):
                mid = (lo + hi) / 2
                below = residual(mid) < 0
                lo, hi = np.where(below, mid, lo), np.where(below, hi, mid)
            t = (lo + hi) / 2
            state = self.state(batch, t)
            if np.max(abs(state.pressure_residual_kpa.detach().numpy())) > 1e-7:
                raise ValueError("Bubble pressure residual exceeds tolerance")
            y = state.y.detach().numpy()
            check_close(y.sum(axis=1), 1, 1e-8)
            temperatures.append(t)
            vapors.append(y)
        return np.concatenate(temperatures), np.concatenate(vapors)


class UnifacBubble:
    """Original UNIFAC and thermo 0.6.1 pure-component vapor pressures."""

    def __init__(self, case: str):
        from importlib.metadata import version
        from thermo import Chemical
        from thermo.unifac import UNIFAC_gammas, UNIFAC_group_assignment_DDBST

        if version("thermo") != "0.6.1":
            raise ValueError("The paper UNIFAC reference requires thermo==0.6.1")
        cas = (
            ["142-82-5", "111-84-2"]
            if case == "binary_distillation"
            else ["78-92-2", "105-46-4", "68-12-2"]
        )
        self.chemicals = [Chemical(c) for c in cas]
        self.groups = [UNIFAC_group_assignment_DDBST(c, "UNIFAC") for c in cas]
        if not all(self.groups):
            raise ValueError("Missing original-UNIFAC group assignment")
        self.gamma = UNIFAC_gammas

    def __call__(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        temperature, vapor = [], []
        for xi in x:

            def raw_y(t: float) -> np.ndarray:
                g = self.gamma(T=t, xs=xi.tolist(), chemgroups=self.groups)
                psat = np.array([c.VaporPressure(t) for c in self.chemicals])
                return xi * g * psat / 101300.0

            t = brentq(lambda t: raw_y(t).sum() - 1, 340, 460, xtol=1e-9)
            y = raw_y(t)
            check_close(y.sum(), 1, 1e-8)
            temperature.append(t)
            vapor.append(y)
        return np.asarray(temperature), np.asarray(vapor)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        choices=["binary_distillation", "extractive_distillation"],
        required=True,
    )
    parser.add_argument("--model", choices=["thermoformer", "unifac"], required=True)
    parser.add_argument("--repository", type=Path, default=ROOT.parent)
    parser.add_argument(
        "--column-states",
        action="store_true",
        help="Also recompute all published local column bubble states",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "generated")
    args = parser.parse_args()
    verify_manifest()
    case = ROOT / "cases" / args.case
    bubble = (
        ThermoFormerBubble(args.case, args.repository)
        if args.model == "thermoformer"
        else UnifacBubble(args.case)
    )
    rows = read_csv(case / "data/equilibrium.csv")
    if args.case == "binary_distillation":
        x = np.array([[float(r["x_heptane"]), 1 - float(r["x_heptane"])] for r in rows])
        original_t = np.array([float(r[f"{args.model}_T_K"]) for r in rows])
        original_y = np.array([float(r[f"{args.model}_y"]) for r in rows])
    else:
        key = "tf" if args.model == "thermoformer" else "unifac"
        x = np.array(
            [[float(r[f"x_{c}"]) for c in ["alcohol", "ester", "DMF"]] for r in rows]
        )
        original_t = np.array([float(r[f"T_{key}_K"]) for r in rows])
        original_y = np.array(
            [
                [float(r[f"y_{key}_{c}"]) for c in ["alcohol", "ester", "DMF"]]
                for r in rows
            ]
        )
    t, y = bubble(x)
    check_close(t, original_t, 2e-5)
    check_close(y[:, 0] if args.case == "binary_distillation" else y, original_y, 2e-7)
    results = dict(
        x=x.tolist(),
        y=y.tolist(),
        T_K=t.tolist(),
        verified_equilibrium_states=len(rows),
    )
    if args.column_states:
        if args.case != "extractive_distillation":
            raise ValueError(
                "--column-states is only defined for extractive_distillation"
            )
        names = (
            ["thermoformer_182", "thermoformer_183"]
            if args.model == "thermoformer"
            else ["unifac_183"]
        )
        results["columns"] = {}
        for name in names:
            record = load(case / "data" / f"{name}.json")
            t, y = bubble(np.asarray(record["x"]))
            check_close(t, record["T"], 2e-5)
            check_close(y, record["y"], 2e-7)
            results["columns"][name] = dict(
                T_K=t.tolist(), y=y.tolist(), verified_stages=len(t)
            )
    write(args.output / f"{args.case}_{args.model}_inference.json", results)
    print(
        f"Fresh {args.model} bubble calculations agree with archived {args.case} results."
    )


if __name__ == "__main__":
    main()
