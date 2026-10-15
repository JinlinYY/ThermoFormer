"""Numerical separation tools. Every equilibrium call crosses the validation gate."""

from dataclasses import asdict, dataclass, field
from math import isfinite

from schemas.column_design import BinaryDistillationResult
from schemas.domain import CalculationEnvelope, FailureType, TaskManifest, ThermodynamicConditions
from schemas.separation import DesignAttempt, DesignCheck
from schemas.separation_task import SeparationDesignRequest
from thermo_engine.column_design import design_binary_distillation_column
from thermo_engine.errors import ThermoEquiError
from thermo_engine.service import calculate_equilibrium, resolve_backend, validate_equilibrium_result


@dataclass
class SeparationTools:
    request: SeparationDesignRequest
    calculations: list[CalculationEnvelope] = field(default_factory=list)
    _distillation_data: tuple[float, float, float] | None = None

    def _equilibrium(self, calculation_type: str, conditions: ThermodynamicConditions) -> CalculationEnvelope:
        task = TaskManifest.model_validate(
            {
                **self.request.task.model_dump(),
                "calculation_type": calculation_type,
                "equilibrium_type": "FLASH" if calculation_type == "tp_flash" else "VLE",
                "conditions": conditions.model_dump(),
                "points": 61,
            }
        )
        backend = resolve_backend(task)
        result = calculate_equilibrium(task, backend)
        report = validate_equilibrium_result(result)
        envelope = CalculationEnvelope(
            result=result, validation=report, parameter_sources=backend.parameter_sources(task)
        )
        self.calculations.append(envelope)
        if report.overall_status == "failed":
            raise ThermoEquiError(
                FailureType.PHYSICAL_VALIDATION_FAILURE,
                "Separation evidence failed physical validation.",
                "Inspect the retained validation report before changing the design.",
            )
        return envelope

    def flash(self) -> DesignAttempt:
        request = self.request
        c = request.task.conditions
        if c.temperature_K is None:
            return DesignAttempt(method="flash", status="screened_out", reason="缺少闪蒸温度，未执行计算。")
        envelope = self._equilibrium(
            "tp_flash",
            ThermodynamicConditions(
                temperature_K=c.temperature_K, pressure_kPa=c.pressure_kPa, feed_composition=c.feed_composition
            ),
        )
        vapor = next((p for p in envelope.result.phases if p.phase == "vapor"), None)
        liquid = next((p for p in envelope.result.phases if p.phase == "liquid"), None)
        if vapor is None or liquid is None or not 0 < vapor.fraction < 1:
            return DesignAttempt(
                method="flash",
                status="screened_out",
                reason="给定温压下没有可用的两相分离。",
                evidence_run_ids=[envelope.result.run_id],
            )
        assert c.feed_composition is not None
        purity = vapor.composition[0]
        recovery = vapor.fraction * purity / c.feed_composition[0]
        passed = purity >= request.target_purity and recovery >= request.target_recovery
        return DesignAttempt(
            method="flash",
            status="preliminary" if passed else "constraint_failed",
            reason="单级闪蒸满足指定目标。" if passed else "单级闪蒸未满足纯度或回收率目标。",
            metrics={"product_purity": purity, "recovery": recovery, "vapor_fraction": vapor.fraction},
            checks=[
                DesignCheck(
                    name="product_targets",
                    status="passed" if passed else "failed",
                    message="依据验证后的汽相组成、相分率和进料组成检查。",
                ),
                DesignCheck(name="phase_stability", status="unverified", message="未将闪蒸收敛视为全局相稳定性证明。"),
            ],
            evidence_run_ids=[envelope.result.run_id],
        )

    def _prepare_distillation(self) -> tuple[float, float, float]:
        request = self.request
        c = request.task.conditions
        assert c.feed_composition is not None
        z = c.feed_composition[0]
        purity = request.target_purity
        if purity <= z:
            raise ValueError("塔顶目标纯度须高于进料中第一组分的摩尔分率。")
        distillate = request.target_recovery * z / purity
        bottom_light = (z - distillate * purity) / (1 - distillate)
        if not 0 < distillate < 1 or not 0 < bottom_light < 1:
            raise ValueError("指定纯度与回收率对应不可行的物料分配。")
        curve = self._equilibrium("isobaric_vle", ThermodynamicConditions(pressure_kPa=c.pressure_kPa))
        points = sorted(curve.result.points, key=lambda p: p.liquid_composition[0])
        if not points or points[0].liquid_composition[0] > bottom_light or points[-1].liquid_composition[0] < purity:
            raise ValueError("相图没有覆盖产品组成区间，不能据此设计精馏。")
        relevant = [p for p in points if bottom_light <= p.liquid_composition[0] <= purity]
        # Independently calculated product endpoints retain the same explicit model.
        endpoints = []
        for x in (purity, bottom_light):
            bubble = self._equilibrium(
                "bubble_point", ThermodynamicConditions(pressure_kPa=c.pressure_kPa, liquid_composition=[x, 1 - x])
            )
            if len(bubble.result.points) != 1:
                raise ValueError("产品泡点未返回唯一有效结果。")
            endpoints.append(bubble.result.points[0])
        relevant.extend(endpoints)
        alphas = []
        for point in relevant:
            x = point.liquid_composition[0]
            y = point.vapor_composition[0]
            if not 0 < x < 1 or not 0 < y < 1:
                raise ValueError("相图存在不可用于相对挥发度计算的组成。")
            alpha = y * (1 - x) / (x * (1 - y))
            if not isfinite(alpha) or alpha <= 1.0001:
                raise ValueError("产品组成区间发现挥发度反转或夹点风险，普通精馏快捷设计被阻止。")
            alphas.append(alpha)
        return min(alphas), endpoints[0].temperature_K, endpoints[1].temperature_K

    def distillation(self, reflux_factor: float) -> DesignAttempt:
        if self._distillation_data is None:
            self._distillation_data = self._prepare_distillation()
        alpha, condenser, reboiler = self._distillation_data
        r = self.request
        c = r.task.conditions
        assert c.feed_composition is not None and c.pressure_kPa is not None
        design = design_binary_distillation_column(
            [component.name for component in r.task.components],
            c.feed_composition,
            feed_flow_mol_s=r.feed_flow_mol_s,
            feed_temperature_K=condenser,
            operating_pressure_kPa=c.pressure_kPa,
            distillate_purity_mole_fraction=r.target_purity,
            recovery=r.target_recovery,
            relative_volatility_override=alpha,
            condenser_temperature_K_override=condenser,
            reboiler_temperature_K_override=reboiler,
            reflux_factor=reflux_factor,
        )
        BinaryDistillationResult.model_validate(asdict(design))
        stages_ok = r.max_stages is None or design.theoretical_stages <= r.max_stages
        reflux_ok = r.max_reflux_ratio is None or design.reflux_ratio <= r.max_reflux_ratio
        passed = stages_ok and reflux_ok
        return DesignAttempt(
            method="distillation",
            status="preliminary" if passed else "constraint_failed",
            reason="快捷设计满足指定塔板数与回流比约束。" if passed else "快捷设计违反塔板数或回流比约束。",
            metrics={
                "specified_purity": r.target_purity,
                "specified_recovery": r.target_recovery,
                "theoretical_stages": float(design.theoretical_stages),
                "reflux_ratio": design.reflux_ratio,
                "reflux_factor": reflux_factor,
                "sampled_minimum_alpha": alpha,
                "distillate_flow_mol_s": design.distillate_flow_mol_s,
                "bottoms_flow_mol_s": design.bottoms_flow_mol_s,
                "condenser_temperature_K": condenser,
                "reboiler_temperature_K": reboiler,
            },
            checks=[
                DesignCheck(name="stage_limit", status="passed" if stages_ok else "failed", message="检查塔板数上限。"),
                DesignCheck(
                    name="reflux_limit", status="passed" if reflux_ok else "failed", message="检查回流比上限。"
                ),
                DesignCheck(
                    name="rigorous_product_targets",
                    status="unverified",
                    message="纯度和回收率为快捷设计输入，尚未通过严格塔模拟独立验证。",
                ),
                DesignCheck(
                    name="global_phase_feasibility",
                    status="unverified",
                    message="有限相图采样不能证明不存在未采样共沸点或液液分相。",
                ),
            ],
            evidence_run_ids=[e.result.run_id for e in self.calculations if e.result.calculation_type != "tp_flash"],
        )
