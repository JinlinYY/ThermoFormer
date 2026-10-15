"""Evidence-gated live LLM controller for an isolated C3 calculation case.

Numerical work belongs to an injected thermo_engine backend. This controller
never invokes the original paper's heptane/nonane protocol and never treats
specified product targets as independently measured process results.
"""

from __future__ import annotations

import copy
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from paper_agent.policy import ProviderFailure
from paper_agent.reliability import ReliabilityLLM

DEFAULT_REQUEST = (
    "原料为丙烷65 mol%、丙烯35 mol%；丙烷产品中的丙烯严格小于1 mol%，"
    "丙烯产品纯度至少99.6 mol%。没有实际分离实验，完成独立计算案例。"
)
CASE_SCOPE = "calculation_case_no_process_experiments"
LIMITATIONS = [
    "No independent process-separation experiment is available.",
    "Product specifications define a preliminary equilibrium-stage design, not measured product performance.",
    "Reflux and stage counts are resource proxies, not computed energy or economic costs.",
    "A bounded candidate search does not establish a global optimum.",
]
ASSUMPTIONS: dict[str, Any] = {
    "pressure_kPa": 1000.0,
    "feed_flow_mol_s": 1.0,
    "feed_quality_q": 1.0,
    "constant_molar_overflow": True,
    "total_condenser": True,
    "equilibrium_reboiler": True,
    "origin": "declared_calculation_assumptions_not_user_measurements",
}
SYSTEM = """Choose exactly one supplied action_id for a preliminary C3 separation calculation.
Return only JSON {"action_id": string, "reason": short string}. Never calculate or invent
thermodynamic values, operating conditions, measurements, or new action settings. The
numerical tools supply candidate evaluations and unrounded target checks. Prefer a useful
candidate near observed feasibility boundaries and request numerical verification before
reporting. Preserve both product targets and all assumptions. Use report_preliminary only
when it is supplied by the deterministic evidence gate. Report only preliminary results
with limitations; there are no independent process-separation experiments. This absence
does not by itself forbid a clearly limited preliminary calculation report. A candidate
failure is not proof of global infeasibility. Use withhold_target_claim when no supported
candidate can be reported or no further allowed calculation is useful. Retain all stated
limitations, including high-purity coverage limits, and do not claim global optimality,
independent experimental confirmation, energy minimization, or a validated engineering
design. The last action is reserved for a terminal decision; a tool-call budget is finite.
Provide a brief decision justification, not hidden reasoning.
"""


class C3DesignTools(Protocol):
    """JSON-serializable numerical tools owned by thermo_engine."""

    def candidate_actions(self) -> list[dict[str, Any]]: ...

    def execute(self, action_id: str) -> dict[str, Any]: ...

    def assess(self) -> dict[str, Any]: ...

    def provenance(self) -> dict[str, Any]: ...


class C3LLM(Protocol):
    calls: list[dict[str, Any]]

    def request(self, system: str, content: Any) -> dict[str, Any]: ...


