"""Run only C1 overall_binary_ternary seed-0 partial physics fine-tuning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.artifacts import artifact_sha256, atomic_write_json, portable_artifact_path
from src.config import load_experiment_config
from src.paper_runner import result_protocol_name, run_paper_experiment
from src.physics_finetuning import write_physics_finetune_report
from src.representation import encoder_cache_filename


def output_roots(project_root: Path, *, smoke: bool) -> tuple[Path, Path, Path]:
    root = project_root / "runs/c1_physics_finetune_smoke" if smoke else project_root
    experiment_path = Path("experiments/physics_finetuning/c1_three_view_vanilla")
    return (
        root / "runs" / experiment_path,
        root / "checkpoints" / experiment_path,
        root / "results" / experiment_path,
    )


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    value.add_argument("--smoke", action="store_true")
    value.add_argument("--overwrite", action="store_true")
    return value


def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    config_path = (
        PROJECT_ROOT
        / "experiments/physics_finetuning/c1_three_view_vanilla/config.json"
    )
    split_path = PROJECT_ROOT / "splits/overall_binary_ternary/seed_0.json"
    stage1_checkpoint = (
        PROJECT_ROOT
        / "checkpoints/multiview/chemical_attention/formal"
        / "c1_three_view_vanilla.on.overall_binary_ternary/seed_0/best_model.pt"
    )
    experiment = load_experiment_config(config_path)
    feature_cache = PROJECT_ROOT / "cache" / encoder_cache_filename(experiment.encoder)
    run_root, checkpoint_root, results_root = output_roots(
        PROJECT_ROOT, smoke=args.smoke
    )
    overrides = (
        (
            "training.epochs_physics=1",
            "training.minimum_physics_epochs=1",
            "training.solver_iterations_train=2",
            "training.solver_iterations_eval=4",
        )
        if args.smoke
        else ()
    )
    protocol = result_protocol_name(experiment.name, "overall_binary_ternary")
    protocol_dir = results_root / protocol
    seed_manifest_path = protocol_dir / "seed_0/manifest.json"
    # The report manifest is the experiment-level completion pointer.  If a
    # process stopped after the seed artifacts committed, rerunning repairs the
    # report bundle without repeating training or requiring --overwrite.
    existing_manifest = None
    if seed_manifest_path.is_file() and not args.overwrite:
        candidate = json.loads(seed_manifest_path.read_text(encoding="utf-8"))
        expected_status = "smoke" if args.smoke else "completed"
        if candidate.get("status") == expected_status:
            existing_manifest = candidate
    manifest = existing_manifest or run_paper_experiment(
        config_path=config_path,
        split_path=split_path,
        seed=0,
        run_root=run_root,
        checkpoint_root=checkpoint_root,
        results_root=results_root,
        feature_cache=feature_cache,
        device_name=args.device,
        overrides=overrides,
        allow_overwrite=args.overwrite,
        run_kind="smoke" if args.smoke else "formal",
        evaluation_partition="validation" if args.smoke else "test",
        stage1_checkpoint=stage1_checkpoint,
        aggregate_expected=False,
    )
    comparison_path = protocol_dir / "seed_0/stage_comparison.json"
    report_path = (
        protocol_dir / "smoke_results.md"
        if args.smoke
        else PROJECT_ROOT
        / "experiments/physics_finetuning/c1_three_view_vanilla/results.md"
    )
    write_physics_finetune_report(comparison_path, report_path)
    report_manifest = {
        "status": "smoke" if args.smoke else "completed",
        "protocol": protocol,
        "seed": 0,
        "selection_partition": "validation",
        "evaluation_partition": "validation" if args.smoke else "test",
        "selected_stage": manifest["selected_stage"],
        "run_manifest": {
            "path": portable_artifact_path(seed_manifest_path),
            "sha256": artifact_sha256(seed_manifest_path),
        },
        "stage_comparison": {
            "path": portable_artifact_path(comparison_path),
            "sha256": artifact_sha256(comparison_path),
        },
        "report": {
            "path": portable_artifact_path(report_path),
            "sha256": artifact_sha256(report_path),
        },
    }
    atomic_write_json(protocol_dir / "report_manifest.json", report_manifest)
    print(json.dumps(report_manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
