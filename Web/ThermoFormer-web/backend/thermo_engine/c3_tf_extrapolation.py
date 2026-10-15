"""Opt-in C3 ThermoFormer extrapolation experiment; never a production override."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq, root
from scipy.special import expit, logit

from thermo_engine.c3_design import (
    C3DesignSpecification,
    C3DesignTools,
    C3EquilibriumCurve,
    construct_column,
    minimum_reflux,
    rate_column,
)
from thermo_engine.c3_engineering_study import load_model
from thermo_engine.c3_pressure_check import PRPressureReference
from thermo_engine.c3_thermodynamics import R, _properties, _vapor_phi, bubble_temperature
from thermo_engine.c3_thermoformer import C3ThermoFormer, file_sha256
from thermo_engine.paper_validation import validate_equilibrium_result


class TFExtrapolation:
    """Preserve neural weights; explicitly extend only this experiment's solver."""

    def __init__(
        self,
        model: C3ThermoFormer,
        *,
        allow_extrapolation: bool = False,
        pressure_kpa: float = 2000,
        volume_method: str = "DIPPR_PERRY_8E",
    ) -> None:
        if not allow_extrapolation:
            raise ValueError("Experimental extrapolation requires explicit opt-in")
        if pressure_kpa not in (1000, 2000):
            raise ValueError("Only the 1 MPa control and 2 MPa experiment are declared")
        if volume_method not in ("DIPPR_PERRY_8E", "HEOS_FIT", "VDI_PPDS"):
            raise ValueError("Undeclared pure-volume correlation")
        self.model, self.pressure_kpa, self.volume_method = model, pressure_kpa, volume_method
        self.constants, self.properties, _ = _properties()
        self.reference = PRPressureReference(2000) if pressure_kpa == 2000 else None

    def pure_reference(self, temperature: float) -> np.ndarray[Any, Any]:
        """Use pure correlations only inside their own published library ranges."""
        from thermo import PR

        values = []
        for i in range(2):
            vp, vol = self.properties.VaporPressures[i], self.properties.VolumeLiquids[i]
            if not vp.test_method_validity(temperature, "HEOS_FIT") or not vol.test_method_validity(
                temperature, self.volume_method
            ):
                raise ValueError("Pure property outside its own correlation range")
            psat = float(vp.calculate(temperature, "HEOS_FIT"))
            volume = float(vol.calculate(temperature, self.volume_method))
            pure = PR(
                Tc=self.constants.Tcs[i],
                Pc=self.constants.Pcs[i],
                omega=self.constants.omegas[i],
                T=temperature,
                P=psat,
            )
            values.append(
                psat * float(pure.phi_g) * np.exp(volume * (self.pressure_kpa * 1000 - psat) / (R * temperature))
            )
        return np.asarray(values)

    def bubble(self, composition: float) -> dict[str, Any]:
        """Solve gamma-phi closure using real, unmodified TF log-gamma outputs."""
        if not 0 <= composition <= 1:
            raise ValueError("Invalid composition")
        x = np.array([composition, 1 - composition])
        initial = (
            self.reference.bubble(composition)
            if self.reference
            else bubble_temperature(1000, composition, self.model.log_gamma)
        )
        present = x > 0

        def evaluate(t: float, y: Any) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
            if not 273.15 <= t <= 350:
                raise ValueError("Outside declared extrapolation experiment search interval")
            lg = self.model.log_gamma(t, self.pressure_kpa, composition)
            if not np.isfinite(lg).all() or abs(lg).max() > 25:
                raise ValueError("Invalid TF activity coefficients")
            liquid = x * np.exp(lg) * self.pure_reference(t)
            gas = np.asarray(y) * _vapor_phi(t, self.pressure_kpa, np.asarray(y)) * self.pressure_kpa * 1000
            return np.log(liquid[present] / gas[present]), lg

        if 0 < composition < 1:

            def residual(v: Any) -> Any:
                yp = float(expit(v[1]))
                return evaluate(float(v[0]), [yp, 1 - yp])[0]

            solved = root(residual, [initial["T_K"], logit(initial["y"][0])], tol=1e-10)
            if not solved.success and np.max(abs(residual(solved.x))) > 1e-8:
                raise ValueError("TF extrapolation closure did not converge; no PR substitution")
            temperature, yp = float(solved.x[0]), float(expit(solved.x[1]))
            y = np.array([yp, 1 - yp])
        else:
            y = x.copy()
            temperature = float(
                brentq(lambda t: float(evaluate(t, y)[0][0]), initial["T_K"] - 2, initial["T_K"] + 2, xtol=1e-10)
            )
        errors, lg = evaluate(temperature, y)
        error = float(np.max(abs(errors)))
        check = validate_equilibrium_result([x, y], error, temperatures=[temperature])
        if not check["passed"]:
            raise ValueError("TF extrapolation failed numerical validation")
        return {
            "T_K": temperature,
            "P_kPa": self.pressure_kpa,
            "x": x.tolist(),
            "y": y.tolist(),
            "log_gamma": lg.tolist(),
            "equilibrium_residual": error,
            "validation": check,
            "backend": "actual_C3_adapted_ThermoFormer_gamma_phi_EXPERIMENTAL_EXTRAPOLATION",
            "within_C3_temperature_training_span": 273.15 <= temperature <= 313.15,
            "within_C3_experimental_pressure_span": 474 <= self.pressure_kpa <= 1652.2,
            "pure_liquid_volume_method": self.volume_method,
            "empirical_extrapolation_accuracy_validated": False,
        }


