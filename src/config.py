"""Typed experiment configuration for ThermoFormer training and ablations."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Literal, Sequence

from .model import ThermoFormerConfig
from .training import TrainingConfig


@dataclass(frozen=True)
class EncoderConfig:
    model_size: str = "84m"
    batch_size: int = 16

    def __post_init__(self) -> None:
        if self.model_size not in ("84m", "164m", "310m", "570m", "1.1B"):
            raise ValueError(f"Unsupported Uni-Mol v2 model_size: {self.model_size}")
        if not isinstance(self.batch_size, int) or isinstance(self.batch_size, bool):
            raise ValueError("encoder.batch_size must be an integer")
        if self.batch_size < 1:
            raise ValueError("encoder.batch_size must be positive")


@dataclass(frozen=True)
class DataConfig:
    root: str = "dataset"
    pure_property_catalog: str = ""
    source_filter: str = ""
    failed_weight: float = 0.0
    max_pressure_kpa: float | None = 500.0
    minimum_pure_anchor_temperatures: int = 2

    def __post_init__(self) -> None:
        if any(
            not isinstance(value, str)
            for value in (self.root, self.pure_property_catalog, self.source_filter)
        ):
            raise ValueError(
                "data.root, data.pure_property_catalog, and data.source_filter must be strings"
            )
        if (
            not isinstance(self.failed_weight, (int, float))
            or isinstance(self.failed_weight, bool)
            or not math.isfinite(self.failed_weight)
        ):
            raise ValueError("data.failed_weight must be a finite number")
        if self.max_pressure_kpa is not None and (
            not isinstance(self.max_pressure_kpa, (int, float))
            or isinstance(self.max_pressure_kpa, bool)
            or not math.isfinite(self.max_pressure_kpa)
        ):
            raise ValueError("data.max_pressure_kpa must be a finite number or null")
        if (
            not isinstance(self.minimum_pure_anchor_temperatures, int)
            or isinstance(self.minimum_pure_anchor_temperatures, bool)
        ):
            raise ValueError("data.minimum_pure_anchor_temperatures must be an integer")
        if not 0.0 <= self.failed_weight <= 1.0:
            raise ValueError("data.failed_weight must be between zero and one")
        if self.max_pressure_kpa is not None and self.max_pressure_kpa <= 0.0:
            raise ValueError("data.max_pressure_kpa must be positive or null")
        if self.minimum_pure_anchor_temperatures < 0:
            raise ValueError("data.minimum_pure_anchor_temperatures cannot be negative")


@dataclass(frozen=True)
class EvaluationConfig:
    mode: Literal["kfold", "holdout"] = "kfold"
    folds: int = 5
    test_fraction: float = 0.15
    validation_fraction: float = 0.15

    def __post_init__(self) -> None:
        if self.mode not in ("kfold", "holdout"):
            raise ValueError("evaluation.mode must be 'kfold' or 'holdout'")
        if not isinstance(self.folds, int) or isinstance(self.folds, bool):
            raise ValueError("evaluation.folds must be an integer")
        if self.folds < 2:
            raise ValueError("evaluation.folds must be at least two")
        if any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            for value in (self.test_fraction, self.validation_fraction)
        ):
            raise ValueError("evaluation fractions must be finite numbers")
        if not 0.0 < self.test_fraction < 1.0:
            raise ValueError("evaluation.test_fraction must be between zero and one")
        if not 0.0 < self.validation_fraction < 1.0:
            raise ValueError("evaluation.validation_fraction must be between zero and one")
        if self.test_fraction + self.validation_fraction >= 1.0:
            raise ValueError("test_fraction + validation_fraction must be below one")


@dataclass(frozen=True)
class RuntimeConfig:
    output_dir: str = "runs/thermoformer"
    device: Literal["auto", "cpu", "cuda"] = "auto"
    results_file: str | None = None

    def __post_init__(self) -> None:
        if self.device not in ("auto", "cpu", "cuda"):
            raise ValueError("runtime.device must be auto, cpu, or cuda")
        if not isinstance(self.output_dir, str) or not self.output_dir.strip():
            raise ValueError("runtime.output_dir cannot be empty")
        if self.results_file is not None and (
            not isinstance(self.results_file, str) or not self.results_file.strip()
        ):
            raise ValueError("runtime.results_file must be a non-empty string or null")


@dataclass(frozen=True)
class ExperimentConfig:
    name: str = "thermoformer_base"
    seed: int = 42
    model: ThermoFormerConfig = field(default_factory=ThermoFormerConfig)
    encoder: EncoderConfig = field(default_factory=EncoderConfig)
    data: DataConfig = field(default_factory=DataConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)

    def __post_init__(self) -> None:
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise ValueError("experiment seed must be an integer")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _parse_override(value: str) -> object:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _with_overrides(payload: dict[str, object], overrides: Sequence[str]) -> dict[str, object]:
    updated = json.loads(json.dumps(payload))
    for expression in overrides:
        if "=" not in expression:
            raise ValueError(f"Override must use section.field=value: {expression}")
        dotted_key, raw_value = expression.split("=", 1)
        path = dotted_key.split(".")
        if len(path) != 2:
            raise ValueError(f"Override must address one section and field: {dotted_key}")
        section, field_name = path
        if section not in {"model", "encoder", "data", "evaluation", "training", "runtime"}:
            raise ValueError(f"Unknown configuration section: {section}")
        section_payload = updated.setdefault(section, {})
        if not isinstance(section_payload, dict):
            raise ValueError(f"Cannot override nested field below {section}")
        section_payload[field_name] = _parse_override(raw_value)
    return updated


def _section(section: str, cls: type, value: object) -> object:
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise ValueError(f"Configuration section '{section}' must be an object")
    allowed = {item.name for item in fields(cls)}
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ValueError(f"Unknown {section} configuration fields: {', '.join(unknown)}")
    return cls(**value)


def _deep_merge(
    base: dict[str, object], override: dict[str, object]
) -> dict[str, object]:
    merged = json.loads(json.dumps(base))
    for key, value in override.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = _deep_merge(current, value)
        else:
            merged[key] = value
    return merged


def _load_payload(path: Path, ancestors: tuple[Path, ...] = ()) -> dict[str, object]:
    resolved = path.resolve()
    if resolved in ancestors:
        chain = " -> ".join(str(item) for item in (*ancestors, resolved))
        raise ValueError(f"Cyclic experiment configuration inheritance: {chain}")
    with resolved.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Experiment configuration root must be a JSON object")
    parent_reference = payload.pop("extends", None)
    if parent_reference is None:
        return payload
    if not isinstance(parent_reference, str) or not parent_reference.strip():
        raise ValueError("Configuration 'extends' must be a non-empty path string")
    parent_path = Path(parent_reference)
    if not parent_path.is_absolute():
        parent_path = resolved.parent / parent_path
    parent = _load_payload(parent_path, (*ancestors, resolved))
    return _deep_merge(parent, payload)


def load_experiment_config(
    path: Path,
    overrides: Sequence[str] = (),
) -> ExperimentConfig:
    payload = _load_payload(path)
    payload = _with_overrides(payload, overrides)
    allowed_root = {"name", "seed", "model", "encoder", "data", "evaluation", "training", "runtime"}
    unknown_root = sorted(set(payload) - allowed_root)
    if unknown_root:
        raise ValueError(
            f"Unknown experiment configuration sections: {', '.join(unknown_root)}"
        )
    seed = payload.get("seed", 42)
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("experiment seed must be an integer")
    training_payload = payload.get("training", {})
    if not isinstance(training_payload, dict):
        raise ValueError("Configuration section 'training' must be an object")
    if "seed" in training_payload and training_payload["seed"] != seed:
        raise ValueError("training.seed must match the top-level experiment seed")
    training_payload = {**training_payload, "seed": seed}
    return ExperimentConfig(
        name=str(payload.get("name", "thermoformer_base")),
        seed=seed,
        model=_section("model", ThermoFormerConfig, payload.get("model", {})),
        encoder=_section("encoder", EncoderConfig, payload.get("encoder", {})),
        data=_section("data", DataConfig, payload.get("data", {})),
        evaluation=_section("evaluation", EvaluationConfig, payload.get("evaluation", {})),
        training=_section("training", TrainingConfig, training_payload),
        runtime=_section("runtime", RuntimeConfig, payload.get("runtime", {})),
    )
