"""Deterministic phase-equilibrium calculation package."""

from typing import Any


def __getattr__(name: str) -> Any:
    # Keep the independent Python 3.9 research worker importable without
    # importing the Python >=3.11 web application's domain schemas.
    if name in {"calculate_equilibrium", "validate_equilibrium_result"}:
        from thermo_engine import service

        return getattr(service, name)
    if name in {"design_extractive_distillation_column", "recommend_extraction_entrainer"}:
        from thermo_engine import column_design

        return getattr(column_design, name)
    raise AttributeError(name)


__all__ = [
    "calculate_equilibrium",
    "design_extractive_distillation_column",
    "recommend_extraction_entrainer",
    "validate_equilibrium_result",
]
