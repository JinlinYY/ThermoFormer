"""Isolated C3 gamma-phi research backend, in [propene, propane] order.

This does not change the low-pressure production ThermoFormer decoder. The
activity-coefficient callback is supplied explicitly; no reference model is
silently substituted for it. A successful numerical gate is not experimental
accuracy or global phase-stability certification.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from functools import lru_cache
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import brentq

from thermo_engine.paper_validation import validate_equilibrium_result

FloatArray = NDArray[np.float64]
LogGammaCallback = Callable[[float, float, float], FloatArray]
COMPONENTS = ("propene", "propane")
CAS_NUMBERS = ("115-07-1", "74-98-6")
TEMPERATURE_BOUNDS_K = (273.15, 313.15)
PRESSURE_BOUNDS_KPA = (400.0, 1800.0)
EXPERIMENTAL_PRESSURE_BOUNDS_KPA = (474.0, 1652.2)
R = 8.31446261815324


class C3ThermodynamicError(ValueError):
    """Explicit research-backend failure with a machine-readable reason."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@lru_cache(maxsize=1)
def _properties() -> tuple[Any, Any, list[list[float]]]:
    from thermo import ChemicalConstantsPackage
    from thermo.interaction_parameters import IPDB

    constants, correlations = ChemicalConstantsPackage.from_IDs(list(CAS_NUMBERS))
    if not IPDB.has_ip_specific("ChemSep PR", list(CAS_NUMBERS), "kij"):
        raise C3ThermodynamicError("missing_parameters", "ChemSep PR has no explicit C3 binary interaction.")
    kijs = IPDB.get_ip_symmetric_matrix("ChemSep PR", list(CAS_NUMBERS), "kij")
    for prop in (*correlations.VaporPressures, *correlations.VolumeLiquids):
        if "HEOS_FIT" not in prop.all_methods:
            raise C3ThermodynamicError("missing_parameters", "Required HEOS_FIT pure correlation is absent.")
        prop.method = "HEOS_FIT"
        prop.extrapolation = None
    return constants, correlations, kijs


def property_provenance() -> dict[str, Any]:
    """Return exact installed correlations, binary interaction, and limitations."""
    import chemicals
    import thermo
    from thermo.interaction_parameters import IPDB

    constants, correlations, kijs = _properties()
    pair_record = next(
        value for key, value in IPDB.tables["ChemSep PR"].items() if set(key.split()) == set(CAS_NUMBERS)
    )
    return {
        "component_order": list(COMPONENTS),
        "CAS_numbers": list(CAS_NUMBERS),
        "library_versions": {"thermo": thermo.__version__, "chemicals": chemicals.__version__},
        "critical_temperatures_K": list(constants.Tcs),
        "critical_pressures_Pa": list(constants.Pcs),
        "acentric_factors": list(constants.omegas),
        "pure_vapor_pressure": [
            {
                "method": p.method,
                "temperature_limits_K": list(p.T_limits[p.method]),
                "source": "thermo bundled polynomial fit of REFPROP Helmholtz-EOS results",
            }
            for p in correlations.VaporPressures
        ],
        "saturated_liquid_molar_volume": [
            {"method": p.method, "temperature_limits_K": list(p.T_limits[p.method])} for p in correlations.VolumeLiquids
        ],
        "vapor_fugacity": "Peng-Robinson, classical quadratic mixing rule, gas root",
        "binary_interaction": {
            "table": "ChemSep PR",
            "kij_matrix": kijs,
            "record_as_distributed": pair_record,
            "raw_record_pressure_units": "not interpreted; library metadata does not state units",
            "source_temperature_upper_bound": "not supplied in distributed pair record",
        },
        "liquid_standard_state": "Psat * pure_PR_vapor_phi_at_Psat * exp(Vsat*(P-Psat)/(R*T))",
        "poynting_assumption": "incompressible pure liquid at its saturated-liquid molar volume",
        "research_temperature_bounds_K": list(TEMPERATURE_BOUNDS_K),
        "research_pressure_bounds_kPa": list(PRESSURE_BOUNDS_KPA),
        "experimental_pressure_bounds_kPa": list(EXPERIMENTAL_PRESSURE_BOUNDS_KPA),
        "global_phase_stability": "not_certified",
        "sources": [
            "https://thermo.readthedocs.io/thermo.vapor_pressure.html",
            "https://thermo.readthedocs.io/thermo.volume.html",
            "https://thermo.readthedocs.io/thermo.interaction_parameters.html",
            "https://thermo.readthedocs.io/thermo.eos_mix.html",
            "https://trc.nist.gov/ThermoML/10.1016/j.fluid.2006.03.009.html",
        ],
    }


