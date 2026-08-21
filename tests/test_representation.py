import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.representation import UniMolV2Encoder


class FakeUniMol:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], bool]] = []

    def get_repr(self, smiles, return_atomic_reprs=False):
        self.calls.append((list(smiles), return_atomic_reprs))
        return {"cls_repr": np.arange(len(smiles) * 4, dtype=np.float32).reshape(len(smiles), 4)}


class UniMolV2EncoderTests(unittest.TestCase):
    def test_uses_cls_repr_dictionary_and_reuses_cache(self) -> None:
        backend = FakeUniMol()
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / "unimolv2.npz"
            encoder = UniMolV2Encoder(cache, batch_size=2, backend_factory=lambda **_: backend)

            first = encoder.encode(["O", "CCO", "O"])
            second = encoder.encode(["CCO", "O"])

        self.assertEqual(set(first), {"CCO", "O"})
        self.assertEqual(first["CCO"].shape, (4,))
        self.assertEqual(len(backend.calls), 1)
        self.assertFalse(backend.calls[0][1])
        np.testing.assert_array_equal(first["O"], second["O"])


if __name__ == "__main__":
    unittest.main()
