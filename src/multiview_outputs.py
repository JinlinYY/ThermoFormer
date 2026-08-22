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
    for variant_id in ("v0_legacy_unimol", *FORMAL_VARIANTS):
        for protocol in FORMAL_PROTOCOLS:
            directory = (
                root / "results" / protocol
                if variant_id == "v0_legacy_unimol"
                else root / "results" / "multiview" / "formal" / "runs"
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
    report_variants = ("v0_legacy_unimol", *FORMAL_VARIANTS)
    for variant_id in report_variants:
        for protocol in FORMAL_PROTOCOLS:
            directory = (
                root / "results" / protocol
                if variant_id == "v0_legacy_unimol"
                else root / "results" / "multiview" / "formal" / "runs"
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
    expected = len(report_variants) * len(FORMAL_PROTOCOLS) * len(MULTIVIEW_SEEDS) * 2
    if len(output) != expected:
        raise ValueError(f"Expected {expected} formal seed-direction rows, found {len(output)}")
    observed_seeds = set(output["seed"].unique())
    if observed_seeds != set(MULTIVIEW_SEEDS):
        raise ValueError(f"Formal seed coverage mismatch: {sorted(observed_seeds)}")
    return output


def formal_cost_table(root: Path) -> pd.DataFrame:
    """Aggregate runtime cost without mixing it into predictive metrics."""
    rows = []
    for variant_id in ("v0_legacy_unimol", *FORMAL_VARIANTS):
        values = []
        for protocol in FORMAL_PROTOCOLS:
            for seed in MULTIVIEW_SEEDS:
                directory = _seed_dir(root, "formal", variant_id, protocol, seed)
                manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
                values.append(
                    {
                        "training_seconds": manifest["training_seconds"],
                        "trainable_parameters": manifest["trainable_parameters"],
                        "peak_gpu_memory_mb": manifest["peak_gpu_memory_mb"],
                    }
                )
        frame = pd.DataFrame(values)
        rows.append(
            {
                "variant_id": variant_id,
                "variant": MULTIVIEW_VARIANTS[variant_id].label,
                "runs": len(frame),
                "trainable_parameters": int(frame["trainable_parameters"].iloc[0]),
                "training_seconds_mean": frame["training_seconds"].mean(),
                "training_seconds_std": frame["training_seconds"].std(ddof=1),
                "peak_gpu_memory_mb_mean": frame["peak_gpu_memory_mb"].mean(),
                "peak_gpu_memory_mb_max": frame["peak_gpu_memory_mb"].max(),
            }
        )
    return pd.DataFrame(rows)


def gate_summary_table(root: Path) -> pd.DataFrame:
    source = root / "results" / "multiview" / "analysis" / "multiview_gate_statistics.csv"
    frame = pd.read_csv(source)
    output = (
        frame.loc[frame["scope"].eq("global")]
        .groupby(["protocol", "view"], as_index=False)
        .agg(
            mean_weight=("mean_weight", "mean"),
            seed_std=("mean_weight", "std"),
            seeds=("seed", "nunique"),
        )
    )
    if not output["seeds"].eq(len(MULTIVIEW_SEEDS)).all():
        raise ValueError("Gate summary does not contain all formal seeds")
    return output


def write_variant_result_pages(
    root: Path,
    screening: pd.DataFrame,
    formal: pd.DataFrame | None = None,
) -> list[Path]:
    """Keep experiment pages synchronized with machine-readable results."""
    outputs = []
    for variant_id, variant in MULTIVIEW_VARIANTS.items():
        path = root / Path(variant.config).parent / "results.md"
        if variant_id == "v0_legacy_unimol":
            status = "frozen five-seed legacy reference; reused without retraining"
            table = (
                formal.loc[formal["variant_id"].eq(variant_id)]
                if formal is not None
                else screening.loc[screening["variant_id"].eq(variant_id)]
            )
        elif formal is not None and variant_id in set(FORMAL_VARIANTS):
            status = "completed formal evaluation (seeds 0--4)"
            table = formal.loc[formal["variant_id"].eq(variant_id)]
        elif variant_id in set(SCREENING_VARIANTS):
            status = "completed seed-0 screening only"
            table = screening.loc[screening["variant_id"].eq(variant_id)]
        elif variant_id == "v2_unimol_only":
            status = "not retrained; interface-equivalent to V0"
            table = pd.DataFrame()
        else:
            status = "implemented but not selected by the locked staged protocol"
            table = pd.DataFrame()
        lines = [f"# {variant_id} results", "", f"Status: {status}.", ""]
        if not table.empty:
            lines.extend(
                [
                    "| Protocol | Task | State MAE | y MAE | Coverage |",
                    "|---|---|---:|---:|---:|",
                ]
            )
            for _, row in table.iterrows():
                unit = " kPa" if row["state"] == "P" else " K"
                if "state_mae_mean" in row.index:
                    state = f"{_fmt(row['state_mae_mean'])} ± {_fmt(row['state_mae_std'])}{unit}"
                    y_value = f"{_fmt(row['y_mae_mean'])} ± {_fmt(row['y_mae_std'])}"
                    coverage = f"{_fmt(row['valid_coverage_mean'], 3)} ± {_fmt(row['valid_coverage_std'], 3)}"
                else:
                    state = f"{_fmt(row['state_mae'])}{unit}"
                    y_value = _fmt(row["y_mae"])
                    coverage = _fmt(row["valid_coverage"], 3)
                lines.append(
                    f"| {row['protocol']} | {row['direction']} ({row['state']}+y) | "
                    f"{state} | {y_value} | {coverage} |"
                )
        lines.extend(["", "Machine-readable source: `results/multiview/`.", ""])
        _atomic_text(path, "\n".join(lines))
        outputs.append(path)
    return outputs


def write_final_report(
    root: Path,
    screening: pd.DataFrame,
    formal: pd.DataFrame,
    formal_seeds: pd.DataFrame,
    costs: pd.DataFrame,
    gates: pd.DataFrame,
) -> Path:
    output = root / "reports" / "multiview_thermoformer_report.md"
    lines = [
        "# Multi-view ThermoFormer report",
        "",
        "## 1. Implementation summary",
        "",
        "The frozen thermodynamic backbone is unchanged: pair interactions still form `sum(x_i x_j phi_ij)`, activity coefficients still come from composition autograd, and the same differentiable isothermal/isobaric solvers and physics losses are used.",
        "",
        "V6 uses 24 train-only-standardized RDKit descriptors, 768 frozen Uni-Mol v2 features, and 28 audited SMARTS occurrence counts (820 raw features total). Independent view projections feed the existing mixture Transformer; three symmetric pair branches and a mixture/state-conditioned softmax gate form `phi_ij`. No additional GNN was introduced.",
        "",
        "New modules/assets are under `src/multiview_*`, `assets/`, `scripts/*multiview*`, and `experiments/multiview/`; runner/config/model/representation/provenance seams were extended without changing committed splits.",
        "",
        "| Variant | Parameters | Formal runs | Train seconds/run | Peak GPU MB mean / max |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, row in costs.iterrows():
        lines.append(
            f"| {row['variant']} | {int(row['trainable_parameters']):,} | {int(row['runs'])} | "
            f"{_fmt(row['training_seconds_mean'], 1)} ± {_fmt(row['training_seconds_std'], 1)} | "
            f"{_fmt(row['peak_gpu_memory_mb_mean'], 1)} / {_fmt(row['peak_gpu_memory_mb_max'], 1)} |"
        )
    lines.extend([
        "",
        "## 2. Representation ablation",
        "",
        "V0--V6 are implemented. V2 is interface-equivalent to V0 and V3 is an implemented functional-group-only control; the locked screening matrix evaluated V0/V1/V4/V5/V6, so V2/V3 are not assigned invented performance. Full seed-0 tables are in `reports/multiview_screening_report.md`.",
        "",
        "Screening showed V1 strongest on unseen components; V4 and V5 degraded that primary target, so simple feature addition was insufficient. V6 improved selected overall/zero-shot directions but did not pass the unseen-component gate. Per the preregistered rule, no further V6 branch ablations were run because V6 had no clear primary-target benefit.",
        "",
        "## 3. Overall performance",
        "",
        "| Variant | Protocol | Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | Coverage |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
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
            "| Protocol | View | Mean weight across seeds | Seed SD |",
            "|---|---|---:|---:|",
        ]
    )
    for _, row in gates.iterrows():
        lines.append(
            f"| {row['protocol']} | {row['view']} | {_fmt(row['mean_weight'], 4)} | "
            f"{_fmt(row['seed_std'], 4)} |"
        )
    lines.extend(
        [
            "",
            "The gate largely collapsed onto RDKit (about 0.95 overall and 0.92 for unseen components); functional-group weights remained small and Uni-Mol was usually near zero. Zero-shot was seed-unstable: seed 4 switched to approximately 0.93 Uni-Mol while the other seeds were nearly all RDKit. These are learned associations, not causal feature importance. Full chemical-family and composition-region strata are in `results/multiview/analysis/multiview_gate_statistics.csv`.",
            "",
            "## 7. Conclusion",
            "",
            "1. **Why RDKit can beat Uni-Mol-only:** the compact descriptors expose molecular size, polarity, hydrogen bonding, topology and charge in a low-data-friendly form. Formally, V1 improved unseen-component P/T and isobaric y over V0, although V0 retained better isothermal y.",
            "2. **Does Uni-Mol add robust value on top of RDKit?** Not for the primary target in the tested fusion schemes. V4 screening and V5/V6 formal unseen-component results were worse than V1.",
            "3. **Do functional-group interactions improve unseen components?** No. V5 degraded all four primary MAE outputs relative to V1; V6 also remained worse, and its learned functional-group gate weight was small.",
            "4. **Is interaction-specific fusion better than naive concatenation?** Only conditionally. V6 improved V5's overall isothermal P/y, but it was worse on unseen-component P/T and did not beat V5 zero-shot. It also used more parameters and roughly doubled training time.",
            "5. **Should V6 replace ThermoFormer?** No. The preregistered primary objective failed and seed variance increased. V1 is the preferred candidate when unseen-component state prediction is primary; retain V0 when isothermal vapor-composition accuracy is paramount, and V5 when fixed-molecule binary-to-ternary transfer is the sole target. No single model dominates every task.",
        ]
    )
    _atomic_text(output, "\n".join(lines) + "\n")
    return output
