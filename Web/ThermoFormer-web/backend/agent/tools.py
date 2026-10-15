"""Constrained engineering-tool registry inspired by CAi's modular tool catalog."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from agent.executor import TaskExecution, calculate_task
from schemas.domain import FailureType, TaskManifest
from thermo_engine.errors import ThermoEquiError

ToolHandler = Callable[[TaskManifest], TaskExecution]


@dataclass(frozen=True)
class EngineeringTool:
    name: str
    description: str
    handler: ToolHandler


class EngineeringToolRegistry:
    """Allow the orchestrator to invoke only explicitly registered domain tools."""

    def __init__(self, tools: tuple[EngineeringTool, ...]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def catalog(self) -> list[dict[str, str]]:
        return [{"name": tool.name, "description": tool.description} for tool in self._tools.values()]

    def execute(self, name: str, task: TaskManifest) -> TaskExecution:
        tool = self._tools.get(name)
        if tool is None:
            raise ThermoEquiError(
                FailureType.UNSUPPORTED_MODEL,
                f"Engineering tool {name!r} is not registered.",
                "Choose a reviewed tool from the engineering tool registry.",
            )
        return tool.handler(task)


DEFAULT_TOOL_REGISTRY = EngineeringToolRegistry(
    (
        EngineeringTool(
            name="phase_equilibrium",
            description=(
                "Execute a structured non-electrolyte phase-equilibrium task through a deterministic "
                "backend and independent validation gate."
            ),
            handler=calculate_task,
        ),
    )
)

# Capability names used by the evidence loop. The numerical capability delegates
# to the existing allowlisted registry; none exposes shell or arbitrary Python.
EVIDENCE_TOOL_CATALOG: dict[str, str] = {
    "lookup_parameters": "Look up exact model/component/condition parameter records.",
    "check_applicability": "Filter models using the deterministic applicability rules.",
    "recall_experience": "Recall condition-bound observations, not scientific facts.",
    "calculate": "Execute a preconstructed task through phase_equilibrium.",
    "validate": "Run independent physical checks on the tool result.",
    "diagnose": "Describe observed failures without inventing root causes.",
    "clarify": "Return the missing input fields and suspend execution.",
    "respond": "Return conclusions bound to evidence and unresolved limitations.",
    "stop": "Stop without manufacturing a result.",
}
