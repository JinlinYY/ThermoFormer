import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from src.multiview_protocols import FORMAL_VARIANTS, MULTIVIEW_VARIANTS, PREDICTIVE_VARIANTS
from src.representation_outputs import (
    PREDICTIVE_SETTINGS,
    representation_predictive_table,
    write_representation_report,
)


def summary_rows(value: float) -> list[dict[str, object]]:
    rows = []
    for scope, cardinalities in (("direction", (None,)), ("direction_cardinality", (2, 3))):
        for component_count in cardinalities:
            for direction in ("isothermal", "isobaric"):
                row: dict[str, object] = {
                    "scope": scope,
                    "component_count": component_count,
                    "direction": direction,
                }
                for metric in (
                    "pressure_mae_kpa", "pressure_rmse_kpa", "pressure_r2",
                    "temperature_mae_k", "temperature_rmse_k", "temperature_r2",
                    "y_mae", "y_rmse", "y_r2", "valid_coverage",
                ):
                    row[f"{metric}_mean"] = value
                    row[f"{metric}_std"] = value / 10
                    row[f"{metric}_available_seeds"] = 5
                    row[f"{metric}_seed_ids"] = "0;1;2;3;4"
                rows.append(row)
    return rows


class RepresentationOutputTests(unittest.TestCase):
    def test_table_uses_three_requested_settings_and_v2_aliases_v0(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)

            def write(path: Path, value: float) -> None:
                path.parent.mkdir(parents=True, exist_ok=True)
                pd.DataFrame(summary_rows(value)).to_csv(path, index=False)

            for protocol in ("overall_binary", "overall_binary_ternary"):
                write(root / "results" / protocol / "metrics_summary.csv", 1.0)
            for index, variant_id in enumerate(PREDICTIVE_VARIANTS, start=2):
                binary = (
                    root / "results" / "multiview" / "predictive" / "runs"
                    / f"{variant_id}.on.overall_binary" / "metrics_summary.csv"
                )
                write(binary, float(index))
                joint_root = "formal" if variant_id in FORMAL_VARIANTS else "predictive"
                joint = (
                    root / "results" / "multiview" / joint_root / "runs"
                    / f"{variant_id}.on.overall_binary_ternary" / "metrics_summary.csv"
                )
                write(joint, float(index))

            table = representation_predictive_table(root)
            self.assertEqual(
                len(table), len(MULTIVIEW_VARIANTS) * len(PREDICTIVE_SETTINGS) * 2
            )
            self.assertEqual(set(table["setting_id"]), {row[0] for row in PREDICTIVE_SETTINGS})
            v0 = table.loc[table["variant_id"].eq("v0_legacy_unimol")]
            v2 = table.loc[table["variant_id"].eq("v2_unimol_only")]
            self.assertEqual(set(v2["source_variant_id"]), {"v0_legacy_unimol"})
            self.assertFalse(v2["independent_run"].any())
            self.assertEqual(
                v0.loc[v0["direction"].eq("isothermal"), "pressure_mae_kpa_mean"].tolist(),
                v2.loc[v2["direction"].eq("isothermal"), "pressure_mae_kpa_mean"].tolist(),
            )

            report = write_representation_report(root, table)
            content = report.read_text(encoding="utf-8")
            self.assertIn("Binary train → binary test", content)
            self.assertIn("Binary+ternary train → ternary test", content)
            self.assertIn("alias of V0", content)
            self.assertIn("MAE winners by setting", content)


if __name__ == "__main__":
    unittest.main()
