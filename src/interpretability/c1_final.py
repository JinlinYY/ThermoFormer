"""Five-seed explanations for the validation-selected final C1 workflow."""

from __future__ import annotations

import itertools
import json
import math
import os
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from torch import Tensor

from ..artifacts import artifact_sha256, atomic_write_json, atomic_write_text
from ..config import load_experiment_config
from ..data import VLESample, VLETensorDataset, collate_vle, load_vle_samples, retain_pure_anchored_systems
from ..representation import build_molecular_encoder, encoder_cache_filename, prepare_partition_features
from ..splits import load_split_assignment, sample_id, system_id
from .core import load_thermoformer_checkpoint, thermodynamic_response_sensitivity
from .selection import molecule_family, system_family


SEEDS = tuple(range(5))
SPLIT_PROTOCOL = "overall_binary_ternary"
FINAL_PROTOCOL = "c1_three_view_vanilla_fugacity_finetune.on.overall_binary_ternary"
FINAL_RESULT_ROOT = Path(
    "results/experiments/physics_finetuning/c1_three_view_vanilla_fugacity"
) / FINAL_PROTOCOL
FINAL_CHECKPOINT_ROOT = Path(
    "checkpoints/experiments/physics_finetuning/c1_three_view_vanilla_fugacity"
) / FINAL_PROTOCOL
VIEW_LABELS = {
    "rdkit_2d": "RDKit descriptors",
    "unimol_v2": "Uni-Mol v2",
    "functional_groups": "Functional groups",
}
OUTPUT_LABELS = {
    "ge_rt": r"$G^E/RT$",
    "mean_abs_log_gamma": r"mean $|\ln\gamma|$",
    "mean_abs_log_alpha": r"mean $|\ln\alpha|$",
    "mean_abs_pair_interaction": r"mean $|I_{ij}|$",
}


@dataclass(frozen=True)
class FinalSeedContext:
    seed: int
    selected_stage: str
    model: torch.nn.Module
    checkpoint: Path
    split_path: Path
    feature_map: dict[str, np.ndarray]
    view_dimensions: dict[str, int]
    train_baseline: np.ndarray
    test: tuple[VLESample, ...]


def exact_group_shapley(coalitions: dict[tuple[int, ...], Tensor], groups: int) -> Tensor:
    """Return exact Shapley values for a small set of grouped input views."""

    expected = {tuple(index for index in range(groups) if mask & (1 << index)) for mask in range(1 << groups)}
    if set(coalitions) != expected:
        raise ValueError("Exact grouped Shapley requires every coalition")
    reference = next(iter(coalitions.values()))
    values = torch.zeros((*reference.shape, groups), dtype=reference.dtype, device=reference.device)
    factorial = math.factorial
    denominator = factorial(groups)
    for group in range(groups):
        others = [index for index in range(groups) if index != group]
        for size in range(groups):
            weight = factorial(size) * factorial(groups - size - 1) / denominator
            for subset in itertools.combinations(others, size):
                key = tuple(sorted(subset))
                extended = tuple(sorted((*subset, group)))
                values[..., group] += weight * (coalitions[extended] - coalitions[key])
    return values


def _device(name: str) -> torch.device:
    if name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    return torch.device(name)


