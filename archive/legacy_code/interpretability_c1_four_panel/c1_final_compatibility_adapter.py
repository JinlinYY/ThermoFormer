"""Compatibility adapter for final-model interpretability."""
from .. import _compat
from ..thermoformer.interpretability import c1_final as _implementation
_compat.export_module(globals(), _implementation)
