"""Nature-style multi-panel visualization for ThermoFormer interpretation."""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.tri import Triangulation


COLORS = {
    "blue": "#4C78A8",
    "orange": "#E69F00",
    "green": "#4E9F75",
    "purple": "#8C6BB1",
    "red": "#C65D57",
    "grey": "#8A8A8A",
}


def _style() -> None:
    available = {font.name for font in mpl.font_manager.fontManager.ttflist}
    family = next(
        (name for name in ("Arial", "Helvetica", "DejaVu Sans") if name in available),
        "sans-serif",
    )
    mpl.rcParams.update(
        {
            "font.family": family,
            "font.size": 7.0,
            "axes.labelsize": 7.2,
            "axes.titlesize": 7.5,
            "xtick.labelsize": 6.2,
            "ytick.labelsize": 6.2,
            "legend.fontsize": 5.8,
            "legend.frameon": False,
            "axes.linewidth": 0.6,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def _clean(axis: mpl.axes.Axes) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.tick_params(width=0.55, length=2.5)


def _label(axis: mpl.axes.Axes, letter: str) -> None:
    axis.text(
        -0.16,
        1.08,
        letter,
        transform=axis.transAxes,
        fontsize=9,
        fontweight="bold",
        va="top",
    )


def _short_category(value: str) -> str:
    labels = {
        "lowest-|gE| hydrocarbon candidate": "Hydrocarbon",
        "water/alcohol hydrogen bonding": "Water/alcohol",
        "model-inferred positive deviation": "Positive $g^E$",
        "model-inferred negative deviation": "Negative $g^E$",
        "experimental azeotrope proxy": "Azeotrope",
    }
    if value in labels:
        return labels[value]
    return " / ".join(labels.get(part, part) for part in value.split("; "))


def build_interpretability_figure(
    attribution: pd.DataFrame,
    composition: pd.DataFrame,
    sensitivity: pd.DataFrame,
    manybody: pd.DataFrame,
    output_stem: Path,
) -> list[Path]:
    _style()
    figure, axes = plt.subplots(2, 3, figsize=(7.2, 5.35))
    axes = axes.ravel()

    representative = attribution.loc[
        attribution["representative_categories"].fillna("").ne("")
    ].copy()
    representative["category"] = representative["representative_categories"].str.split("; ")
    representative = representative.explode("category")
    selected_seed = int(composition["selected_seed"].iloc[0])
    representative = representative.loc[representative["seed"].eq(selected_seed)]
    palette = list(COLORS.values())[:5]
    for color, (category, rows) in zip(palette, representative.groupby("category")):
        center_x = float(rows["absolute_pair_potential"].median())
        center_y = float(rows["mean_pair_mask_delta_y"].median())
        x_quantiles = rows["absolute_pair_potential"].quantile([0.25, 0.75])
        y_quantiles = rows["mean_pair_mask_delta_y"].quantile([0.25, 0.75])
        axes[0].errorbar(
            center_x,
            center_y,
            xerr=np.asarray([[center_x - x_quantiles.loc[0.25]], [x_quantiles.loc[0.75] - center_x]]),
            yerr=np.asarray([[center_y - y_quantiles.loc[0.25]], [y_quantiles.loc[0.75] - center_y]]),
            fmt="o",
            color=color,
            markersize=4,
            capsize=2,
            linewidth=0.8,
            label=_short_category(category),
        )
    axes[0].set(
        xlabel=r"Median $|h_{ij}|$",
        ylabel=r"Median token-mask $\Delta y$",
        title="Pair potential vs token masking",
    )
    axes[0].legend(loc="best", handletextpad=0.3)

    isothermal_composition = composition.loc[composition["direction"].eq("isothermal")]
    azeotrope = isothermal_composition.loc[
        isothermal_composition["category"].str.contains(
            "experimental azeotrope proxy", regex=False
        )
    ].sort_values("x_1")
    scatter = axes[1].scatter(
        azeotrope["latent_pc1"],
        azeotrope["latent_pc2"],
        c=azeotrope["x_1"],
        cmap="viridis",
        s=12,
        edgecolors="none",
    )
    axes[1].plot(azeotrope["latent_pc1"], azeotrope["latent_pc2"], color="#777777", lw=0.6)
    colorbar = figure.colorbar(scatter, ax=axes[1], fraction=0.046, pad=0.03)
    colorbar.set_label(r"$x_1$", fontsize=6.5)
    colorbar.ax.tick_params(labelsize=5.8, length=2)
    axes[1].set(xlabel="Latent PC1", ylabel="Latent PC2", title="Composition-dependent latent path")

    unique_systems = isothermal_composition.drop_duplicates("system_id")[["system_id", "category"]]
    for color, (_, identity) in zip(palette, unique_systems.iterrows()):
        rows = isothermal_composition.loc[
            isothermal_composition["system_id"].eq(identity["system_id"])
        ].sort_values("x_1")
        axes[2].plot(
            rows["latent_nonideality_ge_rt"],
            np.log(rows["relative_volatility_12"].clip(lower=1e-12)),
            color=color,
            lw=1.0,
            label=_short_category(identity["category"]),
        )
    axes[2].axhline(0.0, color="#999999", lw=0.55, ls="--")
    axes[2].set(
        xlabel=r"Latent $g^E/RT$",
        ylabel=r"$\ln\alpha_{12}$",
        title="Latent state and volatility response",
    )
    axes[2].legend(loc="best", handlelength=1.4)

    ternary = sensitivity.loc[
        sensitivity["category"].eq("complete-subsystem ternary")
        & sensitivity["model"].eq("full")
    ]
    matrix = ternary.pivot(
        index="affected_component",
        columns="increased_component",
        values="d_log_gamma_i_d_closed_x_j",
    ).to_numpy()
    limit = max(float(np.max(np.abs(matrix))), 1e-8)
    image = axes[3].imshow(matrix, cmap="RdBu_r", vmin=-limit, vmax=limit)
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            axes[3].text(column, row, f"{matrix[row, column]:.2f}", ha="center", va="center", fontsize=5.7)
    axes[3].set_xticks(range(3), ["1", "2", "3"])
    axes[3].set_yticks(range(3), ["1", "2", "3"])
    axes[3].set(
        xlabel="Component increased",
        ylabel=r"Responding $\ln\gamma_i$",
        title="Closed-simplex sensitivity",
    )
    colorbar = figure.colorbar(image, ax=axes[3], fraction=0.046, pad=0.03)
    colorbar.ax.tick_params(labelsize=5.8, length=2)

    experimental = manybody.loc[manybody["record_type"].eq("experimental_test")].copy()
    paired = experimental.groupby(["seed", "system_id", "direction"], as_index=False).agg(
        full_y_mae=("full_y_mae", "mean"),
        pairwise_y_mae=("pairwise_y_mae", "mean"),
    )
    for direction, color, marker in (
        ("isothermal", COLORS["blue"], "o"),
        ("isobaric", COLORS["orange"], "s"),
    ):
        rows = paired.loc[paired["direction"].eq(direction)]
        axes[4].scatter(
            rows["pairwise_y_mae"],
            rows["full_y_mae"],
            s=16,
            alpha=0.75,
            color=color,
            marker=marker,
            label=direction.capitalize(),
        )
    maximum = float(
        max(paired["full_y_mae"].max(), paired["pairwise_y_mae"].max()) * 1.05
    )
    axes[4].plot([0.0, maximum], [0.0, maximum], color="#777777", ls="--", lw=0.7)
    axes[4].set(
        xlim=(0.0, maximum),
        ylim=(0.0, maximum),
        xlabel="Pairwise-only y MAE",
        ylabel="Full-model y MAE",
        title="All eligible ternary tests",
    )
    axes[4].legend(loc="upper left")

    simplex = manybody.loc[manybody["record_type"].eq("simplex_scan")].copy()
    x_coordinate = simplex["x_2"] + 0.5 * simplex["x_3"]
    y_coordinate = np.sqrt(3.0) * 0.5 * simplex["x_3"]
    triangulation = Triangulation(x_coordinate, y_coordinate)
    contour = axes[5].tricontourf(
        triangulation,
        simplex["manybody_y_l1"],
        levels=12,
        cmap="cividis",
    )
    axes[5].plot([0, 1, 0.5, 0], [0, 0, np.sqrt(3) / 2, 0], color="#444444", lw=0.7)
    axes[5].text(-0.03, -0.035, "1", ha="right", va="top", fontsize=6)
    axes[5].text(1.03, -0.035, "2", ha="left", va="top", fontsize=6)
    axes[5].text(0.5, np.sqrt(3) / 2 + 0.035, "3", ha="center", va="bottom", fontsize=6)
    axes[5].set_aspect("equal")
    axes[5].axis("off")
    axes[5].set_title("Many-body correction over composition")
    colorbar = figure.colorbar(contour, ax=axes[5], fraction=0.046, pad=0.03)
    colorbar.set_label(r"$\sum_i |y_i^{full}-y_i^{pair}|$", fontsize=6.5)
    colorbar.ax.tick_params(labelsize=5.8, length=2)

    for letter, axis in zip("abcdef", axes):
        _label(axis, letter)
        if axis is not axes[5]:
            _clean(axis)
    figure.subplots_adjust(left=0.08, right=0.98, bottom=0.08, top=0.96, wspace=0.43, hspace=0.42)

    output_stem.parent.mkdir(parents=True, exist_ok=True)
    outputs = []
    for suffix, options in (("pdf", {}), ("svg", {}), ("png", {"dpi": 600})):
        path = output_stem.with_suffix(f".{suffix}")
        temporary = path.parent / f".{path.stem}.{os.getpid()}.tmp.{suffix}"
        try:
            figure.savefig(temporary, bbox_inches="tight", pad_inches=0.035, **options)
            if suffix == "svg":
                svg_lines = temporary.read_text(encoding="utf-8").splitlines()
                temporary.write_text(
                    "\n".join(line.rstrip() for line in svg_lines) + "\n",
                    encoding="utf-8",
                )
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()
        outputs.append(path)
    plt.close(figure)
    return outputs
