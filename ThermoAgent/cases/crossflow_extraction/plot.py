from pathlib import Path
import json
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text

CASE = Path(__file__).resolve().parent
OUT = CASE / "figures"
OUT.mkdir(exist_ok=True)
SRC = CASE / "data"


def read(n):
    return json.loads((SRC / (n + ".json")).read_text(encoding="utf-8"))


design = read("cascade_designs")
stages = read("cascade_stages")
scans = read("scan")
allocation = read("allocation_designs")
sens = read("reference_interpolation_sensitivity")
pairs = read("interpolation_protocol")["pairs_by_temperature"]
models = ["ThermoFormer", "Experiment-interpolation", "UNIFAC-LLE"]
names = ["ThermoFormer", "Reference", "UNIFAC-LLE"]
colors = ["#B5674D", "#344E64", "#467E78"]
markers = ["s", "o", "^"]


def chosen(T, N, m):
    return next(
        r
        for r in design
        if r["T"] == T and r["N"] == N and r["total_S"] == 1.5 and r["model"] == m
    )


main = [chosen(303.15, 3, m) for m in models]
selected = [
    [
        r
        for r in stages
        if r["T"] == 303.15
        and r["N_requested"] == 3
        and r["total_S"] == 1.5
        and r["model"] == m
    ]
    for m in models
]
assert all(len(rr) == 3 for rr in selected)
assert all(r["overall_component_balance_error"] < 1e-8 for r in main)
FONT = 11
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
fig = plt.figure(figsize=(310 / 25.4, 335 / 25.4), facecolor="white")
fig.text(
    0.5,
    0.986,
    "Three-stage crossflow extraction of benzene with furfural",
    ha="center",
    weight="bold",
)
fig.text(
    0.5,
    0.971,
    r"Feed: 1 mol s$^{-1}$; $z_H$ = 0.733333, $z_B$ = 0.266667  |  $P$ = 101.3 kPa  |  Main design: 303.15 K, 0.5 mol s$^{-1}$ furfural per stage",
    ha="center",
)


