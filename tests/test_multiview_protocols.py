import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.run_multiview_suite import main as run_suite, release_accelerator_memory
from src.config import load_experiment_config
from src.multiview_protocols import MULTIVIEW_VARIANTS


class MultiViewProtocolTests(unittest.TestCase):
    def test_accelerator_cleanup_is_safe_without_cuda(self) -> None:
        with patch("torch.cuda.is_available", return_value=False):
            release_accelerator_memory()

    def test_v0_through_v6_are_concrete_and_scientifically_distinct(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(len(MULTIVIEW_VARIANTS), 7)
        signatures = set()
        for variant_id, variant in MULTIVIEW_VARIANTS.items():
            config = load_experiment_config(root / variant.config)
            signature = (
                config.encoder.representation,
                config.encoder.fusion_mode,
                config.encoder.use_rdkit_descriptors,
                config.encoder.use_unimol,
                config.encoder.use_functional_groups,
            )
            if variant_id not in ("v0_legacy_unimol", "v2_unimol_only"):
                self.assertNotIn(signature, signatures)
            signatures.add(signature)
        self.assertEqual(
            load_experiment_config(root / MULTIVIEW_VARIANTS["v6_full_interaction"].config).encoder.fusion_mode,
            "interaction_specific",
        )

    def test_locked_stage_rejects_off_matrix_variants_and_seeds(self) -> None:
        with self.assertRaisesRegex(ValueError, "locked stage matrix"):
            run_suite([
                "--stage", "screening", "--variant", "v3_functional_group_only"
            ])
        with self.assertRaisesRegex(ValueError, "seeds must be exactly"):
            run_suite(["--stage", "formal", "--seeds", "0"])


if __name__ == "__main__":
    unittest.main()
