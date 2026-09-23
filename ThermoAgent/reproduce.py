"""Recalculate the three SI process studies from archived equilibrium states."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial import Delaunay

import binary
import column
from extraction import RecordedEndpoints, cascade, composition, experimental_split

ROOT = Path(__file__).resolve().parent


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def check_close(actual: Any, expected: Any, tolerance: float = 1e-8) -> None:
    if not np.allclose(actual, expected, atol=tolerance, rtol=0):
        raise ValueError(f"Published-result mismatch: {actual} != {expected}")


def binary_case(output: Path) -> dict[str, Any]:
    case = ROOT / "cases/binary_distillation"
    rows = read_csv(case / "data/equilibrium.csv")
    if len(rows) != 16:
        raise ValueError("Expected all 16 equilibrium states")
    x = np.array([float(r["x_heptane"]) for r in rows])
    curves = {}
    metrics = {}
    for source, prefix in [
        ("Experimental interpolation", "exp"),
        ("ThermoFormer", "thermoformer"),
        ("UNIFAC", "unifac"),
    ]:
        ykey = "y_exp" if prefix == "exp" else f"{prefix}_y"
        y = np.array([float(r[ykey]) for r in rows])
        y[0], y[-1] = 0, 1
        for kind in ["pchip", "linear"]:
            curves[source, kind] = binary.curve(x, y, kind)
        if prefix != "exp":
            ye = y - np.array([float(r["y_exp"]) for r in rows])
            te = np.array(
                [float(r[f"{prefix}_T_K"]) - float(r["T_exp_K"]) for r in rows]
            )
            metrics[source] = dict(
                y_MAE=float(abs(ye).mean()),
                y_RMSE=float(np.sqrt((ye**2).mean())),
                y_max_error=float(abs(ye).max()),
                T_MAE_K=float(abs(te).mean()),
                T_RMSE_K=float(np.sqrt((te**2).mean())),
                mixture_y_MAE=float(abs(ye[1:-1]).mean()),
                mixture_T_MAE_K=float(abs(te[1:-1]).mean()),
            )
    minima = {key: binary.minimum_reflux(eq) for key, eq in curves.items()}
    reflux = 1.5 * max(minima.values())
    archived = load(case / "results/design.json")
    check_close(reflux, archived["specification"]["common_reflux_ratio"])
    designs, scans = [], []
    for (source, kind), eq in curves.items():
        result = binary.stages(eq, reflux)
        original = next(
            r
            for r in archived["results"]
            if r["source"] == source and r["interpolation"] == kind
        )
        for key in [
            "integer_equilibrium_stages_including_reboiler",
            "feed_stage_from_top",
        ]:
            check_close(result[key], original[key], 0)
        check_close(minima[source, kind], original["minimum_reflux_ratio"])
        designs.append(
            dict(
                source=source,
                interpolation=kind,
                minimum_reflux_ratio=minima[source, kind],
                **result,
            )
        )
        for factor in np.linspace(1.1, 3, 39):
            r = float(factor * max(minima.values()))
            scans.append(
                dict(
                    source=source,
                    interpolation=kind,
                    reflux_ratio=r,
                    equilibrium_stages=binary.stages(eq, r)[
                        "integer_equilibrium_stages_including_reboiler"
                    ],
                )
            )
    stored_scans = read_csv(case / "results/reflux_sensitivity.csv")
    if len(scans) != 234 or len(stored_scans) != 234:
        raise ValueError("Expected 234 reflux calculations")
    for row in scans:
        candidates = [
            r
            for r in stored_scans
            if r["source"] == row["source"]
            and r["interpolation"] == row["interpolation"]
        ]
        match = min(
            candidates,
            key=lambda r: abs(float(r["reflux_ratio"]) - row["reflux_ratio"]),
        )
        check_close(row["reflux_ratio"], float(match["reflux_ratio"]))
        check_close(row["equilibrium_stages"], int(match["equilibrium_stages"]), 0)
    result = dict(
        specification=archived["specification"],
        metrics=metrics,
        designs=designs,
        reflux_sensitivity=scans,
    )
    write(output / "binary_distillation.json", result)
    return dict(
        equilibrium_states=16, design_comparisons=6, reflux_calculations=len(scans)
    )


def column_case(output: Path) -> dict[str, Any]:
    case = ROOT / "cases/extractive_distillation"
    rows = read_csv(case / "data/equilibrium.csv")
    if len(rows) != 17:
        raise ValueError("Expected all 17 ternary VLE states")
    metrics = {}
    comp = ["alcohol", "ester", "DMF"]
    experimental_x = np.array([[float(r[f"x_{c}"]) for c in comp] for r in rows])
    for label in ["tf", "unifac"]:
        ye = np.array(
            [
                [float(r[f"y_{label}_{c}"]) - float(r[f"y_exp_{c}"]) for c in comp]
                for r in rows
            ]
        )
        te = np.array([float(r[f"T_{label}_K"]) - float(r["T_exp_K"]) for r in rows])
        alpha = np.array([float(r[f"alpha_{label}"]) for r in rows])
        alpha_exp = np.array([float(r["alpha_exp"]) for r in rows])
        metrics[label] = dict(
            y_MAE=float(abs(ye).mean()),
            T_MAE_K=float(abs(te).mean()),
            T_max_error_K=float(abs(te).max()),
            alpha_MAE=float(abs(alpha - alpha_exp).mean()),
            direction_agreement=int(np.sum((alpha > 1) == (alpha_exp > 1))),
        )
    summaries = []
    for name in ["thermoformer_182", "thermoformer_183", "unifac_183"]:
        record = load(case / "data" / f"{name}.json")
        x, y, temperature = [np.asarray(record[k]) for k in ["x", "y", "T"]]
        if (
            len(x) != record["N"]
            or x.shape != y.shape
            or len(temperature) != record["N"]
        ):
            raise ValueError("Missing stage states")
        for vector in np.r_[x, y]:
            composition(vector)
        feeds, liquid, vapor, bottoms = column.flows(
            record["N"],
            record["nf"],
            record["ns"],
            record["R"],
            record["S"],
            record["D"],
        )
        balance = feeds - liquid[:, None] * x - vapor * y
        balance[1:] += liquid[:-1, None] * x[:-1]
        balance[:-1] += vapor * y[1:]
        balance[0] += record["R"] * record["D"] * y[0]
        balance[-1] += (liquid[-1] - bottoms) * x[-1]
        maximum = float(abs(balance).max())
        check_close(maximum, 0, 1e-8)
        check_close(
            column.F * column.Z
            + record["S"] * np.array([0, 0, 1])
            - record["D"] * y[0]
            - bottoms * x[-1],
            0,
            1e-7,
        )
        purity = float(y[0, 1])
        recovery = float(record["D"] * purity / 0.5)
        check_close(purity, record["xD"][1])
        check_close(recovery, record["recovery"])
        check_close(y[0], record["xD"])
        check_close(x[-1], record["xB"])
        if name.startswith("thermoformer"):
            calculated_y = (
                x * np.asarray(record["gamma"]) * np.asarray(record["psat_kPa"]) / 101.3
            )
            check_close(calculated_y, y, 1e-8)
        outside_x = int(
            np.sum(Delaunay(experimental_x[:, :2]).find_simplex(x[:, :2]) < 0)
        )
        t_ref = [float(r["T_exp_K"]) for r in rows]
        outside_t = int(np.sum((temperature < min(t_ref)) | (temperature > max(t_ref))))
        summaries.append(
            dict(
                configuration=name,
                N=record["N"],
                feed_stage=record["nf"],
                solvent_stage=record["ns"],
                ester_purity=purity,
                ester_recovery=recovery,
                meets_targets=purity >= 0.995 and recovery >= 0.98,
                maximum_stage_balance_error_mol_s=maximum,
                stages_outside_experimental_composition_hull=outside_x,
                stages_outside_experimental_temperature_interval=outside_t,
            )
        )
    if [r["meets_targets"] for r in summaries] != [False, True, False]:
        raise ValueError("Stage-boundary/common-column result mismatch")
    if (
        metrics["tf"]["direction_agreement"] != 17
        or metrics["unifac"]["direction_agreement"] != 3
    ):
        raise ValueError("Volatility-direction comparison mismatch")
    if (
        summaries[1]["stages_outside_experimental_composition_hull"] != 183
        or summaries[1]["stages_outside_experimental_temperature_interval"] != 183
    ):
        raise ValueError("Experimental-coverage assessment mismatch")
    write(
        output / "extractive_distillation.json",
        dict(metrics=metrics, configurations=summaries),
    )
    return dict(
        equilibrium_states=17,
        column_configurations=3,
        stage_states=548,
        all_selected_stages_outside_experimental_coverage=True,
    )


def extraction_case(output: Path) -> dict[str, Any]:
    data = ROOT / "cases/crossflow_extraction/data"
    designs, stages, allocations, allocation_stages, scans = [
        load(data / f"{name}.json")
        for name in [
            "cascade_designs",
            "cascade_stages",
            "allocation_designs",
            "allocation_stages",
            "scan",
        ]
    ]
    pairs = load(data / "interpolation_protocol.json")["pairs_by_temperature"]
    all_states = stages + allocation_stages + scans
    result = dict(
        cascades=[], allocations=[], single_stage=[], interpolation_sensitivity=[]
    )

    def run(row: dict[str, Any], allocation: list[float]) -> dict[str, Any]:
        if row["status"] != "valid":
            raise ValueError("An archived case has no valid equilibrium result")
        if row["model"] == "Experiment-interpolation":

            def split(z):
                return experimental_split(np.asarray(pairs[str(row["T"])]), z)
        else:
            split = RecordedEndpoints(all_states, row["model"], row["T"])
        value = cascade(allocation, split)
        for metric in ["benzene_recovery", "heptane_retention"]:
            check_close(value[metric], row[metric], 1e-7)
        return dict(model=row["model"], T=row["T"], allocation=allocation, **value)

    for row in designs:
        result["cascades"].append(run(row, [row["total_S"] / row["N"]] * row["N"]))
    for row in allocations:
        result["allocations"].append(run(row, row["allocation"]))
    for row in scans:
        result["single_stage"].append(run(row, [row["S"]]))
    sensitivity = load(data / "reference_interpolation_sensitivity.json")
    for row in sensitivity:
        value = cascade(
            [1.5 / row["N"]] * row["N"],
            lambda z: experimental_split(np.asarray(pairs[str(row["T"])]), z, "pchip"),
        )
        for metric in ["benzene_recovery", "heptane_retention"]:
            check_close(value[metric], row[metric], 1e-7)
        result["interpolation_sensitivity"].append(
            dict(T=row["T"], N=row["N"], **value)
        )
    if [len(result[k]) for k in result] != [24, 66, 132, 4]:
        raise ValueError("Incomplete S5 study data")
    write(output / "crossflow_extraction.json", result)
    return dict(
        experimental_tie_lines=12,
        fixed_solvent_cascades=24,
        allocation_cases=66,
        single_stage_cases=132,
        interpolation_sensitivity_cases=4,
    )


def verify_manifest() -> None:
    manifest = load(ROOT / "checksums.json")
    for name, expected in manifest.items():
        path = ROOT / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Data checksum mismatch: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case", choices=["all", "binary", "extractive", "extraction"], default="all"
    )
    parser.add_argument("--output", type=Path, default=ROOT / "generated")
    args = parser.parse_args()
    verify_manifest()
    runners = dict(
        binary=binary_case, extractive=column_case, extraction=extraction_case
    )
    summary = {
        name: runner(args.output)
        for name, runner in runners.items()
        if args.case in ["all", name]
    }
    write(args.output / "verification.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
