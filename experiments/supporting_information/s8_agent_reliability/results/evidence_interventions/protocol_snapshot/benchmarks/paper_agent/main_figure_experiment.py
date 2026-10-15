"""Supplement the frozen reliability pilot with clarification and evidence feedback."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, ValidationError

from benchmarks.paper_agent.audit_reliability import audit
from benchmarks.paper_agent.reliability_run import ROOT, digest, save
from paper_agent.policy import ProviderFailure
from paper_agent.reliability import (
    PARSE_SYSTEM,
    PLANS,
    ParsedTask,
    ReliabilityLLM,
    StrictModel,
    audit_report,
    compile_task,
)
from paper_agent.runtime import configure_runtime
from thermo_engine.paper_evidence_views import evidence_views

REPLIES = {
    "binary-missing-0": "补充操作压力为101.3 kPa。其余条件不变。",
    "binary-conflict-1": "更正：采用101.3 kPa，撤销150 kPa的要求。其余条件不变。",
    "binary-conflict-2": "更正进料：正庚烷摩尔分数0.466，正壬烷摩尔分数0.534；撤销之前的0.634。其余条件不变。",
    "extractive-ambiguous-3": "补充：DMF/有机进料质量比32:1。其余条件不变。",
    "extractive-missing-4": "补充：乙酸仲丁酯回收率至少0.98。其余条件不变。",
    "extractive-conflict-5": "更正：DMF/有机进料质量比32:1，撤销16:1的要求。其余条件不变。",
    "extraction-missing-6": "补充：总新鲜糠醛流量为1.5 mol/s。其余条件不变。",
    "extraction-conflict-7": "更正操作温度为303.15 K，撤销298.15 K的要求。其余条件不变。",
    "extraction-conflict-8": (
        "更正新鲜烃进料：正庚烷摩尔分数0.7333333333333333、苯摩尔分数0.2666666666666667；"
        "撤销之前的0.3666666666666667。其余条件不变。"
    ),
}

RECOVERY_SYSTEM = (
    PARSE_SYSTEM
    + """
