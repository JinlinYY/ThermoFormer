"""Leakage-safe C2 candidate selection on committed validation partitions."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Mapping, Sequence

from .artifacts import artifact_sha256, portable_artifact_path, resolve_artifact_path
from .config import load_experiment_config


C2_CANDIDATES: dict[str, str] = {
    "o0_original": "experiments/multiview/chemical_attention/c2_optimization/o0_original/config.json",
    "o1_shared_gate": "experiments/multiview/chemical_attention/c2_optimization/o1_shared_gate/config.json",
    "o2_headwise": "experiments/multiview/chemical_attention/c2_optimization/o2_headwise/config.json",
    "o3_headwise_curriculum": "experiments/multiview/chemical_attention/c2_optimization/o3_headwise_curriculum/config.json",
    "o4_headwise_curriculum_modality": "experiments/multiview/chemical_attention/c2_optimization/o4_headwise_curriculum_modality/config.json",
}
C2_SELECTION_SEEDS = (0, 1, 2)
C2_SELECTION_PROTOCOL = "overall_binary_ternary"
SELECTION_ERROR_KEYS = (
    "pressure_mae_kpa",
    "pressure_rmse_kpa",
    "temperature_mae_k",
    "temperature_rmse_k",
    "y_mae",
    "y_rmse",
)


def validation_selection_scores(
    rows_by_candidate: Mapping[str, Sequence[Mapping[str, float | int | str | None]]]
) -> dict[str, float]:
    """Return the predeclared balanced error ratio relative to original C2."""
    if "o0_original" not in rows_by_candidate:
        raise ValueError("Selection rows must include o0_original")
    original = {int(row["seed"]): row for row in rows_by_candidate["o0_original"]}
    if set(original) != set(C2_SELECTION_SEEDS):
        raise ValueError("Original C2 must contain validation seeds 0, 1, and 2")
    scores: dict[str, float] = {}
    for candidate, rows in rows_by_candidate.items():
        indexed = {int(row["seed"]): row for row in rows}
        if set(indexed) != set(C2_SELECTION_SEEDS):
            raise ValueError(f"{candidate} must contain validation seeds 0, 1, and 2")
        ratios: list[float] = []
        for seed in C2_SELECTION_SEEDS:
            for key in SELECTION_ERROR_KEYS:
                baseline = float(original[seed][key])
                value = float(indexed[seed][key])
                if not math.isfinite(baseline) or baseline <= 0.0 or not math.isfinite(value):
                    raise ValueError(f"Invalid selection metric {key} for seed {seed}")
                ratios.append(value / baseline)
        scores[candidate] = sum(ratios) / len(ratios)
    return scores


def _overall_rows(path: Path) -> list[dict[str, float | int | str | None]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected: list[dict[str, float | int | str | None]] = []
    for row in rows:
        if row.get("scope") != "all":
            continue
        parsed: dict[str, float | int | str | None] = {"seed": int(row["seed"])}
        for key in SELECTION_ERROR_KEYS:
            value = row.get(key)
            if value in (None, ""):
                raise ValueError(f"Missing validation metric {key}: {path}")
            parsed[key] = float(value)
        selected.append(parsed)
    return selected


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _resolved_config_snapshot(project_root: Path, config_value: str) -> tuple[dict[str, object], str]:
    payload = load_experiment_config(project_root / config_value).to_dict()
    payload["seed"] = 0
    training = payload.get("training")
    if isinstance(training, dict):
        training["seed"] = 0
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return payload, hashlib.sha256(encoded).hexdigest()


def _validated_aggregate_inputs(
    protocol_dir: Path,
    expected_protocol: str,
) -> tuple[Path, dict[str, object]]:
    manifest_path = protocol_dir / "diagnostic_aggregate_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("status") != "diagnostic"
        or manifest.get("aggregate_kind") != "diagnostic"
        or manifest.get("protocol") != expected_protocol
        or manifest.get("seeds") != list(C2_SELECTION_SEEDS)
    ):
        raise ValueError(f"Incomplete or mismatched validation aggregate: {manifest_path}")
    input_hashes = manifest.get("input_manifest_sha256")
    if not isinstance(input_hashes, dict):
        raise ValueError(f"Aggregate lacks seed-manifest hashes: {manifest_path}")
    for seed in C2_SELECTION_SEEDS:
        seed_manifest_path = protocol_dir / f"seed_{seed}" / "manifest.json"
        seed_manifest = json.loads(seed_manifest_path.read_text(encoding="utf-8"))
        if (
            seed_manifest.get("evaluation_partition") != "validation"
            or seed_manifest.get("run_kind") != "selection"
            or seed_manifest.get("protocol") != expected_protocol
            or input_hashes.get(str(seed)) != artifact_sha256(seed_manifest_path)
        ):
            raise ValueError(f"Invalid validation seed provenance: {seed_manifest_path}")
    output = manifest.get("outputs", {}).get("metrics_by_seed")
    if not isinstance(output, dict):
        raise ValueError(f"Aggregate lacks metrics table provenance: {manifest_path}")
    table = resolve_artifact_path(str(output.get("path", "")))
    if table != (protocol_dir / "diagnostic_metrics_by_seed.csv").resolve():
        raise ValueError(f"Unexpected validation metrics path: {table}")
    if output.get("sha256") != artifact_sha256(table):
        raise ValueError(f"Validation metrics table has changed: {table}")
    return table, manifest


def write_c2_selection_report(project_root: Path, results_root: Path) -> str:
    rows_by_candidate: dict[str, list[dict[str, float | int | str | None]]] = {}
    aggregate_paths: dict[str, Path] = {}
    selection_inputs: dict[str, dict[str, object]] = {}
    for candidate, config_value in C2_CANDIDATES.items():
        config = json.loads((project_root / config_value).read_text(encoding="utf-8"))
        experiment_name = str(config["name"])
        protocol = f"{experiment_name}.on.{C2_SELECTION_PROTOCOL}"
        protocol_dir = results_root / protocol
        table, manifest = _validated_aggregate_inputs(protocol_dir, protocol)
        manifest_path = protocol_dir / "diagnostic_aggregate_manifest.json"
        rows_by_candidate[candidate] = _overall_rows(table)
        aggregate_paths[candidate] = manifest_path
        resolved_snapshot, resolved_digest = _resolved_config_snapshot(
            project_root, config_value
        )
        selection_inputs[candidate] = {
            "aggregate_manifest_sha256": artifact_sha256(manifest_path),
            "metrics_by_seed": {
                "path": portable_artifact_path(table),
                "sha256": artifact_sha256(table),
            },
            "input_manifest_sha256": manifest["input_manifest_sha256"],
            "config": {
                "path": config_value,
                "sha256": artifact_sha256(project_root / config_value),
                "resolved_sha256": resolved_digest,
                "resolved": resolved_snapshot,
            },
        }

    scores = validation_selection_scores(rows_by_candidate)
    selected = min(scores, key=scores.get)
    lines = [
        "# C2 validation-only optimization results",
        "",
        "The candidates were selected on the committed validation partitions for seeds 0–2. "
        "No test prediction was generated in this stage. Training was data-supervised only.",
        "",
        "The locked score is the mean of the six P/T/y MAE and RMSE ratios relative to "
        "the original C2 within each seed; lower is better.",
        "",
        "| candidate | validation score | selected |",
        "|---|---:|:---:|",
    ]
    for candidate in C2_CANDIDATES:
        lines.append(
            f"| {candidate} | {scores[candidate]:.6f} | {'yes' if candidate == selected else ''} |"
        )
    lines.extend(["", f"Locked candidate: `{selected}`.", ""])
    report_path = project_root / "experiments/multiview/chemical_attention/c2_optimization/results.md"
    _atomic_text(report_path, "\n".join(lines))
    candidate_result_paths: dict[str, Path] = {}
    for candidate in C2_CANDIDATES:
        candidate_path = (
            project_root
            / "experiments/multiview/chemical_attention/c2_optimization"
            / candidate
            / "results.md"
        )
        _atomic_text(
            candidate_path,
            "\n".join(
                [
                    f"# {candidate}",
                    "",
                    "Status: completed (validation-only selection).",
                    "",
                    f"Locked validation score: {scores[candidate]:.6f}.",
                    f"Selected for formal evaluation: {'yes' if candidate == selected else 'no'}.",
                    "",
                    "No test partition was evaluated for this candidate-selection result.",
                    "",
                ]
            ),
        )
        candidate_result_paths[candidate] = candidate_path
    manifest_payload = {
        "status": "selected",
        "evaluation_partition": "validation",
        "protocol": C2_SELECTION_PROTOCOL,
        "seeds": list(C2_SELECTION_SEEDS),
        "score_definition": "mean per-seed ratio of P/T/y MAE and RMSE vs o0_original",
        "scores": scores,
        "selected_candidate": selected,
        "selected_config": selection_inputs[selected]["config"],
        "selection_inputs": selection_inputs,
        "aggregate_manifests": {
            candidate: {
                "path": portable_artifact_path(path),
                "sha256": artifact_sha256(path),
            }
            for candidate, path in aggregate_paths.items()
        },
        "report": {
            "path": portable_artifact_path(report_path),
            "sha256": artifact_sha256(report_path),
        },
        "candidate_results": {
            candidate: {
                "path": portable_artifact_path(path),
                "sha256": artifact_sha256(path),
            }
            for candidate, path in candidate_result_paths.items()
        },
    }
    selection_path = results_root.parent / "selection_manifest.json"
    _atomic_text(selection_path, json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n")
    return selected


def validate_c2_selection(project_root: Path, selection_path: Path) -> str:
    """Validate the frozen selected configuration before any test evaluation."""
    manifest = json.loads(selection_path.read_text(encoding="utf-8"))
    selected = str(manifest.get("selected_candidate", ""))
    if (
        manifest.get("status") != "selected"
        or manifest.get("evaluation_partition") != "validation"
        or manifest.get("seeds") != list(C2_SELECTION_SEEDS)
        or selected not in C2_CANDIDATES
    ):
        raise ValueError("Selection manifest is incomplete or malformed")
    report = manifest.get("report")
    if not isinstance(report, dict):
        raise ValueError("Selection manifest lacks report provenance")
    report_path = resolve_artifact_path(str(report.get("path", "")))
    if report.get("sha256") != artifact_sha256(report_path):
        raise ValueError("Selection report has changed")
    config_value = C2_CANDIDATES[selected]
    config_path = project_root / config_value
    _, resolved_digest = _resolved_config_snapshot(project_root, config_value)
    frozen = manifest.get("selected_config")
    if (
        not isinstance(frozen, dict)
        or frozen.get("path") != config_value
        or frozen.get("sha256") != artifact_sha256(config_path)
        or frozen.get("resolved_sha256") != resolved_digest
    ):
        raise ValueError("Selected C2 configuration differs from its frozen snapshot")
    frozen_inputs = manifest.get("selection_inputs")
    stored_scores = manifest.get("scores")
    if not isinstance(frozen_inputs, dict) or not isinstance(stored_scores, dict):
        raise ValueError("Selection manifest lacks frozen scoring evidence")
    results_root = selection_path.parent / "runs"
    rows_by_candidate: dict[str, list[dict[str, float | int | str | None]]] = {}
    for candidate, candidate_config in C2_CANDIDATES.items():
        config = load_experiment_config(project_root / candidate_config)
        protocol = f"{config.name}.on.{C2_SELECTION_PROTOCOL}"
        protocol_dir = results_root / protocol
        table, aggregate = _validated_aggregate_inputs(protocol_dir, protocol)
        aggregate_path = protocol_dir / "diagnostic_aggregate_manifest.json"
        current_snapshot, current_digest = _resolved_config_snapshot(
            project_root, candidate_config
        )
        current_input = {
            "aggregate_manifest_sha256": artifact_sha256(aggregate_path),
            "metrics_by_seed": {
                "path": portable_artifact_path(table),
                "sha256": artifact_sha256(table),
            },
            "input_manifest_sha256": aggregate["input_manifest_sha256"],
            "config": {
                "path": candidate_config,
                "sha256": artifact_sha256(project_root / candidate_config),
                "resolved_sha256": current_digest,
                "resolved": current_snapshot,
            },
        }
        if frozen_inputs.get(candidate) != current_input:
            raise ValueError(f"Frozen validation evidence changed for {candidate}")
        rows_by_candidate[candidate] = _overall_rows(table)
    recomputed_scores = validation_selection_scores(rows_by_candidate)
    if any(
        candidate not in stored_scores
        or not math.isclose(
            float(stored_scores[candidate]), score, rel_tol=0.0, abs_tol=1e-12
        )
        for candidate, score in recomputed_scores.items()
    ):
        raise ValueError("Stored C2 selection scores do not match frozen evidence")
    if selected != min(recomputed_scores, key=recomputed_scores.get):
        raise ValueError("Selected C2 candidate is not the locked validation winner")
    return selected


def write_c2_formal_report(
    project_root: Path,
    selection_path: Path,
    protocol_dir: Path,
    selected: str,
) -> Path:
    """Write the human-readable five-seed test result after formal aggregation."""
    aggregate_path = protocol_dir / "aggregate_manifest.json"
    aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))
    if aggregate.get("status") != "completed" or aggregate.get("seeds") != [0, 1, 2, 3, 4]:
        raise ValueError("Formal C2 aggregate is incomplete")
    summary_path = protocol_dir / "metrics_summary.csv"
    output = aggregate.get("outputs", {}).get("metrics_summary", {})
    if output.get("sha256") != artifact_sha256(summary_path):
        raise ValueError("Formal C2 summary has changed")
    def overall_row(path: Path) -> dict[str, str]:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return next(row for row in csv.DictReader(handle) if row.get("scope") == "all")

    overall = overall_row(summary_path)
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    score = float(selection["scores"][selected])
    metrics = (
        ("P MAE (kPa)", "pressure_mae_kpa"),
        ("P RMSE (kPa)", "pressure_rmse_kpa"),
        ("P R²", "pressure_r2"),
        ("T MAE (K)", "temperature_mae_k"),
        ("T RMSE (K)", "temperature_rmse_k"),
        ("T R²", "temperature_r2"),
        ("y MAE", "y_mae"),
        ("y RMSE", "y_rmse"),
        ("y R²", "y_r2"),
    )
    lines = [
        "# Optimized C2 formal result",
        "",
        f"Selected candidate: `{selected}` (validation-only score {score:.6f}).",
        "",
        "Evaluation: overall_binary_ternary test partition, seeds 0–4, data supervision only.",
        "",
        "| metric | mean | std |",
        "|---|---:|---:|",
    ]
    for label, key in metrics:
        lines.append(f"| {label} | {float(overall[key + '_mean']):.6f} | {float(overall[key + '_std']):.6f} |")
    lines.extend(
        [
            "",
            "## Validation candidate capacity",
            "",
            "| candidate | trainable parameters | validation score |",
            "|---|---:|---:|",
        ]
    )
    selection_runs = selection_path.parent / "runs"
    for candidate, config_value in C2_CANDIDATES.items():
        candidate_config = load_experiment_config(project_root / config_value)
        candidate_protocol = f"{candidate_config.name}.on.{C2_SELECTION_PROTOCOL}"
        seed_manifest = json.loads(
            (selection_runs / candidate_protocol / "seed_0/manifest.json").read_text(
                encoding="utf-8"
            )
        )
        lines.append(
            f"| {candidate} | {int(seed_manifest['trainable_parameters']):,} | "
            f"{float(selection['scores'][candidate]):.6f} |"
        )
    comparison_root = (
        project_root / "results/multiview/chemical_attention/formal/runs"
    )
    comparison_specs = (
        ("C1 three-view vanilla", "c1_three_view_vanilla.on.overall_binary_ternary"),
        ("C2 original", "c2_chemical_bias_full.on.overall_binary_ternary"),
        ("C3 no attention pair bias", "c3_no_pair_bias.on.overall_binary_ternary"),
    )
    optimized_manifest = json.loads(
        (protocol_dir / "seed_0/manifest.json").read_text(encoding="utf-8")
    )
    comparison_rows = [
        ("C2 optimized headwise", overall, int(optimized_manifest["trainable_parameters"]))
    ]
    for label, protocol_name in comparison_specs:
        reference_dir = comparison_root / protocol_name
        reference_manifest = json.loads(
            (reference_dir / "seed_0/manifest.json").read_text(encoding="utf-8")
        )
        comparison_rows.append(
            (
                label,
                overall_row(reference_dir / "metrics_summary.csv"),
                int(reference_manifest["trainable_parameters"]),
            )
        )
    lines.extend(
        [
            "",
            "## Comparison with the frozen ablation",
            "",
            "| variant | parameters | P MAE (kPa) | T MAE (K) | y MAE |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for label, row, parameters in comparison_rows:
        lines.append(
            f"| {label} | {parameters:,} | {float(row['pressure_mae_kpa_mean']):.4f} | "
            f"{float(row['temperature_mae_k_mean']):.4f} | {float(row['y_mae_mean']):.6f} |"
        )
    lines.extend(
        [
            "",
            "Conclusion: the validation-selected headwise bias is not the overall test winner. "
            "It slightly improves y MAE over C1, but degrades pressure, while C3 remains better "
            "on T and y. The current ThermoFormer should therefore not be replaced by this C2.",
            "No additional configuration was chosen after observing these test results.",
            "",
        ]
    )
    top_report = project_root / "experiments/multiview/chemical_attention/c2_optimization/results.md"
    candidate_report = (
        project_root / "experiments/multiview/chemical_attention/c2_optimization"
        / selected / "results.md"
    )
    content = "\n".join(lines)
    _atomic_text(top_report, content)
    _atomic_text(candidate_report, content)
    report_manifest = {
        "status": "completed",
        "selected_candidate": selected,
        "evaluation_partition": "test",
        "seeds": [0, 1, 2, 3, 4],
        "aggregate_manifest_sha256": artifact_sha256(aggregate_path),
        "metrics_summary_sha256": artifact_sha256(summary_path),
        "reports": {
            "top": {"path": portable_artifact_path(top_report), "sha256": artifact_sha256(top_report)},
            "selected": {
                "path": portable_artifact_path(candidate_report),
                "sha256": artifact_sha256(candidate_report),
            },
        },
    }
    report_manifest_path = protocol_dir / "formal_report_manifest.json"
    _atomic_text(report_manifest_path, json.dumps(report_manifest, indent=2, sort_keys=True) + "\n")
    return top_report
