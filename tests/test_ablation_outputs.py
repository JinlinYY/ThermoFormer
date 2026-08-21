import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.ablation_outputs import (
    _select_summary,
    architecture_and_physics_tables,
    manybody_system_effects,
)
from src.ablation_protocols import ABLATION_SEEDS


class AblationOutputTests(unittest.TestCase):
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
