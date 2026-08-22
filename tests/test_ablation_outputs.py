import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.ablation_outputs import (
    _atomic_write_text,
    _metric_rows,
    _select_summary,
    architecture_and_physics_tables,
    manybody_system_effects,
    physical_consistency_table,
    write_report,
)
from src.ablation_protocols import ABLATION_SEEDS, ABLATION_VARIANTS
from scripts.run_ablation_suite import validate_seeds
from scripts.evaluate_reference_consistency import _reference_training_commit


class AblationOutputTests(unittest.TestCase):
    def test_predictive_ablation_rows_include_mae_rmse_and_r2(self) -> None:
        variant = ABLATION_VARIANTS["a0_full"]
        rows = _metric_rows(Path(__file__).resolve().parents[1], "a0_full", variant)

        self.assertGreater(len(rows), 0)
        for row in rows:
            self.assertIn("system_macro_mae_mean", row)
            self.assertIn("system_macro_rmse_mean", row)
            self.assertIn("pointwise_r2_mean", row)
            self.assertGreaterEqual(row["system_macro_rmse_mean"], row["system_macro_mae_mean"])

    def test_atomic_report_write_preserves_previous_file_on_replace_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "report.md"
            path.write_text("old", encoding="utf-8")
            with patch("src.ablation_outputs.os.replace", side_effect=OSError("injected")):
                with self.assertRaisesRegex(OSError, "injected"):
                    _atomic_write_text(path, "new")
            self.assertEqual(path.read_text(encoding="utf-8"), "old")
            self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_ablation_runner_rejects_duplicate_or_off_protocol_seeds(self) -> None:
        self.assertEqual(validate_seeds([4, 0]), (4, 0))
        with self.assertRaisesRegex(ValueError, "unique"):
            validate_seeds([0, 0])
        with self.assertRaisesRegex(ValueError, "0--4"):
            validate_seeds([5])

    def test_reference_commits_are_frozen_per_protocol(self) -> None:
        self.assertNotEqual(
            _reference_training_commit("overall_binary_ternary"),
            _reference_training_commit("unseen_component"),
        )

    def test_summary_selection_keeps_direction_and_cardinality_identity(self) -> None:
        frame = pd.DataFrame(
            [
                {"scope": "direction_cardinality", "direction": "isothermal", "component_count": 2.0, "subgroup": None, "value": 1.0},
                {"scope": "direction_cardinality", "direction": "isothermal", "component_count": 3.0, "subgroup": None, "value": 2.0},
                {"scope": "direction", "direction": "isothermal", "component_count": None, "subgroup": None, "value": 3.0},
            ]
        )

        selected = _select_summary(frame, "direction_cardinality", "isothermal", 3)

        self.assertEqual(selected["value"], 2.0)

    def test_hard_constraints_are_reported_as_not_applicable(self) -> None:
        def rows(_root, variant_id, variant):
            return [{"variant_id": variant_id, "family": variant.family}]

        with patch("src.ablation_outputs._metric_rows", side_effect=rows):
            _, physics = architecture_and_physics_tables(Path("."))

        status = physics.set_index("variant_id")["status"].to_dict()
        self.assertEqual(status["p1_gibbs_duhem"], "not_applicable_hard_constraint")
        self.assertEqual(status["p2_composition_conservation"], "not_applicable_hard_constraint")
        self.assertEqual(status["p5_permutation_consistency"], "not_applicable_hard_constraint")

    def test_manybody_table_retains_pairwise_wins_and_losses(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            full_dir = root / "full"
            pair_dir = root / "pair"
            for seed in ABLATION_SEEDS:
                for directory, y_prediction in ((full_dir, (0.8, 0.1)), (pair_dir, (0.7, 0.2))):
                    seed_dir = directory / f"seed_{seed}"
                    seed_dir.mkdir(parents=True, exist_ok=True)
                    pd.DataFrame(
                        [
                            self._prediction("s1", "sys-a", 0.8, y_prediction[0], 0),
                            self._prediction("s2", "sys-b", 0.2, y_prediction[1], 1),
                        ]
                    ).to_csv(seed_dir / "predictions.csv", index=False)

            def result_dir(_root, variant_id, _benchmark):
                return full_dir if variant_id == "a0_full" else pair_dir

            with patch("src.ablation_outputs._result_dir", side_effect=result_dir):
                table = manybody_system_effects(root)

        deltas = table.set_index("system_id")["delta_y_mae_pairwise_minus_full"]
        self.assertGreater(deltas["sys-a"], 0.0)
        self.assertLess(deltas["sys-b"], 0.0)
        self.assertEqual(set(table["seeds"]), {5})

    def test_physical_table_keeps_every_registered_generalization_benchmark(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for variant_id, variant in ABLATION_VARIANTS.items():
                for benchmark in variant.benchmarks:
                    directory = root / f"{variant_id}.{benchmark}"
                    for seed in ABLATION_SEEDS:
                        seed_dir = directory / f"seed_{seed}"
                        seed_dir.mkdir(parents=True, exist_ok=True)
                        (seed_dir / "physical_consistency.json").write_text(
                            '{"nonphysical_prediction_rate": 0.1}', encoding="utf-8"
                        )

            def result_dir(_root, variant_id, benchmark):
                return root / f"{variant_id}.{benchmark}"

            with patch("src.ablation_outputs._result_dir", side_effect=result_dir):
                table = physical_consistency_table(root)

        a6 = table.loc[table["variant_id"].eq("a6_direct_vle")]
        self.assertEqual(
            set(a6["benchmark"]),
            {"unseen_mixture", "unseen_component", "binary_to_ternary"},
        )

    def test_report_reads_soft_loss_accuracy_from_physics_table(self) -> None:
        architecture = pd.DataFrame(
            [
                {
                    "variant_id": variant,
                    "benchmark": benchmark,
                    "direction": "isothermal",
                    "observable": "y",
                    "system_macro_mae_mean": value,
                }
                for variant, benchmark, value in (
                    ("a0_full", "ternary", 0.10),
                    ("a1_rdkit_descriptors", "ternary", 0.11),
                    ("a2_no_interaction", "ternary", 0.12),
                    ("a3_pairwise_only", "ternary", 0.13),
                    ("a4_condition_concatenation", "ternary", 0.14),
                    ("a5_direct_activity", "ternary", 0.15),
                    ("a6_direct_vle", "ternary", 0.16),
                    ("a0_full", "unseen_mixture", 0.20),
                )
            ]
        )
        physics = pd.DataFrame(
            [
                {
                    "variant_id": variant,
                    "benchmark": "unseen_mixture",
                    "direction": "isothermal",
                    "observable": "y",
                    "system_macro_mae_mean": value,
                    "status": "completed",
                }
                for variant, value in (
                    ("p3_no_pure_boundary", 0.21),
                    ("p4_no_phase_continuity", 0.24),
                    ("p6_no_soft_physics", 0.22),
                )
            ]
        )
        physical = pd.DataFrame(
            [
                {
                    "variant_id": variant,
                    "benchmark": "unseen_mixture",
                    "nonphysical_prediction_rate_mean": rate,
                }
                for variant, rate in (
                    ("a0_full", 0.10),
                    ("p3_no_pure_boundary", 0.11),
                    ("p4_no_phase_continuity", 0.16),
                    ("p6_no_soft_physics", 0.12),
                )
            ]
        )
        manybody = pd.DataFrame({"delta_y_mae_pairwise_minus_full": [0.1, -0.05]})
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.md"
            write_report(report, architecture, physics, physical, manybody)
            text = report.read_text(encoding="utf-8")

        self.assertIn("**p4_no_phase_continuity** (\u0394 system-wise isothermal y MAE 0.04)", text)

    @staticmethod
    def _prediction(sample_id, system, y_true_1, y_pred_1, coverage):
        return {
            "sample_id": sample_id,
            "system_id": system,
            "direction": "isothermal",
            "component_count": 3,
            "binary_subsystem_coverage": coverage,
            "predicted_pressure_kpa": 100.0,
            "target_pressure_kpa": 100.0,
            "predicted_temperature_k": 350.0,
            "target_temperature_k": 350.0,
            "y_true_1": y_true_1,
            "y_true_2": 1.0 - y_true_1,
            "y_true_3": 0.0,
            "y_pred_1": y_pred_1,
            "y_pred_2": 1.0 - y_pred_1,
            "y_pred_3": 0.0,
        }


if __name__ == "__main__":
    unittest.main()
