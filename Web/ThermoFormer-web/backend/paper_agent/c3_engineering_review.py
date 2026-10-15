"""Read-only, evidence-gated engineering review of precomputed C3 candidates.

This module does not conduct autonomous numerical search. Numerical results must
already exist in tool records; the LLM can request evidence and choose an allowed
terminal action, but cannot calculate or alter engineering quantities.
"""

from __future__ import annotations

import copy
import hashlib
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
    "Review precomputed C3 propene/propane separation candidates for the registered feed "
    "and both product specifications. Select a numerically supported preliminary candidate "
    "only after reviewing cold-source feasibility, utilities and the specified robustness "
    "scenarios; otherwise defer. There are no independent process-separation experiments."
)
REVIEW_LIMITS = [
    "All numerical results are precomputed tool records; this review performs no autonomous numerical search.",
    "Utility and cold-source feasibility apply only to the declared operating and utility assumptions.",
    "Robustness applies only to the specified scenarios; it is not a probabilistic reliability guarantee.",
    "This is a preliminary calculation review, not industrial certification or process-experiment validation.",
    "Selection among supplied candidates does not establish a global optimum.",
]
SYSTEM = """Review engineering evidence for a C3 separation calculation. Return exactly JSON
{"action_id": string, "reason": short string}, choosing one supplied action_id. Never
produce numerical values, new settings, new candidates or new action IDs. All quantities
are precomputed numerical tool results; this review is not autonomous numerical search.
The first action MUST be compare_candidates. At that first step it is the only allowed
action; defer is not permitted. Evidence that has not yet been read is UNREAD, not missing.
Use compare_candidates to retrieve it before judging evidence sufficiency. A null summary
before that read is expected and does not justify deferral. After the table has been read,
defer is available only when it appears in the supplied action list.
Compare the complete supplied candidate table, including rejected candidates. Read
utility/cold-source evidence and robustness/applicability evidence for any candidate you
wish to report. Use report_preliminary only when the numerical evidence gate supplies it.
A candidate with failed cold-source feasibility, failed robustness, failed applicability,
failed product targets or incomplete direct numerical validation cannot be accepted.
Use defer when no sufficiently supported candidate is available or the review budget is
insufficient. Rejection and deferral are valid outcomes; do not force success. Retain every
evidence limit. Robustness means the declared finite scenarios, not a probability of
success. Do not claim industrial certification, real process validation, a global optimum,
or an unconstrained energy optimum. Provide a concise decision justification, not hidden
reasoning. Your reason may refer to candidate IDs and evidence without introducing numbers.
"""


class EngineeringCandidate(BaseModel):
    """Boundary for immutable numerical tool records, not LLM-generated data."""

    model_config = ConfigDict(extra="allow", strict=True, allow_inf_nan=False)
    candidate_id: str = Field(min_length=1)
    pressure_kpa: float = Field(gt=0)
    metrics: dict[str, Any]
    meets_targets: bool
    direct_numerical_verified: bool
    utilities: dict[str, Any]
    cold_source_feasible: bool
    robustness: dict[str, Any]
    applicability: dict[str, Any]
    evidence_limits: list[str]
    source: dict[str, Any] = Field(default_factory=dict)


