"""Immutable architecture/physics ablation registry."""

from __future__ import annotations

from typing import NamedTuple


class AblationVariant(NamedTuple):
    label: str
    family: str
    config: str
    benchmarks: tuple[str, ...]
    reference: bool = False


CORE_BENCHMARKS = (
    "overall_binary_ternary",
    "unseen_component",
    "binary_to_ternary_zero_shot",
)

ABLATION_VARIANTS = {
    "a0_full": AblationVariant(
        "A0 Full hybrid ThermoFormer",
        "architecture",
        "experiments/ablation/architecture/a0_full/config.json",
        CORE_BENCHMARKS,
    ),
    "a1_unimol_v2": AblationVariant(
        "A1a Uni-Mol v2 only",
        "architecture",
        "experiments/ablation/architecture/a1_unimol_v2/config.json",
        CORE_BENCHMARKS,
        True,
    ),
    "a1_rdkit_descriptors": AblationVariant(
        "A1b RDKit descriptors only",
        "architecture",
        "experiments/ablation/architecture/a1_rdkit_descriptors/config.json",
        ("overall_binary_ternary",),
    ),
    "a1_no_rdkit_descriptors": AblationVariant(
        "A1c Hybrid without RDKit descriptors",
        "architecture",
        "experiments/ablation/architecture/a1_no_rdkit_descriptors/config.json",
        ("overall_binary_ternary",),
    ),
    "a1_no_unimol": AblationVariant(
        "A1d Hybrid without Uni-Mol v2",
        "architecture",
        "experiments/ablation/architecture/a1_no_unimol/config.json",
        ("overall_binary_ternary",),
    ),
    "a1_no_functional_groups": AblationVariant(
        "A1e Hybrid without functional groups",
        "architecture",
        "experiments/ablation/architecture/a1_no_functional_groups/config.json",
        ("overall_binary_ternary",),
    ),
    "a2_no_interaction": AblationVariant(
        "A2 No multicomponent interaction",
        "architecture",
        "experiments/ablation/architecture/a2_no_interaction/config.json",
        CORE_BENCHMARKS,
    ),
    "a3_pairwise_only": AblationVariant(
        "A3 Pairwise-only interaction",
        "architecture",
        "experiments/ablation/architecture/a3_pairwise_only/config.json",
        CORE_BENCHMARKS,
    ),
    "a4_condition_concatenation": AblationVariant(
        "A4 Condition concatenation",
        "architecture",
        "experiments/ablation/architecture/a4_condition_concatenation/config.json",
        ("overall_binary_ternary",),
    ),
    "a5_direct_activity": AblationVariant(
        "A5 Direct activity decoding",
        "architecture",
        "experiments/ablation/architecture/a5_direct_activity/config.json",
        ("overall_binary_ternary",),
    ),
    "a6_direct_vle": AblationVariant(
        "A6 Direct VLE prediction",
        "architecture",
        "experiments/ablation/architecture/a6_direct_vle/config.json",
        CORE_BENCHMARKS,
    ),
    "p3_no_pure_boundary": AblationVariant(
        "P3 No near-pure boundary loss",
        "physics",
        "experiments/ablation/thermodynamic_constraint/p3_no_pure_boundary/config.json",
        ("overall_binary_ternary",),
    ),
    "p4_no_phase_continuity": AblationVariant(
        "P4 No phase-continuity loss",
        "physics",
        "experiments/ablation/thermodynamic_constraint/p4_no_phase_continuity/config.json",
        ("overall_binary_ternary",),
    ),
    "p6_no_soft_physics": AblationVariant(
        "P6 No soft thermodynamic losses",
        "physics",
        "experiments/ablation/thermodynamic_constraint/p6_no_soft_physics/config.json",
        ("overall_binary_ternary",),
    ),
}

ABLATION_SEEDS = (0, 1, 2, 3, 4)
