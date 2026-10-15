"""Generate a Chinese C3 chapter draft from persisted, auditable calculations.

No equilibrium, process rating, fitting, or LLM call is performed here. Numbers
are read from study records or obtained by transparent counting/unit conversion.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt(value: Any, decimals: int = 3) -> str:
    return "未计算" if value is None else f"{float(value):.{decimals}f}"


def _percent(value: Any, decimals: int = 4) -> str:
    return "未计算" if value is None else _fmt(100 * float(value), decimals)


def _kw(value: Any) -> str:
    return "未计算" if value is None else _fmt(float(value) / 1000, 3)


def _sci(value: Any) -> str:
    return "未计算" if value is None else f"{float(value):.3e}"


def _cold(record: dict[str, Any], name: str = "water_10_to_15C") -> dict[str, Any]:
    return next(
        (
            s
            for s in record.get("utilities", {}).get("cooling_scenarios", [])
            if s.get("scenario", {}).get("name") == name
        ),
        {},
    )


def _scenario_extremes(record: dict[str, Any]) -> tuple[float | None, float | None]:
    # Never hide invalid scenario ratings by treating them as successful values.
    states = record.get("robustness", {}).get("scenarios", [])
    if not states or any(not s.get("numerically_validated") for s in states):
        return None, None
    top = min(float(s["metrics"]["distillate_propene_mole_fraction"]) for s in states)
    bottom = max(float(s["metrics"]["bottoms_propene_mole_fraction"]) for s in states)
    return top, bottom


def _flat_record(record: dict[str, Any]) -> dict[str, Any]:
    candidate = record["candidate"]
    metrics = candidate.get("metrics", {})
    utilities = record.get("utilities", {})
    top, bottom = _scenario_extremes(record)
    cooling = _cold(record)
    heating = record.get("heating", record.get("heating_optional", {}))
    diagnostic = utilities.get("whole_column_energy_diagnostic") or {}
    return {
        "candidate_id": record["candidate_id"],
        "round_type": record.get("margin", "unknown"),
        "pressure_kpa": record["pressure_kpa"],
        "equilibrium_stages_including_reboiler": metrics.get("stages_including_reboiler"),
        "feed_stage_from_top": metrics.get("feed_stage_from_top"),
        "reflux_ratio": metrics.get("reflux_ratio"),
        "nominal_top_propene": metrics.get("distillate_propene_mole_fraction"),
        "nominal_bottom_propene": metrics.get("bottoms_propene_mole_fraction"),
        "nominal_targets_passed": candidate.get("meets_targets", False),
        "direct_numerical_review_passed": candidate.get("verified", False),
        "scenario_gate_passed": record.get("robustness", {}).get("passed", False),
        "minimum_top_propene_in_declared_scenarios": top,
        "maximum_bottom_propene_in_declared_scenarios": bottom,
        "cold_10_to_15C_endpoint_passed": cooling.get("endpoint_screen_passed", False),
        "cold_10_to_15C_minimum_approach_k": cooling.get("minimum_endpoint_approach_k"),
        "cold_10_to_15C_water_flow_kg_s": cooling.get("coolant_mass_flow_kg_s"),
        "local_PR_condenser_duty_w": (utilities.get("condenser") or {}).get("duty_w"),
        "local_PR_reboiler_duty_w": (utilities.get("reboiler") or {}).get("duty_w"),
        "whole_column_relative_energy_discrepancy": diagnostic.get("absolute_discrepancy_relative_to_larger_duty"),
        "whole_column_signed_energy_discrepancy_w": diagnostic.get("Qr_minus_Qc_minus_product_minus_feed_enthalpy_w"),
        "hot_60_to_50C_endpoint_passed": heating.get("endpoint_screen_passed"),
        "hot_60_to_50C_water_flow_kg_s": heating.get("hot_water_mass_flow_kg_s"),
        "autonomous_LLM_numerical_search": False,
        "process_experimental_validation": False,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _comparison_table(records: list[dict[str, Any]], selected_id: str | None) -> str:
    lines = [
        "| 候选 | 压力 / MPa | 平衡级数 | 回流比 | PR 再沸负荷 / kW"
        " | 情景最低塔顶丙烯 / mol% | 情景最高塔底丙烯 / mol% | 10→15°C冷源 |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for record in records:
        row = _flat_record(record)
        mark = "（最终保留）" if row["candidate_id"] == selected_id else ""
        lines.append(
            f"| {row['candidate_id']}{mark} | {_fmt(row['pressure_kpa'] / 1000, 2)}"
            f" | {row['equilibrium_stages_including_reboiler']} | {_fmt(row['reflux_ratio'], 3)}"
            f" | {_kw(row['local_PR_reboiler_duty_w'])}"
            f" | {_percent(row['minimum_top_propene_in_declared_scenarios'])}"
            f" | {_percent(row['maximum_bottom_propene_in_declared_scenarios'])}"
            f" | {'端点通过' if row['cold_10_to_15C_endpoint_passed'] else '端点不通过'} |"
        )
    return "\n".join(lines)


def _agent_attempts(study: Path, current: dict[str, Any]) -> list[dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for path in sorted(study.glob("agent_engineering_review*.json")):
        result = _read(path)
        if not result.get("live_requested") or not result.get("llm_calls"):
            continue
        results[result.get("run_id", path.name)] = {**result, "artifact_name": path.name}
    if current.get("run_id") not in results and current:
        results[current.get("run_id", "current")] = {
            **current,
            "artifact_name": "engineering_summary.json:agent_result",
        }
    return sorted(results.values(), key=lambda row: row.get("started_utc", ""))


def _agent_text(study: Path, agent: dict[str, Any]) -> str:
    if not agent:
        return "当前尚无实际 LLM 运行记录，因此没有生成 Agent 已完成审查或接受候选的结论。"
    attempts = _agent_attempts(study, agent)
    older_failures = [
        a
        for a in attempts
        if a.get("run_id") != agent.get("run_id") and a.get("outcome") in {"provider_error", "execution_error"}
    ]
    paragraphs = [
        "候选构造、参数扫描、最坏情景重算和直接泡点复核均由确定性数值程序预先完成。"
        "本次 LLM 的任务限定为比较这些候选、读取工程及扰动证据、检查是否允许报告并作出停止判断。"
        "读取工具明确标注缓存复用，不产生新的相平衡或流程数值。",
        f"当前实际运行记录包含 {agent.get('llm_calls', 0)} 次 LLM 接口调用、"
        f"{len(agent.get('tool_calls', []))} 次已有证据读取和 "
        f"{agent.get('new_numerical_calculations', 0)} 次新数值计算；"
        f"终止状态为 `{agent.get('outcome', 'unknown')}`。"
        "这一结果支持对给定候选的证据审查能力，不支持 LLM 自主发现设计空间、完成自主数值搜索或优于优化器的主张。",
    ]
    if older_failures:
        paragraphs.append(
            f"另保留了 {len(older_failures)} 次此前实际运行的错误记录。"
            "其中返回允许行动集合之外的输出被执行框架拒绝，运行停止，没有据此接受候选或补造计算结果。"
            "随后修订行动契约说明并进行新的运行，失败记录没有被删除。"
            "这说明本次不合规动作受到边界约束，但单次或少量轨迹不能用于估计通用 Agent 错误率。"
        )
    trace_rows = []
    for i, entry in enumerate(agent.get("trace", []), start=1):
        choice = entry.get("choice") or {}
        if not choice:
            continue
        tool = entry.get("tool_call") or {}
        trace_rows.append(
            f"| {i} | `{choice.get('action_id', 'unknown')}` | "
            f"{'读取预计算记录' if tool else '终止／动作判定'} | "
            f"{entry.get('terminal_gate', '—')} |"
        )
    if trace_rows:
        paragraphs.append("| 顺序 | 实际行动 | 数值来源 | 终止门控 |\n|---:|---|---|---|\n" + "\n".join(trace_rows))
    if attempts:
        paragraphs.append(
            "全部接口尝试记录：\n\n| 文件 | 调用次数 | 结果 |\n|---|---:|---|\n"
            + "\n".join(
                f"| `{a['artifact_name']}` | {a.get('llm_calls', 0)} | `{a.get('outcome', 'unknown')}` |"
                for a in attempts
            )
        )
    return "\n\n".join(paragraphs)


def _optional_pr_text(study: Path, summary: dict[str, Any]) -> str:
    result: dict[str, Any] | None = None
    comparisons = summary.get("reference_comparisons", {})
    if summary.get("selected_candidate_id") in comparisons:
        result = comparisons[summary["selected_candidate_id"]]
    for key in ["selected_pr_comparison", "same_configuration_pr_comparison", "same_column_pr_comparison"]:
        value = summary.get(key)
        if isinstance(value, dict):
            result = value
            break
    if result is None:
        for name in ["selected_pr_comparison.json", "same_configuration_pr_comparison.json"]:
            if (study / name).exists():
                result = _read(study / name)
                break
    if result is None:
        return "当前汇总尚未附加所选方案的独立 PR 同配置重算；不据此声称跨模型一致性。"
    actual = result.get("reference", result.get("result", result.get("rating", result.get("candidate", result))))
    metrics = actual.get("metrics", {})
    if not metrics:
        return "另保存了 PR 对照记录，但该记录不含可报告的产品指标，未将其转写为成功验证。"
    passed = actual.get("numerical_checks", {}).get("passed", False)
    comparison_passes = sum(
        bool(r.get("reference", {}).get("meets_targets"))
        and bool(r.get("reference", {}).get("numerical_checks", {}).get("passed"))
        for r in comparisons.values()
    )
    count_text = (
        f"保存的{len(comparisons)}个同配置PR对照中，{comparison_passes}个通过数值门并满足产品要求。"
        if comparisons
        else ""
    )
    top_impurity = 1e6 * (1 - float(metrics["distillate_propene_mole_fraction"]))
    return (
        count_text + "另以有来源参数的 PR 比较器，在保持同一设备与操作配置的条件下进行重算。"
        f"数值门{'通过' if passed else '未通过'}，计算塔顶丙烯含量为 "
        f"{_percent(metrics.get('distillate_propene_mole_fraction'), 6)} mol%，"
        f"塔底丙烯含量为 {_percent(metrics.get('bottoms_propene_mole_fraction'))} mol%。"
        f"该PR结果对应塔顶丙烷杂质约{top_impurity:.3f} mol ppm，"
        "这一极低杂质预测没有高纯混合物实验支撑，报告位数不表示其物理准确度。"
        "该对照独立于Agent审查完成，未作为LLM审查输入；"
        "用于检验对物性模型选择的敏感性，不是独立过程实验，"
        "也不替代高纯区相平衡数据或完整能量衡算。"
    )


def generate_reports(study: Path) -> dict[str, Path]:
    """Write standalone chapter/method drafts without modifying manuscript PDFs."""
    source = study / "engineering_summary.json"
    summary = _read(source)
    records: list[dict[str, Any]] = summary["records"]
    if not records:
        raise ValueError("A completed numerical record collection is required")
    by_id = {row["candidate_id"]: row for row in records}
    baseline = by_id[summary["baseline_candidate_id"]]
    frontier = [by_id[key] for key in summary["frontier_candidate_ids"]]
    selected_id = summary.get("selected_candidate_id")
    selected = by_id.get(selected_id)
    protocol = _read(study / "protocol.json")
    calibration = _read(study / "stress_calibration.json")
    construction = _read(study / "scenario_design_protocol.json")
    training_recipe = _read(study.parent / "training/training_recipe.json")
    training_summary = _read(study.parent / "training/training_summary.json")
    agent = summary.get("agent_result") or {}
    if isinstance(agent, str):
        agent = _read(study / agent)
    round_one = [r for r in records if r.get("margin") in {"original", "guarded"}]
    round_two = [r for r in records if r.get("margin") == "scenario"]
    stress_one = sum(bool(r["robustness"]["passed"]) for r in round_one)
    stress_two = sum(bool(r["robustness"]["passed"]) for r in round_two)
    cold_stress = [
        r
        for r in records
        if r["robustness"]["passed"]
        and _cold(r).get("endpoint_screen_passed")
        and r["candidate"].get("meets_targets")
        and r["utilities"].get("validation", {}).get("passed")
    ]
    direct = [r for r in records if r["candidate"].get("verified")]
    base_metrics = baseline["candidate"]["metrics"]
    base_cold = _cold(baseline)
    base_top_worst, base_bottom_worst = _scenario_extremes(baseline)
    unsupported = "、".join(_fmt(r["pressure_kpa"] / 1000, 2) for r in summary.get("pressure_failures", []))
    supported = "、".join(_fmt(p / 1000, 2) for p in sorted({float(r["pressure_kpa"]) for r in records}))
    f_basis = float(baseline["specification"]["feed_flow_mol_s"])
    t_bounds = baseline["utilities"]["metadata"]["equilibrium_provenance"]["research_temperature_bounds_K"]
    table = _comparison_table([baseline, *frontier], selected_id)
    counts_table = (
        "| 筛查阶段 | 数量 | 判据与证据范围 |\n|---|---:|---|\n"
        f"| 首轮候选 | {len(round_one)} | 两组名义产品裕量与有限压力／回流比组合 |\n"
        f"| 首轮通过全部指定情景 | {stress_one} | 同一设备在负、零、正开发残差情景下重算 |\n"
        f"| 第二轮情景约束构造 | {len(round_two)} | 根据首轮结果调整的探索性设计 |\n"
        f"| 第二轮通过全部指定情景 | {stress_two} | 不等同概率可靠性保证 |\n"
        f"| 同时通过名义、情景与10→15°C冷源端点门 | {len(cold_stress)} | 仍非完整换热器可行性 |\n"
        f"| 有限非支配候选 | {len(frontier)} | 平衡级数与局部PR再沸负荷两个筛查指标 |\n"
        f"| 已通过直接逐级泡点复核 | {len(direct)} | 包括保留的基准及被复核的非支配候选 |"
    )
    selection_text = "当前没有被接受的最终候选；以下仅报告已计算候选与对应证据。"
    if selected is not None:
        metrics = selected["candidate"]["metrics"]
        flat = _flat_record(selected)
        cooling = _cold(selected)
        heating = selected.get("heating", selected.get("heating_optional", {}))
        verification = selected["candidate"].get("verification", {})
        direct_check = verification.get("direct_column_validation", {})
        stage_energy = (selected["utilities"].get("whole_column_energy_diagnostic") or {}).get(
            "internal_stage_diagnostic", {}
        )
        selection_text = (
            f"在提供的非支配集合中，依据事先向审查器声明的“优先较小局部 PR 再沸负荷”偏好，"
            f"最终保留 `{selected_id}`。其操作压力为 {_fmt(float(selected['pressure_kpa']) / 1000, 2)} MPa，"
            f"包含 {metrics['stages_including_reboiler']} 个平衡级（含再沸器），"
            f"进料级自塔顶计为 {metrics['feed_stage_from_top']}，回流比为 {_fmt(metrics['reflux_ratio'], 3)}。"
            f"名义模型计算的塔顶与塔底丙烯含量分别为 {_percent(metrics['distillate_propene_mole_fraction'])} mol%"
            f"和 {_percent(metrics['bottoms_propene_mole_fraction'])} mol%。"
            f"在给定三个情景中，最低塔顶含量为 {_percent(flat['minimum_top_propene_in_declared_scenarios'])} mol%，"
            f"最高塔底含量为 {_percent(flat['maximum_bottom_propene_in_declared_scenarios'])} mol%。\n\n"
            "名义模型的高纯度显示位数不代表已验证的准确度，接受判断只针对声明的目标和情景。"
            f"直接逐级泡点复核的最大相平衡残差为 {_sci(direct_check.get('numerical_residual'))}，"
            f"最大物料残差为 {_sci(direct_check.get('material_residual'))}；"
            "该复核独立于最初的曲线插值，不将插值自洽性直接当作原始模型的数值闭合。"
            f"声明冷源下的最小端温差为 {_fmt(cooling.get('minimum_endpoint_approach_k'))} K，"
            f"该冷水公用工程的显热流量需求估计为 {_fmt(cooling.get('coolant_mass_flow_kg_s'))} kg/s。"
            f"PR 局部焓衡算得到冷凝和再沸负荷分别为 {_kw(flat['local_PR_condenser_duty_w'])} kW"
            f"和 {_kw(flat['local_PR_reboiler_duty_w'])} kW，均对应 {f_basis:g} mol/s 进料基准。"
            f"全塔净能量失衡为 {_fmt(flat['whole_column_signed_energy_discrepancy_w'])} W，"
            f"占较大局部负荷的 {_percent(flat['whole_column_relative_energy_discrepancy'], 3)}%；"
            f"内部绝热级最大焓失衡为 {_fmt(stage_energy.get('maximum_absolute_stage_energy_residual_w'))} W。"
            "这些非零值用于暴露恒摩尔流近似与独立热量模型之间的不一致，没有被强制修正为闭合。"
        )
        if heating:
            selection_text += (
                f"另对声明的60→50°C热水进行独立端点筛查，最小端温差为 "
                f"{_fmt(heating.get('minimum_endpoint_approach_k'))} K，"
                f"热水流量估计为 {_fmt(heating.get('hot_water_mass_flow_kg_s'))} kg/s。"
                "该假设不代表现场公用工程已具备，也没有计入制冷机、热源系统及泵的能耗。"
            )
    paragraphs = [
        "# 面向高纯度丙烷／丙烯分离的工程约束筛选与证据审查\n\n"
        "本节为新增计算研究的中文草稿，数值由保存的运行结果生成，未改动原论文及原有三个案例。",
        "## 从名义纯度转向有条件的工程可接受性",
        "对于进料含丙烷65 mol%、丙烯35 mol%的分离任务，我们要求塔顶丙烯纯度不低于99.6 mol%，"
        "同时使塔底丙烯含量严格低于1 mol%。本研究没有相应装置的实测分离数据，"
        "因此考察的是模型支持的初步设计及其证据边界。评价除产品组成外，"
        "还纳入声明冷源与冷凝温度的匹配、模型支持范围以及选择性偏差对既定设备的影响。",
        f"在保留的1.00 MPa基准中，{base_metrics['stages_including_reboiler']}级、"
        f"回流比{_fmt(base_metrics['reflux_ratio'], 3)}的方案名义上达到产品要求。"
        f"然而，10→15°C冷水公用工程对应的最小端温差仅为 {_fmt(base_cold.get('minimum_endpoint_approach_k'))} K，"
        "低于声明的5 K要求。"
        f"该方案在指定情景中的最低塔顶丙烯含量和最高塔底丙烯含量分别为 "
        f"{_percent(base_top_worst)} mol%和{_percent(base_bottom_worst)} mol%。"
        "原基准本来就是带限制的初步数值结果；扩展冷源和情景条件后需要重新审查，不能解读为此前已完成工业认证。",
        "## 压力、冷源与模型适用范围的联合筛选",
        f"有限压力扫描在 {supported} MPa 下获得了完整的计算候选；"
        f"在 {unsupported or '未记录'} MPa 的尝试中，"
        f"无法在当前 {t_bounds[0]:g}–{t_bounds[1]:g} K 支持范围内闭合完整设计所需的泡点状态。"
        "这些状态被记录为当前模型域内无法继续，而不是相应压力在物理上不可行。"
        "压力调整需要同时考虑冷凝端温差和分离级数／回流的变化，不能仅根据某一纯度指标决定。"
        "常规水冷条件、较高压力路线以及低压热集成路线仍需分别评估；"
        "已有 C3 蒸气再压缩研究可作为后续热集成与控制设计的背景，"
        "本研究没有借用其设备、能耗或工业验证结果。"
        "[Kumar等，2020](https://doi.org/10.1016/j.cherd.2020.04.036)",
        "## 开发残差情景揭示的脆弱性与第二轮设计",
        f"利用训练与验证集合的 {calibration['observations']} 个混合物内点，"
        "我们从预测与实测气相组成的相对挥发度差异构建固定幅度的敏感性情景。"
        f"所用绝对对数残差的 {_percent(calibration['empirical_quantile'], 0)}%经验分位数为 "
        f"{calibration['log_alpha_scale']:.8f}。"
        "该数值用于定义负、零、正扰动幅度，不是置信区间，也不对应90%的产品达标概率。"
        "留出的测试等温线未用于确定该幅度或筛选候选；"
        "开发集合本身用于训练／早停，因而该尺度也不是独立估计的不确定性。",
        f"首轮 {len(round_one)} 个候选中，{stress_one} 个通过全部指定情景。"
        "据此开展第二轮探索性构造：在负向选择性情景下确定级数、进料位置和回流比，"
        "随后保持设备和物流分配不变，使用原始适配 ThermoFormer 及三个情景分别重算。"
        f"第二轮 {len(round_two)} 个候选中，{stress_two} 个通过了这些指定情景，"
        f"其中 {len(cold_stress)} 个还满足10→15°C冷源的端点门。"
        "这里分别检查名义状态下的冷源端点和指定组成情景下的产品要求，"
        "没有重新求解扰动情景的温度，因而不主张每个情景均已验证冷源可行性。"
        "这一反馈调整由确定性程序完成，属于观察首轮结果后的探索性方法改进，"
        "不应包装为预先注册的一次性验证，也不应归因于后续 LLM 审查。",
        counts_table,
        "## 有限候选的工程权衡与数值复核",
        f"在同时通过名义、情景和冷源筛查的候选中，以平衡级数和局部 PR 再沸负荷估计构建有限非支配集合，"
        f"得到 {len(frontier)} 个候选。"
        "表中给出这些候选及原基准，扰动结果来自同一设备在指定情景下的重算。"
        "该集合不代表连续设计空间的全局最优解，也不是经完整能量方程或经济目标求得的最优前沿。",
        table,
        selection_text,
        _optional_pr_text(study, summary),
        "## Agent 的证据审查与停止判断",
        _agent_text(study, agent),
        "## 本节能够支持的结论及工业推进条件",
        "本研究表明，在这一具体计算任务中，产品约束、声明冷源、模型域和选择性情景的联合审查"
        "会改变对名义候选的接受判断，并形成可追溯的修正与复核记录。"
        "证据支持的是有限候选集合中的初步工程筛选与受约束的 Agent 审查。"
        "高纯度混合物 VLE 区域缺少直接观测，极少量杂质的预测尚未获得实验验证；"
        "百级量级的平衡级需求也不能直接转写为实际塔板数或可建造塔高。"
        "进一步的工业评价需要补充高纯区相平衡与过程实验，求解严格 MESH 方程，"
        "并引入板效率、压降、塔径／塔高、传热面积、热泵／制冷配置、控制及经济性。"
        "在完成这些工作之前，不使用工业可行性认证、概率鲁棒性保证或能耗最优等表述。",
        "## 图与源数据",
        "本节配图由 `scripts/plot_c3_engineering.py` 从相同工程汇总生成。"
        "数据表为 `CHAPTER_CANDIDATES.csv`（基准与有限非支配候选）和 `ALL_CANDIDATES_REPORT.csv`（全部候选）。"
        "相平衡实验来源为 Ho 等的丙烯／丙烷二元研究；这些文献 VLE 数据不能称为本研究新增装置实验。"
        "[数据及来源](https://trc.nist.gov/ThermoML/10.1016/j.fluid.2006.03.009.html)",
    ]
    chapter = "\n\n".join(paragraphs) + "\n"
    methods = _methods_text(study, summary, protocol, calibration, construction, training_recipe, training_summary)
    chapter_path, methods_path = study / "CHAPTER.zh-CN.md", study / "METHODS.zh-CN.md"
    chapter_path.write_text(chapter, encoding="utf-8")
    methods_path.write_text(methods, encoding="utf-8")
    _write_csv(study / "CHAPTER_CANDIDATES.csv", [_flat_record(r) for r in [baseline, *frontier]])
    _write_csv(study / "ALL_CANDIDATES_REPORT.csv", [_flat_record(r) for r in records])
    sources = [
        source,
        study / "protocol.json",
        study / "stress_calibration.json",
        study / "scenario_design_protocol.json",
    ]
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),  # noqa: UP017 - Python 3.9
        "source_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
        "counts": {
            "round_one": len(round_one),
            "round_one_scenario_pass": stress_one,
            "round_two": len(round_two),
            "round_two_scenario_pass": stress_two,
            "cold_and_scenario_pass": len(cold_stress),
            "frontier": len(frontier),
            "direct_review_pass": len(direct),
        },
        "selected_candidate_id": selected_id,
        "agent_outcome": agent.get("outcome"),
        "calculation_performed_by_report_generator": False,
        "manuscript_PDFs_modified": False,
    }
    (study / "report_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"chapter": chapter_path, "methods": methods_path}


def _methods_text(
    study: Path,
    summary: dict[str, Any],
    protocol: dict[str, Any],
    calibration: dict[str, Any],
    construction: dict[str, Any],
    recipe: dict[str, Any],
    training: dict[str, Any],
) -> str:
    pressure_text = "、".join(_fmt(p / 1000, 2) for p in protocol["pressures_kpa"])
    baseline = next(r for r in summary["records"] if r["candidate_id"] == summary["baseline_candidate_id"])
    bounds = baseline["utilities"]["metadata"]["equilibrium_provenance"]["research_temperature_bounds_K"]
    cold_sources = protocol["assumptions"]["coolant_scenarios_celsius"]
    cooling_text = "、".join(f"{pair[0]:g}→{pair[1]:g}°C" for pair in cold_sources)
    trained_params = training["trained_parameters"]
    sections = [
        "# Methods补充：C3工程约束筛查及Agent证据审查",
        "## 任务契约与计算边界",
        "研究对象为不含反应或电解质的丙烯／丙烷二元精馏，所有组成均采用摩尔基准。"
        "进料丙烯摩尔分数为0.35，塔顶要求为≥0.996，塔底丙烯含量必须严格<0.01。"
        f"以{protocol['assumptions']['feed_flow_basis_mol_s']:g} mol/s进料为流量基准，"
        "采用饱和液体进料、恒摩尔流、总冷凝器、平衡再沸器及零压降假设。"
        "级数包含再沸器，不包含总冷凝器。原始需求未提供装置与公用工程实测条件，"
        "补充条件均作为显式计算假设保存。",
        "## 相平衡数据、模型适配与数值协议",
        "现有数据集中的90条C3记录来自同一文献，并按完整等温线分组："
        "训练59条（51个混合物内点）、验证15条（13个内点）、测试16条（14个内点）。"
        "293.15 K等温线为留出测试，其余温度的具体分组与原始行号保存在训练协议中。"
        "纯端点不用于构造缺失组分的活度系数标签；来源已核对不等于自动通过热力学一致性测试。"
        "[VLE原始研究及ThermoML记录](https://trc.nist.gov/ThermoML/10.1016/j.fluid.2006.03.009.html)",
        f"通用 ThermoFormer 的分子编码与主体参数保持冻结，仅适配末端相互作用投影的{trained_params}个参数。"
        f"验证集合用于早停，实际选取第{training['selected_epoch']}轮权重；"
        "测试集合不参与权重选择或本次工程情景幅度的确定。"
        "活度系数目标由观测T、P、x、y与固定γ–φ标准态关系导出，不是直接测得的活度系数。"
        "冻结与适配模型均通过同一个γ–φ求解器评价，以保持气相非理想性和纯物性处理一致。"
        "本工程扩展继续使用该已保存专用权重，没有为压力扫描重新训练原模型。",
        "相平衡采用 $y_i\phi_i^V P=x_i\gamma_i f_i^{L,ref}$，"
        "$f_i^{L,ref}=P_i^{sat}\phi_i^{sat}\exp[V_i^{sat}(P-P_i^{sat})/(RT)]$。"
        "气相逸度系数使用PR方程及存在性核查后的ChemSep二元相互作用参数；"
        "纯蒸气压和饱和液体体积采用库内HEOS_FIT相关式，禁用超出相关式范围的外推。"
        f"本研究计算温区进一步限定为{bounds[0]:g}–{bounds[1]:g} K。"
        "每个名义泡点检查组成归一、相平衡残差及有效状态范围，数值收敛不视为全局相稳定性认证。"
        "二元参数的完整适用区间元数据仍不充分，因此计算范围与实验准确性范围分开报告。",
        "## 有限候选构造及第二轮探索性调整",
        f"压力候选为{pressure_text} MPa（绝压）；"
        f"回流因子采用{', '.join(str(v) for v in protocol['reflux_factors'].values())}倍相应最小回流比。"
        "首轮分别使用0.997／0.009和0.9995／0.003两组名义塔顶／塔底丙烯目标构造初始级数与进料位置。"
        "在固定设备、回流比和产品分流量后，另行求解逐级物料衡算，输出纯度由重算获得，"
        "不直接复制设定目标。超出当前支持范围的无根情况保留为失败记录，不判定物理不可行。",
        "观察首轮情景失败后，第二轮采用负向相对挥发度情景关系构造更保守的设备组合。"
        f"该构造使用的对数选择性偏移为{construction['log_alpha_shift']:.8f}。"
        "生成候选随后分别以原始适配模型和全部指定情景重新计算。"
        "这是一项按反馈修正的探索性设计；其成功率属于这一有限候选集合，"
        "不能被解释为独立确认性试验或跨体系泛化性能。",
        "## 开发残差情景及判据",
        "对开发集合的混合物内点，定义"
        "$r=\operatorname{logit}(y_{obs})-\operatorname{logit}(y_{pred})$。"
        "在相同观测温度和液相组成下，预测值来自闭合泡点解，预测压力可能不同于观测压力；"
        "因此该残差表示等温VLE选择性差异，不是固定T、P条件下的参数后验。"
        f"从{calibration['observations']}个内点的$|r|$取{calibration['empirical_quantile']:.2f}经验分位数"
        f"作为尺度$s={calibration['log_alpha_scale']:.8f}$，按线性分位数插值计算。",
        "指定情景为$\operatorname{logit}(y_s)=\operatorname{logit}(y_0)+ks$，"
        "$k\in\{-1,0,1\}$。在各情景中固定级数、进料级、压力、回流比、进料及D/F，"
        "通过连续推进扰动并重算物料衡算获得两端产品。"
        "只有各情景的数值检查及两个产品约束全部通过，才记为该情景门通过。"
        "这些关系是人为定义的敏感性情景，不是新的实验数据，也不是γ–φ热力学模型；"
        "其数值关系残差不得冒充逸度平衡残差。情景不产生可用于换热计算的新温度，"
        "所有温度和公用工程估计仍来自原始适配模型的名义状态。"
        "评估数据的重复使用、向高纯尾端和不同压力条件的外推均未经独立校准，"
        "故不作概率覆盖率或普适鲁棒性解释。",
        "## 直接泡点复核与插值审查",
        "对于有限非支配候选及保留基准，在每一计算液相组成处直接调用原始γ–φ泡点求解器，"
        "比较直接气相组成与插值值，并重新检查逐级及整体物料衡算。"
        "必要时加入直接状态并细化曲线后重新评级，所有细化轮次和未通过记录保留。"
        "原基准中适用的已验证记录明确标记复用，不能写作新的独立计算或重复实验。"
        "直接复核仍属于同一热力学模型的数值检验，不建立实验准确性或全局相稳定性。",
        "## 公用工程筛查及热负荷近似",
        f"对声明冷源{cooling_text}和最小端温差"
        f"{protocol['assumptions']['minimum_terminal_temperature_difference_k']:g} K，"
        "在同一压力、同一塔顶总体组成下求取泡点与露点，检查逆流两端温差。"
        "端点不通过时不返回可行冷却水流量。通过时用有来源的液态水热容积分估计显热流量。"
        "另报告60→50°C热水的独立再沸器端点与显热流量筛查；未假设现场公用工程已经可用，"
        "也未计算制冷COP、压缩机功、泵功或锅炉效率。",
        "热量估计采用独立PR热量模型：$h=\sum_i z_i\int_{298.15K}^{T}C_{p,i}^{ig}\,dT+h_{PR}^{dep}$。"
        "总冷凝器按$Q_C=V_{top}(h_V^{dew}-h_L^{bubble})$估计，"
        "再沸器按$Q_R=B h_L^{bottom}+V h_V^{boilup}-L h_L^{in}$作局部衡算。"
        "该PR焓模型并非ThermoFormer一致焓，也不是完整MESH能量解。"
        "另计算全塔$Fh_F+Q_R-Dh_D-Bh_B-Q_C$及内部各绝热级的净焓流失衡，"
        "以较大局部负荷归一化报告，而不修改流率使其人为归零。"
        "焓参考的一致性仅在非反应且组分守恒的衡算中成立。"
        "[PR相模型](https://thermo.readthedocs.io/thermo.eos_mix.html)；"
        "[热容相关式](https://thermo.readthedocs.io/thermo.heat_capacity.html)",
        "## 有限非支配筛选与实际Agent审查",
        "首先用确定性程序筛除未通过名义约束、指定情景或声明冷源端点门的候选。"
        "在余下候选上，以平衡级数和局部PR再沸负荷估计识别有限非支配关系，"
        "不使用全局最优或严格能耗最优的表述。"
        "LLM随后只从已注册行动中选择比较、读取公用工程证据、读取情景证据、"
        "报告有条件的初步候选或停止；其停止门由确定性约束校验实施。"
        "对相同有限集合明确声明优先较小局部再沸负荷的偏好，级数代价同时保留。"
        "该LLM运行不生成候选、不执行压力扫描，也不新增数值计算。",
        "保存接口尝试、模型实际输出、行动白名单、调用顺序、证据ID、缓存复用、"
        "候选哈希及终止门控。任何无效行动均不执行、不写成成功步骤；"
        "因行动契约说明修订而产生的重跑单独记录。"
        "本节没有无LLM优化器、规则审查器或多次随机运行的对照，"
        "因此不报告Agent相对这些基线的性能优势或通用可靠性概率。",
        "## 可复现性与证据归属",
        f"工程记录位置：`{study.name}/engineering_summary.json`。"
        "模型权重、源数据、训练划分、情景协议及源码哈希随记录保存。"
        f"训练记录中的`test_used_for_selection`为`{str(recipe['test_used_for_selection']).lower()}`，"
        f"原始权重保持不变的记录为`{str(training['original_checkpoint_unchanged']).lower()}`。"
        "历史三个论文案例及其结果保持独立，本生成器只写新增Markdown和表格，不修改论文PDF。",
    ]
    return "\n\n".join(sections) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--study",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "outputs/paper_agent/c3-propane-propylene-20260928/engineering-20260928",
    )
    args = parser.parse_args()
    print(json.dumps({key: str(path) for key, path in generate_reports(args.study).items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
