import unittest
from dataclasses import fields
from pathlib import Path

from src.chemical_attention_protocols import CHEMICAL_ATTENTION_FORMAL_PROTOCOLS
from src.config import PhysicsFineTuningConfig, load_experiment_config
from src.multiview_protocols import PREDICTIVE_PROTOCOLS
from src.training import TrainingConfig


class FinalExperimentScopeTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_final_c1_configuration_is_three_view_vanilla(self) -> None:
        config = load_experiment_config(
            self.ROOT
            / "experiments/physics_finetuning/c1_three_view_vanilla_fugacity/config.json"
        )
        self.assertEqual(config.encoder.representation, "multiview")
        self.assertEqual(config.encoder.fusion_mode, "naive")
        self.assertTrue(config.encoder.use_rdkit_descriptors)
        self.assertTrue(config.encoder.use_unimol)
        self.assertTrue(config.encoder.use_functional_groups)
        self.assertFalse(config.encoder.chemical_attention_bias)
        self.assertFalse(config.encoder.context_pair_interaction)

    def test_stage2_configuration_exposes_only_fugacity_loss(self) -> None:
        training_fields = {field.name for field in fields(TrainingConfig)}
        self.assertFalse(
            {
                "continuity_weight",
                "boundary_weight",
                "solver_weight",
                "chemical_bias_weight",
                "solver_batches_per_epoch",
            }
            & training_fields
        )
        finetuning_fields = {field.name for field in fields(PhysicsFineTuningConfig)}
        self.assertIn("teacher_forced_fugacity_weight", finetuning_fields)
        self.assertNotIn(
            "additional_pure_vapor_pressure_anchor_weight", finetuning_fields
        )

    def test_ablation_protocols_are_joint_binary_ternary_only(self) -> None:
        self.assertEqual(
            CHEMICAL_ATTENTION_FORMAL_PROTOCOLS, ("overall_binary_ternary",)
        )
        self.assertEqual(PREDICTIVE_PROTOCOLS, ("overall_binary_ternary",))

    def test_only_fugacity_physics_experiment_remains(self) -> None:
        root = self.ROOT / "experiments/physics_finetuning"
        directories = sorted(path.name for path in root.iterdir() if path.is_dir())
        self.assertEqual(directories, ["c1_three_view_vanilla_fugacity"])


if __name__ == "__main__":
    unittest.main()
