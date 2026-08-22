"""Locked variants and staged evaluation matrix for multi-view ThermoFormer."""

from __future__ import annotations

from typing import NamedTuple


class MultiViewVariant(NamedTuple):
    label: str
    config: str
    reference: bool = False


MULTIVIEW_VARIANTS = {
    "v0_legacy_unimol": MultiViewVariant(
        "V0 Legacy Uni-Mol v2", "experiments/multiview/representations/v0_legacy_unimol/config.json", True
    ),
    "v1_rdkit_only": MultiViewVariant(
        "V1 RDKit descriptors only", "experiments/multiview/representations/v1_rdkit_only/config.json"
    ),
    "v2_unimol_only": MultiViewVariant(
        "V2 Uni-Mol v2 unified interface", "experiments/multiview/representations/v2_unimol_only/config.json"
    ),
    "v3_functional_group_only": MultiViewVariant(
        "V3 Functional groups only", "experiments/multiview/representations/v3_functional_group_only/config.json"
    ),
    "v4_rdkit_unimol_naive": MultiViewVariant(
        "V4 RDKit + Uni-Mol naive fusion", "experiments/multiview/representations/v4_rdkit_unimol_naive/config.json"
    ),
    "v5_three_view_naive": MultiViewVariant(
        "V5 Three-view naive fusion", "experiments/multiview/representations/v5_three_view_naive/config.json"
    ),
    "v6_full_interaction": MultiViewVariant(
        "V6 Interaction-specific multi-view fusion", "experiments/multiview/representations/v6_full_interaction/config.json"
    ),
}

SMOKE_VARIANTS = (
    "v1_rdkit_only",
    "v4_rdkit_unimol_naive",
    "v5_three_view_naive",
    "v6_full_interaction",
)
SCREENING_VARIANTS = (
    "v0_legacy_unimol",
    "v1_rdkit_only",
    "v4_rdkit_unimol_naive",
    "v5_three_view_naive",
    "v6_full_interaction",
)
# V3 was added after the locked screen solely to complete the representation
# table. It lives in an exploratory namespace and cannot alter Stage C selection.
EXPLORATORY_SCREENING_VARIANTS = ("v3_functional_group_only",)
SCREENING_REPORT_VARIANTS = (*SCREENING_VARIANTS, *EXPLORATORY_SCREENING_VARIANTS)
FORMAL_VARIANTS = (
    "v1_rdkit_only",
    "v5_three_view_naive",
    "v6_full_interaction",
)
SCREENING_PROTOCOLS = (
    "overall_binary",
    "overall_binary_ternary",
    "state_composition_interpolation",
    "unseen_component",
    "binary_to_ternary_zero_shot",
)
FORMAL_PROTOCOLS = (
    "overall_binary_ternary",
    "unseen_component",
    "binary_to_ternary_zero_shot",
)
# Table-1-style predictive comparison requested after the original staged
# campaign. V0 is reused from the frozen reference and V2 is an explicit alias
# of V0, so only the scientifically distinct trainable variants run here.
PREDICTIVE_VARIANTS = (
    "v1_rdkit_only",
    "v3_functional_group_only",
    "v4_rdkit_unimol_naive",
    "v5_three_view_naive",
    "v6_full_interaction",
)
PREDICTIVE_PROTOCOLS = (
    "overall_binary",
    "overall_binary_ternary",
)
MULTIVIEW_SEEDS = (0, 1, 2, 3, 4)
