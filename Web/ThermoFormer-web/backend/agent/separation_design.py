"""Budgeted separation decisions over physically checked engineering tools."""

from schemas.separation import DesignAttempt, DesignDecision, SeparationCapability, SeparationReport
from schemas.separation_task import SeparationDesignRequest
from thermo_engine.errors import ThermoEquiError
from thermo_engine.separation import SeparationTools


def separation_capabilities() -> list[SeparationCapability]:
    return [
        SeparationCapability(
            method="flash",
            label="单级闪蒸",
            availability="design_loop",
            limitation="给定温压、二元进料、汽相为目标产品；未证明全局相稳定性。",
        ),
        SeparationCapability(
            method="distillation",
            label="普通精馏",
            availability="design_loop",
            limitation="二元快捷设计与回流比调整；有限相图采样，不是严格塔模拟。",
        ),
        SeparationCapability(
            method="extractive_distillation",
            label="萃取精馏",
            availability="legacy_specialized",
            limitation="该专用设计入口不支持统一模型比较和溶剂回收闭环。",
        ),
        SeparationCapability(
            method="liquid_extraction",
            label="液液萃取",
            availability="legacy_specialized",
            limitation="已有特定体系入口；尚无通用多级萃取与溶剂回收设计闭环。",
        ),
        SeparationCapability(
            method="pressure_swing",
            label="压力摆动精馏",
            availability="not_implemented",
            limitation="需要多压力共沸证据、双塔及循环物流求解。",
        ),
        SeparationCapability(
            method="adsorption",
            label="吸附分离",
            availability="not_implemented",
            limitation="需要吸附等温线、传质和循环模型。",
        ),
        SeparationCapability(
            method="membrane",
            label="膜分离",
            availability="not_implemented",
            limitation="需要渗透率、选择性与膜组件模型。",
        ),
    ]


def run_separation_design(request: SeparationDesignRequest) -> SeparationReport:
    tools = SeparationTools(request)
    report = SeparationReport(
        status="blocked",
        stop_reason="no_supported_candidate",
        capabilities=separation_capabilities(),
        input_snapshot=request.model_dump(mode="json"),
        warnings=[
            "结果是候选初步设计；未执行 DWSIM 严格模拟或能耗优化。",
            "第一组分为塔顶或汽相目标组分；比较仅覆盖本次指定方法和候选参数。",
        ],
    )
    report.decisions.append(DesignDecision(action="check_inputs", reason="保留显式模型、进料顺序及设计目标。"))
    if request.methods == ["flash"] and request.task.conditions.temperature_K is None:
        report.status = "needs_input"
        report.stop_reason = "missing_flash_temperature"
        report.missing_inputs = ["闪蒸温度"]
        report.decisions.append(DesignDecision(action="clarify", reason="仅请求闪蒸时必须提供温度。"))
        return report
    calls = 0
    fatal_failure = False
    for method in request.methods:
        capability = next(c for c in report.capabilities if c.method == method)
        if capability.availability != "design_loop":
            report.attempts.append(DesignAttempt(method=method, status="screened_out", reason=capability.limitation))
            report.decisions.append(DesignDecision(action="screen_method", reason=capability.limitation))
            continue
        factors = sorted(set(request.reflux_factors)) if method == "distillation" else [1.0]
        for factor in factors:
            if calls >= request.max_attempts:
                report.status = "budget_exhausted"
                report.stop_reason = "design_attempt_budget_exhausted"
                break
            calls += 1
            report.decisions.append(
                DesignDecision(
                    action="evaluate_candidate",
                    reason=(
                        "调用相平衡并检查单级分离目标。"
                        if method == "flash"
                        else "使用同一模型的已验证相图和产品泡点，计算候选回流比下的快捷设计。"
                    ),
                )
            )
            try:
                attempt = tools.flash() if method == "flash" else tools.distillation(factor)
            except (ThermoEquiError, ValueError, NotImplementedError) as exc:
                reason = str(exc)
                attempt = DesignAttempt(
                    method=method,
                    status="failed",
                    reason=reason,
                    failure_type=exc.detail.failure_type if isinstance(exc, ThermoEquiError) else "design_infeasible",
                    recovery_action=exc.detail.recovery_action if isinstance(exc, ThermoEquiError) else None,
                    evidence_run_ids=[e.result.run_id for e in tools.calculations],
                )
                report.attempts.append(attempt)
                report.decisions.append(
                    DesignDecision(action="diagnose_and_stop_method", reason=reason, attempt_id=attempt.attempt_id)
                )
                report.stop_reason = "tool_or_validation_failure"
                if isinstance(exc, ThermoEquiError) and exc.detail.failure_type in {
                    "missing_parameters",
                    "parameter_out_of_domain",
                    "physical_validation_failure",
                    "phase_instability",
                }:
                    fatal_failure = True
                    report.stop_reason = str(exc.detail.failure_type)
                # Repeating a failed thermodynamic preparation with a different
                # reflux setting cannot repair its missing/invalid evidence.
                break
            report.attempts.append(attempt)
            report.decisions.append(
                DesignDecision(action="check_constraints", reason=attempt.reason, attempt_id=attempt.attempt_id)
            )
            if attempt.status == "preliminary":
                report.status = "preliminary"
                report.stop_reason = "first_candidate_meets_preliminary_checks"
                report.selected_attempt_id = attempt.attempt_id
                break
            if method == "distillation":
                if any(c.name == "reflux_limit" and c.status == "failed" for c in attempt.checks):
                    report.decisions.append(
                        DesignDecision(action="stop_method", reason="回流比已超上限，提高回流不可修复。")
                    )
                    break
                report.decisions.append(
                    DesignDecision(action="revise_reflux", reason="塔板数超限，尝试预算内更高回流比。")
                )
            else:
                report.decisions.append(
                    DesignDecision(action="switch_method", reason="闪蒸未达标，检查下一种获准方法。")
                )
        if report.selected_attempt_id or report.status == "budget_exhausted" or fatal_failure:
            break
    report.calculation_snapshots = [e.model_dump(mode="json") for e in tools.calculations]
    if (
        not fatal_failure
        and report.status == "blocked"
        and any(a.status == "constraint_failed" for a in report.attempts)
    ):
        report.stop_reason = "candidate_set_exhausted_without_meeting_constraints"
    for envelope in tools.calculations:
        report.warnings.extend(envelope.validation.warnings)
        report.warnings.extend(envelope.result.warnings)
    report.warnings = list(dict.fromkeys(report.warnings))
    report.decisions.append(DesignDecision(action="stop", reason=report.stop_reason))
    return report


def separation_summary(report: SeparationReport) -> str:
    if report.status == "needs_input":
        return "分离设计还需要：" + "、".join(report.missing_inputs) + "。"
    lines = ["分离方案初步评估（目标产品为第一组分）："]
    labels = {c.method: c.label for c in report.capabilities}
    for attempt in report.attempts:
        lines.append(f"- {labels.get(attempt.method, attempt.method)}：{attempt.reason}")
        if attempt.metrics:
            lines.append("  " + "；".join(f"{key}={value:g}" for key, value in attempt.metrics.items()))
    lines.extend(report.warnings)
    lines.append("停止原因：" + report.stop_reason)
    return "\n".join(lines)
