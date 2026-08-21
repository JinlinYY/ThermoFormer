import unittest

import numpy as np
import pandas as pd

from src.paper_outputs import bin_extrapolation_distances, select_metric_row


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


if __name__ == "__main__":
    unittest.main()
