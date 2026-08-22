"""Table-1-style predictive comparison for molecular representations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .multiview_outputs import atomic_text
from .multiview_protocols import (
    FORMAL_VARIANTS,
    MULTIVIEW_SEEDS,
    MULTIVIEW_VARIANTS,
    PREDICTIVE_VARIANTS,
)


PREDICTIVE_SETTINGS = (
    (
        "binary_train_binary_test",
        "Binary train → binary test",
        "overall_binary",
        "direction",
        None,
    ),
    (
        "joint_train_binary_test",
        "Binary+ternary train → binary test",
        "overall_binary_ternary",
        "direction_cardinality",
        2,
    ),
    (
        "joint_train_ternary_test",
        "Binary+ternary train → ternary test",
        "overall_binary_ternary",
        "direction_cardinality",
        3,
    ),
)
REPORT_VARIANTS = tuple(MULTIVIEW_VARIANTS)


def _result_protocol(variant_id: str, protocol: str) -> str:
    return f"{variant_id}.on.{protocol}"


def _summary_path(root: Path, variant_id: str, protocol: str) -> tuple[Path, str]:
    source_variant = "v0_legacy_unimol" if variant_id == "v2_unimol_only" else variant_id
    if source_variant == "v0_legacy_unimol":
        return root / "results" / protocol / "metrics_summary.csv", source_variant

    predictive = (
        root / "results" / "multiview" / "predictive" / "runs"
        / _result_protocol(source_variant, protocol) / "metrics_summary.csv"
    )
    if predictive.is_file():
        return predictive, source_variant
    if protocol == "overall_binary_ternary" and source_variant in FORMAL_VARIANTS:
        frozen = (
            root / "results" / "multiview" / "formal" / "runs"
            / _result_protocol(source_variant, protocol) / "metrics_summary.csv"
        )
        if frozen.is_file():
            return frozen, source_variant
    raise FileNotFoundError(
        f"Missing five-seed predictive summary for {variant_id}/{protocol}: {predictive}"
    )


def _select_row(
    frame: pd.DataFrame,
    scope: str,
    direction: str,
    component_count: int | None,
) -> pd.Series:
    selected = frame.loc[frame["scope"].eq(scope) & frame["direction"].eq(direction)]
    if component_count is not None:
        selected = selected.loc[selected["component_count"].eq(component_count)]
    if len(selected) != 1:
        raise ValueError(
            "Expected one predictive metric row for "
            f"scope={scope}, direction={direction}, component_count={component_count}; "
            f"found {len(selected)}"
        )
    return selected.iloc[0]


def _metric_fields(row: pd.Series, metric: str) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for suffix in ("mean", "std", "available_seeds", "seed_ids"):
        value = row[f"{metric}_{suffix}"]
        output[f"{metric}_{suffix}"] = value
    return output


def representation_predictive_table(root: Path) -> pd.DataFrame:
    """Load the three requested evaluation settings for V0--V6."""

    rows: list[dict[str, Any]] = []
    for variant_id in REPORT_VARIANTS:
        for setting_id, setting, protocol, scope, component_count in PREDICTIVE_SETTINGS:
            path, source_variant = _summary_path(root, variant_id, protocol)
            frame = pd.read_csv(path)
            for direction in ("isothermal", "isobaric"):
                metric_row = _select_row(frame, scope, direction, component_count)
                state_metric = "pressure" if direction == "isothermal" else "temperature"
                state_unit = "kPa" if direction == "isothermal" else "K"
                state_keys = (
                    ("pressure_mae_kpa", "pressure_rmse_kpa", "pressure_r2")
                    if direction == "isothermal"
                    else ("temperature_mae_k", "temperature_rmse_k", "temperature_r2")
                )
                row: dict[str, Any] = {
                    "variant_id": variant_id,
                    "variant": MULTIVIEW_VARIANTS[variant_id].label,
                    "source_variant_id": source_variant,
                    "independent_run": variant_id != "v2_unimol_only",
                    "setting_id": setting_id,
                    "evaluation_setting": setting,
                    "protocol": protocol,
                    "component_count": component_count,
                    "direction": direction,
                    "state": "P" if direction == "isothermal" else "T",
                    "state_metric": state_metric,
                    "state_unit": state_unit,
                    "source_summary": path.relative_to(root).as_posix(),
                }
                for metric in (*state_keys, "y_mae", "y_rmse", "y_r2", "valid_coverage"):
                    row.update(_metric_fields(metric_row, metric))
                rows.append(row)
    output = pd.DataFrame(rows)
    expected = len(REPORT_VARIANTS) * len(PREDICTIVE_SETTINGS) * 2
    if len(output) != expected:
        raise ValueError(f"Expected {expected} representation rows, found {len(output)}")
    return output


def _fmt(value: Any, digits: int) -> str:
    if value is None or pd.isna(value):
        return "NA"
    return f"{float(value):.{digits}f}"


def _metric_triplet(
    row: pd.Series,
    metrics: tuple[str, str, str],
    unit: str = "",
    digits: int = 4,
) -> str:
    counts = [int(row[f"{metric}_available_seeds"]) for metric in metrics]
    marker = "†" if min(counts) < len(MULTIVIEW_SEEDS) else ""
    unit_text = f" {unit}" if unit else ""
    mae, rmse, r2 = metrics
    return (
        f"{_fmt(row[f'{mae}_mean'], digits)} ± {_fmt(row[f'{mae}_std'], digits)}{unit_text}<br>"
        f"{_fmt(row[f'{rmse}_mean'], digits)} ± {_fmt(row[f'{rmse}_std'], digits)}{unit_text}<br>"
        f"{_fmt(row[f'{r2}_mean'], 3)} ± {_fmt(row[f'{r2}_std'], 3)}{marker}"
    )


def write_representation_report(root: Path, table: pd.DataFrame) -> Path:
    """Write the requested table without using unseen-component evaluation."""

    output = root / "reports" / "multiview_thermoformer_report.md"
    lines = [
        "# ThermoFormer molecular-representation comparison",
        "",
        "## Evaluation protocol",
        "",
        "This report uses only the requested Table-1-style settings: binary train → binary test, binary+ternary train → binary test, and binary+ternary train → ternary test. It does not use unseen-component ranking. All values are mean ± sample standard deviation across five fixed random seeds. Each metric cell lists MAE, RMSE, and R² from top to bottom; pressure and temperature errors use kPa and K, while vapor-composition errors are dimensionless.",
        "",
        "V2 is an explicit interface-equivalent alias of V0 and is shown for completeness, not counted as an independent experiment. A dagger marks a metric with fewer than five contributing seeds.",
        "",
        "## Predictive performance",
        "",
        "| Representation | Evaluation setting | P (kPa), isothermal | y, isothermal | T (K), isobaric | y, isobaric |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for variant_id in REPORT_VARIANTS:
        for setting_id, setting, *_ in PREDICTIVE_SETTINGS:
            subset = table.loc[
                table["variant_id"].eq(variant_id) & table["setting_id"].eq(setting_id)
            ]
            iso = subset.loc[subset["direction"].eq("isothermal")].iloc[0]
            isob = subset.loc[subset["direction"].eq("isobaric")].iloc[0]
            label = str(iso["variant"])
            if variant_id == "v2_unimol_only":
                label += " (alias of V0)"
            lines.append(
                f"| {label} | {setting} | {_metric_triplet(iso, ('pressure_mae_kpa', 'pressure_rmse_kpa', 'pressure_r2'), 'kPa', 2)} | "
                f"{_metric_triplet(iso, ('y_mae', 'y_rmse', 'y_r2'), '', 4)} | "
                f"{_metric_triplet(isob, ('temperature_mae_k', 'temperature_rmse_k', 'temperature_r2'), 'K', 2)} | "
                f"{_metric_triplet(isob, ('y_mae', 'y_rmse', 'y_r2'), '', 4)} |"
            )

    lines.extend([
        "",
        "## MAE winners by setting",
        "",
        "V2 is excluded from winner selection because it duplicates V0. Lower is better.",
        "",
        "| Evaluation setting | P winner | Isothermal y winner | T winner | Isobaric y winner |",
        "|---|---|---|---|---|",
    ])
    candidates = table.loc[table["independent_run"].astype(bool)]
    for setting_id, setting, *_ in PREDICTIVE_SETTINGS:
        subset = candidates.loc[candidates["setting_id"].eq(setting_id)]
        iso = subset.loc[subset["direction"].eq("isothermal")]
        isob = subset.loc[subset["direction"].eq("isobaric")]

        def winner(frame: pd.DataFrame, metric: str, digits: int, unit: str = "") -> str:
            row = frame.loc[frame[f"{metric}_mean"].idxmin()]
            unit_text = f" {unit}" if unit else ""
            return f"{row['variant']} ({_fmt(row[f'{metric}_mean'], digits)}{unit_text})"

        lines.append(
            f"| {setting} | {winner(iso, 'pressure_mae_kpa', 2, 'kPa')} | "
            f"{winner(iso, 'y_mae', 4)} | {winner(isob, 'temperature_mae_k', 2, 'K')} | "
            f"{winner(isob, 'y_mae', 4)} |"
        )
    lines.extend([
        "",
        "## Interpretation boundary",
        "",
        "The table supports comparisons only under these three grouped random-seed settings. It does not establish unseen-component extrapolation. The raw per-seed metrics, checkpoints, manifests, and resolved configurations remain the source of record under `results/`, `checkpoints/`, and `runs/`.",
        "",
    ])
    atomic_text(output, "\n".join(lines))
    return output


def write_variant_predictive_pages(root: Path, table: pd.DataFrame) -> list[Path]:
    outputs: list[Path] = []
    for variant_id in REPORT_VARIANTS:
        path = root / Path(MULTIVIEW_VARIANTS[variant_id].config).parent / "results.md"
        subset = table.loc[table["variant_id"].eq(variant_id)]
        status = (
            "reuses V0 exactly; no independent retraining"
            if variant_id == "v2_unimol_only"
            else "completed Table-1-style five-seed evaluation"
        )
        lines = [
            f"# {variant_id} results",
            "",
            f"Status: {status}.",
            "",
            "| Evaluation setting | Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
        for _, row in subset.iterrows():
            state_prefix = "pressure" if row["direction"] == "isothermal" else "temperature"
            metric_prefix = f"{state_prefix}_mae_{'kpa' if state_prefix == 'pressure' else 'k'}"
            rmse_prefix = f"{state_prefix}_rmse_{'kpa' if state_prefix == 'pressure' else 'k'}"
            unit = row["state_unit"]
            lines.append(
                f"| {row['evaluation_setting']} | {row['direction']} ({row['state']}+y) | "
                f"{_fmt(row[f'{metric_prefix}_mean'], 4)} ± {_fmt(row[f'{metric_prefix}_std'], 4)} {unit} | "
                f"{_fmt(row[f'{rmse_prefix}_mean'], 4)} ± {_fmt(row[f'{rmse_prefix}_std'], 4)} {unit} | "
                f"{_fmt(row[f'{state_prefix}_r2_mean'], 4)} ± {_fmt(row[f'{state_prefix}_r2_std'], 4)} | "
                f"{_fmt(row['y_mae_mean'], 4)} ± {_fmt(row['y_mae_std'], 4)} | "
                f"{_fmt(row['y_rmse_mean'], 4)} ± {_fmt(row['y_rmse_std'], 4)} | "
                f"{_fmt(row['y_r2_mean'], 4)} ± {_fmt(row['y_r2_std'], 4)} |"
            )
        lines.extend([
            "",
            "Machine-readable source: `results/multiview/predictive/representation_performance.csv`.",
            "",
        ])
        atomic_text(path, "\n".join(lines))
        outputs.append(path)
    return outputs
