"""Post-process the frozen Uni-Mol v2-only comparator with physical metrics."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import torch
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_experiment_config
from src.ablation_protocols import ABLATION_SEEDS
from src.data import load_vle_dataset, retain_pure_anchored_systems
from src.evaluation import predict_vle
from src.evaluation.thermodynamic_consistency import evaluate_thermodynamic_consistency
from src.model import ThermoFormer, ThermoFormerConfig
from src.pure_properties import empty_pure_property_catalog, load_pure_property_catalog
from src.representation import UniMolV2Encoder
from src.splits import dataset_digest, load_split_assignment


REFERENCE_CONFIGS = {
    "overall_binary_ternary": "experiments/predictive_performance/overall_binary_ternary/config.json",
    "unseen_component": "experiments/interpolation_extrapolation/chemical_space/unseen_component/config.json",
    "binary_to_ternary_zero_shot": "experiments/comparison/binary_to_ternary_generalization/zero_shot/config.json",
}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reference_training_commit(protocol: str) -> str:
    snapshot = PROJECT_ROOT / "configs" / "ablation" / "unimol_v2_reference.yaml"
    payload = yaml.safe_load(snapshot.read_text(encoding="utf-8"))
    commits = payload.get("reference_training_commits", {})
    if protocol not in commits:
        raise ValueError(f"Missing frozen training commit for {protocol} in {snapshot}")
    return str(commits[protocol])


def _validate_reference_provenance(
    manifest: dict,
    checkpoint: dict,
    checkpoint_path: Path,
    split_path: Path,
    samples,
    protocol: str,
    seed: int,
) -> None:
    expected_commit = _reference_training_commit(protocol)
    invariants = {
        "status": (manifest.get("status"), "completed"),
        "protocol": (manifest.get("protocol"), protocol),
        "seed": (manifest.get("seed"), seed),
        "git_commit": (manifest.get("git_commit"), expected_commit),
        "checkpoint_git_commit": (checkpoint.get("git_commit"), expected_commit),
        "dataset_sha256": (manifest.get("dataset_sha256"), dataset_digest(samples)),
        "checkpoint_dataset_sha256": (
            checkpoint.get("dataset_sha256"), manifest.get("dataset_sha256")
        ),
        "split_sha256": (manifest.get("split_sha256"), _digest(split_path)),
        "checkpoint_split_sha256": (
            checkpoint.get("split_sha256"), manifest.get("split_sha256")
        ),
        "checkpoint_request_sha256": (
            checkpoint.get("request_sha256"), manifest.get("request_sha256")
        ),
        "checkpoint_artifact_sha256": (
            _digest(checkpoint_path),
            manifest.get("artifacts", {}).get("checkpoint", {}).get("sha256"),
        ),
    }
    mismatches = [name for name, (actual, expected) in invariants.items() if actual != expected]
    if mismatches:
        raise RuntimeError(f"Invalid immutable Uni-Mol v2 provenance: {', '.join(mismatches)}")


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", prefix=f".{path.name}.",
            suffix=".tmp", dir=path.parent, delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", action="append", choices=sorted(REFERENCE_CONFIGS))
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--artifact-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if len(args.seeds) != len(set(args.seeds)) or not set(args.seeds).issubset(ABLATION_SEEDS):
        raise ValueError("Reference evaluation seeds must be a unique subset of 0--4")
    artifact_root = args.artifact_root.resolve()
    device = torch.device(args.device)
    cache = artifact_root / "cache" / "unimolv2_84m.npz"
    evaluation_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    worktree_status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if worktree_status.strip():
        raise RuntimeError("Reference consistency evaluation requires a clean Git worktree")
    for protocol in args.protocol or ["overall_binary_ternary"]:
        experiment = load_experiment_config(PROJECT_ROOT / REFERENCE_CONFIGS[protocol])
        catalog_path = (
            PROJECT_ROOT / experiment.data.pure_property_catalog
            if experiment.data.pure_property_catalog
            else None
        )
        catalog = (
            load_pure_property_catalog(catalog_path)
            if catalog_path is not None
            else empty_pure_property_catalog()
        )
        loaded = load_vle_dataset(
            PROJECT_ROOT / experiment.data.root,
            source_filter=experiment.data.source_filter,
            failed_weight=experiment.data.failed_weight,
            max_pressure_kpa=experiment.data.max_pressure_kpa,
        )
        samples = retain_pure_anchored_systems(
            loaded.samples,
            minimum_temperatures=experiment.data.minimum_pure_anchor_temperatures,
        )
        unique = sorted({smiles for sample in samples for smiles in sample.smiles})
        features = UniMolV2Encoder(
            cache,
            batch_size=experiment.encoder.batch_size,
            model_size=experiment.encoder.model_size,
            use_cuda=device.type == "cuda",
        ).encode(unique)
        for seed in args.seeds:
            split_path = PROJECT_ROOT / "splits" / protocol / f"seed_{seed}.json"
            split = load_split_assignment(
                split_path,
                samples,
            )
            checkpoint_path = artifact_root / "checkpoints" / protocol / f"seed_{seed}" / "best_model.pt"
            checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
            manifest_path = artifact_root / "results" / protocol / f"seed_{seed}" / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            _validate_reference_provenance(
                manifest, checkpoint, checkpoint_path, split_path, samples, protocol, seed
            )
            output = artifact_root / "results" / protocol / f"seed_{seed}" / "physical_consistency.json"
            if output.exists() and not args.overwrite:
                raise FileExistsError(f"Refusing to replace {output}; pass --overwrite")
            model = ThermoFormer(ThermoFormerConfig(**checkpoint["model_config"]))
            model.load_state_dict(checkpoint["model"])
            model.to(device).eval()
            started = time.perf_counter()
            predictions = predict_vle(
                model,
                split.test,
                features,
                batch_size=experiment.training.batch_size,
                device=device,
                solver_iterations=experiment.training.solver_iterations_eval,
                pure_property_catalog=catalog,
            )
            inference_seconds = time.perf_counter() - started
            metrics = evaluate_thermodynamic_consistency(
                model,
                split.test,
                features,
                device,
                prediction_records=predictions,
                solver_iterations=experiment.training.solver_iterations_eval,
                pure_reference_samples=split.train,
                pure_property_catalog=catalog,
            )
            metrics.update(
                {
                    "protocol": protocol,
                    "seed": seed,
                    "training_git_commit": checkpoint["git_commit"],
                    "evaluation_git_commit": evaluation_commit,
                    "checkpoint_sha256": _digest(checkpoint_path),
                    "inference_seconds": inference_seconds,
                    "inference_ms_per_attempt": 1000.0 * inference_seconds / len(predictions),
                }
            )
            _atomic_write_json(output, metrics)
            print(json.dumps({"protocol": protocol, "seed": seed, "output": str(output)}))


if __name__ == "__main__":
    main()
