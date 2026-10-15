# ruff: noqa: E402
"""Six-panel result figure from recorded interactions and unchanged process results."""

from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPOSITORY_ROOT / "Web/ThermoFormer-web/backend"
for _directory in (REPOSITORY_ROOT, BACKEND_ROOT):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))


import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.ticker import FuncFormatter

from scripts.benchmarks.paper_agent.reliability_run import digest

CASES = ["binary", "extractive", "extraction"]
SHORT = {"binary": "Binary", "extractive": "Extractive", "extraction": "Crossflow"}
BLUE, TEAL, AMBER, RED, PURPLE = "#326b99", "#248d80", "#d59b38", "#c35c59", "#7a6ca8"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def heading(ax: Any, letter: str, title: str) -> None:
    ax.set_title(title, loc="left", fontsize=11, pad=16)
    ax.text(-0.12, 1.10, letter, transform=ax.transAxes, fontsize=16, fontweight="bold")


def make_report(directory: Path) -> None:
    manifest = load(directory / "manifest.json")
    source = (directory / manifest["source"]).resolve()
    replay = load(directory / "paired_routing_replay.json")
    recovery = [load(p) for p in sorted((directory / "recovery").glob("*.json"))]
    decisions = [load(p) for p in sorted((directory / "decisions").glob("*.json"))]
    if len(recovery) != 27 or len(decisions) != 27:
        raise ValueError(
            "The main figure requires all 27 recovery and 27 evidence-scenario records"
        )
    if not load(directory / "integrity.json")["source_and_code_unchanged"]:
        raise ValueError("Experiment integrity check failed")
    for relative, value in manifest["source_hashes"].items():
        if digest(source / relative) != value:
            raise ValueError("Source result modified: " + relative)
    bundles = {b["protocol"]: b for p in (source / "numerical").glob("*.json") for b in [load(p)]}
    figures = directory / "figures"
    figures.mkdir(exist_ok=True)
    routing_rows = []
    for kind in ("equivalent", "missing", "conflict", "ambiguous"):
        group = [r for r in replay if r["kind"] == kind]
        routing_rows.append(
            dict(
                kind=kind,
                runs=len(group),
                schema_only_correct=sum(
                    r["schema_only_ready"] == (kind == "equivalent") for r in group
                ),
                full_contract_correct=sum(
                    r["contract_ready"] == (kind == "equivalent") for r in group
                ),
            )
        )
    write_csv(directory / "routing.csv", routing_rows)
    recovery_rows = []
    for case in CASES:
        group = [r for r in recovery if r["case"] == case]
        recovery_rows.append(
            dict(
                case=case,
                runs=len(group),
                input_resolved=sum(r["parsed_correct"] for r in group),
                numerical_cache_retrieved=sum(r["executed"] for r in group),
                result_preserved=sum(r["result_preserved"] for r in group),
                grounded_report=sum(r["report_grounded"] for r in group),
            )
        )
    write_csv(directory / "recovery.csv", recovery_rows)
    evidence_rows = []
    for case in CASES:
        for condition in (
            "complete",
            "validation_withheld",
            "constraint_not_met",
            "validation_restored",
        ):
            base = "validation_withheld" if condition == "validation_restored" else condition
            group = [r for r in decisions if r["case"] == case and r["condition"] == base]
            restored = condition == "validation_restored"
            actions = [
                r.get("restored_decision" if restored else "decision", {}).get("action", "missing")
                for r in group
            ]
            scores = [r["restored_passed" if restored else "passed"] for r in group]
            evidence_rows.append(
                dict(
                    case=case,
                    condition=condition,
                    runs=len(group),
                    passed=sum(scores),
                    actions=json.dumps(dict(Counter(actions)), sort_keys=True),
                )
            )
    write_csv(directory / "evidence_decisions.csv", evidence_rows)
    cost_rows = []
    for name, group in [("clarification_recovery", recovery), ("evidence_feedback", decisions)]:
        cost_rows.append(
            dict(
                experiment=name,
                scenario_runs=len(group),
                api_calls=sum(len(r["llm_calls"]) for r in group),
                total_tokens=sum(r["tokens"] for r in group),
                median_scenario_wall_s=median(r["elapsed_s"] for r in group),
                fresh_equilibrium_calls=0,
            )
        )
    write_csv(directory / "cost.csv", cost_rows)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
        }
    )
    fig, axes = plt.subplots(2, 3, figsize=(13.8, 8.4))
    fig.subplots_adjust(left=0.077, right=0.978, top=0.925, bottom=0.10, hspace=0.68, wspace=0.50)
    fig.suptitle(
        "Reliable execution and evidence-guided decisions in separation design",
        fontsize=15,
        y=1.025,
    )

    ax = axes[0, 0]
    data = np.array(
        [
            [r[k] / r["runs"] for k in ("schema_only_correct", "full_contract_correct")]
            for r in routing_rows
        ]
    )
    ax.imshow(data, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks([0, 1], ["Schema-only\nreplay", "With task\ncontract"])
    ax.set_yticks(range(4), ["Complete", "Missing", "Conflicting", "Basis absent"])
    for y, row in enumerate(routing_rows):
        for col_index, key in enumerate(("schema_only_correct", "full_contract_correct")):
            ax.text(
                col_index,
                y,
                f"{row[key]}/{row['runs']}",
                ha="center",
                va="center",
                color="white" if data[y, col_index] > 0.55 else "#222222",
                fontsize=12,
            )
    heading(ax, "a", "Correct routing of design requests")
    ax.text(
        0.5,
        -0.27,
        "Paired replay of the same LLM outputs",
        ha="center",
        transform=ax.transAxes,
        fontsize=8,
    )

    ax = axes[0, 1]
    recovered = np.array([r["grounded_report"] for r in recovery_rows])
    resolved = np.array([r["input_resolved"] for r in recovery_rows])
    n = np.array([r["runs"] for r in recovery_rows])
    x = np.arange(3)
    ax.bar(x, recovered, width=0.6, color=TEAL, label="Recovered + grounded report")
    ax.bar(
        x, resolved - recovered, bottom=recovered, width=0.6, color=AMBER, label="Report incomplete"
    )
    ax.bar(x, n - resolved, bottom=resolved, width=0.6, color=RED, label="Still unresolved")
    for i, count in enumerate(recovered):
        ax.text(i, n[i] + 0.22, f"{count}/{n[i]}", ha="center", fontsize=11)
    ax.set_xticks(x, [SHORT[c] for c in CASES])
    ax.set_ylim(0, 10.7)
    ax.set_yticks([0, 3, 6, 9])
    ax.set_ylabel("Requests after one scripted correction")
    handles, legend_labels = ax.get_legend_handles_labels()
    if int(recovered.sum()) == int(n.sum()):
        handles, legend_labels = handles[:1], legend_labels[:1]
    ax.legend(
        handles,
        legend_labels,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.14),
        frameon=False,
        fontsize=7.5,
    )
    heading(ax, "b", "Recovery after clarification")

    ax = axes[0, 2]
    action_codes = {
        "report_preliminary": 0,
        "request_verification": 1,
        "withhold_target_claim": 2,
        "claim_experimental_confirmation": 3,
        "missing": 3,
    }
    letters = {0: "P", 1: "V", 2: "H", 3: "X"}
    cells = np.zeros((3, 4))
    for row in evidence_rows:
        y = CASES.index(row["case"])
        xidx = [
            "complete",
            "validation_withheld",
            "constraint_not_met",
            "validation_restored",
        ].index(row["condition"])
        action_counts: dict[str, int] = json.loads(row["actions"])
        cells[y, xidx] = action_codes[max(action_counts, key=lambda k: action_counts[k])]
    ax.imshow(
        cells, cmap=ListedColormap([TEAL, AMBER, PURPLE, RED]), vmin=-0.5, vmax=3.5, aspect="auto"
    )
    for row in evidence_rows:
        y = CASES.index(row["case"])
        xidx = [
            "complete",
            "validation_withheld",
            "constraint_not_met",
            "validation_restored",
        ].index(row["condition"])
        ax.text(
            xidx,
            y,
            f"{letters[int(cells[y, xidx])]}\n{row['passed']}/{row['runs']}",
            ha="center",
            va="center",
            color="white",
        )
    ax.set_xticks(
        range(4),
        ["Complete", "Check\nwithheld", "Constraint\nnot met", "Check\nrestored"],
        fontsize=8,
    )
    ax.set_yticks(range(3), [SHORT[c] for c in CASES])
    heading(ax, "c", "Evidence-conditioned decisions")
    ax.text(
        0.5,
        -0.27,
        "P: preliminary report   V: verify   H: withhold target claim",
        ha="center",
        transform=ax.transAxes,
        fontsize=7.3,
    )

    ax = axes[1, 0]
    binary = bundles["binary"]["final"]
    counts = [binary["pchip_stages"], binary["linear_stages"]]
    ax.bar([0, 1], counts, color=[BLUE, "#78a7c7"], width=0.50)
    ax.axhline(13, color=TEAL, ls="--", lw=1.1)
    ax.axhline(12, color=AMBER, ls=":", lw=1.5)
    for i, value in enumerate(counts):
        ax.text(i, value + 0.14, str(value), ha="center", fontsize=12, fontweight="bold")
    ax.set_xticks([0, 1], ["PCHIP", "Linear"])
    ax.set_ylabel("Equilibrium stages")
    ax.set_ylim(0, 16)
    ax.set_yticks([0, 4, 8, 12, 13, 16])
    ax.text(
        0.04,
        0.95,
        "13-stage budget: both pass\n12-stage budget: interpolation-sensitive",
        transform=ax.transAxes,
        va="top",
        fontsize=8,
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.9),
    )
    heading(ax, "d", "Binary: numerical sensitivity matters")
    ax.text(
        0.5,
        -0.25,
        (
            "Fixed paper reflux and original 16-state grid\nStage budgets are d"
            "iagnostic test constraints"
        ),
        ha="center",
        transform=ax.transAxes,
        fontsize=8,
    )

    ax = axes[1, 1]
    boundary = bundles["extractive"]["paper_agreement"]["actual"]
    margins = np.array(
        [[100 * (r["purity"] - 0.995), 100 * (r["recovery"] - 0.98)] for r in boundary]
    )
    x = np.arange(2)
    for index, (margin_values, color) in enumerate(zip(margins, [RED, TEAL])):  # noqa: B905 -- Python 3.9
        positions = x + (index - 0.5) * 0.31
        ax.bar(
            positions,
            margin_values,
            width=0.28,
            color=color,
            label=f"N = {int(boundary[index]['stages'])}",
        )
        for xp, v in zip(positions, margin_values):  # noqa: B905 -- Python 3.9
            ax.annotate(
                f"{v:+.2e}",
                (xp, v),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=7,
                color="#222222" if v >= 0 else "white",
            )
    ax.set_yscale("symlog", linthresh=1e-5)
    ax.set_ylim(-9e-5, 0.06)
    ax.axhline(0, color="#444444", lw=0.8)
    ax.set_xticks(x, ["Ester purity", "Ester recovery"])
    ax.set_ylabel("Target margin (percentage points; symlog)")
    ax.legend(frameon=False, fontsize=8, loc="center", bbox_to_anchor=(0.57, 0.62))
    heading(ax, "e", "Extractive: nominal pass retains limits")
    ax.text(
        0.5,
        -0.25,
        (
            "183 stages pass; 182 stages narrowly miss\nSelected trajectory out"
            "side available experimental coverage"
        ),
        ha="center",
        transform=ax.transAxes,
        fontsize=7.7,
    )

    ax = axes[1, 2]
    observations = bundles["extraction"]["observations"]
    equal = [r["metrics"] for r in observations[:4]]
    allocation = [r["metrics"] for r in observations[4:]]
    all_metrics = equal + allocation
    xmin = min(79.5, min(100 * r["retention"] for r in all_metrics) - 0.3)
    xmax = max(100 * r["retention"] for r in all_metrics) + 0.6
    ymin = min(100 * r["recovery"] for r in all_metrics) - 1
    ymax = max(100 * r["recovery"] for r in all_metrics) + 2
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.fill_between([80, xmax], 70, ymax, color="#e1f1eb", zorder=0)
    ax.axvline(80, color=TEAL, ls="--", lw=1)
    ax.axhline(70, color=TEAL, ls="--", lw=1)
    for nstage, marker, color in [(2, "o", "#aab4bc"), (3, "^", "#78a7c7")]:
        points = [r for r in allocation if r["stages"] == nstage]
        ax.scatter(
            [100 * r["retention"] for r in points],
            [100 * r["recovery"] for r in points],
            marker=marker,
            s=20,
            color=color,
            label=f"{nstage}-stage allocations",
        )
    ax.plot(
        [100 * r["retention"] for r in equal],
        [100 * r["recovery"] for r in equal],
        "o-",
        color=BLUE,
        lw=1.1,
        ms=4,
        label="Equal solvent allocation",
    )
    for r in equal:
        ax.annotate(
            f"{int(r['stages'])}",
            (100 * r["retention"], 100 * r["recovery"]),
            xytext=(6, -10 if r["stages"] == 3 else 5),
            textcoords="offset points",
            fontsize=9,
        )
    selected = bundles["extraction"]["final"]
    ax.scatter(
        [100 * selected["retention"]],
        [100 * selected["recovery"]],
        marker="*",
        s=120,
        color=TEAL,
        zorder=5,
    )
    ax.set_xlabel("Initial heptane retained (%)")
    ax.set_ylabel("Benzene recovered (%)")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.legend(loc="lower left", fontsize=6.8, frameon=False)
    heading(ax, "f", "Crossflow: both targets must be met")
    ax.text(
        0.5,
        -0.25,
        "Three equal stages first meet both targets\nSame total solvent budget across candidates",
        ha="center",
        transform=ax.transAxes,
        fontsize=8,
    )
    for suffix in ("png", "svg", "pdf"):
        fig.savefig(figures / ("agent_main_figure." + suffix), dpi=350, bbox_inches="tight")
    plt.close(fig)
    failures = [
        dict(task=r["task_id"], repeat=r["repeat"], outcome=r["outcome"])
        for r in recovery
        if r["outcome"] != "recovered"
    ]
    failures += [
        dict(
            case=r["case"],
            condition=r["condition"],
            repeat=r["repeat"],
            assessment=r.get("assessment"),
        )
        for r in decisions
        if not r["passed"] or (r["condition"] == "validation_withheld" and not r["restored_passed"])
    ]
    summary = dict(
        routing=routing_rows,
        recovery=recovery_rows,
        evidence=evidence_rows,
        costs=cost_rows,
        failures=failures,
        source_physics_unchanged=True,
        new_thermodynamic_inference=False,
        evaluation_scope="development pilot; scripted responses and paired evidence interventions",
    )
    (directory / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            dict(
                recovery=sum(r["grounded_report"] for r in recovery_rows),
                recovery_total=27,
                evidence_correct=sum(r["passed"] for r in evidence_rows),
                evidence_decisions=36,
                api_calls=sum(r["api_calls"] for r in cost_rows),
                tokens=sum(r["total_tokens"] for r in cost_rows),
            ),
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    make_report(parser.parse_args().input)


if __name__ == "__main__":
    main()
