"""Additive C3 pressure, utility and robustness screening; preserves the first case."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

from thermo_engine.c3_case_study import build_curve
from thermo_engine.c3_design import (
    C3DesignSpecification,
    C3DesignTools,
    C3EquilibriumCurve,
    construct_column,
    minimum_reflux,
    rate_column,
)
from thermo_engine.c3_thermodynamics import bubble_temperature, pr_reference_log_gamma, property_provenance
from thermo_engine.c3_thermoformer import BASE_SHA256, CASE_ROOT, C3ThermoFormer, file_sha256

DEFAULT_OUTPUT = CASE_ROOT / "engineering-20260928"
PRESSURES_KPA = (800.0, 1000.0, 1200.0, 1300.0, 1400.0, 1600.0)
MARGINS = {"original": (0.997, 0.009), "guarded": (0.9995, 0.003)}
FACTORS = {"r1p3": 1.3, "r1p5": 1.5, "r2p0": 2.0}


def content_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode("utf-8")).hexdigest()


def write_json(path: Path, value: Any) -> None:
    """Persist inspectable calculations without hiding failed states."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def load_model() -> tuple[C3ThermoFormer, dict[str, Any]]:
    torch = importlib.import_module("torch")
    torch.set_num_threads(1)
    training = CASE_ROOT / "training"
    features = training / "features/c3_model_features.npz"
    head = training / "c3_adapted_head.pt"
    model = C3ThermoFormer(features, head)
    signature = {
        "base_sha256": BASE_SHA256,
        "head_sha256": file_sha256(head),
        "features_sha256": file_sha256(features),
        "physics_sha256": file_sha256(Path(__file__).with_name("c3_thermodynamics.py")),
        "curve_grid_version": 1,
    }
    return model, signature


def make_tools(model: C3ThermoFormer, curve: C3EquilibriumCurve, spec: C3DesignSpecification) -> C3DesignTools:
    def direct(x: float) -> dict[str, Any]:
        state = bubble_temperature(spec.pressure_kpa, x, model.log_gamma)
        return {**state, "y_propene": state["y"][0], "temperature_k": state["T_K"]}

    return C3DesignTools(curve, spec, direct, {"thermodynamics": property_provenance()})


def scan_designs(output: Path) -> dict[str, Any]:
    """Freeze a finite exploratory grid, then calculate all candidates and failures."""
    model, signature = load_model()
    protocol = {
        "study_type": "exploratory_calculation_screen_not_confirmatory_trial",
        "pressure_unit": "kPa_absolute",
        "pressures_kpa": list(PRESSURES_KPA),
        "nominal_product_margins": MARGINS,
        "reflux_factors": FACTORS,
        "fixed_user_feed_propene": 0.35,
        "fixed_user_product_targets": {"top_propene_minimum": 0.996, "bottom_propene_exclusive_maximum": 0.01},
        "assumptions": {
            "feed_flow_basis_mol_s": 1.0,
            "feed_quality": 1,
            "constant_molar_overflow": True,
            "total_condenser": True,
            "equilibrium_reboiler": True,
            "pressure_drop_kpa": 0,
            "coolant_scenarios_celsius": [[10, 15], [25, 30]],
            "minimum_terminal_temperature_difference_k": 5,
        },
        "uncertainty_protocol": "development-only empirical log-alpha scenario; not probability coverage",
        "selection": "finite candidate engineering screening; no global or economic optimality",
        "thermoformer_retrained_for_this_extension": False,
        "previous_case_directory": str(CASE_ROOT / "design"),
        "previous_case_is_not_overwritten": True,
        "model_signature": signature,
        "design_module_sha256": file_sha256(Path(__file__).with_name("c3_design.py")),
    }
    protocol_path = output / "protocol.json"
    if protocol_path.exists():
        if json.loads(protocol_path.read_text(encoding="utf-8")) != json.loads(json.dumps(protocol)):
            raise ValueError("Existing protocol differs; use a fresh output directory")
    else:
        write_json(protocol_path, protocol)
    records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for pressure in PRESSURES_KPA:
        folder = output / f"p{int(pressure)}"
        folder.mkdir(parents=True, exist_ok=True)
        try:
            curve, _ = build_curve(
                model.log_gamma,
                "adapted_ThermoFormer_gamma_phi",
                folder / "curve.json",
                {**signature, "pressure_kpa": pressure},
                pressure,
            )
        except ValueError as error:
            failure = {
                "pressure_kpa": pressure,
                "status": "outside_available_equilibrium_support_or_failed",
                "reason": str(error),
                "code": getattr(error, "code", "curve_validation_failed"),
                "interpretation": "not proof that this pressure is physically infeasible",
            }
            write_json(folder / "failure.json", failure)
            failures.append(failure)
            print(json.dumps(failure), flush=True)
            continue
        for margin, (xd, xb) in MARGINS.items():
            spec = C3DesignSpecification(
                pressure_kpa=pressure, nominal_distillate_propene=xd, nominal_bottoms_propene=xb
            )
            numerical_tools = make_tools(model, curve, spec)
            numerical_tools.factors = FACTORS.copy()
            for action in FACTORS:
                identity = f"p{int(pressure)}_{margin}_{action}"
                path = folder / f"{identity}.json"
                if path.exists():
                    record = json.loads(path.read_text(encoding="utf-8"))
                else:
                    candidate = numerical_tools.execute(action)
                    record = {
                        "candidate_id": identity,
                        "pressure_kpa": pressure,
                        "margin": margin,
                        "reflux_factor": FACTORS[action],
                        "specification": spec.model_dump(),
                        "curve_path": str(folder / "curve.json"),
                        "candidate": candidate,
                        "calculation_origin": "deterministic_precomputed_grid_not_LLM_search",
                    }
                    write_json(path, record)
                records.append(record)
                print(json.dumps({"candidate": identity, "status": record["candidate"]["status"]}), flush=True)
    result = {"protocol": protocol, "records": records, "pressure_failures": failures}
    write_json(output / "scan.json", result)
    return result


