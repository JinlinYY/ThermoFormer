import unittest

import numpy as np
import torch

from src.model import ThermoFormer, ThermoFormerConfig
from src.representation import RDKitDescriptorScaler
from src.thermo import solve_isothermal


def multiview_model() -> ThermoFormer:
    torch.manual_seed(7)
    return ThermoFormer(
        ThermoFormerConfig(
            feature_dim=9,
            hidden_dim=12,
            layers=1,
            heads=3,
            pair_hidden_dim=12,
            rdkit_feature_dim=2,
            unimol_feature_dim=4,
            functional_group_feature_dim=3,
            fusion_mode="interaction_specific",
        )
    )


class MultiViewRepresentationTests(unittest.TestCase):
    def test_rdkit_scaler_uses_train_molecules_only(self) -> None:
        raw = {
            "train-a": np.asarray([0.0, 10.0], dtype=np.float32),
            "train-b": np.asarray([2.0, 14.0], dtype=np.float32),
            "held-out": np.asarray([100.0, 100.0], dtype=np.float32),
        }
        scaler = RDKitDescriptorScaler.fit(raw, ["train-a", "train-b"], ("a", "b"))
        np.testing.assert_allclose(scaler.mean, [1.0, 12.0])
        np.testing.assert_allclose(scaler.std, [1.0, 2.0])
        self.assertEqual(scaler.fit_smiles, ("train-a", "train-b"))
        self.assertGreater(float(scaler.transform(raw["held-out"])[0]), 90.0)

    def test_multiview_forward_binary_and_ternary(self) -> None:
        model = multiview_model()
        molecules = torch.randn(2, 3, 9)
        temperature = torch.full((2, 1), 350.0)
        pressure = torch.full((2, 1), 101.325)
        x = torch.tensor([[0.4, 0.6, 0.0], [0.2, 0.3, 0.5]])
        mask = torch.tensor([[1.0, 1.0, 0.0], [1.0, 1.0, 1.0]])
        output = model(molecules, temperature, pressure, x, mask, return_view_weights=True)
        self.assertEqual(output.log_gamma.shape, (2, 3))
        self.assertEqual(output.view_weights.shape, (2, 3, 3, 3))
        self.assertTrue(torch.isfinite(output.log_gamma).all())
        self.assertTrue(torch.isfinite(output.excess_gibbs_rt).all())
        self.assertTrue(torch.allclose(output.view_weights[0, 0, 1].sum(), torch.tensor(1.0)))
        self.assertTrue(torch.all(output.view_weights[0, 0, 2] == 0.0))

    def test_pair_interaction_and_component_permutation_symmetry(self) -> None:
        model = multiview_model().eval()
        molecules = torch.randn(1, 3, 9)
        temperature = torch.tensor([[360.0]])
        pressure = torch.tensor([[120.0]])
        x = torch.tensor([[0.2, 0.3, 0.5]])
        mask = torch.ones_like(x)
        permutation = torch.tensor([2, 0, 1])
        original = model(molecules, temperature, pressure, x, mask, return_view_weights=True)
        permuted = model(
            molecules[:, permutation], temperature, pressure, x[:, permutation],
            mask[:, permutation], return_view_weights=True,
        )
        self.assertTrue(torch.allclose(original.excess_gibbs_rt, permuted.excess_gibbs_rt, atol=1e-6))
        self.assertTrue(torch.allclose(original.log_gamma[:, permutation], permuted.log_gamma, atol=1e-5))
        expected_pairs = original.pair_interactions[:, permutation][:, :, permutation]
        self.assertTrue(torch.allclose(expected_pairs, permuted.pair_interactions, atol=1e-6))
        expected_weights = original.view_weights[:, permutation][:, :, permutation]
        self.assertTrue(torch.allclose(expected_weights, permuted.view_weights, atol=1e-6))
        original_state = solve_isothermal(
            model, molecules, temperature, x, mask, iterations=3, strict=False
        )
        permuted_state = solve_isothermal(
            model, molecules[:, permutation], temperature, x[:, permutation],
            mask[:, permutation], iterations=3, strict=False,
        )
        self.assertTrue(torch.allclose(original_state.pressure_kpa, permuted_state.pressure_kpa, atol=1e-5))
        self.assertTrue(torch.allclose(original_state.y[:, permutation], permuted_state.y, atol=1e-5))

    def test_excess_gibbs_activity_and_solver_gradients_are_finite(self) -> None:
        model = multiview_model()
        molecules = torch.randn(1, 3, 9)
        temperature = torch.tensor([[350.0]])
        x = torch.tensor([[0.25, 0.35, 0.40]], requires_grad=True)
        mask = torch.ones_like(x)
        output = model(molecules, temperature, torch.tensor([[101.325]]), x, mask)
        composition_gradient = torch.autograd.grad(
            output.excess_gibbs_rt.sum(), x, create_graph=True
        )[0]
        self.assertTrue(torch.isfinite(composition_gradient).all())
        self.assertTrue(torch.isfinite(output.log_gamma).all())
        state = solve_isothermal(
            model, molecules, temperature, x, mask, iterations=2, strict=False
        )
        state.pressure_kpa.sum().backward()
        gradients = [parameter.grad for parameter in model.parameters() if parameter.grad is not None]
        self.assertTrue(gradients)
        self.assertTrue(all(torch.isfinite(value).all() for value in gradients))
        self.assertGreater(sum(float(value.abs().sum()) for value in gradients), 0.0)

    def test_legacy_unimol_state_dict_contract_is_preserved(self) -> None:
        model = ThermoFormer(ThermoFormerConfig(feature_dim=4, hidden_dim=8, layers=1, heads=2))
        self.assertIn("molecular_encoder.0.weight", model.state_dict())
        self.assertFalse(any(name.startswith("view_projectors") for name in model.state_dict()))


if __name__ == "__main__":
    unittest.main()
