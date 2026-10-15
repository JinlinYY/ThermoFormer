"""Frozen-gamma comparison using common, externally sourced vapor pressures.

Research-only CLI. Original paper results and production defaults are preserved.
Ester vapor-pressure extrapolation is recorded, never treated as measured truth.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Literal

from paper_agent.runtime import configure_runtime

# This must precede scientific imports in the mixed-OpenMP ggnn39 environment.
# ruff: noqa: E402
configure_runtime()

import numpy as np
from pydantic import BaseModel
from scipy.optimize import brentq

from thermo_engine.paper_unifac_audit import CASE, LEGACY, ROOT, UNIFACAuditBackend, read, stage_checks, write
from thermo_engine.paper_validation import validate_equilibrium_result

OUTPUT = ROOT / "outputs/paper_agent/common-psat-20260928"
P_KPA = 101.3


class EsterAntoine(BaseModel):
    """External coefficient boundary; pressure in kPa and temperature in K."""

    name: str
    a: float
    b: float
    c: float
    source_doi: str
    observed_temperature_range_K: tuple[float, float] | None

    def pressure(self, temperatures: Any) -> Any:
        return 10 ** (self.a - self.b / (np.asarray(temperatures) + self.c))


REFERENCES = {
    "li2013": EsterAntoine(
        name="Li 2013 Table 3, published rounded coefficients",
        a=4.36,
        b=487.96,
        c=-175.67,
        source_doi="10.1016/S1004-9541(13)60534-0",
        observed_temperature_range_K=(329.0, 384.0),
    ),
    "huang2015": EsterAntoine(
        name="Huang 2015, as quoted in Yin 2019 Table 3",
        a=6.52785,
        b=1550.251,
        c=-42.1408,
        source_doi="10.1016/j.fluid.2015.05.032; coefficient access: 10.1021/acs.jced.9b00430",
        observed_temperature_range_K=None,
    ),
}


class CommonBubble:
    """Identical external Psat calls with interchangeable frozen gamma models."""

    def __init__(self, gamma: Literal["unifac", "thermoformer"], reference: str, unifac: Any, tf: Any) -> None:
        self.gamma_name = gamma
        self.reference = REFERENCES[reference]
        self.unifac = unifac
        self.tf = tf
        self.evaluated_states = 0

    def psat(self, temperatures: Any) -> Any:
        values = self.unifac.psat(temperatures) / 1000
        values[:, 1] = self.reference.pressure(temperatures)
        return values

    def gammas(self, x: Any, temperatures: Any) -> Any:
        if self.gamma_name == "unifac":
            return self.unifac.gammas(x, temperatures)
        return self.tf.state(np.asarray(x), np.asarray(temperatures)).gamma.detach().numpy()

    def bubble(self, compositions: Any) -> tuple[Any, Any]:
        ts, ys = [], []
        for start in range(0, len(compositions), 96):
            x = np.asarray(compositions[start : start + 96], dtype=float)

            def raw(t: Any, liquid: Any = x) -> Any:
                self.evaluated_states += len(liquid)
                return liquid * self.gammas(liquid, t) * self.psat(t) / P_KPA

            lo, hi = np.full(len(x), 340.0), np.full(len(x), 460.0)
            if np.any(raw(lo).sum(axis=1) >= 1) or np.any(raw(hi).sum(axis=1) <= 1):
                raise ValueError("Bubble root not bracketed at 340--460 K")
            for _ in range(40):
                mid = (lo + hi) / 2
                below = raw(mid).sum(axis=1) < 1
                lo, hi = np.where(below, mid, lo), np.where(below, hi, mid)
            t = (lo + hi) / 2
            y = raw(t)
            gate = validate_equilibrium_result(np.r_[x, y], float(abs(y.sum(axis=1) - 1).max()), temperatures=t)
            if not gate["passed"]:
                raise ValueError(gate)
            ts.append(t)
            ys.append(y)
        return np.concatenate(ts), np.concatenate(ys)

    def coverage(self, temperatures: Any) -> dict[str, Any]:
        bounds = self.reference.observed_temperature_range_K
        t = np.asarray(temperatures)
        return dict(
            ester_correlation=self.reference.model_dump(),
            ester_range_verified=bounds is not None,
            ester_outside_correlation_range=None if bounds is None else int(np.sum((t < bounds[0]) | (t > bounds[1]))),
            temperature_range_K=[float(t.min()), float(t.max())],
            global_stability="not_certified",
        )


def reference_points(backend: CommonBubble, output: Path) -> dict[str, Any]:
    with (CASE / "data/equilibrium.csv").open(encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    names = ["alcohol", "ester", "DMF"]
    x = np.array([[float(r["x_" + c]) for c in names] for r in rows])
    expected_y = np.array([[float(r["y_exp_" + c]) for c in names] for r in rows])
    expected_t = np.array([float(r["T_exp_K"]) for r in rows])
    t, y = backend.bubble(x)
    alpha = y[:, 1] * x[:, 0] / (y[:, 0] * x[:, 1])
    expected_alpha = expected_y[:, 1] * x[:, 0] / (expected_y[:, 0] * x[:, 1])
    gamma = backend.gammas(x, expected_t)
    psat = backend.psat(expected_t)
    implied_gamma = expected_y * P_KPA / (x * psat)
    at_measured = x * gamma * psat
    result = dict(
        n=len(x),
        x=x.tolist(),
        T_K=t.tolist(),
        y=y.tolist(),
        y_MAE=float(abs(y - expected_y).mean()),
        T_MAE_K=float(abs(t - expected_t).mean()),
        alpha_MAE=float(abs(alpha - expected_alpha).mean()),
        direction_agreement=int(np.sum((alpha > 1) == (expected_alpha > 1))),
        alpha=alpha.tolist(),
        alpha_experiment=expected_alpha.tolist(),
        gamma_at_experimental_T=gamma.tolist(),
        common_psat_at_experimental_T_kPa=psat.tolist(),
        experimental_T_K=expected_t.tolist(),
        gamma_inferred_from_experiment_with_common_psat=implied_gamma.tolist(),
        log_gamma_MAE=float(abs(np.log(gamma) - np.log(implied_gamma)).mean()),
        pressure_MAE_at_measured_xT_kPa=float(abs(at_measured.sum(axis=1) - P_KPA).mean()),
        validation=validate_equilibrium_result(np.r_[x, y], float(abs(y.sum(axis=1) - 1).max()), temperatures=t),
        coverage=backend.coverage(t),
    )
    write(output / "reference_points.json", result)
    return result


def build_surface(backend: CommonBubble, output: Path) -> Path:
    path = output / "surface.json"
    if path.exists():
        # Verify cached surfaces against direct calculations before reusing them.
        cached = read(path)
        indices = np.linspace(0, len(cached["x"]) - 1, 9, dtype=int)
        check_t, check_y = backend.bubble(np.asarray(cached["x"])[indices])
        if not (
            np.max(abs(check_t - np.asarray(cached["T"])[indices])) < 1e-7
            and np.max(abs(check_y - np.asarray(cached["y"])[indices])) < 1e-9
        ):
            raise ValueError("Cached surface does not match the selected gamma and common vapor pressures")
        return path
    # Same Chebyshev grid as the paper, recomputed with the common pure properties.
    original = read(CASE / "data/unifac_surface.json")
    x = np.array(original["x"])
    print(f"Building {output.name} surface ({len(x)} bubble points)", flush=True)
    t, y = backend.bubble(x)
    write(path, dict(axis=original["axis"], x=x.tolist(), T=t.tolist(), y=y.tolist(), coverage=backend.coverage(t)))
    return path


def solve_columns(backend: CommonBubble, surface_path: Path, output: Path) -> list[dict[str, Any]]:
    column = importlib.import_module("column")
    surface_type = importlib.import_module("solve_column").Surface
    config = read(CASE / "data/unifac_183.json")
    runs = []
    for initial_name in ["unifac_183", "thermoformer_183"]:
        initial = column.rs_from_x(np.array(read(CASE / "data" / (initial_name + ".json"))["x"]))
        if backend.gamma_name == "thermoformer":
            initial = continuation_seed(backend, surface_path, config, initial, output, initial_name)
        surface = surface_type(surface_path)
        history = []
        started = time.perf_counter()
        accepted = False
        for iteration in range(40):
            solved = column.solve(
                surface,
                183,
                config["nf"],
                config["ns"],
                config["R"],
                config["S"],
                config["D"],
                init=initial,
                maxeval=500,
            )
            initial = np.array(solved["rs"])
            x, grid_y, grid_t = surface.state(initial)
            t, y = backend.bubble(x)
            check = stage_checks(config, x, y, t, float(abs(y.sum(axis=1) - 1).max()))
            history.append(dict(iteration=iteration, inner_solver_success=solved["success"], **check))
            write(output / ("progress_" + initial_name + ".json"), dict(history=history, rs=initial.tolist()))
            print(
                f"{output.name} {initial_name} iteration {iteration}: "
                f"purity={check['ester_purity']:.10f}, balance={check['maximum_stage_balance_mol_s']:.3g}",
                flush=True,
            )
            if solved["success"] and check["validation"]["passed"] and check["maximum_stage_balance_mol_s"] < 1e-8:
                accepted = True
                break
            surface.delta += np.log(y / grid_y)
            surface.dt += t - grid_t
        gamma = np.concatenate([backend.gammas(x[j : j + 96], t[j : j + 96]) for j in range(0, len(x), 96)])
        psat = backend.psat(t)
        result = dict(
            initialization=initial_name,
            accepted=accepted,
            elapsed_s=time.perf_counter() - started,
            configuration={k: config[k] for k in ["N", "nf", "ns", "R", "S", "D", "B"]},
            history=history,
            x=x.tolist(),
            y=y.tolist(),
            T=t.tolist(),
            gamma=gamma.tolist(),
            psat_kPa=psat.tolist(),
            alpha_ester_alcohol=(gamma[:, 1] * psat[:, 1] / gamma[:, 0] / psat[:, 0]).tolist(),
            coverage=backend.coverage(t),
        )
        write(output / ("column_from_" + initial_name + ".json"), result)
        runs.append(
            dict(initialization=initial_name, accepted=accepted, final=history[-1], coverage=result["coverage"])
        )
    write(output / "column_summary.json", runs)
    return runs


def continuation_seed(
    backend: CommonBubble, surface_path: Path, config: dict[str, Any], initial: Any, output: Path, label: str
) -> Any:
    """Increase column length to condition the fixed-configuration solve.

    Intermediate lengths are numerical continuation steps, not new design results.
    Final numerical acceptance still requires direct equilibrium on all 183 stages.
    """
    column = importlib.import_module("column")
    surface_type = importlib.import_module("solve_column").Surface
    records = []
    for n in [20, 40, 70, 110, 150, 183]:
        nf, ns = round(159 * n / 183), max(2, round(16 * n / 183))
        surf = surface_type(surface_path)
        result = column.solve(surf, n, nf, ns, config["R"], config["S"], config["D"], init=initial, maxeval=1500)
        initial = np.array(result["rs"])
        records.append(dict(N=n, nf=nf, ns=ns, success=result["success"], mass_residual=result["mass_residual"]))
        print(
            f"{output.name} {label} continuation N={n}: "
            f"success={result['success']}, residual={result['mass_residual']:.3g}",
            flush=True,
        )
        write(output / ("continuation_" + label + ".json"), dict(records=records, rs=initial.tolist()))
        if not result["success"]:
            break
    return initial


def pure_checks(unifac: Any, tf: Any, output: Path) -> None:
    with (OUTPUT / "sources/sec_butyl_acetate_li2013_table2.csv").open(encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    t = np.array([float(row["temperature_K"]) for row in rows])
    measured = np.array([float(row["pressure_kPa"]) for row in rows])
    uniform = np.full((len(t), 3), 1 / 3)
    predictions = dict(
        original_unifac=unifac.psat(t)[:, 1] / 1000,
        original_thermoformer=tf.state(uniform, t).psat_kpa.detach().numpy()[:, 1],
    )
    predictions.update({key: ref.pressure(t) for key, ref in REFERENCES.items()})
    curve_t = np.linspace(329.75, 425, 160)
    curve_tf = tf.state(np.full((len(curve_t), 3), 1 / 3), curve_t).psat_kpa.detach().numpy()
    curve_unifac = unifac.psat(curve_t) / 1000
    curves = dict(original_unifac=curve_unifac.tolist(), original_thermoformer=curve_tf.tolist())
    for key, ref in REFERENCES.items():
        common = curve_unifac.copy()
        common[:, 1] = ref.pressure(curve_t)
        curves[key] = common.tolist()
    result = dict(
        T_K=t.tolist(),
        experimental_P_kPa=measured.tolist(),
        curve_T_K=curve_t.tolist(),
        curves_psat_kPa=curves,
        predictions={
            key: dict(
                P_kPa=values.tolist(),
                MAE_kPa=float(abs(values - measured).mean()),
                relative_MAE_percent=float((abs(values - measured) / measured).mean() * 100),
            )
            for key, values in predictions.items()
        },
        external_correlations={key: ref.model_dump() for key, ref in REFERENCES.items()},
        external_normal_boil_K={
            key: float(brentq(lambda temperature, ref=ref: ref.pressure(temperature) - P_KPA, 340, 440))
            for key, ref in REFERENCES.items()
        },
        original_backend_provenance=unifac.provenance(),
    )
    write(output / "pure_pressure_checks.json", result)


def decomposition(unifac: Any, tf: Any, output: Path) -> None:
    old = read(CASE / "data/thermoformer_183.json")
    indices = [0, 15, 89, 158, 182]
    x, t = np.array(old["x"])[indices], np.array(old["T"])[indices]
    state = tf.state(x, t)
    gt, pt = state.gamma.detach().numpy(), state.psat_kpa.detach().numpy()
    gamma_reproduction = float(abs(gt - np.array(old["gamma"])[indices]).max())
    psat_reproduction = float(abs(pt - np.array(old["psat_kPa"])[indices]).max())
    if gamma_reproduction > 1e-9 or psat_reproduction > 1e-7:
        raise ValueError("Frozen ThermoFormer no longer reproduces the archived fixed-state outputs")
    gu, pu = unifac.gammas(x, t), unifac.psat(t) / 1000
    result = dict(
        frozen_tf_gamma_reproduction_max_abs_error=gamma_reproduction,
        frozen_tf_psat_reproduction_max_abs_error_kPa=psat_reproduction,
        stage=[i + 1 for i in indices],
        x=x.tolist(),
        T_K=t.tolist(),
        gamma_ratio_unifac=(gu[:, 1] / gu[:, 0]).tolist(),
        gamma_ratio_tf=(gt[:, 1] / gt[:, 0]).tolist(),
        psat_ratio_old_unifac=(pu[:, 1] / pu[:, 0]).tolist(),
        psat_ratio_old_tf=(pt[:, 1] / pt[:, 0]).tolist(),
        alpha_original_unifac=(gu[:, 1] * pu[:, 1] / gu[:, 0] / pu[:, 0]).tolist(),
        alpha_original_tf=(gt[:, 1] * pt[:, 1] / gt[:, 0] / pt[:, 0]).tolist(),
        log_alpha_difference_gamma=np.log((gt[:, 1] / gt[:, 0]) / (gu[:, 1] / gu[:, 0])).tolist(),
        log_alpha_difference_psat=np.log((pt[:, 1] / pt[:, 0]) / (pu[:, 1] / pu[:, 0])).tolist(),
        common={},
    )
    for key in REFERENCES:
        backend = CommonBubble("unifac", key, unifac, tf)
        common = backend.psat(t)
        result["common"][key] = dict(
            psat_kPa=common.tolist(),
            alpha_unifac=(gu[:, 1] * common[:, 1] / gu[:, 0] / common[:, 0]).tolist(),
            alpha_tf=(gt[:, 1] * common[:, 1] / gt[:, 0] / common[:, 0]).tolist(),
        )
    write(output / "fixed_state_decomposition.json", result)


def summarize(output: Path) -> None:
    """Aggregate only numerically accepted column records and their limitations."""
    original = read(CASE / "results/comparison.json")
    records = []
    for model, key in [("unifac", "unifac"), ("thermoformer", "tf")]:
        column = next(r for r in original["configurations"] if r["configuration"] == model + "_183")
        records.append(
            dict(
                reference="original",
                gamma_model=model,
                purity_percent=100 * column["ester_purity"],
                recovery_percent=100 * column["ester_recovery"],
                y_MAE=original["metrics"][key]["y_MAE"],
                T_MAE_K=original["metrics"][key]["T_MAE_K"],
                direction_agreement=original["metrics"][key]["direction_agreement"],
                maximum_stage_balance_mol_s=column["maximum_stage_balance_error_mol_s"],
                data_origin="original_archived_backend_result",
                ester_extrapolated_stages=None,
            )
        )
    for reference in REFERENCES:
        for model in ["unifac", "thermoformer"]:
            path = output / (reference + "_" + model)
            runs = read(path / "column_summary.json")
            if not all(r["accepted"] and r["final"]["validation"]["passed"] for r in runs):
                raise ValueError("Cannot summarize unvalidated column runs")
            final = runs[0]["final"]
            points = read(path / "reference_points.json")
            records.append(
                dict(
                    reference=reference,
                    gamma_model=model,
                    purity_percent=100 * final["ester_purity"],
                    recovery_percent=100 * final["ester_recovery"],
                    y_MAE=points["y_MAE"],
                    T_MAE_K=points["T_MAE_K"],
                    direction_agreement=points["direction_agreement"],
                    maximum_stage_balance_mol_s=final["maximum_stage_balance_mol_s"],
                    data_origin="fresh_common_psat_frozen_gamma",
                    ester_extrapolated_stages=runs[0]["coverage"]["ester_outside_correlation_range"],
                    initialization_purity_max_difference=float(np.ptp([r["final"]["ester_purity"] for r in runs])),
                )
            )
    write(
        output / "summary.json",
        dict(
            records=records,
            conditional_diagnostic_only=True,
            note=(
                "Reference A is extrapolated above 384 K. "
                "Reference B validity interval is unverified. TF weights are frozen."
            ),
        ),
    )
    keys = list(dict.fromkeys(k for record in records for k in record))
    with (output / "summary.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        writer.writerows(records)
    print(json.dumps(records), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--reference", choices=list(REFERENCES), action="append")
    parser.add_argument("--gamma", choices=["unifac", "thermoformer"], action="append")
    parser.add_argument("--points-only", action="store_true")
    parser.add_argument("--summarize-only", action="store_true")
    args = parser.parse_args()
    if args.summarize_only:
        summarize(args.output)
        return
    sys.path.insert(0, str(LEGACY))
    files = [p for p in (CASE / "data").glob("*") if p.is_file()]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    unifac = UNIFACAuditBackend()
    # Explicit common reference methods: no automatic selection or fallback.
    unifac.chemicals[0].VaporPressure.method = "WAGNER_MCGARRY"
    unifac.chemicals[2].VaporPressure.method = "DIPPR_PERRY_8E"
    tf = importlib.import_module("inference").ThermoFormerBubble("extractive_distillation", LEGACY.parent)
    pure_checks(unifac, tf, args.output)
    decomposition(unifac, tf, args.output)
    failed = False
    for reference in args.reference or list(REFERENCES):
        for gamma in args.gamma or ["unifac", "thermoformer"]:
            output = args.output / (reference + "_" + gamma)
            backend = CommonBubble(gamma, reference, unifac, tf)
            points = reference_points(backend, output)
            print(
                json.dumps(
                    dict(
                        configuration=output.name,
                        reference_metrics={k: points[k] for k in ["y_MAE", "T_MAE_K", "direction_agreement"]},
                    )
                ),
                flush=True,
            )
            if not args.points_only:
                path = build_surface(backend, output)
                runs = solve_columns(backend, path, output)
                failed = failed or any(not run["accepted"] for run in runs)
    unchanged = all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == value for p, value in hashes.items())
    write(args.output / "integrity.json", dict(source_hashes=hashes, unchanged=unchanged))
    if failed or not unchanged:
        raise RuntimeError("Audit failure: unconverged column or modified original data")


if __name__ == "__main__":
    main()
