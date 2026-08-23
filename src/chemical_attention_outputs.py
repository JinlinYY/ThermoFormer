"""Compact, provenance-backed pilot report for chemical attention variants."""

from __future__ import annotations

import csv
import json
import os
import tempfile
from pathlib import Path

from .artifacts import artifact_sha256
from .chemical_attention_protocols import (
    CHEMICAL_ATTENTION_PROTOCOLS,
    CHEMICAL_ATTENTION_VARIANTS,
)


METRICS = (
    ("pressure_mae_kpa_mean", "P MAE (kPa)"),
    ("pressure_rmse_kpa_mean", "P RMSE (kPa)"),
    ("pressure_r2_mean", "P R2"),
    ("temperature_mae_k_mean", "T MAE (K)"),
    ("temperature_rmse_k_mean", "T RMSE (K)"),
    ("temperature_r2_mean", "T R2"),
    ("y_mae_mean", "y MAE"),
    ("y_rmse_mean", "y RMSE"),
    ("y_r2_mean", "y R2"),
    ("valid_coverage_mean", "valid coverage"),
)


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _all_scope(summary_path: Path) -> dict[str, str]:
    with summary_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    matches = [row for row in rows if row.get("scope") == "all"]
    if len(matches) != 1:
        raise ValueError(f"Expected one all-scope row in {summary_path}, found {len(matches)}")
    return matches[0]


