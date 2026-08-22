"""Single-split, single-seed runner with complete paper artifact provenance."""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import time
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import rdkit
import torch

from .config import ExperimentConfig, load_experiment_config
from .auditing import ternary_subsystem_rows
from .data import discover_vle_workbooks, load_vle_dataset, retain_pure_anchored_systems
from .evaluation import predict_vle, prediction_metric_rows, write_prediction_csv
from .evaluation.thermodynamic_consistency import evaluate_thermodynamic_consistency
from .model import ThermoFormer
from .pure_properties import empty_pure_property_catalog, load_pure_property_catalog
from .representation import build_molecular_encoder, prepare_partition_features
from .splits import dataset_digest, load_split_assignment, validate_protocol_name
from .training import fit_model, seed_everything


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def result_protocol_name(experiment_name: str, split_protocol: str) -> str:
    """Namespace a variant on a reused split without overwriting its reference."""
    experiment = validate_protocol_name(experiment_name)
    split = validate_protocol_name(split_protocol)
    return split if experiment == split else validate_protocol_name(f"{experiment}.on.{split}")


def _json_digest(payload: object) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalized_experiment_digest(experiment: ExperimentConfig) -> str:
    payload = experiment.to_dict()
    # Seed-specific assignments differ intentionally; the experiment definition
    # must remain identical across the five replicate seeds.
    payload["seed"] = 0
    training = payload.get("training")
    if isinstance(training, dict):
        training["seed"] = 0
    return _json_digest(payload)


