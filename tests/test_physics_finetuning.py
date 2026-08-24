import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np
import torch

from scripts.run_c1_physics_finetune import (
    output_roots,
    recover_completed_seed_manifest,
)
from src.artifacts import artifact_sha256
from src.config import PhysicsFineTuningConfig, load_experiment_config
from src.data import VLESample
from src.model import ThermoFormer, ThermoFormerConfig
from src.physics_finetuning import (
    configure_physics_finetuning,
    evaluate_physics_residuals,
    fit_physics_stage,
    load_stage1_checkpoint,
    physics_finetune_objective,
    physics_warmup_scale,
)
from src.training import TrainingConfig, _loader


class PhysicsFineTuningTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    @staticmethod
    def model() -> ThermoFormer:
        return ThermoFormer(
            ThermoFormerConfig(
                feature_dim=6,
                hidden_dim=8,
                layers=1,
                heads=2,
                pair_hidden_dim=8,
                pure_hidden_dim=8,
                fusion_mode="naive",
                rdkit_feature_dim=2,
                unimol_feature_dim=2,
                functional_group_feature_dim=2,
                chemical_attention_bias=False,
                context_pair_interaction=False,
            )
        )

    @staticmethod
    def samples() -> list[VLESample]:
        return [
            VLESample(
                smiles=("A", "B"),
                names=("A", "B"),
                temperature_k=340.0 + index,
                pressure_kpa=70.0 + index,
                liquid_composition=(x, 1.0 - x),
                vapor_composition=(min(0.95, x + 0.08), max(0.05, 0.92 - x)),
                quality_weight=1.0,
                quality_status="passed",
                source="synthetic.xlsx",
                doi=f"physics-{index}",
                experiment_mode="isothermal" if index % 2 == 0 else "isobaric",
            )
            for index, x in enumerate((0.2, 0.4, 0.6, 0.8))
        ]

    @staticmethod
    def features() -> dict[str, np.ndarray]:
        return {
            "A": np.asarray([1.0, 0.2, -0.1, 0.4, 1.0, 0.0], dtype=np.float32),
            "B": np.asarray([0.1, 1.0, 0.5, -0.2, 0.0, 1.0], dtype=np.float32),
        }

    @staticmethod
    def config(**overrides: object) -> TrainingConfig:
        values = dict(
            batch_size=4,
            epochs_supervised=80,
            epochs_physics=1,
            minimum_physics_epochs=1,
            early_stopping_patience=0,
            continuity_weight=1e-5,
            boundary_weight=1e-3,
            solver_weight=0.1,
            solver_batches_per_epoch=1,
            solver_iterations_train=2,
        )
        values.update(overrides)
        return TrainingConfig(**values)

    @staticmethod
    def finetuning() -> PhysicsFineTuningConfig:
        return PhysicsFineTuningConfig()

    def test_c1_configuration_keeps_vanilla_pair_potential(self) -> None:
        config = load_experiment_config(
            self.ROOT
            / "experiments/physics_finetuning/c1_three_view_vanilla/config.json"
        )
        self.assertEqual(config.encoder.representation, "multiview")
        self.assertEqual(config.encoder.fusion_mode, "naive")
        self.assertFalse(config.encoder.chemical_attention_bias)
        self.assertFalse(config.encoder.context_pair_interaction)
        self.assertFalse(config.model.chemical_attention_bias)
        self.assertFalse(config.model.context_pair_interaction)
        self.assertEqual(config.training.epochs_supervised, 80)
        self.assertEqual(config.training.epochs_physics, 5)
        self.assertIsNotNone(config.physics_finetuning)
        self.assertTrue(config.physics_finetuning.enabled)
        model = ThermoFormer(
            replace(
                config.model,
                feature_dim=6,
                fusion_mode="naive",
                rdkit_feature_dim=2,
                unimol_feature_dim=2,
                functional_group_feature_dim=2,
            )
        )
        self.assertIsNotNone(model.interaction)
        self.assertIsNone(model.chemical_interaction)
        self.assertIsNotNone(model.pair_potential)
        self.assertIsNone(model.context_pair_potential)

    def test_fugacity_variant_disables_every_legacy_physics_loss(self) -> None:
        config = load_experiment_config(
            self.ROOT
            / "experiments/physics_finetuning/c1_three_view_vanilla_fugacity/config.json"
        )
        self.assertEqual(config.training.continuity_weight, 0.0)
        self.assertEqual(config.training.boundary_weight, 0.0)
        self.assertEqual(config.training.solver_weight, 0.0)
        self.assertEqual(config.training.chemical_bias_weight, 0.0)
        self.assertGreater(
            config.physics_finetuning.teacher_forced_fugacity_weight, 0.0
        )

    def test_fugacity_pure_anchor_variant_only_strengthens_stage2_anchor(self) -> None:
        config = load_experiment_config(
            self.ROOT
            / "experiments/physics_finetuning/c1_three_view_vanilla_fugacity_pure_anchor/config.json"
        )
        self.assertEqual(config.training.pure_weight, 0.5)
        self.assertEqual(config.training.continuity_weight, 0.0)
        self.assertEqual(config.training.boundary_weight, 0.0)
        self.assertEqual(config.training.solver_weight, 0.0)
        self.assertEqual(config.training.chemical_bias_weight, 0.0)
        self.assertEqual(
            config.physics_finetuning.teacher_forced_fugacity_weight, 1.0
        )
        self.assertEqual(
            config.physics_finetuning.additional_pure_vapor_pressure_anchor_weight,
            0.5,
        )

    def test_partial_optimizer_contains_only_declared_unfrozen_groups(self) -> None:
        model = self.model()
        setup = configure_physics_finetuning(
            model, self.config(), self.finetuning()
        )
        optimizer_ids = {
            id(parameter)
            for group in setup.optimizer.param_groups
            for parameter in group["params"]
        }
        expected_prefixes = ("pair_potential.", "vapor_pressure.", "film.")
        for name, parameter in model.named_parameters():
            expected = name == "mixture_token" or name.startswith(expected_prefixes)
            self.assertEqual(parameter.requires_grad, expected, name)
            self.assertEqual(id(parameter) in optimizer_ids, expected, name)
        self.assertEqual(
            [group.name for group in setup.groups],
            ["pair_potential", "vapor_pressure", "film", "mixture_token"],
        )
        self.assertLess(setup.trainable_parameters, setup.total_parameters)

    def test_frozen_parameters_stay_fixed_after_optimizer_step(self) -> None:
        model = self.model()
        config = self.config()
        setup = configure_physics_finetuning(model, config, self.finetuning())
        frozen_before = {
            name: parameter.detach().clone()
            for name, parameter in model.named_parameters()
            if not parameter.requires_grad
        }
        batch = next(iter(_loader(self.samples(), self.features(), config, shuffle=False)))
        objective = physics_finetune_objective(
            model, batch, config, physics_scale=1.0, solver_enabled=True
        )
        setup.optimizer.zero_grad(set_to_none=True)
        objective.total.backward()
        setup.optimizer.step()
        for name, parameter in model.named_parameters():
            if name in frozen_before:
                torch.testing.assert_close(parameter.detach(), frozen_before[name])

    def test_each_unfrozen_group_has_nonzero_finite_gradient(self) -> None:
        model = self.model()
        config = self.config()
        setup = configure_physics_finetuning(model, config, self.finetuning())
        batch = next(iter(_loader(self.samples(), self.features(), config, shuffle=False)))
        objective = physics_finetune_objective(
            model, batch, config, physics_scale=1.0, solver_enabled=True
        )
        setup.optimizer.zero_grad(set_to_none=True)
        objective.total.backward()
        for group in setup.groups:
            gradients = [
                parameter.grad
                for parameter in group.parameters
                if parameter.grad is not None
            ]
            self.assertTrue(gradients, group.name)
            norm = torch.stack([gradient.norm() for gradient in gradients]).sum()
            self.assertTrue(torch.isfinite(norm), group.name)
            self.assertGreater(float(norm), 0.0, group.name)

    def test_physics_terms_have_real_pair_potential_gradient(self) -> None:
        model = self.model()
        config = self.config()
        configure_physics_finetuning(model, config, self.finetuning())
        batch = next(iter(_loader(self.samples(), self.features(), config, shuffle=False)))
        objective = physics_finetune_objective(
            model, batch, config, physics_scale=1.0, solver_enabled=True
        )
        physics = (
            config.continuity_weight * objective.continuity
            + config.boundary_weight * objective.boundary
            + config.solver_weight * objective.solver
        )
        physics.backward()
        gradients = [
            parameter.grad
            for name, parameter in model.named_parameters()
            if name.startswith("pair_potential.") and parameter.grad is not None
        ]
        self.assertTrue(gradients)
        total = torch.stack([gradient.norm() for gradient in gradients]).sum()
        self.assertTrue(torch.isfinite(total))
        self.assertGreater(float(total), 0.0)

    def test_fugacity_only_objective_has_pair_potential_gradient(self) -> None:
        model = self.model()
        config = self.config(
            continuity_weight=0.0,
            boundary_weight=0.0,
            solver_weight=0.0,
        )
        configure_physics_finetuning(model, config, self.finetuning())
        batch = next(iter(_loader(self.samples(), self.features(), config, shuffle=False)))
        objective = physics_finetune_objective(
            model,
            batch,
            config,
            physics_scale=1.0,
            solver_enabled=False,
            teacher_forced_fugacity_weight=1.0,
        )
        objective.teacher_forced_fugacity.backward()
        gradients = [
            parameter.grad
            for name, parameter in model.named_parameters()
            if name.startswith("pair_potential.") and parameter.grad is not None
        ]
        self.assertTrue(gradients)
        norm = torch.stack([gradient.norm() for gradient in gradients]).sum()
        self.assertTrue(torch.isfinite(norm))
        self.assertGreater(float(norm), 0.0)

    def test_additional_pure_anchor_changes_total_and_vapor_pressure_gradient(self) -> None:
        model = self.model()
        config = self.config(
            continuity_weight=0.0,
            boundary_weight=0.0,
            solver_weight=0.0,
        )
        configure_physics_finetuning(model, config, self.finetuning())
        endpoint = replace(
            self.samples()[0],
            liquid_composition=(1.0, 0.0),
            vapor_composition=(1.0, 0.0),
        )
        batch = next(iter(_loader([endpoint], self.features(), config, shuffle=False)))
        base = physics_finetune_objective(
            model,
            batch,
            config,
            physics_scale=0.5,
            solver_enabled=False,
        )
        anchored = physics_finetune_objective(
            model,
            batch,
            config,
            physics_scale=0.5,
            solver_enabled=False,
            additional_pure_vapor_pressure_anchor_weight=0.5,
        )
        torch.testing.assert_close(
            anchored.total,
            base.total + 0.25 * anchored.pure_vapor_pressure,
        )
        self.assertGreater(float(anchored.pure_vapor_pressure.detach()), 0.0)
        anchored.pure_vapor_pressure.backward()
        gradients = [
            parameter.grad
            for name, parameter in model.named_parameters()
            if name.startswith("vapor_pressure.") and parameter.grad is not None
        ]
        self.assertTrue(gradients)
        norm = torch.stack([gradient.norm() for gradient in gradients]).sum()
        self.assertTrue(torch.isfinite(norm))
        self.assertGreater(float(norm), 0.0)

    def test_reported_pure_anchor_loss_is_batch_partition_invariant(self) -> None:
        model = self.model()
        samples = [
            replace(
                sample,
                liquid_composition=(1.0, 0.0),
                vapor_composition=(1.0, 0.0),
                quality_weight=0.5 + 0.2 * index,
            )
            for index, sample in enumerate(self.samples()[:3])
        ]
        warm_batch = next(
            iter(_loader(samples, self.features(), self.config(batch_size=3), False))
        )
        physics_finetune_objective(
            model,
            warm_batch,
            self.config(batch_size=3),
            physics_scale=1.0,
            solver_enabled=False,
        )
        with torch.no_grad():
            for parameter in model.parameters():
                parameter.zero_()
        individual = evaluate_physics_residuals(
            model,
            samples,
            self.features(),
            self.config(batch_size=1),
            torch.device("cpu"),
        )
        together = evaluate_physics_residuals(
            model,
            samples,
            self.features(),
            self.config(batch_size=3),
            torch.device("cpu"),
        )
        self.assertAlmostEqual(
            individual["pure_vapor_pressure"],
            together["pure_vapor_pressure"],
            places=5,
        )

    def test_stage2_loads_stage1_checkpoint_and_validation_selects_epoch_zero(self) -> None:
        model = self.model()
        config = self.config(continuity_weight=0.0, boundary_weight=0.0, solver_weight=0.0)
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "stage1.pt"
            torch.save({"model": model.state_dict(), "model_config": model.config.to_dict()}, checkpoint)
            for parameter in model.parameters():
                parameter.data.add_(10.0)
            digest = load_stage1_checkpoint(model, checkpoint)
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
            stage1 = {name: value.detach().clone() for name, value in model.state_dict().items()}
            result = fit_physics_stage(
                model,
                self.samples(),
                self.features(),
                config,
                self.finetuning(),
                torch.device("cpu"),
                validation_samples=self.samples(),
            )
        self.assertIn(result.selected_stage, ("stage1", "stage2"))
        self.assertEqual(result.stage_states["stage1"].keys(), stage1.keys())
        for name in stage1:
            torch.testing.assert_close(result.stage_states["stage1"][name], stage1[name])
        self.assertNotIn("test", " ".join(result.selection_partitions))

    def test_physics_warmup_reaches_full_weight_after_two_epochs(self) -> None:
        self.assertEqual([physics_warmup_scale(epoch, 2) for epoch in (1, 2, 3)], [0.5, 1.0, 1.0])

    def test_smoke_output_is_isolated_from_formal_results(self) -> None:
        formal = output_roots(self.ROOT, smoke=False)
        smoke = output_roots(self.ROOT, smoke=True)
        self.assertNotEqual(formal, smoke)
        self.assertIn("smoke", str(smoke[0]))
        self.assertIn(
            "runs/experiments/physics_finetuning/c1_three_view_vanilla",
            formal[0].as_posix(),
        )

    def test_report_recovery_rejects_stale_or_corrupt_seed_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "metrics.json"
            artifact.write_text("{}\n", encoding="utf-8")
            manifest_path = root / "manifest.json"
            manifest = {
                "status": "completed",
                "protocol": "example",
                "seed": 0,
                "evaluation_partition": "test",
                "request_sha256": "current",
                "artifacts": {
                    "metrics": {
                        "path": str(artifact),
                        "sha256": artifact_sha256(artifact),
                    }
                },
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            recovered = recover_completed_seed_manifest(
                manifest_path,
                expected_status="completed",
                expected_protocol="example",
                expected_evaluation_partition="test",
                expected_request_sha256="current",
            )
            self.assertEqual(recovered["request_sha256"], "current")
            with self.assertRaisesRegex(RuntimeError, "stale request_sha256"):
                recover_completed_seed_manifest(
                    manifest_path,
                    expected_status="completed",
                    expected_protocol="example",
                    expected_evaluation_partition="test",
                    expected_request_sha256="changed",
                )
            artifact.write_text("corrupt\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "failed SHA"):
                recover_completed_seed_manifest(
                    manifest_path,
                    expected_status="completed",
                    expected_protocol="example",
                    expected_evaluation_partition="test",
                    expected_request_sha256="current",
                )


if __name__ == "__main__":
    unittest.main()
