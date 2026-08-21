"""Command-line orchestration for grouped CV and final VLE model training."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import torch

from .data import (
    DatasetAudit,
    SplitPlan,
    VLESample,
    build_split_plan,
    load_vle_dataset,
    pure_anchor_temperatures,
    retain_pure_anchored_systems,
)
from .config import ExperimentConfig, load_experiment_config
from .metrics import summarize_fold_metrics
from .model import ThermoFormer, ThermoFormerConfig
from .pure_properties import (
    PurePropertyCatalog,
    empty_pure_property_catalog,
    load_pure_property_catalog,
)
from .representation import UniMolV2Encoder
from .reporting import write_experiment_results
from .training import TrainingConfig, evaluate_model, fit_model, seed_everything

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (PROJECT_ROOT / path).resolve()


def _clear_stale_artifacts(out_dir: Path) -> None:
    """Remove products from an earlier run while retaining the costly feature cache."""
    generated = [
        *out_dir.glob("fold_*.pt"),
        out_dir / "holdout.pt",
        out_dir / "final_model.pt",
        out_dir / "best.pt",
        out_dir / "history.json",
        out_dir / "dataset_manifest.json",
        out_dir / "experiment_config.json",
        out_dir / "unimol_features.npy",
        out_dir / "training.stdout.log",
        out_dir / "training.stderr.log",
    ]
    for path in generated:
        if path.is_file():
            path.unlink()


def _package_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train and evaluate ThermoFormer")
    parser.add_argument(
        "--config",
        type=Path,
        default=(
            PROJECT_ROOT
            / "experiments"
            / "baseline"
            / "thermoformer_base"
            / "config.json"
        ),
        help="JSON experiment configuration",
    )
    parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="SECTION.FIELD=VALUE",
        help="Repeatable dotted hyperparameter override for ablation runs",
    )
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument(
        "--results-file",
        "--results-md",
        dest="results_file",
        type=Path,
        default=None,
        help="Markdown result summary written after a successful run",
    )
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default=None)
    parser.add_argument("--evaluation-mode", choices=("kfold", "holdout"), default=None)
    parser.add_argument("--folds", type=int, default=None)
    parser.add_argument(
        "--skip-validation",
        "--skip-cv",
        dest="skip_validation",
        action="store_true",
        help="Skip fold/holdout validation for a quick final-training smoke run",
    )
    return parser


def _device(name: str) -> torch.device:
    if name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("--device cuda requested, but CUDA is unavailable")
    return torch.device(name)


def _model(model_config: ThermoFormerConfig, seed: int) -> ThermoFormer:
    seed_everything(seed)
    return ThermoFormer(model_config)


def _checkpoint(
    path: Path,
    state_dict: dict[str, torch.Tensor],
    model_config: ThermoFormerConfig,
    training_config: TrainingConfig,
    encoder_config: dict[str, object],
    metrics: dict[str, float] | None,
) -> None:
    torch.save(
        {
            "model_name": "ThermoFormer",
            "model": state_dict,
            "model_config": model_config.to_dict(),
            "training_config": asdict(training_config),
            "encoder": encoder_config,
            "units": {"temperature": "K", "pressure": "kPa"},
            "metrics": metrics,
        },
        path,
    )


def _manifest(
    samples: list[VLESample],
    plan: SplitPlan,
    experiment: ExperimentConfig,
    model_config: ThermoFormerConfig,
    device: torch.device,
    fold_metrics: list[dict[str, float]],
    test_metrics: dict[str, float],
    data_audit: DatasetAudit,
    validation_skipped: bool,
    pure_property_catalog: PurePropertyCatalog,
) -> dict[str, object]:
    quality = Counter(sample.quality_status for sample in samples)
    components = Counter(str(sample.component_count) for sample in samples)
    test_systems = {sample.system_key for sample in plan.test}
    cv_systems = {sample.system_key for sample in plan.cv}
    anchor_temperatures = pure_anchor_temperatures(samples)
    molecules = {smile for sample in samples for smile in sample.smiles}
    anchored_molecules = {
        smile
        for smile, temperatures in anchor_temperatures.items()
        if len(temperatures) >= experiment.data.minimum_pure_anchor_temperatures
    }

    def unanchored_count(rows: tuple[VLESample, ...]) -> int:
        row_molecules = {smile for sample in rows for smile in sample.smiles}
        row_anchors = pure_anchor_temperatures(rows)
        return sum(
            len(row_anchors.get(smile, set())) < experiment.data.minimum_pure_anchor_temperatures
            for smile in row_molecules
        )
    return {
        "n_samples": len(samples),
        "n_samples_before_pure_anchor_filter": data_audit.loaded_samples,
        "n_samples_removed_by_pure_anchor_filter": data_audit.loaded_samples - len(samples),
        "data_loading_audit": asdict(data_audit),
        "component_rows": dict(components),
        "cv_component_rows": dict(Counter(str(sample.component_count) for sample in plan.cv)),
        "test_component_rows": dict(Counter(str(sample.component_count) for sample in plan.test)),
        "fold_validation_component_rows": [
            dict(Counter(str(sample.component_count) for sample in fold.validation))
            for fold in plan.folds
        ],
        "quality_rows": dict(quality),
        "experiment_mode_rows": dict(Counter(sample.experiment_mode for sample in samples)),
        "experiment_mode_confidence": {
            "mean": float(np.mean([sample.experiment_mode_confidence for sample in samples])),
            "explicit_rows": sum(
                sample.experiment_mode_confidence >= 1.0 for sample in samples
            ),
            "inferred_rows": sum(
                0.0 < sample.experiment_mode_confidence < 1.0 for sample in samples
            ),
            "ambiguous_rows": sum(
                sample.experiment_mode_confidence <= 0.0 for sample in samples
            ),
            "low_confidence_full_state_rows": sum(
                sample.experiment_mode == "full_state"
                and 0.0 < sample.experiment_mode_confidence < 2.0 / 3.0
                for sample in samples
            ),
        },
        "n_systems": len({sample.system_key for sample in samples}),
        "n_cv_rows": len(plan.cv),
        "n_test_rows": len(plan.test),
        "n_cv_systems": len(cv_systems),
        "n_test_systems": len(test_systems),
        "n_anchor_reference_systems": len(plan.anchor_reference_systems),
        "cv_test_system_overlap": len(cv_systems & test_systems),
        "cv_unanchored_molecules": unanchored_count(plan.cv),
        "fold_training_unanchored_molecules": [
            unanchored_count(fold.train) for fold in plan.folds
        ],
        "fold_validation_metrics": fold_metrics,
        "cross_validation_summary": (
            summarize_fold_metrics(fold_metrics) if plan.mode == "kfold" else {}
        ),
        "final_test_metrics": test_metrics,
        "model_name": "ThermoFormer",
        "model_config": model_config.to_dict(),
        "experiment_config": experiment.to_dict(),
        "device": str(device),
        "molecular_encoder": f"Uni-Mol v2 {experiment.encoder.model_size} frozen cls_repr",
        "failed_quality_weight": experiment.data.failed_weight,
        "maximum_training_pressure_kpa": experiment.data.max_pressure_kpa,
        "minimum_pure_anchor_temperatures": experiment.data.minimum_pure_anchor_temperatures,
        "n_molecules": len(molecules),
        "pure_anchored_molecules": len(anchored_molecules),
        "unanchored_molecules": len(molecules - anchored_molecules),
        "pure_property_catalog_source": pure_property_catalog.source,
        "pure_property_catalog_molecules": len(
            molecules & pure_property_catalog.covered_smiles
        ),
        "pure_property_correlation_types": dict(
            Counter(
                type(parameters).__name__
                for smile, parameters in pure_property_catalog.entries.items()
                if smile in molecules
            )
        ),
        "evaluation_mode": plan.mode,
        "run_status": "smoke" if validation_skipped else "completed",
        "split": "component-count-stratified unordered-system grouped evaluation",
        "runtime_versions": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "numpy": np.__version__,
            "openpyxl": _package_version("openpyxl"),
            "unimol-tools": _package_version("unimol-tools"),
        },
        "units": {
            "source_temperature": "degC",
            "source_pressure": "mmHg",
            "model_temperature": "K",
            "model_pressure": "kPa",
        },
    }


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    experiment = load_experiment_config(args.config, args.overrides)
    data_config = experiment.data
    evaluation_config = experiment.evaluation
    runtime_config = experiment.runtime
    if args.data_root is not None:
        data_config = replace(data_config, root=str(args.data_root))
    if args.out_dir is not None:
        runtime_config = replace(runtime_config, output_dir=str(args.out_dir))
    if args.results_file is not None:
        runtime_config = replace(runtime_config, results_file=str(args.results_file))
    if args.device is not None:
        runtime_config = replace(runtime_config, device=args.device)
    if args.evaluation_mode is not None:
        evaluation_config = replace(evaluation_config, mode=args.evaluation_mode)
    if args.folds is not None:
        evaluation_config = replace(evaluation_config, folds=args.folds)
    catalog_path = (
        str(_project_path(data_config.pure_property_catalog))
        if data_config.pure_property_catalog
        else ""
    )
    data_config = replace(
        data_config,
        root=str(_project_path(data_config.root)),
        pure_property_catalog=catalog_path,
    )
    formal_output_dir = _project_path(runtime_config.output_dir)
    actual_output_dir = (
        formal_output_dir / "smoke" if args.skip_validation else formal_output_dir
    )
    output_dir = str(actual_output_dir)
    if (
        args.skip_validation
        and args.results_file is None
        and runtime_config.results_file is not None
    ):
        results_file = str(actual_output_dir / "smoke_results.md")
    else:
        results_file = (
            str(_project_path(runtime_config.results_file))
            if runtime_config.results_file is not None
            else None
        )
    runtime_config = replace(
        runtime_config,
        output_dir=output_dir,
        results_file=results_file,
    )
    experiment = replace(
        experiment,
        data=data_config,
        evaluation=evaluation_config,
        runtime=runtime_config,
    )
    if experiment.training.epochs_supervised < 0 or experiment.training.epochs_physics < 0:
        raise ValueError("Epoch counts cannot be negative")
    out_dir = Path(experiment.runtime.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    device = _device(experiment.runtime.device)

    load_result = load_vle_dataset(
        Path(experiment.data.root),
        source_filter=experiment.data.source_filter,
        failed_weight=experiment.data.failed_weight,
        max_pressure_kpa=experiment.data.max_pressure_kpa,
    )
    loaded_samples = list(load_result.samples)
    pure_property_catalog = (
        load_pure_property_catalog(Path(experiment.data.pure_property_catalog))
        if experiment.data.pure_property_catalog
        else empty_pure_property_catalog()
    )
    samples = retain_pure_anchored_systems(
        loaded_samples,
        minimum_temperatures=experiment.data.minimum_pure_anchor_temperatures,
    )
    if not samples:
        raise RuntimeError("No rows remain after pure-component anchor filtering")
    plan = build_split_plan(
        samples,
        mode=experiment.evaluation.mode,
        test_fraction=experiment.evaluation.test_fraction,
        validation_fraction=experiment.evaluation.validation_fraction,
        folds=experiment.evaluation.folds,
        seed=experiment.seed,
        minimum_anchor_temperatures=experiment.data.minimum_pure_anchor_temperatures,
    )
    unique_smiles = sorted({smile for sample in samples for smile in sample.smiles})
    seed_everything(experiment.seed)
    encoder = UniMolV2Encoder(
        formal_output_dir / "unimolv2_features.npz",
        batch_size=experiment.encoder.batch_size,
        model_size=experiment.encoder.model_size,
        use_cuda=device.type == "cuda",
    )
    feature_map = encoder.encode(unique_smiles)
    feature_dim = int(next(iter(feature_map.values())).shape[0])
    if experiment.model.feature_dim not in (None, feature_dim):
        raise ValueError(
            "Configured model.feature_dim does not match the Uni-Mol v2 representation: "
            f"{experiment.model.feature_dim} != {feature_dim}"
        )
    model_config = replace(experiment.model, feature_dim=feature_dim)
    base_training_config = experiment.training
    encoder_config = {
        "name": "unimolv2",
        "model_size": experiment.encoder.model_size,
        "feature_dim": feature_dim,
    }
    _clear_stale_artifacts(out_dir)
    resolved_experiment = replace(experiment, model=model_config, training=base_training_config)
    with (out_dir / "experiment_config.json").open("w", encoding="utf-8") as handle:
        json.dump(resolved_experiment.to_dict(), handle, ensure_ascii=False, indent=2)

    histories: dict[str, object] = {}
    fold_metrics: list[dict[str, float]] = []
    if not args.skip_validation:
        for fold_index, fold in enumerate(plan.folds, start=1):
            fold_config = replace(base_training_config, seed=experiment.seed + fold_index)
            model = _model(model_config, fold_config.seed)
            result = fit_model(
                model,
                fold.train,
                feature_map,
                fold_config,
                device,
                validation_samples=fold.validation,
                pure_property_catalog=pure_property_catalog,
            )
            metrics = evaluate_model(
                model,
                fold.validation,
                feature_map,
                base_training_config.batch_size,
                device,
                solver_iterations=base_training_config.solver_iterations_eval,
                pure_property_catalog=pure_property_catalog,
            )
            metrics["best_validation_loss"] = (
                float(result.best_validation_loss)
                if result.best_validation_loss is not None
                else float(np.nan)
            )
            fold_metrics.append(metrics)
            label = f"fold_{fold_index}" if plan.mode == "kfold" else "holdout"
            histories[label] = result.history
            _checkpoint(
                out_dir / (f"fold_{fold_index}.pt" if plan.mode == "kfold" else "holdout.pt"),
                result.state_dict,
                model_config,
                fold_config,
                encoder_config,
                metrics,
            )
            print(json.dumps({"split": label, **metrics}, ensure_ascii=False))
        if plan.mode == "kfold":
            print(
                json.dumps(
                    {"cross_validation": summarize_fold_metrics(fold_metrics)},
                    ensure_ascii=False,
                )
            )

    final_config = replace(base_training_config, seed=experiment.seed + 1000)
    final_model = _model(model_config, final_config.seed)
    final_result = fit_model(
        final_model,
        plan.cv,
        feature_map,
        final_config,
        device,
        pure_property_catalog=pure_property_catalog,
    )
    test_metrics = evaluate_model(
        final_model,
        plan.test,
        feature_map,
        base_training_config.batch_size,
        device,
        solver_iterations=base_training_config.solver_iterations_eval,
        pure_property_catalog=pure_property_catalog,
    )
    histories["final"] = final_result.history
    _checkpoint(
        out_dir / "final_model.pt",
        final_result.state_dict,
        model_config,
        final_config,
        encoder_config,
        test_metrics,
    )
    with (out_dir / "history.json").open("w", encoding="utf-8") as handle:
        json.dump(histories, handle, ensure_ascii=False, indent=2)
    manifest = _manifest(
        samples,
        plan,
        resolved_experiment,
        model_config,
        device,
        fold_metrics,
        test_metrics,
        load_result.audit,
        args.skip_validation,
        pure_property_catalog,
    )
    with (out_dir / "dataset_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
    if resolved_experiment.runtime.results_file is not None:
        write_experiment_results(
            Path(resolved_experiment.runtime.results_file),
            resolved_experiment,
            manifest,
            out_dir,
        )
    print(
        json.dumps(
            {"final_test": test_metrics, "checkpoint": str(out_dir / "final_model.pt")},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
