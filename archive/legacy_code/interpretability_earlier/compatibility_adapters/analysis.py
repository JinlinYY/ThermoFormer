"""Compatibility adapter for interpretability analysis."""
from .. import _compat
from ..thermoformer.interpretability import analysis as _implementation
_compat.export_module(globals(), _implementation)