def _chunks(values: Sequence[VLESample], size: int) -> Iterable[Sequence[VLESample]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _view_slices(dimensions: dict[str, int]) -> dict[str, slice]:
    offset = 0
    slices = {}
    for name in ("rdkit_2d", "unimol_v2", "functional_groups"):
        width = int(dimensions[name])
        if width < 1:
            raise ValueError(f"Final C1 checkpoint is missing {name}")
        slices[name] = slice(offset, offset + width)
        offset += width
    return slices


def _stratified_sample(rows: Sequence[VLESample], maximum: int, seed: int) -> tuple[VLESample, ...]:
    """Select a deterministic, target-blind sample across task/cardinality strata."""

    strata: dict[tuple[str, int], list[VLESample]] = {}
    for row in rows:
        strata.setdefault((row.experiment_mode, row.component_count), []).append(row)
    if maximum < len(strata):
        raise ValueError("max_samples_per_seed must cover every available stratum")
    rng = np.random.default_rng(seed + 1701)
    allocation = maximum // len(strata)
    remainder = maximum % len(strata)
    selected: list[VLESample] = []
    for index, key in enumerate(sorted(strata)):
        candidates = sorted(strata[key], key=sample_id)
        count = min(len(candidates), allocation + int(index < remainder))
        indices = np.sort(rng.choice(len(candidates), size=count, replace=False))
        selected.extend(candidates[position] for position in indices)
    return tuple(sorted(selected, key=sample_id))


def _load_seed_context(
    project_root: Path,
    samples: Sequence[VLESample],
    seed: int,
    device: torch.device,
) -> FinalSeedContext:
    result_root = project_root / FINAL_RESULT_ROOT / f"seed_{seed}"
    manifest_path = result_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    comparison_path = result_root / "stage_comparison.json"
    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    if (
        manifest.get("status") != "completed"
        or manifest.get("evaluation_partition") != "test"
        or manifest.get("protocol") != FINAL_PROTOCOL
        or int(manifest.get("seed", -1)) != seed
        or comparison.get("selection_partition") != "validation"
        or comparison.get("evaluation_partition") != "test"
        or comparison.get("selected_stage") != manifest.get("selected_stage")
    ):
        raise RuntimeError(f"Invalid final-model manifest: {manifest_path}")
    checkpoint = project_root / FINAL_CHECKPOINT_ROOT / f"seed_{seed}/best_model.pt"
    checkpoint_record = manifest["artifacts"]["checkpoint"]
    if artifact_sha256(checkpoint) != checkpoint_record["sha256"]:
        raise RuntimeError(f"Final checkpoint SHA mismatch: {checkpoint}")
    split_path = project_root / f"splits/{SPLIT_PROTOCOL}/seed_{seed}.json"
    split = load_split_assignment(split_path, samples)
    experiment = load_experiment_config(
        project_root / "experiments/physics_finetuning/c1_three_view_vanilla_fugacity/config.json"
    )
    unique_smiles = sorted({value for row in samples for value in row.smiles})
    train_smiles = sorted({value for row in split.train for value in row.smiles})
    cache = project_root / "cache" / encoder_cache_filename(experiment.encoder)
    encoder = build_molecular_encoder(experiment.encoder, cache, use_cuda=device.type == "cuda")
    prepared = prepare_partition_features(encoder, unique_smiles, train_smiles)
    recorded = manifest.get("molecular_feature_preprocessing", {})
    if prepared.metadata.get("feature_definition_sha256") != recorded.get("feature_definition_sha256"):
        raise RuntimeError(f"Feature definition differs from training for seed {seed}")
    if prepared.metadata.get("rdkit_scaler", {}).get("sha256") != recorded.get("rdkit_scaler", {}).get("sha256"):
        raise RuntimeError(f"RDKit scaler differs from training for seed {seed}")
    baseline = np.mean([prepared.values[value] for value in train_smiles], axis=0).astype(np.float32)
    bundle = load_thermoformer_checkpoint(checkpoint, device)
    if bundle.model.config.chemical_attention_bias or bundle.model.config.context_pair_interaction:
        raise RuntimeError("Explainability target is not the final C1 vanilla architecture")
    return FinalSeedContext(
        seed=seed,
        selected_stage=str(manifest["selected_stage"]),
        model=bundle.model,
        checkpoint=checkpoint,
        split_path=split_path,
        feature_map=prepared.values,
        view_dimensions=prepared.view_dimensions,
        train_baseline=baseline,
        test=tuple(split.test),
    )


def _scalar_outputs(output: object, mask: Tensor) -> dict[str, Tensor]:
    active = mask.sum(-1).clamp_min(1.0)
    pair_mask = mask.unsqueeze(1) * mask.unsqueeze(2)
    upper = torch.triu(torch.ones_like(pair_mask), diagonal=1) * pair_mask
    pair_count = upper.sum((1, 2)).clamp_min(1.0)
    log_activity = output.log_gamma + output.log_psat
    differences = torch.abs(log_activity.unsqueeze(2) - log_activity.unsqueeze(1)) * upper
    if output.pair_interactions is None or output.excess_gibbs_rt is None:
        raise RuntimeError("Final C1 model did not expose thermodynamic interactions")
    return {
        "ge_rt": output.excess_gibbs_rt.squeeze(-1),
        "mean_abs_log_gamma": (torch.abs(output.log_gamma) * mask).sum(-1) / active,
        "mean_abs_log_alpha": differences.sum((1, 2)) / pair_count,
        "mean_abs_pair_interaction": (torch.abs(output.pair_interactions) * upper).sum((1, 2)) / pair_count,
    }


def _coalition_molecules(
    molecules: Tensor,
    mask: Tensor,
    baseline: Tensor,
    slices: dict[str, slice],
    included: tuple[int, ...],
) -> Tensor:
    names = tuple(slices)
    result = baseline.view(1, 1, -1).expand_as(molecules).clone()
    for index in included:
        block = slices[names[index]]
        result[..., block] = molecules[..., block]
    return result * mask.unsqueeze(-1)


def modality_shapley_table(
    context: FinalSeedContext,
    rows: Sequence[VLESample],
    device: torch.device,
    batch_size: int,
) -> pd.DataFrame:
    slices = _view_slices(context.view_dimensions)
    baseline = torch.from_numpy(context.train_baseline).to(device)
    records: list[dict[str, object]] = []
    for chunk in _chunks(rows, batch_size):
        dataset = VLETensorDataset(chunk, context.feature_map)
        batch = collate_vle([dataset[index] for index in range(len(dataset))]).to(device)
        coalition_values: dict[str, dict[tuple[int, ...], Tensor]] = {
            name: {} for name in OUTPUT_LABELS
        }
        full_output = None
        for mask_bits in range(8):
            included = tuple(index for index in range(3) if mask_bits & (1 << index))
            perturbed = _coalition_molecules(
                batch.molecules, batch.mask, baseline, slices, included
            )
            with torch.no_grad():
                output = context.model(
                    perturbed,
                    batch.temperature_k,
                    batch.pressure_kpa,
                    batch.x,
                    batch.mask,
                )
            if mask_bits == 7:
                full_output = output
            for name, values in _scalar_outputs(output, batch.mask).items():
                coalition_values[name][included] = values.cpu()
        if full_output is None:
            raise AssertionError("Full coalition was not evaluated")
        shapley = {name: exact_group_shapley(values, 3) for name, values in coalition_values.items()}
        for row_index, sample in enumerate(chunk):
            base = {
                "seed": context.seed,
                "selected_stage": context.selected_stage,
                "sample_id": sample_id(sample),
                "system_id": system_id(sample),
                "direction": sample.experiment_mode,
                "component_count": sample.component_count,
                "chemical_family": system_family(sample.smiles),
                "evaluation_partition": "test",
                "explanation_mode": "teacher_forced_observed_T_P_x",
            }
            for output_name in OUTPUT_LABELS:
                empty = float(coalition_values[output_name][()][row_index])
                full = float(coalition_values[output_name][(0, 1, 2)][row_index])
                for view_index, view_name in enumerate(slices):
                    records.append(
                        {
                            **base,
                            "output": output_name,
                            "view": view_name,
                            "shapley_value": float(shapley[output_name][row_index, view_index]),
                            "absolute_shapley_value": abs(float(shapley[output_name][row_index, view_index])),
                            "empty_value": empty,
                            "full_value": full,
                            "additivity_error": abs(
                                float(shapley[output_name][row_index].sum()) - (full - empty)
                            ),
                        }
                    )
        del full_output
    return pd.DataFrame(records)


def interaction_table(
    context: FinalSeedContext,
    rows: Sequence[VLESample],
    device: torch.device,
    batch_size: int,
) -> pd.DataFrame:
    records = []
    for chunk in _chunks(rows, batch_size):
        dataset = VLETensorDataset(chunk, context.feature_map)
        batch = collate_vle([dataset[index] for index in range(len(dataset))]).to(device)
        with torch.no_grad():
            output = context.model(
                batch.molecules,
                batch.temperature_k,
                batch.pressure_kpa,
                batch.x,
                batch.mask,
            )
        if output.pair_interactions is None or output.excess_gibbs_rt is None:
            raise RuntimeError("Final C1 model did not expose pair interactions")
        for row_index, sample in enumerate(chunk):
            active_log_gamma = output.log_gamma[row_index, : sample.component_count]
            for first in range(sample.component_count):
                for second in range(first + 1, sample.component_count):
                    interaction = float(output.pair_interactions[row_index, first, second].cpu())
                    records.append(
                        {
                            "seed": context.seed,
                            "selected_stage": context.selected_stage,
                            "sample_id": sample_id(sample),
                            "system_id": system_id(sample),
                            "direction": sample.experiment_mode,
                            "component_count": sample.component_count,
                            "chemical_family": system_family(sample.smiles),
                            "component_i_family": molecule_family(sample.smiles[first]),
                            "component_j_family": molecule_family(sample.smiles[second]),
                            "x_i": sample.liquid_composition[first],
                            "x_j": sample.liquid_composition[second],
                            "pair_interaction": interaction,
                            "absolute_pair_interaction": abs(interaction),
                            "composition_weighted_pair_contribution": sample.liquid_composition[first]
                            * sample.liquid_composition[second]
                            * interaction,
                            "mean_abs_log_gamma": float(torch.mean(torch.abs(active_log_gamma)).cpu()),
                            "excess_gibbs_rt": float(output.excess_gibbs_rt[row_index, 0].cpu()),
                            "evaluation_partition": "test",
                        }
                    )
    return pd.DataFrame(records)


def _representative_interior(rows: Sequence[VLESample], cardinality: int) -> VLESample:
    candidates = [
        row
        for row in rows
        if row.component_count == cardinality
        and min(row.liquid_composition) > 0.05
        and max(row.liquid_composition) < 0.95
    ]
    if not candidates:
        raise RuntimeError(f"No interior {cardinality}-component test sample")
    target = np.full(cardinality, 1.0 / cardinality)
    return min(
        candidates,
        key=lambda row: (float(np.linalg.norm(np.asarray(row.liquid_composition) - target)), sample_id(row)),
    )


def sensitivity_table(context: FinalSeedContext, device: torch.device) -> pd.DataFrame:
    records = []
    for cardinality in (2, 3):
        sample = _representative_interior(context.test, cardinality)
        dataset = VLETensorDataset([sample], context.feature_map)
        batch = collate_vle([dataset[0]]).to(device)
        composition_response, temperature_response = thermodynamic_response_sensitivity(
            context.model,
            batch.molecules,
            batch.temperature_k,
            batch.pressure_kpa,
            batch.x,
            batch.mask,
        )
        for affected in range(cardinality):
            for increased in range(cardinality):
                records.append(
                    {
                        "seed": context.seed,
                        "selected_stage": context.selected_stage,
                        "sample_id": sample_id(sample),
                        "system_id": system_id(sample),
                        "component_count": cardinality,
                        "affected_component": affected + 1,
                        "increased_component": increased + 1,
                        "d_log_gamma_i_d_closed_x_j": float(composition_response[affected, increased].cpu()),
                        "d_log_gamma_i_d_temperature_k": float(temperature_response[affected].cpu()),
                        "evaluation_partition": "test",
                    }
                )
    return pd.DataFrame(records)


def _atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = frame.to_csv(index=False, lineterminator="\n")
    atomic_write_text(path, content)


def _plot(
    shapley: pd.DataFrame,
    interactions: pd.DataFrame,
    sensitivities: pd.DataFrame,
    output_stem: Path,
) -> list[Path]:
    mpl.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    })
    figure, axes = plt.subplots(2, 2, figsize=(7.2, 5.5))
    summary = shapley.groupby(["output", "view"], as_index=False)["absolute_shapley_value"].mean()
    outputs = list(OUTPUT_LABELS)
    views = list(VIEW_LABELS)
    width = 0.23
    x_positions = np.arange(len(outputs))
    colors = ("#4472C4", "#ED7D31", "#70AD47")
    for index, (view, color) in enumerate(zip(views, colors)):
        values = [
            float(summary.loc[(summary["output"] == output) & (summary["view"] == view), "absolute_shapley_value"].iloc[0])
            for output in outputs
        ]
        axes[0, 0].bar(x_positions + (index - 1) * width, values, width, label=VIEW_LABELS[view], color=color)
    axes[0, 0].set_xticks(x_positions, [OUTPUT_LABELS[name] for name in outputs], rotation=18, ha="right")
    axes[0, 0].set_ylabel("Mean absolute grouped Shapley value")
    axes[0, 0].set_title("a  Molecular-view attribution", loc="left", fontweight="bold")
    axes[0, 0].legend(frameon=False, fontsize=7)

    alpha = shapley.loc[shapley["output"].eq("mean_abs_log_alpha")]
    distributions = [alpha.loc[alpha["view"].eq(view), "shapley_value"].to_numpy() for view in views]
    violin = axes[0, 1].violinplot(distributions, showmedians=True, showextrema=False)
    for body, color in zip(violin["bodies"], colors):
        body.set_facecolor(color)
        body.set_alpha(0.65)
    axes[0, 1].axhline(0.0, color="#777777", lw=0.7)
    axes[0, 1].set_xticks(range(1, 4), [VIEW_LABELS[name] for name in views], rotation=18, ha="right")
    axes[0, 1].set_ylabel(r"Grouped Shapley value for mean $|\ln\alpha|$")
    axes[0, 1].set_title("b  Signed attribution distribution", loc="left", fontweight="bold")

    for cardinality, marker, color in ((2, "o", "#4472C4"), (3, "^", "#C55A11")):
        rows = interactions.loc[interactions["component_count"].eq(cardinality)]
        axes[1, 0].scatter(
            rows["absolute_pair_interaction"],
            rows["mean_abs_log_gamma"],
            s=9,
            alpha=0.25,
            marker=marker,
            color=color,
            label=f"{cardinality}-component",
        )
    axes[1, 0].set_xlabel(r"$|I_{ij}|$")
    axes[1, 0].set_ylabel(r"Mean $|\ln\gamma|$")
    axes[1, 0].set_title("c  Decoder interaction and nonideality", loc="left", fontweight="bold")
    axes[1, 0].legend(frameon=False, fontsize=7)

    ternary = sensitivities.loc[sensitivities["component_count"].eq(3)]
    matrix = ternary.groupby(["affected_component", "increased_component"])["d_log_gamma_i_d_closed_x_j"].mean().unstack().to_numpy()
    limit = max(float(np.max(np.abs(matrix))), 1e-8)
    image = axes[1, 1].imshow(matrix, cmap="RdBu_r", vmin=-limit, vmax=limit)
    for row in range(3):
        for column in range(3):
            axes[1, 1].text(column, row, f"{matrix[row, column]:.2f}", ha="center", va="center", fontsize=7)
    axes[1, 1].set_xticks(range(3), ("1", "2", "3"))
    axes[1, 1].set_yticks(range(3), ("1", "2", "3"))
    axes[1, 1].set_xlabel("Component increased")
    axes[1, 1].set_ylabel(r"Responding $\ln\gamma_i$")
    axes[1, 1].set_title("d  Mean closed-simplex sensitivity", loc="left", fontweight="bold")
    figure.colorbar(image, ax=axes[1, 1], fraction=0.046, pad=0.04)
    for axis in axes.ravel():
        axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for suffix, options in (("png", {"dpi": 400}), ("pdf", {}), ("svg", {})):
        path = output_stem.with_suffix(f".{suffix}")
        temporary = path.with_name(f".{path.stem}.{os.getpid()}.tmp.{suffix}")
        figure.savefig(temporary, bbox_inches="tight", **options)
        os.replace(temporary, path)
        paths.append(path)
    plt.close(figure)
    return paths


