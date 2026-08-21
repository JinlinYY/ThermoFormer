"""Single registry for every confirmatory ThermoFormer paper protocol."""

from __future__ import annotations


PAPER_SEEDS = (0, 1, 2, 3, 4)

PROTOCOL_CONFIGS = {
    "overall_binary": "experiments/predictive_performance/overall_binary/config.json",
    "overall_binary_ternary": "experiments/predictive_performance/overall_binary_ternary/config.json",
    "state_composition_interpolation": "experiments/interpolation_extrapolation/state/composition_interpolation/config.json",
    "state_composition_edge_extrapolation": "experiments/interpolation_extrapolation/state/composition_edge_extrapolation/config.json",
    "state_temperature_low_extrapolation": "experiments/interpolation_extrapolation/state/temperature_low_extrapolation/config.json",
    "state_temperature_high_extrapolation": "experiments/interpolation_extrapolation/state/temperature_high_extrapolation/config.json",
    "state_pressure_low_extrapolation": "experiments/interpolation_extrapolation/state/pressure_low_extrapolation/config.json",
    "state_pressure_high_extrapolation": "experiments/interpolation_extrapolation/state/pressure_high_extrapolation/config.json",
    "unseen_component": "experiments/interpolation_extrapolation/chemical_space/unseen_component/config.json",
    "binary_to_ternary_zero_shot": "experiments/comparison/binary_to_ternary_generalization/zero_shot/config.json",
    "binary_to_ternary_scale_0.05": "experiments/comparison/binary_to_ternary_generalization/scaling/percent_05/config.json",
    "binary_to_ternary_scale_0.1": "experiments/comparison/binary_to_ternary_generalization/scaling/percent_10/config.json",
    "binary_to_ternary_scale_0.25": "experiments/comparison/binary_to_ternary_generalization/scaling/percent_25/config.json",
    "binary_to_ternary_scale_0.5": "experiments/comparison/binary_to_ternary_generalization/scaling/percent_50/config.json",
    "binary_to_ternary_scale_1": "experiments/comparison/binary_to_ternary_generalization/scaling/percent_100/config.json",
}

