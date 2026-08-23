"""Run the fixed C2 candidate matrix on validation only (seeds 0, 1, 2)."""

from __future__ import annotations

import argparse
import gc
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.c2_optimization import (
    C2_CANDIDATES,
    C2_SELECTION_PROTOCOL,
    C2_SELECTION_SEEDS,
    write_c2_selection_report,
)
from src.config import load_experiment_config
from src.paper_runner import result_protocol_name, run_paper_experiment
from src.representation import encoder_cache_filename
from src.results import aggregate_protocol_results


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    value.add_argument("--artifact-root", type=Path, default=PROJECT_ROOT)
    value.add_argument("--overwrite", action="store_true")
    return value


def _release_accelerator() -> None:
    gc.collect()
    try:
        import torch
    except ImportError:
        return
    if torch.cuda.is_available():
        torch.cuda.synchronize()
        torch.cuda.empty_cache()


def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    artifact_root = args.artifact_root.resolve()
    run_root = artifact_root / "runs/multiview/chemical_attention/selection"
    checkpoint_root = artifact_root / "checkpoints/multiview/chemical_attention/selection"
    results_root = artifact_root / "results/multiview/chemical_attention/selection/runs"
    for candidate, config_value in C2_CANDIDATES.items():
        config_path = PROJECT_ROOT / config_value
        experiment = load_experiment_config(config_path)
        feature_cache = artifact_root / "cache" / encoder_cache_filename(experiment.encoder)
        protocol = result_protocol_name(experiment.name, C2_SELECTION_PROTOCOL)
        for seed in C2_SELECTION_SEEDS:
            try:
                manifest = run_paper_experiment(
                    config_path=config_path,
                    split_path=PROJECT_ROOT / "splits" / C2_SELECTION_PROTOCOL / f"seed_{seed}.json",
                    seed=seed,
                    run_root=run_root,
                    checkpoint_root=checkpoint_root,
                    results_root=results_root,
                    feature_cache=feature_cache,
                    device_name=args.device,
                    allow_overwrite=args.overwrite,
                    run_kind="selection",
                    evaluation_partition="validation",
                )
            finally:
                _release_accelerator()
            print(json.dumps({
                "candidate": candidate,
                "seed": seed,
                "partition": manifest["evaluation_partition"],
                "training_seconds": manifest["training_seconds"],
            }))
        aggregate_protocol_results(
            results_root / protocol,
            expected_seeds=C2_SELECTION_SEEDS,
            aggregate_kind="diagnostic",
        )
    selected = write_c2_selection_report(PROJECT_ROOT, results_root)
    print(json.dumps({"selected_candidate": selected, "test_partition_touched": False}))


if __name__ == "__main__":
    main()
