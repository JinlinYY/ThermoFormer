"""Build an Agent-only publication figure from frozen, auditable run records.

This is a presentation revision, not an experiment or thermodynamic calculation.
All source records remain read-only. Python 3.9 is supported.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle
from matplotlib.transforms import Bbox

CASES = ("binary", "extractive", "extraction")
NAMES = ("Binary", "Extractive", "Crossflow")
INK = "#20272C"
MUTED = "#54616B"
LINE = "#C8D1D6"
BLUE = "#0072B2"
TEAL = "#00846C"
GOLD = "#AE7600"
PURPLE = "#77518D"
PALE_BLUE = "#EEF5F9"
PALE_TEAL = "#EAF5F1"
PALE_GOLD = "#FCF3DC"
PALE_PURPLE = "#F2ECF6"
WIDTH, HEIGHT = 180.0, 110.0
FONT_INCREASE = 0.8
METRICS = (
    "parse_correct",
    "plan_correct",
    "tool_execution_correct",
    "result_consistent",
    "report_grounded",
)
ACTION_LABELS = {
    "report_preliminary": "P",
    "request_verification": "V",
    "withhold_target_claim": "H",
}


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def records(directory: Path) -> list[dict[str, Any]]:
    return [dict(read(p), record_file=p.name) for p in sorted(directory.glob("*.json"))]


def collect(reliability: Path, experiment: Path) -> dict[str, Any]:
    """Recompute every plotted count from complete frozen records."""
    manifest = read(experiment / "manifest.json")
    if Path(manifest["source"]).resolve() != reliability.resolve():
        raise ValueError("The requested reliability source differs from the experiment source")
    for relative, expected in manifest["source_hashes"].items():
        if sha(reliability / relative) != expected:
            raise ValueError("Modified source: " + relative)
    if not read(experiment / "integrity.json")["source_and_code_unchanged"]:
        raise ValueError("Experiment integrity failed")
    if not read(experiment / "audit.json")["passed"]:
        raise ValueError("Experiment audit failed")
    runs = records(reliability / "runs")
    recovery = records(experiment / "recovery")
    decisions = records(experiment / "decisions")
    if (len(runs), len(recovery), len(decisions)) != (72, 27, 27):
        raise ValueError("Only a complete study can be plotted")
    traces = []
    equivalence = []
    for case in CASES:
        candidates = [r for r in runs if r["case"] == case and r["kind"] == "equivalent"]
        run = min(candidates, key=lambda r: (r.get("cache_hit", True), r["repeat"], r["task_id"]))
        if run["outcome"] != "reported" or not all(run["metrics"][m] for m in METRICS):
            raise ValueError("The selected representative trace did not pass")
        traces.append(
            dict(
                case=case,
                task_id=run["task_id"],
                repeat=run["repeat"],
                record_file=run["record_file"],
                cache_hit=run["cache_hit"],
                plan="; ".join(run["parsed"]["plan"]),
                supported_claims=len(run["report_audit"]["supported_claims"]),
                unsupported_claims=len(run["report_audit"]["unsupported_claims"]),
                disposition=run["raw_report"]["disposition"],
                limits_retained=run["trace"][-1]["limits_retained"],
            )
        )
        for variant in range(5):
            group = [r for r in candidates if r["task_id"] == f"{case}-equivalent-{variant}"]
            if len(group) != 3:
                raise ValueError("Missing equivalent-request repetitions")
            equivalence.append(
                dict(case=case, variant=variant, passed=sum(all(r["metrics"][m] for m in METRICS) for r in group), n=3)
            )
    replay = read(experiment / "paired_routing_replay.json")
    gates = []
    for kind in ("missing", "conflict", "ambiguous"):
        group = [r for r in replay if r["kind"] == kind]
        gates.append(
            dict(
                kind=kind,
                n=len(group),
                schema_blocked=sum(not r["schema_only_ready"] for r in group),
                contract_blocked=sum(not r["contract_ready"] for r in group),
            )
        )
    recovered = []
    for case in CASES:
        group = [r for r in recovery if r["case"] == case]
        recovered.append(
            dict(
                case=case,
                n=len(group),
                resolved=sum(r["parsed_correct"] for r in group),
                reused=sum(r["executed"] and r["cache_hit"] and r["result_preserved"] for r in group),
                reported=sum(r["report_grounded"] for r in group),
            )
        )
    actions = []
    for case in CASES:
        for condition in ("complete", "validation_withheld", "constraint_not_met", "validation_restored"):
            restored = condition == "validation_restored"
            original_condition = "validation_withheld" if restored else condition
            group = [r for r in decisions if r["case"] == case and r["condition"] == original_condition]
            labels = [
                ACTION_LABELS.get(r["restored_decision" if restored else "decision"]["action"], "?") for r in group
            ]
            actions.append(
                dict(
                    case=case,
                    condition=condition,
                    n=len(group),
                    passed=sum(r["restored_passed" if restored else "passed"] for r in group),
                    actions="/".join(labels),
                )
            )
    costs = []
    for kind, group in (("Recovery", recovery), ("Decision", decisions)):
        for run in group:
            costs.append(
                dict(
                    experiment=kind,
                    case=run["case"],
                    record_file=run["record_file"],
                    task=run.get("task_id", run.get("condition")),
                    repeat=run["repeat"],
                    tokens=run["tokens"],
                    api_calls=len(run["llm_calls"]),
                    elapsed_s=run["elapsed_s"],
                )
            )
    return dict(traces=traces, equivalence=equivalence, gates=gates, recovery=recovered, actions=actions, costs=costs)


class Canvas:
    """Place vector annotations in physical millimetres, measured from the top."""

    def __init__(self) -> None:
        self.fig = plt.figure(figsize=(WIDTH / 25.4, HEIGHT / 25.4), dpi=200)
        self.ax = self.fig.add_axes((0, 0, 1, 1))
        self.ax.set(xlim=(0, WIDTH), ylim=(HEIGHT, 0))
        self.ax.axis("off")
        self.fitted: list[tuple[Any, float, float, float, float]] = []

    def text(self, x: float, y: float, value: str, size: float = 6.4, **kwargs: Any) -> Any:
        return self.ax.text(x, y, value, fontsize=size + FONT_INCREASE, va="center", color=INK, **kwargs)

    def panel(self, x: float, y: float, letter: str, title: str) -> None:
        self.text(x, y, letter, 8.0, fontweight="bold")
        self.text(x + 4.4, y, title, 7.0)

    def line(self, x0: float, y0: float, x1: float, y1: float, color: str = LINE, lw: float = 0.5) -> None:
        self.ax.plot([x0, x1], [y0, y1], color=color, lw=lw, clip_on=False)

    def box(self, x: float, y: float, w: float, h: float, label: str, fill: str, size: float = 6.0) -> None:
        self.ax.add_patch(Rectangle((x, y), w, h, facecolor=fill, edgecolor="none"))
        artist = self.text(x + w / 2, y + h / 2, label, size, ha="center", linespacing=1.4)
        self.fitted.append((artist, x + 0.7, y + 0.5, w - 1.4, h - 1.0))

    def arrow(self, x0: float, y0: float, x1: float, y1: float, **kwargs: Any) -> None:
        self.ax.add_patch(
            FancyArrowPatch(
                (x0, y0),
                (x1, y1),
                arrowstyle="->",
                mutation_scale=5,
                lw=0.6,
                color=MUTED,
                shrinkA=0,
                shrinkB=0,
                **kwargs,
            )
        )

    def axes(self, x: float, y: float, w: float, h: float) -> Any:
        return self.fig.add_axes((x / WIDTH, 1 - (y + h) / HEIGHT, w / WIDTH, h / HEIGHT))

    def check_fit(self) -> list[str]:
        self.fig.canvas.draw()
        assert isinstance(self.fig.canvas, FigureCanvasAgg)
        renderer = self.fig.canvas.get_renderer()  # type: ignore[no-untyped-call]  # Matplotlib lacks a stub here.
        issues = []
        for artist, x, y, w, h in self.fitted:
            area = artist.get_window_extent(renderer).transformed(self.ax.transData.inverted())
            x0, x1 = sorted((area.x0, area.x1))
            y0, y1 = sorted((area.y0, area.y1))
            if x0 < x or x1 > x + w or y0 < y or y1 > y + h:
                issues.append(artist.get_text())
        return issues


def checkmark(c: Canvas, x: float, y: float, scale: float = 1.0) -> None:
    """A numerical-check status symbol, not a physical-certification badge."""
    c.ax.plot(
        [x - 0.8 * scale, x - 0.15 * scale, x + 1.15 * scale],
        [y, y + 0.65 * scale, y - 0.85 * scale],
        color=TEAL,
        lw=0.85,
        solid_capstyle="round",
        solid_joinstyle="round",
    )


def limit_symbol(c: Canvas, x: float, y: float, scale: float = 1.0) -> None:
    c.ax.add_patch(
        Polygon(
            [(x, y - 1.45 * scale), (x - 1.4 * scale, y + 1.1 * scale), (x + 1.4 * scale, y + 1.1 * scale)],
            facecolor=PALE_GOLD,
            edgecolor=GOLD,
            lw=0.6,
        )
    )
    c.line(x, y - 0.55 * scale, x, y + 0.1 * scale, color=INK, lw=0.6)
    c.ax.add_patch(Circle((x, y + 0.6 * scale), 0.12 * scale, color=INK))


def document(c: Canvas, x: float, y: float, w: float, h: float, fold_color: str = PALE_BLUE) -> None:
    """Draw an editable document outline with a folded corner."""
    fold = 1.6
    c.ax.add_patch(
        Polygon(
            [(x, y), (x + w - fold, y), (x + w, y + fold), (x + w, y + h), (x, y + h)],
            facecolor="white",
            edgecolor=BLUE,
            lw=0.65,
        )
    )
    c.ax.add_patch(
        Polygon(
            [(x + w - fold, y), (x + w - fold, y + fold), (x + w, y + fold)],
            facecolor=fold_color,
            edgecolor=BLUE,
            lw=0.55,
        )
    )


def contract_glyph(c: Canvas, x: float, y: float) -> None:
    document(c, x - 4.0, y - 3.9, 8.0, 7.8)
    for offset in (-1.5, 0.6, 2.6):
        checkmark(c, x - 2.0, y + offset, 0.65)
        c.line(x - 0.1, y + offset, x + 2.5, y + offset, color=MUTED, lw=0.6)


def plan_glyph(c: Canvas, x: float, y: float, protocol: str) -> None:
    for center, label in ((x - 7.5, protocol), (x + 7.5, "Audit")):
        c.ax.add_patch(Rectangle((center - 5, y - 2.5), 10, 5, facecolor="white", edgecolor=BLUE, lw=0.65))
        artist = c.text(center, y, label, 5.6, ha="center")
        c.fitted.append((artist, center - 4.7, y - 2.1, 9.4, 4.2))
    c.arrow(x - 2.3, y, x + 2.3, y)


def execution_glyph(c: Canvas, x: float, y: float) -> None:
    # The processor denotes the thermodynamic engine, and the sheet its returned
    # numerical artifact. No prediction curves or invented numerical data are drawn.
    chip = x - 4.4
    c.ax.add_patch(Rectangle((chip - 3.1, y - 3.1), 6.2, 6.2, facecolor=PALE_BLUE, edgecolor=BLUE, lw=0.7))
    for offset in (-1.8, 0.0, 1.8):
        c.line(chip + offset, y - 4.1, chip + offset, y - 3.1, color=BLUE, lw=0.65)
        c.line(chip + offset, y + 3.1, chip + offset, y + 4.1, color=BLUE, lw=0.65)
        c.line(chip - 4.1, y + offset, chip - 3.1, y + offset, color=BLUE, lw=0.65)
        c.line(chip + 3.1, y + offset, chip + 4.1, y + offset, color=BLUE, lw=0.65)
    c.text(chip, y, "TF", 6.0, ha="center")
    c.arrow(x + 0.1, y, x + 3.3, y)
    document(c, x + 3.6, y - 3.4, 5.4, 6.8)
    for offset in (-0.8, 0.7, 2.2):
        c.line(x + 4.6, y + offset, x + 7.8, y + offset, color=MUTED, lw=0.5)


def review_glyph(c: Canvas, x: float, y: float) -> None:
    checkmark(c, x - 8.5, y - 1.8, 1.0)
    c.text(x - 5.6, y - 1.8, "Checks", 5.8)
    limit_symbol(c, x - 8.5, y + 2.0, 0.85)
    c.text(x - 5.6, y + 2.0, "Scope", 5.8)


def report_glyph(c: Canvas, x: float, y: float, claim_count: int) -> None:
    document(c, x + 1.0, y - 4.2, 7.5, 8.4, PALE_GOLD)
    for offset in np.linspace(-2.7, 2.7, claim_count):
        c.ax.add_patch(Circle((x - 6.0, y + offset), 0.55, facecolor=PALE_TEAL, edgecolor=TEAL, lw=0.65))
        c.line(x - 5.3, y + offset, x + 0.6, y + offset, color=TEAL, lw=0.5)
        c.line(x + 2.2, y + offset, x + 6.2, y + offset, color=MUTED, lw=0.55)
    limit_symbol(c, x + 9.5, y + 3.4, 0.75)


def draw_trajectories(c: Canvas, traces: list[dict[str, Any]]) -> None:
    """Compress recorded events into functional glyphs with case-specific labels."""
    c.panel(2, 3, "a", "Recorded executions across three separation tasks")
    starts = [23.0, 54.0, 85.0, 116.0, 147.0]
    headers = ["Request contract", "Tool plan", "Numerical tools", "Evidence review", "Report"]
    for x, header in zip(starts, headers):  # noqa: B905 -- Python 3.9
        c.text(x + 14.5, 9.6, header, 6.4, ha="center")
    labels = ["Binary\ndistillation", "Extractive\ndistillation", "Crossflow\nextraction"]
    tool_labels = ["VLE", "Column", "LLE"]
    plan_labels = ["Stages / sensitivity", "Boundary / coverage", "Cascade / dual target"]
    scope_labels = ["Interpolation limit", "Coverage limit", "Search limit"]
    for i, trace in enumerate(traces):
        top = 14.0 + 13.4 * i
        cy = top + 4.0
        c.text(2, top + 5.7, labels[i], 6.4, linespacing=1.3)
        for j, x in enumerate(starts):
            c.ax.add_patch(
                Rectangle(
                    (x, top - 0.5), 29, 12.8, facecolor=PALE_TEAL if j == 4 else "#F6F9FB", edgecolor="none", zorder=-1
                )
            )
            if j < 4:
                c.arrow(x + 29.05, cy, x + 30.95, cy)
        contract_glyph(c, starts[0] + 14.5, cy)
        plan_glyph(c, starts[1] + 14.5, cy, tool_labels[i])
        execution_glyph(c, starts[2] + 14.5, cy)
        review_glyph(c, starts[3] + 14.5, cy)
        report_glyph(c, starts[4] + 14.5, cy, trace["supported_claims"])
        captions = [
            "Units / IDs / fields",
            plan_labels[i],
            "Cached result" if trace["cache_hit"] else "Fresh calculation",
            scope_labels[i],
            f"{trace['supported_claims']} linked claims",
        ]
        for x, caption in zip(starts, captions):  # noqa: B905 -- Python 3.9
            artist = c.text(x + 14.5, top + 10.0, caption, 5.8, ha="center")
            c.fitted.append((artist, x + 0.3, top + 8.7, 28.4, 2.7))
    checkmark(c, 24, 57, 0.8)
    c.text(27, 57, "Checks passed", 5.8)
    limit_symbol(c, 62, 57, 0.8)
    c.text(65, 57, "Limits retained", 5.8)
    c.text(94, 57, "TF: ThermoFormer; one fresh run per case", 5.8)


def draw_compact_results(c: Canvas, data: dict[str, Any]) -> None:
    """Five result panels in one row, with transposed matrices where helpful."""
    c.panel(2, 62.5, "b", "Equivalent inputs")
    bcols = [17.5, 24.5, 31.5]
    for x, name in zip(bcols, ("B", "E", "X")):  # noqa: B905 -- Python 3.9
        c.text(x, 69.0, name, 5.8, ha="center")
    for variant, name in enumerate(("Base", "English", "Units", "Order", "Mixed")):
        y = 74.0 + 4.6 * variant
        c.text(2, y, name, 5.4)
        for x, case in zip(bcols, CASES):  # noqa: B905 -- Python 3.9
            row = next(r for r in data["equivalence"] if r["case"] == case and r["variant"] == variant)
            c.box(x - 3, y - 2.1, 6, 4.2, f"{row['passed']}/{row['n']}", PALE_BLUE, 5.4)
    total = sum(r["n"] for r in data["equivalence"])
    passed = sum(r["passed"] for r in data["equivalence"])
    c.text(2, 102.0, f"{passed}/{total} end-to-end", 5.4)

    c.panel(39, 62.5, "c", "Input safeguards")
    c.ax.plot(40.0, 69.0, "o", ms=2.8, mfc="white", mec=MUTED, mew=0.65)
    c.text(42.1, 69.0, "Schema", 5.3)
    c.ax.plot(55.7, 69.0, "s", ms=2.8, color=TEAL)
    c.text(58.0, 69.0, "Contract", 5.3)
    ax = c.axes(48.5, 75.0, 21, 19.5)
    for i, row in enumerate(data["gates"]):
        schema = row["schema_blocked"] / row["n"]
        contract = row["contract_blocked"] / row["n"]
        ax.plot([schema, contract], [i, i], color=LINE, lw=1.0, zorder=1)
        ax.scatter([schema], [i], s=13, facecolor="white", edgecolor=MUTED, lw=0.65, zorder=3)
        ax.scatter([contract], [i], s=14, marker="s", color=TEAL, zorder=3)
        for x, count, offset, alignment in (
            (schema, row["schema_blocked"], -2, "right"),
            (contract, row["contract_blocked"], 2, "left"),
        ):
            ax.annotate(
                f"{count}/{row['n']}",
                (x, i),
                xytext=(offset, 4.5),
                textcoords="offset points",
                ha=alignment,
                fontsize=6.0,
            )
    ax.set(
        xlim=(-0.15, 1.28),
        ylim=(2.4, -0.65),
        yticks=[0, 1, 2],
        yticklabels=["Missing", "Conflict", "Basis"],
        xticks=[0, 1],
        xticklabels=["0", "100"],
    )
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=1.8, labelsize=6.0)
    ax.tick_params(axis="x", labelsize=6.0, pad=1)
    ax.set_xlabel("Blocked (%)", fontsize=6.2, labelpad=1)
    c.text(40, 102.0, "Paired output replay", 5.4)

    c.panel(76, 62.5, "d", "Recovery")
    dcols = [83.0, 91.5, 100.0]
    for x, name in zip(dcols, ("Task", "Cache", "Report")):  # noqa: B905 -- Python 3.9
        c.text(x, 69.0, name, 5.3, ha="center")
    for i, row in enumerate(data["recovery"]):
        y = 76.0 + 8.2 * i
        c.text(76, y, ("B", "E", "X")[i], 5.8)
        c.line(86.3, y, 88.2, y, lw=0.6)
        c.line(94.8, y, 96.7, y, lw=0.6)
        for x, field in zip(dcols, ("resolved", "reused", "reported")):  # noqa: B905 -- Python 3.9
            c.box(x - 3.3, y - 2.3, 6.6, 4.6, f"{row[field]}/{row['n']}", PALE_TEAL, 5.6)
    c.text(76, 98.3, "One scripted correction", 5.2)
    c.text(76, 102.0, "Validated cache reused", 5.2)

    c.panel(110, 62.5, "e", "Evidence decisions")
    ecols = [127.0, 134.5, 142.0]
    for x, name in zip(ecols, ("B", "E", "X")):  # noqa: B905 -- Python 3.9
        c.text(x, 69.0, name, 5.8, ha="center")
    conditions = ("complete", "validation_withheld", "constraint_not_met", "validation_restored")
    names = ("Full", "Withheld", "Unmet", "Restored*")
    for j, (condition, name) in enumerate(zip(conditions, names)):  # noqa: B905 -- Python 3.9
        y = 74.8 + 6.6 * j
        c.text(110, y, name, 5.3)
        for x, case in zip(ecols, CASES):  # noqa: B905 -- Python 3.9
            row = next(r for r in data["actions"] if r["case"] == case and r["condition"] == condition)
            actions = row["actions"].split("/")
            letter = actions[0] if len(set(actions)) == 1 else "?"
            fill = {"P": PALE_TEAL, "V": PALE_GOLD, "H": PALE_PURPLE}.get(letter, "#F8E7E5")
            c.box(x - 3.4, y - 2.5, 6.8, 5.0, f"{letter} {row['passed']}/{row['n']}", fill, 5.2)
    c.line(110, 91.0, 145.4, 91.0, color=MUTED, lw=0.45)
    c.text(110, 102.0, "*After verification", 5.4)

    c.panel(150, 62.5, "f", "Token cost")
    c.text(154, 69.0, "Tokens per run (10³)", 5.4)
    ax = c.axes(155, 73.5, 22, 21.0)
    for j, (kind, color, marker) in enumerate((("Recovery", BLUE, "o"), ("Decision", TEAL, "s"))):
        values = [r["tokens"] / 1000 for r in data["costs"] if r["experiment"] == kind]
        offsets = np.array([-0.17, -0.07, 0.04, 0.14, -0.12, 0.0, 0.10, -0.03, 0.19] * 3)
        ax.scatter(
            j + offsets, values, s=6, marker=marker, facecolor="none", edgecolor=color, lw=0.5, alpha=0.75, zorder=3
        )
        med = float(np.median(values))
        ax.plot([j - 0.28, j + 0.28], [med, med], color=INK, lw=0.9, zorder=4)
    ax.set(xlim=(-0.5, 1.5), ylim=(0, 6.3), xticks=[0, 1], xticklabels=["Rec.", "Dec."], yticks=[0, 3, 6])
    ax.tick_params(labelsize=6.1, pad=1.2)
    c.text(150, 102.0, "27 runs/group; median line", 5.2)

    c.text(2, 107.3, "B: binary; E: extractive; X: crossflow", 5.4)
    c.text(57, 107.3, "P: report with limits; V: verify; H: withhold target claim", 5.4)
    c.text(139, 107.3, "Rec.: recovery; Dec.: decision", 5.2)


def draw(data: dict[str, Any], out: Path) -> dict[str, Any]:
    # Arial is available in the Windows authoring environment; fail rather than
    # silently changing typography and risking layout overflow.
    font_manager.findfont("Arial", fallback_to_default=False)
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 7.2,
            "font.weight": "normal",
            "axes.titleweight": "normal",
            "axes.labelweight": "normal",
            "text.color": INK,
            "axes.labelcolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.6,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.major.size": 2.5,
            "ytick.major.size": 2.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "svg.hashsalt": "agent-publication-figure-v5",
        }
    )
    c = Canvas()
    draw_trajectories(c, data["traces"])

    draw_compact_results(c, data)

    overflow = c.check_fit()
    if overflow:
        raise ValueError("Text exceeds its allocated cell: " + repr(overflow))
    out.mkdir(parents=True, exist_ok=True)
    for suffix in ("pdf", "svg", "png"):
        c.fig.savefig(out / ("agent_main_figure." + suffix), dpi=600, facecolor="white")
    c.fig.savefig(
        out / "panel_a.png",
        dpi=600,
        facecolor="white",
        bbox_inches=Bbox.from_extents(0, (HEIGHT - 59) / 25.4, WIDTH / 25.4, HEIGHT / 25.4),
    )
    plt.close(c.fig)
    return dict(
        width_mm=WIDTH,
        height_mm=HEIGHT,
        font="Arial",
        body_font_pt=[6.0, 7.8],
        panel_label_pt=8.8,
        bold_text="Panel letters a-f only",
        full_width_dividers=False,
        vector_formats=["pdf", "svg"],
        preview_dpi=600,
        text_cell_overflows=overflow,
        physical_results_replotted=False,
        panel_a_style="Functional vector glyphs for contracts, tools, evidence checks and linked claims",
        result_panel_layout="Panels b-f on a single row; b and e matrices transposed",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reliability", type=Path, required=True)
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = collect(args.reliability, args.experiment)
    args.output.mkdir(parents=True, exist_ok=True)
    source_data = args.output / "source_data"
    source_data.mkdir(exist_ok=True)
    for key, rows in data.items():
        dump_csv(source_data / (key + ".csv"), rows)
    qa = draw(data, args.output / "figures")
    manifest = dict(
        reliability_source=str(args.reliability.resolve()),
        experiment_source=str(args.experiment.resolve()),
        builder=str(Path(__file__).resolve()),
        builder_sha256=sha(Path(__file__)),
        qa=qa,
        input_sha256={
            str(p.resolve()): sha(p)
            for parent in (args.reliability, args.experiment)
            for p in sorted(parent.rglob("*.json"))
        },
        scope="Presentation revision only; no new API calls, process calculations or inferred numerical data.",
    )
    (args.output / "figure_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(qa, indent=2))


if __name__ == "__main__":
    main()
