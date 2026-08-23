import tempfile
import unittest
from pathlib import Path

from scripts.run_chemical_attention_suite import main
from src.chemical_attention_protocols import CHEMICAL_ATTENTION_VARIANTS
from src.config import load_experiment_config


class ChemicalAttentionExperimentTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_variants_are_single_factor_controlled(self) -> None:
        configs = {
            variant_id: load_experiment_config(self.ROOT / variant.config)
            for variant_id, variant in CHEMICAL_ATTENTION_VARIANTS.items()
        }
        self.assertFalse(configs["c0_current_vanilla"].encoder.chemical_attention_bias)
        self.assertEqual(configs["c0_current_vanilla"].encoder.representation, "unimol_v2")
        self.assertEqual(configs["c1_three_view_vanilla"].encoder.fusion_mode, "naive")
        self.assertFalse(configs["c1_three_view_vanilla"].encoder.chemical_attention_bias)
        self.assertTrue(configs["c2_chemical_bias_full"].encoder.chemical_attention_bias)
        self.assertTrue(configs["c2_chemical_bias_full"].encoder.context_pair_interaction)
        self.assertFalse(configs["c3_no_pair_bias"].encoder.chemical_attention_bias)
        self.assertTrue(configs["c3_no_pair_bias"].encoder.context_pair_interaction)
        self.assertFalse(configs["c4_no_functional_group"].encoder.use_functional_groups)
        self.assertTrue(configs["c4_no_functional_group"].encoder.chemical_attention_bias)

    def test_formal_stage_requires_explicit_review_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "confirm-pilot-reviewed"):
                main(["--stage", "formal", "--artifact-root", directory])
            with self.assertRaisesRegex(RuntimeError, "pilot report"):
                main(
                    [
                        "--stage",
                        "formal",
                        "--artifact-root",
                        directory,
                        "--confirm-pilot-reviewed",
                    ]
                )


if __name__ == "__main__":
    unittest.main()
