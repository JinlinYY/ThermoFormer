import json
import unittest
from pathlib import Path

from src.artifacts import artifact_sha256, resolve_artifact_path
from src.c2_optimization import (
    C2_CANDIDATES,
    validate_c2_selection,
    validation_selection_scores,
)
from src.config import load_experiment_config
from scripts.run_c2_selected_formal import main as run_selected_formal


class C2OptimizationTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_candidate_matrix_is_supervised_only_and_progressively_adds_controls(self) -> None:
        configs = {
            name: load_experiment_config(self.ROOT / path)
            for name, path in C2_CANDIDATES.items()
        }
        self.assertEqual(tuple(configs), (
            "o0_original", "o1_shared_gate", "o2_headwise",
            "o3_headwise_curriculum", "o4_headwise_curriculum_modality",
        ))
        self.assertTrue(configs["o1_shared_gate"].model.chemical_bias_shared_gate)
        self.assertTrue(configs["o2_headwise"].model.chemical_bias_headwise)
        self.assertEqual(configs["o2_headwise"].model.chemical_bias_hidden_dim, 48)
        self.assertEqual(configs["o3_headwise_curriculum"].model.chemical_bias_warmup_end, 20)
        self.assertEqual(configs["o3_headwise_curriculum"].model.chemical_bias_hidden_dim, 96)
        self.assertTrue(
            configs["o4_headwise_curriculum_modality"].model.chemical_bias_modality_gates
        )
        for config in configs.values():
            self.assertEqual(config.training.epochs_physics, 0)

    def test_formal_stage_requires_explicit_selection_review(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "confirm-selection-reviewed"):
            run_selected_formal([])

    def test_selection_and_formal_reports_use_distinct_artifacts(self) -> None:
        selection_path = (
            self.ROOT
            / "results/multiview/chemical_attention/selection/selection_manifest.json"
        )
        selected = validate_c2_selection(self.ROOT, selection_path)
        selection = json.loads(selection_path.read_text(encoding="utf-8"))
        selection_report = resolve_artifact_path(selection["report"]["path"])
        formal_dir = (
            self.ROOT
            / "results/multiview/chemical_attention/formal_optimized/runs"
            / f"c2opt_{selected}.on.overall_binary_ternary"
        )
        formal = json.loads(
            (formal_dir / "formal_report_manifest.json").read_text(encoding="utf-8")
        )
        formal_report = resolve_artifact_path(formal["reports"]["top"]["path"])
        self.assertNotEqual(selection_report, formal_report)
        self.assertEqual(formal["selection_manifest_sha256"], artifact_sha256(selection_path))
        self.assertEqual(len(formal["comparison_inputs"]), 3)

    def test_locked_score_normalizes_six_errors_against_original_per_seed(self) -> None:
        keys = (
            "pressure_mae_kpa", "pressure_rmse_kpa", "temperature_mae_k",
            "temperature_rmse_k", "y_mae", "y_rmse",
        )
        original = [{"seed": seed, **{key: 2.0 for key in keys}} for seed in (0, 1, 2)]
        improved = [{"seed": seed, **{key: 1.0 for key in keys}} for seed in (0, 1, 2)]
        scores = validation_selection_scores({"o0_original": original, "better": improved})
        self.assertAlmostEqual(scores["o0_original"], 1.0)
        self.assertAlmostEqual(scores["better"], 0.5)


if __name__ == "__main__":
    unittest.main()
