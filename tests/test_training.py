import unittest
from unittest import mock

import numpy as np
import torch

from src.data import VLESample
from src.model import ModelOutputs, ThermoFormer, ThermoFormerConfig
from src.pure_properties import AntoineParameters, PurePropertyCatalog
from src.thermo import solve_isobaric, solve_isothermal
from src.training import TrainingConfig, evaluate_model, fit_model


class MixedModeIdealModel(torch.nn.Module):
    def forward(self, molecules, temperature_k, pressure_kpa, x, mask):
        constant = torch.tensor([100.0, 50.0, 1.0], device=x.device).expand_as(x)
        temperature_dependent = temperature_k.expand_as(x)
        is_isothermal_system = molecules[:, :1, 0] > 0.5
        psat = torch.where(is_isothermal_system, constant, temperature_dependent)
        return ModelOutputs(log_gamma=torch.zeros_like(x), log_psat=torch.log(psat))


class ConstantOneIdealModel(torch.nn.Module):
    def forward(self, molecules, temperature_k, pressure_kpa, x, mask):
        return ModelOutputs(log_gamma=torch.zeros_like(x), log_psat=torch.zeros_like(x))


class NonfiniteIdealModel(torch.nn.Module):
    def forward(self, molecules, temperature_k, pressure_kpa, x, mask):
        return ModelOutputs(
            log_gamma=torch.zeros_like(x),
            log_psat=torch.full_like(x, float("nan")),
        )


class NonfiniteTrainModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.offset = torch.nn.Parameter(torch.tensor(0.0))

    def forward(self, molecules, temperature_k, pressure_kpa, x, mask):
        return ModelOutputs(
            log_gamma=self.offset.expand_as(x) * 0.0,
            log_psat=self.offset.expand_as(x) + float("nan"),
        )