def review_column(
    curve: C3EquilibriumCurve, model: TFExtrapolation, rated: dict[str, Any], spec: C3DesignSpecification
) -> dict[str, Any]:
    """Numerically audit without granting empirical or engineering acceptance."""

    def direct(x: float) -> dict[str, Any]:
        state = model.bubble(x)
        return {**state, "y_propene": state["y"][0], "temperature_k": state["T_K"]}

    tools = C3DesignTools(curve, spec, direct, {"extrapolation": True})
    rated.update(
        status="valid" if rated["numerical_checks"]["passed"] else "failed",
        verified=False,
        candidate_id="extrapolation",
    )
    tools.archive["extrapolation"] = rated
    result = tools.execute("verify:extrapolation")
    result["engineering_accepted"] = False
    result["empirical_extrapolation_accuracy_validated"] = False
    return result


def total_reflux_stages(curve: C3EquilibriumCurve, top: float = 0.996, bottom: float = 0.01) -> dict[str, Any]:
    """Discrete total-reflux bound at the specified product limits, including reboiler."""
    eq = PchipInterpolator(curve.x_propene, curve.y_propene, extrapolate=False)
    y = top
    trace = []
    for stage in range(1, 2001):
        x = float(brentq(lambda v, target=y: float(eq(v)) - target, 0, 1, xtol=1e-13))
        if x >= y:
            raise ValueError("No separation progress in total-reflux stepping")
        trace.append({"stage": stage, "x_propene": x, "y_propene": y})
        if x <= bottom:
            check = validate_equilibrium_result([[x, 1 - x], [y, 1 - y]], abs(float(eq(x)) - y))
            return {
                "stages_including_reboiler": stage,
                "top_limit": top,
                "bottom_limit": bottom,
                "trace": trace,
                "validation": check,
                "interpretation": "infinite-reflux equilibrium-stage bound; not a finite-throughput operating design",
            }
        y = x
    raise ValueError("Total-reflux stage cap exceeded")


