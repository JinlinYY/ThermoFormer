"""Select only eligible actions; provider suggestions never supply tool arguments."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from agent.providers import LLMProviderError, LLMProviderOutputError
from schemas.evidence import ActionCandidate, EvidenceState


@runtime_checkable
class ActionSelector(Protocol):
    async def select_action(self, state: EvidenceState, candidates: list[ActionCandidate]) -> str: ...


class DecisionPolicy:
    def __init__(self, provider: object) -> None:
        self.provider = provider

    async def choose(self, state: EvidenceState, candidates: list[ActionCandidate]) -> tuple[ActionCandidate, str]:
        if not candidates:
            raise ValueError("No eligible action")
        ranked = sorted(candidates, key=lambda action: (-action.priority, action.estimated_cost, action.action_id))
        if isinstance(self.provider, ActionSelector) and len(ranked) > 1:
            try:
                selected = await self.provider.select_action(state.model_copy(deep=True), ranked)
                match = next((action for action in ranked if action.action_id == selected), None)
                if match is not None:
                    return match, "provider"
            except (LLMProviderError, LLMProviderOutputError, ValueError):
                pass
            return ranked[0], "fallback"
        return ranked[0], "rule"
