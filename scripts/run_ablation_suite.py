"""Run the locked ThermoFormer ablation matrix on committed paper splits."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ablation_protocols import ABLATION_SEEDS, ABLATION_VARIANTS
from src.config import load_experiment_config
from src.paper_runner import (
    requested_run_fingerprint,
    result_protocol_name,
    run_paper_experiment,
)
from src.results import aggregate_protocol_results


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--variant", action="append", choices=sorted(ABLATION_VARIANTS))
    value.add_argument("--seeds", type=int, nargs="+", default=list(ABLATION_SEEDS))
    value.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    value.add_argument("--artifact-root", type=Path, default=PROJECT_ROOT)
    value.add_argument("--overwrite", action="store_true")
    value.add_argument("--smoke", action="store_true")
    return value


def validate_seeds(seeds: list[int]) -> tuple[int, ...]:
    if len(seeds) != len(set(seeds)):
        raise ValueError("Ablation seeds must be unique")
    invalid = sorted(set(seeds) - set(ABLATION_SEEDS))
    if invalid:
        raise ValueError(f"Formal ablation seeds are locked to 0--4; invalid: {invalid}")
    return tuple(seeds)


def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    seeds = validate_seeds(args.seeds)
    variants = args.variant or [name for name, item in ABLATION_VARIANTS.items() if not item.reference]
    artifact_root = args.artifact_root.resolve()
    suffix = "ablation_smoke" if args.smoke else "ablation"
    run_root = artifact_root / "runs" / suffix
    checkpoint_root = artifact_root / "checkpoints" / suffix
    results_root = artifact_root / "results" / suffix / "runs"
    overrides = (
        "training.epochs_supervised=2",
        "training.epochs_physics=1",
        "training.solver_iterations_train=2",
        "training.solver_iterations_eval=4",
    ) if args.smoke else ()
    for variant_name in variants:
        variant = ABLATION_VARIANTS[variant_name]
        if variant.reference:
            print(json.dumps({"variant": variant_name, "status": "reuses_reference"}))
            continue
        config_path = PROJECT_ROOT / variant.config
        experiment = load_experiment_config(config_path, overrides)
        feature_cache = (
            artifact_root / "cache" / "rdkit_2d_scaled24_v1.npz"
            if experiment.encoder.representation == "rdkit_2d"
            else artifact_root / "cache" / "unimolv2_84m.npz"
        )
        for benchmark in variant.benchmarks:
            result_protocol = result_protocol_name(experiment.name, benchmark)
            split_root = PROJECT_ROOT / "splits" / benchmark
            for seed in seeds:
                split_path = split_root / f"seed_{seed}.json"
                manifest_path = results_root / result_protocol / f"seed_{seed}" / "manifest.json"
                if manifest_path.is_file() and not args.overwrite:
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                    expected_status = "smoke" if args.smoke else "completed"
                    if manifest.get("status") == expected_status:
                        fingerprint = requested_run_fingerprint(
                            config_path,
                            split_path,
                            seed,
                            feature_cache,
                            args.device,
                            overrides,
                            "smoke" if args.smoke else "formal",
                        )
                        if manifest.get("request_sha256") != fingerprint:
                            raise RuntimeError(
                                f"Stale ablation provenance for {result_protocol}/seed_{seed}; "
                                "rerun with --overwrite"
                            )
                        print(json.dumps({"protocol": result_protocol, "seed": seed, "status": "skipped"}))
                        continue
                manifest = run_paper_experiment(
                    config_path=config_path,
                    split_path=split_path,
                    seed=seed,
                    run_root=run_root,
                    checkpoint_root=checkpoint_root,
                    results_root=results_root,
                    feature_cache=feature_cache,
                    device_name=args.device,
                    overrides=overrides,
                    allow_overwrite=args.overwrite,
                    run_kind="smoke" if args.smoke else "formal",
                )
                print(
                    json.dumps(
                        {
                            "protocol": result_protocol,
                            "seed": seed,
                            "status": manifest["status"],
                            "seconds": manifest["training_seconds"],
                        }
                    )
                )
            if not args.smoke and set(seeds) == set(ABLATION_SEEDS):
                aggregate_protocol_results(
                    results_root / result_protocol,
                    expected_seeds=seeds,
                )


if __name__ == "__main__":
    main()
