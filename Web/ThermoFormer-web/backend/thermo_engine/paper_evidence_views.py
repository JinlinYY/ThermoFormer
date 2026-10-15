"""Read-only evidence interventions on validated, hashed paper calculations.

No synthetic equilibrium values: only select an existing candidate, withhold
diagnostics, or evaluate the binary result against an explicitly changed stage cap.
"""

from __future__ import annotations

import copy
from typing import Any


def evidence_views(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Return public packets and separate evaluator labels; never send labels to LLM."""
    if not bundle["paper_agreement"]["passed"] or not all(
        o["status"] == "valid" and o["numerical_checks"]["passed"] for o in bundle["observations"]
    ):
        raise ValueError("Evidence views require validated source calculations")
    case = bundle["protocol"]
    full: dict[str, Any] = dict(
        case=case,
        source="cached validated ThermoFormer / paper solver outputs; no new numerical inference",
        design=copy.deepcopy(bundle["final"]),
        numerical_validation=dict(available=True, passed=True, global_phase_stability="not_certified"),
        experimental_process_confirmation=False,
        global_optimality_proven=False,
    )
    if case == "binary":
        full["targets"] = dict(stage_cap=13, required_to_hold_for_both_reported_interpolations=True)
        full["target_check"] = dict(
            all_required_targets_met=max(full["design"]["pchip_stages"], full["design"]["linear_stages"]) <= 13
        )
        full["limitation"] = "Stage requirement depends on interpolation; retain both counts."
    elif case == "extractive":
        full["targets"] = dict(ester_purity=0.995, ester_recovery=0.98)
        full["target_check"] = dict(all_required_targets_met=bool(full["design"]["meets_targets"]))
        full["limitation"] = "Selected trajectory is outside the available 17-point experimental coverage."
    else:
        full["targets"] = dict(benzene_recovery=0.7, initial_heptane_retention=0.8)
        full["target_check"] = dict(all_required_targets_met=bool(full["design"]["meets_targets"]))
        full["limitation"] = "Stage and allocation conclusions concern only the tested finite candidate set."
    withheld = copy.deepcopy(full)
    withheld["numerical_validation"] = dict(available=False, reason="withheld in this evidence-ablation experiment")
    contrast = copy.deepcopy(full)
    if case == "binary":
        contrast["targets"]["stage_cap"] = 12
        contrast["target_check"] = dict(all_required_targets_met=False, interpolation_sensitive_feasibility=True)
        contrast["intervention"] = "Counterfactual stage cap only; original paper inputs and results are unchanged."
    elif case == "extractive":
        contrast["design"] = copy.deepcopy(bundle["observations"][1]["metrics"])
        contrast["target_check"] = dict(all_required_targets_met=bool(bundle["observations"][1]["meets_targets"]))
        contrast["intervention"] = "Use the already computed 182-stage boundary candidate, before rounding."
    else:
        contrast["design"] = copy.deepcopy(bundle["observations"][1]["metrics"])
        contrast["target_check"] = dict(all_required_targets_met=bool(bundle["observations"][1]["meets_targets"]))
        contrast["intervention"] = "Use the already computed two-stage cascade at the original solvent budget."
    return [
        dict(
            condition="complete",
            packet=full,
            expected_action="report_preliminary",
            required_ids=["design", "target_check", "numerical_validation", "limitation"],
        ),
        dict(
            condition="validation_withheld",
            packet=withheld,
            expected_action="request_verification",
            required_ids=["numerical_validation"],
        ),
        dict(
            condition="constraint_not_met",
            packet=contrast,
            expected_action="withhold_target_claim",
            required_ids=["design", "target_check"],
        ),
    ]
