from pathlib import Path
import json
import csv
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text
from matplotlib.transforms import Bbox

CASE = Path(__file__).resolve().parent
OUT = CASE / "figures"
OUT.mkdir(exist_ok=True)
DATA = CASE / "data"


def load(stem):
    return json.loads((DATA / (stem + ".json")).read_text(encoding="utf-8"))


with (DATA / "equilibrium.csv").open(encoding="utf-8-sig") as f:
    points = list(csv.DictReader(f))
tf = load("thermoformer_183")
uni = load("unifac_183")
below = load("thermoformer_182")
assert len(points) == 17 and tf["N"] == uni["N"] == 183 and below["N"] == 182
assert all(r["success"] for r in [tf, uni, below])
assert tf["xD"][1] >= 0.995 and tf["recovery"] >= 0.98
assert below["xD"][1] < 0.995 and below["recovery"] < 0.98
FONT = 10.5
plt.rcParams.update(
    {
        "font.family": "Arial",
        "font.size": FONT,
        "axes.labelsize": FONT,
        "axes.titlesize": FONT,
        "xtick.labelsize": FONT,
        "ytick.labelsize": FONT,
        "legend.fontsize": FONT,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "axes.linewidth": 0.65,
    }
)
colors = {"Experiment": "#344E64", "ThermoFormer": "#B5674D", "UNIFAC": "#467E78"}
fig = plt.figure(figsize=(200 / 25.4, 285 / 25.4), facecolor="white")
fig.text(
    0.5,
    0.985,
    "Extractive distillation: sec-butyl alcohol / sec-butyl acetate / DMF",
    ha="center",
    weight="bold",
)
fig.text(
    0.5,
    0.968,
    "101.3 kPa  |  17 ternary VLE states  |  Equimolar alcohol-ester feed: 1 mol s$^{-1}$",
    ha="center",
)
fig.legend(
    handles=[
        Line2D([], [], color=c, marker=m, mfc="white", ms=3, lw=1, label=s)
        for (s, c), m in zip(colors.items(), ["o", "s", "^"])
    ],
    loc="center",
    bbox_to_anchor=(0.5, 0.093),
    ncol=3,
    frameon=False,
)


def panel(bounds, letter, title, chart=True):
    ax = fig.add_axes(bounds)
    fig.text(
        bounds[0],
        bounds[1] + bounds[3] + 0.009,
        letter + "  " + title,
        weight="bold",
        va="bottom",
    )
    if chart:
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(length=2.5, pad=2)
    else:
        ax.axis("off")
    return ax


def table(ax, headers, rows, widths, bbox=(0, 0, 1, 1)):
    t = ax.table(
        cellText=rows, colLabels=headers, colWidths=widths, cellLoc="center", bbox=bbox
    )
    t.auto_set_font_size(False)
    t.set_fontsize(FONT)
    for (r, c), cell in t.get_celld().items():
        cell.set_edgecolor("white")
        cell.set_linewidth(0.6)
        cell.PAD = 0.025
        cell.set_facecolor("#E9EEF1" if r == 0 else ("#F4F6F7" if r % 2 else "white"))
        if r == 0:
            cell.set_text_props(weight="bold")
        if c == 0:
            cell.set_text_props(ha="left")
    return t


def values(key):
    return np.array([float(p[key]) for p in points])


ax = panel([0.085, 0.817, 0.37, 0.097], "a", "Bubble-point temperature")
te = values("T_exp_K")
for prefix, model, marker in [("tf", "ThermoFormer", "s"), ("unifac", "UNIFAC", "^")]:
    ax.scatter(
        te,
        values("T_" + prefix + "_K"),
        s=15,
        marker=marker,
        facecolors="white",
        edgecolors=colors[model],
        linewidths=0.8,
    )
