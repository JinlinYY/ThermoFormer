"""Retain incumbents, rank resource proxies and require a bounded stopping certificate."""

from __future__ import annotations

import time
from typing import Any

from paper_agent.contracts import (
    ActionChoice,
    Candidate,
    PaperRequest,
    PaperRun,
    PaperTask,
    ToolObservation,
    TraceEntry,
)
from paper_agent.policy import LLMActionPolicy, ProviderFailure


def resource_key(task: PaperTask, candidate: Candidate) -> tuple[float, ...]:
    """Declared resource preferences, not predicted thermodynamic or monetary values."""
    if task.case == "binary":
        return (float(candidate.settings["reflux"]),)
    if task.case == "extraction":
        return (float(len(candidate.settings["allocation"])),)
    return (float(candidate.settings["stages"]), float(candidate.settings["reflux"]))


def supported(observation: ToolObservation) -> bool:
    return (
        observation.status == "valid"
        and observation.meets_targets
        and observation.verified
        and not observation.evidence_gaps
    )


def action_space(
    task: PaperTask, designs: list[Candidate], archive: dict[str, ToolObservation], verified: set[str], remaining: int
) -> tuple[list[Candidate], dict[str, Any], str | None]:
    ordered = sorted(designs, key=lambda c: resource_key(task, c))
    credible = [c for c in ordered if c.action_id in archive and supported(archive[c.action_id])]
    nominal = [
        c
        for c in ordered
        if c.action_id in archive and archive[c.action_id].status == "valid" and archive[c.action_id].meets_targets
    ]
    best = credible[0] if credible else (nominal[0] if nominal else None)
    pending = [c for c in ordered if c.action_id not in archive]
    if credible:
        pending = [c for c in pending if resource_key(task, c) < resource_key(task, credible[0])]
    verifiable = [
        c
        for c in nominal
        if c.action_id not in verified
        and not archive[c.action_id].verified
        and (not credible or resource_key(task, c) < resource_key(task, credible[0]))
    ]
    certificate = (
        "budget_exhausted"
        if remaining == 0
        else "resource_preference_resolved"
        if credible and not pending and not verifiable
        else "candidate_set_exhausted"
        if not pending and not verifiable
        else None
    )
    actions: list[Candidate] = []
    if remaining > 0:
        # Reserve the final tool call for an available feasible candidate's verification.
        if remaining > 1 or not verifiable:
            actions.extend(pending)
        actions.extend(
            Candidate(
                action_id="verify:" + c.action_id,
                kind="verify",
                description="Revisit this recorded candidate and verify it; preserve other incumbents.",
                settings=c.settings,
            )
            for c in verifiable
        )
    if certificate:
        if credible:
            actions.append(
                Candidate(action_id="accept", kind="accept", description="Accept the retained verified incumbent.")
            )
        elif nominal:
            actions.append(
                Candidate(
                    action_id="defer", kind="defer", description="Retain nominal design with unresolved evidence."
                )
            )
        else:
            actions.append(
                Candidate(
                    action_id="stop", kind="stop", description="No verified feasible incumbent; bounded search stopped."
                )
            )
    state = dict(
        resource_preference={
            "binary": "lower reflux among feasible verified candidates",
            "extractive": "fewer stages, then lower reflux (lexicographic)",
            "extraction": "fewer stages at fixed total solvent",
        }[task.case],
        resource_proxy_warning="Not energy or economic cost. Equal-resource alternatives are ties.",
        stopping_certificate=certificate,
        incumbent_id=best.action_id if best else None,
        remaining_quality_candidates=[c.action_id for c in pending],
        verification_reserved=remaining == 1 and bool(verifiable),
        ranked_candidates=[dict(action_id=c.action_id, resource_key=resource_key(task, c)) for c in ordered],
        archive={key: value.model_dump(exclude={"details"}) for key, value in archive.items()},
        guidance="Prefer low-resource candidates near observed feasibility boundaries. Failed validation cannot prove "
        "physical infeasibility or justify abandoning untried candidates. Use only listed actions.",
    )
    return actions, state, best.action_id if best else None


def run_guided(request: PaperRequest, engine: Any, designs: list[Candidate], policy: Any = None) -> PaperRun:
    start = time.monotonic()
    result = PaperRun(task=request.task, mode=request.mode, repeat=request.repeat, provenance=engine.provenance())
    llm = policy or (LLMActionPolicy() if request.mode == "llm_guided" else None)
    archive: dict[str, ToolObservation] = {}
    verified: set[str] = set()
    certificate = None
    for index in range(request.task.max_calls + 1):
        actions, diagnostics, incumbent = action_space(
            request.task, designs, archive, verified, request.task.max_calls - result.calls
        )
        state = dict(
            task=request.task.model_dump(), remaining_calls=request.task.max_calls - result.calls, **diagnostics
        )
        tick = time.monotonic()
        try:
            if llm is not None:
                choice = llm.choose(state, actions)
            else:
                preferred = next((c for c in actions if c.kind == "verify"), actions[0])
                choice = ActionChoice(
                    action_id=preferred.action_id,
                    reason="Resource-ranked search; reserve verification and require a stopping certificate.",
                )
            selected = next((c for c in actions if c.action_id == choice.action_id), None)
            if selected is None:
                raise ProviderFailure("Action not in guided allowlist")
        except ProviderFailure as exc:
            result.outcome, result.policy_error = "provider_error", str(exc)
            break
        observation = None
        if selected.kind in {"evaluate", "verify"}:
            result.calls += 1
            observation = engine.execute(selected)
            identity = selected.action_id.removeprefix("verify:") if selected.kind == "verify" else selected.action_id
            if selected.kind == "verify":
                verified.add(identity)
            archive[identity] = observation
        else:
            certificate = diagnostics["stopping_certificate"]
            result.final_observation = archive.get(incumbent) if incumbent else None
            if selected.kind == "accept":
                result.outcome = "accepted"
            elif selected.kind == "defer":
                result.outcome = "deferred"
            else:
                result.outcome = "exhausted" if result.calls == request.task.max_calls else "stopped"
        result.trace.append(
            TraceEntry(
                index=index,
                state=state,
                candidates=actions,
                choice=choice,
                observation=observation,
                elapsed_s=time.monotonic() - tick,
            )
        )
        if observation is None:
            break
    result.assessment = engine.assess(result.final_observation)
    result.assessment.update(
        stopping_certificate=certificate,
        accepted_with_unresolved_evidence=bool(
            result.outcome == "accepted" and result.final_observation and not supported(result.final_observation)
        ),
    )
    reference = result.assessment.get("reference_meets_targets")
    result.assessment["false_acceptance_against_reference"] = (
        (result.outcome == "accepted" and not reference) if reference is not None else None
    )
    result.provenance.update(engine.provenance())
    if llm is not None:
        result.provenance["llm_calls"] = llm.calls
    result.elapsed_s = time.monotonic() - start
    return result
