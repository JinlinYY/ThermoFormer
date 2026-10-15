"""Auditable design loop. Only tools create numbers; choices contain action IDs."""

from __future__ import annotations

import time
from typing import Any

from paper_agent.contracts import Candidate, PaperRequest, PaperRun, PaperTask, ToolObservation, TraceEntry
from paper_agent.policy import LLMActionPolicy, ProviderFailure, choose_fixed, choose_rule
from thermo_engine.paper_tools import PaperThermodynamicBackend


def design_candidates(task: PaperTask) -> list[Candidate]:
    candidates = []
    if task.case == "binary":
        for reflux in (0.8, 0.928052, 1.15, 1.4, 1.8, 2.5):
            if reflux <= task.max_reflux:
                candidates.append(
                    Candidate(
                        action_id="reflux:" + str(reflux),
                        kind="evaluate",
                        description="McCabe-Thiele at bounded reflux; inspect stage requirement.",
                        settings={"reflux": reflux},
                    )
                )
    elif task.case == "extraction":
        for n in range(1, task.max_stages + 1):
            candidates.append(
                Candidate(
                    action_id="equal:" + str(n),
                    kind="evaluate",
                    description="Use equal fresh-solvent allocation over this many stages.",
                    settings={"allocation": [task.solvent_total / n] * n},
                )
            )
        if task.max_stages >= 2:
            for fractions in ([0.7, 0.3], [0.3, 0.7]):
                candidates.append(
                    Candidate(
                        action_id="split:" + str(fractions[0]),
                        kind="evaluate",
                        description="Redistribute the same solvent budget across two stages.",
                        settings={"allocation": [v * task.solvent_total for v in fractions]},
                    )
                )
    else:
        for n, reflux in ((160, 40), (180, 48), (183, 48), (200, 48), (183, 56), (200, 56)):
            if n <= task.max_stages and reflux <= task.max_reflux:
                candidates.append(
                    Candidate(
                        action_id="column:" + str(n) + ":" + str(reflux),
                        kind="evaluate",
                        description="Solve column at candidate stages/reflux; fixed paper solvent/feed family.",
                        settings={"stages": n, "reflux": reflux},
                    )
                )
    return candidates


def run_design(request: PaperRequest, backend: Any | None = None, policy: Any | None = None) -> PaperRun:
    start = time.monotonic()
    task = request.task
    engine = backend or PaperThermodynamicBackend(task)
    if request.mode in {"rule_guided", "llm_guided"}:
        from paper_agent.guided import run_guided

        return run_guided(request, engine, design_candidates(task), policy)
    result = PaperRun(task=task, mode=request.mode, repeat=request.repeat, provenance=engine.provenance())
    llm = policy or (LLMActionPolicy() if request.mode == "llm" else None)
    attempted: set[str] = set()
    verified_settings: set[str] = set()
    current_id = ""
    latest: ToolObservation | None = None
    # Terminal decisions do not consume numerical calls, but are separately bounded.
    for index in range(task.max_calls + 2):
        candidates = []
        if result.calls < task.max_calls:
            candidates = [c for c in design_candidates(task) if c.action_id not in attempted]
            if latest and latest.status == "valid" and not latest.verified and current_id not in verified_settings:
                candidates.append(
                    Candidate(
                        action_id="verify:" + current_id,
                        kind="verify",
                        description="Check current design with alternative interpolation or direct bubble refinement.",
                    )
                )
        if latest and latest.status == "valid" and latest.meets_targets:
            candidates.append(
                Candidate(
                    action_id="accept",
                    kind="accept",
                    description="Accept a preliminary candidate; unresolved evidence will remain explicitly flagged.",
                )
            )
        candidates.extend(
            [
                Candidate(
                    action_id="defer",
                    kind="defer",
                    description="Withhold acceptance because available evidence is insufficient.",
                ),
                Candidate(
                    action_id="stop",
                    kind="stop",
                    description="Stop with no accepted design; do not infer global infeasibility.",
                ),
            ]
        )
        state = {
            "task": task.model_dump(),
            "remaining_calls": task.max_calls - result.calls,
            "latest": None if latest is None else latest.model_dump(exclude={"details"}),
            "history": [
                {
                    "action": entry.choice.action_id,
                    "observation": entry.observation.model_dump(exclude={"details"}) if entry.observation else None,
                }
                for entry in result.trace
            ],
        }
        tick = time.monotonic()
        try:
            if request.mode == "llm":
                assert llm is not None
                choice = llm.choose(state, candidates)
            elif request.mode == "rule":
                choice = choose_rule(state, candidates)
            else:
                choice = choose_fixed(state, candidates)
            selected = next((c for c in candidates if c.action_id == choice.action_id), None)
            if selected is None:
                raise ProviderFailure("Action not in allowlist")
        except ProviderFailure as exc:
            result.outcome = "provider_error"
            result.policy_error = str(exc)
            break
        observation = None
        if selected.kind in {"evaluate", "verify"}:
            result.calls += 1
            if selected.kind == "evaluate":
                attempted.add(selected.action_id)
                current_id = selected.action_id
            else:
                verified_settings.add(current_id)
            observation = engine.execute(selected)
            latest = observation
            result.final_observation = observation
        else:
            if selected.kind == "accept":
                result.outcome = "accepted"
            elif selected.kind == "defer":
                result.outcome = "deferred"
            else:
                result.outcome = "stopped"
            if selected.kind == "stop" and result.calls >= task.max_calls:
                result.outcome = "exhausted"
        result.trace.append(
            TraceEntry(
                index=index,
                state=state,
                candidates=candidates,
                choice=choice,
                observation=observation,
                elapsed_s=time.monotonic() - tick,
            )
        )
        if observation is None:
            break
    result.assessment = engine.assess(result.final_observation)
    result.assessment["accepted_with_unresolved_evidence"] = bool(
        result.outcome == "accepted" and latest and (not latest.verified or latest.evidence_gaps)
    )
    reference_meets = result.assessment.get("reference_meets_targets")
    result.assessment["false_acceptance_against_reference"] = (
        result.outcome == "accepted" and not reference_meets if reference_meets is not None else None
    )
    result.provenance.update(engine.provenance())
    if llm is not None:
        result.provenance["llm_calls"] = llm.calls
    result.elapsed_s = time.monotonic() - start
    return result
