"""Fail-closed input/evidence boundaries; no synthetic thermodynamic observations."""

from __future__ import annotations

from typing import Any

import pytest
from paper_agent.reliability import (
    ORDER,
    PLANS,
    SPECS,
    EvidenceClaim,
    EvidenceReport,
    InputIssue,
    ParsedTask,
    Quantity,
    audit_report,
    compile_task,
    normalize,
)

from scripts.benchmarks.paper_agent.reliability_tasks import reliability_tasks


def specified() -> tuple[ParsedTask, str]:
    quantities = [
        Quantity(
            field=k,
            value=v,
            unit=(
                "fraction"
                if ":" in k
                else {"pressure": "kPa", "feed_flow": "mol/s", "reflux": "dimensionless"}[k]
            ),
            quote=f"{k}={v}",
        )
        for k, v in SPECS["binary"].items()
    ]
    prompt = "; ".join(q.quote for q in quantities)
    parsed = ParsedTask(
        status="ready",
        protocol="binary",
        components=ORDER["binary"],
        feed_state="saturated_liquid",
        quantities=quantities,
        issues=[],
        plan=PLANS["binary"],
    )
    return parsed, prompt


@pytest.mark.parametrize(
    "field,value,unit,expected",
    [
        ("pressure", 101300, "Pa", 101.3),
        ("pressure", 1.013, "bar", 101.3),
        ("feed_flow", 60, "mol/min", 1),
        ("feed_flow", 3.6, "kmol/h", 1),
        ("solvent_flow:furfural", 90, "mol/min", 1.5),
        ("temperature", 30, "degC", 303.15),
        ("purity:n_heptane", 99.5, "mol%", 0.995),
    ],
)
def test_unit_conversions(field: str, value: float, unit: str, expected: float) -> None:
    assert normalize(
        Quantity(field=field, value=value, unit=unit, quote=str(value))
    ) == pytest.approx(expected)


@pytest.mark.parametrize("unit", ["unspecified", "molar_ratio", "mol/mol"])
def test_solvent_mass_ratio_never_assumes_molar_basis(unit: str) -> None:
    with pytest.raises(ValueError):
        normalize(Quantity(field="solvent_ratio:DMF", value=32, unit=unit, quote="32"))


def test_missing_recovery_does_not_get_paper_default() -> None:
    parsed, prompt = specified()
    parsed.quantities = [q for q in parsed.quantities if q.field != "recovery:n_heptane"]
    result = compile_task(parsed, prompt)
    assert result.status == "clarify" and result.contract is None
    assert any(i.field == "recovery:n_heptane" and i.kind == "missing" for i in result.issues)


def test_conflicting_pressures_block_execution() -> None:
    parsed, prompt = specified()
    parsed.quantities.append(
        Quantity(field="pressure", value=150, unit="kPa", quote="also 150 kPa")
    )
    result = compile_task(parsed, prompt + " also 150 kPa")
    assert result.status == "clarify" and result.contract is None
    assert any(i.field == "pressure" and i.kind == "conflict" for i in result.issues)


def test_changed_physics_is_not_silently_replaced_by_canonical_input() -> None:
    parsed, prompt = specified()
    for q in parsed.quantities:
        if q.field == "pressure":
            q.value, q.quote = 150, "150 kPa"
    result = compile_task(parsed, prompt + "150 kPa")
    assert result.status == "unsupported" and result.contract is None


def test_fabricated_quote_and_number_block_execution() -> None:
    parsed, prompt = specified()
    parsed.quantities[0].quote = "not in original prompt"
    assert compile_task(parsed, prompt).contract is None
    parsed, prompt = specified()
    parsed.quantities[0].value = 101.3001
    assert compile_task(parsed, prompt).contract is None


def test_semantically_equal_units_and_component_orders_share_numerical_key() -> None:
    parsed, prompt = specified()
    first = compile_task(parsed, prompt).contract
    parsed.components.reverse()
    q = next(q for q in parsed.quantities if q.field == "feed_flow")
    q.value, q.unit, q.quote = 60, "mol/min", "60 mol/min"
    second = compile_task(parsed, prompt + "60 mol/min").contract
    assert first is not None and second is not None
    assert first.identity() == second.identity()


