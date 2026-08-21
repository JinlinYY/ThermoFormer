import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from src.paper_outputs import (
    PROTOCOL_CONFIGS,
    bin_extrapolation_distances,
    experiment_task_records,
    metric_markdown_tables,
    select_metric_row,
    task_metric_markdown,
    task_metric_tables,
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

    def test_task_report_shows_joint_state_and_vapor_outputs(self) -> None:
        rows = []
        for direction in ("isothermal", "isobaric"):
            row = {
                "test_subset": "Binary-only model: binary test",
                "direction": direction,
                "valid_coverage_mean": 1.0,
                "valid_coverage_std": 0.0,
            }
            metrics = {
                "pressure_mae_kpa": (17.26, 8.42, 5),
                "pressure_rmse_kpa": (35.13, 14.93, 5),
                "pressure_r2": (0.911, 0.051, 5),
                "temperature_mae_k": (5.75, 1.61, 5),
                "temperature_rmse_k": (8.09, 2.50, 5),
                "temperature_r2": (0.920, 0.052, 5),
                "y_mae": (0.064, 0.01, 5),
                "y_rmse": (0.091, 0.02, 5),
                "y_r2": (0.930, 0.03, 5),
            }
            for metric, (mean, std, seeds) in metrics.items():
                row[f"{metric}_mean"] = mean
                row[f"{metric}_std"] = std
                row[f"{metric}_available_seeds"] = seeds
            rows.append(row)

        rendered = task_metric_markdown(pd.DataFrame(rows))

        self.assertIn("Isothermal P–x–y", rendered)
        self.assertIn("Molecules, T, x", rendered)
        self.assertIn("Bubble pressure P and vapor composition y", rendered)
        self.assertIn("Isobaric T–x–y", rendered)
        self.assertIn("Molecules, P, x", rendered)
        self.assertIn("Bubble temperature T and vapor composition y", rendered)
        self.assertEqual(rendered.count("| Vapor composition y |"), 2)

    def test_task_table_assembly_preserves_direction_and_cardinality(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            results_root = Path(temporary_directory)
            for protocol in PROTOCOL_CONFIGS:
                rows = []
                for direction in ("isothermal", "isobaric"):
                    rows.append(self._summary_row("direction", direction))
                if protocol == "overall_binary_ternary":
                    for component_count in (2, 3):
                        for direction in ("isothermal", "isobaric"):
                            rows.append(
                                self._summary_row(
                                    "direction_cardinality",
                                    direction,
                                    component_count=component_count,
                                )
                            )
                protocol_root = results_root / protocol
                protocol_root.mkdir()
                pd.DataFrame(rows).to_csv(protocol_root / "metrics_summary.csv", index=False)

            tables = task_metric_tables(results_root)

            self.assertEqual(
                {name: len(table) for name, table in tables.items()},
                {"binary": 4, "ternary": 2, "state": 12, "difficulty": 6, "scaling": 12},
            )
            binary_identities = {
                (
                    row["direction"],
                    None
                    if pd.isna(row["component_count"])
                    else int(row["component_count"]),
                )
                for _, row in tables["binary"].iterrows()
            }
            self.assertEqual(
                binary_identities,
                {
                    ("isothermal", None),
                    ("isobaric", None),
                    ("isothermal", 2),
                    ("isobaric", 2),
                },
            )
            self.assertEqual(set(tables["ternary"]["component_count"]), {3})

            joint_page = experiment_task_records(results_root, "overall_binary_ternary")
            self.assertEqual(len(joint_page), 4)
            self.assertEqual(
                {(row["direction"], row["component_count"]) for row in joint_page},
                {("isothermal", 2), ("isobaric", 2), ("isothermal", 3), ("isobaric", 3)},
            )
            for protocol in set(PROTOCOL_CONFIGS) - {"overall_binary_ternary"}:
                page = experiment_task_records(results_root, protocol)
                self.assertEqual(len(page), 2)
                self.assertEqual(
                    {row["direction"] for row in page}, {"isothermal", "isobaric"}
                )
                self.assertEqual({row["scope"] for row in page}, {"direction"})

    @staticmethod
    def _summary_row(
        scope: str,
        direction: str,
        *,
        component_count=None,
    ) -> dict[str, object]:
        return {
            "scope": scope,
            "direction": direction,
            "component_count": component_count,
            "subgroup": None,
            "seeds": 5,
            "scope_available_seeds": 5,
            "scope_seed_ids": "0,1,2,3,4",
        }


if __name__ == "__main__":
    unittest.main()
