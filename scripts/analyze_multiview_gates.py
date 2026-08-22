"""Export learned V6 gate statistics from completed multi-view checkpoints."""

from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_experiment_config
from src.data import load_vle_dataset, retain_pure_anchored_systems
from src.model import ThermoFormer, ThermoFormerConfig
from src.multiview_analysis import collect_gate_records, gate_statistics
from src.multiview_protocols import FORMAL_PROTOCOLS, MULTIVIEW_SEEDS, MULTIVIEW_VARIANTS
from src.paper_runner import result_protocol_name
from src.representation import (
    build_molecular_encoder,
    encoder_cache_filename,
    prepare_partition_features,
)
from src.splits import load_split_assignment


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_checkpoint_provenance(
    checkpoint_path: Path,
    checkpoint: dict[str, object],
    manifest_path: Path,
    protocol: str,
    result_protocol: str,
    seed: int,
) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checkpoint_artifact = manifest.get("artifacts", {}).get("checkpoint", {})
    expected = {
        "status": "completed",
        "protocol": result_protocol,
        "seed": seed,
    }
    observed = {name: manifest.get(name) for name in expected}
    if observed != expected:
        raise RuntimeError(f"Invalid formal manifest for {protocol}/seed_{seed}: {observed}")
    if Path(checkpoint_artifact.get("path", "")).resolve() != checkpoint_path.resolve():
        raise RuntimeError(f"Checkpoint path mismatch for {protocol}/seed_{seed}")
    if checkpoint_artifact.get("sha256") != _sha256(checkpoint_path):
        raise RuntimeError(f"Checkpoint SHA mismatch for {protocol}/seed_{seed}")
    checkpoint_identity = {
        "protocol": checkpoint.get("protocol"),
        "split_protocol": checkpoint.get("split_protocol"),
        "seed": checkpoint.get("seed"),
        "git_commit": checkpoint.get("git_commit"),
    }
    expected_identity = {
        "protocol": result_protocol,
        "split_protocol": protocol,
        "seed": seed,
        "git_commit": manifest.get("git_commit"),
    }
    if checkpoint_identity != expected_identity:
        raise RuntimeError(
            f"Checkpoint identity mismatch for {protocol}/seed_{seed}: {checkpoint_identity}"
        )


def _write_rows_atomically(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8-sig", newline="", prefix=f".{path.name}.",
            suffix=".tmp", dir=path.parent, delete=False,
        ) as handle:
            temporary = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", action="append", default=[])
    parser.add_argument("--seeds", type=int, nargs="+", default=list(MULTIVIEW_SEEDS))
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--artifact-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "results" / "multiview" / "analysis" / "multiview_gate_statistics.csv",
    )
    args = parser.parse_args()
    protocols = tuple(args.protocol or FORMAL_PROTOCOLS)
    config_path = PROJECT_ROOT / MULTIVIEW_VARIANTS["v6_full_interaction"].config
    experiment = load_experiment_config(config_path)
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
    unique_smiles = sorted({smile for sample in samples for smile in sample.smiles})
    device = torch.device(args.device)
    records = []
    for protocol in protocols:
        for seed in args.seeds:
            split = load_split_assignment(
                PROJECT_ROOT / "splits" / protocol / f"seed_{seed}.json", samples
            )
            encoder = build_molecular_encoder(
                experiment.encoder,
                args.artifact_root / "cache" / encoder_cache_filename(experiment.encoder),
                use_cuda=device.type == "cuda",
            )
            prepared = prepare_partition_features(
                encoder,
                unique_smiles,
                sorted({smile for sample in split.train for smile in sample.smiles}),
            )
            result_protocol = result_protocol_name(experiment.name, protocol)
            checkpoint_path = (
                args.artifact_root / "checkpoints" / "multiview" / "formal"
                / result_protocol / f"seed_{seed}" / "best_model.pt"
            )
            checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
            manifest_path = (
                args.artifact_root / "results" / "multiview" / "formal" / "runs"
                / result_protocol / f"seed_{seed}" / "manifest.json"
            )
            _validate_checkpoint_provenance(
                checkpoint_path,
                checkpoint,
                manifest_path,
                protocol,
                result_protocol,
                seed,
            )
            if checkpoint.get("molecular_feature_preprocessing") != prepared.metadata:
                raise RuntimeError(f"Feature preprocessing mismatch for {protocol}/seed_{seed}")
            model = ThermoFormer(ThermoFormerConfig(**checkpoint["model_config"]))
            model.load_state_dict(checkpoint["model"])
            block_order = prepared.metadata["block_order"]
            offset = 0
            group_slice = slice(0, 0)
            for block in block_order:
                dimension = prepared.view_dimensions[block]
                if block == "functional_groups":
                    group_slice = slice(offset, offset + dimension)
                offset += dimension
            records.extend(
                collect_gate_records(
                    model,
                    split.test,
                    prepared.values,
                    prepared.metadata["functional_group_names"],
                    group_slice,
                    split.train,
                    experiment.training.batch_size,
                    device,
                    protocol,
                    seed,
                )
            )
            del model, checkpoint, prepared, encoder
            gc.collect()
            if device.type == "cuda":
                torch.cuda.synchronize()
                torch.cuda.empty_cache()
    rows = gate_statistics(records)
    _write_rows_atomically(args.output, rows)
    print(json.dumps({"output": str(args.output), "rows": len(rows)}))


if __name__ == "__main__":
    main()