def export_flat_table(records: list[dict[str, Any]], path: Path) -> None:
    rows = []
    for record in records:
        row = {
            "candidate_id": record["candidate_id"],
            "margin": record["margin"],
            "pressure_kpa": record["pressure_kpa"],
            "reflux_factor": record["reflux_factor"],
            "status": record["candidate"]["status"],
            "meets_targets": record["candidate"]["meets_targets"],
            "direct_numerical_verified": record["candidate"]["verified"],
            **record["candidate"]["metrics"],
        }
        rows.append(row)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def screen_robustness(output: Path) -> dict[str, Any]:
    """Keep unchanged equipment while screening prespecified volatility scenarios."""
    from thermo_engine.c3_robustness import assess_candidate_robustness, estimate_stress_scale

    scan = json.loads((output / "scan.json").read_text(encoding="utf-8"))
    if (output / "scenario_designs.json").exists():
        scan["records"].extend(json.loads((output / "scenario_designs.json").read_text(encoding="utf-8"))["records"])
    calibration = estimate_stress_scale(CASE_ROOT)
    write_json(output / "stress_calibration.json", calibration)
    results = {}
    for record in scan["records"]:
        identity = record["candidate_id"]
        if record["candidate"]["status"] != "valid":
            continue
        path = output / "reviews" / identity / "robustness.json"
        dependencies = {
            "candidate_sha256": content_digest(record["candidate"]),
            "curve_sha256": file_sha256(Path(record["curve_path"])),
            "calibration_sha256": content_digest(calibration),
            "robustness_module_sha256": file_sha256(Path(__file__).with_name("c3_robustness.py")),
            "rating_module_sha256": file_sha256(Path(__file__).with_name("c3_design.py")),
        }
        if path.exists():
            result = json.loads(path.read_text(encoding="utf-8"))
        else:
            result = {}
        if result.get("solver_protocol") != "continuation_v1" or result.get("cache_dependencies") != dependencies:
            if result:
                previous = path.with_name("robustness_previous_" + content_digest(result)[:12] + ".json")
                if not previous.exists():
                    write_json(previous, result)
            stored = json.loads(Path(record["curve_path"]).read_text(encoding="utf-8"))
            curve = C3EquilibriumCurve.model_validate(stored["curve"])
            spec = C3DesignSpecification.model_validate(record["specification"])
            result = assess_candidate_robustness(curve, spec, record["candidate"], calibration)
            result["cache_dependencies"] = dependencies
            write_json(path, result)
        results[identity] = result
        worst = result["scenarios"][0].get("metrics", {})
        print(
            json.dumps(
                {
                    "candidate": identity,
                    "scenario_pass": result["passed"],
                    "worst_top": worst.get("distillate_propene_mole_fraction"),
                    "worst_bottom": worst.get("bottoms_propene_mole_fraction"),
                }
            ),
            flush=True,
        )
    write_json(output / "robustness_summary.json", results)
    return results


