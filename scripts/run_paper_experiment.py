"""CLI for one fixed ThermoFormer paper protocol/seed."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.paper_runner import run_paper_experiment


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--split", type=Path, required=True)
    value.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "experiments" / "baseline" / "thermoformer_base" / "config.json",
    )
    value.add_argument("--seed", type=int, required=True)
    value.add_argument("--set", dest="overrides", action="append", default=[])
    value.add_argument("--device", choices=("auto", "cpu", "cuda"), default=None)
    value.add_argument("--run-root", type=Path, default=None)
    value.add_argument("--checkpoint-root", type=Path, default=None)
    value.add_argument("--results-root", type=Path, default=None)
    value.add_argument(
        "--feature-cache",
        type=Path,
        default=PROJECT_ROOT / "cache" / "unimolv2_84m.npz",
    )
    value.add_argument("--overwrite", action="store_true")
    value.add_argument(
        "--smoke",
        action="store_true",
        help="Mark artifacts as non-aggregatable smoke diagnostics",
    )
    return value


def output_roots(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    """Resolve defaults so every smoke artifact is isolated from formal roots."""
    if args.smoke:
        smoke_root = PROJECT_ROOT / "runs" / "single_smoke"
        return (
            args.run_root or smoke_root / "paper",
            args.checkpoint_root or smoke_root / "checkpoints",
            args.results_root or smoke_root / "results",
        )
    return (
        args.run_root or PROJECT_ROOT / "runs" / "paper",
        args.checkpoint_root or PROJECT_ROOT / "checkpoints",
        args.results_root or PROJECT_ROOT / "results",
    )


def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    run_root, checkpoint_root, results_root = output_roots(args)
    manifest = run_paper_experiment(
        config_path=args.config,
        split_path=args.split,
        seed=args.seed,
        run_root=run_root,
        checkpoint_root=checkpoint_root,
        results_root=results_root,
        feature_cache=args.feature_cache,
        device_name=args.device,
        overrides=args.overrides,
        allow_overwrite=args.overwrite,
        run_kind="smoke" if args.smoke else "formal",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
