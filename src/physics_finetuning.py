"""Partial physics fine-tuning from a frozen supervised ThermoFormer checkpoint."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean, stdev
from typing import Sequence

import numpy as np
import torch
from torch import nn

from .artifacts import artifact_sha256, atomic_write_text
from .config import PhysicsFineTuningConfig
from .data import VLEBatch, VLESample
from .losses import Objective
from .model import ThermoFormerConfig
from .pure_properties import PurePropertyCatalog
from .training import (
    TrainingConfig,
    _cpu_state,
    _loader,
    _objective,
    _run_epoch,
    seed_everything,
)


@dataclass(frozen=True)
class FineTuneParameterGroup:
    name: str
    learning_rate: float
    parameter_count: int
    parameter_names: tuple[str, ...]
    parameters: tuple[nn.Parameter, ...]


@dataclass(frozen=True)
class FineTuneSetup:
    optimizer: torch.optim.Optimizer
    groups: tuple[FineTuneParameterGroup, ...]
    total_parameters: int
    trainable_parameters: int

    def record(self) -> dict[str, object]:
        return {
            "groups": [
                {
                    "name": group.name,
                    "learning_rate": group.learning_rate,
                    "parameter_count": group.parameter_count,
                    "parameter_names": list(group.parameter_names),
                }
                for group in self.groups
            ],
            "total_parameters": self.total_parameters,
            "trainable_parameters": self.trainable_parameters,
            "trainable_fraction": self.trainable_parameters / self.total_parameters,
        }


@dataclass
class PhysicsFitResult:
    state_dict: dict[str, torch.Tensor]
    stage_states: dict[str, dict[str, torch.Tensor]]
    history: list[dict[str, object]]
    selected_stage: str
    stage_validation_losses: dict[str, float | None]
    parameter_summary: dict[str, object]
    best_validation_loss: float
    selection_partitions: tuple[str, ...] = ("validation",)


def physics_warmup_scale(epoch: int, warmup_epochs: int) -> float:
    if epoch < 1 or warmup_epochs < 0:
        raise ValueError("epoch must be positive and warmup_epochs non-negative")
    return 1.0 if warmup_epochs == 0 else min(1.0, epoch / warmup_epochs)


def _matches_group(name: str, group: str) -> bool:
    return name == group or name.startswith(group + ".")


def configure_physics_finetuning(
    model: nn.Module,
    config: TrainingConfig,
    finetuning: PhysicsFineTuningConfig,
) -> FineTuneSetup:
    """Freeze the representation/Transformer and build only declared optimizer groups."""
    if not finetuning.enabled:
        raise ValueError("physics_finetuning must be enabled")
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    learning_rates = {
        "pair_potential": finetuning.pair_potential_lr,
        "vapor_pressure": finetuning.vapor_pressure_lr,
        "film": finetuning.film_lr,
        "mixture_token": finetuning.mixture_token_lr,
    }
    named = tuple(model.named_parameters())
    groups: list[FineTuneParameterGroup] = []
    optimizer_groups: list[dict[str, object]] = []
    for group_name in finetuning.trainable_modules:
        selected = tuple(
            (name, parameter)
            for name, parameter in named
            if _matches_group(name, group_name)
        )
        if not selected:
            raise ValueError(f"ThermoFormer has no parameters for physics group {group_name}")
        parameters = tuple(parameter for _, parameter in selected)
        for parameter in parameters:
            parameter.requires_grad_(True)
        learning_rate = learning_rates[group_name]
        group = FineTuneParameterGroup(
            name=group_name,
            learning_rate=learning_rate,
            parameter_count=sum(parameter.numel() for parameter in parameters),
            parameter_names=tuple(name for name, _ in selected),
            parameters=parameters,
        )
        groups.append(group)
        optimizer_groups.append(
            {"params": list(parameters), "lr": learning_rate, "name": group_name}
        )
    optimizer = torch.optim.AdamW(
        optimizer_groups,
        weight_decay=config.weight_decay,
    )
    total = sum(parameter.numel() for parameter in model.parameters())
    trainable = sum(
        parameter.numel() for parameter in model.parameters() if parameter.requires_grad
    )
    return FineTuneSetup(optimizer, tuple(groups), total, trainable)


def physics_finetune_objective(
    model: nn.Module,
    batch: VLEBatch,
    config: TrainingConfig,
    *,
    physics_scale: float,
    teacher_forced_fugacity_weight: float,
) -> Objective:
    """Supervised objective plus the scaled teacher-forced fugacity loss."""
    return _objective(
        model,
        batch,
        config,
        physics_scale=physics_scale,
        teacher_forced_fugacity_weight=teacher_forced_fugacity_weight,
    )


def load_stage1_checkpoint(
    model: nn.Module,
    checkpoint_path: Path,
    *,
    expected_provenance: dict[str, str] | None = None,
) -> str:
    """Strictly load the supervised best state and return its artifact digest."""
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict) or not isinstance(payload.get("model"), dict):
        raise ValueError("Stage 1 checkpoint lacks a model state")
    checkpoint_config = payload.get("model_config")
    model_config = getattr(getattr(model, "config", None), "to_dict", lambda: None)()
    if checkpoint_config is not None:
        if not isinstance(checkpoint_config, dict):
            raise ValueError("Stage 1 checkpoint model configuration is malformed")
        normalized_checkpoint_config = ThermoFormerConfig(**checkpoint_config).to_dict()
        if normalized_checkpoint_config != model_config:
            raise ValueError("Stage 1 checkpoint model configuration does not match C1")
    for key, expected in (expected_provenance or {}).items():
        if payload.get(key) != expected:
            raise ValueError(
                f"Stage 1 checkpoint {key} does not match the current formal input"
            )
    model.load_state_dict(payload["model"], strict=True)
    return artifact_sha256(checkpoint_path)


def fit_physics_stage(
    model: nn.Module,
    train_samples: Sequence[VLESample],
    feature_map: dict[str, np.ndarray],
    config: TrainingConfig,
    finetuning: PhysicsFineTuningConfig,
    device: torch.device,
    *,
    validation_samples: Sequence[VLESample],
    pure_property_catalog: PurePropertyCatalog | None = None,
) -> PhysicsFitResult:
    """Fine-tune from the already-loaded Stage 1 best using validation only."""
    if not validation_samples:
        raise ValueError("Physics checkpoint selection requires validation samples")
    seed_everything(config.seed)
    model.to(device)
    train_loader = _loader(
        train_samples, feature_map, config, True, pure_property_catalog
    )
    validation_loader = _loader(
        validation_samples, feature_map, config, False, pure_property_catalog
    )
    stage1_state = _cpu_state(model)
    stage1_validation = _run_epoch(
        model, validation_loader, device, config, None
    )["total"]
    setup = configure_physics_finetuning(model, config, finetuning)
    parameter_summary = setup.record()
    print(json.dumps({"physics_finetuning_parameters": parameter_summary}, sort_keys=True))

    history: list[dict[str, object]] = []
    stage2_state = _cpu_state(model)
    stage2_validation = math.inf
    epochs_without_improvement = 0
    for epoch in range(1, config.epochs_physics + 1):
        scale = physics_warmup_scale(epoch, finetuning.warmup_epochs)
        train_metrics = _run_epoch(
            model,
            train_loader,
            device,
            config,
            setup.optimizer,
            physics_scale=scale,
            teacher_forced_fugacity_weight=(
                finetuning.teacher_forced_fugacity_weight or 0.0
            ),
        )
        validation_metrics = _run_epoch(
            model, validation_loader, device, config, None
        )
        history.append(
            {
                "stage": "physics",
                "epoch": epoch,
                "train": train_metrics,
                "validation": validation_metrics,
            }
        )
        if validation_metrics["total"] < stage2_validation - config.validation_min_delta:
            stage2_validation = validation_metrics["total"]
            stage2_state = _cpu_state(model)
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1
        if (
            config.early_stopping_patience > 0
            and epoch >= config.minimum_physics_epochs
            and epochs_without_improvement >= config.early_stopping_patience
        ):
            history[-1]["early_stopped"] = True
            break

    selected_stage = (
        "stage2"
        if stage2_validation < stage1_validation - config.validation_min_delta
        else "stage1"
    )
    selected_state = stage2_state if selected_stage == "stage2" else stage1_state
    model.load_state_dict(selected_state)
    return PhysicsFitResult(
        state_dict=selected_state,
        stage_states={"stage1": stage1_state, "stage2": stage2_state},
        history=history,
        selected_stage=selected_stage,
        stage_validation_losses={
            "stage1": stage1_validation,
            "stage2": stage2_validation,
        },
        parameter_summary=parameter_summary,
        best_validation_loss=min(stage1_validation, stage2_validation),
    )


def evaluate_physics_residuals(
    model: nn.Module,
    samples: Sequence[VLESample],
    feature_map: dict[str, np.ndarray],
    config: TrainingConfig,
    device: torch.device,
    *,
    pure_property_catalog: PurePropertyCatalog | None = None,
) -> dict[str, float]:
    """Evaluate raw thermodynamic residuals without updating parameters."""
    loader = _loader(
        samples, feature_map, config, False, pure_property_catalog
    )
    model.to(device).eval()
    total_fugacity = 0.0
    count = 0
    for host_batch in loader:
        batch = host_batch.to(device)
        with torch.enable_grad():
            objective = physics_finetune_objective(
                model,
                batch,
                config,
                physics_scale=1.0,
                teacher_forced_fugacity_weight=1.0,
            )
        size = batch.x.shape[0]
        count += size
        total_fugacity += float(
            objective.teacher_forced_fugacity.detach().cpu()
        ) * size
    if count == 0:
        raise ValueError("Physics residual evaluation requires samples")
    return {"teacher_forced_fugacity": total_fugacity / count}


def summarize_physics_finetuning(
    comparison_paths: Sequence[Path],
    *,
    expected_evaluation_partition: str = "test",
) -> dict[str, object]:
    """Aggregate paired Stage-1/Stage-2 evidence over fixed random seeds."""
    if not comparison_paths:
        raise ValueError("At least one stage comparison is required")
    payloads: list[tuple[int, dict[str, object]]] = []
    for path in comparison_paths:
        seed_label = path.parent.name
        if not seed_label.startswith("seed_"):
            raise ValueError(f"Cannot infer seed from {path}")
        seed = int(seed_label.removeprefix("seed_"))
        payload = json.loads(path.read_text(encoding="utf-8"))
        if (
            payload.get("selection_partition") != "validation"
            or payload.get("evaluation_partition") != expected_evaluation_partition
        ):
            raise RuntimeError(f"Invalid selection/evaluation partition for seed {seed}")
        weights = payload.get("thermodynamic_loss_weights", {})
        if float(weights.get("teacher_forced_fugacity", 0.0)) != 1.0 or any(
            float(value) != 0.0
            for name, value in weights.items()
            if name != "teacher_forced_fugacity"
        ):
            raise RuntimeError(f"Seed {seed} is not fugacity-only")
        payloads.append((seed, payload))
    payloads.sort(key=lambda item: item[0])
    seeds = [seed for seed, _ in payloads]
    if len(seeds) != len(set(seeds)):
        raise ValueError("Stage comparisons contain duplicate seeds")

    def stats(values: Sequence[float]) -> dict[str, float]:
        return {
            "mean": fmean(values),
            "std": stdev(values) if len(values) > 1 else 0.0,
        }

    def optional_stats(values: Sequence[object]) -> dict[str, float | None]:
        available = [float(value) for value in values if value is not None]
        return stats(available) if available else {"mean": None, "std": None}

    def direction(payload: dict[str, object], stage: str, name: str) -> dict[str, object]:
        return next(
            row
            for row in payload["stages"][stage]["metrics"]
            if row.get("scope") == "direction" and row.get("direction") == name
        )

    metric_keys = {
        "isothermal": (
            "pressure_mae_kpa", "pressure_rmse_kpa", "pressure_r2",
            "y_mae", "y_rmse", "y_r2", "valid_coverage",
            "solver_failure_rate", "nonphysical_rate",
        ),
        "isobaric": (
            "temperature_mae_k", "temperature_rmse_k", "temperature_r2",
            "y_mae", "y_rmse", "y_r2", "valid_coverage",
            "solver_failure_rate", "nonphysical_rate",
        ),
    }
    stages: dict[str, object] = {}
    for stage in ("stage1", "stage2"):
        directions: dict[str, object] = {}
        for name, keys in metric_keys.items():
            directions[name] = {
                key: optional_stats(
                    [direction(payload, stage, name).get(key) for _, payload in payloads]
                )
                for key in keys
            }
        stages[stage] = {
            "validation_loss": stats(
                [float(payload["stages"][stage]["validation_loss"]) for _, payload in payloads]
            ),
            "teacher_forced_fugacity": stats(
                [
                    float(payload["stages"][stage]["physics_residuals"]["teacher_forced_fugacity"])
                    for _, payload in payloads
                ]
            ),
            "directions": directions,
        }
    selected_counts = {
        stage: sum(payload["selected_stage"] == stage for _, payload in payloads)
        for stage in ("stage1", "stage2")
    }
    parameter_summary = payloads[0][1]["parameter_summary"]
    if any(payload["parameter_summary"] != parameter_summary for _, payload in payloads[1:]):
        raise RuntimeError("Fine-tuning parameter summaries differ across seeds")
    return {
        "seeds": seeds,
        "selected_stage_counts": selected_counts,
        "parameter_summary": parameter_summary,
        "stages": stages,
        "inputs": [
            {"seed": seed, "sha256": artifact_sha256(path)}
            for (seed, _), path in zip(payloads, sorted(comparison_paths, key=lambda p: int(p.parent.name.removeprefix('seed_'))))
        ],
    }


def write_multiseed_physics_finetune_report(
    comparison_paths: Sequence[Path],
    report_path: Path,
    *,
    expected_evaluation_partition: str = "test",
) -> tuple[Path, dict[str, object]]:
    """Write the paired multi-seed fugacity fine-tuning report atomically."""
    summary = summarize_physics_finetuning(
        comparison_paths,
        expected_evaluation_partition=expected_evaluation_partition,
    )
    stages = summary["stages"]

    def value(stage: str, direction_name: str, key: str) -> str:
        record = stages[stage]["directions"][direction_name][key]
        if record["mean"] is None:
            return "N/A"
        return f"{record['mean']:.6f} ± {record['std']:.6f}"

    rows = (
        ("P, isothermal", "isothermal", "pressure_mae_kpa", "pressure_rmse_kpa", "pressure_r2"),
        ("y, isothermal", "isothermal", "y_mae", "y_rmse", "y_r2"),
        ("T, isobaric", "isobaric", "temperature_mae_k", "temperature_rmse_k", "temperature_r2"),
        ("y, isobaric", "isobaric", "y_mae", "y_rmse", "y_r2"),
    )
    lines = [
        "# C1 fugacity-equilibrium fine-tuning (five seeds)",
        "",
        "Protocol: `overall_binary_ternary`; seeds: `0--4`; checkpoint selection: validation only.",
        "",
        "| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for label, direction_name, mae, rmse, r2 in rows:
        lines.append(
            f"| {label} | {value('stage1', direction_name, mae)} | "
            f"{value('stage1', direction_name, rmse)} | {value('stage1', direction_name, r2)} | "
            f"{value('stage2', direction_name, mae)} | {value('stage2', direction_name, rmse)} | "
            f"{value('stage2', direction_name, r2)} |"
        )
    counts = summary["selected_stage_counts"]
    residual1 = stages["stage1"]["teacher_forced_fugacity"]
    residual2 = stages["stage2"]["teacher_forced_fugacity"]
    lines.extend(
        [
            "",
            f"Validation selected Stage 2 for **{counts['stage2']}/5** seeds and Stage 1 for **{counts['stage1']}/5** seeds.",
            "Teacher-forced fugacity residual: "
            f"Stage 1 `{residual1['mean']:.6g} ± {residual1['std']:.6g}`; "
            f"Stage 2 `{residual2['mean']:.6g} ± {residual2['std']:.6g}`.",
            "",
        ]
    )
    atomic_write_text(report_path, "\n".join(lines))
    return report_path, summary
