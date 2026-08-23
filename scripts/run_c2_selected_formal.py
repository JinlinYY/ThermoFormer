"""Run the frozen validation-selected C2 on the joint test split for seeds 0--4."""

from __future__ import annotations

import argparse
import gc
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.c2_optimization import (
    C2_CANDIDATES,
    C2_SELECTION_PROTOCOL,
    validate_c2_selection,
    write_c2_formal_report,
)
from src.chemical_attention_protocols import CHEMICAL_ATTENTION_SEEDS
from src.config import load_experiment_config
from src.paper_runner import result_protocol_name, run_paper_experiment
from src.representation import encoder_cache_filename
from src.results import aggregate_protocol_results


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    value.add_argument("--artifact-root", type=Path, default=PROJECT_ROOT)
    value.add_argument("--overwrite", action="store_true")
    value.add_argument("--confirm-selection-reviewed", action="store_true")
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
    if not args.confirm_selection_reviewed:
        raise RuntimeError("Formal C2 evaluation requires --confirm-selection-reviewed")
    artifact_root = args.artifact_root.resolve()
    selection_path = (
        artifact_root
        / "results/multiview/chemical_attention/selection/selection_manifest.json"
    )
    selected = validate_c2_selection(PROJECT_ROOT, selection_path)
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(selection_path.relative_to(PROJECT_ROOT))],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if tracked.returncode:
        raise RuntimeError("Formal C2 evaluation requires a committed selection manifest")
    relative_selection = selection_path.relative_to(PROJECT_ROOT).as_posix()
    unchanged = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", relative_selection],
        cwd=PROJECT_ROOT,
    )
    if unchanged.returncode:
        raise RuntimeError("Formal C2 evaluation requires an unchanged committed selection manifest")
    config_path = PROJECT_ROOT / C2_CANDIDATES[selected]
    experiment = load_experiment_config(config_path)
    feature_cache = artifact_root / "cache" / encoder_cache_filename(experiment.encoder)
    run_root = artifact_root / "runs/multiview/chemical_attention/formal_optimized"
    checkpoint_root = (
        artifact_root / "checkpoints/multiview/chemical_attention/formal_optimized"
    )
    results_root = (
        artifact_root / "results/multiview/chemical_attention/formal_optimized/runs"
    )
    protocol = result_protocol_name(experiment.name, C2_SELECTION_PROTOCOL)
    for seed in CHEMICAL_ATTENTION_SEEDS:
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
                run_kind="formal",
                evaluation_partition="test",
            )
        finally:
            _release_accelerator()
        print(json.dumps({
            "candidate": selected,
            "seed": seed,
            "partition": manifest["evaluation_partition"],
            "training_seconds": manifest["training_seconds"],
        }))
    aggregate_protocol_results(
        results_root / protocol,
        expected_seeds=CHEMICAL_ATTENTION_SEEDS,
        aggregate_kind="formal",
    )
    write_c2_formal_report(
        PROJECT_ROOT,
        selection_path,
        results_root / protocol,
        selected,
    )
    print(json.dumps({"selected_candidate": selected, "formal_seeds": [0, 1, 2, 3, 4]}))


if __name__ == "__main__":
    main()