def _feature_subset_digest(feature_map: dict[str, np.ndarray]) -> str:
    digest = hashlib.sha256()
    for smiles in sorted(feature_map):
        array = np.ascontiguousarray(feature_map[smiles], dtype=np.float32)
        digest.update(smiles.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(array.shape).encode("ascii"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def requested_run_fingerprint(
    config_path: Path,
    split_path: Path,
    seed: int,
    feature_cache: Path,
    device_name: str | None,
    overrides: Sequence[str] = (),
    run_kind: str = "formal",
) -> str:
    """Hash every cheap-to-check input needed to resume an existing run."""
    experiment = load_experiment_config(config_path, overrides)
    requested_device = device_name or experiment.runtime.device
    runtime = _runtime_context(requested_device)
    return _json_digest(
        {
            "git_commit": _git_commit(),
            "resolved_config_sha256": _normalized_experiment_digest(experiment),
            "split_sha256": _file_digest(split_path),
            "feature_cache_sha256": (
                _file_digest(feature_cache) if feature_cache.is_file() else None
            ),
            "seed": int(seed),
            "runtime": runtime,
            "run_kind": run_kind,
        }
    )


def _git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _git_state() -> tuple[bool, bool, list[str]]:
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    paths = []
    for line in completed.stdout.splitlines():
        path = line[3:].strip().replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
    artifact_prefixes = ("results/", "figures/", "runs/", "checkpoints/", "cache/")
    code_paths = [path for path in paths if not path.startswith(artifact_prefixes)]
    return bool(paths), bool(code_paths), code_paths


def _config_source_paths(path: Path, ancestors: tuple[Path, ...] = ()) -> tuple[Path, ...]:
    resolved = path.resolve()
    if resolved in ancestors:
        raise ValueError("Cyclic experiment configuration inheritance")
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    parent = payload.get("extends") if isinstance(payload, dict) else None
    if parent is None:
        return (resolved,)
    if not isinstance(parent, str) or not parent.strip():
        raise ValueError("Configuration 'extends' must be a non-empty path string")
    parent_path = Path(parent)
    if not parent_path.is_absolute():
        parent_path = resolved.parent / parent_path
    return (*_config_source_paths(parent_path, (*ancestors, resolved)), resolved)


def _require_tracked_file(path: Path, label: str) -> None:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(PROJECT_ROOT.resolve())
    except ValueError as error:
        raise RuntimeError(f"Formal {label} must be inside the project: {resolved}") from error
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative.as_posix()],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Formal {label} is not tracked by Git: {resolved}")


def _validate_formal_inputs(
    config_path: Path,
    split_path: Path,
    data_root: Path,
    source_filter: str,
    catalog_path: Path | None,
) -> None:
    for path in _config_source_paths(config_path):
        _require_tracked_file(path, "configuration")
    _require_tracked_file(split_path, "split")
    workbooks = discover_vle_workbooks(data_root, source_filter)
    if not workbooks:
        raise RuntimeError(f"Formal dataset contains no tracked workbooks: {data_root}")
    for workbook in workbooks:
        _require_tracked_file(workbook, "dataset workbook")
    if catalog_path is not None:
        _require_tracked_file(catalog_path, "pure-property catalog")


def _dependency_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def _runtime_context(requested_device: str) -> dict[str, object]:
    if requested_device == "auto":
        resolved_device = "cuda" if torch.cuda.is_available() else "cpu"
    elif requested_device == "cuda" and not torch.cuda.is_available():
        resolved_device = "cuda_unavailable"
    else:
        resolved_device = requested_device
    cuda_active = resolved_device == "cuda" and torch.cuda.is_available()
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "rdkit": rdkit.__version__,
        "unimol_tools": _dependency_version("unimol-tools"),
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "cudnn": torch.backends.cudnn.version(),
        "requested_device": requested_device,
        "resolved_device": resolved_device,
        "cuda_device": torch.cuda.get_device_name(0) if cuda_active else None,
        "cuda_capability": (
            list(torch.cuda.get_device_capability(0)) if cuda_active else None
        ),
    }


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_checkpoint(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        torch.save(payload, temporary)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_training_curves(path: Path, history: Sequence[dict[str, object]]) -> None:
    rows: list[dict[str, object]] = []
    for entry in history:
        row: dict[str, object] = {
            "stage": entry["stage"],
            "epoch": entry["epoch"],
        }
        train = entry.get("train")
        validation = entry.get("validation")
        if isinstance(train, dict):
            row.update({f"train_{key}": value for key, value in train.items()})
        if isinstance(validation, dict):
            row.update({f"validation_{key}": value for key, value in validation.items()})
        rows.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _resolve_data_root(experiment: ExperimentConfig) -> Path:
    root = Path(experiment.data.root)
    return root if root.is_absolute() else (PROJECT_ROOT / root).resolve()


def _resolve_catalog(experiment: ExperimentConfig) -> Path | None:
    if not experiment.data.pure_property_catalog:
        return None
    path = Path(experiment.data.pure_property_catalog)
    return path if path.is_absolute() else (PROJECT_ROOT / path).resolve()


def run_paper_experiment(
    config_path: Path,
    split_path: Path,
    seed: int,
    run_root: Path,
    checkpoint_root: Path,
    results_root: Path,
    feature_cache: Path,
    device_name: str | None = None,
    overrides: Sequence[str] = (),
    allow_overwrite: bool = False,
    run_kind: str = "formal",
) -> dict[str, Any]:
    """Train/evaluate one immutable split and export every required artifact."""
    if run_kind not in {"formal", "smoke"}:
        raise ValueError("run_kind must be 'formal' or 'smoke'")
    git_commit = _git_commit()
    worktree_dirty, git_dirty, dirty_code_paths = _git_state()
    if run_kind == "formal" and git_dirty:
        raise RuntimeError(
            "Formal runs require committed code/config/splits; dirty paths: "
            + ", ".join(dirty_code_paths[:10])
        )
    experiment = load_experiment_config(config_path, overrides)
    training = replace(experiment.training, seed=seed)
    experiment = replace(experiment, seed=seed, training=training)
    requested_device = device_name or experiment.runtime.device
    if requested_device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    elif requested_device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    else:
        device = torch.device(requested_device)

    data_root = _resolve_data_root(experiment)
    catalog_path = _resolve_catalog(experiment)
    if run_kind == "formal":
        _validate_formal_inputs(
            config_path,
            split_path,
            data_root,
            experiment.data.source_filter,
            catalog_path,
        )
    loaded = load_vle_dataset(
        data_root,
        source_filter=experiment.data.source_filter,
        failed_weight=experiment.data.failed_weight,
        max_pressure_kpa=experiment.data.max_pressure_kpa,
    )
    samples = retain_pure_anchored_systems(
        loaded.samples,
        minimum_temperatures=experiment.data.minimum_pure_anchor_temperatures,
    )
    split = load_split_assignment(split_path, samples)
    if split.seed != seed:
        raise ValueError(f"Split seed {split.seed} does not match run seed {seed}")
    split_protocol = validate_protocol_name(split.protocol)
    protocol = result_protocol_name(experiment.name, split_protocol)
    if run_kind == "formal":
        expected_split_path = (
            PROJECT_ROOT / "splits" / split_protocol / f"seed_{seed}.json"
        ).resolve()
        if split_path.resolve() != expected_split_path:
            raise RuntimeError(
                f"Formal split must use the registered protocol path: {expected_split_path}"
            )
    run_dir = run_root / protocol / f"seed_{seed}"
    checkpoint_dir = checkpoint_root / protocol / f"seed_{seed}"
    result_dir = results_root / protocol / f"seed_{seed}"
    completion = result_dir / "manifest.json"
    if completion.exists() and not allow_overwrite:
        raise FileExistsError(
            f"Completed result already exists: {completion}; pass allow_overwrite=True explicitly"
        )
    run_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    result_dir.mkdir(parents=True, exist_ok=True)
    running_manifest = {
        "status": "running",
        "protocol": protocol,
        "seed": seed,
        "git_commit": git_commit,
        "run_kind": run_kind,
    }
    invalidated_aggregate = {
            "status": "invalidated",
            "protocol": protocol,
            "invalidated_by_seed": seed,
            "git_commit": git_commit,
            "reason": "a seed run started; aggregate is invalid until all formal seeds are revalidated",
    }
    for marker in ("aggregate_manifest.json", "diagnostic_aggregate_manifest.json"):
        _atomic_json(result_dir.parent / marker, invalidated_aggregate)
    # Invalidate every old completion marker before overwriting any artifact.
    # A crash can therefore never leave an old "completed" manifest pointing
    # at a partially replaced checkpoint or CSV.
    _atomic_json(run_dir / "manifest.json", running_manifest)
    _atomic_json(completion, running_manifest)

    unique_smiles = sorted({value for sample in samples for value in sample.smiles})
    encoder = build_molecular_encoder(
        experiment.encoder,
        feature_cache,
        use_cuda=device.type == "cuda",
    )
    seed_everything(seed)
    train_smiles = sorted({value for sample in split.train for value in sample.smiles})
    prepared_features = prepare_partition_features(
        encoder,
        unique_smiles,
        train_smiles,
    )
    feature_map = prepared_features.values
    feature_cache_sha256 = _file_digest(feature_cache)
    feature_subset_sha256 = _feature_subset_digest(feature_map)
    feature_definition_sha256 = str(
        prepared_features.metadata["feature_definition_sha256"]
    )
    source_cache_sha256 = prepared_features.metadata.get("source_cache_sha256", {})
    rdkit_scaler = prepared_features.metadata.get("rdkit_scaler", {})
    feature_dim = int(next(iter(feature_map.values())).shape[0])
    if experiment.model.feature_dim not in (None, feature_dim):
        raise ValueError(
            f"Configured feature_dim {experiment.model.feature_dim} != molecular features {feature_dim}"
        )
    view_dimensions = prepared_features.view_dimensions
    multiview = experiment.encoder.fusion_mode != "legacy"
    model_config = replace(
        experiment.model,
        feature_dim=feature_dim,
        fusion_mode=experiment.encoder.fusion_mode,
        rdkit_feature_dim=(view_dimensions["rdkit_2d"] if multiview else 0),
        unimol_feature_dim=(view_dimensions["unimol_v2"] if multiview else 0),
        functional_group_feature_dim=(
            view_dimensions["functional_groups"] if multiview else 0
        ),
    )
    resolved_experiment = replace(experiment, model=model_config)
    resolved_payload = resolved_experiment.to_dict()
    resolved_config_sha256 = _normalized_experiment_digest(resolved_experiment)
    split_sha256 = _file_digest(split_path)
    request_sha256 = requested_run_fingerprint(
        config_path,
        split_path,
        seed,
        feature_cache,
        device_name,
        overrides,
        run_kind,
    )
    runtime_context = _runtime_context(requested_device)
    environment_sha256 = _json_digest(runtime_context)
    resolved_payload["paper_protocol"] = {
        "name": protocol,
        "split_protocol": split_protocol,
        "seed": seed,
        "split_file": str(split_path.resolve()),
        "dataset_sha256": dataset_digest(samples),
    }
    resolved_payload["molecular_feature_preprocessing"] = prepared_features.metadata
    _atomic_json(run_dir / "resolved_config.json", resolved_payload)
    _atomic_json(result_dir / "resolved_config.json", resolved_payload)

    # Uni-Mol inference/conformer generation may consume framework RNG state on
    # a cache miss.  Reseed immediately before model construction so a cache hit
    # and a cache miss produce identical ThermoFormer initialization/training.
    seed_everything(seed)
    model = ThermoFormer(model_config)
    trainable_parameters = sum(
        parameter.numel() for parameter in model.parameters() if parameter.requires_grad
    )
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
    started = time.perf_counter()
    catalog = (
        load_pure_property_catalog(catalog_path)
        if catalog_path is not None
        else empty_pure_property_catalog()
    )
    result = fit_model(
        model,
        split.train,
        feature_map,
        training,
        device,
        validation_samples=split.validation,
        pure_property_catalog=catalog,
    )
    training_seconds = time.perf_counter() - started
    peak_gpu_memory_mb = (
        torch.cuda.max_memory_allocated(device) / (1024.0**2)
        if device.type == "cuda"
        else 0.0
    )
    inference_started = time.perf_counter()
    predictions = predict_vle(
        model,
        split.test,
        feature_map,
        batch_size=training.batch_size,
        device=device,
        solver_iterations=training.solver_iterations_eval,
        pure_property_catalog=catalog,
    )
    inference_seconds = time.perf_counter() - inference_started
    if split_protocol.startswith("binary_to_ternary"):
        subsystem_coverage = {
            str(row["ternary_system_id"]): int(row["covered_binary_subsystems"])
            for row in ternary_subsystem_rows(
                split.test, binary_reference_samples=split.train
            )
        }
        for record in predictions:
            record["binary_subsystem_coverage"] = subsystem_coverage.get(
                str(record["system_id"])
            )
    if split_protocol == "unseen_component":
        strict_ids = set(split.metadata.get("strict_unseen_sample_ids", []))
        for record in predictions:
            record["strict_unseen"] = record["sample_id"] in strict_ids
    metric_rows = prediction_metric_rows(predictions)
    physical_consistency = evaluate_thermodynamic_consistency(
        model,
        split.test,
        feature_map,
        device,
        prediction_records=predictions,
        solver_iterations=training.solver_iterations_eval,
        grid_points=5 if run_kind == "smoke" else 21,
        max_systems=2 if run_kind == "smoke" else None,
        pure_reference_samples=split.train,
        pure_property_catalog=catalog,
    )
    checkpoint_payload = {
        "model_name": "ThermoFormer",
        "model": result.state_dict,
        "model_config": model_config.to_dict(),
        "training_config": asdict(training),
        "protocol": protocol,
        "split_protocol": split_protocol,
        "seed": seed,
        "split_file": str(split_path.resolve()),
        "dataset_sha256": dataset_digest(samples),
        "split_sha256": split_sha256,
        "resolved_config_sha256": resolved_config_sha256,
        "feature_cache_sha256": feature_cache_sha256,
        "feature_subset_sha256": feature_subset_sha256,
        "feature_definition_sha256": feature_definition_sha256,
        "rdkit_descriptor_list_sha256": prepared_features.metadata.get(
            "rdkit_descriptor_definition_sha256"
        ),
        "rdkit_scaler_sha256": (
            rdkit_scaler.get("sha256") if isinstance(rdkit_scaler, dict) else None
        ),
        "functional_group_vocabulary_sha256": prepared_features.metadata.get(
            "functional_group_vocabulary_sha256"
        ),
        "unimol_cache_sha256": (
            source_cache_sha256.get("unimol_v2")
            if isinstance(source_cache_sha256, dict)
            else None
        ),
        "molecular_feature_preprocessing": prepared_features.metadata,
        "environment_sha256": environment_sha256,
        "request_sha256": request_sha256,
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "git_worktree_dirty": worktree_dirty,
        "dirty_code_paths": dirty_code_paths,
        "run_kind": run_kind,
        "best_validation_loss": result.best_validation_loss,
        "units": {"temperature": "K", "pressure": "kPa"},
    }
    checkpoint_path = checkpoint_dir / "best_model.pt"
    _atomic_checkpoint(checkpoint_path, checkpoint_payload)
    history_path = run_dir / "history.json"
    curves_path = run_dir / "training_curves.csv"
    predictions_path = result_dir / "predictions.csv"
    metrics_path = result_dir / "metrics.json"
    physical_consistency_path = result_dir / "physical_consistency.json"
    result_config_path = result_dir / "resolved_config.json"
    _atomic_json(history_path, result.history)
    _write_training_curves(curves_path, result.history)
    write_prediction_csv(predictions_path, predictions)
    _atomic_json(metrics_path, metric_rows)
    _atomic_json(physical_consistency_path, physical_consistency)
    artifact_paths = {
        "checkpoint": checkpoint_path,
        "history": history_path,
        "training_curves": curves_path,
        "predictions": predictions_path,
        "metrics": metrics_path,
        "physical_consistency": physical_consistency_path,
        "resolved_config": result_config_path,
    }
    artifacts = {
        name: {"path": str(path.resolve()), "sha256": _file_digest(path)}
        for name, path in artifact_paths.items()
    }
    manifest: dict[str, Any] = {
        "status": "completed" if run_kind == "formal" else "smoke",
        "protocol": protocol,
        "split_protocol": split_protocol,
        "seed": seed,
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "git_worktree_dirty": worktree_dirty,
        "dirty_code_paths": dirty_code_paths,
        "run_kind": run_kind,
        "dataset_sha256": dataset_digest(samples),
        "split_sha256": split_sha256,
        "resolved_config_sha256": resolved_config_sha256,
        "feature_cache_sha256": feature_cache_sha256,
        "feature_subset_sha256": feature_subset_sha256,
        "feature_definition_sha256": feature_definition_sha256,
        "rdkit_descriptor_list_sha256": prepared_features.metadata.get(
            "rdkit_descriptor_definition_sha256"
        ),
        "rdkit_scaler_sha256": (
            rdkit_scaler.get("sha256") if isinstance(rdkit_scaler, dict) else None
        ),
        "functional_group_vocabulary_sha256": prepared_features.metadata.get(
            "functional_group_vocabulary_sha256"
        ),
        "unimol_cache_sha256": (
            source_cache_sha256.get("unimol_v2")
            if isinstance(source_cache_sha256, dict)
            else None
        ),
        "molecular_feature_preprocessing": prepared_features.metadata,
        "environment_sha256": environment_sha256,
        "request_sha256": request_sha256,
        "split_file": str(split_path.resolve()),
        "split_metadata": split.metadata,
        "rows": {
            "train": len(split.train),
            "validation": len(split.validation),
            "test": len(split.test),
            "prediction_attempts": len(predictions),
        },
        "training_seconds": training_seconds,
        "inference_seconds": inference_seconds,
        "inference_ms_per_attempt": 1000.0 * inference_seconds / max(1, len(predictions)),
        "peak_gpu_memory_mb": peak_gpu_memory_mb,
        "trainable_parameters": trainable_parameters,
        "best_validation_loss": result.best_validation_loss,
        "checkpoint": str(checkpoint_path.resolve()),
        "artifacts": artifacts,
        "runtime": {**runtime_context, "device": str(device)},
        "headline_metrics": next(row for row in metric_rows if row["scope"] == "all"),
        "physical_consistency": physical_consistency,
    }
    _atomic_json(run_dir / "manifest.json", manifest)
    _atomic_json(completion, manifest)
    return manifest