class ReviewChoice(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    action_id: str = Field(min_length=1)
    reason: str = Field(min_length=1, max_length=1000)


class ReviewLLM(Protocol):
    calls: list[dict[str, Any]]

    def request(self, system: str, content: Any) -> dict[str, Any]: ...


def _blockers(record: dict[str, Any]) -> list[str]:
    blockers = []
    for passed, label in (
        (record["meets_targets"] is True, "product_targets_not_satisfied"),
        (record["direct_numerical_verified"] is True, "direct_numerical_validation_incomplete"),
        (record["cold_source_feasible"] is True, "cold_source_infeasible"),
        (bool(record["utilities"]), "utility_evidence_missing"),
        (record["utilities"].get("passed") is True, "utility_checks_not_passed"),
        (record["robustness"].get("passed") is True, "declared_robustness_scenarios_not_passed"),
        (record["applicability"].get("passed") is True, "applicability_not_established"),
    ):
        if not passed:
            blockers.append(label)
    metric_target = record["metrics"].get("meets_targets")
    if metric_target is not None and metric_target is not record["meets_targets"]:
        blockers.append("inconsistent_target_assessments")
    return blockers


class C3EngineeringEvidenceTools:
    """Actual read-only evidence calls with explicit cache-reuse provenance."""

    def __init__(self, candidates: list[dict[str, Any]]) -> None:
        if not candidates:
            raise ValueError("At least one precomputed C3 candidate is required")
        records = [EngineeringCandidate.model_validate(item).model_dump() for item in candidates]
        if len({item["candidate_id"] for item in records}) != len(records):
            raise ValueError("Candidate IDs must be unique")
        serialized = json.dumps(records, ensure_ascii=False, sort_keys=True, allow_nan=False)
        self.records: dict[str, dict[str, Any]] = {item["candidate_id"]: copy.deepcopy(item) for item in records}
        self.sha256 = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        self.compared = False
        self.utilities_reviewed: set[str] = set()
        self.robustness_reviewed: set[str] = set()
        self.calls: list[dict[str, Any]] = []

    def summary(self) -> list[dict[str, Any]]:
        """Expose every candidate, including infeasible rows, without recomputation."""
        return [
            {
                "candidate_id": key,
                "pressure_kpa": record["pressure_kpa"],
                "metrics": copy.deepcopy(record["metrics"]),
                "meets_targets": record["meets_targets"],
                "direct_numerical_verified": record["direct_numerical_verified"],
                "cold_source_feasible": record["cold_source_feasible"],
                "robustness_passed": record["robustness"].get("passed") is True,
                "applicability_passed": record["applicability"].get("passed") is True,
                "blocking_reasons": _blockers(record),
                "evidence_limits": list(record["evidence_limits"]),
            }
            for key, record in self.records.items()
        ]

    def reportable(self, candidate_id: str) -> bool:
        return (
            self.compared
            and candidate_id in self.utilities_reviewed
            and candidate_id in self.robustness_reviewed
            and not _blockers(self.records[candidate_id])
        )

    def actions(self, remaining: int) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        if remaining > 1:
            if not self.compared:
                actions.append(
                    {"action_id": "compare_candidates", "kind": "compare_candidates", "description": "Read all rows."}
                )
            else:
                for key in self.records:
                    if key not in self.utilities_reviewed:
                        actions.append(
                            {
                                "action_id": "review_utilities:" + key,
                                "kind": "review_utilities",
                                "candidate_id": key,
                                "description": "Read computed utilities, cold-source check and assumptions.",
                            }
                        )
                    if key not in self.robustness_reviewed:
                        actions.append(
                            {
                                "action_id": "review_robustness:" + key,
                                "kind": "review_robustness",
                                "candidate_id": key,
                                "description": "Read finite robustness scenarios and applicability checks.",
                            }
                        )
        for key in self.records:
            if self.reportable(key):
                actions.append(
                    {
                        "action_id": "report_preliminary:" + key,
                        "kind": "report_preliminary",
                        "candidate_id": key,
                        "description": "Report this eligible reviewed candidate with all evidence limits.",
                    }
                )
        if self.compared or remaining == 1:
            actions.append(
                {"action_id": "defer", "kind": "defer", "description": "Stop without an unsupported acceptance claim."}
            )
        return actions

    def execute(self, action: dict[str, Any]) -> dict[str, Any]:
        """Read registered records; no thermodynamic/economic numbers are generated."""
        kind = action["kind"]
        raw_key = action.get("candidate_id")
        key = raw_key if isinstance(raw_key, str) else ""
        if kind == "compare_candidates":
            self.compared = True
            evidence: dict[str, Any] = {"all_candidate_summaries": self.summary()}
        elif kind == "review_utilities":
            record = self.records[key]
            self.utilities_reviewed.add(key)
            evidence = {
                "candidate_id": key,
                "utilities": copy.deepcopy(record["utilities"]),
                "cold_source_feasible": record["cold_source_feasible"],
                "source": copy.deepcopy(record["source"]),
                "evidence_limits": list(record["evidence_limits"]),
            }
        elif kind == "review_robustness":
            record = self.records[key]
            self.robustness_reviewed.add(key)
            evidence = {
                "candidate_id": key,
                "robustness": copy.deepcopy(record["robustness"]),
                "applicability": copy.deepcopy(record["applicability"]),
                "direct_numerical_verified": record["direct_numerical_verified"],
                "meets_targets": record["meets_targets"],
                "source": copy.deepcopy(record["source"]),
                "evidence_limits": list(record["evidence_limits"]),
            }
        else:
            raise ValueError("Not a registered read-only evidence action")
        call = {
            "tool_call_id": "evidence_read_" + str(len(self.calls) + 1),
            "action_id": action["action_id"],
            "kind": kind,
            "origin": "read_of_precomputed_numerical_tool_records",
            "numerical_results_precomputed": True,
            "cache_reused": True,
            "cache_reuse_scope": "Evidence is reused here; original numerical cache status remains in source.",
            "new_numerical_calculations": 0,
            "candidate_records_sha256": self.sha256,
            "evidence": evidence,
        }
        self.calls.append(copy.deepcopy(call))
        return call


def _save(path: Path | None, result: dict[str, Any]) -> None:
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def run_engineering_review(
    candidates: list[dict[str, Any]],
    *,
    output_path: Path | None = None,
    llm: ReviewLLM | None = None,
    live: bool = False,
    max_actions: int = 12,
    request: str = DEFAULT_REQUEST,
) -> dict[str, Any]:
    """Prepare evidence by default; execute provider calls only with live=True.

    max_actions includes the terminal report/defer decision. The transport can be
    injected for tests; the default live transport is the real DeepSeek client.
    """
    if not 2 <= max_actions <= 20:
        raise ValueError("Engineering review requires two to twenty actions including the terminal decision")
    if output_path is not None and output_path.exists():
        raise FileExistsError("Refusing to overwrite an existing C3 engineering review")
    tools = C3EngineeringEvidenceTools(candidates)
    started = time.monotonic()
    result: dict[str, Any] = {
        "run_id": str(uuid4()),
        "review_type": "c3_precomputed_candidate_engineering_review",
        "started_utc": datetime.now(timezone.utc).isoformat(),  # noqa: UP017 -- ggnn39 is Python 3.9
        "request": request,
        "numerical_results_precomputed": True,
        "new_numerical_calculations": 0,
        "candidate_records_sha256": tools.sha256,
        "candidate_records": copy.deepcopy(list(tools.records.values())),
        "all_candidate_summaries": tools.summary(),
        "max_actions": max_actions,
        "live_requested": live,
        "outcome": "prepared_not_executed",
        "disposition": "not_reported",
        "selected_candidate_id": None,
        "limitations": list(REVIEW_LIMITS),
        "trace": [],
        "tool_calls": tools.calls,
        "provider_calls": [],
        "llm_calls": 0,
        "llm_tokens": 0,
    }
    if not live:
        result["elapsed_s"] = time.monotonic() - started
        _save(output_path, result)
        return result
    client = llm if llm is not None else ReliabilityLLM()
    result.update(outcome="deferred", disposition="insufficient_evidence")
    try:
        for index in range(max_actions):
            remaining = max_actions - index
            actions = tools.actions(remaining)
            state = {
                "request": request,
                "numerical_results_precomputed": True,
                "remaining_actions_including_terminal": remaining,
                "candidate_ids": list(tools.records),
                "all_candidate_summaries": tools.summary() if tools.compared else None,
                "evidence_read_so_far": copy.deepcopy(tools.calls),
                "limitations": list(REVIEW_LIMITS),
                "actions": actions,
            }
            entry: dict[str, Any] = {
                "index": index,
                "origin": "live_llm_action_choice" if isinstance(client, ReliabilityLLM) else "injected_test_transport",
                "state": state,
                "choice": None,
                "tool_call": None,
            }
            result["trace"].append(entry)
            tick = time.monotonic()
            choice = ReviewChoice.model_validate(client.request(SYSTEM, state))
            entry["choice"] = choice.model_dump()
            action = next((a for a in actions if a["action_id"] == choice.action_id), None)
            if action is None:
                raise ProviderFailure("Engineering review selected an action outside the supplied allowlist")
            if action["kind"] in {"compare_candidates", "review_utilities", "review_robustness"}:
                entry["tool_call"] = tools.execute(action)
            elif action["kind"] == "report_preliminary":
                key = action["candidate_id"]
                if not tools.reportable(key):
                    raise ValueError("Candidate is not supported by the engineering evidence gate")
                record = tools.records[key]
                result.update(
                    outcome="reported_preliminary",
                    disposition="preliminary_with_limits",
                    selected_candidate_id=key,
                    selected_candidate=copy.deepcopy(record),
                    stopping_reason="reviewed_candidate_passes_declared_cold_source_robustness_and_applicability_gates",
                )
                result["limitations"] = list(dict.fromkeys(REVIEW_LIMITS + record["evidence_limits"]))
                result["evidence_bindings"] = [
                    call["tool_call_id"]
                    for call in tools.calls
                    if call["kind"] == "compare_candidates" or call["evidence"].get("candidate_id") == key
                ]
                entry["terminal_gate"] = "passed_declared_engineering_checks_with_limits"
            else:
                result["stopping_reason"] = (
                    "review_budget_exhausted" if remaining == 1 else "llm_deferred_after_inspecting_available_evidence"
                )
                result["candidate_blocking_reasons"] = {key: _blockers(record) for key, record in tools.records.items()}
                entry["terminal_gate"] = "no_unsupported_acceptance_claim"
            entry["elapsed_s"] = time.monotonic() - tick
            result["provider_calls"] = copy.deepcopy(client.calls)
            _save(output_path, result)
            if action["kind"] in {"report_preliminary", "defer"}:
                break
    except ProviderFailure as exc:
        result.update(outcome="provider_error", disposition="insufficient_evidence", error=str(exc))
    except (ValidationError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        result.update(outcome="execution_error", disposition="insufficient_evidence", error=type(exc).__name__)
    finally:
        result["provider_calls"] = copy.deepcopy(client.calls)
        result["tool_calls"] = copy.deepcopy(tools.calls)
        result["llm_calls"] = len(client.calls)
        result["llm_tokens"] = sum(call.get("usage", {}).get("total_tokens", 0) for call in client.calls)
        result["elapsed_s"] = time.monotonic() - started
        _save(output_path, result)
    return result
