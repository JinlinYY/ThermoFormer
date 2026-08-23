"""Run locked chemical-attention pilot or five-seed experiments."""

from __future__ import annotations

import argparse
import gc
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.chemical_attention_protocols import (
    CHEMICAL_ATTENTION_FORMAL_PROTOCOLS,
    CHEMICAL_ATTENTION_PROTOCOLS,
    CHEMICAL_ATTENTION_SEEDS,
    CHEMICAL_ATTENTION_VARIANTS,
)
from src.config import load_experiment_config
from src.chemical_attention_outputs import validate_pilot_report_bundle, write_pilot_outputs
from src.paper_runner import result_protocol_name, run_paper_experiment
from src.representation import encoder_cache_filename
from src.results import aggregate_protocol_results


def _release_accelerator() -> None:
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
    value.add_argument("--stage", choices=("pilot", "formal"), required=True)
    value.add_argument("--variant", action="append", choices=sorted(CHEMICAL_ATTENTION_VARIANTS))
    value.add_argument("--protocol", action="append", choices=CHEMICAL_ATTENTION_PROTOCOLS)
    value.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    value.add_argument("--artifact-root", type=Path, default=PROJECT_ROOT)
    value.add_argument("--overwrite", action="store_true")
    value.add_argument(
        "--confirm-pilot-reviewed",
        action="store_true",
        help="Required for the five-seed stage after the owner reviews the seed-0 report",
    )
    return value


def _require_reviewed_pilot(artifact_root: Path) -> None:
    report = artifact_root / "reports" / "chemical_attention_pilot_report.md"
    if not report.is_file():
        raise RuntimeError("Formal stage requires the generated seed-0 pilot report")
    validate_pilot_report_bundle(artifact_root)


def complete_pilot_matrix(
    stage: str, variants: tuple[str, ...], protocols: tuple[str, ...]
) -> bool:
    return (
        stage == "pilot"
        and variants == tuple(CHEMICAL_ATTENTION_VARIANTS)
        and protocols == CHEMICAL_ATTENTION_PROTOCOLS
    )


def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    variants = tuple(args.variant or CHEMICAL_ATTENTION_VARIANTS)
    default_protocols = (
        CHEMICAL_ATTENTION_FORMAL_PROTOCOLS
        if args.stage == "formal"
        else CHEMICAL_ATTENTION_PROTOCOLS
    )
    protocols = tuple(args.protocol or default_protocols)
    seeds = (0,) if args.stage == "pilot" else CHEMICAL_ATTENTION_SEEDS
    artifact_root = args.artifact_root.resolve()
    if args.stage == "formal":
        if not args.confirm_pilot_reviewed:
            raise RuntimeError(
                "Formal stage is locked until --confirm-pilot-reviewed is explicitly supplied"
            )
        _require_reviewed_pilot(artifact_root)
    run_root = artifact_root / "runs" / "multiview" / "chemical_attention" / args.stage
    checkpoint_root = (
        artifact_root / "checkpoints" / "multiview" / "chemical_attention" / args.stage
    )
    results_root = (
        artifact_root
        / "results"
        / "multiview"
        / "chemical_attention"
        / args.stage
        / "runs"
    )

    for variant_id in variants:
        variant = CHEMICAL_ATTENTION_VARIANTS[variant_id]
        config_path = PROJECT_ROOT / variant.config
        experiment = load_experiment_config(config_path)
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
                        allow_overwrite=args.overwrite,
                        run_kind="pilot" if args.stage == "pilot" else "formal",
                    )
                finally:
                    _release_accelerator()
                print(json.dumps({
                    "variant": variant_id,
                    "protocol": split_protocol,
                    "seed": seed,
                    "status": manifest["status"],
                    "training_seconds": manifest["training_seconds"],
                    "trainable_parameters": manifest["trainable_parameters"],
                }))
            aggregate_protocol_results(
                results_root / protocol,
                expected_seeds=seeds,
                aggregate_kind="diagnostic" if args.stage == "pilot" else "formal",
            )
    if complete_pilot_matrix(args.stage, variants, protocols):
        write_pilot_outputs(artifact_root)
    elif args.stage == "pilot":
        print(json.dumps({"report": "deferred_until_complete_pilot_matrix"}))


if __name__ == "__main__":
    main()
