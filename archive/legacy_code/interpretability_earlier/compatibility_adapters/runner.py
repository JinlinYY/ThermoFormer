"""Compatibility adapter for interpretability execution."""
from .. import _compat
from ..thermoformer.interpretability import runner as _implementation
_compat.export_module(globals(), _implementation)
