"""Standalone numerical gate for the Python 3.9 paper backend.

This deliberately does not import the web domain. Diagnostics remain separate
from empirical accuracy or global phase stability certification.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def validate_equilibrium_result(
    compositions: Any,
    residual: float,
    *,
    tolerance: float = 1e-7,
    material_residual: float = 0,
    temperatures: Any | None = None,
) -> dict[str, Any]:
    vectors = np.asarray(compositions, dtype=float)
    normalized = bool(
        vectors.ndim == 2
        and vectors.size > 0
        and np.isfinite(vectors).all()
        and (vectors >= -1e-10).all()
        and (vectors <= 1 + 1e-10).all()
        and np.max(abs(vectors.sum(axis=1) - 1)) <= 1e-7
    )
    residual_ok = bool(np.isfinite(residual) and 0 <= residual <= tolerance)
    balance_ok = bool(np.isfinite(material_residual) and 0 <= material_residual <= 1e-7)
    temperature_ok = temperatures is None or bool(
        np.isfinite(temperatures).all() and (np.asarray(temperatures) > 0).all()
    )
    return dict(
        passed=normalized and residual_ok and balance_ok and temperature_ok,
        composition_passed=normalized,
        numerical_residual=residual,
        residual_tolerance=tolerance,
        material_residual=material_residual,
        temperature_passed=temperature_ok,
        global_stability="not_certified",
        empirical_accuracy="not_established_by_residuals",
    )
