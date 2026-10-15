"""Design decisions and auditable, explicitly preliminary separation results."""

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

SeparationMethod = Literal[
    "flash",
    "distillation",
    "extractive_distillation",
    "liquid_extraction",
    "pressure_swing",
    "adsorption",
    "membrane",
]


class SeparationCapability(BaseModel):
    method: SeparationMethod
    label: str
    availability: Literal["design_loop", "legacy_specialized", "not_implemented"]
    limitation: str


class DesignCheck(BaseModel):
    name: str
    status: Literal["passed", "failed", "unverified"]
    message: str


class DesignAttempt(BaseModel):
    attempt_id: str = Field(default_factory=lambda: str(uuid4()))
    method: SeparationMethod
    status: Literal["screened_out", "constraint_failed", "preliminary", "failed"]
    reason: str
    failure_type: str | None = None
    recovery_action: str | None = None
    metrics: dict[str, float] = Field(default_factory=dict)
    checks: list[DesignCheck] = Field(default_factory=list)
    evidence_run_ids: list[str] = Field(default_factory=list)


class DesignDecision(BaseModel):
    action: str
    reason: str
    attempt_id: str | None = None


class SeparationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["preliminary", "needs_input", "blocked", "budget_exhausted"]
    stop_reason: str
    selected_attempt_id: str | None = None
    attempts: list[DesignAttempt] = Field(default_factory=list)
    decisions: list[DesignDecision] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    capabilities: list[SeparationCapability] = Field(default_factory=list)
    input_snapshot: dict[str, Any] = Field(default_factory=dict)
    calculation_snapshots: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
