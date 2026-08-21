import unittest

import torch

from src.model import ThermoFormer, ThermoFormerConfig


class ThermoFormerTests(unittest.TestCase):
    def setUp(self) -> None:
        torch.manual_seed(3)
        self.config = ThermoFormerConfig(feature_dim=6, hidden_dim=32, layers=1, heads=4)
        self.model = ThermoFormer(self.config).eval()
        self.molecules = torch.randn(2, 3, 6)
        self.temperature = torch.tensor([[340.0], [360.0]])
        self.pressure = torch.tensor([[90.0], [120.0]])
        self.x = torch.tensor([[0.2, 0.3, 0.5], [0.7, 0.3, 0.0]])
        self.mask = torch.tensor([[1.0, 1.0, 1.0], [1.0, 1.0, 0.0]])

    def test_outputs_are_permutation_equivariant(self) -> None:
        order = torch.tensor([2, 0, 1])
        actual = self.model(self.molecules, self.temperature, self.pressure, self.x, self.mask)
        permuted = self.model(
            self.molecules[:, order],
            self.temperature,
            self.pressure,
            self.x[:, order],
            self.mask[:, order],
        )

        torch.testing.assert_close(permuted.log_gamma, actual.log_gamma[:, order], atol=2e-5, rtol=2e-5)
        torch.testing.assert_close(permuted.log_psat, actual.log_psat[:, order], atol=2e-5, rtol=2e-5)

    def test_pure_vapor_pressure_depends_only_on_molecule_and_temperature(self) -> None:
        molecule = self.molecules[:, :1]
        low = self.model.pure_log_psat(molecule, torch.tensor([[300.0], [300.0]]))
        high = self.model.pure_log_psat(molecule, torch.tensor([[400.0], [400.0]]))

        self.assertTrue(torch.all(high > low))

    def test_present_pure_component_has_unit_activity_coefficient(self) -> None:
        x = torch.tensor([[1.0, 0.0, 0.0]])
        mask = torch.tensor([[1.0, 1.0, 1.0]])
        output = self.model(
            self.molecules[:1],
            self.temperature[:1],
            self.pressure[:1],
            x,
            mask,
        )

        self.assertAlmostEqual(output.log_gamma[0, 0].item(), 0.0, places=6)

    def test_activity_coefficients_obey_gibbs_duhem_along_simplex_direction(self) -> None:
        x = torch.tensor([[0.2, 0.3, 0.5]], requires_grad=True)
        output = self.model(
            self.molecules[:1],
            self.temperature[:1],
            self.pressure[:1],
            x,
            torch.ones_like(x),
        )
        direction = torch.tensor([[1.0, -1.0, 0.0]])
        directional_derivatives = []
        for component in range(3):
            gradient = torch.autograd.grad(
                output.log_gamma[0, component], x, retain_graph=True
            )[0]
            directional_derivatives.append((gradient * direction).sum())
        residual = (x[0] * torch.stack(directional_derivatives)).sum()

        self.assertAlmostEqual(residual.item(), 0.0, places=5)

    def test_film_can_be_disabled_for_conditioning_ablation(self) -> None:
        model = ThermoFormer(
            ThermoFormerConfig(
                feature_dim=6,
                hidden_dim=32,
                layers=1,
                heads=4,
                use_film=False,
            )
        ).eval()

        first = model(self.molecules, self.temperature, self.pressure, self.x, self.mask)
        second = model(
            self.molecules,
            self.temperature + 50.0,
            self.pressure * 2.0,
            self.x,
            self.mask,
        )

        torch.testing.assert_close(first.log_gamma, second.log_gamma)
        self.assertFalse(torch.equal(first.log_psat, second.log_psat))

    def test_ideal_activity_ablation_has_unit_activity_coefficients(self) -> None:
        config = ThermoFormerConfig(
            feature_dim=6,
            hidden_dim=32,
            layers=0,
            heads=4,
            use_transformer=False,
            use_mixture_token=False,
            use_film=False,
            activity_mode="ideal",
        )
        output = ThermoFormer(config)(
            self.molecules,
            self.temperature,
            self.pressure,
            self.x,
            self.mask,
        )

        torch.testing.assert_close(output.log_gamma, torch.zeros_like(output.log_gamma))

    def test_transformer_and_mixture_token_ablation_paths_run(self) -> None:
        configurations = [
            ThermoFormerConfig(
                feature_dim=6,
                hidden_dim=32,
                layers=0,
                heads=4,
                use_transformer=False,
            ),
            ThermoFormerConfig(
                feature_dim=6,
                hidden_dim=32,
                layers=1,
                heads=4,
                use_mixture_token=False,
            ),
        ]

        for config in configurations:
            with self.subTest(config=config):
                output = ThermoFormer(config)(
                    self.molecules,
                    self.temperature,
                    self.pressure,
                    self.x,
                    self.mask,
                )
                self.assertEqual(output.log_gamma.shape, self.x.shape)
                self.assertTrue(torch.isfinite(output.log_gamma).all())


if __name__ == "__main__":
    unittest.main()
