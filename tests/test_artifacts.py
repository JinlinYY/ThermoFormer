import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from src.artifacts import portable_artifact_path, resolve_artifact_path
from src.results import REQUIRED_ARTIFACTS, _validate_manifest_artifacts


class ArtifactPathTests(unittest.TestCase):
    def test_project_artifacts_round_trip_after_repository_relocation(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_root = Path(first)
            second_root = Path(second)
            first_artifact = first_root / "results" / "run" / "metrics.json"
            first_artifact.parent.mkdir(parents=True)
            first_artifact.write_text(json.dumps({"mae": 1.0}), encoding="utf-8")
            recorded = portable_artifact_path(first_artifact, first_root)

            relocated = second_root / recorded
            relocated.parent.mkdir(parents=True)
            relocated.write_bytes(first_artifact.read_bytes())

            self.assertEqual(recorded, "results/run/metrics.json")
            self.assertEqual(resolve_artifact_path(recorded, second_root), relocated.resolve())

    def test_external_artifact_remains_absolute(self) -> None:
        with tempfile.TemporaryDirectory() as project, tempfile.TemporaryDirectory() as external:
            path = Path(external) / "artifact.json"
            path.write_text("{}", encoding="utf-8")
            recorded = portable_artifact_path(path, Path(project))
            self.assertTrue(Path(recorded).is_absolute())

    def test_aggregation_validator_accepts_repository_relative_artifacts(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=root) as temporary:
            directory = Path(temporary)
            artifacts = {}
            for name in REQUIRED_ARTIFACTS:
                path = directory / f"{name}.json"
                path.write_text(json.dumps({"artifact": name}), encoding="utf-8")
                artifacts[name] = {
                    "path": portable_artifact_path(path, root),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            manifest_path = directory / "manifest.json"
            _validate_manifest_artifacts({"artifacts": artifacts}, manifest_path)
