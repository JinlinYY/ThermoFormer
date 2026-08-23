"""Locked pilot and formal matrices for chemical-attention experiments."""

from __future__ import annotations

from typing import NamedTuple


class ChemicalAttentionVariant(NamedTuple):
    label: str
    config: str


CHEMICAL_ATTENTION_VARIANTS = {
    "c0_current_vanilla": ChemicalAttentionVariant(
        "C0 Current Uni-Mol vanilla Transformer",
        "experiments/multiview/chemical_attention/c0_current_vanilla/config.json",
    ),
    "c1_three_view_vanilla": ChemicalAttentionVariant(
        "C1 RDKit + Uni-Mol + FG, vanilla Transformer",
        "experiments/multiview/chemical_attention/c1_three_view_vanilla/config.json",
    ),
    "c2_chemical_bias_full": ChemicalAttentionVariant(
        "C2 Three-view chemical-biased Transformer",
        "experiments/multiview/chemical_attention/c2_chemical_bias_full/config.json",
    ),
    "c3_no_pair_bias": ChemicalAttentionVariant(
        "C3 Full model without attention pair bias",
        "experiments/multiview/chemical_attention/c3_no_pair_bias/config.json",
    ),
    "c4_no_functional_group": ChemicalAttentionVariant(
        "C4 Full model without functional-group branch",
        "experiments/multiview/chemical_attention/c4_no_functional_group/config.json",
    ),
}

CHEMICAL_ATTENTION_PROTOCOLS = (
    "overall_binary",
    "overall_binary_ternary",
    "unseen_component",
    "binary_to_ternary_zero_shot",
)
CHEMICAL_ATTENTION_SEEDS = (0, 1, 2, 3, 4)

