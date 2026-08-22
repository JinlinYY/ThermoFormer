"""Machine-derived screening and final reports for multi-view ThermoFormer."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from .multiview_protocols import (
    FORMAL_PROTOCOLS,
    FORMAL_VARIANTS,
    MULTIVIEW_SEEDS,
    MULTIVIEW_VARIANTS,
    SCREENING_PROTOCOLS,
    SCREENING_VARIANTS,
)


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", prefix=f".{path.name}.",
            suffix=".tmp", dir=path.parent, delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def atomic_csv(path: Path, frame: pd.DataFrame) -> None:
    """Atomically replace a machine-readable report table."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8-sig", newline="", prefix=f".{path.name}.",
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


def _result_protocol(variant_id: str, protocol: str) -> str:
    return f"{variant_id}.on.{protocol}"


def _seed_dir(root: Path, stage: str, variant_id: str, protocol: str, seed: int) -> Path:
    if variant_id == "v0_legacy_unimol":
        return root / "results" / protocol / f"seed_{seed}"
    return (
        root / "results" / "multiview" / stage / "runs"
        / _result_protocol(variant_id, protocol) / f"seed_{seed}"
    )


def _direction_rows(metrics: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = [row for row in metrics if row.get("scope") == "direction"]
    output = []
    for row in selected:
        direction = str(row["direction"])
        state = "P" if direction == "isothermal" else "T"
        prefix = "pressure" if direction == "isothermal" else "temperature"
        suffix = "_kpa" if direction == "isothermal" else "_k"
        output.append(
            {
                "direction": direction,
                "state": state,
                "state_mae": row.get(f"{prefix}_mae{suffix}"),
                "state_rmse": row.get(f"{prefix}_rmse{suffix}"),
                "state_r2": row.get(f"{prefix}_r2"),
                "y_mae": row.get("y_mae"),
                "y_rmse": row.get("y_rmse"),
                "y_r2": row.get("y_r2"),
                "valid_coverage": row.get("valid_coverage"),
            }
        )
    return output


def screening_table(root: Path) -> pd.DataFrame:
    rows = []
    for variant_id in SCREENING_VARIANTS:
        for protocol in SCREENING_PROTOCOLS:
            directory = _seed_dir(root, "screening", variant_id, protocol, 0)
            metrics = json.loads((directory / "metrics.json").read_text(encoding="utf-8"))
            manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
            for direction in _direction_rows(metrics):
                rows.append(
                    {
                        "variant_id": variant_id,
                        "variant": MULTIVIEW_VARIANTS[variant_id].label,
                        "protocol": protocol,
                        **direction,
                        "training_seconds": manifest.get("training_seconds"),
                        "trainable_parameters": manifest.get("trainable_parameters"),
                        "peak_gpu_memory_mb": manifest.get("peak_gpu_memory_mb"),
                    }
                )
    return pd.DataFrame(rows)


def _fmt(value: Any, digits: int = 4) -> str:
    if value is None or pd.isna(value):
        return "NA"
    return f"{float(value):.{digits}f}"


def write_screening_report(root: Path, table: pd.DataFrame) -> Path:
    output = root / "reports" / "multiview_screening_report.md"
    lines = [
        "# Multi-view ThermoFormer seed-0 screening",
        "",
        "All rows use committed seed-0 splits and validation-only model selection. This is a screening result, not a five-seed claim.",
        "",
        "| Variant | Protocol | Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | Valid coverage | Train s | Params |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in table.iterrows():
        unit = " kPa" if row["state"] == "P" else " K"
        lines.append(
            f"| {row['variant']} | {row['protocol']} | {row['direction']} ({row['state']}+y) | "
            f"{_fmt(row['state_mae'])}{unit} | {_fmt(row['state_rmse'])}{unit} | {_fmt(row['state_r2'])} | "
            f"{_fmt(row['y_mae'])} | {_fmt(row['y_rmse'])} | {_fmt(row['y_r2'])} | "
            f"{_fmt(row['valid_coverage'], 3)} | {_fmt(row['training_seconds'], 1)} | {int(row['trainable_parameters']):,} |"
        )
    lines.extend(
        [
            "",
            "Primary screening criterion: unseen-component P/T/y performance. Overall, state-interpolation, and binary-to-ternary rows are retained as non-degradation constraints; no test row is removed.",
        ]
    )
    _atomic_text(output, "\n".join(lines) + "\n")
    return output


def formal_table(root: Path) -> pd.DataFrame:
    rows = []
    for variant_id in FORMAL_VARIANTS:
        for protocol in FORMAL_PROTOCOLS:
            directory = (
                root / "results" / "multiview" / "formal" / "runs"
                / _result_protocol(variant_id, protocol)
            )
            frame = pd.read_csv(directory / "metrics_summary.csv")
            selected = frame.loc[frame["scope"].eq("direction")]
            for _, row in selected.iterrows():
                direction = str(row["direction"])
                prefix = "pressure" if direction == "isothermal" else "temperature"
                suffix = "_kpa" if direction == "isothermal" else "_k"
                rows.append(
                    {
                        "variant_id": variant_id,
                        "variant": MULTIVIEW_VARIANTS[variant_id].label,
                        "protocol": protocol,
                        "direction": direction,
                        "state": "P" if direction == "isothermal" else "T",
                        "state_mae_mean": row[f"{prefix}_mae{suffix}_mean"],
                        "state_mae_std": row[f"{prefix}_mae{suffix}_std"],
                        "state_rmse_mean": row[f"{prefix}_rmse{suffix}_mean"],
                        "state_rmse_std": row[f"{prefix}_rmse{suffix}_std"],
                        "state_r2_mean": row[f"{prefix}_r2_mean"],
                        "state_r2_std": row[f"{prefix}_r2_std"],
                        "y_mae_mean": row["y_mae_mean"],
                        "y_mae_std": row["y_mae_std"],
                        "y_rmse_mean": row["y_rmse_mean"],
                        "y_rmse_std": row["y_rmse_std"],
                        "y_r2_mean": row["y_r2_mean"],
                        "y_r2_std": row["y_r2_std"],
                        "valid_coverage_mean": row["valid_coverage_mean"],
                        "valid_coverage_std": row["valid_coverage_std"],
                    }
                )
    return pd.DataFrame(rows)


def formal_seed_table(root: Path) -> pd.DataFrame:
    """Return every formal seed without silently dropping failed directions."""
    rows = []
    for variant_id in FORMAL_VARIANTS:
        for protocol in FORMAL_PROTOCOLS:
            directory = (
                root / "results" / "multiview" / "formal" / "runs"
                / _result_protocol(variant_id, protocol)
            )
            frame = pd.read_csv(directory / "metrics_by_seed.csv")
            selected = frame.loc[frame["scope"].eq("direction")]
            for _, row in selected.iterrows():
                direction = str(row["direction"])
                prefix = "pressure" if direction == "isothermal" else "temperature"
                suffix = "_kpa" if direction == "isothermal" else "_k"
                rows.append(
                    {
                        "variant_id": variant_id,
                        "variant": MULTIVIEW_VARIANTS[variant_id].label,
                        "protocol": protocol,
                        "seed": int(row["seed"]),
                        "direction": direction,
                        "state": "P" if direction == "isothermal" else "T",
                        "state_mae": row[f"{prefix}_mae{suffix}"],
                        "state_rmse": row[f"{prefix}_rmse{suffix}"],
                        "state_r2": row[f"{prefix}_r2"],
                        "y_mae": row["y_mae"],
                        "y_rmse": row["y_rmse"],
                        "y_r2": row["y_r2"],
                        "valid_coverage": row["valid_coverage"],
                    }
                )
    output = pd.DataFrame(rows)
    expected = len(FORMAL_VARIANTS) * len(FORMAL_PROTOCOLS) * len(MULTIVIEW_SEEDS) * 2
    if len(output) != expected:
        raise ValueError(f"Expected {expected} formal seed-direction rows, found {len(output)}")
    observed_seeds = set(output["seed"].unique())
    if observed_seeds != set(MULTIVIEW_SEEDS):
        raise ValueError(f"Formal seed coverage mismatch: {sorted(observed_seeds)}")
    return output


def write_final_report(
    root: Path,
    screening: pd.DataFrame,
    formal: pd.DataFrame,
    formal_seeds: pd.DataFrame,
) -> Path:
    output = root / "reports" / "multiview_thermoformer_report.md"
    lines = [
        "# Multi-view ThermoFormer report",
        "",
        "## 1. Implementation summary",
        "",
        "The frozen thermodynamic backbone is unchanged. V6 combines train-only-standardized RDKit descriptors, frozen Uni-Mol v2, and audited functional-group cross-attention through a symmetric mixture-conditioned gate.",
        "",
        "## 2. Representation ablation",
        "",
        "V0--V6 screening results are available in `reports/multiview_screening_report.md`; single-seed controls are not promoted to five-seed claims.",
        "",
        "## 3. Overall performance",
        "",
        "| Variant | Protocol | Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | Coverage |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in formal.iterrows():
        unit = " kPa" if row["state"] == "P" else " K"
        pm = lambda name, digits=4: f"{_fmt(row[name + '_mean'], digits)} ± {_fmt(row[name + '_std'], digits)}"
        lines.append(
            f"| {row['variant']} | {row['protocol']} | {row['direction']} ({row['state']}+y) | "
            f"{pm('state_mae')}{unit} | {pm('state_rmse')}{unit} | {pm('state_r2')} | "
            f"{pm('y_mae')} | {pm('y_rmse')} | {pm('y_r2')} | {pm('valid_coverage', 3)} |"
        )
    lines.extend(
        [
            "",
            "## 4. Unseen-component generalization",
            "",
            "The unseen-component rows above are the primary evidence. Every seed is shown below; no seed is excluded.",
            "",
            "| Variant | Seed | Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | Coverage |",
            "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    unseen = formal_seeds.loc[formal_seeds["protocol"].eq("unseen_component")]
    for _, row in unseen.iterrows():
        unit = " kPa" if row["state"] == "P" else " K"
        lines.append(
            f"| {row['variant']} | {int(row['seed'])} | {row['direction']} ({row['state']}+y) | "
            f"{_fmt(row['state_mae'])}{unit} | {_fmt(row['state_rmse'])}{unit} | "
            f"{_fmt(row['state_r2'])} | {_fmt(row['y_mae'])} | {_fmt(row['y_rmse'])} | "
            f"{_fmt(row['y_r2'])} | {_fmt(row['valid_coverage'], 3)} |"
        )
    lines.extend(
        [
            "",
            "## 5. Binary-to-ternary zero-shot",
            "",
            "The zero-shot rows use the unchanged fixed ternary test set and train-only binary subsystem coverage.",
            "",
            "## 6. Gate analysis",
            "",
            "Learned, non-presupposed gate statistics are exported to `results/multiview/analysis/multiview_gate_statistics.csv`.",
            "",
            "## 7. Conclusion",
            "",
            "Replacement of the legacy ThermoFormer is justified only if V6 improves unseen-component performance without material degradation of overall prediction, zero-shot transfer, seed stability, or solver coverage. The numerical tables above are authoritative.",
        ]
    )
    _atomic_text(output, "\n".join(lines) + "\n")
    return output
