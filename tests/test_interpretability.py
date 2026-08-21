import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import torch

from src.data import VLESample
from src.interpretability.core import simplex_response_directions, stable_pca_scores
from src.interpretability.analysis import _add_relative_volatility_fields
from src.interpretability.runner import _digest
from src.interpretability.selection import (
    eligible_ternary_systems,
    select_best_validation_seed,
)


def _sample(smiles: tuple[str, ...]) -> VLESample:
    count = len(smiles)
    composition = tuple([1.0 / count] * count)
    return VLESample(
        smiles=smiles,
        names=smiles,
        temperature_k=350.0,
        pressure_kpa=101.325,
        liquid_composition=composition,
        vapor_composition=composition,
        quality_weight=1.0,
        quality_status="passed",
        source="synthetic.xlsx",
        doi="synthetic",
    )


class InterpretabilityTests(unittest.TestCase):
    def test_simplex_response_directions_preserve_composition_closure(self) -> None:
        composition = torch.tensor([0.2, 0.3, 0.5])

        directions = simplex_response_directions(composition)

        self.assertEqual(tuple(directions.shape), (3, 3))
        torch.testing.assert_close(directions.sum(dim=0), torch.zeros(3))
        torch.testing.assert_close(torch.diag(directions), torch.ones(3))
        perturbed = composition[:, None] + 0.05 * directions
        self.assertTrue(torch.all(perturbed >= 0.0))
        torch.testing.assert_close(perturbed.sum(dim=0), torch.ones(3))

    def test_best_seed_is_selected_only_from_validation_loss(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            result_root = Path(temporary_directory) / "protocol"
            losses = {0: 0.4, 1: 0.2, 2: 0.3}
            for seed, loss in losses.items():
                seed_root = result_root / f"seed_{seed}"
                seed_root.mkdir(parents=True)
                (seed_root / "manifest.json").write_text(
                    json.dumps(
                        {
                            "status": "completed",
                            "seed": seed,
                            "best_validation_loss": loss,
                            "headline_metrics": {"y_mae": 1.0 - loss},
                        }
                    ),
                    encoding="utf-8",
                )

            selected = select_best_validation_seed(result_root)

            self.assertEqual(selected, 1)

    def test_ternary_requires_all_three_experimental_binary_subsystems(self) -> None:
        complete = _sample(("A", "B", "C"))
        incomplete = _sample(("A", "B", "D"))
        dataset = [
            complete,
            incomplete,
            _sample(("A", "B")),
            _sample(("A", "C")),
            _sample(("B", "C")),
            _sample(("A", "D")),
        ]

        selected = eligible_ternary_systems(dataset, [complete, incomplete])

        self.assertEqual(selected, (tuple(sorted(complete.smiles)),))

    def test_simplex_directions_reject_boundary_or_open_compositions(self) -> None:
        for composition in (
            torch.tensor([0.0, 0.5, 0.5]),
            torch.tensor([0.2, 0.2, 0.2]),
        ):
            with self.subTest(composition=composition.tolist()):
                with self.assertRaises(ValueError):
                    simplex_response_directions(composition)

    def test_pca_scores_are_deterministic_and_centered(self) -> None:
        values = np.asarray(
            [[-2.0, 1.0, 0.0], [-1.0, 0.5, 0.2], [1.0, -0.5, -0.2], [2.0, -1.0, 0.0]]
        )

        first_scores, first_explained = stable_pca_scores(values, components=2)
        second_scores, second_explained = stable_pca_scores(values, components=2)

        np.testing.assert_allclose(first_scores, second_scores)
        np.testing.assert_allclose(first_explained, second_explained)
        np.testing.assert_allclose(first_scores.mean(axis=0), np.zeros(2), atol=1e-12)
        self.assertTrue(np.all(first_explained >= 0.0))
        self.assertLessEqual(float(first_explained.sum()), 1.0 + 1e-12)

    def test_all_ternary_relative_volatility_pairs_are_exported(self) -> None:
        record = {}

        _add_relative_volatility_fields(record, [6.0, 3.0, 2.0], [3.0, 2.0, 1.0])

        self.assertEqual(record["alpha_12_full"], 2.0)
        self.assertEqual(record["alpha_13_full"], 3.0)
        self.assertEqual(record["alpha_23_full"], 1.5)
        self.assertAlmostEqual(
            record["delta_log_alpha_13_full_minus_pairwise"], np.log(3.0) - np.log(3.0)
        )

    def test_text_digest_is_independent_of_platform_line_endings(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            lf_path = Path(temporary_directory) / "lf.csv"
            crlf_path = Path(temporary_directory) / "crlf.csv"
            lf_path.write_bytes(b"a,b\n1,2\n")
            crlf_path.write_bytes(b"a,b\r\n1,2\r\n")

            self.assertEqual(_digest(lf_path), _digest(crlf_path))


if __name__ == "__main__":
    unittest.main()