def _composition(value: float | Sequence[float] | FloatArray) -> FloatArray:
    vector = np.asarray(value, dtype=float)
    if vector.ndim == 0:
        vector = np.array([float(vector), 1.0 - float(vector)])
    if (
        vector.shape != (2,)
        or not np.isfinite(vector).all()
        or np.min(vector) < 0
        or np.max(vector) > 1
        or abs(float(vector.sum()) - 1) > 1e-10
    ):
        raise C3ThermodynamicError("invalid_input", "Expected a normalized C3 binary mole fraction.")
    return vector


def _check_conditions(T_K: float, P_kPa: float) -> None:
    if not np.isfinite([T_K, P_kPa]).all():
        raise C3ThermodynamicError("invalid_input", "Nonfinite temperature or pressure.")
    if not TEMPERATURE_BOUNDS_K[0] - 1e-8 <= T_K <= TEMPERATURE_BOUNDS_K[1] + 1e-8:
        raise C3ThermodynamicError("outside_applicability", "Temperature is outside C3 research support.")
    if not PRESSURE_BOUNDS_KPA[0] <= P_kPa <= PRESSURE_BOUNDS_KPA[1]:
        raise C3ThermodynamicError("outside_applicability", "Pressure is outside C3 research support.")


def _vapor_phi(T_K: float, P_kPa: float, y: FloatArray) -> FloatArray:
    from thermo import PRMIX

    constants, _, kijs = _properties()
    eos = PRMIX(
        Tcs=constants.Tcs,
        Pcs=constants.Pcs,
        omegas=constants.omegas,
        zs=y.tolist(),
        kijs=kijs,
        T=T_K,
        P=P_kPa * 1000.0,
    )
    if not hasattr(eos, "phis_g") or eos.dP_dV_g >= 0:
        raise C3ThermodynamicError("no_vapor_root", "No mechanically stable PR vapor root.")
    return np.asarray(eos.phis_g, dtype=float)


@lru_cache(maxsize=32768)
def _pure_terms(T_K: float) -> tuple[FloatArray, FloatArray, FloatArray]:
    from thermo import PR

    constants, correlations, _ = _properties()
    psat, volumes, phi_sat = [], [], []
    for i in range(2):
        p = correlations.VaporPressures[i]
        v = correlations.VolumeLiquids[i]
        if not p.test_method_validity(T_K, p.method) or not v.test_method_validity(T_K, v.method):
            raise C3ThermodynamicError("outside_applicability", "Pure correlation would extrapolate.")
        saturation_pressure = p(T_K)
        volume = v.T_dependent_property(T_K)
        if saturation_pressure is None or volume is None:
            raise C3ThermodynamicError("missing_parameters", "Pure property could not be evaluated.")
        pure = PR(Tc=constants.Tcs[i], Pc=constants.Pcs[i], omega=constants.omegas[i], T=T_K, P=saturation_pressure)
        if not hasattr(pure, "phi_g"):
            raise C3ThermodynamicError("no_vapor_root", "Pure PR saturation vapor root is absent.")
        psat.append(saturation_pressure / 1000.0)
        volumes.append(volume)
        phi_sat.append(pure.phi_g)
    return np.asarray(psat), np.asarray(volumes), np.asarray(phi_sat)


def c3_reference_terms(
    T_K: float,
    P_kPa: float,
    x: float | Sequence[float] | FloatArray,
    y: float | Sequence[float] | FloatArray,
) -> dict[str, Any]:
    """Pure reference and observed-gamma target for an experimental state.

    Targets are conditional on the stated reference/EOS model, not independently
    measured activity coefficients. Absent components have no measurable gamma
    target and are returned as NaN; they must not be used as regression labels.
    """
    _check_conditions(T_K, P_kPa)
    xv, yv = _composition(x), _composition(y)
    psat, volume, phi_sat = _pure_terms(float(T_K))
    poynting = np.exp(volume * (P_kPa - psat) * 1000.0 / (R * T_K))
    reference = psat * phi_sat * poynting
    phi = _vapor_phi(T_K, P_kPa, yv)
    target = np.full(2, np.nan)
    observed = (xv > 0) & (yv > 0)
    target[observed] = np.log(yv[observed] * phi[observed] * P_kPa / (xv[observed] * reference[observed]))
    return {
        "phi_vapor": phi,
        "liquid_reference_fugacity_kPa": reference,
        "pure_saturation_pressure_kPa": psat,
        "pure_saturation_vapor_phi": phi_sat,
        "poynting_factor": poynting,
        "log_gamma_target": target,
        "target_observed_mask": observed,
        "within_experimental_pressure_span": EXPERIMENTAL_PRESSURE_BOUNDS_KPA[0]
        <= P_kPa
        <= EXPERIMENTAL_PRESSURE_BOUNDS_KPA[1],
    }


