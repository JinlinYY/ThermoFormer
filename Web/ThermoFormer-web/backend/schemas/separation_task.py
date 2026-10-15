"""Explicit design objectives; no implicit substitution of a property model."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from schemas.domain import TaskManifest
from schemas.separation import SeparationMethod


def _default_methods() -> list[SeparationMethod]:
    return ["flash", "distillation"]


class SeparationDesignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    task: TaskManifest
    target_purity: float = Field(gt=0, lt=1)
    target_recovery: float = Field(gt=0, lt=1)
    feed_flow_mol_s: float = Field(default=1.0, gt=0)
    methods: list[SeparationMethod] = Field(default_factory=_default_methods, min_length=1)
    reflux_factors: list[float] = Field(default_factory=lambda: [1.2, 1.4, 2.0, 3.0], min_length=1, max_length=8)
    max_stages: int | None = Field(default=None, ge=3)
    max_reflux_ratio: float | None = Field(default=None, gt=0)
    max_attempts: int = Field(default=5, ge=1, le=10)

    @model_validator(mode="after")
    def validate_design(self) -> "SeparationDesignRequest":
        if len(self.task.components) != 2:
            raise ValueError("The current design loop requires exactly two feed components.")
        if self.task.composition_basis != "mole_fraction":
            raise ValueError("Convert feed composition to reviewed mole fractions first.")
        if not self.task.model_name:
            raise ValueError("An explicit thermodynamic model is required for design.")
        if self.task.equilibrium_type not in {"VLE", "FLASH"}:
            raise ValueError("The current design loop requires a VLE/FLASH task.")
        z = self.task.conditions.feed_composition
        if z is None or len(z) != 2 or not all(0 < v < 1 for v in z):
            raise ValueError("Provide two nonzero feed mole fractions.")
        if self.task.conditions.pressure_kPa is None:
            raise ValueError("Operating pressure is required.")
        if any(not 1 < factor <= 10 for factor in self.reflux_factors):
            raise ValueError("Reflux factors must be finite and in (1, 10].")
        if len(set(self.methods)) != len(self.methods):
            raise ValueError("Duplicate methods are not allowed.")
        if any(p.source_type == "test_fixture" for p in self.task.parameters):
            raise ValueError("Test fixture parameters are not engineering inputs.")
        return self