class C3ActionChoice(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action_id: str = Field(min_length=1)
    reason: str = Field(min_length=1, max_length=1000)


def _supported(observation: dict[str, Any]) -> bool:
    checks = observation.get("numerical_checks")
    blocking = observation.get("blocking_evidence_gaps", observation.get("evidence_gaps", []))
    return (
        observation.get("status") == "valid"
        and observation.get("meets_targets") is True
        and observation.get("verified") is True
        and isinstance(checks, dict)
        and checks.get("passed") is True
        and isinstance(blocking, list)
        and not blocking
    )


def _reportable(assessment: dict[str, Any], archive: dict[str, dict[str, Any]]) -> str | None:
    candidate_id = assessment.get("preferred_candidate_id")
    blocking = assessment.get("blocking_evidence_gaps", assessment.get("evidence_gaps", []))
    if (
        assessment.get("can_report_preliminary") is True
        and isinstance(candidate_id, str)
        and candidate_id in archive
        and isinstance(blocking, list)
        and not blocking
        and _supported(archive[candidate_id])
    ):
        return candidate_id
    return None


def _save(output_path: Path | None, result: dict[str, Any]) -> None:
    if output_path is None:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def _candidate_actions(tools: C3DesignTools, *, remaining: int) -> list[dict[str, Any]]:
    if remaining <= 1:
        return []
    actions = copy.deepcopy(tools.candidate_actions())
    ids: set[str] = set()
    for action in actions:
        identity = action.get("action_id")
        if not isinstance(identity, str) or not identity or identity in ids:
            raise ValueError("C3 tool actions require unique nonempty action IDs")
        if identity in {"report_preliminary", "withhold_target_claim"}:
            raise ValueError("Terminal action IDs are owned by the evidence gate")
        if action.get("kind") not in {"evaluate", "verify"}:
            raise ValueError("C3 tool action kind must be evaluate or verify")
        ids.add(identity)
    # The final numerical opportunity is reserved for an available verification.
    verification = [a for a in actions if a["kind"] == "verify"]
    return verification if remaining == 2 and verification else actions


def run_c3_case(
    tools: C3DesignTools,
    *,
    llm: C3LLM | None = None,
    output_path: Path | None = None,
    max_actions: int = 6,
    request: str = DEFAULT_REQUEST,
) -> dict[str, Any]:
    """Record live allowlisted decisions and stop only with numerical evidence.

    The six-action default includes the terminal decision, so at most five
    numerical calls occur. Raw requests/responses come from ReliabilityLLM.calls.
    An injected transport is useful for deterministic controller tests only.
    """
    if not 1 <= max_actions <= 12:
        raise ValueError("C3 action budget must be between one and twelve")
    if output_path is not None and output_path.exists():
        raise FileExistsError("Refusing to overwrite an existing C3 trajectory")
    client = llm if llm is not None else ReliabilityLLM()
    start = time.monotonic()
    archive: dict[str, dict[str, Any]] = {}
    result: dict[str, Any] = {
        "run_id": str(uuid4()),
        "case_id": "c3_propene_propane",
        "scope": CASE_SCOPE,
        "started_utc": datetime.now(timezone.utc).isoformat(),  # noqa: UP017 -- ggnn39 is Python 3.9
        "request": request,
        "task_contract": {
            "components": ["propene", "propane"],
            "composition_basis": "mole_fraction",
            "feed_composition": [0.35, 0.65],
            "distillate_propene_minimum": {"value": 0.996, "operator": ">="},
            "bottoms_propene_maximum": {"value": 0.01, "operator": "<"},
            "origin": "explicit_user_requirements_deterministically_registered",
        },
        "assumptions": copy.deepcopy(ASSUMPTIONS),
        "limitations": list(LIMITATIONS),
        "max_actions": max_actions,
        "numerical_tool_calls": 0,
        "provider_calls": client.calls,
        "trace": [],
        "archive": archive,
        "outcome": "withheld",
        "disposition": "insufficient_evidence",
        "final_observation": None,
        "assessment": {},
        "provenance": {},
    }
    try:
        result["provenance"] = copy.deepcopy(tools.provenance())
        for index in range(max_actions):
            tick = time.monotonic()
            assessment = copy.deepcopy(tools.assess())
            result["assessment"] = assessment
            for limit in assessment.get("limitations", []):
                if isinstance(limit, str) and limit not in result["limitations"]:
                    result["limitations"].append(limit)
            preferred = _reportable(assessment, archive)
            remaining = max_actions - index
            actions = _candidate_actions(tools, remaining=remaining)
            if preferred is not None:
                actions.append(
                    {
                        "action_id": "report_preliminary",
                        "kind": "report",
                        "description": "Report the numerically checked preferred candidate with all limits.",
                        "candidate_id": preferred,
                    }
                )
            actions.append(
                {
                    "action_id": "withhold_target_claim",
                    "kind": "withhold",
                    "description": "Stop without an unsupported target-satisfaction claim; preserve observations.",
                }
            )
            state = {
                "case_scope": CASE_SCOPE,
                "request": request,
                "task_contract": result["task_contract"],
                "assumptions": result["assumptions"],
                "limitations": result["limitations"],
                "remaining_actions_including_terminal": remaining,
                "archive": copy.deepcopy(
                    assessment.get(
                        "archive",
                        {
                            key: {
                                k: v for k, v in observation.items() if k not in {"profiles", "verification", "details"}
                            }
                            for key, observation in archive.items()
                        },
                    )
                ),
                "assessment": assessment,
                "actions": actions,
            }
            entry: dict[str, Any] = {
                "index": index,
                "origin": "live_llm_action_choice" if isinstance(client, ReliabilityLLM) else "injected_test_transport",
                "state": state,
                "candidates": actions,
                "choice": None,
                "observation": None,
            }
            result["trace"].append(entry)
            choice = C3ActionChoice.model_validate(client.request(SYSTEM, state))
            entry["choice"] = choice.model_dump()
            selected = next((a for a in actions if a["action_id"] == choice.action_id), None)
            if selected is None:
                raise ProviderFailure("C3 LLM selected an action outside the supplied allowlist")
            if selected["kind"] in {"evaluate", "verify"}:
                result["numerical_tool_calls"] += 1
                observation = copy.deepcopy(tools.execute(choice.action_id))
                candidate_id = observation.get("candidate_id")
                if not isinstance(candidate_id, str) or not candidate_id:
                    raise ValueError("C3 tool observation must identify its candidate")
                entry["observation"] = observation
                archive[candidate_id] = observation
                result["assessment"] = copy.deepcopy(tools.assess())
            elif choice.action_id == "report_preliminary":
                # Recheck the source tool state rather than accepting the model's reason as evidence.
                assessment = copy.deepcopy(tools.assess())
                preferred = _reportable(assessment, archive)
                if preferred is None:
                    raise ValueError("C3 candidate lost numerical support before reporting")
                result.update(
                    outcome="reported_preliminary",
                    disposition="preliminary_with_limits",
                    final_observation=copy.deepcopy(archive[preferred]),
                    assessment=assessment,
                    stopping_reason=assessment.get("stopping_reason", "numerically_supported_candidate_with_limits"),
                )
                for limit in archive[preferred].get("limitations", []) + assessment.get("limitations", []):
                    if isinstance(limit, str) and limit not in result["limitations"]:
                        result["limitations"].append(limit)
                entry["terminal_gate"] = "passed_numerical_evidence_with_limits_retained"
                entry["evidence_bindings"] = [
                    "archive." + preferred + "." + field
                    for field in ("meets_targets", "verified", "numerical_checks", "limitations")
                ]
                result["evidence_bindings"] = entry["evidence_bindings"]
            else:
                result["stopping_reason"] = (
                    "action_budget_exhausted" if remaining == 1 else "llm_withheld_with_current_tool_evidence"
                )
                entry["terminal_gate"] = "no_target_satisfaction_claim"
            entry["elapsed_s"] = time.monotonic() - tick
            _save(output_path, result)
            if selected["kind"] not in {"evaluate", "verify"}:
                break
    except ProviderFailure as exc:
        result.update(outcome="provider_error", error=str(exc), disposition="insufficient_evidence")
    except (ValidationError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        # Avoid echoing a malformed provider payload in logs; raw output remains in client.calls.
        result.update(outcome="execution_error", error=type(exc).__name__, disposition="insufficient_evidence")
    finally:
        result["elapsed_s"] = time.monotonic() - start
        result["llm_calls"] = len(client.calls)
        result["llm_tokens"] = sum(c.get("usage", {}).get("total_tokens", 0) for c in client.calls)
        result["provider_calls"] = copy.deepcopy(client.calls)
        try:
            result["provenance"] = copy.deepcopy(tools.provenance())
        except (ValueError, RuntimeError, KeyError, TypeError):
            result["provenance_refresh_failed"] = True
        _save(output_path, result)
    return result