ax.plot([400, 408], [400, 408], ls=":", color="#8B9298", lw=0.8)
ax.set(
    xlim=(401.1, 403),
    ylim=(400, 408),
    xlabel="Experimental temperature (K)",
    ylabel="Predicted temperature (K)",
)
ax.set_xticks([401.5, 402, 402.5])
ax.set_yticks([400, 402, 404, 406, 408])
ax = panel([0.58, 0.817, 0.38, 0.097], "b", "Ester-to-alcohol relative volatility")
for prefix, model, marker in [
    ("exp", "Experiment", "o"),
    ("tf", "ThermoFormer", "s"),
    ("unifac", "UNIFAC", "^"),
]:
    ax.plot(
        range(1, 18),
        values("alpha_" + prefix),
        color=colors[model],
        marker=marker,
        ms=3,
        mfc="white",
        lw=0.85,
        mew=0.7,
    )
ax.axhline(1, color="#8B9298", ls=":", lw=0.8)
ax.set(
    xlabel="Experimental state index",
    ylabel=r"Relative volatility, $\alpha_{E/A}$",
    xlim=(0.5, 17.5),
)
ax.set_xticks([1, 5, 9, 13, 17])

ax = panel([0.035, 0.614, 0.475, 0.142], "c", "VLE prediction errors", False)
metric_rows = []
for label, pattern, digits, kind in [
    ("Vapor-composition MAE", "y_{}_MAE", 6, "mean"),
    ("Temperature MAE (K)", "T_{}_abs_error_K", 4, "mean"),
    ("Max. temperature error (K)", "T_{}_abs_error_K", 4, "max"),
    ("Relative-volatility MAE", "alpha_{}", 6, "alpha"),
    ("Volatility-direction agreement", "alpha_{}", 0, "direction"),
]:
    row = [label]
    for pre in ["tf", "unifac"]:
        a = values(pattern.format(pre))
        if kind == "alpha":
            v = abs(a - values("alpha_exp")).mean()
        elif kind == "direction":
            row.append(f"{np.sum((a > 1) == (values('alpha_exp') > 1))}/17")
            continue
        else:
            v = getattr(a, kind)()
        row.append(f"{v:.{digits}f}")
    metric_rows.append(row)
table(
    ax,
    ["Metric", "ThermoFormer", "UNIFAC"],
    metric_rows,
    [0.53, 0.29, 0.18],
    bbox=(0, 0.29, 1, 0.71),
)
ax.text(
    0,
    0.20,
    "E = ester; A = alcohol.\nComposition MAE: 3 components, 17 states.",
    va="top",
    linespacing=1.3,
)
ax = panel([0.535, 0.614, 0.425, 0.142], "d", "Selected column configuration", False)
settings = [
    ["DMF/feed mass ratio", "32:1"],
    ["DMF feed (mol s$^{-1}$)", f"{tf['S']:.6f}"],
    ["Reflux ratio", str(tf["R"])],
    ["Equilibrium stages", str(tf["N"])],
    ["Alcohol-ester feed stage", str(tf["nf"])],
    ["DMF feed stage", str(tf["ns"])],
    ["Distillate flow (mol s$^{-1}$)", f"{tf['D']:.6f}"],
    ["Bottoms flow (mol s$^{-1}$)", f"{tf['B']:.6f}"],
    ["Internal vapor flow (mol s$^{-1}$)", f"{(tf['R'] + 1) * tf['D']:.6f}"],
]
table(ax, ["Parameter", "Value"], settings, [0.73, 0.27])

ax = panel([0.045, 0.427, 0.915, 0.150], "e", "Design-search ranges", False)
search = [
    [
        "Initial search",
        "Mass 2:1; N = {40, 80, 160}; R = {3, 5, 8, 12, 20, 40};\n"
        + r"$n_S$ = {4, 8, 16}; $n_F$ near {0.35, 0.60, 0.85}N.",
    ],
    [
        "ThermoFormer\nrefinement",
        "Mass 2:1; N = {160, 300}; R = 4-10, step 0.5;\n"
        + r"$n_S$ = {8, 20, 40}; $n_F$ = N-{20, 40, 60}.",
    ],
    [
        "Solvent-ratio search",
        "Mass m = {4, 8, 16, 32}; N = 160; "
        + r"$n_F$ = 140;"
        + "\n"
        + r"$n_S$ = {12, 24, 36}; R = {m, 1.5m, 2m, 3m}.",
    ],
    ["Stage-boundary check", r"Mass 32:1; R = 48; $n_S$ = 16; $n_F$ = N-24."],
]
t = table(ax, ["Calculation", "Evaluated parameter sets"], search, [0.225, 0.775])
for r in range(1, 5):
    t[r, 1].set_text_props(ha="left")

