from pathlib import Path
import csv
import json
import sys
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

CASE = Path(__file__).resolve().parent
OUT = CASE / "figures"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(CASE.parents[1]))
import binary as d  # noqa: E402


def read(path):
    with path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


points = read(CASE / "data/equilibrium.csv")
scans = read(CASE / "results/reflux_sensitivity.csv")
meta = json.loads((CASE / "results/design.json").read_text())
R = meta["specification"]["common_reflux_ratio"]
series = [
    ("Experimental interpolation", "Experiment", "y_exp", "#344E64", "o"),
    ("ThermoFormer", "ThermoFormer", "thermoformer_y", "#B5674D", "s"),
    ("UNIFAC", "UNIFAC", "unifac_y", "#467E78", "^"),
]
x = np.array([float(p["x_heptane"]) for p in points])
grid = np.linspace(0, 1, 801)
FONT_SIZE = 9.0
plt.rcParams.update(
    {
        "font.family": "Arial",
        "font.size": FONT_SIZE,
        "axes.labelsize": FONT_SIZE,
        "axes.titlesize": FONT_SIZE,
        "xtick.labelsize": FONT_SIZE,
        "ytick.labelsize": FONT_SIZE,
        "legend.fontsize": FONT_SIZE,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "axes.linewidth": 0.7,
    }
)
fig = plt.figure(figsize=(175 / 25.4, 225 / 25.4), facecolor="white")
fig.text(
    0.5,
    0.983,
    r"$n$-Heptane / $n$-nonane: equilibrium and distillation",
    ha="center",
    weight="bold",
)
fig.text(
    0.5,
    0.962,
    r"$P$ = 101.3 kPa  |  $q$ = 1  |  $z_F$ = 0.466  |  $x_D$ = 0.995  |  Recovery = 98%",
    ha="center",
)


def panel(bounds, letter, title, chart=True):
    ax = fig.add_axes(bounds)
    ax.text(0, 1.07, letter, transform=ax.transAxes, weight="bold", va="bottom")
    ax.text(0.08, 1.07, title, transform=ax.transAxes, weight="bold", va="bottom")
    if chart:
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(length=2.5, pad=2)
    else:
        ax.axis("off")
    return ax


def table(ax, headers, rows, widths, bbox=(0, 0, 1, 0.94)):
    t = ax.table(
        cellText=rows, colLabels=headers, colWidths=widths, cellLoc="center", bbox=bbox
    )
    t.auto_set_font_size(False)
    t.set_fontsize(FONT_SIZE)
    for (r, c), cell in t.get_celld().items():
        cell.set_edgecolor("white")
        cell.set_linewidth(0.6)
        cell.set_facecolor("#E9EEF1" if r == 0 else ("#F4F6F7" if r % 2 else "white"))
        if r == 0:
            cell.set_text_props(weight="bold")
        if c == 0:
            cell.set_text_props(ha="left")
            cell.PAD = 0.035
    return t


ax = panel([0.085, 0.758, 0.285, 0.173], "a", "VLE reference and predictions")
curves = {}
for source, title, col, color, marker in series:
    y = np.array([float(p[col]) for p in points])
    eq = d.curve(x, y, "pchip")
    curves[source] = eq
    ax.plot(grid, eq(grid), color=color, lw=1.05)
    ax.plot(x, y, ls="none", marker=marker, ms=2.7, mfc="white", mec=color, mew=0.65)
