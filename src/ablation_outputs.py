"""Aggregate, visualize, and report the locked ThermoFormer ablation campaign."""

from __future__ import annotations

import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from .ablation_protocols import ABLATION_SEEDS, ABLATION_VARIANTS, AblationVariant
from .config import load_experiment_config
from .paper_runner import result_protocol_name


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COLORS = {
    "full": "#0072B2",
    "pairwise": "#E69F00",
    "independent": "#009E73",
    "direct": "#D55E00",
    "other": "#999999",
}


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", prefix=f".{path.name}.",
            suffix=".tmp", dir=path.parent, delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _atomic_to_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", prefix=f".{path.name}.",
            suffix=".tmp", dir=path.parent, delete=False,
        ) as handle:
            temporary = Path(handle.name)
            frame.to_csv(handle, index=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _result_dir(project_root: Path, variant_id: str, benchmark: str) -> Path:
    variant = ABLATION_VARIANTS[variant_id]
    if variant.reference:
        return project_root / "results" / benchmark
    experiment = load_experiment_config(project_root / variant.config)
    protocol = result_protocol_name(experiment.name, benchmark)
    return project_root / "results" / "ablation" / "runs" / protocol


def _select_summary(
    frame: pd.DataFrame,
    scope: str,
    direction: str,
    component_count: int | None,
) -> pd.Series:
    selected = frame.loc[frame["scope"].eq(scope) & frame["direction"].eq(direction)]
    if component_count is None:
        selected = selected.loc[selected["component_count"].isna()]
    else:
        selected = selected.loc[
            pd.to_numeric(selected["component_count"], errors="coerce").eq(component_count)
        ]
    selected = selected.loc[selected["subgroup"].isna()]
    if len(selected) != 1:
        raise ValueError(
            f"Expected one ablation metric row for {(scope, direction, component_count)}, "
            f"found {len(selected)}"
        )
    return selected.iloc[0]


def _costs(result_dir: Path) -> dict[str, float | None]:
    manifests = [
        json.loads((result_dir / f"seed_{seed}" / "manifest.json").read_text(encoding="utf-8"))
        for seed in ABLATION_SEEDS
    ]
    inference = []
    for seed, manifest in zip(ABLATION_SEEDS, manifests):
        value = manifest.get("inference_ms_per_attempt")
        if value is None:
            physical_path = result_dir / f"seed_{seed}" / "physical_consistency.json"
            if physical_path.is_file():
                value = json.loads(physical_path.read_text(encoding="utf-8")).get(
                    "inference_ms_per_attempt"
                )
        if value is not None:
            inference.append(float(value))
    return {
        "parameters_mean": float(np.mean([row["trainable_parameters"] for row in manifests])),
        "training_seconds_mean": float(np.mean([row["training_seconds"] for row in manifests])),
        "inference_ms_per_attempt_mean": float(np.mean(inference)) if inference else None,
    }


def _metric_rows(
    project_root: Path,
    variant_id: str,
    variant: AblationVariant,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for benchmark in variant.benchmarks:
        result_dir = _result_dir(project_root, variant_id, benchmark)
        summary_path = result_dir / "metrics_summary.csv"
        if not summary_path.is_file():
            raise FileNotFoundError(f"Missing completed ablation summary: {summary_path}")
        frame = pd.read_csv(summary_path)
        if benchmark == "overall_binary_ternary":
            subsets = (
                ("binary", "direction_cardinality", 2),
                ("ternary", "direction_cardinality", 3),
                ("unseen_mixture", "direction", None),
            )
        elif benchmark == "unseen_component":
            subsets = (("unseen_component", "direction", None),)
        else:
            subsets = (("binary_to_ternary", "direction", None),)
        costs = _costs(result_dir)
        for subset, scope, component_count in subsets:
            for direction in ("isothermal", "isobaric"):
                selected = _select_summary(frame, scope, direction, component_count)
                observables = (
                    (("P", "pressure_system_macro_mae_kpa"), ("y", "y_system_macro_mae"))
                    if direction == "isothermal"
                    else (("T", "temperature_system_macro_mae_k"), ("y", "y_system_macro_mae"))
                )
                for observable, metric in observables:
                    rows.append(
                        {
                            "variant_id": variant_id,
                            "variant": variant.label,
                            "family": variant.family,
                            "benchmark": subset,
                            "direction": direction,
                            "component_count": component_count,
                            "observable": observable,
                            "system_macro_mae_mean": selected[f"{metric}_mean"],
                            "system_macro_mae_std": selected[f"{metric}_std"],
                            "available_seeds": int(selected[f"{metric}_available_seeds"]),
                            **costs,
                        }
                    )
    return rows


def architecture_and_physics_tables(project_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_rows = [
        row
        for variant_id, variant in ABLATION_VARIANTS.items()
        for row in _metric_rows(project_root, variant_id, variant)
    ]
    architecture = pd.DataFrame([row for row in all_rows if row["family"] == "architecture"])
    physics_ids = {"a0_full", "p3_no_pure_boundary", "p4_no_phase_continuity", "p6_no_soft_physics"}
    physics = pd.DataFrame([row for row in all_rows if row["variant_id"] in physics_ids])
    physics.loc[physics["variant_id"].eq("a0_full"), "physics_variant"] = "P0 Full physics"
    physics.loc[physics["variant_id"].eq("p3_no_pure_boundary"), "physics_variant"] = "P3 w/o near-pure boundary loss"
    physics.loc[physics["variant_id"].eq("p4_no_phase_continuity"), "physics_variant"] = "P4 w/o phase-continuity loss"
    physics.loc[physics["variant_id"].eq("p6_no_soft_physics"), "physics_variant"] = "P6 w/o all soft physics losses"
    not_applicable = pd.DataFrame(
        [
            {"variant_id": "p1_gibbs_duhem", "physics_variant": "P1 w/o Gibbs-Duhem only", "status": "not_applicable_hard_constraint"},
            {"variant_id": "p2_composition_conservation", "physics_variant": "P2 w/o composition conservation", "status": "not_applicable_hard_constraint"},
            {"variant_id": "p5_permutation_consistency", "physics_variant": "P5 w/o permutation consistency", "status": "not_applicable_hard_constraint"},
        ]
    )
    physics["status"] = "completed"
    physics = pd.concat([physics, not_applicable], ignore_index=True, sort=False)
    return architecture, physics


def physical_consistency_table(project_root: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for variant_id, variant in ABLATION_VARIANTS.items():
        if "overall_binary_ternary" not in variant.benchmarks:
            continue
        result_dir = _result_dir(project_root, variant_id, "overall_binary_ternary")
        payloads = []
        for seed in ABLATION_SEEDS:
            path = result_dir / f"seed_{seed}" / "physical_consistency.json"
            if not path.is_file():
                raise FileNotFoundError(f"Missing physical-consistency artifact: {path}")
            payloads.append(json.loads(path.read_text(encoding="utf-8")))
        row: dict[str, Any] = {
            "variant_id": variant_id,
            "variant": variant.label,
            "benchmark": "unseen_mixture",
            "seeds": len(payloads),
        }
        keys = sorted(
            {
                key
                for payload in payloads
                for key, value in payload.items()
                if isinstance(value, (int, float)) and not isinstance(value, bool)
            }
        )
        for key in keys:
            values = np.asarray(
                [float(payload[key]) for payload in payloads if payload.get(key) is not None],
                dtype=float,
            )
            row[f"{key}_mean"] = float(values.mean()) if values.size else None
            row[f"{key}_std"] = float(values.std(ddof=1)) if values.size > 1 else 0.0 if values.size else None
            row[f"{key}_available_seeds"] = int(values.size)
        rows.append(row)
    return pd.DataFrame(rows)


def _sample_errors(frame: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, row in frame.iterrows():
        count = int(row["component_count"])
        y_error = np.mean(
            [abs(float(row[f"y_pred_{index}"]) - float(row[f"y_true_{index}"])) for index in range(1, count + 1)]
        )
        if row["direction"] == "isothermal":
            primary = abs(float(row["predicted_pressure_kpa"]) - float(row["target_pressure_kpa"]))
            unit = "kPa"
        else:
            primary = abs(float(row["predicted_temperature_k"]) - float(row["target_temperature_k"]))
            unit = "K"
        records.append(
            {
                "sample_id": row["sample_id"],
                "system_id": row["system_id"],
                "direction": row["direction"],
                "binary_subsystem_coverage": int(row["binary_subsystem_coverage"]),
                "y_abs_error": y_error,
                "primary_abs_error": primary,
                "primary_unit": unit,
            }
        )
    return pd.DataFrame(records)


def manybody_system_effects(project_root: Path) -> pd.DataFrame:
    full_dir = _result_dir(project_root, "a0_full", "binary_to_ternary_zero_shot")
    pairwise_dir = _result_dir(project_root, "a3_pairwise_only", "binary_to_ternary_zero_shot")
    seed_rows = []
    for seed in ABLATION_SEEDS:
        full = _sample_errors(pd.read_csv(full_dir / f"seed_{seed}" / "predictions.csv"))
        pairwise = _sample_errors(pd.read_csv(pairwise_dir / f"seed_{seed}" / "predictions.csv"))
        identity = ["sample_id", "system_id", "direction", "binary_subsystem_coverage", "primary_unit"]
        merged = full.merge(pairwise, on=identity, suffixes=("_full", "_pairwise"), validate="one_to_one")
        grouped = merged.groupby(["system_id", "direction", "binary_subsystem_coverage", "primary_unit"], as_index=False).agg(
            full_y_mae=("y_abs_error_full", "mean"),
            pairwise_y_mae=("y_abs_error_pairwise", "mean"),
            full_primary_mae=("primary_abs_error_full", "mean"),
            pairwise_primary_mae=("primary_abs_error_pairwise", "mean"),
        )
        grouped["seed"] = seed
        seed_rows.append(grouped)
    all_seeds = pd.concat(seed_rows, ignore_index=True)
    grouped = all_seeds.groupby(
        ["system_id", "direction", "binary_subsystem_coverage", "primary_unit"], as_index=False
    ).agg(
        full_y_mae=("full_y_mae", "mean"),
        pairwise_y_mae=("pairwise_y_mae", "mean"),
        full_primary_mae=("full_primary_mae", "mean"),
        pairwise_primary_mae=("pairwise_primary_mae", "mean"),
        seeds=("seed", "nunique"),
    )
    grouped["delta_y_mae_pairwise_minus_full"] = grouped["pairwise_y_mae"] - grouped["full_y_mae"]
    grouped["delta_primary_mae_pairwise_minus_full"] = grouped["pairwise_primary_mae"] - grouped["full_primary_mae"]
    return grouped.sort_values(["binary_subsystem_coverage", "system_id", "direction"])


def _style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif"],
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 9,
            "legend.fontsize": 7,
            "legend.frameon": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 300,
            "savefig.dpi": 300,
        }
    )


def _save(figure: mpl.figure.Figure, stem: Path) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    outputs = []
    for suffix, options in (("pdf", {}), ("svg", {}), ("png", {"dpi": 300})):
        path = stem.with_suffix(f".{suffix}")
        temporary = path.parent / f".{path.stem}.{os.getpid()}.tmp.{suffix}"
        try:
            figure.savefig(temporary, bbox_inches="tight", pad_inches=0.04, **options)
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()
        outputs.append(path)
    plt.close(figure)
    return outputs


def _mean_value(table: pd.DataFrame, variant: str, benchmark: str, direction: str, observable: str) -> float:
    selected = table.loc[
        table["variant_id"].eq(variant)
        & table["benchmark"].eq(benchmark)
        & table["direction"].eq(direction)
        & table["observable"].eq(observable)
    ]
    return float(selected.iloc[0]["system_macro_mae_mean"]) if len(selected) == 1 else math.nan


def build_figures(
    output_dir: Path,
    architecture: pd.DataFrame,
    physics: pd.DataFrame,
    physical: pd.DataFrame,
    manybody: pd.DataFrame,
) -> list[Path]:
    _style()
    outputs: list[Path] = []
    core = ["a0_full", "a3_pairwise_only", "a2_no_interaction", "a6_direct_vle"]
    labels = ["Full", "Pairwise", "Independent", "Direct VLE"]
    colors = [COLORS["full"], COLORS["pairwise"], COLORS["independent"], COLORS["direct"]]
    figure, axes = plt.subplots(1, 3, figsize=(6.75, 2.35))
    for axis, direction, observable, title in zip(
        axes,
        ("isothermal", "isobaric", "isothermal"),
        ("P", "T", "y"),
        ("Ternary pressure", "Ternary temperature", "Ternary vapor composition"),
    ):
        values = [_mean_value(architecture, variant, "ternary", direction, observable) for variant in core]
        axis.bar(np.arange(len(core)), values, color=colors, width=0.68)
        axis.set_xticks(np.arange(len(core)), labels, rotation=25, ha="right")
        axis.set_title(title)
        axis.set_ylabel("System-wise MAE")
        axis.grid(axis="y", alpha=0.18)
    figure.tight_layout()
    outputs += _save(figure, output_dir / "architecture_ablation")

    physics_completed = physics.loc[physics["status"].eq("completed")]
    ids = ["a0_full", "p3_no_pure_boundary", "p4_no_phase_continuity", "p6_no_soft_physics"]
    figure, axes = plt.subplots(1, 2, figsize=(6.75, 2.5))
    predictive = [_mean_value(physics_completed, item, "unseen_mixture", "isothermal", "y") for item in ids]
    axes[0].bar(np.arange(len(ids)), predictive, color=[COLORS["full"], "#56B4E9", "#CC79A7", COLORS["other"]])
    axes[0].set_xticks(np.arange(len(ids)), ["P0", "P3", "P4", "P6"])
    axes[0].set_ylabel("System-wise y MAE")
    axes[0].set_title("Predictive accuracy")
    physical_indexed = physical.set_index("variant_id")
    inconsistency = [physical_indexed.loc[item, "nonphysical_prediction_rate_mean"] for item in ids]
    axes[1].bar(np.arange(len(ids)), inconsistency, color=[COLORS["full"], "#56B4E9", "#CC79A7", COLORS["other"]])
    axes[1].set_xticks(np.arange(len(ids)), ["P0", "P3", "P4", "P6"])
    axes[1].set_ylabel("Nonphysical prediction rate")
    axes[1].set_title("Physical consistency")
    for axis in axes:
        axis.grid(axis="y", alpha=0.18)
    figure.tight_layout()
    outputs += _save(figure, output_dir / "thermodynamic_ablation")

    figure, axes = plt.subplots(1, 3, figsize=(6.75, 2.35))
    merged = architecture.loc[
        architecture["benchmark"].eq("unseen_mixture")
        & architecture["direction"].eq("isothermal")
        & architecture["observable"].eq("y")
    ][["variant_id", "system_macro_mae_mean"]].merge(physical, on="variant_id")
    consistency_metrics = (
        "gibbs_duhem_mean_abs_mean",
        "permutation_y_max_abs_mean",
        "nonphysical_prediction_rate_mean",
    )
    titles = ("Gibbs-Duhem", "Permutation", "Nonphysical rate")
    for axis, metric, title in zip(axes, consistency_metrics, titles):
        selected = merged.dropna(subset=[metric])
        axis.scatter(selected["system_macro_mae_mean"], selected[metric], color=COLORS["full"], s=24)
        for _, row in selected.iterrows():
            axis.annotate(row["variant_id"].split("_")[0].upper(), (row["system_macro_mae_mean"], row[metric]), fontsize=6)
        axis.set_xlabel("System-wise y MAE")
        axis.set_ylabel(title)
        axis.grid(alpha=0.18)
    figure.tight_layout()
    outputs += _save(figure, output_dir / "accuracy_consistency_tradeoff")

    figure, axis = plt.subplots(figsize=(3.25, 2.55))
    group = manybody.groupby("binary_subsystem_coverage")[
        ["full_y_mae", "pairwise_y_mae"]
    ].mean()
    positions = np.arange(len(group))
    axis.bar(positions - 0.18, group["full_y_mae"], 0.36, label="Full", color=COLORS["full"])
    axis.bar(positions + 0.18, group["pairwise_y_mae"], 0.36, label="Pairwise", color=COLORS["pairwise"])
    axis.set_xticks(positions, [f"{int(value)}/3" for value in group.index])
    axis.set_xlabel("Binary subsystems observed in training")
    axis.set_ylabel("Ternary system-wise y MAE")
    axis.legend()
    axis.grid(axis="y", alpha=0.18)
    figure.tight_layout()
    outputs += _save(figure, output_dir / "binary_ternary_pairwise_vs_full")
    return outputs


def _fmt(value: float | None, digits: int = 4) -> str:
    return "not available" if value is None or not np.isfinite(value) else f"{value:.{digits}g}"


def write_report(
    path: Path,
    architecture: pd.DataFrame,
    physics: pd.DataFrame,
    physical: pd.DataFrame,
    manybody: pd.DataFrame,
) -> None:
    def value(variant: str, benchmark: str, direction: str, observable: str) -> float:
        return _mean_value(architecture, variant, benchmark, direction, observable)

    full_ternary_y = value("a0_full", "ternary", "isothermal", "y")
    pairwise_ternary_y = value("a3_pairwise_only", "ternary", "isothermal", "y")
    no_interaction_ternary_y = value("a2_no_interaction", "ternary", "isothermal", "y")
    direct_ternary_y = value("a6_direct_vle", "ternary", "isothermal", "y")
    rdkit_ternary_y = value("a1_rdkit_descriptors", "ternary", "isothermal", "y")
    direct_gamma_ternary_y = value("a5_direct_activity", "ternary", "isothermal", "y")
    delta = manybody["delta_y_mae_pairwise_minus_full"].to_numpy()
    wilcoxon = stats.wilcoxon(delta).pvalue if np.any(delta != 0.0) else 1.0
    physical_indexed = physical.set_index("variant_id")
    physics_complete = physics.loc[physics["status"].eq("completed")]
    full_unseen_y = value("a0_full", "unseen_mixture", "isothermal", "y")
    accuracy_changes = {}
    for variant in ("p3_no_pure_boundary", "p4_no_phase_continuity", "p6_no_soft_physics"):
        accuracy_changes[variant] = value(variant, "unseen_mixture", "isothermal", "y") - full_unseen_y
    largest_accuracy = max(accuracy_changes, key=lambda item: abs(accuracy_changes[item]))
    nonphysical_changes = {
        variant: physical_indexed.loc[variant, "nonphysical_prediction_rate_mean"]
        - physical_indexed.loc["a0_full", "nonphysical_prediction_rate_mean"]
        for variant in accuracy_changes
    }
    largest_physical = max(nonphysical_changes, key=lambda item: abs(nonphysical_changes[item]))
    lines = [
        "# ThermoFormer Ablation and Thermodynamic Consistency",
        "",
        "All comparisons use the committed main-experiment splits, preprocessing, seeds 0–4, training budget, and validation-only model-selection rule. No test set or hyperparameter was selected after viewing ablation results. P1, P2, and P5 are not independently run because Gibbs–Duhem consistency, composition closure, and permutation consistency are hard constructions; fabricating zero-signal losses would not be a scientific ablation.",
        "",
        "## Architectural ablation",
        "",
        "The primary ternary comparison uses system-wise vapor-composition MAE. State-variable P and T results remain separate in `results/ablation/architecture.csv`.",
        "",
        "| Variant | Ternary y MAE | Difference from Full |",
        "|---|---:|---:|",
        f"| Full | {_fmt(full_ternary_y)} | 0 |",
        f"| RDKit descriptors | {_fmt(rdkit_ternary_y)} | {_fmt(rdkit_ternary_y - full_ternary_y)} |",
        f"| No interaction | {_fmt(no_interaction_ternary_y)} | {_fmt(no_interaction_ternary_y - full_ternary_y)} |",
        f"| Pairwise-only | {_fmt(pairwise_ternary_y)} | {_fmt(pairwise_ternary_y - full_ternary_y)} |",
        f"| Condition concatenation | {_fmt(value('a4_condition_concatenation', 'ternary', 'isothermal', 'y'))} | {_fmt(value('a4_condition_concatenation', 'ternary', 'isothermal', 'y') - full_ternary_y)} |",
        f"| Direct activity | {_fmt(direct_gamma_ternary_y)} | {_fmt(direct_gamma_ternary_y - full_ternary_y)} |",
        f"| Direct VLE | {_fmt(direct_ternary_y)} | {_fmt(direct_ternary_y - full_ternary_y)} |",
        "",
        "## Thermodynamic-constraint ablation",
        "",
        "P1 is marked not applicable as a one-factor loss ablation because Gibbs–Duhem consistency is the hard excess-Gibbs construction. A5 changes that decoder and is reported only as an architectural intervention, not as an isolated P1 causal estimate. P3/P4 remove one soft loss; P6 removes all removable soft losses while retaining every hard equation and output constraint.",
        "",
        f"The largest absolute predictive change among removable/controlled physics variants is **{largest_accuracy}** (Δ system-wise isothermal y MAE {_fmt(accuracy_changes[largest_accuracy])}). The largest change in nonphysical prediction rate is **{largest_physical}** (Δ {_fmt(nonphysical_changes[largest_physical])}).",
        "",
        "## Many-body evidence",
        "",
        f"Across all coverage-stratified ternary system/direction rows, Pairwise−Full y MAE has mean **{_fmt(float(delta.mean()))}**, median **{_fmt(float(np.median(delta)))}**, and is positive for **{100.0 * float(np.mean(delta > 0.0)):.1f}%** of rows. A paired Wilcoxon signed-rank test gives **p={wilcoxon:.3g}**. The complete distribution, including negative cases, is retained in `results/ablation/manybody_system_effects.csv`.",
        "",
        "## Accuracy–consistency relationship",
        "",
        "The trade-off figure keeps predictive y MAE, Gibbs–Duhem residual, permutation error, and nonphysical rate as separate axes. A direct-VLE model has no activity coefficients, so Gibbs–Duhem and equilibrium-equation residuals are reported as not available rather than assigned zero.",
        "",
        "## Answers to the fixed questions",
        "",
        f"1. **Pretrained representation:** RDKit−Full ternary y MAE is {_fmt(rdkit_ternary_y - full_ternary_y)}; necessity is supported only if this degradation is positive and stable across seeds.",
        f"2. **Multicomponent interaction:** No-interaction−Full ternary y MAE is {_fmt(no_interaction_ternary_y - full_ternary_y)}.",
        f"3. **Full versus pairwise:** the system-level paired distribution above determines whether the gain is concentrated in ternary states; binary and ternary rows are both available in the architecture table.",
        f"4. **Latent nonideality bottleneck:** Direct-gamma−Full ternary y MAE is {_fmt(direct_gamma_ternary_y - full_ternary_y)}, together with the independently measured GD residual change.",
        f"5. **Thermodynamic versus direct decoding:** Direct-VLE−Full ternary y MAE is {_fmt(direct_ternary_y - full_ternary_y)}; unseen-component and binary-to-ternary rows plus physical metrics prevent a headline based on one test slice.",
        f"6. **Largest accuracy effect:** {largest_accuracy} under the fixed isothermal unseen-mixture y metric.",
        f"7. **Largest physical-validity effect:** {largest_physical} under the predeclared nonphysical-rate criterion.",
        "8. **Trade-off:** inspect `accuracy_consistency_tradeoff.*`; any accuracy gain accompanied by larger residual/rate is retained as a trade-off, not relabeled as an improvement.",
        f"9. **Many-body claim:** supported only to the degree quantified by the full paired distribution (mean Δ={_fmt(float(delta.mean()))}, p={wilcoxon:.3g}); no favorable-only systems were selected.",
        "10. **Placement:** Full/Pairwise/No-interaction/Direct-VLE and P6 belong in the main text; RDKit, condition concatenation, direct-gamma/A5, individual soft-loss removals, hard-constraint non-applicability, full physical metric definitions, and all per-system rows belong in SI.",
        "",
        "## Scope and negative results",
        "",
        "Conclusions remain limited to binary/ternary low-pressure VLE below 500 kPa. Missing observables, failed solves, negative deltas, and non-monotonic outcomes are preserved. The absent `reports/model_comparison_report.md` was not used as evidence.",
    ]
    _atomic_write_text(path, "\n".join(lines) + "\n")


def _write_variant_pages(project_root: Path, architecture: pd.DataFrame) -> None:
    for variant_id, variant in ABLATION_VARIANTS.items():
        page = project_root / variant.config
        page = page.parent / "results.md"
        rows = architecture.loc[architecture["variant_id"].eq(variant_id)]
        lines = [f"# {variant.label}", "", "Status: **completed formal five-seed ablation**.", ""]
        if variant.reference:
            lines[2] = "Status: **immutable reference reused from completed formal runs**."
        lines += [
            "| Benchmark | Direction | Observable | System-wise MAE (mean ± SD) | Seeds |",
            "|---|---|---|---:|---:|",
        ]
        for _, row in rows.iterrows():
            lines.append(
                f"| {row['benchmark']} | {row['direction']} | {row['observable']} | "
                f"{row['system_macro_mae_mean']:.5g} ± {row['system_macro_mae_std']:.3g} | {int(row['available_seeds'])} |"
            )
        lines += ["", "Full machine-readable results: `results/ablation/architecture.csv` and `results/ablation/physical_consistency.csv`."]
        _atomic_write_text(page, "\n".join(lines) + "\n")


def build_ablation_outputs(project_root: Path = PROJECT_ROOT) -> dict[str, list[str]]:
    project_root = project_root.resolve()
    result_dir = project_root / "results" / "ablation"
    figure_dir = project_root / "figures" / "ablation"
    result_dir.mkdir(parents=True, exist_ok=True)
    architecture, physics = architecture_and_physics_tables(project_root)
    physical = physical_consistency_table(project_root)
    manybody = manybody_system_effects(project_root)
    _atomic_to_csv(architecture, result_dir / "architecture.csv")
    _atomic_to_csv(physics, result_dir / "physics.csv")
    _atomic_to_csv(physical, result_dir / "physical_consistency.csv")
    _atomic_to_csv(manybody, result_dir / "manybody_system_effects.csv")
    figures = build_figures(figure_dir, architecture, physics, physical, manybody)
    report_path = project_root / "reports" / "ablation_report.md"
    write_report(report_path, architecture, physics, physical, manybody)
    _write_variant_pages(project_root, architecture)
    return {
        "tables": [str(result_dir / name) for name in ("architecture.csv", "physics.csv", "physical_consistency.csv", "manybody_system_effects.csv")],
        "figures": [str(path) for path in figures],
        "reports": [str(project_root / "reports" / "constraint_audit.md"), str(report_path)],
    }
