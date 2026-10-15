"""Plot real saved runs, with evidence deferral separate from failed reference checks."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean, stdev
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from paper_agent.contracts import PaperRun


def build_report(directory: Path) -> None:
    runs = [
        PaperRun.model_validate_json(p.read_text(encoding="utf-8"))
        for p in sorted(directory.glob("*.json"))
        if p.name not in {"tasks.json", "summary.json"}
    ]
    if not runs:
        raise ValueError("No saved runs")
    output = directory / "figures"
    output.mkdir(exist_ok=True)
    modes = [
        mode for mode in ("fixed", "rule", "llm", "rule_guided", "llm_guided") if any(r.mode == mode for r in runs)
    ]
    cases = ["binary", "extractive", "extraction"]
    titles = ["Binary distillation", "Extractive distillation", "Crossflow extraction"]
    rows: list[dict[str, Any]] = []
    repeat_rows: list[dict[str, Any]] = []
    for case in cases:
        for mode in modes:
            selected = [r for r in runs if r.task.case == case and r.mode == mode]
            if not selected:
                continue
            counts = Counter(r.outcome for r in selected)
            repeat_means = []
            for repeat in sorted({r.repeat for r in selected}):
                group = [r for r in selected if r.repeat == repeat]
                repeat_means.append(mean(r.calls for r in group))
                repeat_rows.append(
                    dict(
                        case=case,
                        mode=mode,
                        repeat=repeat,
                        runs=len(group),
                        accepted=sum(r.outcome == "accepted" for r in group),
                        deferred=sum(r.outcome == "deferred" for r in group),
                        mean_calls=mean(r.calls for r in group),
                    )
                )
            ref_accepted = [
                r
                for r in selected
                if r.outcome == "accepted" and r.assessment.get("reference_meets_targets") is not None
            ]
            rows.append(
                dict(
                    case=case,
                    mode=mode,
                    runs=len(selected),
                    accepted=counts["accepted"],
                    deferred=counts["deferred"],
                    stopped=counts["stopped"],
                    exhausted=counts["exhausted"],
                    provider_error=counts["provider_error"],
                    unresolved_acceptance=sum(
                        bool(r.assessment.get("accepted_with_unresolved_evidence")) for r in selected
                    ),
                    accepted_with_reference=len(ref_accepted),
                    failed_reference_checks=sum(
                        bool(r.assessment.get("false_acceptance_against_reference")) for r in ref_accepted
                    ),
                    mean_calls=mean(r.calls for r in selected),
                    repeat_mean_calls_sd=stdev(repeat_means) if len(repeat_means) > 1 else 0,
                    mean_wall_s=mean(r.elapsed_s for r in selected),
                )
            )
    with (output / "comparison.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (output / "repeats.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(repeat_rows[0]))
        writer.writeheader()
        writer.writerows(repeat_rows)
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
        }
    )
    fig, axes = plt.subplots(3, 3, figsize=(16, 10), constrained_layout=True)
    colors = {
        "accepted": "#287c8e",
        "deferred": "#e6af46",
        "stopped": "#a7b0bd",
        "exhausted": "#676f80",
        "provider_error": "#c14f55",
    }
    for col, (case, title) in enumerate(zip(cases, titles)):  # noqa: B905 - ggnn39
        records = [r for r in rows if r["case"] == case]
        if not records:
            for ax in axes[:, col]:
                ax.set_visible(False)
            continue
        bottom = [0] * len(records)
        for outcome, color in colors.items():
            values = [100 * r[outcome] / r["runs"] for r in records]
            axes[0, col].bar([r["mode"] for r in records], values, bottom=bottom, color=color, label=outcome)
            for i, value in enumerate(values):
                if value:
                    axes[0, col].text(i, bottom[i] + value / 2, f"{value:.0f}%", ha="center", va="center")
            bottom = [a + b for a, b in zip(bottom, values)]  # noqa: B905 - ggnn39
        axes[0, col].set_title(title)
        axes[0, col].set_ylabel("Outcomes (% of runs)")
        axes[0, col].set_ylim(0, 100)
        axes[0, col].set_xticks(
            range(len(records)), [f"{r['mode']}\nn={r['runs']}" for r in records], rotation=25, fontsize=8
        )
        for i, record in enumerate(records):
            axes[1, col].bar(
                i, record["mean_calls"], width=0.55, color="#667bb3", yerr=record["repeat_mean_calls_sd"], capsize=4
            )
            axes[2, col].bar(i, 100 * record["unresolved_acceptance"] / record["runs"], width=0.55, color="#ce7559")
        axes[1, col].set_xticks(range(len(records)), [r["mode"] for r in records], rotation=25, fontsize=8)
        axes[1, col].set_ylabel("Mean numerical tool calls")
        axes[1, col].set_ylim(0, max(7, max(r["mean_calls"] for r in records) + 1))
        axes[2, col].set_xticks(range(len(records)), [r["mode"] for r in records], rotation=25, fontsize=8)
        axes[2, col].set_ylabel("Evidence-gap acceptance (% of runs)")
        axes[2, col].set_ylim(0, 100)
    axes[0, 0].legend(loc="lower left", bbox_to_anchor=(0, 1.08), ncol=3, fontsize=8)
    fig.suptitle(
        "Within-system tasks | shared tools and call budgets\n"
        "Rates account for repetitions. Call error bars: SD of repeat means.",
        fontsize=13,
    )
    for extension in ("png", "pdf", "svg"):
        fig.savefig(output / ("comparison." + extension), dpi=180)
    plt.close(fig)

    # Explicit illustrative cases; no claim these alone measure aggregate performance.
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.6), constrained_layout=True)
    selected_ids = ["binary-01", "extractive-01", "extraction-00"]
    trace_mode = "llm_guided" if "llm_guided" in modes else "llm" if "llm" in modes else "rule"
    for ax, task_id, title in zip(axes, selected_ids, titles):  # noqa: B905 - ggnn39
        matches = [r for r in runs if r.task.task_id == task_id and r.mode == trace_mode and r.repeat == 0]
        if not matches:
            ax.text(0.5, 0.5, "No recorded trajectory", ha="center")
            continue
        run = matches[0]
        entries = [t for t in run.trace if t.observation]
        metrics = [t.observation.metrics if t.observation and t.observation.status == "valid" else {} for t in entries]
        x = list(range(1, len(metrics) + 1))
        if run.task.case == "binary":
            ax.plot(x, [m.get("stages", float("nan")) for m in metrics], "o-", color="#287c8e", label="Required stages")
            ax.axhline(run.task.max_stages, color="#ce7559", linestyle="--", label="Stage limit")
            ax.set_ylabel("Equilibrium stages (incl. reboiler)")
        elif run.task.case == "extractive":
            ax.plot(
                x,
                [100 * m.get("margin", float("nan")) for m in metrics],
                "o-",
                color="#287c8e",
                label="Minimum target margin",
            )
            ax.axhline(0, color="#676f80", linestyle=":", label="Nominal threshold")
            ax.axhline(100 * run.task.margin, color="#ce7559", linestyle="--", label="Requested guard")
            ax.set_yscale("symlog", linthresh=0.02)
            ax.set_ylabel("Margin (percentage points; symlog)")
        else:
            ax.plot(
                x, [m.get("recovery", float("nan")) for m in metrics], "o-", color="#287c8e", label="Benzene recovery"
            )
            ax.plot(
                x, [m.get("retention", float("nan")) for m in metrics], "s-", color="#667bb3", label="Heptane retention"
            )
            ax.axhline(run.task.recovery, color="#287c8e", linestyle="--", label="Recovery target")
            ax.axhline(run.task.retention, color="#667bb3", linestyle="--", label="Retention target")
            ax.set_ylabel("Fraction")
        ax.set_xticks(
            x, [t.choice.action_id.replace("verify:", "verify\n") for t in entries], rotation=25, ha="right", fontsize=8
        )
        ax.set_title(title + "\n" + task_id + ": " + run.outcome)
        for position, entry in enumerate(entries, start=1):
            if entry.observation and entry.observation.status == "failed":
                ax.text(
                    position,
                    0.45,
                    "Validation failed\n(result not accepted)",
                    color="#c14f55",
                    ha="center",
                    fontsize=8,
                    transform=ax.get_xaxis_transform(),
                )
        ax.set_xlabel(f"Recorded action ({trace_mode}, repeat 0)")
        ax.margins(y=0.12)
        ax.legend(fontsize=8, loc="best")
    for extension in ("png", "pdf", "svg"):
        fig.savefig(output / ("trajectories." + extension), dpi=180)
    plt.close(fig)
    table = [
        "# Pilot results",
        "",
        "Recorded policies: " + ", ".join(modes) + ". See repeats.csv for repetition-level variation.",
        "",
        "|Case|Policy|Runs|Accepted|Deferred|Other|Evidence-gap acceptance|Mean calls|",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        table.append(
            f"|{r['case']}|{r['mode']}|{r['runs']}|{r['accepted']}|{r['deferred']}|"
            f"{r['runs'] - r['accepted'] - r['deferred']}|{r['unresolved_acceptance']}|{r['mean_calls']:.2f}|"
        )
    table += [
        "",
        "Accepted designs with an experiment-derived process reference: "
        + str(sum(r["accepted_with_reference"] for r in rows))
        + "; failed reference checks: "
        + str(sum(r["failed_reference_checks"] for r in rows))
        + ".",
        "",
        "The extractive column has no independent process reference. Evidence gaps do not establish physical error. "
        "The reference calculations use measured equilibrium data and are not experimental column operations. "
        "No independent train/test split is claimed. Tasks vary conditions within three systems. "
        "Repeated LLM runs share the same tasks and are not independent new systems. "
        "Evidence-gap acceptance is not a demonstrated physical error rate.",
        "",
        "Numerical calls include evaluation and verification; costs per call differ. See comparison.csv for wall time. "
        "Runs were sequential, so wall time is descriptive and not a controlled timing benchmark. "
        "The illustrated traces are selected examples, not a replacement for the full table.",
    ]
    (output / "RESULTS.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    print(json.dumps(rows, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    build_report(parser.parse_args().input)


if __name__ == "__main__":
    main()