def _mean_std(values: pd.Series) -> str:
    return f"{float(values.mean()):.4g} ± {float(values.std(ddof=1)):.3g}"


def _report(
    path: Path,
    shapley: pd.DataFrame,
    interactions: pd.DataFrame,
    sensitivities: pd.DataFrame,
    selected_stages: dict[int, str],
) -> None:
    seed_importance = shapley.groupby(["seed", "output", "view"], as_index=False)["absolute_shapley_value"].mean()
    global_importance = seed_importance.groupby(["output", "view"], as_index=False)["absolute_shapley_value"].agg(["mean", "std"]).reset_index()
    global_importance["share"] = global_importance["mean"] / global_importance.groupby("output")["mean"].transform("sum")
    correlations = []
    for seed, rows in interactions.groupby("seed"):
        correlations.append({
            "seed": seed,
            "rho": rows["absolute_pair_interaction"].corr(rows["mean_abs_log_gamma"], method="spearman"),
        })
    correlation_frame = pd.DataFrame(correlations)
    max_additivity = float(shapley["additivity_error"].max())
    lines = [
        "# C1 final ThermoFormer interpretability",
        "",
        "解释对象为最终 **C1 RDKit + Uni-Mol v2 + functional groups + vanilla Transformer**，"
        "并使用每个 seed 经验证集选择后的最终 checkpoint。分析仅覆盖 `overall_binary_ternary` 测试集。",
        "",
        f"五个 checkpoint 的选择为：{', '.join(f'seed {seed}: {stage}' for seed, stage in sorted(selected_stages.items()))}。",
        "Grouped Shapley 使用各 seed 训练集的视图均值作为背景，将三类分子视图视为三个特征组；"
        "分析在观测 T、P、x 状态上解释模型内部热力学输出，因此属于 teacher-forced model attribution。",
        "",
        "## Molecular-view contributions",
        "",
        "| Explained output | Molecular view | Mean | SD | Normalized share |",
        "|---|---|---:|---:|---:|",
    ]
    for _, row in global_importance.iterrows():
        lines.append(
            f"| {OUTPUT_LABELS[str(row['output'])]} | {VIEW_LABELS[str(row['view'])]} | "
            f"{float(row['mean']):.5g} | {float(row['std']):.4g} | {100.0 * float(row['share']):.1f}% |"
        )
    top_views = {
        output: VIEW_LABELS[str(rows.loc[rows["mean"].idxmax(), "view"])]
        for output, rows in global_importance.groupby("output")
    }
    lines.extend([
        "",
        "按 mean |Shapley|，各输出的最大贡献视图为："
        + "；".join(f"{OUTPUT_LABELS[name]}—**{view}**" for name, view in top_views.items())
        + "。这说明三视图贡献可量化，但不能把归因值解释为因果化学机制。",
        f"精确三组 Shapley 的最大加和误差为 `{max_additivity:.3g}`。",
        "",
        "## Pair interaction and thermodynamic sensitivity",
        "",
        "`pair_potential` 的 |Iij| 与同状态 mean |lnγ| 的 seed-wise Spearman 相关为 "
        f"**{_mean_std(correlation_frame['rho'])}**。它是模型内部 decoder interaction，"
        "不是实验测得的键能或相互作用能。",
    ])
    for cardinality in (2, 3):
        rows = sensitivities.loc[sensitivities["component_count"].eq(cardinality)]
        seed_norm = rows.groupby("seed")["d_log_gamma_i_d_closed_x_j"].apply(
            lambda values: float(np.sqrt(np.mean(np.square(values))))
        )
        temperature_norm = rows.groupby("seed")["d_log_gamma_i_d_temperature_k"].apply(
            lambda values: float(np.sqrt(np.mean(np.square(values))))
        )
        lines.append(
            f"- {cardinality}组分代表状态：组成闭合方向响应 RMS `{_mean_std(seed_norm)}`；"
            f"温度响应 RMS `{_mean_std(temperature_norm)}` K⁻¹。"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "1. 三类视图通过独立 projection 和融合共同影响热力学输出；归因结果回答“模型依赖什么”，不回答“分子为何真实相互作用”。",
        "2. Pair potential 与活度非理想性之间的相关只支持 decoder 内部一致性，不能单独证明氢键、络合或共沸机理。",
        "3. 闭单纯形导数保持 Σx=1，因而比直接对独立 x 分量求导更符合组成变量约束。",
        "4. 解释使用五个验证集选择 checkpoint 汇总，避免以单一随机种子下结论。",
        "",
        "## Reproducibility",
        "",
        "- Grouped Shapley values: `analysis/interpretability_c1_final/results/modality_shapley.csv`",
        "- Pair interactions: `analysis/interpretability_c1_final/results/pair_interactions.csv`",
        "- Thermodynamic sensitivities: `analysis/interpretability_c1_final/results/thermodynamic_sensitivity.csv`",
        "- Figure: `analysis/interpretability_c1_final/figures/Figure_c1_interpretability.{png,pdf,svg}`",
        "",
    ])
    atomic_write_text(path, "\n".join(lines))


