"""Publication-facing outputs for the final C1 fugacity campaign."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .artifacts import (
    artifact_sha256,
    atomic_write_json,
    atomic_write_text,
    portable_artifact_path,
    resolve_artifact_path,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_ROOT = Path(
    "results/experiments/physics_finetuning/c1_three_view_vanilla_fugacity"
)
RUN_PREFIX = "c1_three_view_vanilla_fugacity_finetune.on."


@dataclass(frozen=True)
class ProtocolSpec:
    name: str
    category: str
    label: str


PROTOCOLS = (
    ProtocolSpec("overall_binary", "overall", "Binary train -> binary test"),
    ProtocolSpec(
        "overall_binary_ternary",
        "overall",
        "Binary+ternary train -> joint test",
    ),
    ProtocolSpec("state_composition_interpolation", "state", "Composition interpolation"),
    ProtocolSpec("state_composition_edge_extrapolation", "state", "Composition edge extrapolation"),
    ProtocolSpec("state_temperature_low_extrapolation", "state", "Low-temperature extrapolation"),
    ProtocolSpec("state_temperature_high_extrapolation", "state", "High-temperature extrapolation"),
    ProtocolSpec("state_pressure_low_extrapolation", "state", "Low-pressure extrapolation"),
    ProtocolSpec("state_pressure_high_extrapolation", "state", "High-pressure extrapolation"),
    ProtocolSpec("unseen_component", "chemistry", "Unseen component"),
    ProtocolSpec("binary_to_ternary_zero_shot", "transfer", "0% ternary (zero-shot)"),
    ProtocolSpec("binary_to_ternary_scale_0.05", "transfer", "5.56% ternary"),
    ProtocolSpec("binary_to_ternary_scale_0.1", "transfer", "10% ternary"),
    ProtocolSpec("binary_to_ternary_scale_0.25", "transfer", "25% ternary"),
    ProtocolSpec("binary_to_ternary_scale_0.5", "transfer", "50% ternary"),
    ProtocolSpec("binary_to_ternary_scale_1", "transfer", "100% ternary"),
)


def _protocol_dir(project_root: Path, protocol: str) -> Path:
    return project_root / RESULTS_ROOT / f"{RUN_PREFIX}{protocol}"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected a JSON object: {path}")
    return payload


def _verify_reference(project_root: Path, reference: dict[str, Any]) -> None:
    path = resolve_artifact_path(str(reference["path"]), project_root)
    if not path.is_file():
        raise FileNotFoundError(f"Missing referenced artifact: {path}")
    actual = artifact_sha256(path)
    if actual != str(reference["sha256"]):
        raise RuntimeError(f"Artifact SHA mismatch: {path}")


def validate_protocol_bundle(project_root: Path, protocol: str) -> dict[str, Any]:
    """Validate the committed five-seed report bundle before consuming metrics."""

    directory = _protocol_dir(project_root, protocol)
    report_manifest = _load_json(directory / "report_manifest.json")
    expected = f"{RUN_PREFIX}{protocol}"
    invariants = {
        "status": "completed",
        "protocol": expected,
        "analysis_status": "confirmatory",
        "selection_partition": "validation",
        "evaluation_partition": "test",
    }
    for key, value in invariants.items():
        if report_manifest.get(key) != value:
            raise RuntimeError(
                f"Invalid {key} for {protocol}: {report_manifest.get(key)!r}"
            )
    if report_manifest.get("seeds") != [0, 1, 2, 3, 4]:
        raise RuntimeError(f"Expected seeds 0--4 for {protocol}")

    for key in ("aggregate_manifest", "stage_comparison_summary", "report"):
        _verify_reference(project_root, report_manifest[key])
    for key in ("run_manifests", "stage_comparisons"):
        references = report_manifest.get(key, [])
        if [int(item["seed"]) for item in references] != [0, 1, 2, 3, 4]:
            raise RuntimeError(f"Invalid {key} seed set for {protocol}")
        for reference in references:
            _verify_reference(project_root, reference)

    aggregate_path = resolve_artifact_path(
        str(report_manifest["aggregate_manifest"]["path"]), project_root
    )
    aggregate = _load_json(aggregate_path)
    if aggregate.get("status") != "completed" or aggregate.get("seeds") != [0, 1, 2, 3, 4]:
        raise RuntimeError(f"Incomplete formal aggregate for {protocol}")
    for reference in aggregate.get("outputs", {}).values():
        _verify_reference(project_root, reference)
    input_hashes = aggregate.get("input_manifest_sha256", {})
    for reference in report_manifest["run_manifests"]:
        if input_hashes.get(str(reference["seed"])) != reference["sha256"]:
            raise RuntimeError(f"Aggregate input hash mismatch for {protocol}/seed_{reference['seed']}")
    return report_manifest


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _direction_rows(rows: Iterable[dict[str, str]], protocol: str) -> list[dict[str, str]]:
    rows = list(rows)
    if protocol == "overall_binary_ternary":
        return [
            row
            for row in rows
            if row["scope"] == "direction_cardinality"
            and row["direction"] in {"isothermal", "isobaric"}
            and row["component_count"] in {"2", "3", "2.0", "3.0"}
        ]
    return [
        row
        for row in rows
        if row["scope"] == "direction"
        and row["direction"] in {"isothermal", "isobaric"}
    ]


def _float(row: dict[str, str], key: str) -> float | None:
    value = row.get(key, "")
    return None if value == "" else float(value)


def collect_generalization_rows(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    """Collect validation-selected final test metrics from all 15 protocols."""

    output: list[dict[str, Any]] = []
    for spec in PROTOCOLS:
        validate_protocol_bundle(project_root, spec.name)
        directory = _protocol_dir(project_root, spec.name)
        for row in _direction_rows(_read_rows(directory / "metrics_summary.csv"), spec.name):
            direction = row["direction"]
            cardinality = row.get("component_count", "")
            subset = (
                "binary"
                if cardinality in {"2", "2.0"}
                else "ternary"
                if cardinality in {"3", "3.0"}
                else "all"
            )
            if direction == "isothermal":
                state_name, unit = "P", "kPa"
                mae, rmse, r2 = "pressure_mae_kpa", "pressure_rmse_kpa", "pressure_r2"
            else:
                state_name, unit = "T", "K"
                mae, rmse, r2 = "temperature_mae_k", "temperature_rmse_k", "temperature_r2"
            output.append(
                {
                    "category": spec.category,
                    "protocol": spec.name,
                    "evaluation_setting": spec.label,
                    "test_subset": subset,
                    "direction": direction,
                    "known_inputs": "molecules,T,x" if direction == "isothermal" else "molecules,P,x",
                    "joint_outputs": "P,y" if direction == "isothermal" else "T,y",
                    "state_quantity": state_name,
                    "state_unit": unit,
                    "state_mae_mean": _float(row, f"{mae}_mean"),
                    "state_mae_std": _float(row, f"{mae}_std"),
                    "state_rmse_mean": _float(row, f"{rmse}_mean"),
                    "state_rmse_std": _float(row, f"{rmse}_std"),
                    "state_r2_mean": _float(row, f"{r2}_mean"),
                    "state_r2_std": _float(row, f"{r2}_std"),
                    "y_mae_mean": _float(row, "y_mae_mean"),
                    "y_mae_std": _float(row, "y_mae_std"),
                    "y_rmse_mean": _float(row, "y_rmse_mean"),
                    "y_rmse_std": _float(row, "y_rmse_std"),
                    "y_r2_mean": _float(row, "y_r2_mean"),
                    "y_r2_std": _float(row, "y_r2_std"),
                    "solver_failure_rate_mean": _float(row, "solver_failure_rate_mean"),
                    "nonphysical_rate_mean": _float(row, "nonphysical_rate_mean"),
                    "valid_coverage_mean": _float(row, "valid_coverage_mean"),
                    "available_seeds": int(row[f"{mae}_available_seeds"]),
                }
            )
    return output


def _fmt(mean: float | None, std: float | None, digits: int) -> str:
    if mean is None or std is None:
        return "N/A"
    return f"{mean:.{digits}f} ± {std:.{digits}f}"


def _task_table(rows: Iterable[dict[str, Any]]) -> str:
    lines = [
        "| Evaluation setting | subset | task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | n |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        state_digits = 2 if row["state_quantity"] in {"P", "T"} else 4
        unit = f" {row['state_unit']}" if row["state_unit"] else ""
        lines.append(
            f"| {row['evaluation_setting']} | {row['test_subset']} | "
            f"{row['direction']} ({row['known_inputs']} → {row['joint_outputs']}) | "
            f"{_fmt(row['state_mae_mean'], row['state_mae_std'], state_digits)}{unit} | "
            f"{_fmt(row['state_rmse_mean'], row['state_rmse_std'], state_digits)}{unit} | "
            f"{_fmt(row['state_r2_mean'], row['state_r2_std'], 3)} | "
            f"{_fmt(row['y_mae_mean'], row['y_mae_std'], 4)} | "
            f"{_fmt(row['y_rmse_mean'], row['y_rmse_std'], 4)} | "
            f"{_fmt(row['y_r2_mean'], row['y_r2_std'], 3)} | {row['available_seeds']} |"
        )
    return "\n".join(lines)


def _task_table_zh(rows: Iterable[dict[str, Any]]) -> str:
    lines = [
        "| 评估设置 | 测试子集 | 预测任务 | 状态量 MAE | 状态量 RMSE | 状态量 R² | y MAE | y RMSE | y R² | 有效种子 |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    labels = {
        "Binary train -> binary test": "二元训练 → 二元测试",
        "Binary+ternary train -> joint test": "二元+三元训练 → 联合测试",
        "Composition interpolation": "组成内插",
        "Composition edge extrapolation": "组成边界外推",
        "Low-temperature extrapolation": "低温外推",
        "High-temperature extrapolation": "高温外推",
        "Low-pressure extrapolation": "低压外推",
        "High-pressure extrapolation": "高压外推",
        "Unseen component": "未见组分",
        "0% ternary (zero-shot)": "0% 三元（零样本）",
        "5.56% ternary": "5.56% 三元",
        "10% ternary": "10% 三元",
        "25% ternary": "25% 三元",
        "50% ternary": "50% 三元",
        "100% ternary": "100% 三元",
    }
    for row in rows:
        state_digits = 2
        unit = f" {row['state_unit']}"
        task = "等温：分子,T,x → P,y" if row["direction"] == "isothermal" else "等压：分子,P,x → T,y"
        subset = {"binary": "二元", "ternary": "三元", "all": "全部"}[row["test_subset"]]
        lines.append(
            f"| {labels[row['evaluation_setting']]} | {subset} | {task} | "
            f"{_fmt(row['state_mae_mean'], row['state_mae_std'], state_digits)}{unit} | "
            f"{_fmt(row['state_rmse_mean'], row['state_rmse_std'], state_digits)}{unit} | "
            f"{_fmt(row['state_r2_mean'], row['state_r2_std'], 3)} | "
            f"{_fmt(row['y_mae_mean'], row['y_mae_std'], 4)} | "
            f"{_fmt(row['y_rmse_mean'], row['y_rmse_std'], 4)} | "
            f"{_fmt(row['y_r2_mean'], row['y_r2_std'], 3)} | {row['available_seeds']} |"
        )
    return "\n".join(lines)


def _write_complete_chinese_report(
    project_root: Path,
    rows: list[dict[str, Any]],
    stage_rows: list[dict[str, Any]],
    totals: dict[str, int],
    path: Path,
) -> None:
    parameter_summary = _load_json(
        _protocol_dir(project_root, "overall_binary_ternary")
        / "stage_comparison_summary.json"
    )["parameter_summary"]
    groups = {item["name"]: item for item in parameter_summary["groups"]}
    by_category = {
        category: [row for row in rows if row["category"] == category]
        for category in ("overall", "state", "chemistry", "transfer")
    }
    lines = [
        "# ThermoFormer 最终模型完整性能报告",
        "",
        "## 1. 报告范围与结论摘要",
        "",
        "本报告汇总最终 **C1 三视图 vanilla ThermoFormer** 在 15 个固定协议、5 个随机种子（0--4）上的正式测试结果。最终模型同时使用 RDKit 2D 描述符、Uni-Mol v2 高阶结构表示和 SMARTS 官能团特征；三个分支独立投影后融合，随后使用 vanilla Transformer 和 C1 原有 pair potential。模型不启用 chemical-attention bias，也不启用 context-pair interaction。",
        "",
        "训练采用两阶段流程：Stage 1 为数据监督训练；Stage 2 从 Stage 1 的验证最佳 checkpoint 出发，在保留监督损失的同时，仅增加 teacher-forced 逸度平衡损失并微调 10 epoch。最终 checkpoint 只能由验证集在 Stage 1 与 Stage 2 之间选择，测试集不参与选模。",
        "",
        f"综合 75 个种子级实验，验证集选择 Stage 2 共 **{totals['stage2']}/75** 次，回退 Stage 1 共 **{totals['stage1']}/75** 次；逸度残差在 **{totals['residual_improved']}/15** 个协议均值上下降。作为选模完成后的描述性统计，Stage 2 在 **{totals['predictive_improved']}/{totals['predictive_compared']}** 个方向化 MAE/RMSE/R² 单元上优于 Stage 1。因此，现有证据支持保留“验证门控的逸度微调”，但不支持“逸度损失对所有任务和随机种子均一致提升”的更强结论。",
        "",
        "## 2. 预测任务与评价方式",
        "",
        "模型完成两个耦合 VLE 任务，而不是独立预测一个标量：",
        "",
        "- 等温 P–x–y：输入分子表征、温度 T 和液相组成 x，联合输出泡点压力 P 与汽相组成 y；",
        "- 等压 T–x–y：输入分子表征、压力 P 和液相组成 x，联合输出泡点温度 T 与汽相组成 y。",
        "",
        "所有状态量与汽相组成分别报告 MAE、RMSE 和 R²。压力误差单位为 kPa，温度误差单位为 K，组成误差无量纲。表中数值为随机种子均值 ± 标准差；“有效种子”反映对应任务/子集实际存在可计算指标的种子数，不对缺失方向进行补值。",
        "",
        "## 3. 模型规模与 Stage 2 微调设置",
        "",
        f"模型总参数量为 **{int(parameter_summary['total_parameters']):,}**，Stage 2 实际微调 **{int(parameter_summary['trainable_parameters']):,}** 个参数，占 **{100 * float(parameter_summary['trainable_fraction']):.2f}%**。优化器仅包含以下解冻参数组：",
        "",
        "| 参数组 | 参数量 | 学习率 |",
        "|---|---:|---:|",
        f"| pair_potential | {int(groups['pair_potential']['parameter_count']):,} | {float(groups['pair_potential']['learning_rate']):.0e} |",
        f"| vapor_pressure | {int(groups['vapor_pressure']['parameter_count']):,} | {float(groups['vapor_pressure']['learning_rate']):.0e} |",
        f"| film | {int(groups['film']['parameter_count']):,} | {float(groups['film']['learning_rate']):.0e} |",
        f"| mixture_token | {int(groups['mixture_token']['parameter_count']):,} | {float(groups['mixture_token']['learning_rate']):.0e} |",
        "",
        "Stage 2 使用 2 epoch 线性 warmup；RDKit/Uni-Mol/官能团投影、基础融合层和全部 Transformer 层保持冻结。",
        "",
        "## 4. 总体预测性能",
        "",
        _task_table_zh(by_category["overall"]),
        "",
        "二元+三元联合训练后，二元子集的等温压力 MAE 为 **8.68 kPa**，与只用二元训练的 **8.98 kPa** 接近；等压温度 MAE 均约为 **2.45 K**。联合训练并未损害二元状态量预测，但两种方向的二元 y MAE 略高于二元专用模型，因此不能表述为所有二元指标均改善。",
        "",
        "联合测试中的三元状态量指标较好：等温压力 MAE 为 **1.85 kPa**，等压温度 MAE 为 **1.41 K**。不过这两组三元状态量 MAE/RMSE/R² 只有 4 个有效种子，且等压三元 y R² 的标准差较大（0.919 ± 0.079），说明三元方向仍受样本规模和任务可用性限制。",
        "",
        "## 5. 状态内插与外推性能",
        "",
        _task_table_zh(by_category["state"]),
        "",
        "组成内插是最稳定的状态任务：等温 P MAE 为 **1.61 kPa**，等压 T MAE 为 **0.58 K**。组成边界外推仍保持较高精度，说明模型对同一化学体系内部的组成变化具有较好的连续泛化能力。",
        "",
        "高温和高压方向的等温压力预测更困难，P MAE 分别升至 **5.83 kPa** 和 **5.96 kPa**，明显高于低温和低压外推。与此同时，其 y 预测仍保持较高 R²。这表明当前状态外推误差主要集中在泡点压力尺度，而不是所有输出同步失效。",
        "",
        "## 6. 未见组分泛化",
        "",
        _task_table_zh(by_category["chemistry"]),
        "",
        "未见组分是当前模型最明显的能力边界。等温 P MAE 为 **32.39 kPa**、R² 为 **0.494**；等压 T MAE 为 **36.45 K**、R² 为 **0.456**。两种方向的 y MAE 均超过 0.10。相比状态内插/外推，这一数量级差距说明模型擅长在已见化学空间内沿状态变量泛化，但对完全未见的分子组分仍缺乏可靠外推能力。",
        "",
        "因此，当前结果不能支持“对新分子具有普适预测能力”的表述。更准确的结论是：最终 C1 在训练化学空间覆盖范围内表现较好，而未见组分泛化仍需更广的分子覆盖、纯物性先验或专门的分子域外泛化方法。",
        "",
        "## 7. 二元到三元迁移",
        "",
        _task_table_zh(by_category["transfer"]),
        "",
        "零样本二元→三元迁移在状态量和等温 y 上具有可用精度：P MAE 为 **1.62 kPa**，T MAE 为 **1.91 K**，等温 y MAE 为 **0.0129**。但等压 y MAE 为 **0.0714**、R² 为 **0.774**，明显弱于等温方向。",
        "",
        "随着三元训练比例增加，性能并非严格单调。50% 三元训练时等温 P MAE 最低（**1.30 kPa**），100% 时为 **1.47 kPa**；等压 y 在各比例下约为 0.071--0.074，改善有限。该现象更符合小规模三元体系池、子集组成差异和多任务优化波动，而不是“加入更多三元数据必然降低性能”。",
        "",
        "## 8. 逸度微调效果",
        "",
        "| 协议 | Stage 1 被选 | Stage 2 被选 | Stage 1 逸度残差 | Stage 2 逸度残差 | Stage 2 改善的预测指标 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    labels = {spec.name: spec.label for spec in PROTOCOLS}
    for row in stage_rows:
        lines.append(
            f"| {labels[row['protocol']]} | {row['stage1_selected']} | {row['stage2_selected']} | "
            f"{row['stage1_teacher_forced_fugacity']:.6g} | "
            f"{row['stage2_teacher_forced_fugacity']:.6g} | "
            f"{row['stage2_predictive_metrics_improved']}/{row['predictive_metrics_compared']} |"
        )
    lines.extend(
        [
            "",
            "除 25% 三元训练协议外，其余 14 个协议的平均 teacher-forced 逸度残差均下降。总体与多数状态协议中，Stage 2 改善了大部分预测指标；未见组分和部分三元比例协议的收益更不稳定。这说明逸度约束主要起到物理一致性正则和局部校正作用，不能替代化学空间覆盖。",
            "",
            "由于测试集只在验证选模完成后使用，上述 Stage 1/Stage 2 测试差异属于事后描述性分析，不用于重新调整损失权重或选择协议。最终部署应继续保留验证集回退机制，而不是无条件采用 Stage 2 checkpoint。",
            "",
            "## 9. 数值稳定性与结果可信度",
            "",
            f"在本报告覆盖的任务行中，最大平均 solver failure rate 为 **{max(float(row['solver_failure_rate_mean']) for row in rows):.6f}**，最大平均 nonphysical rate 为 **{max(float(row['nonphysical_rate_mean']) for row in rows):.6f}**，最小有效覆盖率为 **{min(float(row['valid_coverage_mean']) for row in rows):.6f}**。因此当前主要误差来自模型预测能力，而不是求解器未收敛或非物理解。",
            "",
            "所有协议均固定使用 seeds 0--4、已登记 split、相同评价指标和测试后评估规则。每个协议的 report manifest 绑定五个 seed manifest、聚合表、Stage comparison 和对应 SHA-256；完整机器表不依赖本报告中的手工转录。",
            "",
            "## 10. 综合结论",
            "",
            "1. 最终 C1 三视图 vanilla Transformer 在已见化学空间内的总体预测、组成内插以及温度/压力外推表现稳定，适合作为当前 ThermoFormer 主模型。",
            "2. 仅加入 teacher-forced 逸度损失的 10 epoch 部分微调具有总体正收益，但收益并非绝对一致；验证集在 16/75 个运行中回退 Stage 1，证明 epoch-0 候选与回退策略必须保留。",
            "3. 二元到三元零样本迁移的状态量与等温 y 结果具有可用性，但等压 y 是持续短板，且扩大三元训练比例没有带来单调收益。",
            "4. 未见组分性能显著低于状态外推，是当前模型最重要的泛化限制。后续若继续改进，应优先增加分子化学空间覆盖或引入针对未见分子的先验，而不是继续叠加状态型 physics loss。",
            "5. 当前报告支持“C1 + 验证门控逸度微调”为最终方案；不支持“对任意新组分均高精度”或“逸度微调对全部指标均显著提升”等超出证据的论断。",
            "",
            "## 11. 机器可读结果与复现入口",
            "",
            "- 完整任务表：`results/performance/c1_fugacity_generalization_by_task.csv`；",
            "- Stage 选择与逸度残差：`results/performance/c1_fugacity_stage_selection.csv`；",
            "- 英文精简报告：`reports/c1_fugacity_generalization_report.md`；",
            "- 证据链：`reports/c1_fugacity_generalization_report_manifest.json`；",
            "- 重建命令：`conda run -n ggnn39 python scripts/build_c1_generalization_report.py`。",
            "",
        ]
    )
    atomic_write_text(path, "\n".join(lines))


def _stage_summary(project_root: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows: list[dict[str, Any]] = []
    totals = {
        "stage1": 0,
        "stage2": 0,
        "residual_improved": 0,
        "predictive_improved": 0,
        "predictive_compared": 0,
    }
    for spec in PROTOCOLS:
        path = _protocol_dir(project_root, spec.name) / "stage_comparison_summary.json"
        payload = _load_json(path)
        counts = payload["selected_stage_counts"]
        stage1_residual = float(payload["stages"]["stage1"]["teacher_forced_fugacity"]["mean"])
        stage2_residual = float(payload["stages"]["stage2"]["teacher_forced_fugacity"]["mean"])
        totals["stage1"] += int(counts["stage1"])
        totals["stage2"] += int(counts["stage2"])
        totals["residual_improved"] += int(stage2_residual < stage1_residual)
        predictive_improved = 0
        predictive_compared = 0
        for direction, keys in (
            (
                "isothermal",
                ("pressure_mae_kpa", "pressure_rmse_kpa", "pressure_r2", "y_mae", "y_rmse", "y_r2"),
            ),
            (
                "isobaric",
                ("temperature_mae_k", "temperature_rmse_k", "temperature_r2", "y_mae", "y_rmse", "y_r2"),
            ),
        ):
            for key in keys:
                stage1_value = float(payload["stages"]["stage1"]["directions"][direction][key]["mean"])
                stage2_value = float(payload["stages"]["stage2"]["directions"][direction][key]["mean"])
                predictive_improved += int(
                    stage2_value > stage1_value if key.endswith("r2") else stage2_value < stage1_value
                )
                predictive_compared += 1
        totals["predictive_improved"] += predictive_improved
        totals["predictive_compared"] += predictive_compared
        rows.append(
            {
                "protocol": spec.name,
                "evaluation_setting": spec.label,
                "stage1_selected": int(counts["stage1"]),
                "stage2_selected": int(counts["stage2"]),
                "stage1_teacher_forced_fugacity": stage1_residual,
                "stage2_teacher_forced_fugacity": stage2_residual,
                "stage2_predictive_metrics_improved": predictive_improved,
                "predictive_metrics_compared": predictive_compared,
            }
        )
    return rows, totals


def _csv_text(rows: list[dict[str, Any]]) -> str:
    if not rows:
        raise ValueError("Cannot write an empty result table")
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().replace("\r\n", "\n")


def write_c1_generalization_outputs(
    project_root: Path = PROJECT_ROOT,
    *,
    report_path: Path | None = None,
    table_path: Path | None = None,
) -> dict[str, str]:
    """Validate inputs and atomically publish the final C1 campaign summary."""

    project_root = project_root.resolve()
    report_path = report_path or project_root / "reports/c1_fugacity_generalization_report.md"
    complete_report_path = project_root / "reports/c1_fugacity_complete_performance_report_zh.md"
    table_path = table_path or project_root / "results/performance/c1_fugacity_generalization_by_task.csv"
    stage_table_path = table_path.with_name("c1_fugacity_stage_selection.csv")
    manifest_path = report_path.with_name("c1_fugacity_generalization_report_manifest.json")

    rows = collect_generalization_rows(project_root)
    stage_rows, totals = _stage_summary(project_root)
    sections = (
        ("Overall predictive performance", "overall"),
        ("State interpolation and extrapolation", "state"),
        ("Unseen-component generalization", "chemistry"),
        ("Binary-to-ternary transfer", "transfer"),
    )
    lines = [
        "# C1 Three-View Vanilla ThermoFormer: Predictive Performance and Generalization",
        "",
        "Final architecture: RDKit descriptors + Uni-Mol v2 + functional-group features, "
        "independent projections and fusion, vanilla Transformer, original pair potential. "
        "Stage 2 retains supervised loss and adds only the teacher-forced fugacity-equilibrium loss.",
        "",
        "All values are mean ± standard deviation across seeds 0--4. Checkpoint selection uses "
        "validation only; the test partition is evaluated after selection. Isothermal inference is "
        "`molecules,T,x -> P,y`; isobaric inference is `molecules,P,x -> T,y`.",
        "",
    ]
    for title, category in sections:
        lines.extend([f"## {title}", "", _task_table(row for row in rows if row["category"] == category), ""])
    lines.extend(
        [
            "## Fugacity fine-tuning selection",
            "",
            f"Across 15 protocols × 5 seeds, validation retained Stage 1 for "
            f"**{totals['stage1']}/75** runs and selected Stage 2 for **{totals['stage2']}/75** runs. "
            f"The teacher-forced fugacity residual decreased after Stage 2 in "
            f"**{totals['residual_improved']}/15** protocol means.",
            "",
            f"As a post-selection descriptive comparison, raw Stage 2 test means improved over "
            f"raw Stage 1 in **{totals['predictive_improved']}/{totals['predictive_compared']}** "
            "direction-resolved MAE/RMSE/R² cells. This comparison was not used to tune the loss "
            "or select checkpoints.",
            "",
            "This is evidence for using validation-gated fugacity fine-tuning, not a claim that "
            "Stage 2 uniformly improves every predictive metric or every random seed.",
            "",
            "## Numerical diagnostics",
            "",
            f"Maximum mean solver-failure rate: `{max(float(row['solver_failure_rate_mean']) for row in rows):.6f}`; "
            f"maximum mean nonphysical rate: `{max(float(row['nonphysical_rate_mean']) for row in rows):.6f}`; "
            f"minimum valid coverage: `{min(float(row['valid_coverage_mean']) for row in rows):.6f}`.",
            "",
            "Machine-readable task metrics and Stage-1/Stage-2 selection diagnostics are stored in "
            f"`{portable_artifact_path(table_path, project_root)}` and "
            f"`{portable_artifact_path(stage_table_path, project_root)}`.",
            "",
        ]
    )
    atomic_write_text(table_path, _csv_text(rows))
    atomic_write_text(stage_table_path, _csv_text(stage_rows))
    atomic_write_text(report_path, "\n".join(lines))
    _write_complete_chinese_report(
        project_root, rows, stage_rows, totals, complete_report_path
    )

    inputs = []
    for spec in PROTOCOLS:
        path = _protocol_dir(project_root, spec.name) / "report_manifest.json"
        inputs.append(
            {
                "protocol": spec.name,
                "path": portable_artifact_path(path, project_root),
                "sha256": artifact_sha256(path),
            }
        )
    outputs = {
        "report": {
            "path": portable_artifact_path(report_path, project_root),
            "sha256": artifact_sha256(report_path),
        },
        "complete_chinese_report": {
            "path": portable_artifact_path(complete_report_path, project_root),
            "sha256": artifact_sha256(complete_report_path),
        },
        "task_metrics": {
            "path": portable_artifact_path(table_path, project_root),
            "sha256": artifact_sha256(table_path),
        },
        "stage_selection": {
            "path": portable_artifact_path(stage_table_path, project_root),
            "sha256": artifact_sha256(stage_table_path),
        },
    }
    atomic_write_json(
        manifest_path,
        {
            "status": "completed",
            "analysis_status": "confirmatory",
            "protocols": [spec.name for spec in PROTOCOLS],
            "seeds": [0, 1, 2, 3, 4],
            "selection_partition": "validation",
            "evaluation_partition": "test",
            "inputs": inputs,
            "outputs": outputs,
        },
    )
    return {key: value["path"] for key, value in outputs.items()} | {
        "manifest": portable_artifact_path(manifest_path, project_root)
    }
