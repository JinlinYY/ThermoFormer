"""Post-process immutable Full ThermoFormer checkpoints with new physical metrics."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_experiment_config
from src.data import load_vle_dataset, retain_pure_anchored_systems
from src.evaluation import predict_vle
from src.evaluation.thermodynamic_consistency import evaluate_thermodynamic_consistency
from src.model import ThermoFormer, ThermoFormerConfig
from src.representation import UniMolV2Encoder
from src.splits import load_split_assignment


REFERENCE_CONFIGS = {
    "overall_binary_ternary": "experiments/predictive_performance/overall_binary_ternary/config.json",
    "unseen_component": "experiments/interpolation_extrapolation/chemical_space/unseen_component/config.json",
    "binary_to_ternary_zero_shot": "experiments/comparison/binary_to_ternary_generalization/zero_shot/config.json",
}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", action="append", choices=sorted(REFERENCE_CONFIGS))
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--artifact-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
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
    for protocol in args.protocol or ["overall_binary_ternary"]:
        experiment = load_experiment_config(PROJECT_ROOT / REFERENCE_CONFIGS[protocol])
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
            split = load_split_assignment(
                PROJECT_ROOT / "splits" / protocol / f"seed_{seed}.json",
                samples,
            )
            checkpoint_path = artifact_root / "checkpoints" / protocol / f"seed_{seed}" / "best_model.pt"
            checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
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
            )
            inference_seconds = time.perf_counter() - started
            metrics = evaluate_thermodynamic_consistency(
                model,
                split.test,
                features,
                device,
                prediction_records=predictions,
                solver_iterations=experiment.training.solver_iterations_eval,
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
            output = artifact_root / "results" / protocol / f"seed_{seed}" / "physical_consistency.json"
            output.write_text(
                json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(json.dumps({"protocol": protocol, "seed": seed, "output": str(output)}))


if __name__ == "__main__":
    main()