def panel(bounds, letter, title, chart=False):
    ax = fig.add_axes(bounds)
    fig.text(
        bounds[0],
        bounds[1] + bounds[3] + 0.008,
        letter + "  " + title,
        va="bottom",
        weight="bold",
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
        cell.set_facecolor("#E9EEF1" if r == 0 else ("#F3F5F6" if r % 2 else "white"))
        if r == 0:
            cell.set_text_props(weight="bold")
        if c == 0:
            cell.set_text_props(ha="left")
    return t


# Source vectors use H,S,B; all tables below explicitly reorder to H,B,S.
def xy(v):
    return np.array([v[1] + 0.5 * v[2], np.sqrt(3) / 2 * v[2]])


ax = panel([0.05, 0.79, 0.29, 0.157], "a", "Equilibrium path at 303.15 K")
ax.plot([0, 1, 0.5, 0], [0, 0, np.sqrt(3) / 2, 0], color="#919CA4", lw=0.8)
for pair in pairs["303.15"]:
    p = np.array([xy(v) for v in pair])
    ax.plot(p[:, 0], p[:, 1], color="#AEB7BD", lw=0.8)
f = xy([11 / 15, 0, 4 / 15])
solvent = xy([0, 1, 0])
previous = f
ax.plot(*f, "o", color="#344E64", ms=4)
ax.annotate("F", f, xytext=(-10, 6), textcoords="offset points")
for r in selected[0]:
    e, rr, m = map(xy, [r["xE"], r["xR"], r["z"]])
    j = r["stage"]
    ax.plot(
        [previous[0], solvent[0]],
        [previous[1], solvent[1]],
        ls="--",
        color="#C4CBCF",
        lw=0.6,
    )
    ax.plot([e[0], rr[0]], [e[1], rr[1]], color=colors[0], lw=1)
    ax.plot(*e, "o", color=colors[0], ms=3)
    ax.plot(*rr, "s", color=colors[0], ms=3)
    ax.plot(*m, "x", color="#3F454A", ms=4)
    ax.annotate(
        f"E{j}",
        e,
        xytext=(1.10, [0.22, 0.12, 0.02][j - 1]),
        ha="left",
        va="center",
        arrowprops=dict(arrowstyle="-", color="#8A9399", lw=0.5),
    )
    ax.annotate(
        f"R{j}",
        rr,
        xytext=(-0.09, [0.20, 0.11, 0.02][j - 1]),
        ha="right",
        va="center",
        arrowprops=dict(arrowstyle="-", color="#8A9399", lw=0.5),
    )
    previous = rr
for label, p in [("H", (0, -0.055)), ("S", (1, -0.055)), ("B", (0.5, 0.9))]:
    ax.text(*p, label, ha="center")
ax.text(
    0.50,
    0.59,
    "Gray: measured tie lines\nColored: ThermoFormer tie lines\nx: mixed feeds",
    ha="center",
    va="center",
    linespacing=1.4,
)
ax.set_aspect("equal")
ax.set(xlim=(-0.20, 1.24), ylim=(-0.085, 0.94))

ax = panel(
    [0.39, 0.79, 0.58, 0.157], "b", "Experimental tie-line endpoints (mole fractions)"
)
rows = []
for T in ["298.15", "303.15"]:
    for j, (e, r) in enumerate(pairs[T], 1):
        rows.append(
            [T, str(j)]
            + [f"{v:.4f}" for arr in [e, r] for v in np.array(arr)[[0, 2, 1]]]
        )
table(
    ax,
    [
        "T (K)",
        "Line",
        r"$E:x_H$",
        r"$E:x_B$",
        r"$E:x_S$",
        r"$R:x_H$",
        r"$R:x_B$",
        r"$R:x_S$",
    ],
    rows,
    [0.12, 0.07] + [0.135] * 6,
)

ax = panel(
    [0.035, 0.651, 0.935, 0.099],
    "c",
    "Complete outlet streams: three-stage main design",
)
rows = []
for j in range(1, 4):
    for phase in ["E", "R"]:
        row = [f"{phase}{j}"]
        for rr in selected:
            r = next(r for r in rr if r["stage"] == j)
            row += [f"{r[phase]:.6f}"] + [
                f"{v:.6f}" for v in np.array(r["x" + phase])[[0, 2, 1]]
            ]
        rows.append(row)
table(
    ax,
    ["Stream"] + ["Flow", r"$x_H$", r"$x_B$", r"$x_S$"] * 3,
    rows,
    [0.064] + [0.078] * 12,
    bbox=(0, 0, 1, 0.90),
)
for i, name in enumerate(["ThermoFormer", "Experimental reference", "UNIFAC-LLE"]):
    ax.text(
        0.064 + 0.312 * (i + 0.5),
        0.94,
        name,
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        weight="bold",
        color=colors[i],
    )
fig.text(
    0.035,
    0.631,
    r"All flows: mol s$^{-1}$. H: $n$-heptane; B: benzene; S: furfural. Each source independently carries its full raffinate composition into the next stage.",
)

ax = panel([0.035, 0.429, 0.48, 0.178], "d", "Overall results: three-stage main design")
metrics = [
    ("Benzene recovery (%)", lambda r: 100 * r["benzene_recovery"], 2),
    ("Heptane retention (%)", lambda r: 100 * r["heptane_retention"], 2),
    ("Final raffinate flow", lambda r: r["R_final"], 6),
    ("Combined extract flow", lambda r: r["E_total"], 6),
    ("Furfural flow in raffinate", lambda r: r["solvent_to_raffinate"], 6),
    ("Heptane in raffinate (mol%)", lambda r: 100 * r["R_final_x"][0], 2),
    ("Benzene in raffinate (mol%)", lambda r: 100 * r["R_final_x"][2], 2),
    ("Furfural in raffinate (mol%)", lambda r: 100 * r["R_final_x"][1], 2),
    ("Benzene in extract (mol%)", lambda r: 100 * r["E_combined_x"][2], 2),
    ("Furfural in extract (mol%)", lambda r: 100 * r["E_combined_x"][1], 2),
    (
        "Solvent-free raffinate H (mol%)",
        lambda r: 100 * r["R_final_x"][0] / (r["R_final_x"][0] + r["R_final_x"][2]),
        2,
    ),
    (
        "Solvent-free extract B (mol%)",
        lambda r: 100
        * r["E_combined_x"][2]
        / (r["E_combined_x"][0] + r["E_combined_x"][2]),
        2,
    ),
]
table(
    ax,
    ["Quantity"] + names,
    [[label] + [f"{fn(r):.{digits}f}" for r in main] for label, fn, digits in metrics],
    [0.39, 0.23, 0.19, 0.19],
)
ax = panel([0.55, 0.484, 0.42, 0.123], "e", "Stage selection: fixed total solvent flow")
rows = []
for T in [298.15, 303.15]:
    for N in range(1, 5):
        rows.append(
            [f"{T:.2f}", str(N)]
            + [
                f"{100 * chosen(T, N, m)[key]:.2f}"
                for key in ["benzene_recovery", "heptane_retention"]
                for m in models
            ]
        )
table(
    ax,
    ["T (K)", "N", "1", "2", "3", "1", "2", "3"],
    rows,
    [0.145, 0.065] + [0.1316667] * 6,
    bbox=(0, 0, 1, 0.88),
)
ax.text(0.402, 0.92, "B recovery (%)", ha="center", transform=ax.transAxes, va="bottom")
ax.text(
    0.802, 0.92, "H retention (%)", ha="center", transform=ax.transAxes, va="bottom"
)
ax.text(
    0,
    -0.13,
    "Targets: B recovery >= 70%; H retention >= 80%.\n1 ThermoFormer; 2 experimental reference; 3 UNIFAC-LLE.\nTotal furfural: 1.5 mol s$^{-1}$, divided equally.",
    transform=ax.transAxes,
    va="top",
)

ax = panel(
    [0.035, 0.293, 0.48, 0.097], "f", "Best recovery in discrete allocation scans"
)
rows = []
for N in [2, 3]:
    for m, name in zip(models, names):
        rr = [
            r
            for r in allocation
            if r["N"] == N and r["model"] == m and r["status"] == "valid"
        ]
        assert len(rr) == (12 if N == 2 else 10)
        r = max(rr, key=lambda r: r["benzene_recovery"])
        rows.append(
            [
                str(N),
                name,
                " / ".join(f"{v:.2f}" for v in r["allocation"]),
                f"{100 * r['benzene_recovery']:.2f}",
                f"{100 * r['heptane_retention']:.2f}",
            ]
        )
table(
    ax,
    ["N", "Source", "Stagewise solvent", "B rec. (%)", "H ret. (%)"],
    rows,
    [0.06, 0.29, 0.27, 0.19, 0.19],
)
ax = panel([0.55, 0.316, 0.42, 0.074], "g", "Reference interpolation sensitivity")
rows = []
for T in [298.15, 303.15]:
    for N in [2, 3]:
        linear = 100 * chosen(T, N, models[1])["benzene_recovery"]
        pchip = (
            100
            * next(r for r in sens if r["T"] == T and r["N"] == N)["benzene_recovery"]
        )
        rows.append(
            [
                f"{T:.2f}",
                str(N),
                f"{linear:.2f}",
                f"{pchip:.2f}",
                f"{pchip - linear:.3f}",
            ]
        )
table(
    ax,
    ["T (K)", "N", "Linear (%)", "PCHIP (%)", "Diff. (pp)"],
    rows,
    [0.19, 0.08, 0.245, 0.245, 0.24],
)
ax.text(
    0,
    -0.18,
    "Benzene recovery; differences before rounding.\nInterpolation is restricted to measured tie lines.",
    transform=ax.transAxes,
    va="top",
)


def curves(ax, records, xkey, ykey):
    for m, c, mk in zip(models, colors, markers):
        rr = sorted([r for r in records if r["model"] == m], key=lambda r: r[xkey])
        assert all(r["status"] == "valid" for r in rr)
        ax.plot(
            [r[xkey] for r in rr],
            [100 * r[ykey] for r in rr],
            color=c,
            marker=mk,
            ms=3,
            mfc="white",
            lw=0.95,
            mew=0.7,
        )


for i, (letter, title, key) in enumerate(
    [
        ("h", "Stage count: B recovery", "benzene_recovery"),
        ("i", "Stage count: H retention", "heptane_retention"),
        ("j", "Allocation: B recovery", "benzene_recovery"),
        ("k", "Allocation: H retention", "heptane_retention"),
    ]
):
    ax = panel([0.06 + i * 0.24, 0.173, 0.185, 0.074], letter, title, True)
    if i < 2:
        rr = [r for r in design if r["T"] == 303.15 and r["total_S"] == 1.5]
        curves(ax, rr, "N", key)
        ax.set_xticks([1, 2, 3, 4])
        ax.set_xlabel("Number of stages, N")
    else:
        rr = [dict(r, S1=r["allocation"][0]) for r in allocation if r["N"] == 2]
        curves(ax, rr, "S1", key)
        ax.set_xticks([0.2, 0.6, 1, 1.3])
        ax.set_xlabel(r"Stage-1 solvent (mol s$^{-1}$)")
    ax.set_ylabel("B recovery (%)" if key == "benzene_recovery" else "H retention (%)")
    ax.axhline(70 if key == "benzene_recovery" else 80, color="#8D949A", ls=":", lw=0.8)

for i, (T, key) in enumerate(
    [
        (298.15, "benzene_recovery"),
        (303.15, "benzene_recovery"),
        (298.15, "heptane_retention"),
        (303.15, "heptane_retention"),
    ]
):
    ax = panel(
        [0.06 + i * 0.24, 0.055, 0.185, 0.059],
        "lmno"[i],
        f"Single stage: {T:.2f} K",
        True,
    )
    rr = [r for r in scans if r["T"] == T]
    assert all(sum(r["model"] == m for r in rr) == 22 for m in models)
    curves(ax, rr, "S", key)
    ax.set_xticks([0.2, 1.2, 2.2])
    ax.set_xlabel("Solvent/feed molar ratio")
    ax.set_ylabel("B recovery (%)" if key == "benzene_recovery" else "H retention (%)")
fig.legend(
    handles=[
        Line2D([], [], color=c, marker=m, mfc="white", ms=4, lw=1, label=n)
        for c, m, n in zip(
            colors, markers, ["ThermoFormer", "Experimental reference", "UNIFAC-LLE"]
        )
    ],
    loc="center",
    bbox_to_anchor=(0.51, 0.010),
    ncol=3,
    frameon=False,
)
fig.canvas.draw()
assert all(
    abs(t.get_fontsize() - FONT) < 1e-9 for t in fig.findobj(Text) if t.get_text()
)
for ext in ["png", "pdf", "svg"]:
    fig.savefig(OUT / f"furfural_extraction_summary.{ext}", dpi=400)
print(
    "Created 15-panel figure; 12 measured tie lines, 18 outlet streams, 22 allocations per source, and 22 solvent flows per temperature checked."
)