def run_experiment(output: Path, reference_path: Path) -> dict[str, Any]:
    """Reuse a frozen model and compare like-for-like column inputs with PR."""
    output.mkdir(parents=True, exist_ok=True)
    model, signature = load_model()
    experiment = TFExtrapolation(model, allow_extrapolation=True)
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    pr_curve = json.loads((reference_path.parent / "pr_curve.json").read_text(encoding="utf-8"))["curve"]
    states = []
    for i, x in enumerate(pr_curve["x_propene"]):
        try:
            states.append(experiment.bubble(x))
        except ValueError as error:
            (output / "failed_state.json").write_text(
                json.dumps({"x": x, "error": str(error), "previous_states": states}, indent=2), encoding="utf-8"
            )
            raise
        if (i + 1) % 50 == 0:
            print(f"TF extrapolation: {i + 1} states solved", flush=True)
    curve = C3EquilibriumCurve(
        pressure_kpa=2000,
        x_propene=[s["x"][0] for s in states],
        y_propene=[s["y"][0] for s in states],
        temperature_k=[s["T_K"] for s in states],
        maximum_equilibrium_residual=max(s["equilibrium_residual"] for s in states),
        source="C3_ThermoFormer_2MPa_explicit_extrapolation_Perry_volume",
        point_validation_passed=True,
    )
    (output / "tf_curve.json").write_text(
        json.dumps({"curve": curve.model_dump(), "states": states}, indent=2), encoding="utf-8"
    )
    spec = C3DesignSpecification(pressure_kpa=2000)
    rated = rate_column(curve, spec, 90, 120, 86, reference["selected"]["profiles"]["x_propene"])
    reviewed = review_column(curve, experiment, rated, spec)
    print(
        json.dumps({"fixed_column": reviewed["metrics"], "numerically_verified_and_targets_met": reviewed["verified"]}),
        flush=True,
    )
    rmin = minimum_reflux(curve, spec)
    estimates = []
    for reflux in [60.0, 70.0, 80.0, 90.0, 100.0, 120.0, 150.0, 200.0]:
        estimated = construct_column(curve, spec, reflux)
        estimates.append(
            {"R": reflux, "N": estimated["stages_including_reboiler"], "feed": estimated["feed_stage_from_top"]}
        )
    controls = []
    for x in [0.01, 0.35, 0.9, 0.996]:
        previous = bubble_temperature(1000, x, model.log_gamma)
        changed = TFExtrapolation(model, allow_extrapolation=True, pressure_kpa=1000).bubble(x)
        controls.append(
            {
                "x": x,
                "old_HEOS": previous,
                "Perry": changed,
                "delta_y": changed["y"][0] - previous["y"][0],
                "delta_T_K": changed["T_K"] - previous["T_K"],
            }
        )
    alternative_volume = TFExtrapolation(model, allow_extrapolation=True, volume_method="VDI_PPDS")
    volume_sensitivity = []
    for x in [0.01, 0.35, 0.9, 0.996]:
        perry, vdi = experiment.bubble(x), alternative_volume.bubble(x)
        volume_sensitivity.append(
            {
                "x": x,
                "Perry": perry,
                "VDI_PPDS": vdi,
                "delta_y": vdi["y"][0] - perry["y"][0],
                "delta_T_K": vdi["T_K"] - perry["T_K"],
            }
        )
    extended_estimate = construct_column(curve, spec, 90)
    extended_rating = rate_column(
        curve,
        spec,
        90,
        extended_estimate["stages_including_reboiler"],
        extended_estimate["feed_stage_from_top"],
        extended_estimate["initial_x_profile"],
    )
    extended = review_column(curve, experiment, extended_rating, spec)
    result = {
        "model_signature": signature,
        "reference_sha256": file_sha256(reference_path),
        "TF_extrapolation": reviewed,
        "PR_same_column": reference["selected"],
        "minimum_reflux_TF": rmin,
        "construction_estimates_not_fixed120_ratings": estimates,
        "pure_volume_control_1MPa": controls,
        "new_training": False,
        "new_LLM_run": False,
        "pure_volume_sensitivity_2MPa": volume_sensitivity,
        "total_reflux_bound_TF": total_reflux_stages(curve),
        "total_reflux_bound_PR": total_reflux_stages(C3EquilibriumCurve.model_validate(pr_curve)),
        "extended_column_R90_TF": extended,
        "engineering_accepted": False,
        "accuracy_validated": False,
        "protocol": {
            "P_kPa_absolute": 2000,
            "N_including_reboiler": 120,
            "feed_stage": 86,
            "R": 90,
            "feed_quality": 1,
            "F_mol_s": 1,
            "pressure_drop": 0,
            "volume_change": (
                "HEOS liquid-volume fit too narrow; explicit Perry correlation inside declared ranges; "
                "no pure-correlation extrapolation"
            ),
            "PR_role": "initial guess and independent comparator; never returned as a TF solution",
        },
    }
    (output / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"minimum_reflux_TF": rmin, "estimates": estimates}), flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-extrapolation", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    run_experiment(args.output, args.reference)


if __name__ == "__main__":
    main()