def _bubble_state(T_K: float, P_kPa: float, x: FloatArray, callback: LogGammaCallback) -> dict[str, Any]:
    _check_conditions(T_K, P_kPa)
    log_gamma = np.asarray(callback(float(T_K), float(P_kPa), float(x[0])), dtype=float)
    if log_gamma.shape != (2,) or not np.isfinite(log_gamma).all() or abs(log_gamma).max() > 25:
        raise C3ThermodynamicError("invalid_model_output", "Activity callback returned invalid log gamma.")
    psat, volume, phi_sat = _pure_terms(float(T_K))
    reference = psat * phi_sat * np.exp(volume * (P_kPa - psat) * 1000.0 / (R * T_K))
    liquid = x * np.exp(log_gamma) * reference
    y = liquid / liquid.sum()
    for _iteration in range(100):
        phi = _vapor_phi(T_K, P_kPa, y)
        raw_y = liquid / (P_kPa * phi)
        next_y = raw_y / raw_y.sum()
        if np.max(abs(next_y - y)) < 1e-12:
            y = next_y
            break
        y = next_y
    else:
        raise C3ThermodynamicError("nonconvergence", "Vapor-composition inner iteration failed.")
    phi = _vapor_phi(T_K, P_kPa, y)
    residual = liquid / (P_kPa * phi) - y
    return {
        "T_K": float(T_K),
        "P_kPa": float(P_kPa),
        "x": x.tolist(),
        "y": y.tolist(),
        "log_gamma": log_gamma.tolist(),
        "phi_vapor": phi.tolist(),
        "liquid_reference_fugacity_kPa": reference.tolist(),
        "closure": float(np.sum(liquid / (P_kPa * phi)) - 1.0),
        "equilibrium_residual": float(np.max(abs(residual))),
        "inner_iterations": _iteration + 1,
    }


def _finish(state: dict[str, Any], *, solved_variable: str) -> dict[str, Any]:
    validation = validate_equilibrium_result(
        [state["x"], state["y"]],
        state["equilibrium_residual"],
        temperatures=[state["T_K"]],
    )
    validation.update(
        {
            "property_applicability_passed": True,
            "vapor_mechanical_stability_passed": True,
            "mixture_global_phase_stability": "not_certified",
            "binary_parameter_applicability": "sourced_ChemSep_record_has_incomplete_range_metadata",
            "material_balance_scope": "bubble limit with zero vapor fraction; no finite flash inferred",
        }
    )
    state.update(
        {
            "validation": validation,
            "solved_variable": solved_variable,
            "component_order": list(COMPONENTS),
            "backend": "C3_gamma_phi_PR_vapor_HEOS_pure_reference",
        }
    )
    if not validation["passed"]:
        raise C3ThermodynamicError("validation_failed", "Converged bubble state failed numerical gate.")
    return state


def _solve_bubble(
    fixed: float,
    x_propene: float | Sequence[float] | FloatArray,
    callback: LogGammaCallback,
    *,
    variable: str,
) -> dict[str, Any]:
    x = _composition(x_propene)
    bounds = TEMPERATURE_BOUNDS_K if variable == "temperature" else PRESSURE_BOUNDS_KPA

    def state(value: float) -> dict[str, Any]:
        return (
            _bubble_state(value, fixed, x, callback)
            if variable == "temperature"
            else _bubble_state(fixed, value, x, callback)
        )

    # Scan avoids crossing an unavailable PR gas-root segment at low T/high P.
    bracket: tuple[float, float] | None = None
    previous: tuple[float, float] | None = None
    for candidate in np.linspace(bounds[0], bounds[1], 17):
        try:
            value = state(float(candidate))["closure"]
        except C3ThermodynamicError as error:
            if error.code in {"no_vapor_root", "no_liquid_root"}:
                previous = None
                continue
            raise
        if abs(value) <= 1e-10:
            return _finish(state(float(candidate)), solved_variable=variable)
        if previous is not None and previous[1] * value < 0:
            bracket = (previous[0], float(candidate))
            break
        previous = (float(candidate), value)
    if bracket is None:
        raise C3ThermodynamicError(
            "no_bubble_root_in_support", "No bubble closure inside the declared C3 research bounds."
        )
    root = brentq(lambda value: state(value)["closure"], *bracket, xtol=1e-9, rtol=1e-12)
    return _finish(state(float(root)), solved_variable=variable)


