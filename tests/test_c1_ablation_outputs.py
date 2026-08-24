import tempfile
import unittest
from pathlib import Path

from src.c1_ablation_outputs import (
    C1_ABLATION_SOURCES,
    collect_c1_ablation_rows,
    write_c1_ablation_outputs,
)


class C1AblationOutputTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_retained_matrix_has_four_outputs_and_overall_only(self) -> None:
        rows = collect_c1_ablation_rows(self.ROOT)
        self.assertEqual(len(rows), 2 * len(C1_ABLATION_SOURCES))
        self.assertEqual({row["protocol"] for row in rows}, {"overall_binary_ternary"})
        self.assertEqual({row["direction"] for row in rows}, {"isothermal", "isobaric"})
        final_rows = [row for row in rows if row["variant_id"] == "c1_final"]
        self.assertEqual(len(final_rows), 2)
        for row in final_rows:
            self.assertGreater(row["state_r2_mean"], 0.9)
            self.assertGreater(row["y_r2_mean"], 0.9)
            self.assertEqual(row["valid_coverage_mean"], 1.0)
        fg_rows = [row for row in rows if row["variant_id"] == "v3_fg"]
        self.assertLess(
            next(row for row in fg_rows if row["direction"] == "isothermal")[
                "valid_coverage_mean"
            ],
            0.7,
        )

    def test_generated_report_contains_c1_and_fugacity_comparisons(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            outputs = write_c1_ablation_outputs(
                self.ROOT,
                output_root=temporary / "results",
                report_path=temporary / "report.md",
            )
            self.assertEqual(len(outputs), 3)
            written = outputs[0].read_text(encoding="utf-8")
        self.assertIn("C1 RDKit + Uni-Mol + FG vanilla", written)
        self.assertIn("Fugacity Stage 2", written)
        self.assertIn("overall_binary_ternary", written)


if __name__ == "__main__":
    unittest.main()
