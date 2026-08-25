"""Locked variants and staged evaluation matrix for multi-view ThermoFormer."""

from __future__ import annotations

from typing import NamedTuple


class MultiViewVariant(NamedTuple):
    label: str
    config: str


MULTIVIEW_VARIANTS = {
    "v1_rdkit_only": MultiViewVariant(
        "V1 RDKit descriptors only", "experiments/multiview/representations/v1_rdkit_only/config.json"
    ),
    "v3_functional_group_only": MultiViewVariant(
        "V3 Functional groups only", "experiments/multiview/representations/v3_functional_group_only/config.json"
    ),
    "v4_rdkit_unimol_naive": MultiViewVariant(
        "V4 RDKit + Uni-Mol naive fusion", "experiments/multiview/representations/v4_rdkit_unimol_naive/config.json"
    ),
}

PREDICTIVE_VARIANTS = tuple(MULTIVIEW_VARIANTS)
PREDICTIVE_PROTOCOLS = ("overall_binary_ternary",)
MULTIVIEW_SEEDS = (0, 1, 2, 3, 4)
