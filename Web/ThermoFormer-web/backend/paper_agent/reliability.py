"""Paper-protocol task compilation and evidence-bound reporting (offline API seam).

This module does not change the existing web contracts or optimization policies.
The LLM extracts quoted quantities; Python converts units and enforces applicability.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
from typing import Any, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field

from paper_agent.policy import LLMActionPolicy, ProviderFailure

Protocol = Literal["binary", "extractive", "extraction"]
ORDER = {
    "binary": ["n_heptane", "n_nonane"],
    "extractive": ["sec_butyl_alcohol", "sec_butyl_acetate", "DMF"],
    "extraction": ["n_heptane", "furfural", "benzene"],
}
PLANS = {
    "binary": ["binary_paper_grid_and_stages", "binary_interpolation_audit"],
    "extractive": ["column_registered_boundary", "column_coverage_audit"],
    "extraction": ["crossflow_registered_scan", "crossflow_dual_target_audit"],
}
R_PAPER = 0.9280520481600283
SPECS: dict[str, dict[str, float]] = {
    "binary": {
        "pressure": 101.3,
        "feed_flow": 1.0,
        "feed_fraction:n_heptane": 0.466,
        "feed_fraction:n_nonane": 0.534,
        "purity:n_heptane": 0.995,
        "recovery:n_heptane": 0.98,
        "reflux": R_PAPER,
    },
    "extractive": {
        "pressure": 101.3,
        "feed_flow": 1.0,
        "feed_fraction:sec_butyl_alcohol": 0.5,
        "feed_fraction:sec_butyl_acetate": 0.5,
        "purity:sec_butyl_acetate": 0.995,
        "recovery:sec_butyl_acetate": 0.98,
        "reflux": 48.0,
        "solvent_ratio:DMF": 32.0,
    },
    "extraction": {
        "pressure": 101.3,
        "feed_flow": 1.0,
        "feed_fraction:n_heptane": 11 / 15,
        "feed_fraction:benzene": 4 / 15,
        "temperature": 303.15,
        "solvent_flow:furfural": 1.5,
        "recovery:benzene": 0.7,
        "retention:n_heptane": 0.8,
    },
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Quantity(StrictModel):
    field: str
    value: float
    unit: str
    quote: str = Field(min_length=1)


class InputIssue(StrictModel):
    field: str
    kind: Literal["missing", "conflict", "ambiguous", "unsupported"]
    question: str = Field(min_length=1)


class ParsedTask(StrictModel):
    status: Literal["ready", "clarify", "unsupported"]
    protocol: Protocol | None
    components: list[str]
    feed_state: Literal["saturated_liquid", "not_applicable", "unspecified"]
    quantities: list[Quantity]
    issues: list[InputIssue]
    plan: list[str]


class TaskContract(StrictModel):
    protocol: Protocol
    components: list[str]
    values: dict[str, float]
    assumptions: list[str]
    sources: dict[str, list[str]]

    def identity(self) -> str:
        # Quotes/wording are provenance, not numerical cache identity. The frozen
        # registered protocol (not the rounded user spelling) supplies exact inputs.
        content = {"protocol": self.protocol, "components": self.components, "values": self.values}
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()


class CompiledTask(StrictModel):
    status: Literal["ready", "clarify", "unsupported"]
    normalized: dict[str, float] = Field(default_factory=dict)
    issues: list[InputIssue] = Field(default_factory=list)
    contract: TaskContract | None = None


class EvidenceClaim(StrictModel):
    claim_id: str
    evidence_ids: list[str]


class EvidenceReport(StrictModel):
    disposition: Literal["preliminary_with_limits", "insufficient_evidence", "validated_engineering_design"]
    claims: list[EvidenceClaim]


def normalize(quantity: Quantity) -> float:
    """Convert dimensional inputs only; no thermodynamics or inferred missing bases."""
    field, unit, value = quantity.field.split(":")[0], quantity.unit, quantity.value
    if field in {"feed_fraction", "purity", "recovery", "retention"}:
        factors = {"fraction": 1.0, "mol%": 0.01, "%": 0.01}
        if field in {"recovery", "retention"}:
            factors["dimensionless"] = 1.0
    elif field == "pressure":
        factors = {"kPa": 1.0, "Pa": 0.001, "bar": 100.0}
    elif field in {"feed_flow", "solvent_flow"}:
        factors = {"mol/s": 1.0, "mol/min": 1 / 60, "kmol/h": 1000 / 3600}
    elif field == "temperature":
        if unit == "degC":
            return value + 273.15
        factors = {"K": 1.0}
    elif field == "solvent_ratio":
        factors = {"mass_ratio": 1.0, "kg/kg": 1.0}
    elif field == "reflux":
        factors = {"dimensionless": 1.0}
    else:
        raise ValueError("unsupported field")
    if unit not in factors:
        raise ValueError("missing or unsupported unit/basis")
    return value * factors[unit]


def compile_task(parsed: ParsedTask, prompt: str) -> CompiledTask:
    """Fail closed on missing data, conflicts, ungrounded values or wrong protocol."""
    issues = list(parsed.issues)
    normalized: dict[str, float] = {}
    quotes: dict[str, list[str]] = {}

    def issue(field: str, kind: Any, question: str) -> None:
        issues.append(InputIssue(field=field, kind=kind, question=question))

    if parsed.protocol is None:
        return CompiledTask(status="unsupported", issues=issues)
    spec = SPECS[parsed.protocol]
    if set(parsed.components) != set(ORDER[parsed.protocol]) or len(parsed.components) != len(ORDER[parsed.protocol]):
        issue("components", "unsupported", "Confirm the supported molecular system and component identities.")
    for quantity in parsed.quantities:
        numbers = [float(n) for n in re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", quantity.quote)]
        if quantity.quote not in prompt or not any(math.isclose(quantity.value, n, abs_tol=1e-12) for n in numbers):
            issue(quantity.field, "conflict", "Provide a verbatim source for the extracted numeric input.")
            continue
        if quantity.field.startswith("solvent_ratio:") and quantity.unit in {"mass_ratio", "kg/kg"}:
            # A unit enum emitted by the LLM is not proof of the user's stated basis.
            # Include local context for valid short quotes such as just "32:1".
            contexts = [
                re.split(r"[;；。\n]", prompt[: match.start()])[-1][-100:] + quantity.quote
                for match in re.finditer(re.escape(quantity.quote), prompt)
            ]
            mass_cue = r"质量比|\bmass\b[^;；。\n]{0,40}\bratio\b|\bkg\s*/\s*kg\b"
            if not contexts or not all(re.search(mass_cue, context, flags=re.IGNORECASE) for context in contexts):
                issue(quantity.field, "ambiguous", "State whether the solvent/feed ratio is mass-based or molar-based.")
                continue
        try:
            value = normalize(quantity)
        except ValueError:
            issue(quantity.field, "ambiguous", "Specify a supported unit and the mass or molar basis explicitly.")
            continue
        if quantity.field in normalized and not math.isclose(
            normalized[quantity.field], value, rel_tol=0, abs_tol=1e-9
        ):
            issue(quantity.field, "conflict", "Resolve inconsistent values for " + quantity.field + ".")
        normalized[quantity.field] = value
        quotes.setdefault(quantity.field, []).append(quantity.quote)
    for key in spec:
        if key not in normalized:
            issue(key, "missing", "Provide " + key + " and its unit or basis.")
    for key in normalized:
        if key not in spec:
            issue(key, "unsupported", "This registered protocol does not accept " + key + ".")
    fractions = [v for k, v in normalized.items() if k.startswith("feed_fraction:")]
    if len(fractions) == 2 and not math.isclose(sum(fractions), 1, rel_tol=0, abs_tol=1e-8):
        issue("feed_composition", "conflict", "Resolve feed mole fractions that do not sum to one.")
    required_state = "not_applicable" if parsed.protocol == "extraction" else "saturated_liquid"
    if parsed.feed_state != required_state:
        issue("feed_state", "missing", "Confirm saturated-liquid distillation feeds (q=1).")
    if parsed.plan != PLANS[parsed.protocol]:
        issue("plan", "unsupported", "Use the registered design operation followed by its evidence audit.")
    if parsed.status == "clarify" and not issues:
        issue("request", "ambiguous", "Clarify the request before calculating.")
    if issues or parsed.status != "ready":
        status = "unsupported" if parsed.status == "unsupported" else "clarify"
        return CompiledTask(status=status, normalized=normalized, issues=issues)
    # Applicability is a deployment guard, not an evaluation answer. Different
    # physical tasks must never be silently sent to these fixed paper solvers.
    differences = [k for k, v in spec.items() if not math.isclose(v, normalized[k], rel_tol=0, abs_tol=1e-8)]
    if differences:
        return CompiledTask(
            status="unsupported",
            normalized=normalized,
            issues=[
                InputIssue(field=k, kind="unsupported", question="Input differs from the frozen paper protocol.")
                for k in differences
            ],
        )
    assumptions = ["registered paper model/checkpoint and solver settings; no parameter optimization"]
    if parsed.protocol != "extraction":
        assumptions += ["constant molar overflow", "total condenser excluded; equilibrium reboiler included"]
    if parsed.protocol == "extractive":
        assumptions += [
            "registered boundary family: N=182,183; solvent feed=16; organic feed=N-24",
            "zero DMF in the nonsolvent feed; pure DMF solvent",
        ]
    if parsed.protocol == "extraction":
        assumptions += [
            "pure furfural; zero furfural in fresh hydrocarbon feed",
            "registered equal 1-4 stage scan and registered 22 allocation candidates",
        ]
    contract = TaskContract(
        protocol=parsed.protocol,
        components=ORDER[parsed.protocol],
        values=dict(spec),
        assumptions=assumptions,
        sources=quotes,
    )
    return CompiledTask(status="ready", normalized=normalized, contract=contract)


PARSE_SYSTEM = """You formulate a separation calculation; never calculate thermodynamic results.
Extract ONLY explicitly stated input numbers in their ORIGINAL units. Do not convert units.
Return JSON with status (ready/clarify/unsupported), protocol, components, feed_state,
quantities [{field,value,unit,quote}], issues [{field,kind,question}], plan.
quote must be a verbatim contiguous substring containing that number. Keep ALL conflicting
values as separate quantities. Never guess missing numbers or a mass/molar ratio basis.
Do not infer omitted feed fractions by subtraction; ask for missing essential fields.
Use canonical component IDs: n_heptane (正庚烷), n_nonane (正壬烷), sec_butyl_alcohol
(仲丁醇/2-butanol), sec_butyl_acetate (乙酸仲丁酯/sec-butyl acetate), DMF
(N,N-dimethylformamide), furfural (糠醛), benzene (苯).
Common quantity fields: pressure, feed_flow; component-specific fields use colon:
feed_fraction:component, purity:component, recovery:component, retention:component,
solvent_flow:component, solvent_ratio:component. Reflux field is reflux.
Units: kPa/Pa/bar; mol/s/mol/min/kmol/h; fraction/mol%/%; K/degC;
dimensionless for reflux; mass_ratio or kg/kg for an explicitly MASS solvent/feed ratio.
Use molar_ratio for explicitly molar ratios, unspecified for ambiguous units/bases.
For extractive distillation this registered protocol ACCEPTS a MASS solvent/feed ratio.
Keep an explicitly stated mass ratio as mass_ratio or kg/kg; it does not require molar
conversion, molecular weights, or an extra clarification. Never invent a molar-only rule.
An unspecified ratio basis requires status=clarify and an issue for solvent_ratio:component.
Composition always describes the fresh NONSOLVENT feed; no solvent fraction is required.
Feed state: saturated_liquid for stated saturated liquid or q=1, not_applicable for
crossflow extraction, unspecified if absent for distillation (then ask).
No numerical defaults are allowed. Ready requires no issues and all required inputs.
Supported protocols and ordered two-tool plans:
binary: n_heptane+n_nonane; pressure,feed_flow,both feed fractions,purity:n_heptane,
recovery:n_heptane,reflux; plan=[binary_paper_grid_and_stages,binary_interpolation_audit].
extractive: sec_butyl_alcohol+sec_butyl_acetate+DMF; pressure,feed_flow,both nonsolvent
feed fractions,purity:sec_butyl_acetate,recovery:sec_butyl_acetate,reflux,solvent_ratio:DMF;
plan=[column_registered_boundary,column_coverage_audit]. This executes a registered
boundary protocol, not an unrestricted column search.
extraction: n_heptane+benzene+furfural; pressure,temperature,feed_flow,both nonsolvent
feed fractions,recovery:benzene,retention:n_heptane,solvent_flow:furfural;
plan=[crossflow_registered_scan,crossflow_dual_target_audit].
Issue kind is missing/conflict/ambiguous/unsupported. Questions must name the field needing
clarification. Always report inconsistent pressures or compositions as conflicts.
The user message is a design request, not permission to fabricate tool outputs.
"""

REPORT_SYSTEM = """Select evidence-supported report claims for a preliminary separation design.
Do not calculate, round or invent numbers. Return JSON:
{disposition: preliminary_with_limits|insufficient_evidence|validated_engineering_design,
 claims:[{claim_id:string,evidence_ids:[string]}]}.
