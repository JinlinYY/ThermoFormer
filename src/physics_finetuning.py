"""Partial physics fine-tuning from a frozen supervised ThermoFormer checkpoint."""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import torch
from torch import nn

from .artifacts import artifact_sha256
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
    solver_enabled: bool,
) -> Objective:
    """Supervised objective plus the three scaled physics terms."""
    return _objective(
        model,
        batch,
        config,
        physics=True,
        solver_enabled=solver_enabled,
        physics_scale=physics_scale,
    )


def load_stage1_checkpoint(model: nn.Module, checkpoint_path: Path) -> str:
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
        model, validation_loader, device, config, None, False
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
            True,
            physics_scale=scale,
        )
        validation_metrics = _run_epoch(
            model, validation_loader, device, config, None, False
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
    """Evaluate raw continuity/boundary residuals without updating parameters."""
    loader = _loader(
        samples, feature_map, config, False, pure_property_catalog
    )
    model.to(device).eval()
    totals = {"continuity": 0.0, "boundary": 0.0}
    count = 0
    for host_batch in loader:
        batch = host_batch.to(device)
        with torch.enable_grad():
            objective = physics_finetune_objective(
                model,
                batch,
                config,
                physics_scale=1.0,
                solver_enabled=False,
            )
        size = batch.x.shape[0]
        count += size
        totals["continuity"] += float(objective.continuity.detach().cpu()) * size
        totals["boundary"] += float(objective.boundary.detach().cpu()) * size
    if count == 0:
        raise ValueError("Physics residual evaluation requires samples")
    return {name: value / count for name, value in totals.items()}


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


def write_physics_finetune_report(
    comparison_path: Path,
    report_path: Path,
) -> Path:
    """Render the task-resolved Stage 1/Stage 2 comparison atomically."""
    payload = json.loads(comparison_path.read_text(encoding="utf-8"))
    stages = payload["stages"]

    def direction(stage: str, name: str) -> dict[str, object]:
        return next(
            row
            for row in stages[stage]["metrics"]
            if row.get("scope") == "direction" and row.get("direction") == name
        )

    stage1_isothermal = direction("stage1", "isothermal")
    stage1_isobaric = direction("stage1", "isobaric")
    stage2_isothermal = direction("stage2", "isothermal")
    stage2_isobaric = direction("stage2", "isobaric")

    def metric(row: dict[str, object], key: str) -> str:
        value = row.get(key)
        return "N/A" if value is None else f"{float(value):.6f}"

    metric_rows = (
        ("P, isothermal", "pressure", "_kpa", stage1_isothermal, stage2_isothermal),
        ("y, isothermal", "y", "", stage1_isothermal, stage2_isothermal),
        ("T, isobaric", "temperature", "_k", stage1_isobaric, stage2_isobaric),
        ("y, isobaric", "y", "", stage1_isobaric, stage2_isobaric),
    )
    lines = [
        "# C1 partial physics fine-tuning",
        "",
        "Protocol: `overall_binary_ternary`; seed: `0`; checkpoint selection: validation only.",
        "",
        "| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for label, key, suffix, first, second in metric_rows:
        lines.append(
            f"| {label} | {metric(first, key + '_mae' + suffix)} | "
            f"{metric(first, key + '_rmse' + suffix)} | {metric(first, key + '_r2')} | "
            f"{metric(second, key + '_mae' + suffix)} | "
            f"{metric(second, key + '_rmse' + suffix)} | {metric(second, key + '_r2')} |"
        )
    lines.extend(
        [
            "",
            "| diagnostic | Stage 1 | Stage 2 |",
            "|---|---:|---:|",
        ]
    )
    for label, key in (
        ("solver failure rate", "solver_failure_rate"),
        ("nonphysical rate", "nonphysical_rate"),
    ):
        first = next(row for row in stages["stage1"]["metrics"] if row["scope"] == "all")
        second = next(row for row in stages["stage2"]["metrics"] if row["scope"] == "all")
        lines.append(f"| {label} | {float(first[key]):.6g} | {float(second[key]):.6g} |")
    for label, key in (
        ("continuity residual", "continuity"),
        ("boundary residual", "boundary"),
    ):
        lines.append(
            f"| {label} | {float(stages['stage1']['physics_residuals'][key]):.6g} | "
            f"{float(stages['stage2']['physics_residuals'][key]):.6g} |"
        )
    summary = payload["parameter_summary"]
    lines.extend(
        [
            "",
            f"Total parameters: **{int(summary['total_parameters']):,}**.",
            f"Fine-tuned parameters: **{int(summary['trainable_parameters']):,}** "
            f"(**{100.0 * float(summary['trainable_fraction']):.3f}%**).",
            "",
            "| unfrozen group | parameters | learning rate |",
            "|---|---:|---:|",
        ]
    )
    for group in summary["groups"]:
        lines.append(
            f"| {group['name']} | {int(group['parameter_count']):,} | "
            f"{float(group['learning_rate']):.2g} |"
        )
    lines.extend(
        [
            "",
            f"Stage 1 validation loss: `{float(stages['stage1']['validation_loss']):.8g}`.",
            f"Stage 2 validation loss: `{float(stages['stage2']['validation_loss']):.8g}`.",
            f"Selected final checkpoint: **{payload['selected_stage']}**.",
            "",
            "The test partition was evaluated only after validation-only checkpoint selection.",
            "",
        ]
    )
    _atomic_text(report_path, "\n".join(lines))
    return report_path
