"""Conservative design-input parsing; ambiguity returns missing fields."""

import copy
import re
from typing import Any

from pydantic import ValidationError

from agent.extractive_distillation import (
    _find_feed_flow,
    _find_pressure,
    _find_temperature,
)
from agent.separation_design import run_separation_design, separation_capabilities
from schemas.domain import ParameterSet
from schemas.separation import SeparationReport
from schemas.separation_task import SeparationDesignRequest
from thermo_engine.identity import resolve_literal_components


def is_separation_design_request(message: str) -> bool:
    return any(
        marker in message.casefold()
        for marker in (
            "分离方案",
            "分离过程设计",
            "继续分离",
            "闪蒸分离",
            "压力摆动精馏",
            "变压精馏",
            "膜分离设计",
            "吸附分离设计",
            "separation design",
        )
    )


def design_from_message(
    message: str, previous: dict[str, Any], parameters: list[ParameterSet]
) -> tuple[SeparationReport, dict[str, Any]]:
    try:
        return _design_from_message(message, previous, parameters)
    except (ValueError, OverflowError):
        return SeparationReport(
            status="needs_input",
            stop_reason="invalid_design_inputs",
            missing_inputs=["请检查数字格式、单位与组成，并重新提供明确的设计输入。"],
            capabilities=separation_capabilities(),
        ), copy.deepcopy(previous)


def _design_from_message(
    message: str, previous: dict[str, Any], parameters: list[ParameterSet]
) -> tuple[SeparationReport, dict[str, Any]]:
    values = copy.deepcopy(previous)
    task = values.setdefault("task", {"equilibrium_type": "VLE", "calculation_type": "isobaric_vle"})
    conditions = task.setdefault("conditions", {})
    resolved = [component for _, component in resolve_literal_components(message)]
    if resolved:
        if len(resolved) >= 2:
            new_components = [component.model_dump() for component in resolved]
            if task.get("components") and task["components"] != new_components:
                # Never reuse the old feed for a different component pair/order.
                conditions.pop("feed_composition", None)
            task["components"] = new_components
    composition = re.search(
        r"(?:进料(?:摩尔)?组成|feed composition)\s*[:：=为]?\s*\[?\s*([\d.]+)\s*[,，/]\s*([\d.]+)", message, re.I
    )
    if composition:
        conditions["feed_composition"] = [float(composition[1]), float(composition[2])]
    pressure = _find_pressure(message)
    temperature = _find_temperature(message)
    if pressure is not None:
        conditions["pressure_kPa"] = pressure
    if temperature is not None:
        conditions["temperature_K"] = temperature
    requested_models = []
    for pattern, model in (
        (r"thermoformer", "ThermoFormer"),
        (r"uniquac", "UNIQUAC"),
        (r"unifac", "UNIFAC"),
        (r"nrtl", "NRTL"),
        (r"wilson", "Wilson"),
        (r"ideal|raoult|理想模型", "Ideal/Raoult"),
    ):
        if re.search(pattern, message, re.I):
            requested_models.append(model)
    if len(requested_models) > 1:
        return SeparationReport(
            status="needs_input",
            stop_reason="ambiguous_property_model",
            missing_inputs=["本次设计请指定一个物性模型；当前不支持在设计中混用多个模型。"],
            capabilities=separation_capabilities(),
        ), values
    if requested_models:
        task["model_name"] = requested_models[0]
    for label, field in ((r"纯度|purity", "target_purity"), (r"回收率|recovery", "target_recovery")):
        match = re.search(rf"(?:{label})\s*(?:为|=|:|：|≥|>=)?\s*([\d.]+)\s*(%|％)?", message, re.I)
        if match:
            number = float(match[1])
            values[field] = number / 100 if match[2] else number
    for pattern, field in (
        (r"(?:最多|不超过|最大)\s*(\d+)\s*(?:块|级|层)?\s*(?:塔板|理论板)", "max_stages"),
        (r"回流比\s*(?:不超过|上限|<=|≤)\s*([\d.]+)", "max_reflux_ratio"),
    ):
        match = re.search(pattern, message)
        if match:
            values[field] = int(match[1]) if field == "max_stages" else float(match[1])
    flow = _find_feed_flow(message)
    if flow is not None:
        values["feed_flow_mol_s"] = flow
    for marker, method in (
        ("变压精馏", "pressure_swing"),
        ("压力摆动精馏", "pressure_swing"),
        ("膜分离设计", "membrane"),
        ("吸附分离设计", "adsorption"),
        ("只用闪蒸", "flash"),
        ("只用普通精馏", "distillation"),
    ):
        if marker in message:
            values["methods"] = [method]
            break
    if "自动选择" in message:
        values["methods"] = ["flash", "distillation"]
    task["original_question"] = message
    # Keep submitted parameter snapshots on follow-up; new records are only
    # supplied by the parameter repository, never generated from prose.
    if parameters:
        task["parameters"] = [p.model_dump(mode="json") for p in parameters if p.source_type != "test_fixture"]
    missing = [
        label
        for present, label in (
            (task.get("components"), "二元组分（第一组分为目标产品）"),
            (conditions.get("feed_composition"), "进料摩尔组成，例如：进料组成 0.5,0.5"),
            (conditions.get("pressure_kPa"), "操作压力"),
            (task.get("model_name"), "物性模型"),
            (values.get("target_purity"), "目标纯度，例如：纯度95%"),
            (values.get("target_recovery"), "目标回收率，例如：回收率95%"),
        )
        if not present
    ]
    if missing:
        return SeparationReport(
            status="needs_input",
            stop_reason="missing_design_inputs",
            missing_inputs=missing,
            capabilities=separation_capabilities(),
        ), values
    try:
        request = SeparationDesignRequest.model_validate(values)
    except ValidationError as exc:
        return SeparationReport(
            status="needs_input",
            stop_reason="invalid_design_inputs",
            missing_inputs=[error["msg"] for error in exc.errors()],
            capabilities=separation_capabilities(),
        ), values
    return run_separation_design(request), values
