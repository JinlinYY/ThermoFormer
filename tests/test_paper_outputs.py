import unittest

import numpy as np
import pandas as pd

from src.paper_outputs import (
    bin_extrapolation_distances,
    metric_markdown_tables,
    select_metric_row,
)


class PaperOutputTests(unittest.TestCase):
    def test_select_metric_row_requires_exact_identity(self) -> None:
        frame = pd.DataFrame(
            [
                {
                    "scope": "cardinality",
                    "direction": np.nan,
                    "component_count": 2.0,
                    "subgroup": np.nan,
                },
                {
                    "scope": "cardinality",
                    "direction": np.nan,
                    "component_count": 3.0,
                    "subgroup": np.nan,
                },
            ]
        )
        row = select_metric_row(frame, "cardinality", component_count=3)
        self.assertEqual(row["component_count"], 3)
        with self.assertRaisesRegex(ValueError, "Expected one metric row"):
            select_metric_row(frame, "cardinality")

    def test_distance_bins_keep_physical_metrics_separate(self) -> None:
        frame = pd.DataFrame(
            {
                "sample_id": [f"s{index}" for index in range(10)],
                "distance": np.arange(1, 11, dtype=float),
                "normalized_distance": np.arange(1, 11, dtype=float) / 10.0,
                "pressure_abs_error_kpa": np.arange(10, dtype=float),
                "temperature_abs_error_k": np.arange(10, dtype=float) + 20.0,
                "y_abs_error": np.arange(10, dtype=float) / 100.0,
            }
        )
        result = bin_extrapolation_distances(frame, bins=5)
        self.assertEqual(len(result), 5)
        self.assertEqual(int(result["samples"].sum()), 10)
        self.assertLess(result["pressure_mae_kpa"].iloc[0], result["pressure_mae_kpa"].iloc[-1])
        self.assertGreater(result["temperature_mae_k"].min(), result["pressure_mae_kpa"].min())

    def test_metric_tables_report_mae_rmse_r2_and_available_seeds(self) -> None:
        row = {"test_subset": "Held-out systems"}
        values = {
            "pressure_mae_kpa": (1.2, 0.1, 4),
            "pressure_rmse_kpa": (2.3, 0.2, 4),
            "pressure_r2": (0.91, 0.03, 4),
            "temperature_mae_k": (3.4, 0.4, 5),
            "temperature_rmse_k": (4.5, 0.5, 5),
            "temperature_r2": (0.82, 0.04, 5),
            "y_mae": (0.056, 0.006, 5),
            "y_rmse": (0.078, 0.008, 5),
            "y_r2": (0.73, 0.05, 5),
        }
        for metric, (mean, std, seeds) in values.items():
            row[f"{metric}_mean"] = mean
            row[f"{metric}_std"] = std
            row[f"{metric}_available_seeds"] = seeds
        row.update({"valid_coverage_mean": 0.99, "valid_coverage_std": 0.01})

        rendered = metric_markdown_tables(pd.DataFrame([row]))

        self.assertIn("Pressure metrics", rendered)
        self.assertIn("Temperature metrics", rendered)
        self.assertIn("Vapor-composition metrics", rendered)
        self.assertEqual(rendered.count("MAE"), 3)
        self.assertEqual(rendered.count("RMSE"), 3)
        self.assertEqual(rendered.count("R²"), 3)
        self.assertIn("1.20 ± 0.10 (n=4)", rendered)
        self.assertIn("0.730 ± 0.050 (n=5)", rendered)


if __name__ == "__main__":
    unittest.main()
