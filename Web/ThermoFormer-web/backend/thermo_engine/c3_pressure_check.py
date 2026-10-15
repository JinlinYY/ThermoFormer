"""Independent high-pressure PR reference calculation; never a TF fallback."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import root
from scipy.special import expit, logit

from thermo_engine.c3_design import (
    C3DesignSpecification,
    C3DesignTools,
    C3EquilibriumCurve,
    construct_column,
    minimum_reflux,
    rate_column,
)
from thermo_engine.c3_thermodynamics import _properties, bubble_temperature, pr_reference_log_gamma, property_provenance
from thermo_engine.paper_validation import validate_equilibrium_result


class PRPressureReference:
    """Explicit phi-phi comparator with sourced binary interaction data."""

    def __init__(self, pressure_kpa: float = 2000) -> None:
        from thermo import PRMIX, CEOSGas, CEOSLiquid, FlashVL

        if not 1800 <= pressure_kpa <= 2200:
            raise ValueError("This isolated reference study supports only 1800–2200 kPa")
        self.pressure_kpa = pressure_kpa
        self.constants, correlations, kijs = _properties()
        self.kwargs = dict(Tcs=self.constants.Tcs, Pcs=self.constants.Pcs, omegas=self.constants.omegas, kijs=kijs)
        self.eos = PRMIX
        gas = CEOSGas(PRMIX, eos_kwargs=self.kwargs, HeatCapacityGases=correlations.HeatCapacityGases)
        liquid = CEOSLiquid(PRMIX, eos_kwargs=self.kwargs, HeatCapacityGases=correlations.HeatCapacityGases)
        self.flasher = FlashVL(self.constants, correlations, gas=gas, liquid=liquid)

    def bubble(self, composition: float) -> dict[str, Any]:
        """Refine a PR bubble state and independently verify fugacity closure."""
        if not 0 <= composition <= 1:
            raise ValueError("Composition must lie in [0, 1]")
        x = np.array([composition, 1 - composition])
        pressure = self.pressure_kpa * 1000
        initial = self.flasher.flash(P=pressure, VF=0, zs=x.tolist())

        def phases(t: float, y: Any) -> tuple[Any, Any]:
            liq = self.eos(**self.kwargs, T=t, P=pressure, zs=x.tolist())
            gas = self.eos(**self.kwargs, T=t, P=pressure, zs=list(y))
            if not hasattr(liq, "phis_l") or not hasattr(gas, "phis_g"):
                raise ValueError("Required PR liquid/vapor roots absent")
            if liq.dP_dV_l >= 0 or gas.dP_dV_g >= 0 or gas.V_g <= liq.V_l:
                raise ValueError("Mechanically stable distinct liquid and vapor roots required")
            return liq, gas

        def residual(v: Any) -> Any:
            y = np.array([expit(v[1]), 1 - expit(v[1])])
            liq, gas = phases(float(v[0]), y)
            return np.log(x * np.asarray(liq.phis_l) / (y * np.asarray(gas.phis_g)))

        t, y = float(initial.T), np.asarray(initial.gas.zs)
        if 0 < composition < 1:
            solved = root(residual, [t, logit(y[0])], tol=1e-10)
            if not solved.success and np.max(abs(residual(solved.x))) > 1e-8:
                raise ValueError("PR bubble refinement did not converge")
            t = float(solved.x[0])
            y = np.array([expit(solved.x[1]), 1 - expit(solved.x[1])])
        liq, gas = phases(t, y)
        present = x > 0
        error = float(
            np.max(
                abs(
                    np.log(
                        x[present] * np.asarray(liq.phis_l)[present] / (y[present] * np.asarray(gas.phis_g)[present])
                    )
                )
            )
        )
        validation = validate_equilibrium_result([x, y], error, temperatures=[t])
        if not validation["passed"] or not 300 <= t <= 350:
            raise ValueError("Reference bubble numerical or declared temperature check failed")
        return {
            "T_K": t,
            "P_kPa": self.pressure_kpa,
            "x": x.tolist(),
            "y": y.tolist(),
            "equilibrium_residual": error,
            "validation": validation,
            "model": "independent_PR_phi_phi_not_ThermoFormer",
            "global_phase_stability": "not_certified",
        }

    def enthalpy(self, temperature: float, composition: float, vapor: bool) -> float:
        """PR departure plus sourced ideal-gas sensible enthalpy; reference 298.15 K."""
        from thermo_engine.c3_utilities import _enthalpy_properties

        if not 300 <= temperature <= 350 or not 0 <= composition <= 1:
            raise ValueError("Outside declared reference enthalpy calculation conditions")
        _, correlations, _, _, _ = _enthalpy_properties()
        z = [composition, 1 - composition]
        ideal = 0.0
        for fraction, cp in zip(z, correlations.HeatCapacityGases):  # noqa: B905
            if not cp.test_method_validity(temperature, cp.method) or not cp.test_method_validity(298.15, cp.method):
                raise ValueError("Heat capacity would extrapolate")
            integral = cp.T_dependent_property_integral(298.15, temperature)
            if integral is None or not np.isfinite(integral):
                raise ValueError("Missing heat capacity integral")
            ideal += fraction * float(integral)
        eos = self.eos(**self.kwargs, T=temperature, P=self.pressure_kpa * 1000, zs=z)
        phase = "g" if vapor else "l"
        if not hasattr(eos, f"H_dep_{phase}") or getattr(eos, f"dP_dV_{phase}") >= 0:
            raise ValueError("Required caloric phase root unavailable")
        value = ideal + float(getattr(eos, f"H_dep_{phase}"))
        check = validate_equilibrium_result([z], 0, temperatures=[temperature])
        if not check["passed"] or not np.isfinite(value):
            raise ValueError("Caloric numerical check failed")
        return value


def reference_utilities(model: PRPressureReference, candidate: dict[str, Any]) -> dict[str, Any]:
    """Local duties for a reviewed CMO column, with explicit energy nonclosure."""
    from thermo_engine.c3_utilities import CoolingScenario, HeatingScenario, screen_cooling_water, screen_heating_water

    if not candidate.get("verified"):
        raise ValueError("Direct numerical review required before duty estimates")
    m, profile = candidate["metrics"], candidate["profiles"]
    xd, xb = m["distillate_propene_mole_fraction"], m["bottoms_propene_mole_fraction"]
    d, b, reflux = m["distillate_flow_mol_s"], m["bottoms_flow_mol_s"], m["reflux_ratio"]
    f = d + b
    liquid, vapor = reflux * d, (reflux + 1) * d
    top = model.bubble(profile["x_propene"][0])
    condensed = model.bubble(xd)
    bottom = model.bubble(xb)
    inlet = model.bubble(profile["x_propene"][-2])
    feed = model.bubble(0.35)
    h_d = model.enthalpy(condensed["T_K"], xd, False)
    h_b = model.enthalpy(bottom["T_K"], xb, False)
    qc = vapor * (model.enthalpy(top["T_K"], xd, True) - h_d)
    qr = (
        b * h_b
        + vapor * model.enthalpy(bottom["T_K"], bottom["y"][0], True)
        - (liquid + f) * model.enthalpy(inlet["T_K"], inlet["x"][0], False)
    )
    energy_residual = qr - qc - (d * h_d + b * h_b - f * model.enthalpy(feed["T_K"], 0.35, False))
    check = validate_equilibrium_result(
        [top["y"], bottom["x"]], max(top["equilibrium_residual"], bottom["equilibrium_residual"])
    )
    if not check["passed"] or not np.isfinite([qc, qr]).all() or min(qc, qr) <= 0:
        raise ValueError("Invalid reference duty estimate")
    return {
        "condenser_duty_kw": qc / 1000,
        "reboiler_duty_kw": qr / 1000,
        "top_vapor_temperature_c": top["T_K"] - 273.15,
        "condensed_liquid_temperature_c": condensed["T_K"] - 273.15,
        "bottom_temperature_c": bottom["T_K"] - 273.15,
        "feed_temperature_c": feed["T_K"] - 273.15,
        "cooling": screen_cooling_water(
            top["T_K"],
            condensed["T_K"],
            qc,
            CoolingScenario(name="water_25_to_35C", inlet_temperature_c=25, outlet_temperature_c=35),
        ).model_dump(),
        "heating": screen_heating_water(
            inlet["T_K"],
            bottom["T_K"],
            qr,
            HeatingScenario(name="water_80_to_70C", inlet_temperature_c=80, outlet_temperature_c=70),
        ).model_dump(),
        "old_heating_60_to_50C": screen_heating_water(inlet["T_K"], bottom["T_K"], qr, HeatingScenario()).model_dump(),
        "whole_column_energy_residual_w": energy_residual,
        "full_MESH_energy_solved": False,
        "numerical_validation": check,
        "basis": "local PR enthalpy estimate, F=1 mol/s; not equipment sizing or plant utilities",
    }


def build_reference_curve(model: PRPressureReference, destination: Path) -> C3EquilibriumCurve:
    """Generate and record a validated reference curve without changing TF bounds."""
    tail = np.geomspace(1e-5, 0.1, 45)
    xs = np.unique(np.r_[0, tail, np.linspace(0.1, 0.9, 161), 1 - tail, 1, 0.009, 0.01, 0.35, 0.996, 0.997])
    states = [model.bubble(float(x)) for x in xs]
    curve = C3EquilibriumCurve(
        pressure_kpa=model.pressure_kpa,
        x_propene=xs.tolist(),
        y_propene=[s["y"][0] for s in states],
        temperature_k=[s["T_K"] for s in states],
        maximum_equilibrium_residual=max(s["equilibrium_residual"] for s in states),
        source="PR_phi_phi_reference_not_ThermoFormer",
        point_validation_passed=True,
    )
    destination.write_text(json.dumps({"curve": curve.model_dump(), "states": states}, indent=2), encoding="utf-8")
    return curve


def run_study(output: Path, pressure_kpa: float = 2000, stages: int = 120) -> dict[str, Any]:
    """Search fixed-stage reference designs; retain failures and model restrictions."""
    output.mkdir(parents=True, exist_ok=True)
    try:
        bubble_temperature(pressure_kpa, 0.35, pr_reference_log_gamma)
        tf_gate = {"status": "unexpectedly_in_support"}
    except ValueError as error:
        tf_gate = {"status": "outside_applicability", "code": getattr(error, "code", "error"), "message": str(error)}
    (output / "thermoformer_applicability.json").write_text(json.dumps(tf_gate, indent=2), encoding="utf-8")
    model = PRPressureReference(pressure_kpa)
    curve = build_reference_curve(model, output / "pr_curve.json")
    spec = C3DesignSpecification(pressure_kpa=pressure_kpa)
    rmin = minimum_reflux(curve, spec)
    estimates = []
    for factor in [1.1, 1.3, 1.5, 2, 3, 5, 10, 100]:
        estimate = construct_column(curve, spec, factor * rmin)
        estimates.append(
            {
                "factor": factor,
                "reflux_ratio": factor * rmin,
                "stages": estimate["stages_including_reboiler"],
                "feed_stage": estimate["feed_stage_from_top"],
            }
        )
    prelim = {
        "thermoformer_status": tf_gate,
        "pressure_kpa_absolute": pressure_kpa,
        "stages_including_reboiler": stages,
        "minimum_reflux": rmin,
        "estimates": estimates,
        "provenance": property_provenance(),
    }
    (output / "preliminary.json").write_text(json.dumps(prelim, indent=2), encoding="utf-8")
    print(json.dumps({"minimum_reflux": rmin, "estimates": estimates}), flush=True)
    records = []
    retained: dict[str, Any] | None = None
    for reflux in [60.0, 70.0, 80.0, 90.0, 100.0]:
        estimate = construct_column(curve, spec, reflux)
        n, nf = estimate["stages_including_reboiler"], estimate["feed_stage_from_top"]
        for feed_stage in range(70, 101):
            knots = np.r_[np.linspace(0, nf - 1, feed_stage), np.linspace(nf, n - 1, stages - feed_stage)]
            initial = np.interp(knots, np.arange(n), estimate["initial_x_profile"]).tolist()
            rated = rate_column(curve, spec, reflux, stages, feed_stage, initial)
            records.append(
                {
                    "metrics": rated["metrics"],
                    "checks": rated["numerical_checks"],
                    "meets_targets": rated["meets_targets"],
                }
            )
            if reflux == 90 and feed_stage == 86:
                retained = rated
        print(f"Reference fixed-stage scan: R={reflux} complete", flush=True)
    if retained is None:
        raise ValueError("Selected reference candidate absent")

    def direct(x: float) -> dict[str, Any]:
        state = model.bubble(x)
        return {**state, "y_propene": state["y"][0], "temperature_k": state["T_K"]}

    tools = C3DesignTools(curve, spec, direct, {"reference_only": True})
    retained.update(
        status="valid" if retained["numerical_checks"]["passed"] else "failed",
        verified=False,
        candidate_id="fixed120_R90_F86",
    )
    tools.archive["fixed120_R90_F86"] = retained
    reviewed = tools.execute("verify:fixed120_R90_F86")
    if not reviewed["verified"]:
        raise ValueError("Direct reference column review failed")
    result = {
        **prelim,
        "scan": records,
        "selected": reviewed,
        "utilities": reference_utilities(model, reviewed),
        "selection": "R=90, feed=86; explicit margin over near-boundary R=70 reference, not economic optimization",
        "assumptions": {
            "pressure_basis": "absolute_provisional",
            "feed_flow_mol_s": 1,
            "feed_quality": 1,
            "total_condenser": True,
            "120_stages_include_reboiler": True,
            "pressure_drop": 0,
        },
        "not_a_ThermoFormer_prediction": True,
        "new_LLM_run": False,
        "limitations": [
            "PR binary interaction range metadata incomplete; no independent 2 MPa VLE validation",
            "No claim of global stability or industrial performance; constant molar overflow, not full MESH",
            "Old 2.8% TF stress calibration is not transferred to this reference model",
        ],
    }
    (output / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"selected": reviewed["metrics"], "verified": reviewed["verified"]}), flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pressure-kpa", type=float, default=2000)
    args = parser.parse_args()
    run_study(args.output, args.pressure_kpa)


if __name__ == "__main__":
    main()
