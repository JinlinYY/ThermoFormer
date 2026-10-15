"""Bounded evidence-driven scientific agent built on the existing LangGraph runtime."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict, cast

from langgraph.graph import END, START, StateGraph

from agent.decision_policy import DecisionPolicy
from agent.diagnostics import diagnose_failure, missing_conditions, validation_evidence
from agent.executor import TaskExecution, validate_task_execution
from agent.experience import ExperienceStore, task_fingerprint
from agent.router import rank_executable_models
from agent.tools import EngineeringToolRegistry
from schemas.domain import (
    AgentStep, CalculationEnvelope, EvidenceStatement, FailureDetail, FailureType, ParameterSet, TaskManifest,
)
from schemas.evidence import (
    ActionCandidate, ActionKind, ActionRecord, EvidenceGap, EvidenceItem, EvidenceSource, EvidenceState, StopReason,
)
from thermo_engine.errors import ThermoEquiError
from thermo_engine.parameter_store import load_production_parameter_sets
from thermo_engine.registry import DEFAULT_BACKEND_REGISTRY


@dataclass
class WorkflowOutcome:
    task: TaskManifest
    state: EvidenceState
    envelope: CalculationEnvelope | None
    statements: list[EvidenceStatement]
    steps: list[AgentStep]
    failure: FailureDetail | None = None


@dataclass
class _Frame:
    message: str
    session: str
    task: TaskManifest
    evidence: EvidenceState
    explicit_model: bool
    selected: ActionCandidate | None = None
    selection: str = "rule"
    models: list[str] = field(default_factory=list)
    execution: TaskExecution | None = None
    envelope: CalculationEnvelope | None = None
    failure: FailureDetail | None = None
    needs_diagnosis: bool = False
    done: bool = False


class _GraphState(TypedDict):
    frame: _Frame


def _parameter_matches(parameter: ParameterSet, task: TaskManifest) -> bool:
    if parameter.source_type in {"test_fixture", "unknown", "estimated"}:
        return False
    if task.model_name and parameter.model_name.casefold() != task.model_name.casefold():
        return False
    if task.equilibrium_type not in parameter.equilibrium_types:
        return False
    identities = [{c.name.casefold(), c.component_id.casefold(), (c.cas_number or "").casefold(),
                   *(alias.casefold() for alias in c.aliases)} for c in task.components]
    if len(parameter.component_order) != len(identities):
        return False
    if not all(name.casefold() in identities[i] for i, name in enumerate(parameter.component_order)):
        return False
    for value, bounds in ((task.conditions.temperature_K, parameter.temperature_range_K),
                          (task.conditions.pressure_kPa, parameter.pressure_range_kPa)):
        if value is not None and bounds is not None and not bounds[0] <= value <= bounds[1]:
            return False
    if task.conditions.temperature_span_K and parameter.temperature_range_K:
        if not (parameter.temperature_range_K[0] <= task.conditions.temperature_span_K[0]
                and task.conditions.temperature_span_K[1] <= parameter.temperature_range_K[1]):
            return False
    return True


class EvidenceAgentGraph:
    def __init__(self, provider: object, tools: EngineeringToolRegistry, *,
                 memory: ExperienceStore | None = None, max_actions: int = 12, max_calculations: int = 3) -> None:
        self.policy = DecisionPolicy(provider)
        self.tools = tools
        self.memory = memory or ExperienceStore()
        self.max_actions = max_actions
        self.max_calculations = max_calculations
        builder = StateGraph(_GraphState)
        builder.add_node("decide", self._decide)
        builder.add_node("act", self._act)
        builder.add_edge(START, "decide")
        builder.add_edge("decide", "act")
        builder.add_conditional_edges("act", lambda state: "end" if state["frame"].done else "continue",
                                      {"end": END, "continue": "decide"})
        self._graph: Any = builder.compile()

    @staticmethod
    def _did(frame: _Frame, kind: ActionKind) -> bool:
        return any(action.kind == kind for action in frame.evidence.actions)

    def _candidates(self, frame: _Frame) -> list[ActionCandidate]:
        def action(kind: ActionKind, reason: str, priority: float = 0, model: str | None = None) -> ActionCandidate:
            return ActionCandidate(action_id=f"{kind}:{model or 'task'}", kind=kind, reason=reason,
                                   model_name=model, priority=priority)

        state = frame.evidence
        # A calculation reserves its mandatory validation slot; even failures
        # during later reasoning never expose an unvalidated raw result.
        if frame.execution is not None:
            return [action("validate", "计算结果必须先经过独立校验。")]
        if frame.done:
            return [action("stop", "任务已经结束。")]
        if state.actions_used >= state.max_actions:
            return [action("stop", "行动预算已耗尽。")]
        missing = missing_conditions(frame.task)
        if missing:
            return [action("clarify", "必要输入缺失，需先补充。")]
        if frame.needs_diagnosis:
            return [action("diagnose", "根据可观测的失败和校验结果进行诊断。")]
        if frame.envelope is not None and frame.envelope.validation.overall_status != "failed":
            return [action("respond", "输出已经校验的结果，同时保留未验证项和警告。")]
        if frame.failure is not None:
            diagnostics = state.diagnostics
            if diagnostics and not diagnostics[-1].recoverable:
                return [action("stop", "当前失败不能由现有工具安全恢复。")]
        if not self._did(frame, "lookup_parameters"):
            return [action("lookup_parameters", "仅从结构化参数记录补充适用数据。")]
        if not self._did(frame, "check_applicability"):
            return [action("check_applicability", "在执行前筛选模型与任务适用性。")]
        if not self._did(frame, "recall_experience"):
            return [action("recall_experience", "查询相同会话、输入与参数版本下的历史执行经验。")]
        attempted = {a.model_name for a in state.actions if a.kind == "calculate"}
        candidates = []
        if state.calculations_used < state.max_calculations and state.actions_used + 2 <= state.max_actions:
            for i, model in enumerate(frame.models):
                if model not in attempted:
                    candidates.append(action("calculate", "执行适用候选；模型变化将记录在轨迹与输入快照中。",
                                             20.0 - i, model))
        return candidates or [action("stop", "没有未尝试且可执行的安全行动。")]

    async def _decide(self, state: _GraphState) -> _GraphState:
        frame = state["frame"]
        frame.selected, frame.selection = await self.policy.choose(frame.evidence, self._candidates(frame))
        return state

    @staticmethod
    def _finish(frame: _Frame, reason: StopReason) -> None:
        frame.evidence.stop_reason = reason
        frame.evidence.status = "completed" if reason == "evidence_sufficient" else "warning" if (
            frame.envelope is not None and frame.envelope.validation.overall_status != "failed"
        ) else "blocked"
        frame.done = True

    def _lookup_parameters(self, frame: _Frame) -> str:
        supplied = list(frame.task.parameters)
        if any(p.source_type == "test_fixture" for p in supplied):
            raise ThermoEquiError(FailureType.MISSING_PARAMETERS, "Test fixtures cannot enter an engineering run.",
                                 "Import reviewed production parameters.")
        # User-supplied records are not silently replaced. Their form and domain
        # are checked by the engine; automatically retrieved records are filtered.
        additions = [] if supplied else [p for p in load_production_parameter_sets() if _parameter_matches(p, frame.task)]
        frame.task = frame.task.model_copy(update={"parameters": supplied + additions})
        for parameter in frame.task.parameters:
            valid = _parameter_matches(parameter, frame.task)
            frame.evidence.evidence.append(EvidenceItem(
                evidence_id=f"parameter:{parameter.parameter_set_id}", claim=f"参数记录：{parameter.model_name}；{parameter.parameter_form}",
                status="supported" if valid else "unverified", scope="Parameter metadata; backend must verify equation form and units.",
                source=EvidenceSource(source_id=parameter.parameter_set_id, title=parameter.source_title or "User-supplied parameter",
                                      uri=parameter.source_identifier or f"parameter:{parameter.parameter_set_id}",
                                      source_kind="parameter", reviewed=parameter.source_type in {"literature", "database"}),
            ))
        return f"找到 {len(additions)} 条满足组分方向、任务类型与已知工况的参数记录；保留用户输入。"

    @staticmethod
    def _check_applicability(frame: _Frame) -> str:
        if frame.explicit_model:
            DEFAULT_BACKEND_REGISTRY.resolve(frame.task)
            frame.models = [cast(str, frame.task.model_name)]
        elif frame.task.equilibrium_type == "LLE":
            # Preserve the explicit LLE contract rather than implicitly upgrading scope.
            DEFAULT_BACKEND_REGISTRY.route_task(frame.task)
        else:
            frame.models = [item.model_name for item in rank_executable_models(frame.task)]
        if not frame.models:
            raise ThermoEquiError(FailureType.MISSING_PARAMETERS, "No executable model has the required reviewed parameters.",
                                 "Supply a supported model and applicable evidence-bearing parameters.")
        return "可执行模型候选：" + ", ".join(frame.models)

    async def _act(self, state: _GraphState) -> _GraphState:
        frame = state["frame"]
        selected = frame.selected
        assert selected is not None
        kind = selected.kind
        start = time.monotonic()
        evidence_start = len(frame.evidence.evidence)
        status: Literal["completed", "failed", "blocked"] = "completed"
        summary = selected.reason
        failure_type: str | None = None
        run_id: str | None = None
        try:
            if kind == "clarify":
                missing = missing_conditions(frame.task)
                frame.evidence.clarification = missing
                frame.evidence.gaps = [EvidenceGap(code="missing_input", description=name, suggested_actions=["clarify"]) for name in missing]
                summary = "需要补充：" + ", ".join(missing)
                self._finish(frame, "needs_input")
                status = "blocked"
            elif kind == "lookup_parameters":
                summary = self._lookup_parameters(frame)
            elif kind == "check_applicability":
                summary = self._check_applicability(frame)
            elif kind == "recall_experience":
                memories = self.memory.recall(frame.session, frame.evidence.task_fingerprint)
                frame.evidence.experience_ids = [identifier for identifier, _ in memories]
                # Experience is advisory only; always rerun calculation and validation.
                summary = f"找到 {len(memories)} 条同条件执行经验；历史结果不替代当前验证。"
            elif kind == "calculate":
                frame.evidence.calculations_used += 1
                task = frame.task.model_copy(deep=True, update={"model_name": selected.model_name})
                if not frame.explicit_model:
                    task.assumptions.append(f"Evidence agent selected {selected.model_name}; see action trace for prior attempts.")
                frame.execution = self.tools.execute("phase_equilibrium", task)
                frame.failure = None
                run_id = frame.execution.result.run_id
                summary = "求解结束，原始结果尚未作为已验证结论发布。"
            elif kind == "validate":
                assert frame.execution is not None
                envelope = validate_task_execution(frame.execution)
                frame.envelope = envelope
                frame.task = frame.execution.task
                frame.execution = None
                run_id = envelope.result.run_id
                items, gaps = validation_evidence(envelope)
                frame.evidence.evidence.extend(items)
                frame.evidence.gaps = gaps
                summary = f"独立校验：{envelope.validation.overall_status}；未执行的检查保持未验证。"
                if envelope.validation.overall_status == "failed":
                    status = "failed"
                    frame.failure = FailureDetail(failure_type=FailureType.PHYSICAL_VALIDATION_FAILURE,
                        message="Physical validation failed; solver convergence is not sufficient.",
                        recovery_action="Review validation observations and model applicability.")
                    frame.needs_diagnosis = True
            elif kind == "diagnose":
                assert frame.failure is not None
                diagnostic = diagnose_failure(frame.failure, explicit_model=frame.explicit_model)
                frame.evidence.diagnostics.append(diagnostic)
                frame.needs_diagnosis = False
                frame.evidence.gaps.append(EvidenceGap(code=diagnostic.code, description=diagnostic.observation,
                                                       suggested_actions=diagnostic.suggested_actions))
                summary = diagnostic.observation + ("；根因尚未确定。" if not diagnostic.cause_confirmed else "")
            elif kind == "respond":
                required_gaps = [gap for gap in frame.evidence.gaps if gap.required]
                reason: StopReason = "evidence_incomplete" if required_gaps or (
                    frame.envelope and frame.envelope.validation.overall_status == "warning"
                ) else "evidence_sufficient"
                self._finish(frame, reason)
            elif kind == "stop":
                reason = "no_safe_action"
                if frame.evidence.actions_used >= frame.evidence.max_actions or (
                    frame.evidence.calculations_used >= frame.evidence.max_calculations
                ):
                    reason = "budget_exhausted"
                elif frame.failure:
                    reason = {FailureType.MISSING_PARAMETERS: "missing_parameters",
                              FailureType.UNSUPPORTED_MODEL: "unsupported",
                              FailureType.PHYSICAL_VALIDATION_FAILURE: "validation_failed"}.get(
                                  frame.failure.failure_type, "no_safe_action")
                self._finish(frame, cast(StopReason, reason))
                status = "blocked"
        except ThermoEquiError as error:
            frame.failure = error.detail
            frame.execution = None
            frame.needs_diagnosis = True
            status = "failed"
            failure_type = error.detail.failure_type.value
            summary = error.detail.message
        except (OSError, ValueError, RuntimeError) as error:
            # No raw provider/network exception or secret-bearing repr in public traces.
            frame.execution = None
            frame.failure = FailureDetail(failure_type=FailureType.MISSING_DATA,
                message=f"{kind} unavailable ({type(error).__name__}).", recovery_action="Check the configured tool and data source.")
            frame.needs_diagnosis = True
            status = "failed"
            failure_type = frame.failure.failure_type.value
            summary = frame.failure.message
        if kind != "stop" or frame.evidence.actions_used < frame.evidence.max_actions:
            frame.evidence.actions_used += 1
        frame.evidence.actions.append(ActionRecord(
            sequence=len(frame.evidence.actions) + 1, action_id=selected.action_id, kind=kind,
            status=status, reason=selected.reason, summary=summary, model_name=selected.model_name, run_id=run_id,
            evidence_ids=[item.evidence_id for item in frame.evidence.evidence[evidence_start:]],
            failure_type=failure_type,
            selection=cast(Literal["rule", "provider", "learned", "fallback"], frame.selection),
            elapsed_ms=(time.monotonic() - start) * 1000,
        ))
        return state

    @staticmethod
    def _report(frame: _Frame) -> list[EvidenceStatement]:
        statements: list[EvidenceStatement] = []
        if frame.envelope is not None:
            run_id = frame.envelope.result.run_id
            valid = frame.envelope.validation.overall_status
            statements.append(EvidenceStatement(category="Calculation" if valid != "failed" else "Warning",
                text=f"模型 {frame.envelope.result.model_name} 的计算记录已保存；校验状态：{valid}。",
                evidence_ids=[f"{run_id}:convergence", f"{run_id}:equilibrium_residual"]))
        for gap in frame.evidence.gaps:
            statements.append(EvidenceStatement(category="Warning", text=gap.description,
                evidence_ids=[e.evidence_id for e in frame.evidence.evidence if e.field_path == f"validation.{gap.code}"]))
        if frame.failure:
            statements.append(EvidenceStatement(category="Warning", text=frame.failure.recovery_action))
        if frame.evidence.clarification:
            statements.append(EvidenceStatement(category="Warning", text="缺失必要计算条件：" + ", ".join(frame.evidence.clarification)))
        if not statements:
            statements.append(EvidenceStatement(category="Warning", text="证据不足，未生成数值结论。"))
        return statements

    async def run(self, message: str, task: TaskManifest, *, session: str = "") -> WorkflowOutcome:
        evidence = EvidenceState(task_fingerprint=task_fingerprint(task), max_actions=self.max_actions,
                                 max_calculations=self.max_calculations)
        frame = _Frame(message, session, task.model_copy(deep=True), evidence, task.model_name is not None)
        await self._graph.ainvoke({"frame": frame}, config={"recursion_limit": 2 * self.max_actions + 8})
        try:
            self.memory.save(session, frame.evidence)
        except (OSError, ValueError, RuntimeError):
            frame.evidence.diagnostics.append(diagnose_failure(FailureDetail(failure_type=FailureType.MISSING_DATA,
                message="Experience storage unavailable.", recovery_action="Check the experience database."), explicit_model=True))
        phases: list[Literal["plan", "execute", "validate", "respond"]] = ["plan", "execute", "validate", "respond"]
        steps = [AgentStep(phase=phase, status="completed", summary=summary, tool_name=tool)
                 for phase, summary, tool in zip(phases, [
                     "Evidence-driven action selection completed; detailed actions are attached.",
                     "Deterministic tools executed." if frame.envelope else "No validated calculation is available.",
                     f"Validation: {frame.envelope.validation.overall_status}." if frame.envelope else "No numerical result published.",
                     f"Stopped: {frame.evidence.stop_reason}.",
                 ], [None, "phase_equilibrium", "validate_equilibrium_result", None], strict=True)]
        if frame.envelope is None:
            steps[1].status = "blocked"
            steps[2].status = "blocked"
        elif frame.envelope.validation.overall_status == "failed":
            steps[2].status = "failed"
        return WorkflowOutcome(frame.task, frame.evidence, frame.envelope, self._report(frame), steps, frame.failure)
