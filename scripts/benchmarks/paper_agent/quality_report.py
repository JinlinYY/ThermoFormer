"""Joint quality/evidence/cost evaluation without converting proxies into economics."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from paper_agent.contracts import PaperRun

MODES = ("fixed", "rule", "llm", "rule_guided", "llm_guided")


def accepted_key(run: PaperRun) -> tuple[float, ...] | None:
    observation = run.final_observation
    if run.outcome != "accepted" or observation is None or observation.status != "valid":
        return None
    metrics = observation.metrics
    if run.task.case == "binary":
        return (metrics["reflux"],)
    if run.task.case == "extraction":
        return (metrics["stages"],)
    return (metrics["stages"], metrics["reflux"])


def emit_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_quality_report(directory: Path) -> dict[str, Any]:
    runs = [PaperRun.model_validate_json(p.read_text(encoding="utf-8")) for p in sorted(directory.glob("*-*-*.json"))]
    output = directory / "figures"
    output.mkdir(exist_ok=True)
    rows: list[dict[str, Any]] = []
    case_rows: list[dict[str, Any]] = []
    for mode in MODES:
        group = [r for r in runs if r.mode == mode]
        if not group:
            continue
        costs = [
            sum(c.get("usage", {}).get("total_tokens", 0) for c in r.provenance.get("llm_calls", [])) for r in group
        ]
        rows.append(
            dict(
                mode=mode,
                runs=len(group),
                accepted=sum(r.outcome == "accepted" for r in group),
                nominal_found=sum(
                    any(
                        e.observation and e.observation.status == "valid" and e.observation.meets_targets
                        for e in r.trace
                    )
                    for r in group
                ),
                evidence_gap_acceptance=sum(bool(r.assessment.get("accepted_with_unresolved_evidence")) for r in group),
                mean_calls=mean(r.calls for r in group),
                mean_wall_s=mean(r.elapsed_s for r in group),
                mean_llm_tokens=mean(costs),
                total_llm_tokens=sum(costs),
                provider_error=sum(r.outcome == "provider_error" for r in group),
            )
        )
        for case in ("binary", "extractive", "extraction"):
            accepted = [r for r in group if r.task.case == case and r.outcome == "accepted" and r.final_observation]
            record: dict[str, Any] = dict(case=case, mode=mode, accepted_runs=len(accepted))
            for metric in ("reflux", "stages", "recovery", "retention"):
                values = [
                    r.final_observation.metrics[metric]
                    for r in accepted
                    if r.final_observation and metric in r.final_observation.metrics
                ]
                record["mean_" + metric] = mean(values) if values else None
            case_rows.append(record)
    emit_csv(output / "joint_metrics.csv", rows)
    emit_csv(output / "accepted_design_quality.csv", case_rows)
    pairs: list[dict[str, Any]] = []
    for comparator in ("llm", "rule_guided"):
        baseline = {(r.task.task_id, r.repeat): r for r in runs if r.mode == comparator}
        for run in runs:
            if run.mode != "llm_guided":
                continue
            previous = baseline.get((run.task.task_id, run.repeat if comparator == "llm" else 0))
            if previous is None:
                continue
            current_key, previous_key = accepted_key(run), accepted_key(previous)
            quality = "not_both_accepted"
            if current_key is not None and previous_key is not None:
                quality = "better" if current_key < previous_key else "worse" if current_key > previous_key else "tie"
            pairs.append(
                dict(
                    task_id=run.task.task_id,
                    case=run.task.case,
                    repeat=run.repeat,
                    comparator=comparator,
                    baseline_outcome=previous.outcome,
                    guided_outcome=run.outcome,
                    quality_comparison=quality,
                    baseline_resource_key=previous_key,
                    guided_resource_key=current_key,
                    baseline_calls=previous.calls,
                    guided_calls=run.calls,
                )
            )
    if pairs:
        emit_csv(output / "paired_quality.csv", pairs)
    summary = {
        "modes": rows,
        "paired_quality": {
            comparator: dict(Counter(p["quality_comparison"] for p in pairs if p["comparator"] == comparator))
            for comparator in ("llm", "rule_guided")
        },
        "stopping_certificates": dict(
            Counter(str(r.assessment.get("stopping_certificate")) for r in runs if r.mode == "llm_guided")
        ),
    }
    (output / "quality_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
        }
    )
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), constrained_layout=True)
    labels = [r["mode"].replace("_", "\n") for r in rows]
    accepted = [100 * r["accepted"] / r["runs"] for r in rows]
    nominal = [100 * r["nominal_found"] / r["runs"] for r in rows]
    x = list(range(len(rows)))
    axes[0, 0].bar([i - 0.18 for i in x], nominal, width=0.35, label="Nominal target found", color="#adb6c5")
    axes[0, 0].bar([i + 0.18 for i in x], accepted, width=0.35, label="Accepted", color="#287c8e")
    axes[0, 0].set_ylim(0, 100)
    axes[0, 0].set_ylabel("% of runs")
    axes[0, 0].legend(fontsize=8)
    axes[0, 0].set_title("Design attainment")
    axes[0, 1].bar(x, [100 * r["evidence_gap_acceptance"] / r["runs"] for r in rows], color="#ce7559")
    axes[0, 1].set_ylim(0, 100)
    axes[0, 1].set_ylabel("% of runs")
    axes[0, 1].set_title("Acceptance with evidence gaps")
    axes[0, 2].bar(x, [r["mean_calls"] for r in rows], color="#667bb3")
    axes[0, 2].set_title("Mean numerical tool calls")
    axes[1, 0].bar(x, [r["mean_wall_s"] for r in rows], color="#667bb3")
    axes[1, 0].set_ylabel("Seconds")
    axes[1, 0].set_title("Mean wall time (descriptive)")
    axes[1, 1].bar(x, [r["mean_llm_tokens"] for r in rows], color="#667bb3")
    axes[1, 1].set_title("Mean LLM tokens per run")
    compare = [p for p in pairs if p["comparator"] == "llm" and p["quality_comparison"] != "not_both_accepted"]
    counts = Counter(p["quality_comparison"] for p in compare)
    axes[1, 2].bar(
        ["better", "tie", "worse"],
        [counts[k] for k in ["better", "tie", "worse"]],
        color=["#287c8e", "#adb6c5", "#ce7559"],
    )
    axes[1, 2].set_title("Guided vs original LLM: resource preference\nBoth accepted; correlated repeated tasks")
    axes[1, 2].set_ylabel("Paired runs")
    for ax in list(axes.flat)[:5]:
        ax.set_xticks(x, labels, fontsize=8)
    fig.suptitle("Design quality, evidence and computational cost | Resource proxies are not energy or monetary cost")
    for extension in ("png", "pdf", "svg"):
        fig.savefig(output / ("joint_evaluation." + extension), dpi=180)
    plt.close(fig)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    print(json.dumps(build_quality_report(parser.parse_args().input), indent=2))


if __name__ == "__main__":
    main()