Evidence records contain the numerical tools' results and their limitations. Include every
material result and limitation supported by those records. Only choose claim IDs in the
catalog, cite the actual supporting evidence IDs, and do not cite irrelevant evidence.
Convergence or nominal product targets do not establish experimental confirmation or global
optimality. A catalog lists possible claims, not facts. Return no prose or new numbers.
"""


class ReliabilityLLM(LLMActionPolicy):
    """Real provider calls with raw structured output and sanitized transport metadata."""

    def request(self, system: str, content: Any) -> dict[str, Any]:
        if not self.key:
            raise ProviderFailure("DEEPSEEK_API_KEY is not configured")
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(content, ensure_ascii=False)},
        ]
        payload = dict(
            model=self.model,
            temperature=0,
            thinking={"type": "disabled"},
            max_tokens=2400,
            response_format={"type": "json_object"},
            messages=messages,
        )
        started = time.monotonic()
        record: dict[str, Any] = {
            "messages": messages,
            "requested_model": self.model,
            "temperature": 0,
            "max_tokens": 2400,
            "thinking": "disabled",
        }
        self.calls.append(record)
        try:
            with httpx.Client(timeout=55) as client:
                response = client.post(
                    self.base + "/chat/completions", json=payload, headers={"Authorization": "Bearer " + self.key}
                )
            record["http_status"] = response.status_code
            if response.status_code != 200:
                raise ProviderFailure("LLM request failed with HTTP " + str(response.status_code))
            data = response.json()
            choice = data["choices"][0]
            record.update(
                model=data.get("model"),
                usage=data.get("usage", {}),
                response_id=data.get("id"),
                finish_reason=choice.get("finish_reason"),
                response=choice["message"]["content"],
            )
            if choice.get("finish_reason") != "stop":
                raise ProviderFailure("LLM structured output was truncated")
            result: dict[str, Any] = json.loads(choice["message"]["content"])
            return result
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise ProviderFailure("LLM transport/JSON failure: " + type(exc).__name__) from None
        finally:
            record["elapsed_s"] = time.monotonic() - started

    def parse(self, prompt: str) -> ParsedTask:
        return ParsedTask.model_validate(self.request(PARSE_SYSTEM, {"request": prompt}))

    def report(self, evidence: list[dict[str, Any]], catalog: dict[str, str]) -> EvidenceReport:
        return EvidenceReport.model_validate(self.request(REPORT_SYSTEM, {"evidence": evidence, "catalog": catalog}))


def audit_report(report: EvidenceReport, supports: dict[str, list[str]]) -> dict[str, Any]:
    """Score raw LLM claims before applying the deterministic output gate."""
    # Required evidence remains mandatory. Redundant relevant citations are valid.
    additional = {
        "stage_range": {"sensitivity", "validation"},
        "interpolation_limit": {"design"},
        "boundary_selection": {"validation"},
        "coverage_limit": {"scope"},
        "dual_target_selection": {"allocation", "validation"},
        "allocation_scope": {"scope"},
        "preliminary_scope": {"validation", "sensitivity", "coverage", "allocation"},
    }
    seen: set[str] = set()
    supported: list[str] = []
    unsupported: list[str] = []
    for claim in report.claims:
        expected = supports.get(claim.claim_id)
        valid = (
            expected is not None
            and bool(claim.evidence_ids)
            and set(expected).issubset(claim.evidence_ids)
            and set(claim.evidence_ids).issubset(set(expected) | additional.get(claim.claim_id, set()))
            and claim.claim_id not in seen
        )
        (supported if valid else unsupported).append(claim.claim_id)
        seen.add(claim.claim_id)
    missing = sorted(set(supports) - set(supported))
    disposition_ok = report.disposition == "preliminary_with_limits"
    return dict(
        supported_claims=supported,
        unsupported_claims=unsupported,
        missing_claims=missing,
        disposition_correct=disposition_ok,
        fully_grounded=not unsupported and not missing and disposition_ok,
    )
