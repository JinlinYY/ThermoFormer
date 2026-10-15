"""Paper-case numerical adapter with isolated solver instances.

Each adapter loads private solver modules so parameterizing a case does not
change another calculation's process-global constants.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
from scipy.spatial import Delaunay

from paper_agent.contracts import Candidate, PaperTask, ToolObservation
from thermo_engine.paper_validation import validate_equilibrium_result

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = Path(__file__).resolve().parents[4]
SCIENTIFIC = REPOSITORY / "ThermoAgent"


def load_solver(name: str) -> Any:
    spec = importlib.util.spec_from_file_location("_paper_" + name + uuid4().hex, SCIENTIFIC / (name + ".py"))
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load paper solver")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def records(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


class PaperThermodynamicBackend:
    """Typed public seam; no LLM-supplied numerical results enter this class."""

    def __init__(self, task: PaperTask):
        self.task = task
        if str(SCIENTIFIC) not in sys.path:
            sys.path.insert(0, str(SCIENTIFIC))
        self.binary = load_solver("binary")
        self.extraction = load_solver("extraction")
        self.column = load_solver("column")
        self._bubble: Any = None
        self._split: Any = None
        self._curve: Any = None
        self._curve_linear: Any = None
        self._vle_checks: dict[str, Any] = {}
        self.last: ToolObservation | None = None
        self.settings: dict[str, Any] = {}
        self.column_surface: Any = None
        self.prior_column: dict[str, Any] | None = None
        self.equilibrium_states = 0
        self.column_solves = 0
        self.binary.F = 1.0
        self.binary.Z = task.feed_fraction
        self.binary.XD = task.purity
        self.binary.RECOVERY = task.recovery
        self.binary.D = task.feed_fraction * task.recovery / task.purity
        self.binary.B = 1 - self.binary.D
        self.binary.XB = (task.feed_fraction - self.binary.D * task.purity) / self.binary.B
        self.extraction.FEED = np.array([1 - task.feed_fraction, 0.0, task.feed_fraction])

    def provenance(self) -> dict[str, Any]:
        data = json.loads((SCIENTIFIC / "provenance.json").read_text(encoding="utf-8"))
        name = {
            "binary": "binary_distillation",
            "extractive": "extractive_distillation",
            "extraction": "crossflow_extraction",
        }[self.task.case]
        source = data[name]
        actual = hashlib.sha256((REPOSITORY / source["checkpoint"]).read_bytes()).hexdigest()
        if actual != source["checkpoint_sha256"]:
            raise ValueError("Paper checkpoint is missing or does not match registered SHA-256")
        return dict(
            checkpoint=source["checkpoint"],
            checkpoint_sha256=actual,
            python=sys.executable,
            python_version=sys.version.split()[0],
            runtime_environment={key: os.getenv(key) for key in ("MKL_THREADING_LAYER", "OMP_NUM_THREADS")},
            scientific_sources={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in SCIENTIFIC.glob("*.py")},
            orchestration_sources={
                str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in list((ROOT / "paper_agent").glob("*.py"))
                + [ROOT / "thermo_engine/paper_tools.py", ROOT / "thermo_engine/paper_validation.py"]
            },
            case_data_sources={
                str(p.relative_to(SCIENTIFIC)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (SCIENTIFIC / "cases" / name).rglob("*")
                if p.is_file() and p.suffix in {".json", ".csv"}
            },
            equilibrium_states=self.equilibrium_states,
            column_solves=self.column_solves,
            pressure_kPa=101.3,
            feed_flow_mol_s=1.0,
            initialization="generic_or_previous_computed_candidate; no published column trajectory",
        )

    def _get_bubble(self) -> Any:
        if self._bubble is None:
            from inference import ThermoFormerBubble  # type: ignore[import-not-found]

            case = "binary_distillation" if self.task.case == "binary" else "extractive_distillation"
            self._bubble = ThermoFormerBubble(case, REPOSITORY)
        return self._bubble

    def _binary_curve(self) -> None:
        if self._curve is not None:
            return
        # A fixed model-query grid, independent of experimental response values.
        x = np.linspace(0, 1, 41)
        liquid = np.c_[x, 1 - x]
        bubble = self._get_bubble()
        temperature, vapor = bubble(liquid)
        pressure_error = float(abs(bubble.state(liquid, temperature).pressure_residual_kpa.detach().numpy()).max())
        self.equilibrium_states += len(x)
        self._vle_checks = validate_equilibrium_result(np.r_[liquid, vapor], pressure_error, temperatures=temperature)
        if not self._vle_checks["passed"]:
            raise ValueError("Fresh binary equilibrium failed validation")
        vapor[0, 0], vapor[-1, 0] = 0, 1  # exact pure-component identities
        self._curve = self.binary.curve(x, vapor[:, 0], "pchip")
        self._curve_linear = self.binary.curve(x, vapor[:, 0], "linear")

    def _binary(self, settings: dict[str, Any], verify: bool) -> ToolObservation:
        self._binary_curve()
        reflux = float(settings["reflux"])
        result = self.binary.stages(self._curve, reflux)
        stages = result["integer_equilibrium_stages_including_reboiler"]
        alternative = self.binary.stages(self._curve_linear, reflux) if verify else None
        stable = alternative is None or alternative["integer_equilibrium_stages_including_reboiler"] == stages
        meets = stages <= self.task.max_stages and reflux <= self.task.max_reflux
        gaps = (
            []
            if verify and stable
            else ["interpolation_sensitivity_unchecked" if not verify else "stage_count_sensitive_to_interpolation"]
        )
        return ToolObservation(
            status="valid",
            meets_targets=meets,
            verified=verify,
            metrics={
                "stages": stages,
                "feed_stage": result["feed_stage_from_top"],
                "reflux": reflux,
                "minimum_reflux": self.binary.minimum_reflux(self._curve),
            },
            numerical_checks=self._vle_checks,
            evidence_gaps=gaps,
            data_origin="fresh_ThermoFormer_on_fixed_grid",
            details={"profile": result, "linear_check": alternative, "settings": settings},
        )

    def _extraction(self, settings: dict[str, Any]) -> ToolObservation:
        if self._split is None:
            from lle_inference import ThermoFormerSplit  # type: ignore[import-not-found]

            self._split = ThermoFormerSplit(REPOSITORY)
        allocation = list(settings["allocation"])
        if abs(sum(allocation) - self.task.solvent_total) > 1e-9:
            raise ValueError("Solvent allocation violates the fixed total budget")
        result = self.extraction.cascade(allocation, lambda z: self._split.split(self.task.temperature_K, z))
        self.equilibrium_states += len(allocation)
        compositions = [s[key] for s in result["stages"] for key in ("z", "xE", "xR")]
        error = max(s["component_balance_error_mol_s"] for s in result["stages"])
        checks = validate_equilibrium_result(
            compositions, error, material_residual=result["overall_component_balance_error"]
        )
        checks["upstream_equilibrium_gate"] = "chemical_potential_RMS<=1e-3; finite_grid_TPD>=-1e-4"
        recovery, retention = result["benzene_recovery"], result["heptane_retention"]
        return ToolObservation(
            status="valid" if checks["passed"] else "failed",
            verified=checks["passed"],
            meets_targets=checks["passed"] and recovery >= self.task.recovery and retention >= self.task.retention,
            metrics={
                "recovery": recovery,
                "retention": retention,
                "stages": len(allocation),
                "solvent_total": sum(allocation),
            },
            numerical_checks=checks,
            data_origin="fresh_ThermoFormer_LLE_at_each_propagated_feed",
            details={"cascade": result, "settings": settings},
        )

    def _extractive(self, settings: dict[str, Any], verify: bool) -> ToolObservation:
        from solve_column import Surface  # type: ignore[import-not-found]

        n, reflux = int(settings["stages"]), float(settings["reflux"])
        nf, ns = n - 24, 16
        solvent, distillate = self.column.S, self.column.D
        surface = Surface(SCIENTIFIC / "cases/extractive_distillation/data/thermoformer_surface.json")
        initial = None if self.prior_column is None else np.asarray(self.prior_column["rs"])
        result = self.column.solve(surface, n, nf, ns, reflux, solvent, distillate, init=initial, maxeval=80)
        self.column_solves += 1
        if verify:
            bubble = self._get_bubble()
            for _ in range(4):
                initial = np.asarray(result["rs"])
                x, grid_y, grid_t = surface.state(initial)
                temperature, y = bubble(x)
                self.equilibrium_states += len(x)
                surface.delta += np.log(y / grid_y)
                surface.dt += temperature - grid_t
                balance, _, _, _ = self.column.residual(initial, surface, n, nf, ns, reflux, solvent, distillate, True)
                error = float(abs(balance).max())
                result.update(
                    x=x.tolist(),
                    y=y.tolist(),
                    T=temperature.tolist(),
                    xD=y[0].tolist(),
                    recovery=distillate * y[0, 1] / 0.5,
                    mass_residual=error,
                    success=error < 1e-7,
                )
                if error < 1e-8:
                    break
                result = self.column.solve(surface, n, nf, ns, reflux, solvent, distillate, init=initial, maxeval=80)
                self.column_solves += 1
            else:
                raise ValueError("Direct bubble refinement exceeded its four-step budget")
        x, y, temperature = [np.asarray(result[key]) for key in ("x", "y", "T")]
        bottom = 1 + solvent - distillate
        global_error = float(
            abs(self.column.Z + solvent * np.array([0, 0, 1]) - distillate * y[0] - bottom * x[-1]).max()
        )
        result.update(xB=x[-1].tolist(), global_residual=global_error)
        checks = validate_equilibrium_result(
            np.r_[x, y], float(result["mass_residual"]), material_residual=global_error, temperatures=temperature
        )
        rows = records(SCIENTIFIC / "cases/extractive_distillation/data/equilibrium.csv")
        reference_x = np.array([[float(r["x_alcohol"]), float(r["x_ester"])] for r in rows])
        inside = Delaunay(reference_x).find_simplex(x[:, :2]) >= 0
        t_ref = np.array([float(r["T_exp_K"]) for r in rows])
        covered = inside & (temperature >= t_ref.min()) & (temperature <= t_ref.max())
        purity, recovery = float(y[0, 1]), float(distillate * y[0, 1] / 0.5)
        margin = min(purity - self.task.purity, recovery - self.task.recovery)
        gaps = []
        if not verify:
            gaps.append("direct_bubble_verification_missing")
        if not covered.all():
            gaps.append("trajectory_outside_available_experimental_coverage")
        if margin < self.task.margin:
            gaps.append("product_margin_below_requested_guard")
        if checks["passed"]:
            self.prior_column = result
        return ToolObservation(
            status="valid" if checks["passed"] else "failed",
            verified=verify and checks["passed"],
            meets_targets=checks["passed"] and purity >= self.task.purity and recovery >= self.task.recovery,
            metrics={
                "purity": purity,
                "recovery": recovery,
                "margin": margin,
                "coverage_fraction": float(covered.mean()),
                "stages": n,
                "reflux": reflux,
            },
            numerical_checks=checks,
            evidence_gaps=gaps,
            failure=None if checks["passed"] else "column_balance_validation_failed",
            data_origin="fresh_direct_bubble_refinement" if verify else "registered_neural_equilibrium_grid",
            details={
                "column": result,
                "settings": settings,
                "coverage_scope": "17 available measurements, not the entire training domain",
            },
        )

    def execute(self, candidate: Candidate) -> ToolObservation:
        verify = candidate.kind == "verify"
        settings = dict(self.settings if verify and not candidate.settings else candidate.settings)
        try:
            if self.task.case == "binary":
                result = self._binary(settings, verify)
            elif self.task.case == "extraction":
                result = self._extraction(settings)
            else:
                result = self._extractive(settings, verify)
        except (ValueError, RuntimeError, FloatingPointError) as exc:
            result = ToolObservation(
                status="failed", failure=str(exc), data_origin="tool_execution", details={"settings": settings}
            )
        self.last, self.settings = result, settings
        return result

    def assess(self, observation: ToolObservation | None) -> dict[str, Any]:
        """Post-run evaluation only. This output is never sent back to a policy."""
        if observation is None or observation.status != "valid":
            return {"reference_status": "unavailable", "reference_meets_targets": None}
        settings = observation.details["settings"]
        try:
            if self.task.case == "binary":
                rows = records(SCIENTIFIC / "cases/binary_distillation/data/equilibrium.csv")
                eq = self.binary.curve(
                    np.array([float(r["x_heptane"]) for r in rows]),
                    np.array([float(r["y_exp"]) for r in rows]),
                    "pchip",
                )
                count = self.binary.stages(eq, settings["reflux"])["integer_equilibrium_stages_including_reboiler"]
                return {
                    "reference_status": "experiment_derived_equilibrium_stage_calculation",
                    "reference_meets_targets": count <= self.task.max_stages,
                    "reference_stages": count,
                }
            if self.task.case == "extraction":
                protocol = json.loads(
                    (SCIENTIFIC / "cases/crossflow_extraction/data/interpolation_protocol.json").read_text()
                )
                pairs = np.asarray(protocol["pairs_by_temperature"][str(self.task.temperature_K)])
                result = self.extraction.cascade(
                    settings["allocation"], lambda z: self.extraction.experimental_split(pairs, z, "linear")
                )
                return {
                    "reference_status": "experiment_derived_equilibrium_stage_calculation",
                    "reference_meets_targets": bool(
                        result["benzene_recovery"] >= self.task.recovery
                        and result["heptane_retention"] >= self.task.retention
                    ),
                    "reference_recovery": result["benzene_recovery"],
                    "reference_retention": result["heptane_retention"],
                }
        except (ValueError, KeyError) as exc:
            return {
                "reference_status": "outside_reference_support",
                "reference_meets_targets": None,
                "reason": str(exc),
            }
        return {"reference_status": "no_independent_column_reference", "reference_meets_targets": None}