def test_report_rejects_unrelated_evidence_and_unearned_validation() -> None:
    report = EvidenceReport(
        disposition="validated_engineering_design",
        claims=[
            EvidenceClaim(claim_id="stage_range", evidence_ids=["scope"]),
            EvidenceClaim(claim_id="global_optimum", evidence_ids=["design"]),
        ],
    )
    result = audit_report(report, {"stage_range": ["design"], "preliminary_scope": ["scope"]})
    assert not result["fully_grounded"] and not result["disposition_correct"]
    assert result["unsupported_claims"] == ["stage_range", "global_optimum"]
    assert "preliminary_scope" in result["missing_claims"]


def test_additional_relevant_evidence_does_not_invalidate_a_supported_claim() -> None:
    report = EvidenceReport(
        disposition="preliminary_with_limits",
        claims=[
            EvidenceClaim(claim_id="stage_range", evidence_ids=["design", "sensitivity"]),
            EvidenceClaim(claim_id="preliminary_scope", evidence_ids=["scope", "validation"]),
        ],
    )
    assert audit_report(report, {"stage_range": ["design"], "preliminary_scope": ["scope"]})[
        "fully_grounded"
    ]
    report.claims[0].evidence_ids = ["sensitivity"]
    assert not audit_report(report, {"stage_range": ["design"], "preliminary_scope": ["scope"]})[
        "fully_grounded"
    ]


def test_recovery_dimensionless_unit_is_a_valid_fraction() -> None:
    assert (
        normalize(Quantity(field="recovery:benzene", value=0.7, unit="dimensionless", quote="0.7"))
        == 0.7
    )


@pytest.mark.parametrize(
    "source,quote,expected",
    [
        ("DMF/有机进料质量比32:1", "DMF/有机进料质量比32:1", True),
        ("DMF solvent/feed mass ratio of 32:1", "32:1", True),
        ("DMF/organic feed 32 kg/kg", "32 kg/kg", True),
        ("DMF/有机进料用量比32:1", "DMF/有机进料用量比32:1", False),
        ("An unrelated mass ratio was measured; DMF/organic feed 32:1", "32:1", False),
    ],
)
def test_mass_basis_requires_source_evidence_even_if_llm_labels_it_mass(
    source: str,
    quote: str,
    expected: bool,
) -> None:
    fields = []
    for key, value in SPECS["extractive"].items():
        if key.startswith("solvent_ratio"):
            fields.append(Quantity(field=key, value=value, unit="mass_ratio", quote=quote))
        else:
            unit = (
                "fraction"
                if ":" in key
                else {"pressure": "kPa", "feed_flow": "mol/s", "reflux": "dimensionless"}[key]
            )
            fields.append(Quantity(field=key, value=value, unit=unit, quote=f"{key}={value}"))
    prompt = (
        "; ".join(q.quote for q in fields if not q.field.startswith("solvent_ratio"))
        + "; "
        + source
    )
    parsed = ParsedTask(
        status="ready",
        protocol="extractive",
        components=ORDER["extractive"],
        feed_state="saturated_liquid",
        quantities=fields,
        issues=[],
        plan=PLANS["extractive"],
    )
    result = compile_task(parsed, prompt)
    assert (result.status == "ready") is expected
    if not expected:
        assert any(i.field == "solvent_ratio:DMF" and i.kind == "ambiguous" for i in result.issues)


def test_clarification_never_enters_numerical_backend(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    import thermo_engine.paper_reliability as backend

    import scripts.benchmarks.paper_agent.reliability_run as runner

    parsed, _ = specified()
    parsed.status = "clarify"
    parsed.issues = [InputIssue(field="pressure", kind="missing", question="What pressure?")]

    class Stub:
        calls: list[Any] = []

        def parse(self, prompt: str) -> ParsedTask:
            return parsed

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("An incomplete request must not reach a numerical solver")

    monkeypatch.setattr(runner, "ReliabilityLLM", Stub)
    monkeypatch.setattr(backend, "execute_frozen_protocol", forbidden)
    task = next(t for t in reliability_tasks() if t["task_id"] == "binary-missing-0")
    result = runner.run_one(task, 0, tmp_path, {})
    assert result["metrics"]["clarification_correct"] and result["metrics"]["gate_blocks_invalid"]
    assert not any(s["step"] == "tool" for s in result["trace"])
