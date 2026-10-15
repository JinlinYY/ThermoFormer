# ruff: noqa: E402
"""Frozen, manually specified within-case language pilot; not a held-out benchmark."""

from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPOSITORY_ROOT / "Web/ThermoFormer-web/backend"
for _directory in (REPOSITORY_ROOT, BACKEND_ROOT):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))


from typing import Any

from paper_agent.reliability import SPECS


def reliability_tasks() -> list[dict[str, Any]]:
    prompts = {
        "binary": [
            "按论文协议计算正庚烷/正壬烷二元精馏。压力101.3 kPa，饱和液体进料1 mol/s；"
            "进料摩尔分数：正庚烷0.466，正壬烷0.534。馏出液正庚烷摩尔分数至少0.995，"
            "正庚烷回收率至少0.98，固定回流比0.9280520481600283。执行原组成网格和插值敏感性核查。",
            "Run the registered binary distillation protocol for n-heptane and n-nonane. "
            "Saturated-liquid feed: 1 mol/s, mole fractions n-heptane 0.466 and n-nonane 0.534. "
            "Pressure 101.3 kPa. Require n-heptane distillate purity >=0.995 (mole fraction) and "
            "n-heptane recovery >=0.98 (fraction). Hold reflux at 0.9280520481600283.",
            "正庚烷/正壬烷精馏采用论文已登记协议。压力101300 Pa；饱和液体进料60 mol/min，"
            "正庚烷46.6 mol%，正壬烷53.4 mol%。塔顶正庚烷纯度至少99.5 mol%，"
            "正庚烷回收率至少98%；回流比固定0.9280520481600283。",
            "请分析正壬烷与正庚烷的二元精馏：进料为饱和液体，正壬烷摩尔分数0.534、"
            "正庚烷摩尔分数0.466，总进料1 mol/s，压力101.3 kPa。"
            "目标组分是正庚烷，其回收率至少98%，塔顶纯度至少99.5 mol%；"
            "回流比0.9280520481600283。请执行论文协议。",
            "Use the paper's binary protocol. Product requirement: n-heptane recovery >=98% "
            "and overhead n-heptane purity >=99.5 mol%. Fixed reflux ratio: 0.9280520481600283. "
            "Feed (saturated liquid): 3.6 kmol/h; n-nonane 53.4 mol%, n-heptane 46.6 mol%. "
            "Operating pressure: 1.013 bar. Include the interpolation audit.",
        ],
        "extractive": [
            "执行仲丁醇/乙酸仲丁酯体系以DMF为溶剂的论文萃取精馏边界核查协议。"
            "压力101.3 kPa；有机进料1 mol/s，其中仲丁醇摩尔分数0.5，乙酸仲丁酯摩尔分数0.5；"
            "两股进料均为饱和液体。DMF/有机进料质量比32:1，固定回流比48。"
            "要求塔顶乙酸仲丁酯摩尔分数至少0.995，乙酸仲丁酯回收率至少0.98。",
            "Execute the registered extractive-distillation boundary protocol with DMF solvent. "
            "Pressure 101.3 kPa, organic feed 1 mol/s: sec-butyl alcohol mole fraction 0.5, "
            "sec-butyl acetate mole fraction 0.5. Both feeds are saturated liquids. "
            "DMF/organic-feed MASS ratio 32:1, reflux 48. Require sec-butyl acetate overhead "
            "purity >=0.995 (mole fraction), sec-butyl acetate recovery >=0.98 (fraction).",
            "萃取精馏边界核查，溶剂DMF；压力101300 Pa。有机进料60 mol/min，"
            "仲丁醇50 mol%、乙酸仲丁酯50 mol%；两股进料均为饱和液体。"
            "DMF/有机进料32 kg/kg，回流比48，乙酸仲丁酯塔顶纯度至少99.5 mol%，回收率至少98%。",
            "乙酸仲丁酯/仲丁醇/DMF萃取精馏采用论文边界协议。乙酸仲丁酯塔顶纯度至少99.5 mol%，"
            "乙酸仲丁酯回收率至少98%。有机进料1 mol/s：乙酸仲丁酯摩尔分数0.5、仲丁醇摩尔分数0.5。"
            "压力101.3 kPa，两股进料均为饱和液体，DMF/有机进料质量比32:1，回流比48。",
            "Use the paper boundary protocol for extractive distillation. At 1.013 bar, feed "
            "3.6 kmol/h of sec-butyl acetate (50 mol%) and 2-butanol (50 mol%). "
            "Use N,N-dimethylformamide (DMF) at a solvent/organic-feed mass ratio of 32:1. "
            "Both feeds are saturated liquids; reflux ratio 48. Overhead sec-butyl acetate "
            "purity >=99.5 mol% and sec-butyl acetate recovery >=98%.",
        ],
        "extraction": [
            "按论文协议进行正庚烷/苯/糠醛错流萃取。温度303.15 K，压力101.3 kPa；"
            "新鲜烃进料1 mol/s，正庚烷摩尔分数0.7333333333333333、苯摩尔分数0.2666666666666667；"
            "总新鲜糠醛1.5 mol/s。要求苯回收率至少0.70，初始正庚烷保留率至少0.80。",
            "Run the registered crossflow extraction protocol with furfural solvent at 303.15 K "
            "and 101.3 kPa. Hydrocarbon feed 1 mol/s; mole fractions n-heptane 0.7333333333333333 "
            "and benzene 0.2666666666666667. Total fresh furfural 1.5 mol/s. Require benzene "
            "recovery >=0.70 (fraction) and initial n-heptane retention >=0.80 (fraction).",
            "糠醛用于正庚烷/苯错流萃取，执行论文协议。温度30 degC、压力101300 Pa；"
            "新鲜烃进料60 mol/min，正庚烷73.33333333333333 mol%，苯26.66666666666667 mol%；"
            "总新鲜糠醛90 mol/min。苯回收率至少70%，初始正庚烷保留率至少80%。",
            "请执行苯/正庚烷/糠醛错流萃取论文协议。苯回收率至少70%，初始正庚烷保留率至少80%。"
            "新鲜烃进料1 mol/s，其中苯摩尔分数0.2666666666666667、正庚烷摩尔分数0.7333333333333333。"  # noqa: E501 -- fixed report text or request text
            "总新鲜糠醛1.5 mol/s；压力101.3 kPa，温度303.15 K。",
            "For the paper crossflow protocol require >=80% retention of initial n-heptane "
            "and >=70% benzene recovery. Fresh hydrocarbon feed: 3.6 kmol/h, benzene "
            "26.66666666666667 mol% and n-heptane 73.33333333333333 mol%. Total fresh furfural "
            "5.4 kmol/h. Operate at 30 degC and 1.013 bar.",
        ],
    }
    tasks: list[dict[str, Any]] = []
    for case, variants in prompts.items():
        for i, prompt in enumerate(variants):
            tasks.append(
                dict(
                    task_id=f"{case}-equivalent-{i}",
                    case=case,
                    kind="equivalent",
                    prompt=prompt,
                    expected_values=SPECS[case],
                    expected_status="ready",
                    expected_issue_fields=[],
                )
            )
    bad = [
        ("binary", "missing", prompts["binary"][0].replace("压力101.3 kPa，", ""), ["pressure"]),
        (
            "binary",
            "conflict",
            prompts["binary"][0] + "同一操作压力另指定为150 kPa；两项均要求生效。",
            ["pressure"],
        ),
        (
            "binary",
            "conflict",
            prompts["binary"][0].replace("正壬烷0.534", "正壬烷0.634"),
            ["feed_composition", "feed_fraction:n_heptane", "feed_fraction:n_nonane"],
        ),
        (
            "extractive",
            "ambiguous",
            prompts["extractive"][0].replace("质量比32:1", "用量比32:1"),
            ["solvent_ratio:DMF"],
        ),
        (
            "extractive",
            "missing",
            prompts["extractive"][0].replace("，乙酸仲丁酯回收率至少0.98", ""),
            ["recovery:sec_butyl_acetate"],
        ),
        (
            "extractive",
            "conflict",
            prompts["extractive"][0] + "同时要求DMF/有机进料质量比16:1；两项均要求生效。",
            ["solvent_ratio:DMF"],
        ),
        (
            "extraction",
            "missing",
            prompts["extraction"][0].replace("总新鲜糠醛1.5 mol/s。", ""),
            ["solvent_flow:furfural"],
        ),
        (
            "extraction",
            "conflict",
            prompts["extraction"][0] + "同一操作温度另要求为298.15 K；两项均要求生效。",
            ["temperature"],
        ),
        (
            "extraction",
            "conflict",
            prompts["extraction"][0].replace(
                "苯摩尔分数0.2666666666666667", "苯摩尔分数0.3666666666666667"
            ),
            ["feed_composition", "feed_fraction:n_heptane", "feed_fraction:benzene"],
        ),
    ]
    for i, (case, kind, prompt, fields) in enumerate(bad):
        tasks.append(
            dict(
                task_id=f"{case}-{kind}-{i}",
                case=case,
                kind=kind,
                prompt=prompt,
                expected_values=None,
                expected_status="clarify",
                expected_issue_fields=fields,
            )
        )
    return tasks
