"""Public research interface for ThermoFormer's scientific modules."""

from .configuration import ExperimentConfig, load_experiment_config
from .data import VLEBatch, VLESample, load_vle_dataset
from .features import build_molecular_encoder, prepare_partition_features
from .model import ModelOutputs, ThermoFormer, ThermoFormerConfig, final_model_config
from .thermodynamics import (
    ConvergenceError,
    EquilibriumState,
    equilibrium_at_tp,
    solve_isobaric,
    solve_isothermal,
)

__all__ = [
    "ConvergenceError",
    "EquilibriumState",
    "ExperimentConfig",
    "ModelOutputs",
    "ThermoFormer",
    "ThermoFormerConfig",
    "VLEBatch",
    "VLESample",
    "build_molecular_encoder",
    "equilibrium_at_tp",
    "final_model_config",
    "load_experiment_config",
    "load_vle_dataset",
    "prepare_partition_features",
    "solve_isobaric",
    "solve_isothermal",
]
