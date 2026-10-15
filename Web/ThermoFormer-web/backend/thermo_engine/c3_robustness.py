"""Empirical relative-volatility stress ratings for the isolated C3 case.

The curves in this module are explicitly constructed sensitivity scenarios,
not new thermodynamic predictions, experimental records, or confidence bounds.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from thermo_engine.c3_design import C3DesignSpecification, C3EquilibriumCurve, product_flows, rate_column
from thermo_engine.paper_validation import validate_equilibrium_result

CALIBRATION_QUANTILE = 0.90
SCENARIO_SCOPE = "empirical_relative_volatility_scenario_not_a_thermodynamic_model"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def estimate_stress_scale(case_root: Path) -> dict[str, Any]:
    """Calibrate log-alpha scenario amplitude using development observations only.

    Observed and predicted y are compared at the same observed T and x; the
    prediction has its own bubble pressure. Thus this is an isothermal VLE
    selectivity discrepancy, not a fixed-(T,P) activity-parameter uncertainty.
    """
    path = case_root / "training" / "closed_equilibrium_predictions.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    development = [
        row
        for row in rows
        if row["model"] == "adapted_thermoformer" and row["partition"] in {"train", "validation"} and row["interior"]
    ]
    if not development:
        raise ValueError("No development mixture observations for C3 stress calibration")
    if any(not row["solver_returned"] or not row["validation"]["passed"] for row in development):
        raise ValueError("Development predictions must all pass their original numerical validation")
    residuals: list[float] = []
    records: list[dict[str, Any]] = []
    for row in development:
        observed, predicted = float(row["y_propene"]), float(row["predicted_y_propene"])
        liquid = float(row["x_propene"])
        if not all(math.isfinite(value) and 0 < value < 1 for value in (observed, predicted, liquid)):
            raise ValueError("Log-relative-volatility calibration requires finite interior compositions")
        residual = math.log(observed / (1 - observed)) - math.log(predicted / (1 - predicted))
        residuals.append(residual)
        records.append(
            {
                "source_csv_line": row["source_csv_line"],
                "partition": row["partition"],
                "temperature_k": row["temperature_k"],
                "x_propene": liquid,
                "observed_y_propene": observed,
                "predicted_y_propene": predicted,
                "log_alpha_observed_minus_predicted": residual,
            }
        )
    amplitude = float(np.quantile(np.abs(residuals), CALIBRATION_QUANTILE, method="linear"))
    if not math.isfinite(amplitude) or amplitude <= 0:
        raise ValueError("A positive empirical log-alpha discrepancy scale is required")
    return {
        "method": "development_absolute_log_relative_volatility_residual_quantile",
        "empirical_quantile": CALIBRATION_QUANTILE,
        "quantile_interpolation": "linear",
        "log_alpha_scale": amplitude,
        "one_scale_alpha_multiplier": math.exp(amplitude),
        "residual_signed_median": float(np.median(residuals)),
        "maximum_absolute_residual": float(np.max(np.abs(residuals))),
        "observations": len(records),
        "partitions_used": ["train", "validation"],
        "test_used_for_calibration": False,
        "pure_endpoints_used": False,
        "source_prediction_file": str(path.resolve()),
        "source_prediction_sha256": _digest(path),
        "records": records,
        "statistical_interpretation": "scenario amplitude only; not a confidence interval or reliability probability",
        "development_reuse": "same model fitting/early-stopping data; not an independent uncertainty estimate",
        "high_purity_transfer": "unvalidated extension of a global discrepancy scale into data-poor composition tails",
        "pressure_transfer": (
            "same scenario scale may be reused across pressures; pressure-specific uncertainty is not estimated"
        ),
    }


def _scenario_curve(curve: C3EquilibriumCurve, delta_log_alpha: float) -> C3EquilibriumCurve:
    """Build a numerically checked empirical curve; no fugacity closure is claimed."""
    y = np.asarray(curve.y_propene, dtype=float)
    shift = math.exp(delta_log_alpha)
    perturbed: NDArray[np.float64] = shift * y / (1.0 - y + shift * y)
    interior = (y > 0) & (y < 1)
    relation = np.log(perturbed[interior] / (1 - perturbed[interior])) - np.log(y[interior] / (1 - y[interior]))
    residual = float(np.max(np.abs(relation - delta_log_alpha)))
    checks = validate_equilibrium_result(np.c_[perturbed, 1 - perturbed], residual)
    # C3EquilibriumCurve's gate checks finite normalized compositions and a
    # numerical relation residual. Here that relation is the specified logit
    # shift, not a gamma-phi fugacity residual. Its source and result metadata
    # preserve this distinction explicitly.
    return C3EquilibriumCurve(
        pressure_kpa=curve.pressure_kpa,
        x_propene=list(curve.x_propene),
        y_propene=perturbed.tolist(),
        temperature_k=list(curve.temperature_k),
        maximum_equilibrium_residual=residual,
        source=f"{SCENARIO_SCOPE}; delta_log_alpha={delta_log_alpha:.17g}",
        point_validation_passed=bool(checks["passed"]),
    )


def relative_volatility_scenario_curve(curve: C3EquilibriumCurve, delta_log_alpha: float) -> C3EquilibriumCurve:
    """Expose an explicit empirical scenario for conservative construction.

    The returned y(x) relationship is shifted in log relative volatility.
    Temperatures are retained only as a nominal placeholder required by the
    existing curve container: they are not scenario bubble temperatures and
    must not be used for heat duties or thermal design. A constructed column
    still needs independent rating and direct review under the original model.
    """
    if not math.isfinite(delta_log_alpha) or abs(delta_log_alpha) > 1.0:
        raise ValueError("Require a finite log-alpha scenario shift within [-1, 1]")
    scenario = _scenario_curve(curve, delta_log_alpha)
    scenario.source += (
        "; physical_equilibrium_validation=not_applicable_to_scenario"
        "; temperatures=nominal_placeholder_not_for_heat_duty"
    )
    return scenario


def assess_candidate_robustness(
    curve: C3EquilibriumCurve,
    spec: C3DesignSpecification,
    candidate: dict[str, Any],
    calibration: dict[str, Any],
    multipliers: Sequence[float] = (-1.0, 0.0, 1.0),
) -> dict[str, Any]:
    """Rate fixed equipment under declared empirical log-alpha shifts.

    N, feed-stage position, R, P, feed and D/F are fixed in every scenario.
    No candidate redesign or interpretation as probabilistic robustness occurs.
    """
    amplitude = float(calibration["log_alpha_scale"])
    if not math.isfinite(amplitude) or amplitude <= 0 or calibration.get("test_used_for_calibration") is not False:
        raise ValueError("Require a finite positive development-only calibration scale")
    values = tuple(float(value) for value in multipliers)
    if not values or len(set(values)) != len(values) or not all(math.isfinite(value) for value in values):
        raise ValueError("Require unique finite nonempty scenario multipliers")
    if 0.0 not in values:
        raise ValueError("The nominal zero-shift scenario must be included")
    if max(abs(value * amplitude) for value in values) > 1.0:
        raise ValueError("Requested log-alpha shift exceeds the bounded diagnostic range")
    metrics = candidate["metrics"]
    stages, feed_stage = int(metrics["stages_including_reboiler"]), int(metrics["feed_stage_from_top"])
    reflux = float(metrics["reflux_ratio"])
    distillate, bottoms = product_flows(spec)
    for key, expected in (
        ("pressure_kpa", spec.pressure_kpa),
        ("distillate_flow_mol_s", distillate),
        ("bottoms_flow_mol_s", bottoms),
    ):
        if not math.isclose(float(metrics[key]), expected, rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError(f"Candidate {key} differs from the fixed rating specification")
    initial = list(candidate["profiles"]["x_propene"])
    scenarios: list[dict[str, Any]] = []
    for multiplier in values:
        delta = multiplier * amplitude
        scenario: dict[str, Any] = {
            "scale_multiplier": multiplier,
            "delta_log_alpha": delta,
            "relative_volatility_multiplier": math.exp(delta),
            "physical_equilibrium_validation": "not_applicable_to_scenario",
            "temperature_status": "not_recomputed; nominal temperature curve not used for thermal conclusions",
        }
        try:
            # Continuation changes only the numerical initial state. Large
            # positive shifts can drive upper trays very close to the pure
            # limit, where a direct jump from the nominal profile is fragile.
            step_count = max(1, int(math.ceil(abs(delta) / 0.0015)))
            warm_start = initial
            trace: list[dict[str, Any]] = []
            result: dict[str, Any] = {}
            for subdelta in np.linspace(0.0, delta, step_count + 1)[1:]:
                scenario_curve = relative_volatility_scenario_curve(curve, float(subdelta))
                result = rate_column(scenario_curve, spec, reflux, stages, feed_stage, warm_start)
                trace.append(
                    {
                        "delta_log_alpha": float(subdelta),
                        "numerically_validated": bool(result["numerical_checks"]["passed"]),
                        "stage_balance_residual": result["numerical_checks"]["stage_balance_residual"],
                        "overall_component_residual": result["numerical_checks"]["overall_component_residual"],
                    }
                )
                if not result["numerical_checks"]["passed"]:
                    scenario["continuation_trace"] = trace
                    raise RuntimeError("A continuation stage failed the numerical gate")
                warm_start = result["profiles"]["x_propene"]
            numerical = dict(result["numerical_checks"])
            numerical.update(
                equilibrium_relation="interpolated empirical y(x) scenario; not gamma-phi fugacity closure",
                physical_equilibrium_validation="not_applicable_to_scenario",
                temperature_passed=None,
                temperature_interpretation="nominal placeholder only; no scenario temperature solution",
            )
            clean_metrics = {key: value for key, value in result["metrics"].items() if "temperature" not in key}
            scenario.update(
                passed=bool(numerical["passed"] and result["meets_targets"]),
                numerically_validated=bool(numerical["passed"]),
                meets_targets=bool(result["meets_targets"]),
                metrics=clean_metrics,
                numerical_checks=numerical,
                continuation_trace=trace,
                composition_profiles={
                    "x_propene": result["profiles"]["x_propene"],
                    "y_propene": result["profiles"]["y_propene"],
                },
            )
        except (ValueError, RuntimeError, FloatingPointError) as error:
            scenario.update(
                passed=False,
                numerically_validated=False,
                meets_targets=False,
                failure=f"{type(error).__name__}: {error}",
            )
        scenarios.append(scenario)
    return {
        "solver_protocol": "continuation_v1",
        "maximum_continuation_step_log_alpha": 0.0015,
        "passed": all(row["passed"] for row in scenarios),
        "gate_definition": "both product targets and numerical checks pass in every specified scenario",
        "scope": SCENARIO_SCOPE,
        "probabilistic_reliability_claim": False,
        "confidence_interval": False,
        "empirical_quantile_is_not_reliability_probability": True,
        "scale": amplitude,
        "multipliers": list(values),
        "fixed_equipment": {
            "stages_including_reboiler": stages,
            "feed_stage_from_top": feed_stage,
            "reflux_ratio": reflux,
            "pressure_kpa": spec.pressure_kpa,
            "feed_flow_mol_s": spec.feed_flow_mol_s,
            "feed_propene": spec.feed_propene,
            "distillate_flow_mol_s": distillate,
            "bottoms_flow_mol_s": bottoms,
        },
        "scenarios": scenarios,
        "limitations": [
            "High-purity mixture coverage is sparse; the amplitude is not locally calibrated in those tails.",
            "Uniform relative-volatility shifts do not identify a physically consistent Gibbs-energy perturbation.",
            "No new vapor-fugacity, bubble-temperature, heat-duty, or phase-stability validation is implied.",
            "A pass establishes robustness only to the explicitly specified deterministic scenarios.",
        ],
    }
