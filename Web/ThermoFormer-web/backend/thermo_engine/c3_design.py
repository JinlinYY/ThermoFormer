"""Isolated, constant-molar-overflow C3 distillation design and numerical review.

The light component is propene throughout. Product targets are inputs to the
initial construction; a separate stage-balance rating computes outlet purities.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq, least_squares, root
from scipy.sparse import diags

from thermo_engine.paper_validation import validate_equilibrium_result


class C3DesignSpecification(BaseModel):
    """Declared engineering assumptions, distinct from user purity targets."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    pressure_kpa: float = Field(default=1000.0, gt=0)
    feed_flow_mol_s: float = Field(default=1.0, gt=0)
    feed_propene: float = Field(default=0.35, gt=0, lt=1)
    target_distillate_propene: float = Field(default=0.996, gt=0, lt=1)
    maximum_bottoms_propene_exclusive: float = Field(default=0.01, gt=0, lt=1)
    nominal_distillate_propene: float = Field(default=0.997, gt=0, lt=1)
    nominal_bottoms_propene: float = Field(default=0.009, gt=0, lt=1)
    numerical_stage_cap: int = Field(default=500, ge=3, le=1000)

    @model_validator(mode="after")
    def check_separation(self) -> C3DesignSpecification:
        if not self.nominal_bottoms_propene < self.feed_propene < self.nominal_distillate_propene:
            raise ValueError("Nominal products must bracket the feed composition")
        if not self.nominal_bottoms_propene < self.maximum_bottoms_propene_exclusive:
            raise ValueError("The strict bottoms target requires a positive design margin")
        if self.nominal_distillate_propene < self.target_distillate_propene:
            raise ValueError("Nominal distillate must meet the user purity target")
        return self


