"""Compatibility adapter for interpretability reports."""
from .. import _compat
from ..thermoformer.interpretability import reporting as _implementation
_compat.export_module(globals(), _implementation)