def construct_scenario_designs(output: Path) -> dict[str, Any]:
    """Respond to observed sensitivity with a clearly labelled second design round.

    The conservative scenario constructs equipment; the actual predictions and
    temperatures come from a subsequent independent original-ThermoFormer rating.
    """
    from thermo_engine.c3_robustness import estimate_stress_scale, relative_volatility_scenario_curve

    calibration = estimate_stress_scale(CASE_ROOT)
    amplitude = float(calibration["log_alpha_scale"])
    protocol = {
        "round": 2,
        "trigger": "round-one nominal and tightened-purity designs failed the negative development-scale scenario",
        "exploratory_adaptation_after_round_one": True,
        "construction_relation": "nominal y(x) logit shifted by minus one empirical development discrepancy scale",
        "scenario_is_not_new_experimental_data_or_physical_model": True,
        "log_alpha_shift": -amplitude,
        "nominal_specification": C3DesignSpecification().model_dump(),
        "reflux_factors_relative_to_scenario_minimum": FACTORS,
        "prediction_relation": "independent rating with original adapted ThermoFormer curve",
        "temperature_and_utility_source": "original adapted ThermoFormer, never scenario placeholder temperatures",
        "test_used_for_design": False,
    }
    write_json(output / "scenario_design_protocol.json", protocol)
    scan = json.loads((output / "scan.json").read_text(encoding="utf-8"))
    by_pressure = {record["pressure_kpa"]: record["curve_path"] for record in scan["records"]}
    records: list[dict[str, Any]] = []
    for pressure, curve_path in by_pressure.items():
        curve = C3EquilibriumCurve.model_validate(json.loads(Path(curve_path).read_text(encoding="utf-8"))["curve"])
        conservative = relative_volatility_scenario_curve(curve, -amplitude)
        spec = C3DesignSpecification(pressure_kpa=pressure)
        conservative_rmin = minimum_reflux(conservative, spec)
        for action, factor in FACTORS.items():
            identity = f"p{int(pressure)}_scenario_{action}"
            path = output / f"p{int(pressure)}" / f"{identity}.json"
            if path.exists():
                record = json.loads(path.read_text(encoding="utf-8"))
            else:
                reflux = factor * conservative_rmin
                estimate = construct_column(conservative, spec, reflux)
                # Continue from the construction scenario to the physical curve
                # without changing N, feed location, reflux or the product split.
                import numpy as np

                initial = estimate["initial_x_profile"]
                rating: dict[str, Any] = {}
                nominal_trace = []
                for delta in np.linspace(-amplitude, 0, 21):
                    relation = curve if delta == 0 else relative_volatility_scenario_curve(curve, float(delta))
                    rating = rate_column(
                        relation,
                        spec,
                        reflux,
                        estimate["stages_including_reboiler"],
                        estimate["feed_stage_from_top"],
                        initial,
                    )
                    nominal_trace.append({"delta_log_alpha": float(delta), "checks": rating["numerical_checks"]})
                    if not rating["numerical_checks"]["passed"]:
                        break
                    initial = rating["profiles"]["x_propene"]
                physically_rated = nominal_trace[-1]["delta_log_alpha"] == 0
                candidate = {
                    **rating,
                    "status": "valid" if physically_rated and rating["numerical_checks"]["passed"] else "failed",
                    "candidate_id": identity,
                    "verified": False,
                    "evidence_gaps": ["direct stage equilibrium review pending"],
                    "limitations": C3DesignTools._limitations(),
                    "minimum_reflux_ratio": minimum_reflux(curve, spec),
                    "construction_scenario_minimum_reflux_ratio": conservative_rmin,
                }
                record = {
                    "candidate_id": identity,
                    "pressure_kpa": pressure,
                    "margin": "scenario",
                    "reflux_factor": factor,
                    "specification": spec.model_dump(),
                    "curve_path": curve_path,
                    "candidate": candidate,
                    "construction": {"scenario_delta_log_alpha": -amplitude, "continuation": nominal_trace},
                    "calculation_origin": "adaptive_deterministic_second_round_not_LLM_search",
                }
                write_json(path, record)
            records.append(record)
            print(
                json.dumps(
                    {
                        "candidate": identity,
                        "status": record["candidate"]["status"],
                        "N": record["candidate"]["metrics"].get("stages_including_reboiler"),
                    }
                ),
                flush=True,
            )
    result = {"protocol": protocol, "records": records}
    write_json(output / "scenario_designs.json", result)
    return result


