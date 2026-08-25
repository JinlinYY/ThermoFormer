"""Compatibility adapter for the C1 ablation report builder."""
from . import _compat
from .thermoformer.reporting import c1_ablation as _implementation
_compat.export_module(globals(), _implementation)
