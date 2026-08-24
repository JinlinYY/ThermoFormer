"""Run only C1 overall_binary_ternary seed-0 partial physics fine-tuning."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.artifacts import (
    artifact_sha256,
    atomic_write_json,
    portable_artifact_path,
    resolve_artifact_path,
)
from src.config import load_experiment_config
from src.paper_runner import (
    requested_run_fingerprint,
    result_protocol_name,
    run_paper_experiment,
)
from src.physics_finetuning import write_physics_finetune_report
from src.representation import encoder_cache_filename


@dataclass(frozen=True)
class ExperimentVariant:
    folder: str
    fugacity_reference: bool = False
    exploratory: bool = False


EXPERIMENT_VARIANTS = {
    "fugacity_pure_anchor": ExperimentVariant(
        "c1_three_view_vanilla_fugacity_pure_anchor",
        fugacity_reference=True,
    ),
    "pure_anchor": ExperimentVariant("c1_three_view_vanilla_pure_anchor"),
    "pure_anchor_0p1": ExperimentVariant(
        "c1_three_view_vanilla_pure_anchor_0p1",
        exploratory=True,
    ),
    "fugacity": ExperimentVariant("c1_three_view_vanilla_fugacity"),
    "legacy": ExperimentVariant("c1_three_view_vanilla"),
}


def output_roots(
    project_root: Path,
    *,
    smoke: bool,
    experiment_folder: str = "c1_three_view_vanilla",
) -> tuple[Path, Path, Path]:
    root = project_root / "runs/c1_physics_finetune_smoke" if smoke else project_root
    experiment_path = Path("experiments/physics_finetuning") / experiment_folder
    return (
        root / "runs" / experiment_path,
        root / "checkpoints" / experiment_path,
        root / "results" / experiment_path,
    )


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    value.add_argument(
        "--objective",
        choices=tuple(EXPERIMENT_VARIANTS),
        default="fugacity",
        help="Stage-2 thermodynamic objective; fugacity is the current default.",
    )
    value.add_argument("--smoke", action="store_true")
    value.add_argument("--overwrite", action="store_true")
    return value


def recover_completed_seed_manifest(
    path: Path,
    *,
    expected_status: str,
    expected_protocol: str,
    expected_evaluation_partition: str,
    expected_request_sha256: str,
) -> dict[str, object] | None:
    """Validate a completed seed bundle before repairing its final report."""

    if not path.is_file():
        return None
    candidate = json.loads(path.read_text(encoding="utf-8"))
    if candidate.get("status") != expected_status:
        return None
    invariants = {
        "protocol": expected_protocol,
        "seed": 0,
        "evaluation_partition": expected_evaluation_partition,
        "request_sha256": expected_request_sha256,
    }
    for key, expected in invariants.items():
        if candidate.get(key) != expected:
            raise RuntimeError(
                f"Existing completed seed has stale {key}; use --overwrite to rerun"
            )
    artifacts = candidate.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise RuntimeError("Existing completed seed has no auditable artifacts")
    for name, record in artifacts.items():
        if not isinstance(record, dict):
            raise RuntimeError(f"Malformed artifact record: {name}")
        artifact_path = resolve_artifact_path(str(record.get("path", "")))
        if not artifact_path.is_file() or artifact_sha256(artifact_path) != record.get(
            "sha256"
        ):
            raise RuntimeError(f"Existing completed seed artifact failed SHA validation: {name}")
    return candidate


def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    variant = EXPERIMENT_VARIANTS[args.objective]
    experiment_folder = variant.folder
    config_path = (
        PROJECT_ROOT
        / "experiments/physics_finetuning"
        / experiment_folder
        / "config.json"
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
        PROJECT_ROOT,
        smoke=args.smoke,
        experiment_folder=experiment_folder,
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
    expected_evaluation_partition = "validation" if args.smoke else "test"
    analysis_status = (
        "diagnostic"
        if args.smoke
        else "test_exposed_exploratory"
        if variant.exploratory
        else "confirmatory"
    )
    recorded_git_commit = None
    if seed_manifest_path.is_file() and not args.overwrite:
        existing_payload = json.loads(seed_manifest_path.read_text(encoding="utf-8"))
        value = existing_payload.get("git_commit")
        if isinstance(value, str) and value:
            recorded_git_commit = value
    expected_request_sha256 = requested_run_fingerprint(
        config_path,
        split_path,
        0,
        feature_cache,
        args.device,
        overrides,
        "smoke" if args.smoke else "formal",
        expected_evaluation_partition,
        stage1_checkpoint,
        False,
        recorded_git_commit,
        analysis_status,
    )
    existing_manifest = (
        recover_completed_seed_manifest(
            seed_manifest_path,
            expected_status="smoke" if args.smoke else "completed",
            expected_protocol=protocol,
            expected_evaluation_partition=expected_evaluation_partition,
            expected_request_sha256=expected_request_sha256,
        )
        if not args.overwrite
        else None
    )
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
        evaluation_partition=expected_evaluation_partition,
        stage1_checkpoint=stage1_checkpoint,
        aggregate_expected=False,
        analysis_status=analysis_status,
    )
    comparison_path = protocol_dir / "seed_0/stage_comparison.json"
    report_path = (
        protocol_dir / "smoke_results.md"
        if args.smoke
        else PROJECT_ROOT
        / "experiments/physics_finetuning"
        / experiment_folder
        / "results.md"
    )
    reference_comparison_path = None
    if variant.fugacity_reference and not args.smoke:
        reference_comparison_path = (
            PROJECT_ROOT
            / "results/experiments/physics_finetuning/c1_three_view_vanilla_fugacity"
            / "c1_three_view_vanilla_fugacity_finetune.on.overall_binary_ternary"
            / "seed_0/stage_comparison.json"
        )
        if not reference_comparison_path.is_file():
            raise FileNotFoundError(
                "The frozen fugacity-only Stage-2 comparison is required"
            )
    write_physics_finetune_report(
        comparison_path,
        report_path,
        reference_comparison_path=reference_comparison_path,
        exploratory=variant.exploratory,
    )
    report_manifest = {
        "status": "smoke" if args.smoke else "completed",
        "protocol": protocol,
        "seed": 0,
        "selection_partition": "validation",
        "evaluation_partition": "validation" if args.smoke else "test",
        "selected_stage": manifest["selected_stage"],
        "analysis_status": analysis_status,
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
    if reference_comparison_path is not None:
        report_manifest["reference_stage_comparison"] = {
            "path": portable_artifact_path(reference_comparison_path),
            "sha256": artifact_sha256(reference_comparison_path),
        }
    atomic_write_json(protocol_dir / "report_manifest.json", report_manifest)
    print(json.dumps(report_manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
