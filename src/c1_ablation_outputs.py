"""Build the focused C1 ablation report from frozen overall-test artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from .artifacts import artifact_sha256, atomic_write_text


@dataclass(frozen=True)
class AblationSource:
    label: str
    family: str
    result_dir: str


C1_ABLATION_SOURCES = {
    "c0_unimol": AblationSource(
        "C0 Uni-Mol v2 vanilla", "representation",
        "results/multiview/chemical_attention/formal/runs/"
        "c0_current_vanilla.on.overall_binary_ternary",
    ),
    "v1_rdkit": AblationSource(
        "V1 RDKit descriptors only", "representation",
        "results/multiview/formal/runs/v1_rdkit_only.on.overall_binary_ternary",
    ),
    "v3_fg": AblationSource(
        "V3 functional groups only", "representation",
        "results/multiview/predictive/runs/"
        "v3_functional_group_only.on.overall_binary_ternary",
    ),
    "v4_rdkit_unimol": AblationSource(
        "V4 RDKit + Uni-Mol", "representation",
        "results/multiview/predictive/runs/"
        "v4_rdkit_unimol_naive.on.overall_binary_ternary",
    ),
    "c1_final": AblationSource(
        "C1 RDKit + Uni-Mol + FG vanilla", "representation interaction",
        "results/multiview/chemical_attention/formal/runs/"
        "c1_three_view_vanilla.on.overall_binary_ternary",
    ),
    "c2_chemical_bias": AblationSource(
        "C2 chemical-biased + context pair", "interaction",
        "results/multiview/chemical_attention/formal/runs/"
        "c2_chemical_bias_full.on.overall_binary_ternary",
    ),
    "c3_context_pair": AblationSource(
        "C3 context pair without attention bias", "interaction",
        "results/multiview/chemical_attention/formal/runs/"
        "c3_no_pair_bias.on.overall_binary_ternary",
    ),
}

PHYSICS_COMPARISON = (
    "results/experiments/physics_finetuning/c1_three_view_vanilla_fugacity/"
    "c1_three_view_vanilla_fugacity_finetune.on.overall_binary_ternary/"
    "seed_0/stage_comparison.json"
)


def _validated_summary(
    project_root: Path,
    source: AblationSource,
) -> tuple[Path, Path, list[dict[str, str]]]:
    result_dir = project_root / source.result_dir
    manifest_path = result_dir / "aggregate_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "completed" or manifest.get("seeds") != [0, 1, 2, 3, 4]:
        raise RuntimeError(f"Incomplete five-seed aggregate: {source.label}")
    if not str(manifest.get("protocol", "")).endswith(".on.overall_binary_ternary"):
        raise RuntimeError(f"Unexpected ablation protocol: {source.label}")
    summary_path = result_dir / "metrics_summary.csv"
    expected = manifest.get("outputs", {}).get("metrics_summary", {}).get("sha256")
    if artifact_sha256(summary_path) != expected:
        raise RuntimeError(f"Aggregate summary SHA mismatch: {source.label}")
    with summary_path.open("r", encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row["scope"] == "direction"]
    if {row["direction"] for row in rows} != {"isothermal", "isobaric"}:
        raise RuntimeError(f"Missing direction metrics: {source.label}")
    return manifest_path, summary_path, rows


def collect_c1_ablation_rows(project_root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for variant_id, source in C1_ABLATION_SOURCES.items():
        manifest_path, summary_path, rows = _validated_summary(project_root, source)
        for row in rows:
            direction = row["direction"]
            prefix = "pressure" if direction == "isothermal" else "temperature"
            unit_suffix = "_kpa" if direction == "isothermal" else "_k"
            records.append(
                {
                    "variant_id": variant_id,
                    "variant": source.label,
                    "family": source.family,
                    "protocol": "overall_binary_ternary",
                    "direction": direction,
                    "state": "P" if direction == "isothermal" else "T",
                    "state_unit": "kPa" if direction == "isothermal" else "K",
                    "state_mae_mean": float(row[f"{prefix}_mae{unit_suffix}_mean"]),
                    "state_mae_std": float(row[f"{prefix}_mae{unit_suffix}_std"]),
                    "state_rmse_mean": float(row[f"{prefix}_rmse{unit_suffix}_mean"]),
                    "state_rmse_std": float(row[f"{prefix}_rmse{unit_suffix}_std"]),
                    "state_r2_mean": float(row[f"{prefix}_r2_mean"]),
                    "state_r2_std": float(row[f"{prefix}_r2_std"]),
                    "y_mae_mean": float(row["y_mae_mean"]),
                    "y_mae_std": float(row["y_mae_std"]),
                    "y_rmse_mean": float(row["y_rmse_mean"]),
                    "y_rmse_std": float(row["y_rmse_std"]),
                    "y_r2_mean": float(row["y_r2_mean"]),
                    "y_r2_std": float(row["y_r2_std"]),
                    "valid_coverage_mean": float(row["valid_coverage_mean"]),
                    "valid_coverage_std": float(row["valid_coverage_std"]),
                    "solver_failure_rate_mean": float(row["solver_failure_rate_mean"]),
                    "solver_failure_rate_std": float(row["solver_failure_rate_std"]),
                    "source": summary_path.relative_to(project_root).as_posix(),
                    "source_sha256": artifact_sha256(summary_path),
                    "aggregate_manifest": manifest_path.relative_to(project_root).as_posix(),
                    "aggregate_manifest_sha256": artifact_sha256(manifest_path),
                }
            )
    return records


def _mean_std(row: dict[str, object], name: str, digits: int) -> str:
    return f"{float(row[name + '_mean']):.{digits}f} ± {float(row[name + '_std']):.{digits}f}"


def _table(records: list[dict[str, object]], family: str, direction: str) -> list[str]:
    selected = [
        row for row in records
        if family in str(row["family"]).split() and row["direction"] == direction
    ]
    state = "P (kPa)" if direction == "isothermal" else "T (K)"
    lines = [
        f"| Variant | {state} MAE | {state} RMSE | {state} R² | y MAE | y RMSE | y R² | Valid coverage |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in selected:
        lines.append(
            f"| {row['variant']} | {_mean_std(row, 'state_mae', 3)} | "
            f"{_mean_std(row, 'state_rmse', 3)} | {_mean_std(row, 'state_r2', 3)} | "
            f"{_mean_std(row, 'y_mae', 4)} | {_mean_std(row, 'y_rmse', 4)} | "
            f"{_mean_std(row, 'y_r2', 3)} | "
            f"{100.0 * float(row['valid_coverage_mean']):.1f}% |"
        )
    return lines


def _physics_rows(project_root: Path) -> tuple[Path, dict[str, object]]:
    path = project_root / PHYSICS_COMPARISON
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("selection_partition") != "validation" or payload.get("evaluation_partition") != "test":
        raise RuntimeError("Fugacity fine-tuning comparison has invalid partitions")
    weights = payload.get("thermodynamic_loss_weights", {})
    if float(weights.get("teacher_forced_fugacity", 0.0)) != 1.0 or any(
        float(value) != 0.0
        for name, value in weights.items()
        if name != "teacher_forced_fugacity"
    ):
        raise RuntimeError("Frozen fugacity comparison is not fugacity-only")
    return path, payload


def write_c1_ablation_outputs(
    project_root: Path,
    *,
    output_root: Path | None = None,
    report_path: Path | None = None,
) -> tuple[Path, Path, Path]:
    records = collect_c1_ablation_rows(project_root)
    physics_path, physics = _physics_rows(project_root)
    output_root = output_root or project_root / "results/c1_ablation"
    report_path = report_path or project_root / "reports/c1_ablation_overall_binary_ternary.md"
    metrics_path = output_root / "overall_binary_ternary_metrics.csv"
    manifest_path = output_root / "report_manifest.json"

    def recorded_path(path: Path) -> str:
        try:
            return path.relative_to(project_root).as_posix()
        except ValueError:
            return str(path)

    fieldnames = list(records[0])
    from io import StringIO
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    atomic_write_text(metrics_path, stream.getvalue())

    lines = [
        "# C1 三视图 vanilla 消融实验结果",
        "",
        "所有表征与交互消融均采用固定 `overall_binary_ternary`：二元+三元训练，"
        "随后在联合二元+三元测试集上评估。结果为 seeds 0--4 的均值 ± 样本标准差。",
        "",
        "## 分子表征消融",
        "",
        "### 等温任务：输入分子、T、x，预测 P 与 y",
        "",
        *_table(records, "representation", "isothermal"),
        "",
        "### 等压任务：输入分子、P、x，预测 T 与 y",
        "",
        *_table(records, "representation", "isobaric"),
        "",
        "三视图 C1 相比 Uni-Mol-only 明显降低四类预测误差；FG-only 无法独立支撑 VLE，"
        "其等温/等压有效覆盖率仅 63.4%/96.7%，不能把其误差与满覆盖模型作脱离覆盖率的比较。"
        "在 RDKit+Uni-Mol 上增加 FG 后，P 与等压 T 改善，但 y 的变化较小。",
        "",
        "## 组分交互模块消融",
        "",
        "### 等温任务",
        "",
        *_table(records, "interaction", "isothermal"),
        "",
        "### 等压任务",
        "",
        *_table(records, "interaction", "isobaric"),
        "",
        "C2 chemical-biased Transformer 没有稳定超过 C1；C3 的 T/y 较好但压力明显较差。"
        "综合 P、T、y 和参数复杂度，C1 是当前最均衡的最终结构。",
        "",
        "## 逸度损失微调消融（seed 0）",
        "",
        "Stage 1 是 C1 数据监督最佳 checkpoint；Stage 2 保留监督损失并只增加"
        " teacher-forced 逸度平衡损失，checkpoint 仅由验证集选择。",
        "",
        "| Task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Fugacity Stage 2 MAE | Fugacity Stage 2 RMSE | Fugacity Stage 2 R² |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    stages = physics["stages"]
    for direction, state, prefix, suffix in (
        ("isothermal", "P", "pressure", "_kpa"),
        ("isothermal", "y", "y", ""),
        ("isobaric", "T", "temperature", "_k"),
        ("isobaric", "y", "y", ""),
    ):
        first = next(row for row in stages["stage1"]["metrics"] if row.get("scope") == "direction" and row.get("direction") == direction)
        second = next(row for row in stages["stage2"]["metrics"] if row.get("scope") == "direction" and row.get("direction") == direction)
        lines.append(
            f"| {state}, {direction} | {float(first[prefix + '_mae' + suffix]):.6f} | "
            f"{float(first[prefix + '_rmse' + suffix]):.6f} | {float(first[prefix + '_r2']):.6f} | "
            f"{float(second[prefix + '_mae' + suffix]):.6f} | {float(second[prefix + '_rmse' + suffix]):.6f} | "
            f"{float(second[prefix + '_r2']):.6f} |"
        )
    lines.extend(
        [
            "",
            f"验证损失：Stage 1 `{float(stages['stage1']['validation_loss']):.8f}`，"
            f"Stage 2 `{float(stages['stage2']['validation_loss']):.8f}`；最终选择 **{physics['selected_stage']}**。",
            "逸度微调改善 P MAE/RMSE 和两种方向的 y MAE，但 T RMSE/R² 及等温 y RMSE/R² 略有退化。"
            "因此它是验证集支持的 seed-0 改善，不应在缺少多种子结果时宣称全面最优。",
            "",
            "## 最终选择",
            "",
            "最终模型固定为 **C1 RDKit descriptors + Uni-Mol v2 + functional groups + vanilla Transformer**；"
            "Stage 2 仅保留 teacher-forced 逸度平衡损失。监督阶段的纯端点 Psat 项仍属于数据监督，"
            "不属于额外物理微调损失。",
            "",
        ]
    )
    atomic_write_text(report_path, "\n".join(lines))
    manifest = {
        "status": "completed",
        "protocol": "overall_binary_ternary",
        "representation_and_interaction_seeds": [0, 1, 2, 3, 4],
        "physics_finetuning_seed": 0,
        "inputs": {
            variant_id: {
                "metrics_summary": {
                    "path": next(row["source"] for row in records if row["variant_id"] == variant_id),
                    "sha256": next(row["source_sha256"] for row in records if row["variant_id"] == variant_id),
                },
                "aggregate_manifest": {
                    "path": next(row["aggregate_manifest"] for row in records if row["variant_id"] == variant_id),
                    "sha256": next(
                        row["aggregate_manifest_sha256"]
                        for row in records
                        if row["variant_id"] == variant_id
                    ),
                },
            }
            for variant_id in C1_ABLATION_SOURCES
        },
        "physics_stage_comparison": {
            "path": physics_path.relative_to(project_root).as_posix(),
            "sha256": artifact_sha256(physics_path),
        },
        "outputs": {
            "metrics": {"path": recorded_path(metrics_path), "sha256": artifact_sha256(metrics_path)},
            "report": {"path": recorded_path(report_path), "sha256": artifact_sha256(report_path)},
        },
    }
    atomic_write_text(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return report_path, metrics_path, manifest_path
