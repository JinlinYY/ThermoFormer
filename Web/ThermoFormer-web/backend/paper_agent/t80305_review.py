"""Live, bounded evidence review of the industrial C3 experiment's actual tool records.

This is evidence retrieval/selection, not an LLM-controlled numerical optimization.
The experiment runner calculates candidates before this explicitly cached review.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from paper_agent.policy import ProviderFailure
from paper_agent.reliability import ReliabilityLLM
from thermo_engine.c3_engineering_study import write_json
from thermo_engine.c3_thermoformer import file_sha256
from thermo_engine.t80305_experiment import DEFAULT_OUTPUT, LIMITS

SYSTEM = """Review a C3 industrial design-document comparison using only supplied tools.
The deliverable is a reduced-experiment review plus a separate full-plant disposition.
Missing full-plant inputs alone do not prevent reviewing the reduced experiment.
Return exactly JSON {"action_id": string, "reason": short string, "candidate_id": string or null}.
Select an allowed action. Do not calculate numbers, invent evidence, or tune model parameters.
Read the source audit first. Distinguish full-plant reproduction from an explicitly reduced
binary CMO experiment. Efficiency is assumed, industrial conditions extrapolate the C3 data,
and PR is a comparator rather than experiment. All numerical results are cached records;
you are reviewing evidence, not autonomously running numerical search. A frozen C3-adapted
model is not the original unadapted checkpoint. Prefer read_baselines before read_improvements.
Only report_reduced may select a candidate, and then only from the supplied eligible IDs.
Use defer_full when full-plant evidence is insufficient. It is legitimate to report a reduced
calculation and still defer plant validation. When choosing a reduced candidate, prefer lower
vapor circulation within the finite supplied grid, then greater minimum normalized target margin.
Do not claim actual side-product purity, duty savings, a global optimum or industrial validation.
Your short reason must not introduce new numerical claims. Missing evidence cannot be invented.
UNREAD evidence is not missing evidence. Null eligible_candidate_ids means the improvement
table has not been read, not that it contains no eligible candidates. Read all available
evidence categories before the terminal review; the tool gate enforces this minimum review.
"""


class Client(Protocol):
    calls: list[dict[str, Any]]

    def request(self, system: str, content: Any) -> dict[str, Any]: ...


class Choice(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action_id: str
    reason: str = Field(min_length=1, max_length=1200)
    candidate_id: str | None = None


def eligible_ids(records: list[dict[str, Any]]) -> list[str]:
    """Numerical eligibility only; never confers physical or industrial validation."""
    return [
        r["candidate_id"]
        for r in records
        if r["model"] == "TF"
        and r["validation"]["passed"]
        and r["validation"]["direct_fugacity_checked"]
        and r["metrics"]["reduced_targets_met"]
    ]


def actions(read: set[str], eligible: list[str]) -> list[str]:
    if "read_source_audit" not in read:
        return ["read_source_audit"]
    options = [a for a in ("read_thermodynamics", "read_baselines", "read_improvements") if a not in read]
    if all(a in read for a in ("read_thermodynamics", "read_baselines", "read_improvements")):
        if eligible:
            options.append("report_reduced")
        options.append("defer_full")
    return options


def compact(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{k: r[k] for k in ("candidate_id", "model", "input", "metrics", "validation")} for r in records]


def run_review(output: Path, client: Client | None = None) -> dict[str, Any]:
    """Run the configured provider; preserve raw failures without a rule substitution."""
    llm = client if client is not None else ReliabilityLLM()
    paths = [
        output / n
        for n in (
            "source_audit.json",
            "thermodynamic_comparison.json",
            "columns.json",
            "improvement_screen.json",
            "sampled_phase_stability.json",
        )
    ]
    audit, thermodynamics, columns, improvements, stability = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
    eligible = eligible_ids(improvements)
    diagnostics_path = output / "additional_diagnostics.json"
    diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
    paths.append(diagnostics_path)
    # Do not send original proprietary files or organizational identifiers to the provider.
    catalog = {
        "read_source_audit": {
            "mass_balance_gap_fraction": audit["total_mass_gap_fraction"],
            "full_plant_status": audit["full_plant_status"],
            "missing_parameters": audit["missing_parameters"],
            "binary_cases": audit["binary_cases"],
            "material_balance_bounds": diagnostics["material_balance_bounds"],
            "limits": LIMITS,
        },
        "read_thermodynamics": {
            "comparison_points": [
                {
                    k: r[k]
                    for k in ("pressure_kpa", "x_propene", "alpha", "delta_y_TF_minus_PR", "delta_T_K_TF_minus_PR")
                }
                for r in thermodynamics
            ],
            "negative_sampled_TPD_states": sum(s["negative_sample_found"] for s in stability),
            "accuracy_validated": False,
            "phase_stability_globally_certified": False,
        },
        "read_baselines": compact(columns),
        "read_improvements": compact(improvements),
    }
    seen: set[str] = set()
    trace: list[dict[str, Any]] = []
    result: dict[str, Any] = {
        "status": "running",
        "review_mode": "live_LLM_review_of_cached_tool_results",
        "protocol_revision": "v2_distinguish_unread_from_missing",
        "numerical_optimization_controlled_by_LLM": False,
        "plant_validated": False,
        "source_records_sha256": {p.name: file_sha256(p) for p in paths},
        "trace": trace,
    }
    try:
        for step in range(7):
            allowed = actions(seen, eligible)
            if step == 6:
                allowed = [a for a in allowed if a in ("report_reduced", "defer_full")]
            payload = {
                "allowed_actions": allowed,
                "seen_evidence": {a: catalog[a] for a in sorted(seen)},
                "evidence_availability": {a: "read" if a in seen else "available_unread" for a in catalog},
                "eligible_candidate_ids": eligible if "read_improvements" in seen else None,
                "remaining_action_budget": 7 - step,
            }
            choice = Choice.model_validate(llm.request(SYSTEM, payload))
            if choice.action_id not in allowed:
                raise ProviderFailure("Action outside the evidence-gated allowlist")
            if choice.action_id == "report_reduced" and choice.candidate_id not in eligible:
                raise ProviderFailure("Candidate failed the deterministic numerical evidence gate")
            if choice.action_id != "report_reduced" and choice.candidate_id is not None:
                raise ProviderFailure("Candidate may only be named in report_reduced")
            event = {
                "step": step + 1,
                "choice": choice.model_dump(),
                "allowed_actions": allowed,
                "cache_reused": choice.action_id.startswith("read_"),
                "new_numerical_calculations": 0,
            }
            trace.append(event)
            if choice.action_id in catalog:
                seen.add(choice.action_id)
                event["tool_result"] = catalog[choice.action_id]
            else:
                result.update(
                    status="completed",
                    terminal_action=choice.action_id,
                    candidate_id=choice.candidate_id,
                    full_plant_disposition="deferred_missing_parameters",
                )
                break
    except (ProviderFailure, ValueError) as error:
        result.update(status="provider_or_contract_failure", error=str(error), rule_fallback_used=False)
    result["provider_calls"] = llm.calls
    write_json(output / "agent_review.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run_review(args.output)
    print(json.dumps({k: result.get(k) for k in ("status", "terminal_action", "candidate_id", "error")}))


if __name__ == "__main__":
    main()
