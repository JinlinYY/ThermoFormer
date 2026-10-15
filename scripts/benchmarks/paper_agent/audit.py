"""Audit complete paired experiments and export task-level evidence for the SI."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from paper_agent.contracts import PaperRun


def audit(directory: Path) -> dict[str, Any]:
    tasks = json.loads((directory / "tasks.json").read_text(encoding="utf-8"))
    protocol = directory / "protocol/experiment.json"
    experiment = (
        json.loads(protocol.read_text()) if protocol.exists() else {"modes": ["fixed", "rule", "llm"], "llm_repeats": 3}
    )
    runs = [PaperRun.model_validate_json(p.read_text(encoding="utf-8")) for p in sorted(directory.glob("*-*-*.json"))]
    expected = {
        (t["task_id"], mode, repeat)
        for t in tasks
        for mode in experiment["modes"]
        for repeat in (range(experiment["llm_repeats"]) if mode.startswith("llm") else range(1))
    }
    actual = {(r.task.task_id, r.mode, r.repeat) for r in runs}
    if len(actual) != len(runs) or actual != expected:
        raise ValueError(f"Incomplete or duplicate experiment: expected {len(expected)}, found {len(runs)}")
    sources = {json.dumps(r.provenance["orchestration_sources"], sort_keys=True) for r in runs}
    if len(sources) != 1:
        raise ValueError("Orchestration code changed across paired runs")
    environments = {json.dumps(r.provenance.get("runtime_environment"), sort_keys=True) for r in runs}
    if len(environments) != 1:
        raise ValueError("Numerical runtime configuration changed across paired runs")
    for case in {r.task.case for r in runs}:
        identities = {
            json.dumps(
                {
                    key: r.provenance.get(key)
                    for key in ("checkpoint_sha256", "scientific_sources", "case_data_sources")
                },
                sort_keys=True,
            )
            for r in runs
            if r.task.case == case
        }
        if len(identities) != 1:
            raise ValueError("Scientific resources changed within case " + case)
    rows: list[dict[str, Any]] = []
    tokens: Counter[str] = Counter()
    models: Counter[str] = Counter()
    for run in runs:
        assert run.calls <= run.task.max_calls
        assert run.calls == sum(e.observation is not None for e in run.trace)
        for entry in run.trace:
            assert entry.choice.action_id in {c.action_id for c in entry.candidates}
            assert "reference_meets_targets" not in json.dumps(entry.state)
        if run.mode.endswith("_guided") and run.outcome != "provider_error":
            assert run.assessment.get("stopping_certificate") in {
                "budget_exhausted",
                "resource_preference_resolved",
                "candidate_set_exhausted",
            }
            if run.final_observation:
                assert run.final_observation.observation_id in {
                    e.observation.observation_id for e in run.trace if e.observation
                }
            if run.outcome == "accepted":
                assert run.final_observation is not None
                assert run.final_observation.status == "valid" and run.final_observation.verified
                assert run.final_observation.meets_targets and not run.final_observation.evidence_gaps
        calls = run.provenance.get("llm_calls", [])
        for call in calls:
            models[call["model"]] += 1
            for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                tokens[key] += call.get("usage", {}).get(key, 0)
        metrics = run.final_observation.metrics if run.final_observation else {}
        rows.append(
            dict(
                task_id=run.task.task_id,
                case=run.task.case,
                mode=run.mode,
                repeat=run.repeat,
                outcome=run.outcome,
                calls=run.calls,
                wall_s=run.elapsed_s,
                reflux=metrics.get("reflux"),
                stages=metrics.get("stages"),
                purity=metrics.get("purity"),
                recovery=metrics.get("recovery"),
                retention=metrics.get("retention"),
                reference_meets=run.assessment.get("reference_meets_targets"),
                evidence_gap_acceptance=run.assessment.get("accepted_with_unresolved_evidence"),
                false_acceptance=run.assessment.get("false_acceptance_against_reference"),
                llm_requests=len(calls),
                llm_tokens=sum(c.get("usage", {}).get("total_tokens", 0) for c in calls),
            )
        )
    output = directory / "figures"
    output.mkdir(exist_ok=True)
    with (output / "all_tasks.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    result: dict[str, Any] = {
        "runs": len(runs),
        "same_orchestration_sources": True,
        "llm_request_models": dict(models),
        "llm_token_usage": dict(tokens),
        "policies": {},
    }
    for mode in experiment["modes"]:
        group = [r for r in runs if r.mode == mode]
        result["policies"][mode] = dict(
            runs=len(group),
            outcomes=dict(Counter(r.outcome for r in group)),
            mean_calls=mean(r.calls for r in group),
            nominal_target_reached=sum(
                any(e.observation and e.observation.status == "valid" and e.observation.meets_targets for e in r.trace)
                for r in group
            ),
            evidence_gap_acceptance=sum(bool(r.assessment.get("accepted_with_unresolved_evidence")) for r in group),
            accepted_with_reference=sum(
                r.outcome == "accepted" and r.assessment.get("reference_meets_targets") is not None for r in group
            ),
            failed_reference_checks=sum(bool(r.assessment.get("false_acceptance_against_reference")) for r in group),
        )
    rule = {r.task.task_id: r for r in runs if r.mode == "rule"}
    pairs = [
        (r, rule[r.task.task_id])
        for r in runs
        if r.mode == "llm" and r.outcome == "accepted" and rule[r.task.task_id].outcome == "accepted"
    ]
    result["paired_accepted_llm_vs_rule"] = dict(
        run_pairs=len(pairs),
        unique_tasks=len({a.task.task_id for a, _ in pairs}),
        llm_mean_calls=mean(a.calls for a, _ in pairs) if pairs else None,
        rule_mean_calls=mean(b.calls for _, b in pairs) if pairs else None,
        note="Repeated tasks are correlated. Fewer calls do not imply lower energy or a better process design.",
    )
    (output / "audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    print(json.dumps(audit(parser.parse_args().input), indent=2))


if __name__ == "__main__":
    main()
