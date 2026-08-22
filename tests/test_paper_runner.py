import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import openpyxl

from src.data import load_vle_samples
from src.paper_runner import result_protocol_name, run_paper_experiment
from src.splits import DatasetPartitions, save_split_assignment
from scripts.run_paper_experiment import output_roots, parser


class PaperRunnerTests(unittest.TestCase):
    def test_ablation_result_namespace_reuses_split_without_overwriting_reference(self) -> None:
        self.assertEqual(
            result_protocol_name("overall_binary_ternary", "overall_binary_ternary"),
            "overall_binary_ternary",
        )
        self.assertEqual(
            result_protocol_name("ablation_pairwise", "overall_binary_ternary"),
            "ablation_pairwise.on.overall_binary_ternary",
        )

    def test_single_run_smoke_defaults_are_isolated_from_formal_roots(self) -> None:
        args = parser().parse_args(["--split", "split.json", "--seed", "0", "--smoke"])
        run_root, checkpoint_root, results_root = output_roots(args)
        self.assertIn("single_smoke", str(run_root))
        self.assertIn("single_smoke", str(checkpoint_root))
        self.assertIn("single_smoke", str(results_root))
        self.assertNotEqual(results_root, Path("D:/VLE/VLE/results"))

    def test_end_to_end_run_exports_checkpoint_predictions_metrics_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_root = root / "dataset"
            data_root.mkdir()
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.append(
                [
                    "name1", "cas1", "smiles1", "name2", "cas2", "smiles2",
                    "check1", "check2", "P", "T", "x1", "y1", "doi",
                ]
            )
            systems = [("C", "O"), ("CC", "O"), ("CCC", "O")]
            for system_index, (first, second) in enumerate(systems):
                for point in range(3):
                    x = 0.2 + 0.2 * point
                    sheet.append(
                        [
                            first, "", first, second, "", second, 1, 1,
                            760.0 + 5.0 * system_index, 30.0 + point,
                            x, x, f"series-{system_index}",
                        ]
                    )
            workbook.save(data_root / "binary.xlsx")
            samples = load_vle_samples(data_root)
            split = DatasetPartitions(
                train=tuple(samples[:3]),
                validation=tuple(samples[3:6]),
                test=tuple(samples[6:]),
                protocol="runner_contract",
                seed=0,
            )
            split_path = root / "split.json"
            save_split_assignment(split_path, samples, split)
            config = {
                "name": "runner_contract",
                "seed": 0,
                "model": {
                    "hidden_dim": 8,
                    "layers": 1,
                    "heads": 2,
                    "activity_mode": "ideal",
                },
                "encoder": {"representation": "unimol_v2"},
                "data": {
                    "root": str(data_root),
                    "minimum_pure_anchor_temperatures": 0,
                },
                "training": {
                    "batch_size": 3,
                    "epochs_supervised": 1,
                    "epochs_physics": 0,
                    "solver_iterations_eval": 2,
                },
                "runtime": {"device": "cpu"},
            }
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            cache = root / "unimol.npz"
            unique = sorted({smiles for sample in samples for smiles in sample.smiles})
            np.savez_compressed(
                cache,
                smiles=np.asarray(unique),
                features=np.arange(len(unique) * 4, dtype=np.float32).reshape(len(unique), 4),
                model=np.asarray("unimolv2"),
                model_size=np.asarray("84m"),
            )

            manifest = run_paper_experiment(
                config_path=config_path,
                split_path=split_path,
                seed=0,
                run_root=root / "runs",
                checkpoint_root=root / "checkpoints",
                results_root=root / "results",
                feature_cache=cache,
                run_kind="smoke",
            )

            run_dir = root / "runs" / "runner_contract" / "seed_0"
            result_dir = root / "results" / "runner_contract" / "seed_0"
            checkpoint = root / "checkpoints" / "runner_contract" / "seed_0" / "best_model.pt"
            self.assertEqual(manifest["status"], "smoke")
            self.assertRegex(manifest["git_commit"], r"^[0-9a-f]{7,40}$")
            self.assertIsInstance(manifest["git_dirty"], bool)
            self.assertRegex(manifest["resolved_config_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(manifest["feature_cache_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(manifest["feature_subset_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(manifest["environment_sha256"], r"^[0-9a-f]{64}$")
            self.assertIn("numpy", manifest["runtime"])
            self.assertIn("rdkit", manifest["runtime"])
            self.assertIn("unimol_tools", manifest["runtime"])
            self.assertGreaterEqual(manifest["inference_seconds"], 0.0)
            self.assertGreaterEqual(manifest["inference_ms_per_attempt"], 0.0)
            self.assertTrue(checkpoint.is_file())
            self.assertTrue((run_dir / "history.json").is_file())
            self.assertTrue((run_dir / "training_curves.csv").is_file())
            self.assertTrue((result_dir / "predictions.csv").is_file())
            self.assertTrue((result_dir / "metrics.json").is_file())
            self.assertTrue((result_dir / "physical_consistency.json").is_file())
            self.assertTrue((result_dir / "resolved_config.json").is_file())
            prediction_lines = (result_dir / "predictions.csv").read_text(
                encoding="utf-8-sig"
            ).splitlines()
            self.assertGreater(len(prediction_lines), len(split.test))

            protocol_dir = root / "results" / "runner_contract"
            (protocol_dir / "aggregate_manifest.json").write_text(
                json.dumps({"status": "completed"}), encoding="utf-8"
            )
            (protocol_dir / "diagnostic_aggregate_manifest.json").write_text(
                json.dumps({"status": "diagnostic"}), encoding="utf-8"
            )
            (protocol_dir / "metrics_by_seed.csv").write_text(
                "old", encoding="utf-8"
            )
            (protocol_dir / "metrics_summary.csv").write_text(
                "old", encoding="utf-8"
            )

            with patch("src.paper_runner.fit_model", side_effect=RuntimeError("injected")):
                with self.assertRaisesRegex(RuntimeError, "injected"):
                    run_paper_experiment(
                        config_path=config_path,
                        split_path=split_path,
                        seed=0,
                        run_root=root / "runs",
                        checkpoint_root=root / "checkpoints",
                        results_root=root / "results",
                        feature_cache=cache,
                        allow_overwrite=True,
                        run_kind="smoke",
                    )
            interrupted = json.loads(
                (result_dir / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertNotEqual(interrupted["status"], "completed")
            self.assertNotEqual(interrupted["status"], "smoke")
            aggregate = json.loads(
                (protocol_dir / "aggregate_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(aggregate["status"], "invalidated")
            diagnostic_aggregate = json.loads(
                (protocol_dir / "diagnostic_aggregate_manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(diagnostic_aggregate["status"], "invalidated")


if __name__ == "__main__":
    unittest.main()
