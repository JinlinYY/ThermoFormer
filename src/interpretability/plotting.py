"""Compatibility adapter for interpretability plotting."""
from .. import _compat
from ..thermoformer.interpretability import plotting as _implementation
_compat.export_module(globals(), _implementation)