class TrainingSmokeTests(unittest.TestCase):
    def test_evaluation_fails_instead_of_reporting_nonfinite_metrics(self) -> None:
        sample = VLESample(
            smiles=("A", "B"),
            names=("A", "B"),
            temperature_k=350.0,
            pressure_kpa=70.0,
            liquid_composition=(0.4, 0.6),
            vapor_composition=(0.5, 0.5),
            quality_weight=1.0,
            quality_status="passed",
            source="synthetic.xlsx",
            doi="nan",
            experiment_mode="isothermal",
        )
        features = {
            "A": np.zeros(1, dtype=np.float32),
            "B": np.zeros(1, dtype=np.float32),
        }

        with self.assertRaisesRegex(FloatingPointError, "non-finite"):
            evaluate_model(
                NonfiniteIdealModel(),
                [sample],
                features,
                batch_size=1,
                device=torch.device("cpu"),
                solver_iterations=1,
            )

    def test_evaluation_prefers_catalogued_antoine_pressure(self) -> None:
        sample = VLESample(
            smiles=("O", "X"),
            names=("water", "X"),
            temperature_k=373.15,
            pressure_kpa=101.336,
            liquid_composition=(1.0, 0.0),
            vapor_composition=(1.0, 0.0),
            quality_weight=1.0,
            quality_status="passed",
            source="synthetic.xlsx",
            doi="antoine",
            experiment_mode="isothermal",
        )
        catalog = PurePropertyCatalog(
            entries={
                "O": AntoineParameters(8.07131, 1730.63, 233.426, 274.15, 373.15)
            }
        )
        metrics = evaluate_model(
            ConstantOneIdealModel(),
            [sample],
            {"O": np.zeros(1, dtype=np.float32), "X": np.zeros(1, dtype=np.float32)},
            batch_size=1,
            device=torch.device("cpu"),
            pure_property_catalog=catalog,
        )

        self.assertAlmostEqual(metrics["isothermal_pressure_log_rmse"], 0.0, places=4)

    def test_evaluation_uses_mode_specific_bubble_solvers(self) -> None:
        samples = [
            VLESample(
                smiles=("A", "B"),
                names=("A", "B"),
                temperature_k=350.0,
                pressure_kpa=70.0,
                liquid_composition=(0.4, 0.6),
                vapor_composition=(4.0 / 7.0, 3.0 / 7.0),
                quality_weight=1.0,
                quality_status="passed",
                source="synthetic.xlsx",
                doi="isothermal",
                experiment_mode="isothermal",
            ),
            VLESample(
                smiles=("C", "D"),
                names=("C", "D"),
                temperature_k=350.0,
                pressure_kpa=350.0,
                liquid_composition=(0.4, 0.6),
                vapor_composition=(0.4, 0.6),
                quality_weight=1.0,
                quality_status="passed",
                source="synthetic.xlsx",
                doi="isobaric",
                experiment_mode="isobaric",
            ),
        ]
        features = {
            "A": np.asarray([1.0], dtype=np.float32),
            "B": np.asarray([1.0], dtype=np.float32),
            "C": np.asarray([0.0], dtype=np.float32),
            "D": np.asarray([0.0], dtype=np.float32),
        }

        with (
            mock.patch("src.thermo.solve_isothermal", wraps=solve_isothermal) as isothermal,
            mock.patch("src.thermo.solve_isobaric", wraps=solve_isobaric) as isobaric,
        ):
            metrics = evaluate_model(
                MixedModeIdealModel(), samples, features, batch_size=2, device=torch.device("cpu")
            )

        self.assertAlmostEqual(metrics["isothermal_pressure_log_rmse"], 0.0, places=5)
        self.assertAlmostEqual(metrics["isothermal_convergence_rate"], 1.0)
        self.assertAlmostEqual(metrics["isobaric_temperature_rmse_k"], 0.0, places=4)
        self.assertAlmostEqual(metrics["isobaric_convergence_rate"], 1.0)
        self.assertIsNone(isothermal.call_args.kwargs.get("initial_pressure_kpa"))
        self.assertIsNone(isobaric.call_args.kwargs.get("initial_temperature_k"))

    def test_training_fails_before_nonfinite_loss_can_update_parameters(self) -> None:
        row = VLESample(
            smiles=("A", "B"),
            names=("A", "B"),
            temperature_k=350.0,
            pressure_kpa=70.0,
            liquid_composition=(0.4, 0.6),
            vapor_composition=(0.5, 0.5),
            quality_weight=1.0,
            quality_status="passed",
            source="synthetic.xlsx",
            doi="nan-train",
        )
        model = NonfiniteTrainModel()
        before = model.offset.detach().clone()

        with self.assertRaisesRegex(FloatingPointError, "non-finite"):
            fit_model(
                model,
                [row],
                {"A": np.zeros(1, dtype=np.float32), "B": np.zeros(1, dtype=np.float32)},
                TrainingConfig(batch_size=1, epochs_supervised=1, epochs_physics=0),
                torch.device("cpu"),
            )

        torch.testing.assert_close(model.offset.detach(), before)

    def test_one_epoch_updates_through_thermodynamic_objective(self) -> None:
        samples = [
            VLESample(
                smiles=("A", "B"),
                names=("A", "B"),
                temperature_k=340.0,
                pressure_kpa=70.0,
                liquid_composition=(x, 1.0 - x),
                vapor_composition=(x, 1.0 - x),
                quality_weight=1.0,
                quality_status="passed",
                source="synthetic.xlsx",
                doi="synthetic",
            )
            for x in (0.2, 0.4, 0.6, 0.8)
        ]
        features = {
            "A": np.asarray([1.0, 0.0, 0.0, 0.0], dtype=np.float32),
            "B": np.asarray([0.0, 1.0, 0.0, 0.0], dtype=np.float32),
        }
        model = ThermoFormer(
            ThermoFormerConfig(feature_dim=4, hidden_dim=16, layers=1, heads=4)
        )
        config = TrainingConfig(
            batch_size=4,
            epochs_supervised=1,
            epochs_physics=1,
            learning_rate=1e-4,
            boundary_weight=1e-3,
            solver_weight=0.1,
            solver_batches_per_epoch=1,
            solver_iterations_train=1,
        )

        with (
            mock.patch("src.thermo.solve_isothermal", wraps=solve_isothermal) as isothermal,
            mock.patch("src.thermo.solve_isobaric", wraps=solve_isobaric) as isobaric,
        ):
            result = fit_model(model, samples, features, config, torch.device("cpu"))

        self.assertEqual(len(result.history), 2)
        self.assertEqual([row["stage"] for row in result.history], ["experimental", "physics"])
        self.assertTrue(np.isfinite(result.history[0]["train"]["total"]))
        for name in ("boundary", "solver"):
            self.assertEqual(result.history[0]["train"][name], 0.0)
            self.assertTrue(np.isfinite(result.history[1]["train"][name]))
        self.assertIsNone(isothermal.call_args.kwargs.get("initial_pressure_kpa"))
        self.assertIsNone(isobaric.call_args.kwargs.get("initial_temperature_k"))


if __name__ == "__main__":
    unittest.main()
