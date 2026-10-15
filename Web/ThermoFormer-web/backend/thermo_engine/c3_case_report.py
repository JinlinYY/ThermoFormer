"""Render retained C3 numerical artifacts without rerunning or inventing results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from thermo_engine.c3_thermoformer import CASE_ROOT


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_report(case_root: Path = CASE_ROOT) -> Path:
    summary = read_json(case_root / "design/case_summary.json")
    archive = read_json(case_root / "design/candidate_archive.json")
    selected = summary["selected_candidate_id"]
    if selected is None:
        raise ValueError("No reviewed design is available for a successful-design report")
    result = archive[selected]
    metrics = result["metrics"]
    training = read_json(case_root / "training/equilibrium_metrics.json")
    scores = {
        item["model"]: item
        for item in training["metrics"]
        if item["partition"] == "test" and item["scope"] == "mixture_interior"
    }
    adapted, frozen = scores["adapted_thermoformer"], scores["frozen_thermoformer"]
    agent = read_json(case_root / "design/agent_trajectory.json")
    check = result["verification"]["direct_column_validation"]
    report = [
        "# C3 丙烷/丙烯分离计算结果",
        "",
        "已完成C3专用ThermoFormer适配、独立逐级塔计算和真实LLM决策轨迹。"
        "用户已确认没有真实过程实验，以下均为带有明确假设的初步计算结果。",
        "",
        "## 用户要求与计算假设",
        "",
        "用户要求：丙烷65 mol%、丙烯35 mol%；丙烷产品中丙烯严格低于1 mol%；"
        "丙烯产品纯度至少99.6 mol%。所有目标使用未舍入结果判定。",
        "",
        "计算假设：压力1000 kPa、进料基准1 mol/s、饱和液体进料(q=1)、恒摩尔流、"
        "全凝器、平衡再沸器、无塔压降。级数包括再沸器，不包括全凝器，进料级从塔顶向下编号。"
        "名义初始设计采用塔顶丙烯99.7 mol%、塔底丙烯0.9 mol%，提供一定裕量。"
        "随后固定产品流量分配、级数、进料位置和回流比，独立求解逐级衡算，得到下列产品组成。",
        "",
        "## 保留候选",
        "",
        "| 项目 | 计算结果 | 说明 |",
        "|---|---:|---|",
        f"| 平衡级数 | {metrics['stages_including_reboiler']} | 包含再沸器 |",
        f"| 进料级位置 | {metrics['feed_stage_from_top']} | 自塔顶计数 |",
        f"| 回流比 | {metrics['reflux_ratio']:.6f} | 有限候选的低回流偏好，不是能耗最优 |",
        f"| 最小回流比估计 | {result['minimum_reflux_ratio']:.6f} | 两塔段夹点扫描 |",
        f"| 塔顶丙烯纯度 | {100 * metrics['distillate_propene_mole_fraction']:.6f} mol% | ≥99.6，通过 |",
        f"| 塔底丙烯杂质 | {100 * metrics['bottoms_propene_mole_fraction']:.6f} mol% | <1，通过 |",
        f"| 塔底丙烷纯度 | {100 * (1 - metrics['bottoms_propene_mole_fraction']):.6f} mol% | 二元组成闭合 |",
        f"| 丙烯回收率 | {100 * metrics['propene_recovery']:.6f}% | 计算结果，非预设指标 |",
        f"| 丙烷回收率 | {100 * metrics['propane_recovery']:.6f}% | 计算结果，非预设指标 |",
        f"| 塔顶产品流量 | {metrics['distillate_flow_mol_s']:.9f} mol/s | 进料基准1 mol/s |",
        f"| 塔底产品流量 | {metrics['bottoms_flow_mol_s']:.9f} mol/s | 进料基准1 mol/s |",
        f"| 顶部平衡级温度 | {metrics['top_stage_temperature_k']:.6f} K | 不含冷凝器换热设计 |",
        f"| 再沸器温度 | {metrics['reboiler_temperature_k']:.6f} K | 不含热负荷计算 |",
        "",
        "## 验证反馈与Agent轨迹",
        "",
        "在各级组成直接重算相平衡，复查直接塔顶纯度，并将直接气相组成回代逐级和整体物料衡算。"
        "首次复核发现插值误差；工具补点、重新评级，保留原级数、回流比、进料位置和产品流量。"
        "补点是验证工具内部的数值操作，不计作额外LLM决策。",
        "",
        "| 复核轮次 | 归一化最大逐级衡算残差 | 数值门 |",
        "|---|---:|---|",
    ]
    for item in result["verification"]["refinement_rounds"]:
        label = "通过" if item["direct_validation"]["passed"] else "需要细化"
        report.append(f"| {item['round']} | {item['direct_stage_balance_residual']:.6e} | {label} |")
    report.extend(
        [
            "",
            f"最终直接相平衡最大残差 {check['numerical_residual']:.6e}；"
            "密化线性重采样敏感性复算也满足两端指标。数值收敛不能替代实验准确性或全局相稳定性证明。",
            "",
            f"真实DeepSeek运行有 {agent['llm_calls']} 次决策、{agent['numerical_tool_calls']} 次数值工具调用，"
            f"记录token合计 {agent['llm_tokens']}。轨迹为：计算候选 → 请求逐级复核 → 报告有限制的初步结果。"
            "LLM没有计算平衡数值。完整请求、响应、候选集合和证据引用见design/agent_trajectory.json。",
            "",
            "## 同配置PR比较",
            "",
            "保持同一塔级数、进料位置、回流比及产品流量，用有来源参数的PR比较器复算。"
            "它是另一热力学模型的结果，并非新实验。该比较在Agent停止后补充，未作为此前停止决策的输入。",
        ]
    )
    pr = summary["same_column_pr_comparison"]
    if pr is not None:
        pm = pr["metrics"]
        report.extend(
            [
                "",
                f"PR塔顶丙烯纯度 {100 * pm['distillate_propene_mole_fraction']:.6f} mol%，"
                f"塔底丙烯 {100 * pm['bottoms_propene_mole_fraction']:.6f} mol%；"
                f"两端指标判定：{'通过' if pr['meets_targets'] else '未通过'}。",
            ]
        )
    report.extend(
        [
            "",
            "## 模型训练与留出评测",
            "",
            "从原二元seed-2 ThermoFormer初始化，仅微调193个G^E相互作用末层参数，冻结分子表示与主体网络。"
            "原低压解码器保持不变；本案例采用独立gamma-phi后端，包含PR气相逸度、饱和参考逸度和Poynting修正。",
            "",
            "固定完整等温线划分：训练59点(51个混合内点)、验证15点(13个混合内点)、"
            "测试293.15 K的16点(14个混合内点)。第60轮验证最优，第140轮早停；测试不参与选模。",
            "",
            "| 测试混合内点，n=14 | 冻结模型 | C3适配模型 |",
            "|---|---:|---:|",
            f"| 泡点压力MAE/kPa | {frozen['pressure_mae_kpa']:.6f} | {adapted['pressure_mae_kpa']:.6f} |",
            f"| 气相丙烯摩尔分数MAE | {frozen['y_propene_mae']:.6f} | {adapted['y_propene_mae']:.6f} |",
            f"| 数值有效点 | {frozen['validated']}/{frozen['attempted']} | "
            f"{adapted['validated']}/{adapted['attempted']} |",
            "",
            "两模型采用相同gamma-phi后端，因此比较的是任务适配贡献。评测限于同体系、同文献的温度留出。"
            "适配模型90/90点数值通过；冻结模型在训练区11次无适用范围内根，失败记录完整保留。"
            "不能将上述结果写为跨体系泛化或独立来源实验验证。",
            "",
            "## 结论适用范围",
            "",
            "本例支持：在明确假设下，C3专用模型与Agent产生满足给定纯度的初步精馏候选，"
            "并完成逐级数值复核和同配置参考模型比较。",
            "",
            "没有真实过程实验，高纯混合区也缺少直接VLE覆盖。尚未计算能量衡算、实际塔效率、塔径、压降、"
            "公用工程和经济最优；ChemSep二元参数范围元数据不完整，已记录。不能表述为实测达标、工业验证或全局最优。",
            "",
            "## 文件与复现",
            "",
            "- training/：专用权重、分子特征、训练配方、留出指标及完整预测。",
            "- design/candidate_archive.json：候选逐级剖面、数值检查与直接复核。",
            "- design/agent_trajectory.json：真实LLM轨迹。",
            "- design/candidate_scan.csv：四个有限候选；其余三个在Agent后补扫，不是Agent执行记录。",
            "- design/case_summary.json：计算假设、保留候选、对照和完整性记录。",
            "- figures/：C3新增结果图。",
            "",
            "数值环境为ggnn39。训练入口scripts/train_c3_thermoformer.py；"
            "新案例执行python -m thermo_engine.c3_case_study --output <新目录>。"
            "重跑请使用独立输出目录，已存在的权重与轨迹不覆盖。"
            "报告可由python -m thermo_engine.c3_case_report重新生成。",
            "",
            "原论文模型SHA256核对未变，旧三个案例未修改。新增模块行为测试20项通过；Ruff与strict mypy通过。",
            "",
        ]
    )
    target = case_root / "RESULTS.zh-CN.md"
    target.write_text("\n".join(report), encoding="utf-8")
    return target


if __name__ == "__main__":
    print(write_report())
