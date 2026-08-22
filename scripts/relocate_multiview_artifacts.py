"""Migrate completed multi-view manifests to the portable artifact-path schema."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.artifacts import artifact_sha256, portable_artifact_path, resolve_artifact_path


def _sha256(path: Path) -> str:
    return artifact_sha256(path)


def _atomic_json(path: Path, payload: Any) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _portable(value: str, root: Path) -> str:
    path = Path(value)
    if path.is_absolute():
        return portable_artifact_path(path, root)
    return Path(value).as_posix()


def relocate_multiview_formal_artifacts(root: Path) -> int:
    """Rewrite formal JSON provenance without changing trained numerical artifacts."""

    root = root.resolve()
    results_root = root / "results" / "multiview" / "formal" / "runs"
    migrated = 0
    for protocol_dir in sorted(path for path in results_root.iterdir() if path.is_dir()):
        for result_seed_dir in sorted(protocol_dir.glob("seed_*")):
            if not result_seed_dir.is_dir():
                continue
            seed_name = result_seed_dir.name
            run_seed_dir = root / "runs" / "multiview" / "formal" / protocol_dir.name / seed_name
            for config_path in (
                result_seed_dir / "resolved_config.json",
                run_seed_dir / "resolved_config.json",
            ):
                payload = json.loads(config_path.read_text(encoding="utf-8"))
                paper = payload.get("paper_protocol", {})
                if isinstance(paper.get("split_file"), str):
                    paper["split_file"] = _portable(paper["split_file"], root)
                _atomic_json(config_path, payload)

            manifest_path = result_seed_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("status") != "completed":
                raise RuntimeError(f"Cannot migrate incomplete manifest: {manifest_path}")
            artifacts = manifest.get("artifacts", {})
            for entry in artifacts.values():
                if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                    raise ValueError(f"Malformed artifact entry: {manifest_path}")
                actual = resolve_artifact_path(entry["path"], root)
                if not actual.is_file():
                    raise FileNotFoundError(actual)
                entry["path"] = portable_artifact_path(actual, root)
                entry["sha256"] = _sha256(actual)
            for field in ("split_file", "checkpoint"):
                if isinstance(manifest.get(field), str):
                    manifest[field] = _portable(manifest[field], root)
            manifest["artifact_path_schema"] = "project-relative-v1"
            _atomic_json(manifest_path, manifest)
            _atomic_json(run_seed_dir / "manifest.json", manifest)
            migrated += 1

        aggregate_path = protocol_dir / "aggregate_manifest.json"
        aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))
        for entry in aggregate.get("outputs", {}).values():
            actual = resolve_artifact_path(str(entry["path"]), root)
            entry["path"] = portable_artifact_path(actual, root)
            entry["sha256"] = _sha256(actual)
        aggregate["input_manifest_sha256"] = {
            seed_dir.name.removeprefix("seed_"): _sha256(seed_dir / "manifest.json")
            for seed_dir in sorted(protocol_dir.glob("seed_*"))
        }
        aggregate["artifact_path_schema"] = "project-relative-v1"
        _atomic_json(aggregate_path, aggregate)
    return migrated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()
    count = relocate_multiview_formal_artifacts(args.project_root)
    print(json.dumps({"migrated_seed_manifests": count}))


if __name__ == "__main__":
    main()
