"""Turn observable failures into bounded recovery suggestions, not guessed causes."""

from __future__ import annotations

from schemas.domain import CalculationEnvelope, FailureDetail, FailureType, TaskManifest
from schemas.evidence import Diagnostic, EvidenceGap, EvidenceItem, EvidenceSource


def missing_conditions(task: TaskManifest) -> list[str]:
    conditions = task.conditions
    kind = task.calculation_type
    missing: list[str] = []
    if kind == "isobaric_vle" and conditions.pressure_kPa is None:
        missing.append("pressure_kPa")
    if kind in {"bubble_point", "dew_point", "azeotrope"}:
        if conditions.temperature_K is None and conditions.pressure_kPa is None:
            missing.append("temperature_K or pressure_kPa")
    if kind in {"isothermal_vle", "tp_flash", "phase_stability", "lle", "infinite_dilution_activity"}:
        if conditions.temperature_K is None and conditions.temperature_span_K is None:
            missing.append("temperature_K")
    if kind in {"tp_flash", "phase_stability"}:
        if conditions.pressure_kPa is None:
            missing.append("pressure_kPa")
        if conditions.feed_composition is None:
            missing.append("feed_composition")
    if kind == "bubble_point" and conditions.liquid_composition is None:
        missing.append("liquid_composition")
    if kind == "dew_point" and conditions.vapor_composition is None:
        missing.append("vapor_composition")
    return missing


def diagnose_failure(failure: FailureDetail, *, explicit_model: bool) -> Diagnostic:
    recoverable = not explicit_model and failure.failure_type in {
        FailureType.NUMERICAL_NONCONVERGENCE, FailureType.PHYSICAL_VALIDATION_FAILURE,
        FailureType.PHASE_INSTABILITY, FailureType.PARAMETER_OUT_OF_DOMAIN,
    }
    known = failure.failure_type in {FailureType.MISSING_PARAMETERS, FailureType.UNSUPPORTED_MODEL,
                                    FailureType.SEMANTIC_FAILURE, FailureType.MISSING_DATA}
    return Diagnostic(
        code=failure.failure_type.value, observation=failure.message,
        cause=failure.failure_type.value if known else "unknown", cause_confirmed=known,
        recoverable=recoverable,
        suggested_actions=["check_applicability"] if recoverable else ["stop"],
    )


def validation_evidence(envelope: CalculationEnvelope) -> tuple[list[EvidenceItem], list[EvidenceGap]]:
    run_id = envelope.result.run_id
    validation = envelope.validation
    source = EvidenceSource(source_id=f"validation:{run_id}", title="Independent validation report",
                            uri=f"run:{run_id}", source_kind="validation", reviewed=True)
    items: list[EvidenceItem] = []
    gaps: list[EvidenceGap] = []
    for name in ("composition_balance", "material_balance", "equilibrium_residual", "convergence",
                 "parameter_applicability", "phase_stability"):
        check = getattr(validation, name)
        if check is None:
            status = "unverified" if name == "phase_stability" else "not_applicable"
            claim = "未提供完整相稳定性检查证据。" if name == "phase_stability" else "This check is not applicable."
        else:
            unknown = name == "phase_stability" and "not performed" in check.message.lower()
            status = "unverified" if unknown else "supported" if check.passed else "failed"
            claim = check.message
        items.append(EvidenceItem(evidence_id=f"{run_id}:{name}", claim=claim, status=status,
                                  source=source, scope=envelope.result.model_name,
                                  field_path=f"validation.{name}"))
        if status in {"failed", "unverified"}:
            required = name != "phase_stability" or envelope.result.calculation_type in {"tp_flash", "phase_stability", "lle"}
            gaps.append(EvidenceGap(code=name, description=claim, required=required,
                                    suggested_actions=["diagnose"] if status == "failed" else []))
    return items, gaps
