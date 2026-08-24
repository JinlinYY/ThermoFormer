import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

from scripts.run_c1_physics_finetune import output_roots, recover_completed_seed_manifest
from src.artifacts import artifact_sha256
from src.config import PhysicsFineTuningConfig, load_experiment_config
from src.data import VLESample
from src.model import ThermoFormer, ThermoFormerConfig
from src.physics_finetuning import (
    configure_physics_finetuning,
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
            solver_iterations_eval=4,
        )
        values.update(overrides)
        return TrainingConfig(**values)

    @staticmethod
    def finetuning() -> PhysicsFineTuningConfig:
        return PhysicsFineTuningConfig(teacher_forced_fugacity_weight=1.0)

    def test_final_configuration_is_c1_with_fugacity_only(self) -> None:
        config = load_experiment_config(
            self.ROOT
            / "experiments/physics_finetuning/c1_three_view_vanilla_fugacity/config.json"
        )
        self.assertEqual(config.encoder.representation, "multiview")
        self.assertEqual(config.encoder.fusion_mode, "naive")
        self.assertFalse(config.encoder.chemical_attention_bias)
        self.assertFalse(config.encoder.context_pair_interaction)
        self.assertEqual(config.training.epochs_physics, 5)
        self.assertEqual(config.physics_finetuning.teacher_forced_fugacity_weight, 1.0)

    def test_partial_optimizer_contains_only_declared_unfrozen_groups(self) -> None:
        model = self.model()
        setup = configure_physics_finetuning(model, self.config(), self.finetuning())
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
        self.assertLess(setup.trainable_parameters, setup.total_parameters)

    def test_frozen_parameters_stay_fixed_and_unfrozen_groups_receive_gradients(self) -> None:
        model = self.model()
        config = self.config()
        setup = configure_physics_finetuning(model, config, self.finetuning())
        frozen_before = {
            name: parameter.detach().clone()
            for name, parameter in model.named_parameters()
            if not parameter.requires_grad
        }
        batch = next(iter(_loader(self.samples(), self.features(), config, False)))
        objective = physics_finetune_objective(
            model,
            batch,
            config,
            physics_scale=1.0,
            teacher_forced_fugacity_weight=1.0,
        )
        setup.optimizer.zero_grad(set_to_none=True)
        objective.total.backward()
        for group in setup.groups:
            gradients = [p.grad for p in group.parameters if p.grad is not None]
            self.assertTrue(gradients, group.name)
            norm = torch.stack([gradient.norm() for gradient in gradients]).sum()
            self.assertTrue(torch.isfinite(norm), group.name)
            self.assertGreater(float(norm), 0.0, group.name)
        setup.optimizer.step()
        for name, parameter in model.named_parameters():
            if name in frozen_before:
                torch.testing.assert_close(parameter.detach(), frozen_before[name])

    def test_fugacity_loss_has_real_pair_potential_gradient(self) -> None:
        model = self.model()
        config = self.config()
        configure_physics_finetuning(model, config, self.finetuning())
        batch = next(iter(_loader(self.samples(), self.features(), config, False)))
        objective = physics_finetune_objective(
            model,
            batch,
            config,
            physics_scale=1.0,
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

    def test_stage2_loads_stage1_and_uses_validation_only_for_selection(self) -> None:
        model = self.model()
        config = self.config()
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "stage1.pt"
            torch.save(
                {"model": model.state_dict(), "model_config": model.config.to_dict()},
                checkpoint,
            )
            for parameter in model.parameters():
                parameter.data.add_(10.0)
            load_stage1_checkpoint(model, checkpoint)
            stage1 = {
                name: value.detach().clone() for name, value in model.state_dict().items()
            }
            result = fit_physics_stage(
                model,
                self.samples(),
                self.features(),
                config,
                self.finetuning(),
                torch.device("cpu"),
                validation_samples=self.samples(),
            )
        for name in stage1:
            torch.testing.assert_close(result.stage_states["stage1"][name], stage1[name])
        self.assertEqual(result.selection_partitions, ("validation",))

    def test_warmup_and_smoke_isolation(self) -> None:
        self.assertEqual(
            [physics_warmup_scale(epoch, 2) for epoch in (1, 2, 3)],
            [0.5, 1.0, 1.0],
        )
        formal = output_roots(self.ROOT, smoke=False)
        smoke = output_roots(self.ROOT, smoke=True)
        self.assertNotEqual(formal, smoke)
        self.assertIn("smoke", str(smoke[0]))
        self.assertIn("c1_three_view_vanilla_fugacity", formal[0].as_posix())

    def test_report_recovery_rejects_stale_status_or_corrupt_artifact(self) -> None:
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
                "analysis_status": "confirmatory",
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
                expected_analysis_status="confirmatory",
            )
            self.assertEqual(recovered["request_sha256"], "current")
            manifest["analysis_status"] = "diagnostic"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "stale analysis_status"):
                recover_completed_seed_manifest(
                    manifest_path,
                    expected_status="completed",
                    expected_protocol="example",
                    expected_evaluation_partition="test",
                    expected_request_sha256="current",
                    expected_analysis_status="confirmatory",
                )
            manifest["analysis_status"] = "confirmatory"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            artifact.write_text("corrupt\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "failed SHA"):
                recover_completed_seed_manifest(
                    manifest_path,
                    expected_status="completed",
                    expected_protocol="example",
                    expected_evaluation_partition="test",
                    expected_request_sha256="current",
                    expected_analysis_status="confirmatory",
                )


if __name__ == "__main__":
    unittest.main()
