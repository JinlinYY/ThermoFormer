import unittest
from pathlib import Path

from src.config import load_experiment_config
from src.multiview_protocols import MULTIVIEW_VARIANTS


class MultiViewProtocolTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
