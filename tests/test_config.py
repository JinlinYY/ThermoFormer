import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from src.config import DataConfig, EncoderConfig, load_experiment_config
from src.model import ThermoFormer, ThermoFormerConfig
from src.training import TrainingConfig


class ExperimentConfigTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]
    CONFIG_ROOT = ROOT / "experiments"
    BASE_CONFIG = CONFIG_ROOT / "baseline" / "thermoformer_base" / "config.json"

    def assert_only_named_config_changes(
        self,
        candidate_path: Path,
        section_changes: dict[str, dict[str, object]],
    ) -> None:
        base = load_experiment_config(self.BASE_CONFIG)
        candidate = load_experiment_config(candidate_path)
        expected = base.to_dict()
        expected["name"] = candidate.name
        expected["runtime"]["output_dir"] = candidate.runtime.output_dir
        expected["runtime"]["results_file"] = candidate.runtime.results_file
        for section, changes in section_changes.items():
            expected[section].update(changes)
        self.assertEqual(candidate.to_dict(), expected)

    def test_json_config_and_dotted_overrides_define_an_ablation(self) -> None:
        payload = {
            "model": {"hidden_dim": 64, "layers": 2, "heads": 4},
            "evaluation": {"mode": "kfold", "folds": 5},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "experiment.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            config = load_experiment_config(
                path,
                overrides=["model.use_film=false", "evaluation.folds=3"],
            )

        self.assertEqual(config.model.hidden_dim, 64)
        self.assertFalse(config.model.use_film)
        self.assertEqual(config.evaluation.folds, 3)
        self.assertEqual(config.evaluation.mode, "kfold")

    def test_repository_configs_construct_thermoformer(self) -> None:
        paths = sorted(self.CONFIG_ROOT.rglob("config.json"))

        self.assertGreater(len(paths), 0)

        for path in paths:
            with self.subTest(config=path):
                experiment = load_experiment_config(path)
                model = ThermoFormer(replace(experiment.model, feature_dim=8))
                self.assertEqual(model.config.feature_dim, 8)

    def test_ablation_configs_inherit_base_and_change_only_named_fields(self) -> None:
        expected_model_changes = {
            "no_film": {"use_film": False},
            "no_transformer": {"layers": 0, "use_transformer": False},
            "no_mixture_token": {"use_mixture_token": False},
        }
        for experiment_name, changes in expected_model_changes.items():
            with self.subTest(config=experiment_name):
                self.assert_only_named_config_changes(
                    self.CONFIG_ROOT
                    / "ablation"
                    / "component"
                    / experiment_name
                    / "config.json",
                    {"model": changes},
                )

    def test_thermodynamic_loss_ablations_change_only_the_named_weight(self) -> None:
        changes_by_experiment = {
            "no_continuity_loss": {"continuity_weight": 0.0},
            "no_boundary_loss": {"boundary_weight": 0.0},
            "no_solver_loss": {"solver_weight": 0.0},
        }
        for experiment_name, changes in changes_by_experiment.items():
            with self.subTest(experiment=experiment_name):
                self.assert_only_named_config_changes(
                    self.CONFIG_ROOT
                    / "ablation"
                    / "thermodynamic_loss"
                    / experiment_name
                    / "config.json",
                    {"training": changes},
                )

    def test_comparison_config_is_not_classified_as_an_ablation(self) -> None:
        self.assert_only_named_config_changes(
            self.CONFIG_ROOT / "comparison" / "ideal_activity" / "config.json",
            {"model": {"activity_mode": "ideal"}},
        )

    def test_concrete_experiments_are_nested_and_have_complete_records(self) -> None:
        experiment_root = self.CONFIG_ROOT

        self.assertEqual(list(experiment_root.glob("*/config.json")), [])
        config_paths = sorted(experiment_root.rglob("config.json"))
        self.assertGreater(len(config_paths), 0)
        for config_path in config_paths:
            with self.subTest(config=config_path):
                experiment_dir = config_path.parent
                relative_dir = experiment_dir.relative_to(experiment_root).as_posix()
                run_file = experiment_dir / "run.md"
                results_file = experiment_dir / "results.md"
                self.assertTrue(run_file.is_file())
                self.assertTrue(results_file.is_file())
                run_text = run_file.read_text(encoding="utf-8")
                self.assertIn(
                    f"experiments/{relative_dir}/config.json",
                    run_text,
                )
                config = load_experiment_config(config_path)
                self.assertEqual(
                    config.runtime.output_dir,
                    f"runs/experiments/{relative_dir}",
                )
                self.assertEqual(
                    config.runtime.results_file,
                    f"experiments/{relative_dir}/results.md",
                )

    def test_cyclic_config_inheritance_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.json").write_text('{"extends": "b.json"}', encoding="utf-8")
            (root / "b.json").write_text('{"extends": "a.json"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Cyclic experiment configuration"):
                load_experiment_config(root / "a.json")

    def test_unknown_config_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "experiment.json"
            path.write_text(json.dumps({"modell": {"use_film": False}}), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Unknown experiment configuration"):
                load_experiment_config(path)

            valid = Path(directory) / "valid.json"
            valid.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Unknown configuration section"):
                load_experiment_config(valid, overrides=["modell.use_film=false"])

    def test_conflicting_training_seed_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "experiment.json"
            path.write_text(
                json.dumps({"seed": 7, "training": {"seed": 8}}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "training.seed"):
                load_experiment_config(path)

    def test_invalid_training_hyperparameters_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TrainingConfig(batch_size=0)
        with self.assertRaises(ValueError):
            TrainingConfig(continuity_weight=-1.0)
        with self.assertRaises(ValueError):
            TrainingConfig(learning_rate=float("nan"))
        with self.assertRaises(ValueError):
            TrainingConfig(epochs_supervised=1.5)
        with self.assertRaises(ValueError):
            TrainingConfig(solver_iterations_eval=0)
        with self.assertRaises(ValueError):
            TrainingConfig(solver_batches_per_epoch=-1)
        with self.assertRaises(ValueError):
            ThermoFormerConfig(film_scale=float("inf"))
        with self.assertRaises(ValueError):
            ThermoFormerConfig(layers=1.5)
        with self.assertRaises(ValueError):
            DataConfig(max_pressure_kpa=float("nan"))
        with self.assertRaises(ValueError):
            EncoderConfig(representation="unknown")

    def test_ablation_switches_are_explicit_and_validated(self) -> None:
        config = ThermoFormerConfig(
            interaction_mode="pairwise",
            activity_mode="direct_gamma",
            decoder_mode="thermodynamic",
        )

        self.assertEqual(config.interaction_mode, "pairwise")
        self.assertEqual(config.activity_mode, "direct_gamma")
        with self.assertRaises(ValueError):
            ThermoFormerConfig(interaction_mode="implicit")
        with self.assertRaises(ValueError):
            ThermoFormerConfig(decoder_mode="black_box")


if __name__ == "__main__":
    unittest.main()
