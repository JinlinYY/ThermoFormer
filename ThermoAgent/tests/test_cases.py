"""Behavioral checks for the numerical case interfaces."""

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import binary
from extraction import FEED, RecordedEndpoints, cascade, experimental_split, lever_rule
from reproduce import (
    ROOT,
    binary_case,
    column_case,
    extraction_case,
    load,
    verify_manifest,
)


class PaperCases(unittest.TestCase):
    def test_binary_analytical_limits(self):
        self.assertEqual(len(binary.tests()), 5)

    def test_three_component_lever_rule_rejects_invalid_feed(self):
        endpoints = np.asarray(
            load(ROOT / "cases/crossflow_extraction/data/interpolation_protocol.json")[
                "pairs_by_temperature"
            ]["303.15"][2]
        )
        mixed = 0.3 * endpoints[0] + 0.7 * endpoints[1]
        self.assertAlmostEqual(lever_rule(mixed, *endpoints), 0.3, places=12)
        with self.assertRaises(ValueError):
            lever_rule(FEED, *endpoints)
        with self.assertRaises(ValueError):
            lever_rule(mixed, endpoints[0], endpoints[0])

    def test_reference_does_not_extrapolate(self):
        pairs = np.asarray(
            load(ROOT / "cases/crossflow_extraction/data/interpolation_protocol.json")[
                "pairs_by_temperature"
            ]["303.15"]
        )
        for method in ["linear", "pchip"]:
            with self.assertRaises(ValueError):
                experimental_split(pairs, np.array([1.0, 0.0, 0.0]), method)

    def test_recorded_backend_rejects_unavailable_state(self):
        rows = load(ROOT / "cases/crossflow_extraction/data/cascade_stages.json")
        split = RecordedEndpoints(rows, "ThermoFormer", 303.15)
        with self.assertRaises(ValueError):
            split(np.array([1.0, 0.0, 0.0]))
        with self.assertRaises(ValueError):
            cascade([-0.5], split)

    def test_complete_paper_reproduction(self):
        verify_manifest()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self.assertEqual(binary_case(output)["reflux_calculations"], 234)
            self.assertEqual(column_case(output)["stage_states"], 548)
            self.assertEqual(extraction_case(output)["allocation_cases"], 66)


if __name__ == "__main__":
    unittest.main()