ax.plot([0, 1], [0, 1], color="#A5AAAF", ls=":", lw=0.7)
ax.set(
    xlim=(0, 1),
    ylim=(0, 1),
    xlabel="Liquid mole fraction, $x$",
    ylabel="Vapor mole fraction, $y$",
)
ax.set_xticks([0, 0.5, 1])
ax.set_yticks([0, 0.5, 1])
ax = panel([0.435, 0.743, 0.535, 0.188], "b", "VLE prediction errors", False)
metrics = []
for pred in ["thermoformer", "unifac"]:
    ey = np.array([float(p[pred + "_y"]) - float(p["y_exp"]) for p in points])
    et = np.array([float(p[pred + "_T_K"]) - float(p["T_exp_K"]) for p in points])
    metrics.append(
        [
            f"{abs(ey).mean():.6f}",
            f"{np.sqrt((ey**2).mean()):.6f}",
            f"{abs(ey).max():.6f}",
            f"{abs(et).mean():.4f}",
            f"{np.sqrt((et**2).mean()):.4f}",
            f"{abs(ey[1:-1]).mean():.6f}",
            f"{abs(et[1:-1]).mean():.4f}",
        ]
    )
labels = [
    "Vapor-composition MAE",
    "Vapor-composition RMSE",
    "Maximum composition error",
    "Temperature MAE (K)",
    "Temperature RMSE (K)",
    "Composition MAE, mixtures",
    "Temperature MAE, mixtures (K)",
]
table(
    ax,
    ["Metric", "ThermoFormer", "UNIFAC"],
    [[s, metrics[0][i], metrics[1][i]] for i, s in enumerate(labels)],
    [0.54, 0.25, 0.21],
    bbox=(0, 0.07, 1, 0.91),
)
ax.text(
    0,
    0,
    "Rows 1-5: all 16 states; rows 6-7: 14 mixture states.\nComposition errors are dimensionless.",
    va="top",
)
ax = panel([0.04, 0.566, 0.45, 0.125], "c", "Common material balance", False)
rows = [
    ["Feed", "1.000000", "0.466000", "0.466000", "0.534000"],
    ["Distillate", "0.458975", "0.995000", "0.456680", "0.002295"],
    ["Bottoms", "0.541025", "0.017227", "0.009320", "0.531705"],
]
table(
    ax,
    ["Stream", "Total\nflow", "$x_{C7}$", "$C_7$\nflow", "$C_9$\nflow"],
    rows,
    [0.20, 0.20, 0.20, 0.20, 0.20],
    bbox=(0, 0.22, 1, 0.76),
)
ax.text(0, 0.045, r"Flows: mol s$^{-1}$; $C_7$: $n$-heptane; $C_9$: $n$-nonane.")
ax = panel(
    [0.525, 0.558, 0.445, 0.133], "d", "Design and interpolation sensitivity", False
)
rows = []
for source, title, *_ in [series[1], series[0], series[2]]:
    for kind in ["pchip", "linear"]:
        r = next(
            v
            for v in meta["results"]
            if v["source"] == source and v["interpolation"] == kind
        )
        rows.append(
            [
                title,
                "PCHIP" if kind == "pchip" else "Linear",
                f"{r['minimum_reflux_ratio']:.6f}",
                str(r["integer_equilibrium_stages_including_reboiler"]),
                str(r["feed_stage_from_top"]),
            ]
        )
