"""Run fixed ThermoFormer paper protocols and aggregate complete seed sets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.paper_runner import requested_run_fingerprint, run_paper_experiment
from src.paper_protocols import PAPER_SEEDS, PROTOCOL_CONFIGS
from src.config import load_experiment_config
from src.representation import encoder_cache_filename
from src.results import aggregate_protocol_results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", action="append", choices=sorted(PROTOCOL_CONFIGS))
    parser.add_argument("--seeds", type=int, nargs="+", default=list(PAPER_SEEDS))
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    protocols = args.protocol or list(PROTOCOL_CONFIGS)
    if args.smoke:
        run_root = PROJECT_ROOT / "runs" / "suite_smoke" / "paper"
        checkpoint_root = PROJECT_ROOT / "runs" / "suite_smoke" / "checkpoints"
        results_root = PROJECT_ROOT / "runs" / "suite_smoke" / "results"
        overrides = (
            "training.epochs_supervised=2",
            "training.epochs_physics=1",
            "training.solver_iterations_train=2",
            "training.solver_iterations_eval=8",
        )
    else:
        run_root = PROJECT_ROOT / "runs" / "paper"
        checkpoint_root = PROJECT_ROOT / "checkpoints"
        results_root = PROJECT_ROOT / "results"
        overrides = ()
    for protocol in protocols:
        config = PROJECT_ROOT / PROTOCOL_CONFIGS[protocol]
        experiment = load_experiment_config(config, overrides)
        feature_cache = PROJECT_ROOT / "cache" / encoder_cache_filename(experiment.encoder)
        for seed in args.seeds:
            manifest_path = results_root / protocol / f"seed_{seed}" / "manifest.json"
            if manifest_path.exists() and not args.overwrite:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                expected_status = "smoke" if args.smoke else "completed"
                if manifest.get("status") == expected_status:
                    expected_request = requested_run_fingerprint(
                        config,
                        PROJECT_ROOT / "splits" / protocol / f"seed_{seed}.json",
                        seed,
                        feature_cache,
                        args.device,
                        overrides,
                        "smoke" if args.smoke else "formal",
                    )
                    if manifest.get("request_sha256") != expected_request:
                        raise RuntimeError(
                            f"Existing result for {protocol}/seed_{seed} has stale provenance; "
                            "rerun explicitly with --overwrite"
                        )
                    print(json.dumps({"protocol": protocol, "seed": seed, "status": "skipped_existing"}))
                    continue
            manifest = run_paper_experiment(
                config_path=config,
                split_path=PROJECT_ROOT / "splits" / protocol / f"seed_{seed}.json",
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
                        "protocol": protocol,
                        "seed": seed,
                        "status": manifest["status"],
                        "seconds": manifest["training_seconds"],
                    },
                    ensure_ascii=False,
                )
            )
        if not args.smoke and set(args.seeds) == set(PAPER_SEEDS):
            aggregate_protocol_results(results_root / protocol, expected_seeds=args.seeds)


if __name__ == "__main__":
    main()