def bubble_temperature(
    P_kPa: float,
    x_propene: float | Sequence[float] | FloatArray,
    log_gamma_callback: LogGammaCallback,
) -> dict[str, Any]:
    """Validated fixed-pressure C3 bubble temperature; no implicit gamma model."""
    return _solve_bubble(P_kPa, x_propene, log_gamma_callback, variable="temperature")


def bubble_pressure(
    T_K: float,
    x_propene: float | Sequence[float] | FloatArray,
    log_gamma_callback: LogGammaCallback,
) -> dict[str, Any]:
    """Validated fixed-temperature C3 bubble pressure; no implicit gamma model."""
    return _solve_bubble(T_K, x_propene, log_gamma_callback, variable="pressure")


def pr_reference_log_gamma(T_K: float, P_kPa: float, x_propene: float) -> FloatArray:
    """Explicit PR liquid reference comparator, never a ThermoFormer fallback."""
    from thermo import PRMIX

    _check_conditions(T_K, P_kPa)
    constants, _, kijs = _properties()
    x = _composition(x_propene)
    eos = PRMIX(
        Tcs=constants.Tcs, Pcs=constants.Pcs, omegas=constants.omegas, zs=x.tolist(), kijs=kijs, T=T_K, P=P_kPa * 1000.0
    )
    if not hasattr(eos, "phis_l") or eos.dP_dV_l >= 0:
        raise C3ThermodynamicError("no_liquid_root", "No mechanically stable PR liquid root.")
    psat, volume, phi_sat = _pure_terms(float(T_K))
    reference = psat * phi_sat * np.exp(volume * (P_kPa - psat) * 1000.0 / (R * T_K))
    return np.asarray(np.log(np.asarray(eos.phis_l) * P_kPa / reference), dtype=float)


def run_reference_diagnostics(source_csv: str, output_dir: str) -> dict[str, Any]:
    """Evaluate the unfitted PR comparator against sourced C3 observations."""
    import csv
    import json
    from pathlib import Path

    source = Path(source_csv)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    with source.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    results: list[dict[str, Any]] = []
    for row in rows:
        T = float(row["source_temperature_k"])
        P = float(row["source_pressure_kpa"])
        x, y = float(row["x1"]), float(row["y1"])
        record: dict[str, Any] = {
            "T_observed_K": T,
            "P_observed_kPa": P,
            "x_propene": x,
            "y_observed_propene": y,
            "source_csv_line": row["source_csv_line"],
            "doi": row["doi"],
        }
        try:
            bubble = bubble_pressure(T, x, pr_reference_log_gamma)
            record.update(
                {
                    "P_predicted_kPa": bubble["P_kPa"],
                    "y_predicted_propene": bubble["y"][0],
                    "P_error_kPa": bubble["P_kPa"] - P,
                    "y_error": bubble["y"][0] - y,
                    "equilibrium_residual": bubble["equilibrium_residual"],
                    "validation_passed": bubble["validation"]["passed"],
                    "failure": "",
                }
            )
        except C3ThermodynamicError as error:
            record.update({"validation_passed": False, "failure": error.code})
        results.append(record)
    passed = [r for r in results if r["validation_passed"]]
    mixed = [r for r in passed if 0 < r["x_propene"] < 1]
    summary = {
        "model": "unfitted_PR_phi_phi_reference_via_explicit_reference_callback",
        "not_a_ThermoFormer_result": True,
        "observations": len(rows),
        "numerically_valid": len(passed),
        "mixed_observations": len(mixed),
        "P_MAE_kPa_all": float(np.mean([abs(r["P_error_kPa"]) for r in passed])),
        "P_MAPE_percent_all": float(np.mean([100 * abs(r["P_error_kPa"]) / r["P_observed_kPa"] for r in passed])),
        "y_MAE_mixed": float(np.mean([abs(r["y_error"]) for r in mixed])),
        "y_max_abs_error_mixed": float(np.max([abs(r["y_error"]) for r in mixed])),
        "fitted_to_these_observations": False,
        "independent_experimental_dataset": False,
        "data_quality": "source provenance audited; original thermodynamic consistency flags remain unverified",
        "global_stability": "not_certified",
        "property_provenance": property_provenance(),
    }
    (destination / "pr_reference_diagnostics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    fields = list(dict.fromkeys(key for result in results for key in result))
    with (destination / "pr_reference_predictions.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    return summary