def all_records(output: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = json.loads((output / "scan.json").read_text(encoding="utf-8"))["records"]
    extra = output / "scenario_designs.json"
    if extra.exists():
        records.extend(json.loads(extra.read_text(encoding="utf-8"))["records"])
    return records


def screen_utilities(output: Path) -> dict[str, Any]:
    """Estimate local PR duties at validated TF states and screen two cold sources."""
    from thermo_engine.c3_utilities import assess_c3_utilities

    model, _ = load_model()
    results = {}
    module_digest = file_sha256(Path(__file__).with_name("c3_utilities.py"))
    for record in all_records(output):
        identity = record["candidate_id"]
        if record["candidate"]["status"] != "valid":
            continue
        path = output / "reviews" / identity / "utilities.json"
        dependencies = {
            "candidate_sha256": content_digest(record["candidate"]),
            "specification_sha256": content_digest(record["specification"]),
            "utilities_module_sha256": module_digest,
            "thermodynamics_module_sha256": file_sha256(Path(__file__).with_name("c3_thermodynamics.py")),
            "head_sha256": file_sha256(CASE_ROOT / "training/c3_adapted_head.pt"),
        }
        result = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        if result.get("cache_dependencies") != dependencies:
            spec = C3DesignSpecification.model_validate(record["specification"])
            result = assess_c3_utilities(record["candidate"], spec, model.log_gamma).model_dump()
            result["calculation_module_sha256"] = module_digest
            result["cache_dependencies"] = dependencies
            write_json(path, result)
        results[identity] = result
        print(
            json.dumps(
                {
                    "candidate": identity,
                    "utility_status": result["status"],
                    "cold_sources": [row["endpoint_screen_passed"] for row in result["cooling_scenarios"]],
                    "reboiler_duty_w": (result.get("reboiler") or {}).get("duty_w"),
                }
            ),
            flush=True,
        )
    write_json(output / "utilities_summary.json", results)
    return results


def is_cold_source_supported(utilities: dict[str, Any]) -> bool:
    return bool(
        utilities.get("validation", {}).get("passed")
        and any(
            row["scenario"]["name"] == "water_10_to_15C" and row["endpoint_screen_passed"]
            for row in utilities.get("cooling_scenarios", [])
        )
    )


def attach_review_evidence(record: dict[str, Any], directory: Path) -> None:
    """Retain failed calculations even when no downstream review files exist."""
    for field in ("utilities", "robustness"):
        path = directory / f"{field}.json"
        if path.exists():
            record[field] = json.loads(path.read_text(encoding="utf-8"))
        else:
            record[field] = {
                "status": "not_evaluated",
                "passed": False,
                "validation": {"passed": False},
                "reason": "upstream candidate invalid or review evidence missing",
            }


def nondominated_candidates(records: list[dict[str, Any]]) -> list[str]:
    """Finite screening front in equilibrium-stage count and estimated PR Qr."""
    supported = [
        row
        for row in records
        if row["candidate"]["status"] == "valid"
        and row["candidate"]["meets_targets"]
        and row["robustness"]["passed"]
        and is_cold_source_supported(row["utilities"])
    ]

    def coordinates(row: dict[str, Any]) -> tuple[int, float]:
        return int(row["candidate"]["metrics"]["stages_including_reboiler"]), float(
            row["utilities"]["reboiler"]["duty_w"]
        )

    result = []
    for row in supported:
        n, duty = coordinates(row)
        dominated = any(
            other["candidate_id"] != row["candidate_id"]
            and coordinates(other)[0] <= n
            and coordinates(other)[1] <= duty
            and (coordinates(other)[0] < n or coordinates(other)[1] < duty)
            for other in supported
        )
        if not dominated:
            result.append(row["candidate_id"])
    return result


def verify_frontier(output: Path) -> dict[str, Any]:
    """Directly review finite engineering finalists, with independent legacy evidence."""
    from thermo_engine.c3_robustness import assess_candidate_robustness, estimate_stress_scale
    from thermo_engine.c3_utilities import assess_c3_utilities

    existing = output / "engineering_summary.json"
    if existing.exists() and json.loads(existing.read_text(encoding="utf-8")).get("agent_result"):
        raise FileExistsError("Completed Agent evidence exists; use a new directory for fresh numerical work")
    model, signature = load_model()
    calibration = estimate_stress_scale(CASE_ROOT)
    records = all_records(output)
    for record in records:
        directory = output / "reviews" / record["candidate_id"]
        attach_review_evidence(record, directory)
    frontier = nondominated_candidates(records)
    legacy_id = "p1000_original_r1p3"
    write_json(
        output / "frontier_protocol.json",
        {
            "candidate_ids": frontier,
            "objectives": ["equilibrium_stage_count", "local_PR_reboiler_duty_estimate"],
            "constraints": ["nominal_targets", "development_scale_scenarios", "water_10_to_15C_endpoint_screen"],
            "interpretation": "finite screening Pareto set; not economic optimization or full MESH energy ranking",
        },
    )
    for record in records:
        identity = record["candidate_id"]
        if identity not in frontier and identity != legacy_id:
            continue
        directory = output / "reviews" / identity
        path = directory / "verified_candidate.json"
        spec = C3DesignSpecification.model_validate(record["specification"])
        curve = C3EquilibriumCurve.model_validate(
            json.loads(Path(record["curve_path"]).read_text(encoding="utf-8"))["curve"]
        )
        if path.exists():
            candidate = json.loads(path.read_text(encoding="utf-8"))
        elif identity == legacy_id:
            legacy_path = CASE_ROOT / "design/candidate_archive.json"
            candidate = json.loads(legacy_path.read_text(encoding="utf-8"))["design_r1p3"]
            candidate["candidate_id"] = identity
            candidate["reused_verified_numerical_evidence"] = {
                "path": str(legacy_path),
                "sha256": file_sha256(legacy_path),
                "original_candidate_id": "design_r1p3",
                "reuse_scope": "same frozen weights, pressure, feed, equipment and targets",
            }
            write_json(path, candidate)
        else:
            tools = make_tools(model, curve, spec)
            tools.archive[identity] = record["candidate"]
            candidate = tools.execute("verify:" + identity)
            write_json(path, candidate)
        record["candidate"] = candidate
        record["utilities"] = assess_c3_utilities(candidate, spec, model.log_gamma).model_dump()
        record["robustness"] = assess_candidate_robustness(curve, spec, candidate, calibration)
        write_json(directory / "utilities_after_verification.json", record["utilities"])
        write_json(directory / "robustness_after_verification.json", record["robustness"])
        print(json.dumps({"verified": identity, "passed": candidate["verified"]}), flush=True)
    summary = {
        "scope": "engineering_screening_no_process_experiments_no_industrial_certification",
        "records": records,
        "pressure_failures": json.loads((output / "scan.json").read_text(encoding="utf-8"))["pressure_failures"],
        "frontier_candidate_ids": frontier,
        "frontier_after_direct_review": nondominated_candidates(records),
        "frontier_unchanged_after_direct_review": nondominated_candidates(records) == frontier,
        "baseline_candidate_id": legacy_id,
        "selected_candidate_id": None,
        "agent_result": None,
        "model_signature": signature,
        "calibration_file": str(output / "stress_calibration.json"),
    }
    write_json(output / "engineering_summary.json", summary)
    export_flat_table(records, output / "all_candidates.csv")
    return summary


def prepare_agent_records(summary: dict[str, Any], output: Path = DEFAULT_OUTPUT) -> list[dict[str, Any]]:
    """Keep concise numerical evidence, with explicit scope for every gate."""
    selected_ids = [summary["baseline_candidate_id"], *summary["frontier_candidate_ids"]]
    records = []
    for row in summary["records"]:
        if row["candidate_id"] not in selected_ids:
            continue
        candidate, utilities, robustness = row["candidate"], row["utilities"], row["robustness"]
        diagnostic = utilities.get("whole_column_energy_diagnostic") or {}
        compact_utilities = {
            "passed": utilities["validation"]["passed"],
            "status": utilities["status"],
            "condenser_duty_w": (utilities.get("condenser") or {}).get("duty_w"),
            "reboiler_duty_w": (utilities.get("reboiler") or {}).get("duty_w"),
            "cooling_scenarios": utilities["cooling_scenarios"],
            "whole_column_relative_energy_discrepancy": diagnostic.get("absolute_discrepancy_relative_to_larger_duty"),
            "full_MESH_energy_solution": False,
            "thermoformer_caloric_consistency": False,
            "limitations": utilities["limitations"],
        }
        compact_robustness = {
            key: robustness[key]
            for key in ("passed", "scope", "scale", "multipliers", "probabilistic_reliability_claim", "limitations")
        }
        compact_robustness["scenarios"] = [
            {key: value for key, value in scenario.items() if key not in {"composition_profiles", "continuation_trace"}}
            for scenario in robustness["scenarios"]
        ]
        limits = [
            "No real process experiment or industrial certification; high-purity mixed VLE is sparsely covered.",
            "No full MESH solution, tray efficiency, pressure drop, column diameter, compressor or economics.",
            "PR local duty is a screening estimate, not a ThermoFormer-consistent caloric model or energy optimum.",
            "Cold-source availability is assumed; only declared endpoint temperature differences were screened.",
            "Robustness covers declared deterministic development-residual scenarios, not a probability guarantee.",
            "Computational applicability means registered T/P domain; global phase stability is not certified.",
            "ChemSep binary parameter validity-range metadata are incomplete.",
            "The complete pressure/design scan was deterministic and precomputed, not performed by this LLM.",
        ]
        records.append(
            {
                "candidate_id": row["candidate_id"],
                "pressure_kpa": float(row["pressure_kpa"]),
                "metrics": {
                    **candidate["metrics"],
                    "local_PR_reboiler_duty_estimate_w": compact_utilities["reboiler_duty_w"],
                    "local_PR_condenser_duty_estimate_w": compact_utilities["condenser_duty_w"],
                },
                "meets_targets": bool(candidate["meets_targets"]),
                "direct_numerical_verified": bool(candidate["verified"]),
                "utilities": compact_utilities,
                "cold_source_feasible": is_cold_source_supported(utilities),
                "robustness": compact_robustness,
                "applicability": {
                    "passed": bool(candidate["status"] == "valid" and candidate["numerical_checks"]["passed"]),
                    "scope": "nominal computational T/P domain only; no experimental accuracy certification",
                    "global_phase_stability": "not_certified",
                    "binary_parameter_range_metadata": "incomplete",
                },
                "evidence_limits": limits,
                "source": {
                    "calculation_origin": row["calculation_origin"],
                    "original_verified_evidence_reused": "reused_verified_numerical_evidence" in candidate,
                    "record_directory": str(output / "reviews" / row["candidate_id"]),
                },
            }
        )
    return records


def run_final_review(output: Path, *, live: bool, attempt: int = 1) -> dict[str, Any]:
    """Record an actual LLM evidence review, after all numerical work is explicit."""
    from paper_agent.c3_engineering_review import run_engineering_review
    from thermo_engine.c3_utilities import screen_heating_water

    path = output / "engineering_summary.json"
    summary: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    for row in summary["records"]:
        reboiler = row["utilities"].get("reboiler")
        if reboiler:
            enthalpies = reboiler["enthalpy_states"]
            row["heating"] = screen_heating_water(
                enthalpies["liquid_in"]["temperature_k"],
                enthalpies["bottoms_out"]["temperature_k"],
                reboiler["duty_w"],
            ).model_dump()
    candidates = prepare_agent_records(summary, output)
    write_json(output / "agent_candidate_records.json", candidates)
    suffix = "" if attempt == 1 else f"_attempt{attempt}"
    target = output / (f"agent_engineering_review{suffix}.json" if live else "agent_engineering_review_preflight.json")
    if target.exists():
        result = json.loads(target.read_text(encoding="utf-8"))
    else:
        result = run_engineering_review(
            candidates,
            output_path=target,
            live=live,
            max_actions=12,
            request=(
                "Review the supplied original C3 candidate and finite screening Pareto alternatives. "
                "The full deterministic scan and conservative scenario redesign were precomputed separately. "
                "First compare all supplied candidates. Retain the original as a negative-control evidence row. "
                "For a preliminary report require direct numerical validation, both purity targets, declared "
                "10-to-15 degC water endpoint feasibility and all specified volatility scenarios. Among eligible "
                "candidates prefer the smaller local PR reboiler-duty estimate, acknowledging the stage-count "
                "tradeoff and that this is not a rigorous energy or economic optimum. Read utility and robustness "
                "evidence before reporting. Preserve every limitation and defer if the evidence "
                "does not support a report."
            ),
        )
    if live:
        summary["agent_result"] = result
        summary["selected_candidate_id"] = result.get("selected_candidate_id")
        attempts = []
        for history_path in sorted(output.glob("agent_engineering_review*.json")):
            history = json.loads(history_path.read_text(encoding="utf-8"))
            if history.get("live_requested"):
                attempts.append(
                    {
                        "path": str(history_path),
                        "sha256": file_sha256(history_path),
                        "outcome": history["outcome"],
                        "error": history.get("error"),
                        "llm_calls": history["llm_calls"],
                        "llm_tokens": history["llm_tokens"],
                        "selected_candidate_id": history.get("selected_candidate_id"),
                    }
                )
        summary["agent_attempts"] = attempts
    summary["heating_scenario_status"] = "separate_preliminary_60_to_50C_sensible_water_screen"
    write_json(path, summary)
    print(
        json.dumps(
            {
                "outcome": result["outcome"],
                "selected": result.get("selected_candidate_id"),
                "llm_calls": result["llm_calls"],
            }
        ),
        flush=True,
    )
    return summary


def compare_reference(output: Path) -> dict[str, Any]:
    """Same-configuration PR rating, kept outside the LLM acceptance evidence."""
    summary_path = output / "engineering_summary.json"
    summary: dict[str, Any] = json.loads(summary_path.read_text(encoding="utf-8"))
    comparisons = {}
    for row in summary["records"]:
        identity = row["candidate_id"]
        if identity not in summary["frontier_candidate_ids"]:
            continue
        spec = C3DesignSpecification.model_validate(row["specification"])
        signature = {
            "thermodynamics": property_provenance(),
            "pressure_kpa": spec.pressure_kpa,
            "model": "separate_PR_comparator_not_ThermoFormer",
        }
        curve, _ = build_curve(
            pr_reference_log_gamma,
            "separate_PR_comparator",
            output / f"p{int(spec.pressure_kpa)}" / "reference_curve.json",
            signature,
            spec.pressure_kpa,
        )
        candidate = row["candidate"]
        metrics = candidate["metrics"]
        reference = rate_column(
            curve,
            spec,
            metrics["reflux_ratio"],
            metrics["stages_including_reboiler"],
            metrics["feed_stage_from_top"],
            candidate["profiles"]["x_propene"],
        )
        comparison = {
            "candidate_id": identity,
            "reference": reference,
            "all_equipment_operating_conditions_and_product_split_fixed": True,
            "agent_received_this_comparison": False,
            "interpretation": "interpolated validated PR states; a reference calculation, not independent experiment",
        }
        write_json(output / "reviews" / identity / "same_column_PR.json", comparison)
        comparisons[identity] = comparison
        print(json.dumps({"PR_candidate": identity, "meets_targets": reference["meets_targets"]}), flush=True)
    summary["reference_comparisons"] = comparisons
    write_json(summary_path, summary)
    return comparisons


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--phase",
        choices=("scan", "robustness", "scenario-design", "utilities", "verify", "review", "reference"),
        default="scan",
    )
    parser.add_argument("--live", action="store_true", help="Explicitly run the real LLM for the review phase")
    parser.add_argument("--attempt", type=int, choices=range(1, 6), default=1)
    args = parser.parse_args()
    if args.phase == "scan":
        result = scan_designs(args.output)
        export_flat_table(result["records"], args.output / "candidate_table.csv")
    elif args.phase == "robustness":
        screen_robustness(args.output)
    elif args.phase == "scenario-design":
        construct_scenario_designs(args.output)
    elif args.phase == "utilities":
        screen_utilities(args.output)
    elif args.phase == "verify":
        verify_frontier(args.output)
    elif args.phase == "review":
        run_final_review(args.output, live=args.live, attempt=args.attempt)
    else:
        compare_reference(args.output)


if __name__ == "__main__":
    main()
