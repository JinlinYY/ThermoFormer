"""Build compact, publishable evidence from isolated multi-view smoke runs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.multiview_outputs import atomic_csv, atomic_text
from src.multiview_protocols import MULTIVIEW_VARIANTS, SMOKE_VARIANTS


def build_smoke_summary(root: Path) -> pd.DataFrame:
    rows = []
    for variant_id in SMOKE_VARIANTS:
        protocol = f"{variant_id}.on.overall_binary_ternary"
        run_dir = root / "runs" / "multiview" / "smoke" / protocol / "seed_0"
        result_dir = (
            root / "results" / "multiview" / "smoke" / "runs" / protocol / "seed_0"
        )
        history = json.loads((run_dir / "history.json").read_text(encoding="utf-8"))
        manifest = json.loads((result_dir / "manifest.json").read_text(encoding="utf-8"))
        metrics = json.loads((result_dir / "metrics.json").read_text(encoding="utf-8"))
        if manifest.get("status") != "smoke":
            raise RuntimeError(f"Not an isolated smoke manifest: {result_dir}")
        direction_rows = {
            str(row["direction"]): row
            for row in metrics
            if row.get("scope") == "direction"
        }
        totals = [float(epoch["train"]["total"]) for epoch in history]
        gradients = [float(epoch["train"]["gradient_norm_mean"]) for epoch in history]
        finite = all(
            pd.notna(value)
            for value in (
                *totals,
                *gradients,
                *[row.get("valid_coverage") for row in direction_rows.values()],
            )
        )
        rows.append(
            {
                "variant_id": variant_id,
                "variant": MULTIVIEW_VARIANTS[variant_id].label,
                "epochs": len(history),
                "train_loss_first": totals[0],
                "train_loss_last": totals[-1],
                "finite": finite,
                "gradient_norm_mean_last": gradients[-1],
                "isothermal_valid_coverage": direction_rows["isothermal"]["valid_coverage"],
                "isobaric_valid_coverage": direction_rows["isobaric"]["valid_coverage"],
                "training_seconds": manifest["training_seconds"],
                "peak_gpu_memory_mb": manifest["peak_gpu_memory_mb"],
                "trainable_parameters": manifest["trainable_parameters"],
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    table = build_smoke_summary(PROJECT_ROOT)
    csv_path = PROJECT_ROOT / "results" / "multiview" / "smoke_summary.csv"
    report_path = PROJECT_ROOT / "reports" / "multiview_smoke_report.md"
    atomic_csv(csv_path, table)
    lines = [
        "# Multi-view smoke-test report",
        "",
        "These seed-0, three-epoch runs are isolated numerical diagnostics. They are not performance estimates and were not aggregated with formal results.",
        "",
        "| Variant | Epochs | Train loss first → last | Finite | Last gradient norm | Solver coverage P / T | Train s | Peak GPU MB | Parameters |",
        "|---|---:|---:|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in table.iterrows():
        lines.append(
            f"| {row['variant']} | {int(row['epochs'])} | "
            f"{row['train_loss_first']:.4f} → {row['train_loss_last']:.4f} | "
            f"{bool(row['finite'])} | {row['gradient_norm_mean_last']:.4f} | "
            f"{row['isothermal_valid_coverage']:.3f} / {row['isobaric_valid_coverage']:.3f} | "
            f"{row['training_seconds']:.1f} | {row['peak_gpu_memory_mb']:.1f} | "
            f"{int(row['trainable_parameters']):,} |"
        )
    lines.extend([
        "",
        "The deliberately short solver evaluation used four iterations, so coverage is a stability signal only; the formal campaign used 48 iterations.",
        "",
    ])
    atomic_text(report_path, "\n".join(lines))
    print(json.dumps({"csv": str(csv_path), "report": str(report_path)}))


if __name__ == "__main__":
    main()