def run_c1_final_interpretability(
    project_root: Path,
    *,
    device_name: str = "auto",
    max_samples_per_seed: int = 256,
    batch_size: int = 64,
    output_root: Path | None = None,
    experiment_results: Path | None = None,
) -> dict[str, object]:
    project_root = project_root.resolve()
    device = _device(device_name)
    samples = tuple(
        retain_pure_anchored_systems(
            load_vle_samples(project_root / "dataset"),
            minimum_temperatures=2,
        )
    )
    shapley_frames = []
    interaction_frames = []
    sensitivity_frames = []
    contexts = []
    for seed in SEEDS:
        context = _load_seed_context(project_root, samples, seed, device)
        contexts.append(context)
        selected = _stratified_sample(context.test, max_samples_per_seed, seed)
        shapley_frames.append(modality_shapley_table(context, selected, device, batch_size))
        interaction_frames.append(interaction_table(context, selected, device, batch_size))
        sensitivity_frames.append(sensitivity_table(context, device))
        if device.type == "cuda":
            torch.cuda.empty_cache()
    shapley = pd.concat(shapley_frames, ignore_index=True)
    interactions = pd.concat(interaction_frames, ignore_index=True)
    sensitivities = pd.concat(sensitivity_frames, ignore_index=True)
    formal_output_root = project_root / "analysis/interpretability_c1_final"
    output_root = (output_root or formal_output_root).resolve()
    result_paths = {
        "modality_shapley": output_root / "results/modality_shapley.csv",
        "pair_interactions": output_root / "results/pair_interactions.csv",
        "thermodynamic_sensitivity": output_root / "results/thermodynamic_sensitivity.csv",
    }
    for name, frame in (
        ("modality_shapley", shapley),
        ("pair_interactions", interactions),
        ("thermodynamic_sensitivity", sensitivities),
    ):
        _atomic_csv(frame, result_paths[name])
    figure_paths = _plot(
        shapley,
        interactions,
        sensitivities,
        output_root / "figures/Figure_c1_interpretability",
    )
    report_path = output_root / "reports/interpretability_report.md"
    selected_stages = {context.seed: context.selected_stage for context in contexts}
    _report(report_path, shapley, interactions, sensitivities, selected_stages)
    inputs = []
    for context in contexts:
        inputs.extend([
            context.checkpoint,
            context.split_path,
            project_root / FINAL_RESULT_ROOT / f"seed_{context.seed}/manifest.json",
        ])
    inputs.extend(sorted((project_root / "dataset").glob("*.xlsx")))
    inputs.extend([
        project_root / "cache/rdkit_2d_raw24_v1.npz",
        project_root / "cache/unimolv2_84m.npz",
        project_root / "cache/functional_groups_thermoformer_v1.npz",
        project_root / "assets/rdkit_descriptors.json",
        project_root / "assets/functional_groups.json",
        project_root / "experiments/explainability/c1_final/config.json",
    ])
    artifacts = [*result_paths.values(), *figure_paths, report_path]
    git_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=project_root, text=True
    ).strip()
    code_paths = [
        project_root / "src/interpretability/c1_final.py",
        project_root / "src/interpretability/core.py",
        project_root / "src/interpretability/selection.py",
        project_root / "scripts/run_interpretability.py",
    ]
    manifest = {
        "status": "completed",
        "analysis": "C1 final five-seed grouped Shapley and thermodynamic sensitivity",
        "analysis_status": (
            "confirmatory_descriptive"
            if output_root == formal_output_root.resolve()
            else "diagnostic_smoke"
        ),
        "git_commit": git_commit,
        "protocol": SPLIT_PROTOCOL,
        "checkpoint_protocol": FINAL_PROTOCOL,
        "seeds": list(SEEDS),
        "selected_stages": {str(key): value for key, value in selected_stages.items()},
        "evaluation_partition": "test",
        "explanation_mode": "teacher_forced_observed_T_P_x",
        "max_samples_per_seed": max_samples_per_seed,
        "row_counts": {
            "modality_shapley": len(shapley),
            "pair_interactions": len(interactions),
            "thermodynamic_sensitivity": len(sensitivities),
        },
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "torch": torch.__version__,
            "device": str(device),
            "cuda": torch.version.cuda,
        },
        "inputs": {
            path.relative_to(project_root).as_posix(): artifact_sha256(path)
            for path in inputs
        },
        "analysis_code": {
            path.relative_to(project_root).as_posix(): artifact_sha256(path)
            for path in code_paths
        },
        "artifacts": {
            path.relative_to(project_root).as_posix(): artifact_sha256(path)
            for path in artifacts
        },
    }
    manifest_path = output_root / "reports/analysis_manifest.json"
    atomic_write_json(manifest_path, manifest)
    if experiment_results is None and output_root == formal_output_root.resolve():
        experiment_results = project_root / "experiments/explainability/c1_final/results.md"
    if experiment_results is not None:
        atomic_write_text(experiment_results, report_path.read_text(encoding="utf-8"))
    return {**manifest, "manifest": manifest_path.relative_to(project_root).as_posix()}
