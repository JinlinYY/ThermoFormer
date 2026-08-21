"""Create the publication-ready six-panel VLE dataset overview figure."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy.ndimage import gaussian_filter

SEED = 42
MM_TO_INCH = 1.0 / 25.4
PALETTE = {
    "Binary": "#4C78A8",
    "Ternary": "#D58A55",
    "Shared": "#75638A",
    "Grey": "#8C8C8C",
    "LightGrey": "#D9D9D9",
    "Dark": "#333333",
}


def _font_family() -> str:
    available = {item.name for item in mpl.font_manager.fontManager.ttflist}
    for candidate in ("Arial", "Helvetica", "DejaVu Sans"):
        if candidate in available:
            return candidate
    return "sans-serif"


def _set_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": _font_family(),
            "font.size": 7.2,
            "axes.labelsize": 7.5,
            "axes.titlesize": 8.0,
            "axes.linewidth": 0.6,
            "xtick.labelsize": 6.7,
            "ytick.labelsize": 6.7,
            "xtick.major.width": 0.55,
            "ytick.major.width": 0.55,
            "xtick.major.size": 2.6,
            "ytick.major.size": 2.6,
            "legend.fontsize": 6.5,
            "legend.frameon": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def _clean_axes(ax: mpl.axes.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#777777")
    ax.spines["bottom"].set_color("#777777")
    ax.tick_params(colors="#4A4A4A")


def _panel_label(ax: mpl.axes.Axes, label: str, x: float = -0.16) -> None:
    ax.text(
        x,
        1.06,
        f"({label})",
        transform=ax.transAxes,
        fontsize=9.2,
        fontweight="bold",
        va="bottom",
        ha="left",
        clip_on=False,
        color=PALETTE["Dark"],
    )


def _compact_number(value: int) -> str:
    return f"{value / 1000:.1f}k" if value >= 10_000 else f"{value:,}"


def _panel_scale(ax: mpl.axes.Axes, scale: pd.DataFrame) -> None:
    metrics = [
        ("Data points", "data_points"),
        ("Systems", "unique_systems"),
        ("Components", "unique_components"),
    ]
    colors = {"Binary": PALETTE["Binary"], "Ternary": PALETTE["Ternary"]}
    positions = {"Binary": 0.11, "Ternary": -0.11}
    for row, (title, column) in zip([2.15, 1.15, 0.15], metrics):
        values = scale.set_index("dataset")[column]
        maximum = float(values.max())
        ax.text(-0.43, row, title, ha="left", va="center", fontsize=7.2, color=PALETTE["Dark"])
        ax.plot([0, 1], [row, row], color="#E6E6E6", lw=0.7, zorder=0)
        for dataset in ("Binary", "Ternary"):
            value = int(values[dataset])
            normalized = value / maximum
            y = row + positions[dataset]
            ax.plot([0, normalized], [y, y], color=colors[dataset], lw=1.3, alpha=0.8)
            ax.scatter(
                normalized,
                y,
                s=17,
                color=colors[dataset],
                marker="o" if dataset == "Binary" else "^",
                edgecolor="white",
                linewidth=0.35,
                zorder=3,
            )
            offset = 0.035 if normalized < 0.88 else -0.035
            ax.text(
                normalized + offset,
                y,
                _compact_number(value),
                ha="left" if offset > 0 else "right",
                va="center",
                fontsize=6.5,
                color=colors[dataset],
            )
    ax.set_xlim(-0.44, 1.18)
    ax.set_ylim(-0.25, 2.55)
    ax.axis("off")
    ax.legend(
        handles=[
            Line2D([], [], color=PALETTE["Binary"], marker="o", lw=1.2, ms=3.5, label="Binary"),
            Line2D([], [], color=PALETTE["Ternary"], marker="^", lw=1.2, ms=3.5, label="Ternary"),
        ],
        loc="upper right",
        bbox_to_anchor=(1.02, 1.08),
        ncol=2,
        handlelength=1.3,
        columnspacing=0.8,
    )
    _panel_label(ax, "a", x=-0.09)


def _density_contours(
    ax: mpl.axes.Axes,
    frame: pd.DataFrame,
    color: str,
    linestyle: str,
    temperature_edges: np.ndarray,
    log_pressure_edges: np.ndarray,
) -> None:
    histogram, _, _ = np.histogram2d(
        frame["temperature_k"],
        np.log10(frame["pressure_kpa"]),
        bins=(temperature_edges, log_pressure_edges),
    )
    density = gaussian_filter(histogram.T, sigma=1.15)
    positive = density[density > 0]
    if positive.size == 0:
        return
    ordered = np.sort(positive)[::-1]
    cumulative = np.cumsum(ordered) / ordered.sum()
    thresholds = []
    for fraction in (0.90, 0.70, 0.45):
        thresholds.append(ordered[min(np.searchsorted(cumulative, fraction), len(ordered) - 1)])
    levels = np.unique(np.sort(thresholds))
    if levels.size < 2:
        return
    t_centers = (temperature_edges[:-1] + temperature_edges[1:]) / 2
    logp_centers = (log_pressure_edges[:-1] + log_pressure_edges[1:]) / 2
    ax.contour(
        t_centers,
        10**logp_centers,
        density,
        levels=levels,
        colors=[color],
        linestyles=linestyle,
        linewidths=[0.55, 0.75, 1.0][: len(levels)],
        alpha=0.95,
    )


def _panel_state_space(ax: mpl.axes.Axes, records: pd.DataFrame) -> None:
    rng = np.random.default_rng(SEED)
    t_edges = np.linspace(records["temperature_k"].min(), records["temperature_k"].max(), 92)
    lp_edges = np.linspace(
        np.log10(records["pressure_kpa"].min()),
        np.log10(records["pressure_kpa"].max()),
        72,
    )
    for dataset, marker, linestyle in (
        ("Binary", "o", "solid"),
        ("Ternary", "^", "dashed"),
    ):
        frame = records.loc[records["dataset"] == dataset]
        count = min(1_500, len(frame))
        selected = rng.choice(frame.index.to_numpy(), size=count, replace=False)
        sample = frame.loc[selected]
        ax.scatter(
            sample["temperature_k"],
            sample["pressure_kpa"],
            s=2.8,
            marker=marker,
            color=PALETTE[dataset],
            alpha=0.14,
            linewidth=0,
        )
        _density_contours(ax, frame, PALETTE[dataset], linestyle, t_edges, lp_edges)
    ax.set_yscale("log")
    ax.set_xlim(140, 1600)
    ax.set_ylim(7e-3, 7e4)
    ax.set_xlabel("Temperature (K)")
    ax.set_ylabel("Pressure (kPa, log scale)")
    ax.set_xticks([200, 600, 1000, 1400])
    ax.grid(which="major", color="#ECECEC", lw=0.45, zorder=0)
    ax.grid(which="minor", visible=False)
    ax.legend(
        handles=[
            Line2D([], [], color=PALETTE["Binary"], marker="o", lw=0.9, ms=3, label="Binary"),
            Line2D([], [], color=PALETTE["Ternary"], marker="^", lw=0.9, ls="--", ms=3, label="Ternary"),
        ],
        loc="upper right",
        handlelength=1.7,
        borderaxespad=0.2,
    )
    _clean_axes(ax)
    _panel_label(ax, "b")


def _panel_composition(ax: mpl.axes.Axes, records: pd.DataFrame) -> None:
    ax.axis("off")
    binary_ax = ax.inset_axes([0.00, 0.08, 0.49, 0.84])
    ternary_ax = ax.inset_axes([0.56, 0.08, 0.44, 0.84])
    binary = records.loc[records["dataset"] == "Binary"]
    ternary = records.loc[records["dataset"] == "Ternary"]
    blue_map = LinearSegmentedColormap.from_list("binary_density", ["#F7F9FB", PALETTE["Binary"]])
    orange_map = LinearSegmentedColormap.from_list("ternary_density", ["#FDF9F5", PALETTE["Ternary"]])
    binary_ax.hexbin(
        binary["x1"],
        binary["y1"],
        gridsize=34,
        extent=(0, 1, 0, 1),
        mincnt=1,
        bins="log",
        cmap=blue_map,
        linewidths=0,
    )
    binary_ax.plot([0, 1], [0, 1], color="#666666", lw=0.55, ls=(0, (2, 2)))
    binary_ax.set(xlim=(0, 1), ylim=(0, 1), xlabel=r"Liquid $x_1$", ylabel=r"Vapor $y_1$")
    binary_ax.set_xticks([0, 0.5, 1])
    binary_ax.set_yticks([0, 0.5, 1])
    binary_ax.set_title("Binary", pad=2)
    _clean_axes(binary_ax)

    x3 = ternary["x3"].to_numpy()
    cart_x = ternary["x2"].to_numpy() + 0.5 * x3
    cart_y = (np.sqrt(3) / 2) * x3
    ternary_ax.hexbin(
        cart_x,
        cart_y,
        gridsize=31,
        extent=(0, 1, 0, np.sqrt(3) / 2),
        mincnt=1,
        bins="log",
        cmap=orange_map,
        linewidths=0,
    )
    vertices_x = [0, 1, 0.5, 0]
    vertices_y = [0, 0, np.sqrt(3) / 2, 0]
    ternary_ax.plot(vertices_x, vertices_y, color="#555555", lw=0.7)
    ternary_ax.text(-0.02, -0.035, r"$x_1$", ha="right", va="top", fontsize=6.7)
    ternary_ax.text(1.02, -0.035, r"$x_2$", ha="left", va="top", fontsize=6.7)
    ternary_ax.text(0.5, np.sqrt(3) / 2 + 0.025, r"$x_3$", ha="center", va="bottom", fontsize=6.7)
    ternary_ax.set_xlim(-0.06, 1.06)
    ternary_ax.set_ylim(-0.06, 0.94)
    ternary_ax.set_aspect("equal")
    ternary_ax.set_title("Ternary liquid", pad=2)
    ternary_ax.axis("off")
    _panel_label(ax, "c", x=-0.12)


def _panel_molecular(ax: mpl.axes.Axes, molecular: pd.DataFrame) -> None:
    projected = molecular.loc[
        molecular["umap_status"].eq("projected")
        & molecular["umap_1"].notna()
        & molecular["umap_2"].notna()
    ]
    styles = {
        "Binary only": (PALETTE["Binary"], "o", 12, 0.68),
        "Ternary only": (PALETTE["Ternary"], "^", 15, 0.76),
        "Shared": (PALETTE["Shared"], "D", 14, 0.82),
    }
    for membership in ("Binary only", "Ternary only", "Shared"):
        group = projected.loc[projected["dataset_membership"] == membership]
        total = int((molecular["dataset_membership"] == membership).sum())
        color, marker, size, alpha = styles[membership]
        ax.scatter(
            group["umap_1"],
            group["umap_2"],
            s=size,
            marker=marker,
            color=color,
            alpha=alpha,
            linewidth=0,
            label=f"{membership} ({len(group)}/{total})",
        )
    y_min = float(projected["umap_2"].min())
    y_max = float(projected["umap_2"].max())
    y_span = max(y_max - y_min, 1.0)
    ax.set_ylim(y_min - 0.22 * y_span, y_max + 0.34 * y_span)
    ax.set_xlabel("UMAP 1")
    ax.set_ylabel("UMAP 2")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines[:].set_visible(False)
    ax.legend(
        loc="upper left",
        handletextpad=0.25,
        borderaxespad=0.15,
        labelspacing=0.25,
        title="Projected / total",
        title_fontsize=6.2,
    )
    disconnected = int((molecular["umap_status"] == "disconnected").sum())
    unresolved = int((molecular["umap_status"] == "unresolved_smiles").sum())
    ax.text(
        0.99,
        0.02,
        f"{unresolved} unresolved structures;\n{disconnected} isolated fingerprints",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        color="#666666",
        fontsize=6.2,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 1.4},
    )
    _panel_label(ax, "d")


def _panel_rank(ax: mpl.axes.Axes, ranks: pd.DataFrame) -> None:
    for dataset, marker, linestyle in (
        ("Binary", "o", "-"),
        ("Ternary", "^", "--"),
    ):
        frame = ranks.loc[ranks["dataset"] == dataset]
        mark_every = max(1, len(frame) // 12)
        ax.plot(
            frame["rank"],
            frame["data_points"],
            color=PALETTE[dataset],
            lw=1.15,
            ls=linestyle,
            marker=marker,
            ms=2.1,
            markevery=mark_every,
            label=dataset,
        )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("System rank (log scale)")
    ax.set_ylabel("Experimental points per system")
    ax.grid(which="major", color="#ECECEC", lw=0.45)
    ax.grid(which="minor", visible=False)
    ax.legend(loc="upper right", handlelength=1.8, borderaxespad=0.2)
    _clean_axes(ax)
    _panel_label(ax, "e")


def _panel_coverage(ax: mpl.axes.Axes, coverage: pd.DataFrame) -> None:
    counts = (
        coverage["available_binary_subsystems"]
        .value_counts()
        .reindex([3, 2, 1, 0], fill_value=0)
    )
    percentages = 100 * counts / counts.sum()
    colors = [PALETTE["Shared"], PALETTE["Binary"], PALETTE["Ternary"], PALETTE["Grey"]]
    left = 0.0
    for known, color in zip([3, 2, 1, 0], colors):
        width = float(percentages[known])
        ax.barh(0.56, width, left=left, height=0.28, color=color, edgecolor="white", linewidth=0.7)
        if width >= 9:
            ax.text(
                left + width / 2,
                0.56,
                f"{counts[known]}\n{width:.1f}%",
                ha="center",
                va="center",
                color="white",
                fontsize=6.2,
                fontweight="bold",
            )
        else:
            ax.annotate(
                f"{counts[known]} ({width:.1f}%)",
                xy=(left + width / 2, 0.72),
                xytext=(94, 0.90),
                textcoords="data",
                ha="center",
                va="bottom",
                fontsize=6.1,
                color=PALETTE["Dark"],
                arrowprops={"arrowstyle": "-", "color": "#777777", "lw": 0.5},
            )
        left += width
    ax.set_xlim(0, 100)
    ax.set_ylim(0.0, 1.08)
    ax.set_xlabel("Fraction of ternary systems (%)")
    ax.set_yticks([])
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#777777")
    ax.legend(
        handles=[
            Patch(facecolor=color, label=f"{known}/3 available")
            for known, color in zip([3, 2, 1, 0], colors)
        ],
        loc="lower center",
        bbox_to_anchor=(0.5, -0.03),
        ncol=2,
        columnspacing=0.8,
        handlelength=0.9,
        handletextpad=0.35,
    )
    _panel_label(ax, "f")


def create_figure(analysis_root: Path) -> list[Path]:
    results = analysis_root / "results"
    figures = analysis_root / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    scale = pd.read_csv(results / "dataset_scale.csv")
    records = pd.read_csv(results / "vle_records_for_plotting.csv")
    molecular = pd.read_csv(results / "molecular_space.csv")
    ranks = pd.read_csv(results / "system_rank_frequency.csv")
    coverage = pd.read_csv(results / "ternary_binary_subsystem_coverage.csv")

    _set_style()
    figure, axes = plt.subplots(
        2,
        3,
        figsize=(180 * MM_TO_INCH, 133 * MM_TO_INCH),
    )
    _panel_scale(axes[0, 0], scale)
    _panel_state_space(axes[0, 1], records)
    _panel_composition(axes[0, 2], records)
    _panel_molecular(axes[1, 0], molecular)
    _panel_rank(axes[1, 1], ranks)
    _panel_coverage(axes[1, 2], coverage)
    figure.subplots_adjust(left=0.072, right=0.988, bottom=0.095, top=0.955, wspace=0.39, hspace=0.42)

    outputs = []
    for suffix, kwargs in (
        ("pdf", {}),
        ("svg", {}),
        ("png", {"dpi": 600}),
    ):
        path = figures / f"Figure_dataset_overview.{suffix}"
        figure.savefig(path, bbox_inches="tight", pad_inches=0.035, **kwargs)
        outputs.append(path)
    plt.close(figure)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--analysis-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args()
    outputs = create_figure(args.analysis_root.resolve())
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
