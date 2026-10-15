"""Transport contracts shared by the ggnn39 worker and the web API."""

from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

Case = Literal["binary", "extractive", "extraction"]
Mode = Literal["fixed", "rule", "llm", "rule_guided", "llm_guided"]


class PaperTask(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    task_id: str
    case: Case
    purity: float = Field(default=0.995, gt=0, lt=1)
    recovery: float = Field(default=0.98, gt=0, lt=1)
    retention: float = Field(default=0.80, gt=0, lt=1)
    feed_fraction: float = Field(default=0.466, gt=0, lt=1)
    temperature_K: float = Field(default=303.15, ge=298.15, le=303.15)
    solvent_total: float = Field(default=1.5, gt=0, le=3)
    max_stages: int = Field(default=13, ge=1, le=220)
    max_calls: int = Field(default=6, ge=1, le=12)
    max_reflux: float = Field(default=3, gt=0, le=60)
    margin: float = Field(default=0.0005, ge=0, le=0.05)

    @model_validator(mode="after")
    def check_case(self) -> PaperTask:
        if self.case == "binary" and self.purity <= self.feed_fraction:
            raise ValueError("Binary distillate purity must exceed the feed fraction.")
        if self.case == "extraction" and self.max_stages > 4:
            raise ValueError("The extraction pilot supports at most four stages.")
        if self.case == "extractive" and self.feed_fraction != 0.5:
            raise ValueError("The extractive pilot retains the equimolar paper feed.")
        return self


class Candidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action_id: str
    kind: Literal["evaluate", "verify", "accept", "defer", "stop"]
    description: str
    settings: dict[str, Any] = Field(default_factory=dict)


class ToolObservation(BaseModel):
    observation_id: str = Field(default_factory=lambda: str(uuid4()))
    status: Literal["valid", "failed"]
    metrics: dict[str, float] = Field(default_factory=dict)
    meets_targets: bool = False
    verified: bool = False
    numerical_checks: dict[str, Any] = Field(default_factory=dict)
    evidence_gaps: list[str] = Field(default_factory=list)
    failure: str | None = None
    data_origin: str
    details: dict[str, Any] = Field(default_factory=dict)


class ActionChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action_id: str
    reason: str = Field(max_length=1000)


class TraceEntry(BaseModel):
    index: int
    state: dict[str, Any]
    candidates: list[Candidate]
    choice: ActionChoice
    observation: ToolObservation | None = None
    elapsed_s: float


class PaperRun(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    task: PaperTask
    mode: Mode
    repeat: int = 0
    outcome: Literal["accepted", "deferred", "exhausted", "stopped", "provider_error"] = "stopped"
    calls: int = 0
    trace: list[TraceEntry] = Field(default_factory=list)
    final_observation: ToolObservation | None = None
    assessment: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    policy_error: str | None = None
    elapsed_s: float = 0


class PaperRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task: PaperTask
    mode: Mode = "rule"
    repeat: int = Field(default=0, ge=0, le=20)
