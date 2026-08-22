import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from src.multiview_outputs import (
    _direction_rows, formal_seed_table, gate_summary_table, screening_table,
)
from src.multiview_protocols import (
    FORMAL_PROTOCOLS, FORMAL_VARIANTS, MULTIVIEW_SEEDS,
    SCREENING_PROTOCOLS, SCREENING_REPORT_VARIANTS,
)


class MultiViewOutputTests(unittest.TestCase):
    def test_direction_rows_keep_state_and_y_metrics_separate(self) -> None:
        rows = _direction_rows([
            {
                "scope": "direction", "direction": "isothermal",
                "pressure_mae_kpa": 1.0, "pressure_rmse_kpa": 2.0,
                "pressure_r2": 0.9, "y_mae": 0.1, "y_rmse": 0.2,
                "y_r2": 0.8, "valid_coverage": 0.95,
            },
            {
                "scope": "direction", "direction": "isobaric",
                "temperature_mae_k": 3.0, "temperature_rmse_k": 4.0,
                "temperature_r2": 0.7, "y_mae": 0.3, "y_rmse": 0.4,
                "y_r2": 0.6, "valid_coverage": 0.9,
            },
        ])
        self.assertEqual([(row["state"], row["state_mae"]) for row in rows], [("P", 1.0), ("T", 3.0)])
        self.assertEqual([row["y_mae"] for row in rows], [0.1, 0.3])

    def test_formal_seed_table_requires_and_preserves_all_seeds(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_rows = []
            for seed in MULTIVIEW_SEEDS:
                for direction in ("isothermal", "isobaric"):
                    source_rows.append(
                        {
                            "scope": "direction", "seed": seed, "direction": direction,
                            "pressure_mae_kpa": seed + 1.0, "pressure_rmse_kpa": seed + 2.0,
                            "pressure_r2": 0.9, "temperature_mae_k": seed + 3.0,
                            "temperature_rmse_k": seed + 4.0, "temperature_r2": 0.8,
                            "y_mae": 0.1 + seed / 100, "y_rmse": 0.2,
                            "y_r2": 0.7, "valid_coverage": 1.0,
                        }
                    )
            for variant in FORMAL_VARIANTS:
                for protocol in FORMAL_PROTOCOLS:
                    directory = (
                        root / "results" / "multiview" / "formal" / "runs"
                        / f"{variant}.on.{protocol}"
                    )
                    directory.mkdir(parents=True)
                    pd.DataFrame(source_rows).to_csv(directory / "metrics_by_seed.csv", index=False)
            for protocol in FORMAL_PROTOCOLS:
                directory = root / "results" / protocol
                directory.mkdir(parents=True)
                pd.DataFrame(source_rows).to_csv(directory / "metrics_by_seed.csv", index=False)
            output = formal_seed_table(root)
            self.assertEqual(
                len(output), (1 + len(FORMAL_VARIANTS)) * len(FORMAL_PROTOCOLS) * len(MULTIVIEW_SEEDS) * 2,
            )
            self.assertEqual(set(output["seed"]), set(MULTIVIEW_SEEDS))
            self.assertEqual(set(output["state"]), {"P", "T"})

    def test_gate_summary_keeps_single_seed_known_mixture_diagnostic(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "results" / "multiview" / "analysis"
            path.mkdir(parents=True)
            rows = []
            for seed in MULTIVIEW_SEEDS:
                rows.append({
                    "protocol": "unseen_component", "seed": seed, "scope": "global",
                    "subgroup": "all", "view": "rdkit", "mean_weight": 0.8,
                })
            rows.append({
                "protocol": "state_composition_interpolation", "seed": 0,
                "scope": "global", "subgroup": "all", "view": "rdkit",
                "mean_weight": 0.9,
            })
            pd.DataFrame(rows).to_csv(path / "multiview_gate_statistics.csv", index=False)
            output = gate_summary_table(root)
            observed = dict(zip(output["protocol"], output["seeds"]))
            self.assertEqual(observed["unseen_component"], 5)
            self.assertEqual(observed["state_composition_interpolation"], 1)

    def test_screening_report_replays_published_table_without_raw_runs(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "results" / "multiview" / "screening"
            path.mkdir(parents=True)
            rows = [
                {
                    "variant_id": variant,
                    "protocol": protocol,
                    "direction": direction,
                    "state": "P" if direction == "isothermal" else "T",
                }
                for variant in SCREENING_REPORT_VARIANTS
                for protocol in SCREENING_PROTOCOLS
                for direction in ("isothermal", "isobaric")
            ]
            pd.DataFrame(rows).to_csv(path / "screening_metrics.csv", index=False)
            replayed = screening_table(root)
            self.assertEqual(len(replayed), len(rows))
            self.assertEqual(set(replayed["variant_id"]), set(SCREENING_REPORT_VARIANTS))


if __name__ == "__main__":
    unittest.main()
