"""Preliminary C3 utility screening, separate from the ThermoFormer VLE model.

PR departure enthalpies plus sourced ideal-gas heat capacities provide an
explicit engineering estimate. They are not a calorically consistent extension
of ThermoFormer, and no MESH energy solution is implied by a successful screen.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
from scipy.optimize import brentq

from thermo_engine.c3_design import C3DesignSpecification
from thermo_engine.c3_thermodynamics import (
    CAS_NUMBERS,
    PRESSURE_BOUNDS_KPA,
    TEMPERATURE_BOUNDS_K,
    C3ThermodynamicError,
    LogGammaCallback,
    bubble_temperature,
    property_provenance,
)
from thermo_engine.paper_validation import validate_equilibrium_result

REFERENCE_T_K = 298.15
COMMON_LIMITATIONS = [
    "PR enthalpies are a separate caloric estimate, not a ThermoFormer-consistent enthalpy model.",
    "The existing constant-molar-overflow design has not been solved with full MESH energy equations.",
    "No heat-transfer coefficient, exchanger area, fouling allowance, pressure drop or tray efficiency is computed.",
    "No real process experiment, global phase-stability certification or economic optimum is available.",
]


class UtilityError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class CoolingScenario(BaseModel):
    """Declared countercurrent sensible-water screening conditions."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str
    inlet_temperature_c: float = Field(allow_inf_nan=False)
    outlet_temperature_c: float = Field(allow_inf_nan=False)
    minimum_approach_k: float = Field(default=5.0, gt=0, allow_inf_nan=False)
    fluid: Literal["liquid_water"] = "liquid_water"
    basis: str = "declared_calculation_scenario_not_measured_utility_conditions"

    @model_validator(mode="after")
    def check_temperatures(self) -> CoolingScenario:
        if not 0 <= self.inlet_temperature_c < self.outlet_temperature_c < 100:
            raise ValueError("Sensible-water screen requires 0 <= inlet < outlet < 100 degC")
        return self


