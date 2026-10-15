"""Tables and scientific figures derived only from the immutable reliability logs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean, median
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

NAMES = {"binary": "Binary distillation", "extractive": "Extractive distillation", "extraction": "Crossflow extraction"}


def csv_write(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def export(fig: Any, directory: Path, name: str) -> None:
    for suffix in ("png", "svg", "pdf"):
        fig.savefig(directory / (name + "." + suffix), dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_report(directory: Path) -> None:
    runs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((directory / "runs").glob("*.json"))]
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    expected_total = len(manifest["tasks"]) * manifest["repeats"]
    figures = directory / "figures"
    figures.mkdir(exist_ok=True)
    rows = []
    for case in NAMES:
        good = [r for r in runs if r["case"] == case and r["kind"] == "equivalent"]
        bad = [r for r in runs if r["case"] == case and r["kind"] != "equivalent"]
        if not good:
            continue
        eligible_reports = [r for r in good if "report_audit" in r]
        case_runs = good + bad
        row: dict[str, Any] = dict(case=case, equivalent_requests=len(good), challenge_requests=len(bad))
        for metric in (
            "parse_correct",
            "plan_correct",
            "tool_execution_correct",
            "result_consistent",
            "report_grounded",
        ):
            row[metric] = sum(r["metrics"][metric] for r in good)
        for metric in ("clarification_correct", "gate_blocks_invalid"):
            row[metric] = sum(r["metrics"][metric] for r in bad)
        row.update(
            fresh_protocol_runs=sum(r.get("cache_hit") is False for r in good),
            cached_protocol_runs=sum(r.get("cache_hit") is True for r in good),
            generated_reports=len(eligible_reports),
            unsupported_claims=sum(len(r["report_audit"]["unsupported_claims"]) for r in eligible_reports),
            total_claims=sum(len(r["raw_report"]["claims"]) for r in eligible_reports),
            mean_llm_tokens=mean(r["llm_tokens"] for r in case_runs),
            median_request_wall_s=median(r["elapsed_s"] for r in case_runs),
            llm_calls=sum(len(r["provider_calls"]) for r in case_runs),
        )
        rows.append(row)
    csv_write(directory / "evaluation.csv", rows)
    csv_write(
        directory / "runs.csv",
        [
            dict(
                task_id=r["task_id"],
                case=r["case"],
                kind=r["kind"],
                repeat=r["repeat"],
                outcome=r["outcome"],
                cache_hit=r.get("cache_hit"),
                elapsed_s=r["elapsed_s"],
                llm_tokens=r["llm_tokens"],
                **r["metrics"],
            )
            for r in runs
        ],
    )
    repeat_rows = []
    for repeat in range(manifest["repeats"]):
        good = [r for r in runs if r["repeat"] == repeat and r["kind"] == "equivalent"]
        bad = [r for r in runs if r["repeat"] == repeat and r["kind"] != "equivalent"]
        repeat_rows.append(
            dict(
                repeat=repeat,
                equivalent_requests=len(good),
                challenge_requests=len(bad),
                parsed=sum(r["metrics"]["parse_correct"] for r in good),
                grounded=sum(r["metrics"]["report_grounded"] for r in good),
                clarified=sum(r["metrics"]["clarification_correct"] for r in bad),
                invalid_blocked=sum(r["metrics"]["gate_blocks_invalid"] for r in bad),
            )
        )
    csv_write(directory / "repeats.csv", repeat_rows)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 4.4), gridspec_kw={"width_ratios": [2, 1]}, layout="constrained")
    metrics = ["parse_correct", "plan_correct", "tool_execution_correct", "result_consistent", "report_grounded"]
    labels = ["Task\ncompilation", "Tool\nplan", "Tool\nexecution*", "Paper result\nconsistency*", "Grounded\nreport"]
    for ax, fields, names, denominator in (
        (axes[0], metrics, labels, "equivalent_requests"),
        (
            axes[1],
            ["clarification_correct", "gate_blocks_invalid"],
            ["LLM\nclarification", "System\nblocking"],
            "challenge_requests",
        ),
    ):
        data = np.array([[row[m] / row[denominator] if row[denominator] else 0 for m in fields] for row in rows])
        ax.imshow(data, vmin=0, vmax=1, cmap="Blues", aspect="auto")
        ax.set_xticks(range(len(fields)), names)
        ax.set_yticks(range(len(rows)), [NAMES[r["case"]] for r in rows])
        for y, row in enumerate(rows):
            for x, field in enumerate(fields):
                ax.text(
                    x,
                    y,
                    f"{row[field]}/{row[denominator]}",
                    ha="center",
                    va="center",
                    color="white" if data[y, x] > 0.6 else "black",
                    fontsize=12,
                )
    axes[0].set_title("a  Equivalent requests (5 per case, each repeated 3 times)", loc="left", pad=14)
    axes[1].set_title("b  Incomplete / conflicting inputs", loc="left", pad=14)
    axes[1].set_yticklabels([])
    fig.supxlabel(
        "*First matching contract runs fresh physics; later equivalent requests reuse its recorded result.\n"
        "Counts describe this 24-request development pilot; repetitions are not independent chemical tasks.",
        fontsize=9,
    )
    export(fig, figures, "reliability")
    fig, axes = plt.subplots(3, 5, figsize=(16.4, 8.5))
    headers = ["Requirement", "Compiled plan", "Numerical tools", "Evidence review", "Bounded report"]
    for row_idx, case in enumerate(NAMES):
        options = [r for r in runs if r["case"] == case and r["kind"] == "equivalent" and r["outcome"] == "reported"]
        if not options:
            continue
        run = min(options, key=lambda r: (r.get("cache_hit", True), r["repeat"], r["task_id"]))
        final = run.get("final", {})
        compiled = run.get("compiled", {}).get("contract")
        if case == "binary":
            requirement = (
                "n-Heptane / n-nonane\n1 mol/s; 101.3 kPa\nPurity >=99.5 mol%\nRecovery >=98%\nFixed paper reflux"
            )
            numerical = (
                f"Original 16-state grid\nPCHIP: {final.get('pchip_stages', '?')} stages\n"
                f"Linear: {final.get('linear_stages', '?')} stages\nFeed stage: {final.get('feed_stage', '?')}"
            )
            review = (
                "Composition + balances\nBubble pressure residual\nInterpolation sensitivity\nPreliminary model scope"
            )
        elif case == "extractive":
            requirement = (
                "Alcohol / ester / DMF\n1 mol/s; 101.3 kPa\nMass S/F=32; reflux=48\nPurity >=99.5 mol%\nRecovery >=98%"
            )
            numerical = (
                "Fresh direct bubbles\n182 / 183 stage boundary\n"
                f"Selected purity: {100 * final.get('purity', 0):.6f}%\n"
                f"Recovery: {100 * final.get('recovery', 0):.6f}%"
            )
            review = "Unrounded target check\nStage + global balances\nExperimental coverage\nNo process certification"
        else:
            requirement = (
                "Heptane / benzene\nFurfural: 1.5 mol/s\n303.15 K; 101.3 kPa\nRecovery >=70%\nHeptane retention >=80%"
            )
            numerical = (
                f"Selected stages: {final.get('stages', '?')}\n"
                f"Recovery: {100 * final.get('recovery', 0):.4f}%\n"
                f"Retention: {100 * final.get('retention', 0):.4f}%\nRegistered allocation scan"
            )
            review = "Stagewise balances\nLLE residual / grid TPD\nBoth product targets\nFinite candidate scope"
        plan = "Normalize units\nBind component identities\nCheck required fields\nSelect registered protocol"
        if compiled is None:
            plan = "No executable contract\n" + run["outcome"]
        report = (
            f"Outcome: {run['outcome']}\n"
            f"Supported claims: {len(run.get('report_audit', {}).get('supported_claims', []))}\n"
            f"{'Cached' if run.get('cache_hit') else 'Fresh'} numerical tool result\n"
            "Evidence IDs attached\nLimitations retained"
        )
        for col_idx, content in enumerate([requirement, plan, numerical, review, report]):
            ax = axes[row_idx, col_idx]
            ax.axis("off")
            if row_idx == 0:
                ax.set_title(headers[col_idx], fontsize=12, fontweight="bold", pad=24)
            ax.text(
                0.5,
                0.52,
                content,
                transform=ax.transAxes,
                ha="center",
                va="center",
                linespacing=1.7,
                fontsize=9.5,
                bbox=dict(boxstyle="round,pad=0.7", facecolor="#eef4f8", edgecolor="#9bb4c5"),
            )
            if col_idx < 4:
                ax.annotate(
                    "",
                    xy=(1.13, 0.52),
                    xytext=(0.98, 0.52),
                    xycoords="axes fraction",
                    arrowprops=dict(arrowstyle="->", color="#526a78"),
                    annotation_clip=False,
                )
        axes[row_idx, 0].text(
            0, 1.08, NAMES[case], transform=axes[row_idx, 0].transAxes, fontsize=11, fontweight="bold"
        )
        axes[row_idx, 0].text(
            0, -0.03, f"{run['task_id']}; repetition {run['repeat']}", transform=axes[row_idx, 0].transAxes, fontsize=8
        )
    fig.suptitle("Recorded Agent executions under frozen paper protocols", fontsize=15, y=1.01)
    fig.text(
        0.5,
        -0.015,
        "First successful fresh execution per case when available; exact request IDs are shown. "
        "The LLM does not generate thermodynamic numbers.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(w_pad=1.5, h_pad=3)
    export(fig, figures, "trajectories")
    numerical_bundles = [
        json.loads(p.read_text(encoding="utf-8")) for p in sorted((directory / "numerical").glob("*.json"))
    ]
    models = sorted({c.get("model", c.get("requested_model", "unknown")) for r in runs for c in r["provider_calls"]})
    failures = [
        dict(
            task_id=r["task_id"],
            repeat=r["repeat"],
            outcome=r["outcome"],
            metrics=r["metrics"],
            error=r.get("error"),
            report_audit=r.get("report_audit"),
        )
        for r in runs
        if (r["kind"] == "equivalent" and not all(r["metrics"][m] for m in metrics))
        or (r["kind"] != "equivalent" and not r["metrics"]["clarification_correct"])
    ]
    summary = dict(
        completed=len(runs),
        expected=expected_total,
        complete=len(runs) == expected_total,
        models=models,
        llm_calls=sum(len(r["provider_calls"]) for r in runs),
        llm_tokens=sum(r["llm_tokens"] for r in runs),
        cases=rows,
        repeats=repeat_rows,
        paper_agreement={b["protocol"]: b["paper_agreement"] for b in numerical_bundles},
        failures=failures,
    )
    (directory / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    text = [
        "# Agent reliability experiment: results and reproduction record",
        "",
        f"Completed {len(runs)}/{expected_total} scheduled requests. Model(s): {', '.join(models)}.",
        "",
        "This is a development pilot over three known chemical systems: 15 equivalent requests and 9 input challenges, "
        "each repeated independently three times at temperature 0. Repeated runs are not independent design tasks.",
        "",
        "|Case|Task compilation|Tool plan|Tool execution*|Result consistency*|Grounded report|"
        "LLM clarification|System blocks invalid|",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        values = [f"{row[m]}/{row['equivalent_requests']}" for m in metrics]
        values += [f"{row[m]}/{row['challenge_requests']}" for m in ("clarification_correct", "gate_blocks_invalid")]
        text.append("|" + NAMES[row["case"]] + "|" + "|".join(values) + "|")
    text += [
        "",
        "*First matching contract invokes fresh ThermoFormer/process calculations. Later matches reuse the "
        "same hashed numerical artifact. Cached equivalence is a routing/reproducibility check, not independent "
        "numerical validation or repeated model inference.",
        "",
        "## Paper result checks",
        "",
    ]
    for bundle in numerical_bundles:
        text.append(
            f"- {NAMES[bundle['protocol']]}: agreement={bundle['paper_agreement']['passed']}; "
            f"tolerance: {bundle['paper_agreement']['tolerance']}."
        )
    text += [
        "",
        "Unrounded extractive-column targets are checked separately from floating-point agreement. "
        "Original scientific source files, weights, and archived paper outputs are not overwritten.",
        "",
        "## Interpretation",
        "",
        "Task compilation includes deterministic unit conversion and source/applicability checks. "
        "LLM clarification is scored on its raw status, issue type and named field; system blocking is separate. "
        "Grounding is scored on the LLM's raw structured claims before the output gate. Reports use a constrained "
        "claim catalog and evidence IDs; this does not measure unrestricted prose hallucination.",
        "",
        "No fixed/rule/LLM search competition, new process optimization, held-out molecular generalization, "
        "independent process experiments, or DWSIM certification is claimed. "
        "Reference agreement does not establish physical accuracy or global phase stability.",
        "",
        f"Provider calls: {summary['llm_calls']}; provider-reported total tokens: {summary['llm_tokens']}.",
        "",
        "See evaluation.csv, runs.csv and repeats.csv for denominators, time, tokens and cache counts. "
        "See summary.json for all failures (including empty lists), manifest.json for pre-run inputs and hashes, "
        "source_integrity.json for the end-of-run integrity check, runs/ for exact requests/responses/tool provenance, "
        "and numerical/ for complete solver observations.",
        "",
        "## Reproduce (PowerShell)",
        "",
        "```powershell",
        "& E:/anaconda/envs/ggnn39/python.exe -m benchmarks.paper_agent.reliability_run "
        "--output outputs/paper_agent/reliability-new --repeats 3",
        "& E:/anaconda/envs/ggnn39/python.exe -m benchmarks.paper_agent.reliability_report "
        "--input outputs/paper_agent/reliability-new",
        "```",
        "",
    ]
    (directory / "RESULTS.md").write_text("\n".join(text), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("complete", "completed", "llm_calls", "llm_tokens", "models")}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    build_report(parser.parse_args().input)


if __name__ == "__main__":
    main()
