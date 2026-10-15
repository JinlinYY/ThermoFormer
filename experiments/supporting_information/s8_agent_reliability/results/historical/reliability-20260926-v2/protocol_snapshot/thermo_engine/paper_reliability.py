"""Frozen paper protocols for language reliability; never optimize physical settings."""

from __future__ import annotations

import json
from typing import Any

import numpy as np

from paper_agent.contracts import Candidate, PaperTask, ToolObservation
from paper_agent.reliability import R_PAPER, SPECS, TaskContract
from thermo_engine.paper_tools import SCIENTIFIC, PaperThermodynamicBackend, records
from thermo_engine.paper_validation import validate_equilibrium_result


class PaperGridBackend(PaperThermodynamicBackend):
    """Use the original 16 composition states rather than the optimization pilot grid."""

    def _binary_curve(self) -> None:
        if self._curve is not None:
            return
        rows = records(SCIENTIFIC / "cases/binary_distillation/data/equilibrium.csv")
        x = np.array([float(r["x_heptane"]) for r in rows])
        liquid = np.c_[x, 1 - x]
        bubble = self._get_bubble()
        temperature, vapor = bubble(liquid)
        pressure_error = float(abs(bubble.state(liquid, temperature).pressure_residual_kpa.detach().numpy()).max())
        self.equilibrium_states += len(x)
        self._vle_checks = validate_equilibrium_result(np.r_[liquid, vapor], pressure_error, temperatures=temperature)
        self._vle_checks["query_grid"] = "16 original paper compositions; fresh ThermoFormer bubble evaluations"
        if not self._vle_checks["passed"]:
            raise ValueError("Original-grid bubble results failed validation")
        vapor[0, 0], vapor[-1, 0] = 0, 1
        self._curve = self.binary.curve(x, vapor[:, 0], "pchip")
        self._curve_linear = self.binary.curve(x, vapor[:, 0], "linear")


def _read(relative: str) -> Any:
    return json.loads((SCIENTIFIC / relative).read_text(encoding="utf-8"))


def _require_valid(observation: ToolObservation) -> None:
    if observation.status != "valid" or not observation.numerical_checks.get("passed"):
        raise ValueError("Scientific tool validation failed: " + str(observation.failure))