ax = panel([0.03, 0.303, 0.50, 0.098], "f", "Stage boundary and common column", False)
rows = []
for model, r in [("ThermoFormer", below), ("ThermoFormer", tf), ("UNIFAC", uni)]:
    rows.append(
        [
            model,
            str(r["N"]),
            str(r["nf"]),
            f"{100 * r['xD'][1]:.6f}",
            f"{100 * r['recovery']:.6f}",
            "Yes" if r["xD"][1] >= 0.995 and r["recovery"] >= 0.98 else "No",
        ]
    )
table(
    ax,
    ["Model", "N", r"$n_F$", "Purity", "Recovery", "Met"],
    rows,
    [0.32, 0.08, 0.08, 0.20, 0.20, 0.12],
    bbox=(0, 0.42, 1, 0.58),
)
ax.text(
    0,
    0.30,
    "Targets: purity >= 99.5 mol%; recovery >= 98%.\nCompliance uses unrounded values.",
    va="top",
    linespacing=1.3,
)
ax = panel([0.55, 0.303, 0.42, 0.098], "g", "Product compositions (mol%)", False)
rows = []
for stream, key in [("Distillate", "xD"), ("Bottoms", "xB")]:
    for k, comp in enumerate(["Alcohol", "Ester", "DMF"]):
        rows.append(
            [
                stream if k == 0 else "",
                comp,
                f"{100 * tf[key][k]:.6f}",
                f"{100 * uni[key][k]:.6f}",
            ]
        )
table(
    ax,
    ["Stream", "Component", "ThermoFormer", "UNIFAC"],
    rows,
    [0.21, 0.20, 0.35, 0.24],
)

for i, (letter, title, key, component) in enumerate(
    [
        ("h", "Alcohol", "x", 0),
        ("i", "Ester", "x", 1),
        ("j", "DMF", "x", 2),
        ("k", "Temperature", "T", None),
    ]
):
    ax = panel([0.072 + i * 0.236, 0.15, 0.19, 0.095], letter, title)
    for r, model, ls in [(tf, "ThermoFormer", "-"), (uni, "UNIFAC", "--")]:
        v = np.array(r[key])
        v = v[:, component] if component is not None else v
        assert len(v) == 183
        ax.plot(range(1, 184), v, color=colors[model], ls=ls, lw=1.1)
    for stage in [16, 159]:
        ax.axvline(stage, color="#9BA2A8", ls=":", lw=0.7)
    ax.set(xlim=(1, 183))
    ax.set_xticks([1, 90, 183])
    if i == 0:
        ax.set_ylabel("Liquid mole fraction")
    if key == "T":
        ax.set_ylabel("Temperature (K)")
    if key == "x":
        ax.set_ylim(-0.03, 1.03)
        ax.set_yticks([0, 0.5, 1])
fig.text(0.5, 0.12, "Stage from top", ha="center")
fig.canvas.draw()
assert all(
    abs(t.get_fontsize() - FONT) < 1e-9 for t in fig.findobj(Text) if t.get_text()
)
trimmed_page = Bbox.from_bounds(0, 20 / 25.4, 200 / 25.4, 265 / 25.4)
for ext in ["pdf", "svg", "png"]:
    fig.savefig(OUT / f"sec_dmf_summary.{ext}", dpi=400, bbox_inches=trimmed_page)
print(
    "Created 200 x 265 mm composite, all text 10.5 pt. Verified 17 VLE points and two 183-stage profiles."
)
