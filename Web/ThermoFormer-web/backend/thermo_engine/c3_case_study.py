"""Reproducible isolated C3 calculation case using the adapted ThermoFormer."""

from __future__ import annotations

import argparse
import csv
import importlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from thermo_engine.c3_design import C3DesignSpecification, C3DesignTools, C3EquilibriumCurve, rate_column
from thermo_engine.c3_thermodynamics import bubble_temperature, pr_reference_log_gamma, property_provenance
from thermo_engine.c3_thermoformer import BASE_CHECKPOINT, BASE_SHA256, CASE_ROOT, C3ThermoFormer, file_sha256


def build_curve(
    callback: Any, source: str, destination: Path, signature: dict[str, Any], pressure_kpa: float
) -> tuple[C3EquilibriumCurve, dict[str, Any]]:
    """Cache only exactly matching, explicitly validated curve calculations."""
    if destination.exists():
        stored = json.loads(destination.read_text(encoding="utf-8"))
        if stored["signature"] != signature:
            raise ValueError("Existing C3 curve has a different signature; use a new output directory")
        return C3EquilibriumCurve.model_validate(stored["curve"]), stored
    tail = np.geomspace(0.0001, 0.1, 25)
    xs = np.unique(np.r_[0, tail, np.linspace(0.1, 0.9, 61), 1 - tail, 1, 0.009, 0.01, 0.35, 0.996, 0.997])
    states = []
    for index, x in enumerate(xs):
        states.append(bubble_temperature(pressure_kpa, float(x), callback))
        if (index + 1) % 25 == 0:
            print(f"{source}: validated {index + 1}/{len(xs)} curve states", flush=True)
    curve = C3EquilibriumCurve(
        pressure_kpa=pressure_kpa,
        x_propene=xs.tolist(),
        y_propene=[row["y"][0] for row in states],
        temperature_k=[row["T_K"] for row in states],
        maximum_equilibrium_residual=max(row["equilibrium_residual"] for row in states),
        point_validation_passed=all(row["validation"]["passed"] for row in states),
        source=source,
    )
    stored = {"signature": signature, "curve": curve.model_dump(), "states": states}
    destination.write_text(json.dumps(stored, indent=2), encoding="utf-8")
    return curve, stored


def run_case(output: Path, *, run_agent: bool = True) -> dict[str, Any]:
    """Run numerical tools and a real, separately recorded LLM controller."""
    torch = importlib.import_module("torch")

    from paper_agent.c3_case import run_c3_case

    torch.set_num_threads(1)
    output.mkdir(parents=True, exist_ok=True)
    training = CASE_ROOT / "training"
    feature_path = training / "features/c3_model_features.npz"
    head_path = training / "c3_adapted_head.pt"
    model = C3ThermoFormer(feature_path, head_path)
    spec = C3DesignSpecification()
    physics_file = Path(__file__).with_name("c3_thermodynamics.py")
    signature = {
        "base_sha256": BASE_SHA256,
        "head_sha256": file_sha256(head_path),
        "features_sha256": file_sha256(feature_path),
        "physics_sha256": file_sha256(physics_file),
        "pressure_kpa": spec.pressure_kpa,
        "curve_grid_version": 1,
    }
    curve, _ = build_curve(
        model.log_gamma, "adapted_ThermoFormer_gamma_phi", output / "tf_curve.json", signature, spec.pressure_kpa
    )
    reference_signature = {**signature, "model": "unfitted_PR_comparator_not_ThermoFormer"}
    reference_curve, _ = build_curve(
        pr_reference_log_gamma, "PR_reference", output / "pr_curve.json", reference_signature, spec.pressure_kpa
    )
    physics = property_provenance()
    (output / "property_provenance.json").write_text(json.dumps(physics, indent=2), encoding="utf-8")

    def direct(x: float) -> dict[str, Any]:
        state = bubble_temperature(spec.pressure_kpa, x, model.log_gamma)
        return {
            **state,
            "y_propene": state["y"][0],
            "temperature_k": state["T_K"],
        }

    tools = C3DesignTools(curve, spec, direct, {"model": signature, "thermodynamics": physics})
    agent_result: dict[str, Any] | None = None
    if run_agent:
        path = output / "agent_trajectory.json"
        if path.exists():
            raise FileExistsError("A live Agent trajectory already exists; use a new directory for another run")
        print("Starting real LLM candidate-selection and review loop", flush=True)
        agent_result = run_c3_case(tools, output_path=path, max_actions=6)
        print("Agent loop completed: " + str(agent_result.get("disposition", agent_result.get("outcome"))), flush=True)
    # Supplementary deterministic scan is separate from, and occurs after, the
    # recorded Agent run. Its uncalled results were not provided to the LLM.
    for action_id in tools.factors:
        if action_id not in tools.archive:
            tools.execute(action_id)
    (output / "candidate_archive.json").write_text(json.dumps(tools.archive, indent=2), encoding="utf-8")
    rows = [
        {
            "candidate_id": key,
            "status": value["status"],
            "meets_targets": value["meets_targets"],
            "numerically_reviewed": value["verified"],
            **value["metrics"],
        }
        for key, value in tools.archive.items()
    ]
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with (output / "candidate_scan.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    assessment = tools.assess()
    selected_id = assessment["preferred_candidate_id"]
    comparison: dict[str, Any] | None = None
    if selected_id is not None:
        retained = tools.archive[selected_id]
        metrics = retained["metrics"]
        comparison = rate_column(
            reference_curve,
            spec,
            metrics["reflux_ratio"],
            metrics["stages_including_reboiler"],
            metrics["feed_stage_from_top"],
            retained["profiles"]["x_propene"],
        )
        (output / "same_column_pr_comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    integrity: dict[str, Any] = {
        "original_checkpoint_sha256": file_sha256(BASE_CHECKPOINT),
        "expected_sha256": BASE_SHA256,
    }
    integrity["original_checkpoint_unchanged"] = integrity["original_checkpoint_sha256"] == BASE_SHA256
    summary = {
        "scope": "calculation_case_no_process_experiments",
        "specification": spec.model_dump(),
        "selected_candidate_id": selected_id,
        "assessment": assessment,
        "live_agent_run": run_agent,
        "agent_disposition": None if agent_result is None else agent_result.get("disposition"),
        "supplementary_scan_was_after_agent_run": True,
        "same_column_pr_comparison": None
        if comparison is None
        else {
            "metrics": comparison["metrics"],
            "meets_targets": comparison["meets_targets"],
            "numerical_checks": comparison["numerical_checks"],
            "interpretation": "Separate sourced thermodynamic comparator, not independent process measurements",
        },
        "integrity": integrity,
    }
    (output / "case_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(
        json.dumps({"selected": selected_id, "original_unchanged": integrity["original_checkpoint_unchanged"]}),
        flush=True,
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=CASE_ROOT / "design")
    parser.add_argument(
        "--no-agent", action="store_true", help="Explicit numerical-only diagnostic; no LLM is substituted"
    )
    args = parser.parse_args()
    run_case(args.output, run_agent=not args.no_agent)


if __name__ == "__main__":
    main()