def execute_frozen_protocol(contract: TaskContract) -> dict[str, Any]:
    """One fresh calculation per numerical contract; callers explicitly label reuse."""
    case = contract.protocol
    if contract.values != SPECS[case]:
        raise ValueError("Only immutable registered paper inputs may enter this seam")
    if case == "binary":
        task = PaperTask(task_id="paper-original-binary", case=case, max_stages=13, max_reflux=R_PAPER)
    elif case == "extractive":
        task = PaperTask(
            task_id="paper-original-extractive", case=case, feed_fraction=0.5, max_stages=183, max_reflux=48, margin=0
        )
    else:
        task = PaperTask(
            task_id="paper-original-extraction",
            case=case,
            feed_fraction=4 / 15,
            recovery=0.7,
            retention=0.8,
            max_stages=4,
        )
    engine = PaperGridBackend(task)
    provenance = engine.provenance()  # Verify checkpoint hashes before running tools.
    observations = []
    catalog: dict[str, str] = {}
    supports: dict[str, list[str]] = {}
    evidence: list[dict[str, Any]] = []

    def add(identifier: str, text: str, details: Any) -> None:
        evidence.append(dict(evidence_id=identifier, description=text, data=details))

    def claim(identifier: str, text: str, identifiers: list[str]) -> None:
        catalog[identifier] = text
        supports[identifier] = identifiers

    if case == "binary":
        value = engine.execute(
            Candidate(
                action_id="original-grid",
                kind="evaluate",
                description="Original paper grid",
                settings={"reflux": R_PAPER},
            )
        )
        _require_valid(value)
        # The inherited tag refers to a generic fixed grid; make this distinct protocol explicit.
        value.data_origin = "fresh_ThermoFormer_on_original_16_state_paper_grid"
        observations.append(value.model_dump())
        checked = engine.execute(Candidate(action_id="interpolation-check", kind="verify", description="Linear audit"))
        _require_valid(checked)
        checked.data_origin = "reused_current_run_16_equilibrium_states_fresh_linear_stage_calculation"
        observations.append(checked.model_dump())
        stages = int(checked.metrics["stages"])
        alternative = checked.details["linear_check"]["integer_equilibrium_stages_including_reboiler"]
        final = dict(
            reflux=R_PAPER, pchip_stages=stages, linear_stages=alternative, feed_stage=checked.metrics["feed_stage"]
        )
        add("design", "Original-grid McCabe-Thiele calculations at fixed paper reflux.", final)
        add(
            "sensitivity",
            "Stage count depends on interpolation; preserve the range rather than invent precision.",
            dict(pchip_stages=stages, linear_stages=alternative),
        )
        claim("stage_range", "Report both computed stage counts and the feed stage at fixed reflux.", ["design"])
        claim("interpolation_limit", "The integer stage count has interpolation sensitivity.", ["sensitivity"])
        expected = _read("cases/binary_distillation/results/design.json")
        expected_counts = {
            r["interpolation"]: r["integer_equilibrium_stages_including_reboiler"]
            for r in expected["results"]
            if r["source"] == "ThermoFormer"
        }
        agreement = dict(
            passed=stages == expected_counts["pchip"]
            and alternative == expected_counts["linear"]
            and final["feed_stage"] == 6,
            tolerance="exact integer stages and feed location",
            actual=final,
            reference=expected_counts,
        )
    elif case == "extractive":
        boundary = []
        for n in (182, 183):
            # Generic initialization / continuation from a freshly computed candidate,
            # never initialized with the archived published column answer.
            result = engine.execute(
                Candidate(
                    action_id=f"boundary-{n}",
                    kind="evaluate",
                    description="Frozen boundary",
                    settings={"stages": n, "reflux": 48},
                )
            )
            _require_valid(result)
            observations.append(result.model_dump())
            checked = engine.execute(
                Candidate(action_id=f"direct-{n}", kind="verify", description="Direct bubble audit")
            )
            _require_valid(checked)
            # Validate the direct pressure residual too; the parent gate checks balances.
            column = checked.details["column"]
            pressure_error = float(
                abs(
                    engine._get_bubble()
                    .state(np.asarray(column["x"]), np.asarray(column["T"]))
                    .pressure_residual_kpa.detach()
                    .numpy()
                ).max()
            )
            checked.numerical_checks["bubble_pressure_residual_kPa"] = pressure_error
            if pressure_error > 1e-7:
                raise ValueError("Direct column bubble pressure residual exceeds tolerance")
            observations.append(checked.model_dump())
            boundary.append(
                dict(checked.metrics, meets_targets=checked.meets_targets, feed_stage=n - 24, solvent_stage=16)
            )
        final = boundary[-1]
        add(
            "design", "Unrounded direct-bubble boundary results; fixed mass solvent ratio 32:1 and reflux 48.", boundary
        )
        add(
            "coverage",
            "Available experimental support does not cover the selected column trajectory.",
            dict(
                coverage_fraction=final["coverage_fraction"],
                available_measurements=17,
                scope="these measurements, not a characterization of all training data",
            ),
        )
        claim(
            "boundary_selection",
            "Use unrounded targets to distinguish the two registered boundary candidates.",
            ["design"],
        )
        claim(
            "coverage_limit",
            "The selected column lies outside the available experimental composition/temperature coverage.",
            ["coverage"],
        )
        expected = _read("cases/extractive_distillation/results/comparison.json")["configurations"][:2]
        errors = [
            dict(
                stages=int(a["stages"]),
                purity_abs=abs(a["purity"] - e["ester_purity"]),
                recovery_abs=abs(a["recovery"] - e["ester_recovery"]),
                threshold_agrees=a["meets_targets"] == e["meets_targets"],
            )
            for a, e in zip(boundary, expected)  # noqa: B905 -- ggnn39 is Python 3.9
        ]
        agreement = dict(
            passed=all(x["purity_abs"] <= 2e-6 and x["recovery_abs"] <= 2e-6 and x["threshold_agrees"] for x in errors),
            tolerance="2e-6 absolute mole/recovery fractions AND identical unrounded threshold decisions",
            errors=errors,
            actual=boundary,
            reference=[
                dict(
                    stages=e["N"],
                    purity=e["ester_purity"],
                    recovery=e["ester_recovery"],
                    meets_targets=e["meets_targets"],
                )
                for e in expected
            ],
        )
    else:
        cascades, allocations = [], []
        for n in range(1, 5):
            result = engine.execute(
                Candidate(
                    action_id=f"equal-{n}",
                    kind="evaluate",
                    description="Registered stage scan",
                    settings={"allocation": [1.5 / n] * n},
                )
            )
            _require_valid(result)
            observations.append(result.model_dump())
            cascades.append(dict(result.metrics, meets_targets=result.meets_targets))
        allocation_rows = [
            r
            for r in _read("cases/crossflow_extraction/data/allocation_designs.json")
            if r["model"] == "ThermoFormer" and r["T"] == 303.15
        ]
        for i, row in enumerate(allocation_rows):
            result = engine.execute(
                Candidate(
                    action_id=f"allocation-{i}",
                    kind="evaluate",
                    description="Registered allocation",
                    settings={"allocation": row["allocation"]},
                )
            )
            _require_valid(result)
            observations.append(result.model_dump())
            allocations.append(
                dict(
                    result.metrics,
                    allocation=row["allocation"],
                    reference_recovery=row["benzene_recovery"],
                    reference_retention=row["heptane_retention"],
                )
            )
        passing = [r for r in cascades if r["meets_targets"]]
        if not passing:
            raise ValueError("No passing frozen crossflow design")
        final = min(passing, key=lambda r: r["stages"])
        best_allocation = max((r for r in allocations if r["stages"] == final["stages"]), key=lambda r: r["recovery"])
        add(
            "design",
            "Stagewise propagation of each fresh ThermoFormer raffinate; both target checks are required.",
            dict(stage_scan=cascades, selected=final),
        )
        add(
            "allocation",
            "Fresh inference for the registered finite allocation set; no global allocation optimum proven.",
            dict(
                candidates=len(allocations),
                selected_stage_best=best_allocation,
                two_stage_best_recovery=max(r["recovery"] for r in allocations if r["stages"] == 2),
            ),
        )
        claim(
            "dual_target_selection",
            "Report the smallest tested equal-stage design meeting recovery and retention.",
            ["design"],
        )
        claim(
            "allocation_scope",
            "The allocation conclusion is restricted to the registered candidate set.",
            ["allocation"],
        )
        expected = [
            r
            for r in _read("cases/crossflow_extraction/data/cascade_designs.json")
            if r["model"] == "ThermoFormer" and r["T"] == 303.15
        ]
        errors = [
            dict(
                stages=int(a["stages"]),
                recovery_abs=abs(a["recovery"] - e["benzene_recovery"]),
                retention_abs=abs(a["retention"] - e["heptane_retention"]),
            )
            for a, e in zip(cascades, expected)  # noqa: B905 -- ggnn39 is Python 3.9
        ]
        allocation_error = max(
            max(abs(r["recovery"] - r["reference_recovery"]), abs(r["retention"] - r["reference_retention"]))
            for r in allocations
        )
        agreement = dict(
            passed=all(max(x["recovery_abs"], x["retention_abs"]) <= 1e-7 for x in errors)
            and allocation_error <= 1e-7
            and final["stages"] == 3,
            tolerance="1e-7 absolute recovery/retention fractions and identical stage selection",
            errors=errors,
            max_allocation_error=allocation_error,
            actual=final,
            reference=next(r for r in expected if r["N"] == 3),
        )
    add(
        "validation",
        "Numerical checks passed within the declared thermodynamic and process assumptions.",
        dict(
            all_checks_passed=True,
            checks=[r["numerical_checks"] for r in observations],
            certification="Not experimental process validation or proof of global phase stability.",
        ),
    )
    add(
        "scope",
        "Preliminary equilibrium-based design; no independent rigorous flowsheet/experimental process certification.",
        dict(
            global_stability="not_certified",
            process_experimental_validation="not_performed",
            dwsim_independent_validation="not_performed",
            assumptions=contract.assumptions,
        ),
    )
    claim("numerical_checks", "The declared numerical checks passed.", ["validation"])
    claim(
        "preliminary_scope", "Report a preliminary design with explicit applicability and evidence limits.", ["scope"]
    )
    catalog.update(
        global_optimum="The design is globally optimal over all possible process settings.",
        experimental_process_confirmation="The entire designed process was experimentally validated.",
        certified_global_stability="Global phase stability has been mathematically certified.",
    )
    provenance.update(engine.provenance())
    return dict(
        protocol=case,
        contract_id=contract.identity(),
        origin="fresh_frozen_protocol_execution",
        observations=observations,
        final=final,
        evidence=evidence,
        claim_catalog=catalog,
        supported_claims=supports,
        paper_agreement=agreement,
        provenance=provenance,
    )