This is a continuation after a clarification. The supplied user_correction explicitly
supersedes earlier conflicting values ONLY for the named fields. Return the effective
current full task, retaining unaffected original facts. Do not keep explicitly revoked
values as active quantities. Quote verbatim from original_request or user_correction.
The system_questions are not new user facts. Do not invent omitted values.
"""
)

DECISION_SYSTEM = """Choose the next engineering action from a supplied numerical tool packet.
Never calculate or invent equilibrium values. Use the tool's unrounded target assessment.
Actions:
report_preliminary: numerical checks available and passed, all required targets met;
retain the stated limitations and do not imply experimental confirmation or global optimality.
request_verification: necessary numerical diagnostics are unavailable; request the tool check.
withhold_target_claim: a computed candidate does not meet all requirements (including any
explicit interpolation-robust requirement); do not claim global infeasibility.
claim_experimental_confirmation: only if independent experimental process confirmation exists.
Return JSON {action:string,evidence_ids:[string],retain_limits:bool}.
evidence_ids name supporting top-level keys of the packet. Cite all facts essential to the
decision, including design, target_check, numerical_validation and limitation when reporting.
When a verification tool response is supplied, decide using the updated current_packet.
Set retain_limits=true when retaining all stated applicability limits, for every action.
"""


class EvidenceDecision(StrictModel):
    action: Literal[
        "report_preliminary", "request_verification", "withhold_target_claim", "claim_experimental_confirmation"
    ]
    evidence_ids: list[str] = Field(min_length=1)
    retain_limits: bool


def score_decision(decision: EvidenceDecision, scenario: dict[str, Any]) -> dict[str, bool]:
    expected = scenario["expected_action"]
    packet = scenario["packet"]
    action_ok = decision.action == expected
    evidence_ok = set(scenario["required_ids"]).issubset(decision.evidence_ids) and set(decision.evidence_ids).issubset(
        packet
    )
    return dict(
        action_correct=action_ok,
        evidence_bound=evidence_ok,
        passed=action_ok and evidence_ok and decision.retain_limits,
    )


def recovery_run(initial: dict[str, Any], bundle: dict[str, Any]) -> dict[str, Any]:
    llm = ReliabilityLLM()
    started = time.monotonic()
    questions = sorted({i["question"] for i in initial["compiled"]["issues"]})
    conversation = dict(
        original_request=initial["request"], system_questions=questions, user_correction=REPLIES[initial["task_id"]]
    )
    record: dict[str, Any] = dict(
        task_id=initial["task_id"],
        case=initial["case"],
        repeat=initial["repeat"],
        conversation=conversation,
        initial_origin="replayed frozen v3 interaction",
        reply_origin="predeclared scripted benchmark reply, not a real user conversation",
        llm_calls=llm.calls,
        outcome="failed",
        parsed_correct=False,
        executed=False,
        result_preserved=False,
        report_grounded=False,
    )
    try:
        parsed = ParsedTask.model_validate(llm.request(RECOVERY_SYSTEM, conversation))
        record["parsed"] = parsed.model_dump()
        source = conversation["original_request"] + "\n" + conversation["user_correction"]
        compiled = compile_task(parsed, source)
        record["compiled"] = compiled.model_dump()
        contract = compiled.contract
        record["parsed_correct"] = bool(
            contract and contract.identity() == bundle["contract_id"] and parsed.plan == PLANS[initial["case"]]
        )
        if compiled.status != "ready" or not record["parsed_correct"]:
            record["outcome"] = compiled.status if compiled.status != "ready" else "wrong_contract"
            return record
        record.update(
            executed=True,
            cache_hit=True,
            numerical_contract_id=bundle["contract_id"],
            final=bundle["final"],
            result_preserved=bundle["paper_agreement"]["passed"],
            tool_trace=[dict(action=a, origin="cached validated v3 artifact") for a in parsed.plan],
        )
        report = llm.report(bundle["evidence"], bundle["claim_catalog"])
        checked = audit_report(report, bundle["supported_claims"])
        record.update(
            report=report.model_dump(),
            report_audit=checked,
            report_grounded=checked["fully_grounded"],
            outcome="recovered" if checked["fully_grounded"] else "report_blocked",
        )
    except ProviderFailure as exc:
        record.update(outcome="provider_error", error=str(exc))
    except (ValidationError, ValueError, KeyError) as exc:
        record.update(outcome="structured_error", error=type(exc).__name__ + ": " + str(exc))
    finally:
        record["elapsed_s"] = time.monotonic() - started
        record["tokens"] = sum(c.get("usage", {}).get("total_tokens", 0) for c in llm.calls)
    return record


def decision_run(scenario: dict[str, Any], full: dict[str, Any], repeat: int) -> dict[str, Any]:
    llm = ReliabilityLLM()
    started = time.monotonic()
    record: dict[str, Any] = dict(
        case=scenario["packet"]["case"],
        condition=scenario["condition"],
        repeat=repeat,
        packet=scenario["packet"],
        llm_calls=llm.calls,
        outcome="failed",
        passed=False,
        restored_passed=False,
        verification_requests=0,
    )
    try:
        selected = EvidenceDecision.model_validate(llm.request(DECISION_SYSTEM, {"current_packet": scenario["packet"]}))
        record.update(decision=selected.model_dump(), assessment=score_decision(selected, scenario))
        record["passed"] = record["assessment"]["passed"]
        if scenario["condition"] == "validation_withheld" and selected.action == "request_verification":
            record["verification_requests"] = 1
            response = dict(
                tool="retrieve_existing_numerical_validation",
                origin="cached verified v3 diagnostics",
                result=full["packet"]["numerical_validation"],
            )
            record["verification_tool"] = response
            restored = EvidenceDecision.model_validate(
                llm.request(
                    DECISION_SYSTEM,
                    dict(
                        previous_packet=scenario["packet"],
                        previous_decision=selected.model_dump(),
                        verification_tool=response,
                        current_packet=full["packet"],
                    ),
                )
            )
            record["restored_decision"] = restored.model_dump()
            record["restored_assessment"] = score_decision(restored, full)
            record["restored_passed"] = record["restored_assessment"]["passed"]
        record["outcome"] = "completed"
    except ProviderFailure as exc:
        record.update(outcome="provider_error", error=str(exc))
    except (ValidationError, ValueError, KeyError) as exc:
        record.update(outcome="structured_error", error=type(exc).__name__ + ": " + str(exc))
    finally:
        record["elapsed_s"] = time.monotonic() - started
        record["tokens"] = sum(c.get("usage", {}).get("total_tokens", 0) for c in llm.calls)
    return record


def source_hashes() -> dict[str, str]:
    names = [
        "paper_agent/reliability.py",
        "paper_agent/policy.py",
        "paper_agent/runtime.py",
        "thermo_engine/paper_evidence_views.py",
        "benchmarks/paper_agent/main_figure_experiment.py",
    ]
    return {name: digest(ROOT / name) for name in names}


def run(source: Path, output: Path) -> None:
    if output.exists():
        raise ValueError("Choose a new output directory; immutable experiments are never overwritten")
    source = source.resolve()
    if not audit(source)["passed"]:
        raise ValueError("Source experiment failed its integrity audit")
    bundles = {
        b["protocol"]: b
        for p in (source / "numerical").glob("*.json")
        for b in [json.loads(p.read_text(encoding="utf-8"))]
    }
    initial = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((source / "runs").glob("*.json"))]
    bad = [r for r in initial if r["kind"] != "equivalent"]
    scenarios = [s for case in ("binary", "extractive", "extraction") for s in evidence_views(bundles[case])]
    source_files = (
        [source / "manifest.json"]
        + list((source / "runs").glob("*.json"))
        + list((source / "numerical").glob("*.json"))
    )
    hashes = {str(p.relative_to(source)): digest(p) for p in source_files}
    manifest: dict[str, Any] = dict(
        source=str(source),
        source_hashes=hashes,
        code_hashes=source_hashes(),
        replies=REPLIES,
        decision_scenarios=scenarios,
        repeats=3,
        environment="ggnn39",
        scope="within-case development extension; scripted corrections and evidence interventions",
        frozen_numerical_data=True,
        new_thermodynamic_inference=False,
        recovery_system=RECOVERY_SYSTEM,
        decision_system=DECISION_SYSTEM,
    )
    save(output / "manifest.json", manifest)
    for name in manifest["code_hashes"]:
        snapshot = output / "protocol_snapshot" / name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes((ROOT / name).read_bytes())
    # Same original LLM outputs for both gates; no unsafe physical calls are executed.
    replay = []
    for row in initial:
        parsed = row.get("parsed", {})
        schema_ready = bool(
            parsed.get("status") == "ready" and not parsed.get("issues") and parsed.get("plan") == PLANS[row["case"]]
        )
        replay.append(
            dict(
                task_id=row["task_id"],
                case=row["case"],
                repeat=row["repeat"],
                kind=row["kind"],
                schema_only_ready=schema_ready,
                contract_ready=row["compiled"]["status"] == "ready",
            )
        )
    save(output / "paired_routing_replay.json", replay)
    for item in bad:
        record = recovery_run(item, bundles[item["case"]])
        save(output / "recovery" / (item["task_id"] + f"-r{item['repeat']}.json"), record)
        print("recovery", item["task_id"], item["repeat"], record["outcome"], flush=True)
        if record["outcome"] == "provider_error":
            return
    for repeat in range(3):
        for scenario in scenarios:
            full = next(
                s
                for s in scenarios
                if s["packet"]["case"] == scenario["packet"]["case"] and s["condition"] == "complete"
            )
            record = decision_run(scenario, full, repeat)
            save(output / "decisions" / (record["case"] + "-" + record["condition"] + f"-r{repeat}.json"), record)
            print("evidence", record["case"], record["condition"], repeat, record["passed"], flush=True)
            if record["outcome"] == "provider_error":
                return
    unchanged = (
        hashes == {str(p.relative_to(source)): digest(p) for p in source_files}
        and source_hashes() == manifest["code_hashes"]
    )
    save(output / "integrity.json", dict(source_and_code_unchanged=unchanged))
    if not unchanged:
        raise ValueError("Experiment source changed during execution")


def main() -> None:
    configure_runtime()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.output)


if __name__ == "__main__":
    main()
