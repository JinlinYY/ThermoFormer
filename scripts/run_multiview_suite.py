"""Run staged multi-view ThermoFormer experiments without touching legacy results."""

from __future__ import annotations

import argparse
import gc
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_experiment_config
from src.multiview_protocols import (
    FORMAL_PROTOCOLS,
    FORMAL_VARIANTS,
    MULTIVIEW_SEEDS,
    MULTIVIEW_VARIANTS,
    SCREENING_PROTOCOLS,
    SCREENING_VARIANTS,
    SMOKE_VARIANTS,
)
from src.paper_runner import result_protocol_name, run_paper_experiment
from src.representation import encoder_cache_filename
from src.results import aggregate_protocol_results


def release_accelerator_memory() -> None:
    """Release per-run CUDA caches before the next experiment."""
    gc.collect()
    try:
        import torch
    except ImportError:
        return
    if torch.cuda.is_available():
        torch.cuda.synchronize()
        torch.cuda.empty_cache()


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--stage", choices=("smoke", "screening", "formal"), required=True)
    value.add_argument("--variant", action="append", choices=sorted(MULTIVIEW_VARIANTS))
    value.add_argument("--protocol", action="append")
    value.add_argument("--seeds", type=int, nargs="+")
    value.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    value.add_argument("--artifact-root", type=Path, default=PROJECT_ROOT)
    value.add_argument("--overwrite", action="store_true")
    value.add_argument(
        "--exploratory", action="store_true",
        help="Allow an off-matrix diagnostic and isolate it from locked stage artifacts",
    )
    return value


def _matrix(stage: str) -> tuple[tuple[str, ...], tuple[str, ...], tuple[int, ...]]:
    if stage == "smoke":
        return SMOKE_VARIANTS, ("overall_binary_ternary",), (0,)
    if stage == "screening":
        return SCREENING_VARIANTS, SCREENING_PROTOCOLS, (0,)
    return FORMAL_VARIANTS, FORMAL_PROTOCOLS, MULTIVIEW_SEEDS


def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    default_variants, default_protocols, default_seeds = _matrix(args.stage)
    variants = tuple(args.variant or default_variants)
    protocols = tuple(args.protocol or default_protocols)
    seeds = tuple(args.seeds or default_seeds)
    if len(seeds) != len(set(seeds)) or not set(seeds).issubset(MULTIVIEW_SEEDS):
        raise ValueError("Multi-view seeds must be a unique subset of 0--4")
    if not args.exploratory:
        if not set(variants).issubset(default_variants):
            raise ValueError(f"{args.stage} variants must stay within the locked stage matrix")
        if not set(protocols).issubset(default_protocols):
            raise ValueError(f"{args.stage} protocols must stay within the locked stage matrix")
        if seeds != default_seeds:
            raise ValueError(f"{args.stage} seeds must be exactly {default_seeds}")
    elif args.stage == "formal":
        raise ValueError("Off-matrix experiments cannot use the formal namespace")
    artifact_root = args.artifact_root.resolve()
    namespace = f"{args.stage}_exploratory" if args.exploratory else args.stage
    run_root = artifact_root / "runs" / "multiview" / namespace
    checkpoint_root = artifact_root / "checkpoints" / "multiview" / namespace
    results_root = artifact_root / "results" / "multiview" / namespace / "runs"
    overrides = (
        "training.epochs_supervised=2",
        "training.epochs_physics=1",
        "training.solver_iterations_train=2",
        "training.solver_iterations_eval=4",
    ) if args.stage == "smoke" else ()
    for variant_id in variants:
        variant = MULTIVIEW_VARIANTS[variant_id]
        if variant.reference:
            print(json.dumps({"variant": variant_id, "status": "reuses_legacy_reference"}))
            continue
        config_path = PROJECT_ROOT / variant.config
        experiment = load_experiment_config(config_path, overrides)
        feature_cache = artifact_root / "cache" / encoder_cache_filename(experiment.encoder)
        for split_protocol in protocols:
            protocol = result_protocol_name(experiment.name, split_protocol)
            for seed in seeds:
                try:
                    manifest = run_paper_experiment(
                        config_path=config_path,
                        split_path=PROJECT_ROOT / "splits" / split_protocol / f"seed_{seed}.json",
                        seed=seed,
                        run_root=run_root,
                        checkpoint_root=checkpoint_root,
                        results_root=results_root,
                        feature_cache=feature_cache,
                        device_name=args.device,
                        overrides=overrides,
                        allow_overwrite=args.overwrite,
                        run_kind="smoke" if args.stage == "smoke" else "formal",
                    )
                finally:
                    release_accelerator_memory()
                print(json.dumps({
                    "variant": variant_id,
                    "protocol": split_protocol,
                    "seed": seed,
                    "status": manifest["status"],
                    "training_seconds": manifest["training_seconds"],
                }))
            if args.stage == "formal":
                aggregate_protocol_results(
                    results_root / protocol,
                    expected_seeds=MULTIVIEW_SEEDS,
                )


if __name__ == "__main__":
    main()
