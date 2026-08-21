"""Measure solver convergence/accuracy sensitivity for a saved smoke checkpoint."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_experiment_config
from src.data import load_vle_dataset, retain_pure_anchored_systems
from src.evaluation import predict_vle, prediction_metric_rows
from src.model import ThermoFormer, ThermoFormerConfig
from src.pure_properties import empty_pure_property_catalog
from src.splits import load_split_assignment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "experiments" / "baseline" / "thermoformer_base" / "config.json",
    )
    parser.add_argument(
        "--feature-cache",
        type=Path,
        default=PROJECT_ROOT / "cache" / "unimolv2_84m.npz",
    )
    parser.add_argument("--iterations", type=int, nargs="+", default=[8, 16, 24, 48])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    experiment = load_experiment_config(args.config)
    data_root = Path(experiment.data.root)
    if not data_root.is_absolute():
        data_root = PROJECT_ROOT / data_root
    loaded = load_vle_dataset(
        data_root,
        failed_weight=experiment.data.failed_weight,
        max_pressure_kpa=experiment.data.max_pressure_kpa,
    )
    samples = retain_pure_anchored_systems(
        loaded.samples,
        minimum_temperatures=experiment.data.minimum_pure_anchor_temperatures,
    )
    split = load_split_assignment(args.split, samples)
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    model = ThermoFormer(ThermoFormerConfig(**checkpoint["model_config"]))
    model.load_state_dict(checkpoint["model"])
    with np.load(args.feature_cache, allow_pickle=False) as cache:
        smiles = cache["smiles"].astype(str).tolist()
        features = np.asarray(cache["features"], dtype=np.float32)
    feature_map = {value: features[index] for index, value in enumerate(smiles)}
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rows = []
    for iterations in args.iterations:
        started = time.perf_counter()
        predictions = predict_vle(
            model,
            split.test,
            feature_map,
            batch_size=experiment.training.batch_size,
            device=device,
            solver_iterations=iterations,
            pure_property_catalog=empty_pure_property_catalog(),
        )
        elapsed = time.perf_counter() - started
        metrics = prediction_metric_rows(predictions)
        for row in metrics:
            rows.append({"iterations": iterations, "seconds": elapsed, **row})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
