"""Public contracts for bounded scientific decisions and source-backed evidence."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ActionKind = Literal[
    "lookup_parameters", "check_applicability",
    "recall_experience", "calculate", "validate", "diagnose", "clarify", "respond", "stop",
]
EvidenceStatus = Literal["supported", "failed", "unverified", "not_applicable"]
StopReason = Literal[
    "evidence_sufficient", "needs_input", "missing_parameters", "unsupported",
    "budget_exhausted", "no_safe_action", "validation_failed", "evidence_incomplete",
]


class EvidenceSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str
    title: str
    uri: str
    locator: str = ""
    content_hash: str = ""
    source_kind: Literal["literature", "documentation", "parameter", "calculation", "validation", "experience"]
    reviewed: bool = False


class EvidenceItem(BaseModel):
    evidence_id: str
    claim: str
    status: EvidenceStatus
    source: EvidenceSource
    scope: str
    field_path: str | None = None


class EvidenceGap(BaseModel):
    code: str
    description: str
    required: bool = True
    suggested_actions: list[ActionKind] = Field(default_factory=list)


class Diagnostic(BaseModel):
    code: str
    observation: str
    cause: str = "unknown"
    cause_confirmed: bool = False
    recoverable: bool = False
    suggested_actions: list[ActionKind] = Field(default_factory=list)


class ActionCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action_id: str
    kind: ActionKind
    reason: str
    model_name: str | None = None
    estimated_cost: int = Field(default=1, ge=0)
    priority: float = 0.0


class ActionRecord(BaseModel):
    sequence: int
    action_id: str
    kind: ActionKind
    status: Literal["completed", "failed", "blocked"]
    reason: str
    summary: str
    model_name: str | None = None
    run_id: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    failure_type: str | None = None
    selection: Literal["rule", "provider", "learned", "fallback"] = "rule"
    elapsed_ms: float = Field(default=0.0, ge=0)


class EvidenceState(BaseModel):
    task_fingerprint: str
    status: Literal["running", "completed", "warning", "blocked"] = "running"
    stop_reason: StopReason | None = None
    max_actions: int = Field(default=12, ge=2, le=40)
    actions_used: int = Field(default=0, ge=0)
    max_calculations: int = Field(default=3, ge=1, le=5)
    calculations_used: int = Field(default=0, ge=0)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    gaps: list[EvidenceGap] = Field(default_factory=list)
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    actions: list[ActionRecord] = Field(default_factory=list)
    clarification: list[str] = Field(default_factory=list)
    experience_ids: list[str] = Field(default_factory=list)
