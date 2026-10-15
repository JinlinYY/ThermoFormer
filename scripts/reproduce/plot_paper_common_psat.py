"""Plot the validated common-Psat audit; no thermodynamic computations here."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "experiments/supporting_information/s7_separation_design/results/common-psat-20260928"
BLUE, ORANGE = "#3079A8", "#CC633D"


def load(name: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((DATA / name).read_text(encoding="utf-8")))


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 11,
            "axes.titlesize": 12,
            "axes.labelsize": 11,
            "axes.linewidth": 0.8,
            "svg.fonttype": "none",
            "xtick.direction": "out",
            "ytick.direction": "out",
            "xtick.major.size": 3,
            "ytick.major.size": 3,
        }
    )
    pure = load("pure_pressure_checks.json")
    summary = load("summary.json")["records"]
    fixed = load("fixed_state_decomposition.json")
    fig, axes = plt.subplots(2, 2, figsize=(11.4, 7.8))
    fig.subplots_adjust(left=0.085, right=0.975, top=0.94, bottom=0.16, hspace=0.43, wspace=0.28)
    for index, ax in enumerate(axes.flat):
        label = "abcd"[index]
        ax.spines[["top", "right"]].set_visible(False)
        ax.text(-0.15, 1.07, label, transform=ax.transAxes, fontsize=16, fontweight="bold")

    ax = axes[0, 0]
    ax.set_title("Sec-butyl acetate vapour pressure", loc="left", pad=12)
    t = np.array(pure["curve_T_K"])
    ax.axvspan(384, 425, color="#F0F0F0", zorder=0)
    styles = [
        ("original_unifac", "Original UNIFAC backend", BLUE, "-"),
        ("original_thermoformer", "ThermoFormer learned", ORANGE, "-"),
        ("li2013", "Reference A (Li 2013)", "#262626", "--"),
        ("huang2015", "Reference B (Huang 2015)", "#929292", "-."),
    ]
    for key, label, color, style in styles:
        ax.plot(t, np.array(pure["curves_psat_kPa"][key])[:, 1], color=color, ls=style, lw=1.7, label=label)
    ax.scatter(
        pure["T_K"],
        pure["experimental_P_kPa"],
        marker="o",
        s=21,
        facecolor="white",
        edgecolor="#262626",
        lw=0.8,
        zorder=5,
        label="Measured (Li 2013)",
    )
    ax.set(xlabel="Temperature (K)", ylabel="Saturation pressure (kPa)", xlim=(328, 426), ylim=(0, 320))
    ax.legend(frameon=False, fontsize=8.9, loc="upper left", handlelength=2.2, labelspacing=0.32)
    ax.text(405, 9, "A: extrapolated", fontsize=9, color="#555555", ha="center")

    labels = ["Original\n(separate $P^{sat}$)", "Common $P^{sat}$\nReference A", "Common $P^{sat}$\nReference B"]
    references = ["original", "li2013", "huang2015"]
    lookup = {(row["reference"], row["gamma_model"]): row for row in summary}
    for ax, metric, title, ylabel in [
        (axes[0, 1], "y_MAE", "Mixture VLE prediction (17 states)", "Vapour-composition MAE"),
        (axes[1, 0], "purity_percent", "Same 183-stage column", "Distillate ester purity (mol%)"),
    ]:
        for model, color, shift, name in [
            ("unifac", BLUE, -0.19, "UNIFAC"),
            ("thermoformer", ORANGE, 0.19, "ThermoFormer"),
        ]:
            values = [lookup[(ref, model)][metric] for ref in references]
            pos = np.arange(3) + shift
            ax.bar(pos, values, width=0.34, color=color, label=name, zorder=3)
            for index, value in enumerate(values):
                xx = pos[index]
                ax.text(
                    xx,
                    value + (0.0011 if metric == "y_MAE" else 2),
                    f"{value:.4f}" if metric == "y_MAE" else f"{value:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                )
        ax.set_xticks(np.arange(3), labels, fontsize=10)
        ax.set_title(title, loc="left", pad=12)
        ax.set_ylabel(ylabel)
        ax.set_ylim(0, 0.045 if metric == "y_MAE" else 115)
        ax.grid(axis="y", lw=0.5, color="#E7E7E7", zorder=0)
        if metric == "y_MAE":
            ax.legend(frameon=False, loc="upper right", fontsize=9, ncol=2)
            ax.set_yticks([0, 0.01, 0.02, 0.03, 0.04])
        else:
            ax.set_yticks([0, 25, 50, 75, 100])

    ax = axes[1, 1]
    j = fixed["stage"].index(16)
    alphas = {
        "unifac": [fixed["alpha_original_unifac"][j]],
        "thermoformer": [fixed["alpha_original_tf"][j]],
    }
    for ref in ["li2013", "huang2015"]:
        alphas["unifac"].append(fixed["common"][ref]["alpha_unifac"][j])
        alphas["thermoformer"].append(fixed["common"][ref]["alpha_tf"][j])
    for model, color, shift, marker in [("unifac", BLUE, -0.12, "o"), ("thermoformer", ORANGE, 0.12, "s")]:
        pos = np.arange(3) + shift
        ax.plot(pos, alphas[model], marker=marker, color=color, lw=1, ms=6)
        for index, value in enumerate(alphas[model]):
            xx = pos[index]
            ax.text(xx, value + 0.018, f"{value:.3f}", color=color, ha="center", fontsize=10)
    ax.axhline(1, color="#555555", ls="--", lw=0.9)
    ax.text(2.42, 1.006, "$\\alpha=1$", ha="right", va="bottom", fontsize=10)
    ax.set_title("Same composition and temperature", loc="left", pad=12)
    ax.set_ylabel("Ester / alcohol relative volatility")
    ax.set_xticks(np.arange(3), labels, fontsize=10)
    ax.set(xlim=(-0.5, 2.5), ylim=(0.78, 1.23))
    ax.text(0.02, 0.03, "$T=410.22$ K; $x_{DMF}=0.84735$", transform=ax.transAxes, fontsize=10)

    fig.text(
        0.085,
        0.069,
        (
            "Common references use the same alcohol and DMF correlations; "
            "only the ester correlation differs between A and B."
        ),
        fontsize=9.5,
    )
    fig.text(
        0.085,
        0.044,
        (
            "A is extrapolated above 384 K; B's validation range is unverified. "
            "ThermoFormer weights are frozen. Column values are simulations."
        ),
        fontsize=9.5,
    )
    destination = DATA / "figures"
    destination.mkdir(exist_ok=True)
    for extension in ["png", "svg"]:
        fig.savefig(destination / ("common_psat_comparison." + extension), dpi=300, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