class C3EquilibriumCurve(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pressure_kpa: float = Field(gt=0, allow_inf_nan=False)
    x_propene: list[float]
    y_propene: list[float]
    temperature_k: list[float]
    maximum_equilibrium_residual: float
    source: str
    point_validation_passed: bool

    @model_validator(mode="after")
    def check_curve(self) -> C3EquilibriumCurve:
        x, y, t = map(np.asarray, (self.x_propene, self.y_propene, self.temperature_k))
        if len(x) < 5 or not len(x) == len(y) == len(t):
            raise ValueError("Need at least five aligned equilibrium states")
        if not np.isfinite(np.r_[x, y, t]).all() or np.any(t <= 0):
            raise ValueError("Nonfinite or nonphysical curve entries")
        if np.any(np.diff(x) <= 0) or np.any(np.diff(y) <= 0):
            raise ValueError("A unique monotone inverse equilibrium curve is required")
        if abs(x[0]) > 1e-10 or abs(y[0]) > 1e-10 or abs(x[-1] - 1) > 1e-10 or abs(y[-1] - 1) > 1e-10:
            raise ValueError("Both pure-component endpoints must be present")
        check = validate_equilibrium_result(
            np.r_[np.c_[x, 1 - x], np.c_[y, 1 - y]],
            self.maximum_equilibrium_residual,
            temperatures=t,
        )
        if not self.point_validation_passed or not check["passed"]:
            raise ValueError("Equilibrium curve failed numerical validation")
        return self


def product_flows(spec: C3DesignSpecification) -> tuple[float, float]:
    """Nominal material split; actual compositions are found by column rating."""
    distillate = (
        spec.feed_flow_mol_s
        * (spec.feed_propene - spec.nominal_bottoms_propene)
        / (spec.nominal_distillate_propene - spec.nominal_bottoms_propene)
    )
    return distillate, spec.feed_flow_mol_s - distillate


def minimum_reflux(curve: C3EquilibriumCurve, spec: C3DesignSpecification) -> float:
    """Scan rectifying and stripping pinch conditions with saturated-liquid feed."""
    eq = PchipInterpolator(curve.x_propene, curve.y_propene, extrapolate=False)
    z, xd, xb = spec.feed_propene, spec.nominal_distillate_propene, spec.nominal_bottoms_propene
    xr = np.linspace(z, xd - 1e-9, 10001)
    xs = np.linspace(xb + 1e-9, z, 10001)
    rect = (xd - eq(xr)) / (xd - xr)
    ymax_feed = xb + (eq(xs) - xb) * (z - xb) / (xs - xb)
    strip = (xd - ymax_feed) / (xd - z)
    slope = max(0.0, float(np.max(rect)), float(np.max(strip)))
    if slope >= 1 or not math.isfinite(slope):
        raise ValueError("A pinch or volatility reversal prevents this ordinary-distillation construction")
    return slope / (1 - slope)


def construct_column(curve: C3EquilibriumCurve, spec: C3DesignSpecification, reflux_ratio: float) -> dict[str, Any]:
    """McCabe-Thiele starting estimate, explicitly not an outlet-purity test."""
    if not math.isfinite(reflux_ratio) or reflux_ratio <= 0:
        raise ValueError("A finite positive reflux ratio is required")
    eq = PchipInterpolator(curve.x_propene, curve.y_propene, extrapolate=False)
    distillate, bottoms = product_flows(spec)
    liquid = reflux_ratio * distillate
    vapor = liquid + distillate
    y = spec.nominal_distillate_propene
    previous = y
    profile: list[float] = []
    feed_stage: int | None = None
    for stage in range(1, spec.numerical_stage_cap + 1):
        x = float(brentq(lambda v, target=y: float(eq(v)) - target, 0, 1, xtol=1e-13))
        if x >= previous - 1e-12:
            raise ValueError("Stage construction made no separation progress")
        profile.append(x)
        if feed_stage is None and x <= spec.feed_propene:
            feed_stage = stage
        if x <= spec.nominal_bottoms_propene:
            if feed_stage is None or feed_stage >= stage:
                raise ValueError("No interior feed stage in constructed column")
            return {
                "stages_including_reboiler": stage,
                "feed_stage_from_top": feed_stage,
                "initial_x_profile": profile,
            }
        if x > spec.feed_propene:
            y = (liquid * x + distillate * spec.nominal_distillate_propene) / vapor
        else:
            y = ((liquid + spec.feed_flow_mol_s) * x - bottoms * spec.nominal_bottoms_propene) / vapor
        previous = x
    raise ValueError("Numerical stage cap exceeded; not proof of physical infeasibility")


def rate_column(
    curve: C3EquilibriumCurve,
    spec: C3DesignSpecification,
    reflux_ratio: float,
    stages: int,
    feed_stage: int,
    initial_x: list[float] | None = None,
) -> dict[str, Any]:
    """Independently solve each stage's component balance at fixed N, feed, R, D/F."""
    if not math.isclose(curve.pressure_kpa, spec.pressure_kpa, rel_tol=1e-12):
        raise ValueError("Equilibrium curve and rating pressures must match")
    if stages < 3 or not 1 < feed_stage < stages:
        raise ValueError("Require an interior feed and at least three equilibrium stages")
    eq = PchipInterpolator(curve.x_propene, curve.y_propene, extrapolate=False)
    deq = eq.derivative()
    temp = PchipInterpolator(curve.x_propene, curve.temperature_k, extrapolate=False)
    distillate, bottoms = product_flows(spec)
    feed = spec.feed_flow_mol_s
    liquid, vapor = reflux_ratio * distillate, (reflux_ratio + 1) * distillate
    feed_index = feed_stage - 1
    entering_liquid = np.array([liquid + (feed if i > feed_index else 0) for i in range(stages)])
    leaving_liquid = np.array([liquid + (feed if i >= feed_index else 0) for i in range(stages)])
    balance_scale = max(feed, vapor, liquid + feed)

    def residual(x: Any) -> Any:
        y = eq(x)
        values = np.zeros(stages)
        values[0] = vapor * y[1] - liquid * x[0] - distillate * y[0]
        values[1:-1] = entering_liquid[1:-1] * x[:-2] + vapor * y[2:] - leaving_liquid[1:-1] * x[1:-1] - vapor * y[1:-1]
        values[feed_index] += feed * spec.feed_propene
        values[-1] = entering_liquid[-1] * x[-2] - bottoms * x[-1] - vapor * y[-1]
        return values / balance_scale

    def jacobian(x: Any) -> Any:
        derivative = deq(x)
        diagonal = -leaving_liquid - vapor * derivative
        diagonal[0] = -liquid - distillate * derivative[0]
        diagonal[-1] = -bottoms - vapor * derivative[-1]
        lower = entering_liquid[1:]
        upper = vapor * derivative[1:]
        return diags([lower, diagonal, upper], [-1, 0, 1], shape=(stages, stages), format="csr") / balance_scale

    initial = np.asarray(
        initial_x
        if initial_x is not None
        else np.linspace(spec.nominal_distillate_propene, spec.nominal_bottoms_propene, stages)
    )
    if initial.shape != (stages,):
        raise ValueError("Initial composition profile has the wrong number of stages")
    clipped = np.clip(initial, 1e-10, 1 - 1e-10)
    solution = root(residual, clipped, jac=lambda value: jacobian(value).toarray(), tol=1e-11)
    if not solution.success or not np.isfinite(solution.x).all() or np.any(solution.x <= 0) or np.any(solution.x >= 1):
        solution = least_squares(
            residual,
            clipped,
            jac=jacobian,
            bounds=(1e-12, 1 - 1e-12),
            tr_options={"atol": 1e-13, "btol": 1e-13},
            xtol=1e-12,
            ftol=1e-12,
            gtol=1e-12,
            max_nfev=600,
        )
    x = solution.x
    y = np.asarray(eq(x))
    xd, xb = float(y[0]), float(x[-1])
    balance = abs(distillate * xd + bottoms * xb - feed * spec.feed_propene) / feed
    maximum_stage_residual = float(np.max(np.abs(residual(x))))
    equilibrium_residual = float(np.max(np.abs(y - eq(x))))
    checks = validate_equilibrium_result(
        np.r_[np.c_[x, 1 - x], np.c_[y, 1 - y]],
        equilibrium_residual,
        material_residual=max(balance, maximum_stage_residual),
        temperatures=temp(x),
    )
    checks.update(
        solver_success=bool(solution.success),
        stage_balance_residual=maximum_stage_residual,
        overall_component_residual=balance,
        equilibrium_relation="interpolated validated model curve; direct review is separate",
    )
    checks["passed"] = bool(checks["passed"] and solution.success)
    targets = xd >= spec.target_distillate_propene and xb < spec.maximum_bottoms_propene_exclusive
    return {
        "numerical_checks": checks,
        "meets_targets": bool(targets),
        "metrics": {
            "stages_including_reboiler": stages,
            "feed_stage_from_top": feed_stage,
            "reflux_ratio": reflux_ratio,
            "pressure_kpa": spec.pressure_kpa,
            "distillate_flow_mol_s": distillate,
            "bottoms_flow_mol_s": bottoms,
            "distillate_propene_mole_fraction": xd,
            "bottoms_propene_mole_fraction": xb,
            "propene_recovery": distillate * xd / (feed * spec.feed_propene),
            "propane_recovery": bottoms * (1 - xb) / (feed * (1 - spec.feed_propene)),
            "top_stage_temperature_k": float(temp(x[0])),
            "reboiler_temperature_k": float(temp(x[-1])),
        },
        "profiles": {
            "stage_from_top": list(range(1, stages + 1)),
            "x_propene": x.tolist(),
            "y_propene": y.tolist(),
            "temperature_k": np.asarray(temp(x)).tolist(),
        },
    }


class C3DesignTools:
    """Bounded numerical action set for an independently recorded Agent run."""

    def __init__(
        self,
        curve: C3EquilibriumCurve,
        spec: C3DesignSpecification,
        direct_bubble: Callable[[float], dict[str, Any]],
        provenance: dict[str, Any],
    ) -> None:
        if not math.isclose(curve.pressure_kpa, spec.pressure_kpa, rel_tol=1e-12):
            raise ValueError("Equilibrium curve and design pressures must match")
        self.curve, self.spec, self.direct_bubble = curve, spec, direct_bubble
        self._provenance = provenance
        self.rmin = minimum_reflux(curve, spec)
        self.archive: dict[str, dict[str, Any]] = {}
        self.factors = {"design_r1p3": 1.3, "design_r1p5": 1.5, "design_r2p0": 2.0, "design_r3p0": 3.0}

    def provenance(self) -> dict[str, Any]:
        return {
            **self._provenance,
            "case_type": "calculation_case_no_process_experiments",
            "assumptions": {
                "pressure_kpa": self.spec.pressure_kpa,
                "feed_flow_mol_s": self.spec.feed_flow_mol_s,
                "feed_quality": 1,
                "constant_molar_overflow": True,
                "total_condenser": True,
                "equilibrium_reboiler": True,
                "column_pressure_drop_kpa": 0,
                "stage_efficiency": "not_modeled; equilibrium stages only",
            },
            "product_targets": self.spec.model_dump(),
            "resource_preference": "lower reflux among sampled, numerically reviewed feasible candidates",
            "resource_warning": "No energy balance or economic optimization has been performed",
        }

    def candidate_actions(self) -> list[dict[str, Any]]:
        actions = [
            {
                "action_id": key,
                "kind": "evaluate",
                "description": "Construct then independently rate a column at the stated reflux factor.",
                "settings": {"reflux_factor": factor, "reflux_ratio": factor * self.rmin},
            }
            for key, factor in self.factors.items()
            if key not in self.archive
        ]
        actions.extend(
            {
                "action_id": "verify:" + key,
                "kind": "verify",
                "description": "Recompute VLE directly at every retained stage and rate with linear interpolation.",
            }
            for key, result in self.archive.items()
            if result["status"] == "valid"
            and result["meets_targets"]
            and not result["verified"]
            and not result.get("verification_attempted", False)
        )
        return actions

    def execute(self, action_id: str) -> dict[str, Any]:
        if action_id.startswith("verify:"):
            identity = action_id.split(":", 1)[1]
            if identity not in self.archive:
                raise ValueError("No retained design exists for this verification")
            self.archive[identity]["verification_attempted"] = True
            try:
                return self._verify(identity)
            except (ValueError, RuntimeError) as error:
                result = self.archive[identity]
                result["verified"] = False
                result["evidence_gaps"] = ["Verification failed: " + str(error)]
                result["verification"] = {"status": "failed", "reason": str(error)}
                return result
        if action_id not in self.factors:
            raise ValueError("Unknown C3 numerical action")
        try:
            reflux = self.factors[action_id] * self.rmin
            estimate = construct_column(self.curve, self.spec, reflux)
            rating = rate_column(
                self.curve,
                self.spec,
                reflux,
                estimate["stages_including_reboiler"],
                estimate["feed_stage_from_top"],
                estimate["initial_x_profile"],
            )
            result = {
                **rating,
                "status": "valid" if rating["numerical_checks"]["passed"] else "failed",
                "candidate_id": action_id,
                "verified": False,
                "evidence_gaps": ["direct stage equilibrium review pending"],
                "limitations": self._limitations(),
                "minimum_reflux_ratio": self.rmin,
            }
        except (ValueError, RuntimeError) as error:
            result = {
                "status": "failed",
                "candidate_id": action_id,
                "meets_targets": False,
                "verified": False,
                "numerical_checks": {"passed": False},
                "metrics": {},
                "evidence_gaps": [str(error)],
                "limitations": self._limitations(),
            }
        self.archive[action_id] = result
        return result

    def _verify(self, candidate_id: str) -> dict[str, Any]:
        result = self.archive[candidate_id]
        audit_curve = self.curve
        rounds: list[dict[str, Any]] = []
        direct_ok = False
        for iteration in range(4):
            profile, metrics = result["profiles"], result["metrics"]
            x = np.array(profile["x_propene"])
            states = [self.direct_bubble(float(value)) for value in x]
            direct_y = np.array([state["y_propene"] for state in states])
            error = float(np.max(np.abs(direct_y - np.array(profile["y_propene"]))))
            states_pass = all(state["validation"]["passed"] for state in states)
            d, b = product_flows(self.spec)
            f = self.spec.feed_flow_mol_s
            liquid, vapor = metrics["reflux_ratio"] * d, (metrics["reflux_ratio"] + 1) * d
            feed_index = metrics["feed_stage_from_top"] - 1
            balances = [vapor * direct_y[1] - liquid * x[0] - d * direct_y[0]]
            for index in range(1, len(x) - 1):
                lin = liquid + (f if index > feed_index else 0)
                lout = liquid + (f if index >= feed_index else 0)
                balances.append(
                    lin * x[index - 1]
                    + vapor * direct_y[index + 1]
                    - lout * x[index]
                    - vapor * direct_y[index]
                    + (f * self.spec.feed_propene if index == feed_index else 0)
                )
            balances.append((liquid + f) * x[-2] - b * x[-1] - vapor * direct_y[-1])
            stage_error = float(np.max(np.abs(balances)) / max(f, vapor, liquid + f))
            overall_error = float(abs(d * direct_y[0] + b * x[-1] - f * self.spec.feed_propene) / f)
            direct_checks = validate_equilibrium_result(
                np.r_[np.c_[x, 1 - x], np.c_[direct_y, 1 - direct_y]],
                max(state["equilibrium_residual"] for state in states),
                material_residual=max(stage_error, overall_error),
                temperatures=[state["temperature_k"] for state in states],
            )
            direct_targets = (
                direct_y[0] >= self.spec.target_distillate_propene
                and x[-1] < self.spec.maximum_bottoms_propene_exclusive
            )
            direct_ok = bool(states_pass and direct_checks["passed"] and direct_targets)
            rounds.append(
                {
                    "round": iteration,
                    "maximum_y_error": error,
                    "direct_stage_balance_residual": stage_error,
                    "direct_overall_component_residual": overall_error,
                    "direct_targets_met": bool(direct_targets),
                    "direct_validation": direct_checks,
                }
            )
            if direct_ok or iteration == 3:
                break
            # Insert the independently recomputed stage states, then solve all stage
            # balances again at the same hardware, reflux and product flow split.
            points = {
                value: (audit_curve.y_propene[index], audit_curve.temperature_k[index])
                for index, value in enumerate(audit_curve.x_propene)
            }
            points.update(
                {float(x[index]): (state["y_propene"], state["temperature_k"]) for index, state in enumerate(states)}
            )
            ordered = sorted(points)
            audit_curve = C3EquilibriumCurve(
                pressure_kpa=self.spec.pressure_kpa,
                x_propene=ordered,
                y_propene=[points[value][0] for value in ordered],
                temperature_k=[points[value][1] for value in ordered],
                maximum_equilibrium_residual=max(
                    audit_curve.maximum_equilibrium_residual, max(state["equilibrium_residual"] for state in states)
                ),
                source=self.curve.source + ":direct_stage_refinement",
                point_validation_passed=states_pass,
            )
            rating = rate_column(
                audit_curve,
                self.spec,
                metrics["reflux_ratio"],
                metrics["stages_including_reboiler"],
                metrics["feed_stage_from_top"],
                profile["x_propene"],
            )
            result.update(rating)
            if not rating["numerical_checks"]["passed"]:
                break
        # This is an interpolation sensitivity audit, not a second physical model.
        dense_x = np.linspace(0, 1, 10001)
        linear_y = np.interp(dense_x, audit_curve.x_propene, audit_curve.y_propene)
        linear_t = np.interp(dense_x, audit_curve.x_propene, audit_curve.temperature_k)
        linear_curve = C3EquilibriumCurve(
            **{
                **audit_curve.model_dump(),
                "x_propene": dense_x.tolist(),
                "y_propene": linear_y.tolist(),
                "temperature_k": linear_t.tolist(),
                "source": self.curve.source + ":linear_interpolation_audit",
            }
        )
        metrics = result["metrics"]
        sensitivity = rate_column(
            linear_curve,
            self.spec,
            metrics["reflux_ratio"],
            metrics["stages_including_reboiler"],
            metrics["feed_stage_from_top"],
            profile["x_propene"],
        )
        sensitivity_ok = sensitivity["numerical_checks"]["passed"] and sensitivity["meets_targets"]
        result["verified"] = bool(direct_ok and sensitivity_ok)
        result["evidence_gaps"] = [] if result["verified"] else ["direct/interpolation numerical audit did not pass"]
        result["verification"] = {
            "direct_stage_states": states,
            "maximum_direct_vs_interpolated_y_error": error,
            "all_direct_states_numerically_valid": states_pass,
            "direct_column_validation": direct_checks,
            "refinement_rounds": rounds,
            "interpolation_sensitivity_rating": sensitivity,
            "interpolation_sensitivity_method": "dense linear resampling followed by local PCHIP rating",
            "scope": "numerical review; no experimental accuracy or global phase-stability certification",
        }
        return result

    @staticmethod
    def _limitations() -> list[str]:
        return [
            "No real process experiment is available; this is a calculated preliminary design.",
            "The .996 propene and <.01 impurity regions lack direct mixed-phase VLE coverage.",
            "Constant molar overflow, q=1, no pressure drop and equilibrium stages are assumed.",
            "Energy duties, real tray efficiency, equipment sizing and economics are not calculated.",
            "Convergence does not certify global phase stability or global design optimality.",
        ]

    def assess(self) -> dict[str, Any]:
        candidates = [
            result
            for result in self.archive.values()
            if result["status"] == "valid"
            and result["meets_targets"]
            and result["verified"]
            and result["numerical_checks"]["passed"]
        ]
        preferred = min(candidates, key=lambda result: result["metrics"]["reflux_ratio"]) if candidates else None
        return {
            "can_report_preliminary": preferred is not None,
            "preferred_candidate_id": preferred["candidate_id"] if preferred else None,
            "evidence_gaps": [] if preferred else ["No numerically reviewed, target-satisfying candidate yet"],
            "stopping_reason": "validated_preliminary_candidate_with_limits" if preferred else None,
            "limitations": self._limitations(),
            "archive": {
                key: {k: v for k, v in result.items() if k not in {"profiles", "verification"}}
                for key, result in self.archive.items()
            },
        }
