"""Generate every fixed, digest-checked split used by paper experiments."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data import load_vle_dataset, retain_pure_anchored_systems
from src.protocols import (
    binary_to_ternary_split,
    composition_edge_split,
    composition_interpolation_split,
    overall_system_split,
    protect_pure_reference_systems,
    state_extreme_split,
    unseen_component_split,
)
from src.paper_protocols import PAPER_SEEDS
from src.splits import DatasetPartitions, load_split_assignment, save_split_assignment


SEEDS = PAPER_SEEDS
TERNARY_FRACTIONS = (0.0, 0.05, 0.10, 0.25, 0.50, 1.0)


def _protocols(samples, seed: int) -> list[DatasetPartitions]:
    protocols = [
        overall_system_split(
            samples,
            seed,
            component_counts=(2,),
            minimum_anchor_temperatures=2,
            protocol="overall_binary",
        ),
        overall_system_split(
            samples,
            seed,
            component_counts=(2, 3),
            minimum_anchor_temperatures=2,
            protocol="overall_binary_ternary",
        ),
        unseen_component_split(samples, seed, minimum_anchor_temperatures=2),
    ]
    state_protocols = [
        composition_interpolation_split(samples, seed),
        composition_edge_split(samples, seed),
        state_extreme_split(samples, "temperature", "low", seed),
        state_extreme_split(samples, "temperature", "high", seed),
        state_extreme_split(samples, "pressure", "low", seed),
        state_extreme_split(samples, "pressure", "high", seed),
    ]
    all_components = {smiles for row in samples for smiles in row.smiles}
    protocols.extend(
        protect_pure_reference_systems(
            samples,
            split,
            minimum_temperatures=2,
            allowed_components=all_components,
            required_components=all_components,
        )
        for split in state_protocols
    )
    protocols.extend(
        binary_to_ternary_split(
            samples,
            seed,
            fraction,
            minimum_anchor_temperatures=2,
        )
        for fraction in TERNARY_FRACTIONS
    )
    return protocols


def main() -> None:
    loaded = load_vle_dataset(
        PROJECT_ROOT / "dataset",
        failed_weight=0.0,
        max_pressure_kpa=500.0,
    )
    samples = retain_pure_anchored_systems(
        loaded.samples,
        minimum_temperatures=2,
    )
    summary: dict[str, dict[str, object]] = {}
    for seed in SEEDS:
        for split in _protocols(samples, seed):
            path = PROJECT_ROOT / "splits" / split.protocol / f"seed_{seed}.json"
            save_split_assignment(path, samples, split)
            restored = load_split_assignment(path, samples)
            if restored != split:
                raise RuntimeError(f"Split round-trip mismatch: {path}")
            summary[f"{split.protocol}/seed_{seed}"] = split.metadata
    index = PROJECT_ROOT / "splits" / "index.json"
    index.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "dataset_rows": len(samples),
                "seeds": list(SEEDS),
                "artifacts": len(summary),
                "index": str(index),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
