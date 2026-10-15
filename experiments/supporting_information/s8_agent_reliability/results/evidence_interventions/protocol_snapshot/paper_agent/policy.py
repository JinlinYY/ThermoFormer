"""Three policies sharing the same actions, observations and hard acceptance gate."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx
from dotenv import load_dotenv

from paper_agent.contracts import ActionChoice, Candidate


class ProviderFailure(RuntimeError):
    pass


class LLMActionPolicy:
    def __init__(self) -> None:
        load_dotenv()
        self.key = os.getenv("DEEPSEEK_API_KEY", "")
        self.base = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
        self.calls: list[dict[str, Any]] = []

    def choose(self, state: dict[str, Any], candidates: list[Candidate]) -> ActionChoice:
        if not self.key:
            raise ProviderFailure("DEEPSEEK_API_KEY is not configured; no rule fallback was substituted.")
        payload = {
            "model": self.model,
            "temperature": 0,
            "thinking": {"type": "disabled"},
            "max_tokens": 768,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Select one supplied action_id for a preliminary separation design. Never calculate or invent "
                        "thermodynamic values. Preserve goals and budgets. Decide whether to improve a design, verify "
                        "its numerical evidence, accept, or defer. Verification does not create independent "
                        "experimental support. Avoid accepting unresolved evidence gaps; stop when tools cannot repair "
                        "them. Return exactly JSON {action_id: string, reason: short decision justification}. "
                        "Do not provide hidden reasoning, fabricated tool results or additional fields."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps({"state": state, "actions": [c.model_dump() for c in candidates]}),
                },
            ],
        }
        try:
            with httpx.Client(timeout=45) as client:
                response = client.post(
                    self.base + "/chat/completions", json=payload, headers={"Authorization": "Bearer " + self.key}
                )
            if response.status_code != 200:
                raise ProviderFailure("LLM request failed with HTTP " + str(response.status_code))
            data = response.json()
            self.calls.append(
                {
                    "model": data.get("model", self.model),
                    "usage": data.get("usage", {}),
                    "response_id": data.get("id"),
                    "thinking": "disabled",
                    "max_tokens": 768,
                    "finish_reason": data["choices"][0].get("finish_reason"),
                }
            )
            if data["choices"][0].get("finish_reason") != "stop":
                raise ProviderFailure("LLM output did not finish normally")
            choice = ActionChoice.model_validate_json(data["choices"][0]["message"]["content"])
        except (httpx.HTTPError, ValueError, KeyError, IndexError) as exc:
            raise ProviderFailure("LLM transport or structured output failure: " + type(exc).__name__) from None
        if choice.action_id not in {c.action_id for c in candidates}:
            raise ProviderFailure("LLM selected an action outside the supplied allowlist")
        return choice


def choose_fixed(state: dict[str, Any], candidates: list[Candidate]) -> ActionChoice:
    del state
    accepted = next((c for c in candidates if c.kind == "accept"), None)
    selected = accepted or next((c for c in candidates if c.kind == "evaluate"), candidates[-1])
    assert selected is not None
    return ActionChoice(
        action_id=selected.action_id, reason="Fixed candidate order; accept first nominally passing design."
    )


def choose_rule(state: dict[str, Any], candidates: list[Candidate]) -> ActionChoice:
    latest = state.get("latest")
    if latest and latest["meets_targets"]:
        selected = next((c for c in candidates if c.kind == "verify"), None)
        if selected is None:
            kind = "defer" if latest["evidence_gaps"] else "accept"
            selected = next((c for c in candidates if c.kind == kind), candidates[-1])
        return ActionChoice(
            action_id=selected.action_id, reason="Check evidence before accepting nominal target satisfaction."
        )
    selected = next((c for c in candidates if c.kind == "evaluate"), candidates[-1])
    return ActionChoice(action_id=selected.action_id, reason="Try the next bounded candidate after target failure.")
