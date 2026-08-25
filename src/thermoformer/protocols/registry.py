"""Single registry for every confirmatory ThermoFormer paper protocol."""

from __future__ import annotations


PAPER_SEEDS = (0, 1, 2, 3, 4)

PROTOCOL_CONFIGS = {
    "overall_binary": "experiments/predictive_performance/overall_binary/config.yaml",
    "overall_binary_ternary": "experiments/predictive_performance/overall_binary_ternary/config.yaml",
    "state_composition_interpolation": "experiments/predictive_performance/state_generalization/config.yaml",
    "state_composition_edge_extrapolation": "experiments/predictive_performance/state_generalization/config.yaml",
    "state_temperature_low_extrapolation": "experiments/predictive_performance/state_generalization/config.yaml",
    "state_temperature_high_extrapolation": "experiments/predictive_performance/state_generalization/config.yaml",
    "state_pressure_low_extrapolation": "experiments/predictive_performance/state_generalization/config.yaml",
    "state_pressure_high_extrapolation": "experiments/predictive_performance/state_generalization/config.yaml",
    "unseen_component": "experiments/predictive_performance/unseen_components/config.yaml",
    "binary_to_ternary_zero_shot": "experiments/predictive_performance/binary_to_ternary/config.yaml",
    "binary_to_ternary_scale_0.05": "experiments/predictive_performance/binary_to_ternary/config.yaml",
    "binary_to_ternary_scale_0.1": "experiments/predictive_performance/binary_to_ternary/config.yaml",
    "binary_to_ternary_scale_0.25": "experiments/predictive_performance/binary_to_ternary/config.yaml",
    "binary_to_ternary_scale_0.5": "experiments/predictive_performance/binary_to_ternary/config.yaml",
    "binary_to_ternary_scale_1": "experiments/predictive_performance/binary_to_ternary/config.yaml",
}