class HeatingScenario(BaseModel):
    """Declared sensible-hot-water conditions; not an assumed plant utility."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str = "hot_water_60_to_50C"
    inlet_temperature_c: float = Field(default=60, allow_inf_nan=False)
    outlet_temperature_c: float = Field(default=50, allow_inf_nan=False)
    minimum_approach_k: float = Field(default=5.0, gt=0, allow_inf_nan=False)
    fluid: Literal["liquid_water"] = "liquid_water"
    basis: str = "declared_calculation_scenario_not_measured_utility_conditions"

    @model_validator(mode="after")
    def check_temperatures(self) -> HeatingScenario:
        if not 0 <= self.outlet_temperature_c < self.inlet_temperature_c < 100:
            raise ValueError("Sensible-hot-water screen requires 0 <= outlet < inlet < 100 degC")
        return self


class HeatingScreen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    scenario: HeatingScenario
    status: Literal["passes_endpoint_screen", "fails_endpoint_screen"]
    hot_in_minus_process_out_k: float
    hot_out_minus_process_in_k: float
    minimum_endpoint_approach_k: float
    endpoint_screen_passed: bool
    hot_water_mass_flow_kg_s: float | None = None
    water_sensible_enthalpy_drop_j_kg: float
    validation: dict[str, Any]
    limitations: list[str] = Field(
        default_factory=lambda: [
            "Countercurrent endpoint screen only; the full reboiler boiling path is not solved.",
            "Hot-water flow uses a sourced sensible heat-capacity integral; no steam or boiler efficiency is assumed.",
            "Heating availability, transfer coefficient, exchanger area and pumping energy are not established.",
        ]
    )


class EnthalpyState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    temperature_k: float
    pressure_kpa: float
    propene_mole_fraction: float
    phase: Literal["liquid", "vapor"]
    molar_enthalpy_j_mol: float
    ideal_gas_sensible_enthalpy_j_mol: float
    pr_departure_enthalpy_j_mol: float
    validation: dict[str, Any]
    limitations: list[str] = Field(default_factory=lambda: list(COMMON_LIMITATIONS[:1]))


class ProductSaturation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    pressure_kpa: float
    product_propene_mole_fraction: float
    bubble_temperature_k: float
    dew_temperature_k: float
    bubble_state: dict[str, Any]
    dew_state: dict[str, Any]
    validation: dict[str, Any]
    limitations: list[str] = Field(
        default_factory=lambda: [
            "Bubble and dew endpoints do not establish the full two-phase condensation enthalpy path.",
            "The gamma-phi equilibrium model has not been globally phase-stability certified.",
        ]
    )


class DutyEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    duty_w: float
    sign_convention: str
    method: str
    molar_flows_mol_s: dict[str, float]
    enthalpy_states: dict[str, EnthalpyState]
    validation: dict[str, Any]
    limitations: list[str] = Field(default_factory=lambda: list(COMMON_LIMITATIONS))


class CoolingScreen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    scenario: CoolingScenario
    status: Literal["passes_endpoint_screen", "fails_endpoint_screen", "unsupported"]
    hot_in_minus_cold_out_k: float | None = None
    hot_out_minus_cold_in_k: float | None = None
    minimum_endpoint_approach_k: float | None = None
    endpoint_screen_passed: bool = False
    coolant_mass_flow_kg_s: float | None = None
    water_sensible_enthalpy_increase_j_kg: float | None = None
    maximum_cold_out_for_hot_in_approach_c: float | None = None
    validation: dict[str, Any]
    limitations: list[str] = Field(
        default_factory=lambda: [
            "Only countercurrent endpoint temperature approaches were screened; no full exchanger pinch analysis.",
            "Water flow is a sensible-heat estimate for the declared inlet/outlet temperatures.",
            "Chiller COP, refrigeration electricity, pumping duty and ambient availability are not evaluated.",
            "A passing endpoint screen is not an exchanger design or proof of plant utility availability.",
        ]
    )


class UtilitiesAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    status: Literal["preliminary_estimate", "partial", "unsupported", "invalid_input", "missing_parameters"]
    candidate_id: str | None = None
    specification: dict[str, Any]
    product_saturation: dict[str, ProductSaturation] = Field(default_factory=dict)
    condenser: DutyEstimate | None = None
    reboiler: DutyEstimate | None = None
    cooling_scenarios: list[CoolingScreen] = Field(default_factory=list)
    whole_column_energy_diagnostic: dict[str, Any] | None = None
    failures: list[dict[str, str]] = Field(default_factory=list)
    validation: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=lambda: list(COMMON_LIMITATIONS))


def _numeric_gate(
    compositions: list[list[float]],
    values: list[float],
    *,
    material_residual: float = 0.0,
) -> dict[str, Any]:
    check = validate_equilibrium_result(compositions, 0.0, material_residual=material_residual)
    check.update(
        {
            "finite_values_passed": bool(np.isfinite(values).all()),
            "equilibrium_residual_applicable": False,
            "gate_scope": "composition, finite values and stated material balance; not new VLE validation",
            "caloric_accuracy": "not_established_by_numerical_checks",
        }
    )
    check["passed"] = bool(check["passed"] and check["finite_values_passed"])
    return check


@lru_cache(maxsize=1)
def _enthalpy_properties() -> tuple[Any, Any, list[list[float]], Any, Any]:
    from thermo import ChemicalConstantsPackage
    from thermo.interaction_parameters import IPDB

    constants, correlations = ChemicalConstantsPackage.from_IDs(list(CAS_NUMBERS))
    if not IPDB.has_ip_specific("ChemSep PR", list(CAS_NUMBERS), "kij"):
        raise UtilityError("missing_parameters", "Required sourced ChemSep PR binary parameter is absent")
    kijs = IPDB.get_ip_symmetric_matrix("ChemSep PR", list(CAS_NUMBERS), "kij")
    water_constants, water = ChemicalConstantsPackage.from_IDs(["7732-18-5"])
    for prop in [*correlations.HeatCapacityGases, water.HeatCapacityLiquids[0]]:
        if "HEOS_FIT" not in prop.all_methods:
            raise UtilityError("missing_parameters", "Required sourced HEOS_FIT heat capacity is absent")
        prop.method = "HEOS_FIT"
        prop.extrapolation = None
    return constants, correlations, kijs, water_constants, water


def utility_provenance() -> dict[str, Any]:
    """Identify exact caloric correlations and the different VLE/enthalpy roles."""
    _, properties, kijs, water_constants, water = _enthalpy_properties()
    return {
        "equilibrium_provenance": property_provenance(),
        "enthalpy_model": "ideal-gas sensible enthalpy integral plus PR phase departure enthalpy",
        "enthalpy_reference": "each pure ideal gas has zero sensible enthalpy at 298.15 K; no formation enthalpies",
        "reference_cancellation": "valid for nonreacting component-balanced unit balances",
        "ideal_gas_heat_capacities": [
            {"CAS": CAS_NUMBERS[i], "method": prop.method, "temperature_limits_k": list(prop.T_limits[prop.method])}
            for i, prop in enumerate(properties.HeatCapacityGases)
        ],
        "heat_capacity_source": "thermo bundled HEOS_FIT polynomials of fundamental Helmholtz-EOS results",
        "PR_binary_kij": kijs,
        "coolant": {
            "fluid": "water",
            "CAS": "7732-18-5",
            "molecular_weight_g_mol": float(water_constants.MWs[0]),
            "heat_capacity_method": water.HeatCapacityLiquids[0].method,
            "temperature_limits_k": list(water.HeatCapacityLiquids[0].T_limits["HEOS_FIT"]),
            "pressure_dependence": "neglected for the preliminary liquid-water sensible-heat screen",
        },
        "thermoformer_caloric_consistency": False,
        "full_MESH_energy_solution": False,
        "sources": [
            "https://thermo.readthedocs.io/thermo.eos_mix.html",
            "https://thermo.readthedocs.io/thermo.heat_capacity.html",
            "https://thermo.readthedocs.io/thermo.interaction_parameters.html",
        ],
    }


def pr_molar_enthalpy(
    temperature_k: float,
    pressure_kpa: float,
    propene_mole_fraction: float,
    phase: Literal["liquid", "vapor"],
) -> EnthalpyState:
    """Calculate sourced PR phase enthalpy with a declared common reference."""
    from thermo import PRMIX

    T, P, z = temperature_k, pressure_kpa, propene_mole_fraction
    if not np.isfinite([T, P, z]).all() or not 0 <= z <= 1 or phase not in {"liquid", "vapor"}:
        raise UtilityError("invalid_input", "Need finite normalized C3 state and an explicit phase")
    if not TEMPERATURE_BOUNDS_K[0] - 1e-8 <= T <= TEMPERATURE_BOUNDS_K[1] + 1e-8:
        raise UtilityError("outside_applicability", "Enthalpy temperature is outside the declared C3 study range")
    if not PRESSURE_BOUNDS_KPA[0] <= P <= PRESSURE_BOUNDS_KPA[1]:
        raise UtilityError("outside_applicability", "Enthalpy pressure is outside the declared C3 study range")
    constants, correlations, kijs, _, _ = _enthalpy_properties()
    composition = [z, 1 - z]
    ideal = 0.0
    for fraction, cp in zip(composition, correlations.HeatCapacityGases):  # noqa: B905 - Python 3.9
        if not cp.test_method_validity(T, cp.method) or not cp.test_method_validity(REFERENCE_T_K, cp.method):
            raise UtilityError("outside_applicability", "Ideal heat-capacity integral would extrapolate")
        integral = cp.T_dependent_property_integral(REFERENCE_T_K, T)
        if integral is None or not np.isfinite(integral):
            raise UtilityError("missing_parameters", "Ideal heat-capacity integral could not be evaluated")
        ideal += fraction * float(integral)
    eos = PRMIX(
        Tcs=constants.Tcs, Pcs=constants.Pcs, omegas=constants.omegas, zs=composition, kijs=kijs, T=T, P=P * 1000
    )
    suffix = "g" if phase == "vapor" else "l"
    if not hasattr(eos, f"H_dep_{suffix}") or getattr(eos, f"dP_dV_{suffix}") >= 0:
        raise UtilityError("unsupported_phase_root", "Requested mechanically stable PR phase root is absent")
    departure = float(getattr(eos, f"H_dep_{suffix}"))
    total = ideal + departure
    validation = _numeric_gate([composition], [total, ideal, departure])
    validation.update(correlation_applicability_passed=True, requested_phase_root_passed=True)
    if not validation["passed"]:
        raise UtilityError("validation_failed", "Enthalpy state failed numerical property validation")
    return EnthalpyState(
        temperature_k=T,
        pressure_kpa=P,
        propene_mole_fraction=z,
        phase=phase,
        molar_enthalpy_j_mol=total,
        ideal_gas_sensible_enthalpy_j_mol=ideal,
        pr_departure_enthalpy_j_mol=departure,
        validation=validation,
    )


def product_saturation_endpoints(
    pressure_kpa: float,
    product_propene: float,
    log_gamma_callback: LogGammaCallback,
) -> ProductSaturation:
    """Bubble and dew endpoints at the same bulk product composition and pressure.

    Dew is obtained by inverting validated binary bubble states. No ideal K-value
    substitute is used; missing roots within the supported range are explicit.
    """
    if not np.isfinite(product_propene) or not 0 <= product_propene <= 1:
        raise UtilityError("invalid_input", "Product mole fraction must lie in [0,1]")
    cache: dict[float, dict[str, Any]] = {}

    def state(x: float) -> dict[str, Any]:
        if x not in cache:
            cache[x] = bubble_temperature(pressure_kpa, x, log_gamma_callback)
        return cache[x]

    bubble = state(product_propene)
    if product_propene in {0.0, 1.0}:
        dew = bubble
    else:
        bracket: tuple[float, float] | None = None
        previous: tuple[float, float] | None = None
        for x in np.unique(np.r_[np.linspace(0, 1, 17), product_propene]):
            try:
                error = float(state(float(x))["y"][0]) - product_propene
            except C3ThermodynamicError as exc:
                if exc.code in {"no_bubble_root_in_support", "no_vapor_root", "no_liquid_root"}:
                    previous = None
                    continue
                raise
            if abs(error) <= 1e-11:
                bracket = (float(x), float(x))
                break
            if previous is not None and previous[1] * error < 0:
                bracket = (previous[0], float(x))
                break
            previous = float(x), error
        if bracket is None:
            raise UtilityError("unsupported_dew_endpoint", "No dew endpoint inside supported C3 bubble states")
        root = (
            bracket[0]
            if bracket[0] == bracket[1]
            else float(
                brentq(
                    lambda x: state(float(x))["y"][0] - product_propene,
                    *bracket,
                    xtol=1e-12,
                )
            )
        )
        dew = state(root)
    composition_error = abs(float(dew["y"][0]) - product_propene)
    residual = max(bubble["equilibrium_residual"], dew["equilibrium_residual"], composition_error)
    validation = validate_equilibrium_result(
        [bubble["x"], bubble["y"], dew["x"], dew["y"]],
        residual,
        temperatures=[bubble["T_K"], dew["T_K"]],
    )
    validation.update(
        bubble_validation_passed=bool(bubble["validation"]["passed"]),
        dew_validation_passed=bool(dew["validation"]["passed"]),
        dew_composition_residual=composition_error,
        equation="dew solved by y(x,P)=product composition using the supplied activity model",
    )
    validation["passed"] = bool(validation["passed"] and bubble["validation"]["passed"] and dew["validation"]["passed"])
    if not validation["passed"]:
        raise UtilityError("validation_failed", "Product bubble/dew endpoints failed validation")
    return ProductSaturation(
        pressure_kpa=pressure_kpa,
        product_propene_mole_fraction=product_propene,
        bubble_temperature_k=bubble["T_K"],
        dew_temperature_k=dew["T_K"],
        bubble_state=bubble,
        dew_state=dew,
        validation=validation,
    )


def screen_cooling_water(
    hot_dew_temperature_k: float,
    hot_bubble_temperature_k: float,
    condenser_duty_w: float,
    scenario: CoolingScenario,
) -> CoolingScreen:
    """Countercurrent terminal-temperature screen and sensible-water demand."""
    inlet, outlet = scenario.inlet_temperature_c + 273.15, scenario.outlet_temperature_c + 273.15
    if (
        not np.isfinite([hot_dew_temperature_k, hot_bubble_temperature_k, condenser_duty_w]).all()
        or min(hot_dew_temperature_k, hot_bubble_temperature_k, condenser_duty_w) <= 0
    ):
        raise UtilityError("invalid_input", "Cooling screen needs finite temperatures and positive heat rejection")
    if hot_dew_temperature_k + 1e-7 < hot_bubble_temperature_k:
        raise UtilityError("unsupported_condensation_path", "Dew temperature is below bubble temperature")
    approach_in = hot_dew_temperature_k - outlet
    approach_out = hot_bubble_temperature_k - inlet
    minimum = min(approach_in, approach_out)
    feasible = minimum >= scenario.minimum_approach_k
    _, _, _, water_constants, water = _enthalpy_properties()
    cp = water.HeatCapacityLiquids[0]
    if not cp.test_method_validity(inlet, cp.method) or not cp.test_method_validity(outlet, cp.method):
        raise UtilityError("outside_applicability", "Water heat-capacity integral would extrapolate")
    molar_increase = cp.T_dependent_property_integral(inlet, outlet)
    if molar_increase is None or not np.isfinite(molar_increase) or molar_increase <= 0:
        raise UtilityError("missing_parameters", "Water sensible heat-capacity integral is unavailable")
    increase = float(molar_increase) / (float(water_constants.MWs[0]) / 1000)
    mass_flow = condenser_duty_w / increase if feasible else None
    validation = _numeric_gate([[1.0]], [approach_in, approach_out, minimum, increase])
    validation.update(
        endpoint_thermal_feasibility_passed=feasible,
        full_condensation_path_checked=False,
        duty_recovery_residual_w=abs(mass_flow * increase - condenser_duty_w) if mass_flow is not None else None,
        coolant_flow_withheld_if_endpoint_screen_fails=True,
    )
    return CoolingScreen(
        scenario=scenario,
        status="passes_endpoint_screen" if feasible else "fails_endpoint_screen",
        hot_in_minus_cold_out_k=approach_in,
        hot_out_minus_cold_in_k=approach_out,
        minimum_endpoint_approach_k=minimum,
        endpoint_screen_passed=feasible,
        coolant_mass_flow_kg_s=mass_flow,
        water_sensible_enthalpy_increase_j_kg=increase,
        maximum_cold_out_for_hot_in_approach_c=hot_dew_temperature_k - scenario.minimum_approach_k - 273.15,
        validation=validation,
    )


def screen_heating_water(
    process_in_temperature_k: float,
    process_bubble_temperature_k: float,
    reboiler_duty_w: float,
    scenario: HeatingScenario | None = None,
) -> HeatingScreen:
    """Optional 60-to-50 degC hot-water endpoint screen, independent of ranking."""
    source = scenario if scenario is not None else HeatingScenario()
    if (
        not np.isfinite([process_in_temperature_k, process_bubble_temperature_k, reboiler_duty_w]).all()
        or min(process_in_temperature_k, process_bubble_temperature_k, reboiler_duty_w) <= 0
    ):
        raise UtilityError("invalid_input", "Heating screen needs positive finite process temperatures and duty")
    inlet, outlet = source.inlet_temperature_c + 273.15, source.outlet_temperature_c + 273.15
    approach_in = inlet - process_bubble_temperature_k
    approach_out = outlet - process_in_temperature_k
    minimum = min(approach_in, approach_out)
    feasible = minimum >= source.minimum_approach_k
    _, _, _, water_constants, water = _enthalpy_properties()
    cp = water.HeatCapacityLiquids[0]
    if not cp.test_method_validity(inlet, cp.method) or not cp.test_method_validity(outlet, cp.method):
        raise UtilityError("outside_applicability", "Hot-water heat-capacity integral would extrapolate")
    molar_drop = cp.T_dependent_property_integral(outlet, inlet)
    if molar_drop is None or not np.isfinite(molar_drop) or molar_drop <= 0:
        raise UtilityError("missing_parameters", "Hot-water sensible enthalpy drop is unavailable")
    drop = float(molar_drop) / (float(water_constants.MWs[0]) / 1000)
    flow = reboiler_duty_w / drop if feasible else None
    check = _numeric_gate([[1.0]], [approach_in, approach_out, minimum, drop])
    check.update(
        endpoint_thermal_feasibility_passed=feasible,
        full_reboiling_path_checked=False,
        duty_recovery_residual_w=abs(flow * drop - reboiler_duty_w) if flow is not None else None,
    )
    return HeatingScreen(
        scenario=source,
        status="passes_endpoint_screen" if feasible else "fails_endpoint_screen",
        hot_in_minus_process_out_k=approach_in,
        hot_out_minus_process_in_k=approach_out,
        minimum_endpoint_approach_k=minimum,
        endpoint_screen_passed=feasible,
        hot_water_mass_flow_kg_s=flow,
        water_sensible_enthalpy_drop_j_kg=drop,
        validation=check,
    )


def _condenser_duty(
    product: ProductSaturation,
    distillate_mol_s: float,
    reflux_ratio: float,
) -> DutyEstimate:
    z, P = product.product_propene_mole_fraction, product.pressure_kpa
    vapor = pr_molar_enthalpy(product.dew_temperature_k, P, z, "vapor")
    liquid = pr_molar_enthalpy(product.bubble_temperature_k, P, z, "liquid")
    vapor_flow = (reflux_ratio + 1) * distillate_mol_s
    duty = vapor_flow * (vapor.molar_enthalpy_j_mol - liquid.molar_enthalpy_j_mol)
    check = _numeric_gate([[z, 1 - z]], [duty, vapor_flow])
    check["passed"] = bool(check["passed"] and duty > 0 and vapor_flow > 0 and product.validation["passed"])
    if not check["passed"]:
        raise UtilityError("validation_failed", "Condenser estimate is not positive or state validation failed")
    return DutyEstimate(
        duty_w=duty,
        sign_convention="positive heat rejected",
        method="total condenser: Vtop*(H_PR,vapor at gamma-phi dew - H_PR,liquid at gamma-phi bubble)",
        molar_flows_mol_s={
            "vapor_in": vapor_flow,
            "total_liquid_out": vapor_flow,
            "distillate": distillate_mol_s,
            "reflux": reflux_ratio * distillate_mol_s,
        },
        enthalpy_states={"vapor_in": vapor, "saturated_liquid_out": liquid},
        validation=check,
        limitations=[*COMMON_LIMITATIONS, "No distillate/reflux subcooling or incoming-vapor superheat is assumed."],
    )


def _reboiler_duty(
    candidate: dict[str, Any],
    spec: C3DesignSpecification,
    log_gamma_callback: LogGammaCallback,
) -> DutyEstimate:
    metrics, profiles = candidate["metrics"], candidate["profiles"]
    if len(profiles["x_propene"]) < 2:
        raise UtilityError("invalid_input", "Reboiler assessment needs the last two liquid-stage compositions")
    D, B = float(metrics["distillate_flow_mol_s"]), float(metrics["bottoms_flow_mol_s"])
    reflux = float(metrics["reflux_ratio"])
    vapor_flow, liquid_flow = (reflux + 1) * D, reflux * D + spec.feed_flow_mol_s
    xb, xin = float(profiles["x_propene"][-1]), float(profiles["x_propene"][-2])
    bottom_state = bubble_temperature(spec.pressure_kpa, xb, log_gamma_callback)
    incoming_state = bubble_temperature(spec.pressure_kpa, xin, log_gamma_callback)
    yb = float(bottom_state["y"][0])
    material = max(abs(liquid_flow - B - vapor_flow), abs(liquid_flow * xin - B * xb - vapor_flow * yb))
    material /= max(liquid_flow, spec.feed_flow_mol_s)
    liquid_in = pr_molar_enthalpy(incoming_state["T_K"], spec.pressure_kpa, xin, "liquid")
    bottoms = pr_molar_enthalpy(bottom_state["T_K"], spec.pressure_kpa, xb, "liquid")
    vapor = pr_molar_enthalpy(bottom_state["T_K"], spec.pressure_kpa, yb, "vapor")
    duty = (
        B * bottoms.molar_enthalpy_j_mol
        + vapor_flow * vapor.molar_enthalpy_j_mol
        - liquid_flow * liquid_in.molar_enthalpy_j_mol
    )
    check = _numeric_gate([[xin, 1 - xin], [xb, 1 - xb], [yb, 1 - yb]], [duty], material_residual=material)
    check.update(
        reboiler_component_balance_residual=material,
        outgoing_equilibrium_validation=bottom_state["validation"],
        incoming_equilibrium_validation=incoming_state["validation"],
    )
    check["passed"] = bool(check["passed"] and duty > 0)
    if not check["passed"]:
        raise UtilityError(
            "reboiler_material_or_property_validation_failed",
            "Local reboiler states do not support a balanced positive estimate",
        )
    return DutyEstimate(
        duty_w=duty,
        sign_convention="positive heat supplied",
        method="local reboiler: B*HL(bottoms)+V*HV(boilup)-L*HL(penultimate-stage liquid), PR caloric model",
        molar_flows_mol_s={"liquid_in": liquid_flow, "bottoms_out": B, "boilup_out": vapor_flow},
        enthalpy_states={"liquid_in": liquid_in, "bottoms_out": bottoms, "boilup_out": vapor},
        validation=check,
        limitations=[
            *COMMON_LIMITATIONS,
            "The heating utility temperature and steam consumption are not specified or computed.",
        ],
    )


def assess_c3_utilities(
    candidate: dict[str, Any],
    spec: C3DesignSpecification | dict[str, Any],
    log_gamma_callback: LogGammaCallback,
    coolant_scenarios: list[CoolingScenario] | None = None,
) -> UtilitiesAssessment:
    """Screen a saved C3 candidate without modifying or reoptimizing the column."""
    specification = spec if isinstance(spec, C3DesignSpecification) else C3DesignSpecification.model_validate(spec)
    scenarios = (
        coolant_scenarios
        if coolant_scenarios is not None
        else [
            CoolingScenario(name="water_10_to_15C", inlet_temperature_c=10, outlet_temperature_c=15),
            CoolingScenario(name="water_25_to_30C", inlet_temperature_c=25, outlet_temperature_c=30),
        ]
    )
    product_states: dict[str, ProductSaturation] = {}
    failures: list[dict[str, str]] = []
    cooling: list[CoolingScreen] = []
    condenser: DutyEstimate | None = None
    reboiler: DutyEstimate | None = None
    energy: dict[str, Any] | None = None
    candidate_id = candidate.get("candidate_id")
    try:
        metadata = utility_provenance()
    except UtilityError as error:
        return UtilitiesAssessment(
            status="missing_parameters",
            candidate_id=candidate_id,
            specification=specification.model_dump(),
            failures=[{"part": "property_provenance", "code": error.code, "message": str(error)}],
            validation={"passed": False, "scope": "property parameter availability"},
        )
    metadata["process_assumptions"] = {
        "feed_quality_q": 1.0,
        "constant_molar_overflow": True,
        "total_condenser": True,
        "equilibrium_reboiler": True,
        "pressure_drop_kpa": 0.0,
        "cooling_screen_basis": "declared scenarios; no plant-utility measurements supplied",
    }
    try:
        if not candidate.get("numerical_checks", {}).get("passed"):
            raise UtilityError("invalid_input", "Candidate has not passed its numerical design gate")
        md = candidate["metrics"]
        P, D, B, reflux = map(
            float, (md["pressure_kpa"], md["distillate_flow_mol_s"], md["bottoms_flow_mol_s"], md["reflux_ratio"])
        )
        xd, xb = float(md["distillate_propene_mole_fraction"]), float(md["bottoms_propene_mole_fraction"])
        if not np.isfinite([P, D, B, reflux, xd, xb]).all() or min(D, B, reflux) <= 0 or not 0 <= xb < xd <= 1:
            raise UtilityError("invalid_input", "Candidate flows, reflux or compositions are invalid")
        if not np.isclose(P, specification.pressure_kpa, rtol=1e-12, atol=1e-10):
            raise UtilityError("invalid_input", "Candidate and specification pressures differ")
        flow_residual = (
            max(
                abs(D + B - specification.feed_flow_mol_s),
                abs(D * xd + B * xb - specification.feed_flow_mol_s * specification.feed_propene),
            )
            / specification.feed_flow_mol_s
        )
        if flow_residual > 1e-7:
            raise UtilityError("invalid_input", "Candidate product material balance does not match the specification")
    except (KeyError, ValueError) as error:
        code = error.code if isinstance(error, UtilityError) else "invalid_input"
        return UtilitiesAssessment(
            status="invalid_input",
            candidate_id=candidate_id,
            specification=specification.model_dump(),
            failures=[{"part": "candidate", "code": code, "message": str(error)}],
            validation={"passed": False, "scope": "input/material validation"},
            metadata=metadata,
        )

    for name, composition in [("distillate", xd), ("bottoms", xb)]:
        try:
            product_states[name] = product_saturation_endpoints(P, composition, log_gamma_callback)
        except (C3ThermodynamicError, UtilityError) as error:
            failures.append({"part": name, "code": error.code, "message": str(error)})
    if "distillate" in product_states:
        try:
            condenser = _condenser_duty(product_states["distillate"], D, reflux)
        except UtilityError as error:
            failures.append({"part": "condenser", "code": error.code, "message": str(error)})
    if condenser is not None:
        state = product_states["distillate"]
        for scenario in scenarios:
            try:
                cooling.append(
                    screen_cooling_water(
                        state.dew_temperature_k, state.bubble_temperature_k, condenser.duty_w, scenario
                    )
                )
            except UtilityError as error:
                failures.append({"part": scenario.name, "code": error.code, "message": str(error)})
                cooling.append(CoolingScreen(scenario=scenario, status="unsupported", validation={"passed": False}))
    try:
        reboiler = _reboiler_duty(candidate, specification, log_gamma_callback)
    except (C3ThermodynamicError, UtilityError, KeyError) as error:
        code = error.code if isinstance(error, (C3ThermodynamicError, UtilityError)) else "missing_profile_data"  # noqa: UP038
        failures.append({"part": "reboiler", "code": code, "message": str(error)})
    if condenser is not None and reboiler is not None:
        try:
            feed_state = bubble_temperature(P, specification.feed_propene, log_gamma_callback)
            feed_h = pr_molar_enthalpy(feed_state["T_K"], P, specification.feed_propene, "liquid")
            top_h = condenser.enthalpy_states["saturated_liquid_out"]
            bottom_h = reboiler.enthalpy_states["bottoms_out"]
            external = (
                D * top_h.molar_enthalpy_j_mol
                + B * bottom_h.molar_enthalpy_j_mol
                - specification.feed_flow_mol_s * feed_h.molar_enthalpy_j_mol
            )
            discrepancy = reboiler.duty_w - condenser.duty_w - external
            relative = abs(discrepancy) / max(abs(reboiler.duty_w), abs(condenser.duty_w))
            energy = {
                "Qr_minus_Qc_minus_product_minus_feed_enthalpy_w": discrepancy,
                "absolute_discrepancy_relative_to_larger_duty": relative,
                "external_product_minus_feed_enthalpy_rate_w": external,
                "feed_enthalpy_state": feed_h.model_dump(),
                "validation": _numeric_gate(
                    [[xd, 1 - xd], [xb, 1 - xb]], [discrepancy, relative, external], material_residual=flow_residual
                ),
                "energy_closure_enforced": False,
                "interpretation": "diagnostic of the two local duty estimates, not a closed MESH energy solution",
            }
            energy["internal_stage_diagnostic"] = _internal_stage_energy_diagnostic(
                candidate,
                specification,
                feed_h,
                top_h,
                max(abs(reboiler.duty_w), abs(condenser.duty_w)),
            )
            if not energy["validation"]["passed"] or not energy["internal_stage_diagnostic"]["validation"]["passed"]:
                failures.append(
                    {
                        "part": "whole_column_energy_diagnostic",
                        "code": "diagnostic_numerical_validation_failed",
                        "message": "Internal property/material validation failed; energy closure is not required.",
                    }
                )
        except (C3ThermodynamicError, UtilityError, KeyError) as error:
            failures.append(
                {
                    "part": "whole_column_energy_diagnostic",
                    "code": getattr(error, "code", "missing_profile_data"),
                    "message": str(error),
                }
            )
    complete = condenser is not None and reboiler is not None and len(product_states) == 2 and not failures
    validation = {
        "passed": complete,
        "scope": "numerical property and local-balance estimates, not full process validation",
        "candidate_material_balance_residual": flow_residual,
        "any_declared_cooling_endpoint_screen_passed": any(s.endpoint_screen_passed for s in cooling),
        "full_MESH_energy_solution": False,
        "thermoformer_caloric_consistency": False,
    }
    status: Literal["preliminary_estimate", "partial", "unsupported", "invalid_input", "missing_parameters"]
    status = (
        "preliminary_estimate"
        if complete
        else "partial"
        if condenser is not None or reboiler is not None
        else "unsupported"
    )
    return UtilitiesAssessment(
        status=status,
        candidate_id=candidate_id,
        specification=specification.model_dump(),
        product_saturation=product_states,
        condenser=condenser,
        reboiler=reboiler,
        cooling_scenarios=cooling,
        whole_column_energy_diagnostic=energy,
        failures=failures,
        validation=validation,
        metadata=metadata,
    )


def _internal_stage_energy_diagnostic(
    candidate: dict[str, Any],
    spec: C3DesignSpecification,
    feed_h: EnthalpyState,
    reflux_h: EnthalpyState,
    duty_basis_w: float,
) -> dict[str, Any]:
    """Check each nominally adiabatic tray; do not alter the CMO solution."""
    profiles, metrics = candidate["profiles"], candidate["metrics"]
    temperature = np.asarray(profiles["temperature_k"], dtype=float)
    x, y = np.asarray(profiles["x_propene"]), np.asarray(profiles["y_propene"])
    n = int(metrics["stages_including_reboiler"])
    if not len(temperature) == len(x) == len(y) == n or n < 3:
        raise UtilityError("invalid_input", "Aligned complete stage profiles are required for energy diagnosis")
    if not np.isfinite(np.r_[temperature, x, y]).all():
        raise UtilityError("invalid_input", "Stage profiles contain nonfinite values")
    liquid_enthalpy = np.asarray(
        [
            pr_molar_enthalpy(float(temperature[i]), spec.pressure_kpa, float(x[i]), "liquid").molar_enthalpy_j_mol
            for i in range(n)
        ]
    )
    vapor_enthalpy = np.asarray(
        [
            pr_molar_enthalpy(float(temperature[i]), spec.pressure_kpa, float(y[i]), "vapor").molar_enthalpy_j_mol
            for i in range(n)
        ]
    )
    distillate, reflux = float(metrics["distillate_flow_mol_s"]), float(metrics["reflux_ratio"])
    L, V, F = reflux * distillate, (reflux + 1) * distillate, spec.feed_flow_mol_s
    feed_index = int(metrics["feed_stage_from_top"]) - 1
    residuals, material = [], []
    for i in range(n - 1):
        Lin = L + (F if i > feed_index else 0)
        Lout = L + (F if i >= feed_index else 0)
        previous_h = reflux_h.molar_enthalpy_j_mol if i == 0 else float(liquid_enthalpy[i - 1])
        previous_x = reflux_h.propene_mole_fraction if i == 0 else float(x[i - 1])
        incoming = Lin * previous_h + V * vapor_enthalpy[i + 1]
        outgoing = Lout * liquid_enthalpy[i] + V * vapor_enthalpy[i]
        component_in = Lin * previous_x + V * y[i + 1]
        component_out = Lout * x[i] + V * y[i]
        if i == feed_index:
            incoming += F * feed_h.molar_enthalpy_j_mol
            component_in += F * spec.feed_propene
        residuals.append(float(incoming - outgoing))
        material.append(abs(float(component_in - component_out)) / max(L + F, V, F))
    largest = int(np.argmax(abs(np.asarray(residuals))))
    validation = _numeric_gate(
        np.r_[np.c_[x, 1 - x], np.c_[y, 1 - y]].tolist(), residuals, material_residual=max(material)
    )
    return {
        "scope": "nominally adiabatic equilibrium stages; excludes reboiler with external heat input",
        "stage_numbers_from_top": list(range(1, n)),
        "signed_incoming_minus_outgoing_enthalpy_rate_w": residuals,
        "maximum_absolute_stage_energy_residual_w": abs(residuals[largest]),
        "stage_at_maximum_absolute_residual": largest + 1,
        "maximum_absolute_stage_residual_divided_by_larger_duty": abs(residuals[largest]) / duty_basis_w,
        "sum_signed_internal_stage_residual_w": sum(residuals),
        "validation": validation,
        "energy_closure_enforced": False,
        "interpretation": "CMO/caloric residuals are not corrected or interpreted as MESH closure.",
    }
