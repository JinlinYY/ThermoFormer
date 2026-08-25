"""Build paper-facing ThermoFormer tables, figures, and formal result reports."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Callable, Iterable, NamedTuple, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .data import VLESample, load_vle_samples
from .splits import sample_id, system_id


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MM_TO_INCH = 1.0 / 25.4
COLORS = {
    "binary": "#3B6FB6",
    "ternary": "#D97736",
    "interpolation": "#3A8D77",
    "mixture": "#7566A8",
    "component": "#C44E52",
    "grey": "#6F6F6F",
}

PROTOCOL_CONFIGS = {
    "overall_binary": "experiments/predictive_performance/overall_binary/config.json",
    "overall_binary_ternary": "experiments/predictive_performance/overall_binary_ternary/config.json",
    "state_composition_interpolation": "experiments/interpolation_extrapolation/state/composition_interpolation/config.json",
    "state_composition_edge_extrapolation": "experiments/interpolation_extrapolation/state/composition_edge_extrapolation/config.json",
    "state_temperature_low_extrapolation": "experiments/interpolation_extrapolation/state/temperature_low_extrapolation/config.json",
    "state_temperature_high_extrapolation": "experiments/interpolation_extrapolation/state/temperature_high_extrapolation/config.json",
    "state_pressure_low_extrapolation": "experiments/interpolation_extrapolation/state/pressure_low_extrapolation/config.json",
    "state_pressure_high_extrapolation": "experiments/interpolation_extrapolation/state/pressure_high_extrapolation/config.json",
    "unseen_component": "experiments/interpolation_extrapolation/chemical_space/unseen_component/config.json",
    "binary_to_ternary_zero_shot": "experiments/comparison/binary_to_ternary_generalization/zero_shot/config.json",
    "binary_to_ternary_scale_0.05": "experiments/comparison/binary_to_ternary_generalization/scaling/percent_05/config.json",
    "binary_to_ternary_scale_0.1": "experiments/comparison/binary_to_ternary_generalization/scaling/percent_10/config.json",
    "binary_to_ternary_scale_0.25": "experiments/comparison/binary_to_ternary_generalization/scaling/percent_25/config.json",
    "binary_to_ternary_scale_0.5": "experiments/comparison/binary_to_ternary_generalization/scaling/percent_50/config.json",
    "binary_to_ternary_scale_1": "experiments/comparison/binary_to_ternary_generalization/scaling/percent_100/config.json",
}

STATE_PROTOCOLS = (
    ("state_composition_interpolation", "State interpolation"),
    ("state_composition_edge_extrapolation", "Composition edge"),
    ("state_temperature_low_extrapolation", "Low temperature"),
    ("state_temperature_high_extrapolation", "High temperature"),
    ("state_pressure_low_extrapolation", "Low pressure"),
    ("state_pressure_high_extrapolation", "High pressure"),
)

SCALING_PROTOCOLS = (
    ("binary_to_ternary_zero_shot", 0.0, "0%"),
    ("binary_to_ternary_scale_0.05", 1.0 / 18.0, "5.56%"),
    ("binary_to_ternary_scale_0.1", 0.1, "10%"),
    ("binary_to_ternary_scale_0.25", 0.25, "25%"),
    ("binary_to_ternary_scale_0.5", 0.5, "50%"),
    ("binary_to_ternary_scale_1", 1.0, "100%"),
)

METRICS = (
    "pressure_mae_kpa",
    "pressure_rmse_kpa",
    "pressure_r2",
    "pressure_system_macro_mae_kpa",
    "temperature_mae_k",
    "temperature_rmse_k",
    "temperature_r2",
    "temperature_system_macro_mae_k",
    "y_mae",
    "y_rmse",
    "y_r2",
    "y_system_macro_mae",
    "y_component_macro_mae",
    "valid_coverage",
    "solver_failure_rate",
    "nonphysical_rate",
    "attempted_samples",
    "systems",
)


class MetricSection(NamedTuple):
    title: str
    page_label: str
    unit: str
    mae: str
    rmse: str
    r2: str
    table_error_digits: int
    table_r2_digits: int
    page_error_digits: int
    page_r2_digits: int


METRIC_SECTIONS = (
    MetricSection(
        "Pressure metrics",
        "pressure",
        "kPa",
        "pressure_mae_kpa",
        "pressure_rmse_kpa",
        "pressure_r2",
        2,
        3,
        3,
        4,
    ),
    MetricSection(
        "Temperature metrics",
        "temperature",
        "K",
        "temperature_mae_k",
        "temperature_rmse_k",
        "temperature_r2",
        2,
        3,
        3,
        4,
    ),
    MetricSection(
        "Vapor-composition metrics",
        "vapor composition",
        "",
        "y_mae",
        "y_rmse",
        "y_r2",
        4,
        3,
        4,
        4,
    ),
)
PRESSURE_METRICS, TEMPERATURE_METRICS, VAPOR_COMPOSITION_METRICS = METRIC_SECTIONS


class PredictionTask(NamedTuple):
    direction: str
    title: str
    known_inputs: str
    joint_outputs: str
    state_quantity: str
    state_metrics: MetricSection


PREDICTION_TASKS = (
    PredictionTask(
        "isothermal",
        "Isothermal P–x–y",
        "Molecules, T, x",
        "Bubble pressure P and vapor composition y",
        "Bubble pressure P",
        PRESSURE_METRICS,
    ),
    PredictionTask(
        "isobaric",
        "Isobaric T–x–y",
        "Molecules, P, x",
        "Bubble temperature T and vapor composition y",
        "Bubble temperature T",
        TEMPERATURE_METRICS,
    ),
)


def _set_plot_style() -> None:
    available = {font.name for font in mpl.font_manager.fontManager.ttflist}
    family = next(
        (name for name in ("Arial", "Helvetica", "DejaVu Sans") if name in available),
        "sans-serif",
    )
    mpl.rcParams.update(
        {
            "font.family": family,
            "font.size": 7.2,
            "axes.labelsize": 7.5,
            "axes.titlesize": 8.0,
            "axes.linewidth": 0.65,
            "xtick.labelsize": 6.6,
            "ytick.labelsize": 6.6,
            "legend.fontsize": 6.4,
            "legend.frameon": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def _clean_axis(axis: mpl.axes.Axes) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.grid(axis="y", color="#E8E8E8", linewidth=0.45, zorder=0)


def _save_figure(figure: mpl.figure.Figure, stem: Path) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for suffix, options in (("pdf", {}), ("svg", {}), ("png", {"dpi": 600})):
        output = stem.with_suffix(f".{suffix}")
        figure.savefig(output, bbox_inches="tight", pad_inches=0.035, **options)
        outputs.append(output)
    plt.close(figure)
    return outputs


def read_summary(results_root: Path, protocol: str) -> pd.DataFrame:
    path = results_root / protocol / "metrics_summary.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Missing formal summary: {path}")
    return pd.read_csv(path)


def select_metric_row(
    frame: pd.DataFrame,
    scope: str,
    *,
    component_count: int | None = None,
    direction: str | None = None,
    subgroup: str | None = None,
) -> pd.Series:
    """Select exactly one aggregate metric identity from a summary table."""
    selected = frame.loc[frame["scope"].eq(scope)]
    conditions = (
        ("component_count", component_count),
        ("direction", direction),
        ("subgroup", subgroup),
    )
    for field, value in conditions:
        if value is None:
            selected = selected.loc[selected[field].isna()]
        elif field == "component_count":
            selected = selected.loc[pd.to_numeric(selected[field], errors="coerce").eq(float(value))]
        else:
            selected = selected.loc[selected[field].astype(str).eq(str(value))]
    if len(selected) != 1:
        raise ValueError(
            f"Expected one metric row for {(scope, direction, component_count, subgroup)}, "
            f"found {len(selected)}"
        )
    return selected.iloc[0]


def metric_record(
    results_root: Path,
    protocol: str,
    label: str,
    *,
    scope: str = "all",
    component_count: int | None = None,
    direction: str | None = None,
    subgroup: str | None = None,
) -> dict[str, Any]:
    row = select_metric_row(
        read_summary(results_root, protocol),
        scope,
        component_count=component_count,
        direction=direction,
        subgroup=subgroup,
    )
    record: dict[str, Any] = {
        "protocol": protocol,
        "test_subset": label,
        "scope": scope,
        "component_count": component_count,
        "direction": direction,
        "subgroup": subgroup,
        "requested_seeds": int(row["seeds"]),
        "scope_available_seeds": int(row["scope_available_seeds"]),
        "scope_seed_ids": str(row["scope_seed_ids"]),
    }
    for metric in METRICS:
        for suffix in ("mean", "std", "available_seeds", "seed_ids"):
            field = f"{metric}_{suffix}"
            record[field] = row.get(field, np.nan)
    return record


def _prediction_frame(results_root: Path, protocol: str) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for seed in range(5):
        path = results_root / protocol / f"seed_{seed}" / "predictions.csv"
        frame = pd.read_csv(path)
        frame.insert(0, "seed", seed)
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def _component_label(row: pd.Series) -> str:
    values = [
        str(row.get(f"component_smiles_{index}"))
        for index in range(1, int(row["component_count"]) + 1)
    ]
    return " | ".join(values)


def _sample_y_error(row: pd.Series) -> float:
    errors = []
    for index in range(1, int(row["component_count"]) + 1):
        actual = row.get(f"y_true_{index}")
        predicted = row.get(f"y_pred_{index}")
        if pd.notna(actual) and pd.notna(predicted):
            errors.append(abs(float(predicted) - float(actual)))
    return float(np.mean(errors)) if errors else math.nan


def system_extremes(predictions: pd.DataFrame) -> pd.DataFrame:
    """Return best/worst system-level errors separately in physical units."""
    frame = predictions.copy()
    frame["pressure_abs_error_kpa"] = (
        frame["predicted_pressure_kpa"] - frame["target_pressure_kpa"]
    ).abs()
    frame["temperature_abs_error_k"] = (
        frame["predicted_temperature_k"] - frame["target_temperature_k"]
    ).abs()
    frame["y_abs_error"] = frame.apply(_sample_y_error, axis=1)
    frame["components"] = frame.apply(_component_label, axis=1)
    rows: list[dict[str, Any]] = []
    for metric in (
        "pressure_abs_error_kpa",
        "temperature_abs_error_k",
        "y_abs_error",
    ):
        grouped = (
            frame.groupby(["system_id", "component_count", "components"], as_index=False)[metric]
            .mean()
            .dropna(subset=[metric])
            .sort_values(metric)
        )
        count = min(5, len(grouped))
        for rank, (_, row) in enumerate(grouped.head(count).iterrows(), start=1):
            rows.append({"metric": metric, "extreme": "best", "rank": rank, **row.to_dict()})
        for rank, (_, row) in enumerate(
            grouped.tail(count).sort_values(metric, ascending=False).iterrows(), start=1
        ):
            rows.append({"metric": metric, "extreme": "worst", "rank": rank, **row.to_dict()})
    return pd.DataFrame(rows)


def bin_extrapolation_distances(frame: pd.DataFrame, bins: int = 5) -> pd.DataFrame:
    """Quantile-bin extrapolation distances without mixing physical error units."""
    valid = frame.loc[frame["normalized_distance"].notna()].copy()
    if valid.empty:
        return valid
    number = min(bins, len(valid))
    valid["distance_bin"] = pd.qcut(
        valid["normalized_distance"].rank(method="first"),
        q=number,
        labels=False,
    )
    aggregated = (
        valid.groupby("distance_bin", as_index=False)
        .agg(
            samples=("sample_id", "size"),
            distance_mean=("distance", "mean"),
            distance_min=("distance", "min"),
            distance_max=("distance", "max"),
            normalized_distance_mean=("normalized_distance", "mean"),
            pressure_mae_kpa=("pressure_abs_error_kpa", "mean"),
            temperature_mae_k=("temperature_abs_error_k", "mean"),
            y_mae=("y_abs_error", "mean"),
        )
    )
    return aggregated


def extrapolation_distance_table(
    project_root: Path,
    results_root: Path,
) -> pd.DataFrame:
    samples = load_vle_samples(project_root / "dataset", max_pressure_kpa=500.0)
    by_id = {sample_id(sample): sample for sample in samples}
    definitions: tuple[tuple[str, str, str, Callable[[VLESample], float]], ...] = (
        (
            "state_composition_edge_extrapolation",
            "composition_edge",
            "mole_fraction",
            lambda sample: min(sample.liquid_composition),
        ),
        (
            "state_temperature_low_extrapolation",
            "temperature_low",
            "K",
            lambda sample: sample.temperature_k,
        ),
        (
            "state_temperature_high_extrapolation",
            "temperature_high",
            "K",
            lambda sample: sample.temperature_k,
        ),
        (
            "state_pressure_low_extrapolation",
            "pressure_low",
            "kPa",
            lambda sample: sample.pressure_kpa,
        ),
        (
            "state_pressure_high_extrapolation",
            "pressure_high",
            "kPa",
            lambda sample: sample.pressure_kpa,
        ),
    )
    outputs: list[pd.DataFrame] = []
    for protocol, label, unit, feature in definitions:
        rows: list[dict[str, Any]] = []
        for seed in range(5):
            split = json.loads(
                (project_root / "splits" / protocol / f"seed_{seed}.json").read_text(
                    encoding="utf-8"
                )
            )
            train_ranges: dict[str, list[float]] = {}
            for identifier in split["partitions"]["train"]:
                sample = by_id[identifier]
                train_ranges.setdefault(system_id(sample), []).append(feature(sample))
            predictions = pd.read_csv(
                results_root / protocol / f"seed_{seed}" / "predictions.csv"
            )
            for _, prediction in predictions.iterrows():
                sample = by_id[str(prediction["sample_id"])]
                values = train_ranges.get(str(prediction["system_id"]))
                if not values:
                    continue
                lower, upper = min(values), max(values)
                value = feature(sample)
                distance = max(lower - value, value - upper, 0.0)
                span = upper - lower
                rows.append(
                    {
                        "sample_id": prediction["sample_id"],
                        "seed": seed,
                        "distance": distance,
                        "normalized_distance": distance / span if span > 0.0 else math.nan,
                        "pressure_abs_error_kpa": abs(
                            float(prediction["predicted_pressure_kpa"])
                            - float(prediction["target_pressure_kpa"])
                        )
                        if pd.notna(prediction["target_pressure_kpa"])
                        else math.nan,
                        "temperature_abs_error_k": abs(
                            float(prediction["predicted_temperature_k"])
                            - float(prediction["target_temperature_k"])
                        )
                        if pd.notna(prediction["target_temperature_k"])
                        else math.nan,
                        "y_abs_error": _sample_y_error(prediction),
                    }
                )
        binned = bin_extrapolation_distances(pd.DataFrame(rows))
        binned.insert(0, "distance_unit", unit)
        binned.insert(0, "extrapolation_axis", label)
        binned.insert(0, "protocol", protocol)
        outputs.append(binned)
    return pd.concat(outputs, ignore_index=True)


def _plot_parity(
    predictions: pd.DataFrame,
    actual_field: str,
    predicted_field: str,
    label: str,
    stem: Path,
) -> list[Path]:
    frame = predictions.dropna(subset=[actual_field, predicted_field])
    figure, axis = plt.subplots(figsize=(88 * MM_TO_INCH, 75 * MM_TO_INCH))
    for count, name, color, marker in (
        (2, "Binary", COLORS["binary"], "o"),
        (3, "Ternary", COLORS["ternary"], "^"),
    ):
        values = frame.loc[frame["component_count"].eq(count)]
        axis.scatter(
            values[actual_field],
            values[predicted_field],
            s=5,
            alpha=0.22,
            linewidths=0,
            color=color,
            marker=marker,
            label=f"{name} (n={len(values):,})",
            rasterized=True,
        )
    lower = float(min(frame[actual_field].min(), frame[predicted_field].min()))
    upper = float(max(frame[actual_field].max(), frame[predicted_field].max()))
    axis.plot([lower, upper], [lower, upper], color="#333333", lw=0.8, ls="--")
    axis.set(xlabel=f"Experimental {label}", ylabel=f"Predicted {label}")
    axis.set_xlim(lower, upper)
    axis.set_ylim(lower, upper)
    axis.legend(loc="upper left")
    axis.set_aspect("equal", adjustable="box")
    _clean_axis(axis)
    figure.tight_layout()
    return _save_figure(figure, stem)


def _long_y(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, sample in predictions.iterrows():
        for index in range(1, int(sample["component_count"]) + 1):
            rows.append(
                {
                    "component_count": int(sample["component_count"]),
                    "y_true": sample[f"y_true_{index}"],
                    "y_pred": sample[f"y_pred_{index}"],
                }
            )
    return pd.DataFrame(rows)


def _plot_error_distribution(predictions: pd.DataFrame, stem: Path) -> list[Path]:
    data = predictions.copy()
    data["P"] = (data["predicted_pressure_kpa"] - data["target_pressure_kpa"]).abs()
    data["T"] = (data["predicted_temperature_k"] - data["target_temperature_k"]).abs()
    data["y"] = data.apply(_sample_y_error, axis=1)
    figure, axes = plt.subplots(1, 3, figsize=(180 * MM_TO_INCH, 58 * MM_TO_INCH))
    labels = (("P", "Absolute pressure error (kPa)"), ("T", "Absolute temperature error (K)"), ("y", "Absolute vapor-composition error"))
    for axis, (field, xlabel) in zip(axes, labels):
        for count, name, color in ((2, "Binary", COLORS["binary"]), (3, "Ternary", COLORS["ternary"])):
            values = data.loc[data["component_count"].eq(count), field].dropna().sort_values().to_numpy()
            if values.size:
                axis.plot(values, np.arange(1, len(values) + 1) / len(values), color=color, lw=1.25, label=name)
        axis.set(xlabel=xlabel, ylabel="Empirical cumulative probability")
        axis.set_ylim(0, 1.01)
        _clean_axis(axis)
    axes[0].legend(loc="lower right")
    figure.tight_layout(w_pad=2.0)
    return _save_figure(figure, stem)


def _plot_difficulty_ladder(records: pd.DataFrame, stem: Path) -> list[Path]:
    figure, axes = plt.subplots(1, 3, figsize=(180 * MM_TO_INCH, 62 * MM_TO_INCH))
    definitions = (
        ("pressure_mae_kpa", "Pressure MAE (kPa)"),
        ("temperature_mae_k", "Temperature MAE (K)"),
        ("y_mae", "Vapor-composition MAE"),
    )
    colors = [COLORS["interpolation"], COLORS["mixture"], COLORS["component"]]
    for axis, (metric, ylabel) in zip(axes, definitions):
        means = records[f"{metric}_mean"].astype(float).to_numpy()
        stds = records[f"{metric}_std"].astype(float).to_numpy()
        positions = np.arange(len(records))
        axis.bar(positions, means, yerr=stds, color=colors, width=0.68, capsize=2.0, linewidth=0, zorder=2)
        axis.set_xticks(positions, ["State\ninterpolation", "Unseen\nmixture", "Unseen\ncomponent"])
        axis.set_ylabel(ylabel)
        _clean_axis(axis)
    figure.tight_layout(w_pad=2.0)
    return _save_figure(figure, stem)


def _plot_state_generalization(
    state: pd.DataFrame,
    distances: pd.DataFrame,
    stem: Path,
) -> list[Path]:
    figure, axes = plt.subplots(2, 3, figsize=(180 * MM_TO_INCH, 120 * MM_TO_INCH))
    definitions = (
        ("pressure_mae_kpa", "Pressure MAE (kPa)"),
        ("temperature_mae_k", "Temperature MAE (K)"),
        ("y_mae", "Vapor-composition MAE"),
    )
    colors = plt.get_cmap("viridis")(np.linspace(0.12, 0.88, len(state)))
    short_labels = ("Interp.", "Comp. edge", "T low", "T high", "P low", "P high")
    for column, (metric, ylabel) in enumerate(definitions):
        axis = axes[0, column]
        means = state[f"{metric}_mean"].astype(float).to_numpy()
        stds = state[f"{metric}_std"].astype(float).to_numpy()
        positions = np.arange(len(state))
        axis.bar(positions, means, yerr=stds, color=colors, capsize=1.8, width=0.72, linewidth=0)
        axis.set_xticks(positions, short_labels, rotation=28, ha="right")
        axis.set_ylabel(ylabel)
        _clean_axis(axis)

        distance_axis = axes[1, column]
        for index, (protocol, group) in enumerate(distances.groupby("protocol", sort=False)):
            distance_axis.plot(
                group["normalized_distance_mean"],
                group[metric],
                marker="o",
                ms=2.8,
                lw=1.0,
                color=colors[min(index + 1, len(colors) - 1)],
                label=group["extrapolation_axis"].iloc[0].replace("_", " "),
            )
        distance_axis.set(xlabel="Normalized extrapolation distance", ylabel=ylabel)
        _clean_axis(distance_axis)
    axes[1, 2].legend(loc="upper left", bbox_to_anchor=(1.02, 1.02))
    figure.tight_layout(w_pad=2.0, h_pad=2.0)
    return _save_figure(figure, stem)


def _plot_binary_to_ternary(
    scaling: pd.DataFrame,
    coverage: pd.DataFrame,
    stem: Path,
) -> list[Path]:
    figure, axes = plt.subplots(2, 2, figsize=(130 * MM_TO_INCH, 112 * MM_TO_INCH))
    definitions = (
        ("pressure_mae_kpa", "Pressure MAE (kPa)"),
        ("temperature_mae_k", "Temperature MAE (K)"),
        ("y_mae", "Vapor-composition MAE"),
    )
    positions = np.arange(len(scaling), dtype=float)
    for axis, (metric, ylabel) in zip(axes.flat[:3], definitions):
        means = scaling[f"{metric}_mean"].astype(float).to_numpy()
        stds = scaling[f"{metric}_std"].astype(float).to_numpy()
        axis.errorbar(positions, means, yerr=stds, color=COLORS["ternary"], marker="o", ms=3.2, lw=1.1, capsize=2.0)
        axis.set(xlabel="Ternary training fraction (discrete systems)", ylabel=ylabel)
        axis.set_xticks(positions, scaling["fraction_label"], rotation=25, ha="right")
        _clean_axis(axis)

    axis = axes[1, 1]
    widths = 0.34
    positions = np.arange(4)
    for offset, protocol, label, color in (
        (-widths / 2, "binary_to_ternary_zero_shot", "0%", COLORS["binary"]),
        (widths / 2, "binary_to_ternary_scale_1", "100%", COLORS["ternary"]),
    ):
        group = coverage.loc[coverage["protocol"].eq(protocol)].sort_values("covered_binary_subsystems")
        axis.bar(
            positions + offset,
            group["y_mae_mean"].astype(float),
            yerr=group["y_mae_std"].astype(float),
            width=widths,
            color=color,
            capsize=1.8,
            label=label,
        )
    axis.set_xticks(positions, ["0/3", "1/3", "2/3", "3/3"])
    axis.set(xlabel="Binary subsystems observed in training", ylabel="Vapor-composition MAE")
    axis.legend(title="Ternary supervision")
    _clean_axis(axis)
    figure.tight_layout(w_pad=2.0, h_pad=2.0)
    return _save_figure(figure, stem)


def _format(mean: Any, std: Any, digits: int = 3) -> str:
    if pd.isna(mean):
        return "not available"
    return f"{float(mean):.{digits}f} ± {float(std):.{digits}f}"


def _format_metric(row: pd.Series, metric: str, digits: int) -> str:
    rendered = _format(row[f"{metric}_mean"], row[f"{metric}_std"], digits)
    available = int(row.get(f"{metric}_available_seeds", 0))
    return f"{rendered} (n={available})"


def metric_markdown_tables(records: pd.DataFrame) -> str:
    """Render publication metrics without pooling unlike physical observables."""
    blocks: list[str] = []
    for section in METRIC_SECTIONS:
        unit_suffix = f" ({section.unit})" if section.unit else ""
        lines = [
            f"**{section.title}**",
            "",
            f"| Test subset | MAE{unit_suffix} | RMSE{unit_suffix} | R² |",
            "|---|---:|---:|---:|",
        ]
        for _, row in records.iterrows():
            lines.append(
                "| {label} | {mae} | {rmse} | {r2} |".format(
                    label=row["test_subset"],
                    mae=_format_metric(row, section.mae, section.table_error_digits),
                    rmse=_format_metric(row, section.rmse, section.table_error_digits),
                    r2=_format_metric(row, section.r2, section.table_r2_digits),
                )
            )
        blocks.append("\n".join(lines))

    coverage = [
        "**Prediction validity**",
        "",
        "| Test subset | Valid coverage |",
        "|---|---:|",
    ]
    for _, row in records.iterrows():
        coverage.append(
            f"| {row['test_subset']} | "
            f"{_format(row['valid_coverage_mean'], row['valid_coverage_std'], 4)} |"
        )
    blocks.append("\n".join(coverage))
    return "\n\n".join(blocks)


def task_metric_markdown(records: pd.DataFrame) -> str:
    """Render VLE performance by inference task and its coupled outputs."""
    blocks: list[str] = []
    task_by_direction = {task.direction: task for task in PREDICTION_TASKS}
    for _, row in records.iterrows():
        direction = str(row["direction"])
        if direction not in task_by_direction:
            raise ValueError(f"Unsupported prediction direction: {direction}")
        task = task_by_direction[direction]
        state = task.state_metrics
        vapor = VAPOR_COMPOSITION_METRICS
        blocks.append(
            "\n".join(
                [
                    f"### {row['test_subset']} — {task.title}",
                    "",
                    f"- Known inputs: **{task.known_inputs}**.",
                    f"- Joint prediction: **{task.joint_outputs}**.",
                    "",
                    "| Predicted quantity | MAE | RMSE | R² |",
                    "|---|---:|---:|---:|",
                    f"| {task.state_quantity} ({state.unit}) | "
                    f"{_format_metric(row, state.mae, state.table_error_digits)} | "
                    f"{_format_metric(row, state.rmse, state.table_error_digits)} | "
                    f"{_format_metric(row, state.r2, state.table_r2_digits)} |",
                    "| Vapor composition y | "
                    f"{_format_metric(row, vapor.mae, vapor.table_error_digits)} | "
                    f"{_format_metric(row, vapor.rmse, vapor.table_error_digits)} | "
                    f"{_format_metric(row, vapor.r2, vapor.table_r2_digits)} |",
                    "",
                    "Valid coverage: "
                    f"{_format(row['valid_coverage_mean'], row['valid_coverage_std'], 4)}.",
                ]
            )
        )
    return "\n\n".join(blocks)


def task_metric_records(
    results_root: Path,
    protocol: str,
    label: str,
    *,
    component_count: int | None = None,
) -> list[dict[str, Any]]:
    """Read both task directions for one protocol/test subset."""
    scope = "direction_cardinality" if component_count is not None else "direction"
    return [
        metric_record(
            results_root,
            protocol,
            label,
            scope=scope,
            component_count=component_count,
            direction=task.direction,
        )
        for task in PREDICTION_TASKS
    ]


def experiment_task_records(results_root: Path, protocol: str) -> list[dict[str, Any]]:
    """Return the task rows shown on one formal experiment result page."""
    if protocol == "overall_binary_ternary":
        return task_metric_records(
            results_root,
            protocol,
            "Joint model: binary test",
            component_count=2,
        ) + task_metric_records(
            results_root,
            protocol,
            "Joint model: ternary test",
            component_count=3,
        )
    return task_metric_records(results_root, protocol, protocol)


def task_metric_tables(results_root: Path) -> dict[str, pd.DataFrame]:
    """Assemble every machine-readable task table from direction-resolved metrics."""
    binary = pd.DataFrame(
        task_metric_records(
            results_root,
            "overall_binary",
            "Binary-only model: binary test",
        )
        + task_metric_records(
            results_root,
            "overall_binary_ternary",
            "Joint model: binary test",
            component_count=2,
        )
    )
    ternary = pd.DataFrame(
        task_metric_records(
            results_root,
            "overall_binary_ternary",
            "Joint model: ternary test",
            component_count=3,
        )
    )
    state = pd.DataFrame(
        [
            record
            for protocol, label in STATE_PROTOCOLS
            for record in task_metric_records(results_root, protocol, label)
        ]
    )
    difficulty = pd.DataFrame(
        task_metric_records(
            results_root,
            "state_composition_interpolation",
            "State interpolation",
        )
        + task_metric_records(
            results_root,
            "overall_binary_ternary",
            "Unseen mixture",
        )
        + task_metric_records(
            results_root,
            "unseen_component",
            "Unseen component",
        )
    )
    scaling_records: list[dict[str, Any]] = []
    for protocol, fraction, label in SCALING_PROTOCOLS:
        for record in task_metric_records(results_root, protocol, label):
            record["ternary_training_fraction"] = fraction
            record["fraction_label"] = label
            scaling_records.append(record)
    return {
        "binary": binary,
        "ternary": ternary,
        "state": state,
        "difficulty": difficulty,
        "scaling": pd.DataFrame(scaling_records),
    }


def _eligible_system_range(project_root: Path, protocol: str) -> str:
    values = []
    for seed in range(5):
        split = json.loads(
            (project_root / "splits" / protocol / f"seed_{seed}.json").read_text(encoding="utf-8")
        )
        systems = split["metadata"].get("systems", {}).get("test")
        if systems is not None:
            values.append(int(systems))
    if not values:
        return "not recorded"
    return str(values[0]) if len(set(values)) == 1 else f"{min(values)}–{max(values)}"


def write_predictive_report(
    project_root: Path,
    performance_tasks: pd.DataFrame,
    state_tasks: pd.DataFrame,
    difficulty_tasks: pd.DataFrame,
    scaling_tasks: pd.DataFrame,
) -> Path:
    path = project_root / "reports" / "predictive_performance_report.md"
    lines = [
        "# ThermoFormer Predictive Performance and Generalization",
        "",
        "Date: 2026-08-21. All confirmatory experiments use seeds 0–4, validation-only model selection, fixed committed splits, Uni-Mol v2 84M representations, and the differentiable mode-appropriate bubble solver. Values are mean ± sample standard deviation across seeds. Pressure, temperature, and composition errors are never combined into one scalar.",
        "",
        "## Prediction tasks and outputs",
        "",
        "ThermoFormer is evaluated as two coupled bubble-point tasks. A row does not predict only one scalar: each task jointly returns the unknown bubble-point state variable and the full vapor-composition vector.",
        "",
        "| Task | Known inputs | Joint prediction |",
        "|---|---|---|",
        "| Isothermal P–x–y | Molecules, T, liquid composition x | Bubble pressure P and vapor composition y |",
        "| Isobaric T–x–y | Molecules, P, liquid composition x | Bubble temperature T and vapor composition y |",
        "",
        "Full-state TP–x–y records are evaluated in both directions. Pressure metrics therefore use only isothermal solves, temperature metrics use only isobaric solves, and vapor-composition metrics are reported separately for each direction. The number in `(n=...)` is the actual number of contributing seeds.",
        "",
        "## Overall predictive performance",
        "",
        task_metric_markdown(performance_tasks),
        "",
        "The joint binary/ternary model is reported by cardinality and task direction rather than as one pooled headline. Independent activity-coefficient error is not reported because the workbooks do not provide a complete trusted pure-property reference needed to invert experimental gamma without reusing the model's learned Psat branch.",
        "",
        "## Thermodynamic-state interpolation and extrapolation",
        "",
        task_metric_markdown(state_tasks),
        "",
        "Eligible test-system counts are: "
        + "; ".join(
            f"{label}={_eligible_system_range(project_root, protocol)}"
            for protocol, label in STATE_PROTOCOLS
        )
        + ". Distance-binned results are stored in `results/generalization/extrapolation_distance.csv`; strict split audit confirms that extrapolation test states lie beyond both validation and training boundaries for each mixture.",
        "",
        "## Unseen mixtures and components",
        "",
        task_metric_markdown(difficulty_tasks),
        "",
        "The sharp degradation for held-out components is the clearest present limitation. System-disjoint unseen mixtures remain substantially easier when their constituent molecules have appeared elsewhere.",
        "",
        "## Binary-to-ternary transfer",
        "",
        task_metric_markdown(scaling_tasks),
        "",
        "The fixed-test scaling curve is non-monotonic. With only 18 candidate ternary training systems, subset identity and seed variability dominate several nominal fractions; added ternary labels do not consistently improve vapor-composition MAE over binary-only zero-shot transfer. This negative result is retained rather than smoothed or selectively reported.",
        "",
        "Coverage-controlled metrics for 0/3 through 3/3 observed binary subsystems are in `results/generalization/binary_subsystem_controlled.csv`. They use only binary systems present in the actual training partition when assigning coverage.",
        "",
        "## Solver validity and scope",
        "",
        "Most protocols have 100% valid coverage. High-pressure extrapolation and unseen-component tests contain small, explicitly reported failure fractions; failed rows remain in attempted-sample denominators. No nonphysical predictions were observed in aggregate summaries. The supported claim is limited to low-pressure binary and ternary VLE below the configured 500 kPa cutoff. There are no quaternary data or quaternary claims.",
        "",
        "## Recommendation",
        "",
        "Do not expand the architecture solely to improve the first formal metrics. First add strong thermodynamic and data-driven baselines on the identical committed splits, instrument per-objective gradient diagnostics during training, and investigate held-out-component representation/calibration and the non-monotonic ternary scaling subsets. Any method-changing modification should be proposed separately and preserve these first-round results.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_training_diagnosis(
    project_root: Path,
    results_root: Path,
    extremes: pd.DataFrame,
    performance: pd.DataFrame,
    difficulty: pd.DataFrame,
) -> Path:
    curve_rows: list[pd.DataFrame] = []
    nonfinite = 0
    physics_improved = 0
    supervised_stopped = 0
    validation_reductions: list[float] = []
    gaps: list[float] = []
    for protocol in PROTOCOL_CONFIGS:
        for seed in range(5):
            manifest = json.loads(
                (results_root / protocol / f"seed_{seed}" / "manifest.json").read_text(encoding="utf-8")
            )
            curves = pd.read_csv(Path(manifest["artifacts"]["training_curves"]["path"]))
            numeric = curves.select_dtypes(include=[np.number])
            nonfinite += int((~np.isfinite(numeric.to_numpy())).sum())
            experimental = curves.loc[curves["stage"].eq("experimental")]
            physics = curves.loc[curves["stage"].eq("physics")]
            if len(experimental) < 80:
                supervised_stopped += 1
            initial = float(experimental["validation_total"].iloc[0])
            best_index = experimental["validation_total"].astype(float).idxmin()
            best_validation = float(curves.loc[best_index, "validation_total"])
            best_train = float(curves.loc[best_index, "train_total"])
            validation_reductions.append(best_validation / initial)
            gaps.append(best_validation - best_train)
            if not physics.empty and float(physics["validation_total"].min()) < best_validation:
                physics_improved += 1
            curves.insert(0, "seed", seed)
            curves.insert(0, "protocol", protocol)
            curve_rows.append(curves)
    all_curves = pd.concat(curve_rows, ignore_index=True)
    physics_rows = all_curves.loc[all_curves["stage"].eq("physics")]
    solver_rates = []
    nonphysical_rates = []
    for protocol in PROTOCOL_CONFIGS:
        row = select_metric_row(read_summary(results_root, protocol), "all")
        solver_rates.append(float(row["solver_failure_rate_mean"]))
        nonphysical_rates.append(float(row["nonphysical_rate_mean"]))

    best_systems = extremes.loc[extremes["extreme"].eq("best") & extremes["rank"].eq(1)]
    worst_systems = extremes.loc[extremes["extreme"].eq("worst") & extremes["rank"].eq(1)]
    lines = [
        "# First Formal Training Diagnosis",
        "",
        "Date: 2026-08-21. This report supersedes the earlier single-seed pilot diagnosis. It summarizes 15 protocols × 5 seeds = 75 completed formal runs on an NVIDIA GeForce RTX 3090 Ti in `ggnn39`.",
        "",
        "## Convergence and numerical behavior",
        "",
        f"- Non-finite values in all recorded numeric training/validation curves: **{nonfinite}**.",
        f"- Median best/initial experimental validation-loss ratio: **{np.median(validation_reductions):.3f}** (lower is better).",
        f"- Median validation-minus-training total loss at the selected supervised epoch: **{np.median(gaps):.4f}**.",
        f"- Supervised early stopping before the 80-epoch ceiling occurred in **{supervised_stopped}/75** runs.",
        f"- Physics fine-tuning produced a lower experimental validation objective than the supervised best in **{physics_improved}/75** runs; otherwise the supervised checkpoint was retained as the valid epoch-0 candidate.",
        f"- Maximum protocol-mean solver failure rate: **{max(solver_rates):.4%}**; maximum protocol-mean nonphysical rate: **{max(nonphysical_rates):.4%}**.",
        "",
        "## Physics-loss and gradient scales",
        "",
        f"Across physics epochs, median raw continuity loss was **{physics_rows['train_continuity'].median():.3g}**; after the configured 1e-5 weight its median contribution was **{(1e-5 * physics_rows['train_continuity']).median():.3g}**. Median raw boundary loss was **{physics_rows['train_boundary'].median():.3g}** (weighted contribution **{(1e-3 * physics_rows['train_boundary']).median():.3g}**), and median raw differentiable-solver loss was **{physics_rows['train_solver'].median():.3g}** (weighted contribution **{(0.1 * physics_rows['train_solver']).median():.3g}**).",
        f"The recorded total pre-clipping gradient-norm mean was **{all_curves.loc[all_curves['stage'].eq('experimental'), 'train_gradient_norm_mean'].median():.3g}** in supervised epochs and **{physics_rows['train_gradient_norm_mean'].median():.3g}** in physics epochs. Historical runs did not record a separate gradient norm for each objective, so per-loss gradients cannot be reconstructed exactly from history alone; the weighted loss contributions above are not mislabeled as gradients. A future instrumentation-only run should record those norms explicitly.",
        "",
        "## Error gaps and capability boundaries",
        "",
        metric_markdown_tables(performance),
        "",
        metric_markdown_tables(difficulty),
        "",
        "The joint-model ternary subset is not uniformly harder than its binary subset, but the unseen-component protocol is dramatically harder than both state interpolation and system-disjoint unseen mixtures. Binary-to-ternary zero-shot transfer is viable on the fixed four-system test sets, whereas adding small ternary subsets gives a non-monotonic response.",
        "",
        "## Best and worst systems in the joint binary/ternary benchmark",
        "",
        "| Metric | Extreme | System | Components | Mean absolute error |",
        "|---|---|---|---|---:|",
    ]
    for extreme, table in (("best", best_systems), ("worst", worst_systems)):
        for _, row in table.iterrows():
            lines.append(
                f"| {row['metric']} | {extreme} | `{row['system_id']}` | `{row['components']}` | {float(row[row['metric']]):.5g} |"
            )
    lines.extend(
        [
            "",
            "## Diagnosis",
            "",
            "- **Data limitation:** only 18 ternary training systems are available for the scaling pool, so nominal fractions correspond to very small discrete subsets and strong selection variance.",
            "- **Optimization issue:** several scaling seeds degrade despite more ternary systems, suggesting multi-task/cardinality optimization conflict or sensitivity to subset composition; this should be tested before changing architecture.",
            "- **Architectural limitation:** the large unseen-component gap indicates that learned pure-property/nonideality extrapolation outside observed molecular support remains weak.",
            "- **Implementation bug:** no new bug is indicated by the formal runs; NaN checks, strict split audit, artifact hashes, solver convergence flags, and provenance gates behaved as designed.",
            "",
            "Recommendation: proceed first to baseline comparisons on the exact splits and add instrumentation/diagnostics. Do not add layers, hidden dimensions, or new loss terms solely in response to this first round. If a method change is later justified, write `reports/proposed_model_change.md` before implementation and retain these results as the unchanged reference.",
        ]
    )
    path = project_root / "reports" / "first_training_diagnosis.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_experiment_result_pages(
    project_root: Path,
    results_root: Path,
) -> None:
    for protocol, config in PROTOCOL_CONFIGS.items():
        pooled = metric_record(results_root, protocol, protocol)
        task_rows = pd.DataFrame(experiment_task_records(results_root, protocol))
        manifest = json.loads(
            (results_root / protocol / "aggregate_manifest.json").read_text(encoding="utf-8")
        )
        content = [
            f"# {protocol}",
            "",
            "Status: **completed formal five-seed experiment**.",
            "",
            f"- Seeds: `{','.join(str(value) for value in manifest['seeds'])}`",
            "",
            "## Task-resolved predictive performance",
            "",
            task_metric_markdown(task_rows),
            "",
        ]
        content.extend(
            [
                "## Provenance and pooled diagnostics",
                "",
                f"- Pooled solver failure rate: {_format(pooled['solver_failure_rate_mean'], pooled['solver_failure_rate_std'], 5)}",
                f"- Pooled nonphysical rate: {_format(pooled['nonphysical_rate_mean'], pooled['nonphysical_rate_std'], 5)}",
                f"- Training commit: `{manifest['training_git_commit']}`",
                f"- Aggregation commit: `{manifest['aggregation_git_commit']}`",
                f"- Formal summary: `results/{protocol}/metrics_summary.csv`",
                f"- Per-seed predictions: `results/{protocol}/seed_*/predictions.csv`",
                "",
                "These values are generated from committed fixed splits and should not be replaced by smoke or diagnostic runs.",
            ]
        )
        (project_root / config).parent.joinpath("results.md").write_text(
            "\n".join(content) + "\n", encoding="utf-8"
        )


def build_paper_outputs(project_root: Path = PROJECT_ROOT) -> dict[str, list[str]]:
    """Create all requested first-round tables, figures, and narrative reports."""
    project_root = project_root.resolve()
    results_root = project_root / "results"
    performance_dir = results_root / "performance"
    generalization_dir = results_root / "generalization"
    performance_dir.mkdir(parents=True, exist_ok=True)
    generalization_dir.mkdir(parents=True, exist_ok=True)
    _set_plot_style()

    binary_rows = pd.DataFrame(
        [
            metric_record(results_root, "overall_binary", "Binary-only model: binary test"),
            metric_record(
                results_root,
                "overall_binary_ternary",
                "Joint model: binary test",
                scope="cardinality",
                component_count=2,
            ),
        ]
    )
    ternary_rows = pd.DataFrame(
        [
            metric_record(
                results_root,
                "overall_binary_ternary",
                "Joint model: ternary test",
                scope="cardinality",
                component_count=3,
            )
        ]
    )
    binary_rows.to_csv(performance_dir / "binary_overall.csv", index=False)
    ternary_rows.to_csv(performance_dir / "ternary_overall.csv", index=False)

    task_tables = task_metric_tables(results_root)
    binary_tasks = task_tables["binary"]
    ternary_tasks = task_tables["ternary"]
    binary_tasks.to_csv(performance_dir / "binary_by_task.csv", index=False)
    ternary_tasks.to_csv(performance_dir / "ternary_by_task.csv", index=False)

    seed_frames = []
    for protocol in ("overall_binary", "overall_binary_ternary"):
        frame = pd.read_csv(results_root / protocol / "metrics_by_seed.csv")
        if protocol == "overall_binary":
            selected = frame.loc[frame["scope"].eq("all")].copy()
            selected["test_subset"] = "Binary-only model: binary test"
        else:
            selected = frame.loc[frame["scope"].eq("cardinality")].copy()
            selected["test_subset"] = selected["component_count"].map(
                {2.0: "Joint model: binary test", 3.0: "Joint model: ternary test"}
            )
        selected.insert(0, "protocol", protocol)
        seed_frames.append(selected)
    seed_summary = pd.concat(seed_frames, ignore_index=True)
    seed_summary.to_csv(performance_dir / "seed_summary.csv", index=False)

    state = pd.DataFrame(
        [metric_record(results_root, protocol, label) for protocol, label in STATE_PROTOCOLS]
    )
    state.iloc[[0]].to_csv(generalization_dir / "state_interpolation.csv", index=False)
    state.iloc[[1]].to_csv(generalization_dir / "composition_extrapolation.csv", index=False)
    state.iloc[[2, 3]].to_csv(generalization_dir / "temperature_extrapolation.csv", index=False)
    state.iloc[[4, 5]].to_csv(generalization_dir / "pressure_extrapolation.csv", index=False)
    state_tasks = task_tables["state"]
    state_tasks.to_csv(generalization_dir / "state_by_task.csv", index=False)

    difficulty = pd.DataFrame(
        [
            metric_record(results_root, "state_composition_interpolation", "State interpolation"),
            metric_record(results_root, "overall_binary_ternary", "Unseen mixture"),
            metric_record(results_root, "unseen_component", "Unseen component"),
        ]
    )
    difficulty.to_csv(generalization_dir / "unseen_mixture_component.csv", index=False)
    difficulty_tasks = task_tables["difficulty"]
    difficulty_tasks.to_csv(
        generalization_dir / "unseen_mixture_component_by_task.csv", index=False
    )

    scaling_records = []
    for protocol, fraction, label in SCALING_PROTOCOLS:
        record = metric_record(results_root, protocol, label)
        record["ternary_training_fraction"] = fraction
        record["fraction_label"] = label
        scaling_records.append(record)
    scaling = pd.DataFrame(scaling_records)
    scaling.to_csv(generalization_dir / "binary_to_ternary_scaling.csv", index=False)
    scaling_tasks = task_tables["scaling"]
    scaling_tasks.to_csv(
        generalization_dir / "binary_to_ternary_scaling_by_task.csv", index=False
    )

    coverage_rows = []
    for protocol in ("binary_to_ternary_zero_shot", "binary_to_ternary_scale_1"):
        for covered in range(4):
            record = metric_record(
                results_root,
                protocol,
                f"{covered}/3 binary subsystems observed",
                scope="binary_subsystem_coverage",
                subgroup=f"{covered}/3",
            )
            record["covered_binary_subsystems"] = covered
            coverage_rows.append(record)
    coverage = pd.DataFrame(coverage_rows)
    coverage.to_csv(generalization_dir / "binary_subsystem_controlled.csv", index=False)

    distances = extrapolation_distance_table(project_root, results_root)
    distances.to_csv(generalization_dir / "extrapolation_distance.csv", index=False)

    predictions = _prediction_frame(results_root, "overall_binary_ternary")
    extremes = system_extremes(predictions)
    extremes.to_csv(performance_dir / "system_extremes.csv", index=False)

    figure_paths: list[Path] = []
    figure_paths += _plot_parity(
        predictions,
        "target_temperature_k",
        "predicted_temperature_k",
        "temperature (K)",
        project_root / "figures" / "performance" / "parity_T",
    )
    figure_paths += _plot_parity(
        predictions,
        "target_pressure_kpa",
        "predicted_pressure_kpa",
        "pressure (kPa)",
        project_root / "figures" / "performance" / "parity_P",
    )
    y_values = _long_y(predictions)
    figure_paths += _plot_parity(
        y_values,
        "y_true",
        "y_pred",
        "vapor mole fraction",
        project_root / "figures" / "performance" / "parity_y",
    )
    figure_paths += _plot_error_distribution(
        predictions, project_root / "figures" / "performance" / "error_distribution"
    )
    figure_paths += _plot_difficulty_ladder(
        difficulty,
        project_root / "figures" / "generalization" / "generalization_difficulty_ladder",
    )
    figure_paths += _plot_state_generalization(
        state,
        distances,
        project_root / "figures" / "generalization" / "state_interpolation_extrapolation",
    )
    figure_paths += _plot_binary_to_ternary(
        scaling,
        coverage,
        project_root / "figures" / "generalization" / "binary_to_ternary_transfer",
    )

    performance = pd.concat([binary_rows, ternary_rows], ignore_index=True)
    performance_tasks = pd.concat([binary_tasks, ternary_tasks], ignore_index=True)
    report_paths = [
        write_predictive_report(
            project_root,
            performance_tasks,
            state_tasks,
            difficulty_tasks,
            scaling_tasks,
        ),
        write_training_diagnosis(
            project_root,
            results_root,
            extremes,
            performance,
            difficulty,
        ),
    ]
    _write_experiment_result_pages(project_root, results_root)
    table_paths = [
        performance_dir / "binary_overall.csv",
        performance_dir / "ternary_overall.csv",
        performance_dir / "binary_by_task.csv",
        performance_dir / "ternary_by_task.csv",
        performance_dir / "seed_summary.csv",
        performance_dir / "system_extremes.csv",
        generalization_dir / "state_interpolation.csv",
        generalization_dir / "composition_extrapolation.csv",
        generalization_dir / "temperature_extrapolation.csv",
        generalization_dir / "pressure_extrapolation.csv",
        generalization_dir / "state_by_task.csv",
        generalization_dir / "unseen_mixture_component.csv",
        generalization_dir / "unseen_mixture_component_by_task.csv",
        generalization_dir / "binary_to_ternary_scaling.csv",
        generalization_dir / "binary_to_ternary_scaling_by_task.csv",
        generalization_dir / "binary_subsystem_controlled.csv",
        generalization_dir / "extrapolation_distance.csv",
    ]
    return {
        "tables": [str(path) for path in table_paths],
        "figures": [str(path) for path in figure_paths],
        "reports": [str(path) for path in report_paths],
    }