def collect_pilot_rows(project_root: Path) -> list[dict[str, object]]:
    result_root = (
        project_root
        / "results"
        / "multiview"
        / "chemical_attention"
        / "pilot"
        / "runs"
    )
    rows: list[dict[str, object]] = []
    for variant_id, variant in CHEMICAL_ATTENTION_VARIANTS.items():
        for protocol in CHEMICAL_ATTENTION_PROTOCOLS:
            run_name = f"{variant_id}.on.{protocol}"
            run_dir = result_root / run_name
            summary_path = run_dir / "diagnostic_metrics_summary.csv"
            manifest_path = run_dir / "seed_0" / "manifest.json"
            aggregate_path = run_dir / "diagnostic_aggregate_manifest.json"
            if (
                not summary_path.is_file()
                or not manifest_path.is_file()
                or not aggregate_path.is_file()
            ):
                raise FileNotFoundError(f"Incomplete pilot output: {run_dir}")
            aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))
            expected_manifest_sha = aggregate.get("input_manifest_sha256", {}).get("0")
            expected_summary_sha = (
                aggregate.get("outputs", {}).get("metrics_summary", {}).get("sha256")
            )
            if (
                aggregate.get("status") != "diagnostic"
                or aggregate.get("aggregate_kind") != "diagnostic"
                or aggregate.get("seeds") != [0]
                or expected_manifest_sha != artifact_sha256(manifest_path)
                or expected_summary_sha != artifact_sha256(summary_path)
            ):
                raise ValueError(f"Invalid or stale diagnostic aggregate: {aggregate_path}")
            summary = _all_scope(summary_path)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("status") != "completed":
                raise ValueError(f"Pilot run is not completed: {manifest_path}")
            row: dict[str, object] = {
                "variant_id": variant_id,
                "variant": variant.label,
                "protocol": protocol,
                "seed": 0,
                "trainable_parameters": int(manifest["trainable_parameters"]),
            }
            for key, _ in METRICS:
                value = summary.get(key, "")
                row[key.removesuffix("_mean")] = float(value) if value not in (None, "") else None
            rows.append(row)
    return rows


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("Pilot rows must be non-empty")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_pilot_outputs(project_root: Path) -> tuple[Path, Path]:
    rows = collect_pilot_rows(project_root)
    csv_path = (
        project_root
        / "results"
        / "multiview"
        / "chemical_attention"
        / "pilot"
        / "pilot_performance.csv"
    )
    report_path = project_root / "reports" / "chemical_attention_pilot_report.md"
    _write_csv(csv_path, rows)

    lines = [
        "# Chemical-interaction-biased Transformer pilot",
        "",
        "Seed-0 diagnostic on frozen committed splits. This report is a screening result, not five-seed confirmatory evidence.",
        "",
        "No dataset split, thermodynamic equation, differentiable solver, physics loss, or evaluation metric was changed.",
        "",
        "## Architecture variants",
        "",
        "| Variant | Molecular views | Attention | Pair interaction | Parameters |",
        "|---|---|---|---|---:|",
    ]
    first_protocol = CHEMICAL_ATTENTION_PROTOCOLS[0]
    parameter_by_variant = {
        str(row["variant_id"]): int(row["trainable_parameters"])
        for row in rows
        if row["protocol"] == first_protocol
    }
    descriptions = {
        "c0_current_vanilla": ("Uni-Mol", "vanilla", "legacy symmetric pair"),
        "c1_three_view_vanilla": ("RDKit + Uni-Mol + FG", "vanilla", "legacy symmetric pair"),
        "c2_chemical_bias_full": ("RDKit + Uni-Mol + FG", "chemical pair bias", "context-conditioned phi"),
        "c3_no_pair_bias": ("RDKit + Uni-Mol + FG", "vanilla", "context-conditioned phi"),
        "c4_no_functional_group": ("RDKit + Uni-Mol", "chemical pair bias", "context-conditioned phi"),
    }
    for variant_id, variant in CHEMICAL_ATTENTION_VARIANTS.items():
        views, attention, pair = descriptions[variant_id]
        lines.append(
            f"| {variant.label} | {views} | {attention} | {pair} | {parameter_by_variant[variant_id]:,} |"
        )

    lines.extend(["", "## Predictive performance", ""])
    by_identity = {(str(row["variant_id"]), str(row["protocol"])): row for row in rows}
    for protocol in CHEMICAL_ATTENTION_PROTOCOLS:
        lines.extend(
            [
                f"### {protocol}",
                "",
                "Each cell lists MAE / RMSE / R².",
                "",
                "| Variant | P (kPa) | T (K) | y | valid coverage |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for variant_id, variant in CHEMICAL_ATTENTION_VARIANTS.items():
            row = by_identity[(variant_id, protocol)]
            def formatted(key: str, digits: int) -> str:
                value = row[key]
                return "—" if value is None else f"{float(value):.{digits}f}"
            pressure = " / ".join(
                [
                    formatted("pressure_mae_kpa", 3),
                    formatted("pressure_rmse_kpa", 3),
                    formatted("pressure_r2", 3),
                ]
            )
            temperature = " / ".join(
                [
                    formatted("temperature_mae_k", 3),
                    formatted("temperature_rmse_k", 3),
                    formatted("temperature_r2", 3),
                ]
            )
            vapor = " / ".join(
                [
                    formatted("y_mae", 4),
                    formatted("y_rmse", 4),
                    formatted("y_r2", 3),
                ]
            )
            lines.append(
                f"| {variant.label} | {pressure} | {temperature} | {vapor} | "
                f"{formatted('valid_coverage', 3)} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Interpretation boundary",
            "",
            "C2 versus C1 isolates the complete interaction-module change; C2 versus C3 isolates attention pair bias; C2 versus C4 isolates the functional-group branch. Seed 0 is sufficient for a go/no-go pilot only. Any replacement claim requires the locked seeds 0--4 campaign.",
            "",
        ]
    )
    _atomic_text(report_path, "\n".join(lines))
    for variant_id in CHEMICAL_ATTENTION_VARIANTS:
        variant_rows = [row for row in rows if row["variant_id"] == variant_id]
        page = [f"# {variant_id} pilot results", "", "Status: seed-0 pilot completed.", ""]
        for row in variant_rows:
            page.append(
                f"- {row['protocol']}: P MAE/RMSE/R2={row['pressure_mae_kpa']}/"
                f"{row['pressure_rmse_kpa']}/{row['pressure_r2']}; "
                f"T={row['temperature_mae_k']}/{row['temperature_rmse_k']}/"
                f"{row['temperature_r2']}; y={row['y_mae']}/{row['y_rmse']}/{row['y_r2']}"
            )
        page.extend(["", "See `reports/chemical_attention_pilot_report.md` for the controlled comparison.", ""])
        _atomic_text(
            project_root
            / "experiments"
            / "multiview"
            / "chemical_attention"
            / variant_id
            / "results.md",
            "\n".join(page),
        )
    return csv_path, report_path