table(
    ax,
    ["Source", "Interp.", "$R_{min}$", "$N$", "Feed"],
    rows,
    [0.31, 0.20, 0.23, 0.11, 0.15],
)
fig.text(
    0.5,
    0.536,
    r"Common reflux ratio: $R$ = 0.928052  |  $N$ includes the equilibrium reboiler and excludes the total condenser.",
    ha="center",
)
for i, (source, title, col, color, marker) in enumerate(series):
    ax = panel([0.085 + i * 0.31, 0.299, 0.264, 0.199], "efg"[i], title)
    eq = curves[source]
    calc = d.stages(eq, R)
    archive = next(
        r
        for r in meta["results"]
        if r["source"] == source and r["interpolation"] == "pchip"
    )
    assert (
        calc["integer_equilibrium_stages_including_reboiler"]
        == archive["integer_equilibrium_stages_including_reboiler"]
    )
    assert calc["feed_stage_from_top"] == archive["feed_stage_from_top"]
    path = np.array(calc["path"])
    ax.plot(grid, eq(grid), color=color, lw=1)
    ax.plot(
        x,
        [float(p[col]) for p in points],
        ls="none",
        marker=marker,
        ms=2.5,
        mfc="white",
        mec=color,
        mew=0.6,
    )
    ax.plot(grid, grid, color="#ACB0B4", ls=":", lw=0.6)
    a = np.linspace(d.Z, d.XD, 100)
    b = np.linspace(d.XB, d.Z, 100)
    ax.plot(
        a,
        (R * d.D * a + d.D * d.XD) / ((R + 1) * d.D),
        color="#747D85",
        ls="--",
        lw=0.8,
    )
    ax.plot(
        b,
        ((R * d.D + d.F) * b - d.B * d.XB) / ((R + 1) * d.D),
        color="#747D85",
        ls="--",
        lw=0.8,
    )
    ax.axvline(d.Z, color="#8D959C", ls=":", lw=0.7)
    ax.plot(path[:, 0], path[:, 1], color="#24282C", lw=0.8)
    ax.set(xlim=(0, 1), ylim=(0, 1), xlabel="Liquid mole fraction, $x$")
    ax.set_xticks([0, 0.5, 1])
    ax.set_yticks([0, 0.5, 1])
    if i == 0:
        ax.set_ylabel("Vapor mole fraction, $y$")
    ax.text(
        0.96,
        0.07,
        f"{calc['integer_equilibrium_stages_including_reboiler']} stages\nFeed stage {calc['feed_stage_from_top']}",
        transform=ax.transAxes,
        ha="right",
        bbox=dict(fc="white", ec="none", pad=1),
    )
handles = [
    Line2D([], [], color="#24282C", lw=0.9, label="Stage stepping"),
    Line2D([], [], color="#747D85", lw=0.8, ls="--", label="Operating lines"),
    Line2D([], [], color="#8D959C", ls=":", lw=0.8, label="$q$-line"),
]
fig.legend(
    handles=handles, loc="center", bbox_to_anchor=(0.52, 0.251), ncol=3, frameon=False
)
for i, kind in enumerate(["pchip", "linear"]):
    ax = panel(
        [0.085 + i * 0.48, 0.071, 0.40, 0.139],
        "hi"[i],
        "Reflux sensitivity: " + ("PCHIP" if i == 0 else "linear"),
    )
    for source, title, col, color, marker in series:
        rows = [
            r for r in scans if r["source"] == source and r["interpolation"] == kind
        ]
        assert len(rows) == 39
        ax.plot(
            [float(r["reflux_ratio"]) for r in rows],
            [int(r["equilibrium_stages"]) for r in rows],
            color=color,
            marker=marker,
            ms=2.5,
            mfc="white",
            mew=0.6,
            lw=0.9,
        )
    ax.axvline(R, color="#8D959C", ls=":", lw=0.8)
    ax.set(xlabel="Reflux ratio, $R$", ylim=(7.5, 18.5))
    ax.set_xticks([0.7, 1, 1.3, 1.6, 1.9])
    ax.set_yticks([8, 10, 12, 14, 16, 18])
    if i == 0:
        ax.set_ylabel("Equilibrium stages, $N$")
    ax.text(R + 0.025, 17.2, "Design $R$", color="#6D7379")
fig.legend(
    handles=[
        Line2D([], [], color=c, marker=m, mfc="white", ms=3, lw=1, label=t)
        for s, t, col, c, m in series
    ],
    loc="center",
    bbox_to_anchor=(0.52, 0.019),
    ncol=3,
    frameon=False,
)
for ext in ["pdf", "svg", "png"]:
    fig.savefig(OUT / f"binary_distillation_summary.{ext}", dpi=450)
print(
    "Saved 175 x 225 mm composite; 6 design rows, 3 stepping profiles, and 234 scan records checked."
)
