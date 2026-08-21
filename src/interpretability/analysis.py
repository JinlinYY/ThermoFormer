"""End-to-end ThermoFormer interpretation analyses on locked test partitions."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
import torch

from ..data import (
    VLESample,
    VLETensorDataset,
    collate_vle,
    load_vle_samples,
    retain_pure_anchored_systems,
)
from ..representation import UniMolV2Encoder
from ..splits import DatasetPartitions, load_split_assignment, sample_id, system_id
from ..thermo import solve_isobaric, solve_isothermal
from .core import (
    ModelBundle,
    load_thermoformer_checkpoint,
    padded_state_tensors,
    pairwise_log_relative_volatility,
    stable_pca_scores,
    thermodynamic_response_sensitivity,
    vapor_from_outputs,
)
from .selection import (
    canonical_state,
    eligible_ternary_systems,
    experimental_azeotrope_proxy,
    grouped_systems,
    molecule_family,
    select_best_validation_seed,
    system_family,
)


FULL_PROTOCOL = "overall_binary_ternary"
PAIRWISE_PROTOCOL = "a3_pairwise_only.on.overall_binary_ternary"
SEEDS = tuple(range(5))


@dataclass
class InterpretabilityContext:
    project_root: Path
    device: torch.device
    samples: tuple[VLESample, ...]
    feature_map: dict[str, np.ndarray]
    best_seed: int
    best_split: DatasetPartitions
    full: ModelBundle
    pairwise: ModelBundle


def load_context(project_root: Path, device_name: str = "auto") -> InterpretabilityContext:
    project_root = project_root.resolve()
    if device_name == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    elif device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    else:
        device = torch.device(device_name)
    samples = tuple(
        retain_pure_anchored_systems(
            load_vle_samples(project_root / "dataset"),
            minimum_temperatures=2,
        )
    )
    unique_smiles = sorted({smile for sample in samples for smile in sample.smiles})
    feature_map = UniMolV2Encoder(project_root / "cache" / "unimolv2_84m.npz").encode(
        unique_smiles
    )
    best_seed = select_best_validation_seed(project_root / "results" / FULL_PROTOCOL)
    split = load_split_assignment(
        project_root / "splits" / FULL_PROTOCOL / f"seed_{best_seed}.json",
        samples,
    )
    full = load_thermoformer_checkpoint(
        project_root / "checkpoints" / FULL_PROTOCOL / f"seed_{best_seed}" / "best_model.pt",
        device,
    )
    pairwise = load_thermoformer_checkpoint(
        project_root
        / "checkpoints"
        / "ablation"
        / PAIRWISE_PROTOCOL
        / f"seed_{best_seed}"
        / "best_model.pt",
        device,
    )
    return InterpretabilityContext(
        project_root=project_root,
        device=device,
        samples=samples,
        feature_map=feature_map,
        best_seed=best_seed,
        best_split=split,
        full=full,
        pairwise=pairwise,
    )


def _chunks(values: Sequence[VLESample], size: int) -> Iterable[Sequence[VLESample]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _model_at_midcomposition(
    bundle: ModelBundle,
    rows: Sequence[VLESample],
    feature_map: dict[str, np.ndarray],
    device: torch.device,
) -> float:
    smiles, _, _, _ = canonical_state(rows[0])
    temperature = np.asarray([np.median([sample.temperature_k for sample in rows])])
    molecules, temperature_t, _, x, mask = padded_state_tensors(
        smiles,
        feature_map,
        temperature,
        np.asarray([101.325]),
        np.asarray([[0.5, 0.5]]),
        device,
    )
    with torch.no_grad():
        state = solve_isothermal(
            bundle.model,
            molecules,
            temperature_t,
            x,
            mask,
            iterations=48,
            strict=False,
        )
        output = bundle.model(molecules, temperature_t, state.pressure_kpa, x, mask)
    return float(output.excess_gibbs_rt[0, 0].cpu())


def select_representative_cases(context: InterpretabilityContext) -> dict[str, tuple[str, ...]]:
    groups = {
        key: rows
        for key, rows in grouped_systems(context.best_split.test).items()
        if len(key) == 2
    }
    complete = {
        key: rows
        for key, rows in groups.items()
        if len(rows) >= 12
        and min(canonical_state(row)[2][0] for row in rows) <= 0.05
        and max(canonical_state(row)[2][0] for row in rows) >= 0.94
    }
    if not complete:
        raise RuntimeError("No composition-complete binary test systems are available")
    scores = {
        key: _model_at_midcomposition(
            context.full, rows, context.feature_map, context.device
        )
        for key, rows in complete.items()
    }
    alkane_pairs = [
        key
        for key in complete
        if all(molecule_family(smile) == "alkane/cycloalkane" for smile in key)
    ]
    water_alcohol = [
        key
        for key in complete
        if {molecule_family(smile) for smile in key} >= {"water", "alcohol/polyol"}
    ]
    azeotropes = [
        key for key, rows in complete.items() if experimental_azeotrope_proxy(rows)[0]
    ]
    if not alkane_pairs or not water_alcohol or not azeotropes:
        raise RuntimeError("Required chemistry-defined representative test cases are unavailable")
    return {
        "lowest-|gE| hydrocarbon candidate": min(
            alkane_pairs, key=lambda key: abs(scores[key])
        ),
        "water/alcohol hydrogen bonding": max(water_alcohol, key=lambda key: len(complete[key])),
        "model-inferred positive deviation": max(scores, key=scores.get),
        "model-inferred negative deviation": min(scores, key=scores.get),
        "experimental azeotrope proxy": max(azeotropes, key=lambda key: len(complete[key])),
    }


def interaction_attribution_table(
    context: InterpretabilityContext,
    representative: dict[str, tuple[str, ...]],
    batch_size: int = 256,
) -> pd.DataFrame:
    """Pair potentials cross-validated by mean-embedding component masking."""
    category_by_system: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for category, key in representative.items():
        category_by_system[key].append(category)
    records = []
    for seed in SEEDS:
        split = load_split_assignment(
            context.project_root / "splits" / FULL_PROTOCOL / f"seed_{seed}.json",
            context.samples,
        )
        bundle = load_thermoformer_checkpoint(
            context.project_root
            / "checkpoints"
            / FULL_PROTOCOL
            / f"seed_{seed}"
            / "best_model.pt",
            context.device,
        )
        training_smiles = sorted({value for row in split.train for value in row.smiles})
        baseline = torch.from_numpy(
            np.mean([context.feature_map[value] for value in training_smiles], axis=0).astype(
                np.float32
            )
        ).to(context.device)
        test_rows = list(split.test)
        for rows in _chunks(test_rows, batch_size):
            dataset = VLETensorDataset(rows, context.feature_map)
            batch = collate_vle([dataset[index] for index in range(len(dataset))]).to(
                context.device
            )
            with torch.no_grad():
                output = bundle.model(
                    batch.molecules,
                    batch.temperature_k,
                    batch.pressure_kpa,
                    batch.x,
                    batch.mask,
                )
                nonideal_y, ideal_y = vapor_from_outputs(output, batch.x, batch.mask)
                masked_outputs = []
                masked_vapors = []
                for component in range(3):
                    perturbed = batch.molecules.clone()
                    perturbed[:, component] = baseline
                    masked = bundle.model(
                        perturbed,
                        batch.temperature_k,
                        batch.pressure_kpa,
                        batch.x,
                        batch.mask,
                    )
                    masked_outputs.append(masked)
                    masked_vapors.append(vapor_from_outputs(masked, batch.x, batch.mask)[0])
            if output.pair_interactions is None or output.excess_gibbs_rt is None:
                raise RuntimeError("Full ThermoFormer did not expose interaction potentials")
            for row_index, sample in enumerate(rows):
                count = sample.component_count
                active = slice(0, count)
                log_gamma = output.log_gamma[row_index, active]
                sample_pair_values = [
                    abs(float(output.pair_interactions[row_index, first, second].cpu()))
                    for first in range(count)
                    for second in range(first + 1, count)
                ]
                pair_normalizer = max(sum(sample_pair_values), 1e-12)
                mask_log_gamma = []
                mask_y = []
                mask_ge = []
                for component in range(count):
                    mask_log_gamma.append(
                        float(
                            torch.mean(
                                torch.abs(
                                    masked_outputs[component].log_gamma[row_index, active]
                                    - log_gamma
                                )
                            ).cpu()
                        )
                    )
                    mask_y.append(
                        float(
                            torch.mean(
                                torch.abs(
                                    masked_vapors[component][row_index, active]
                                    - nonideal_y[row_index, active]
                                )
                            ).cpu()
                        )
                    )
                    mask_ge.append(
                        abs(
                            float(
                                masked_outputs[component].excess_gibbs_rt[row_index, 0].cpu()
                                - output.excess_gibbs_rt[row_index, 0].cpu()
                            )
                        )
                    )
                log_shifts = [
                    abs(float((log_gamma[first] - log_gamma[second]).cpu()))
                    for first in range(count)
                    for second in range(first + 1, count)
                ]
                categories = category_by_system.get(sample.system_key, [])
                for first in range(count):
                    for second in range(first + 1, count):
                        interaction = float(
                            output.pair_interactions[row_index, first, second].cpu()
                        )
                        records.append(
                            {
                                "seed": seed,
                                "sample_id": sample_id(sample),
                                "system_id": system_id(sample),
                                "component_count": count,
                                "representative_categories": "; ".join(categories),
                                "chemical_family": system_family(sample.smiles),
                                "component_i": first + 1,
                                "component_j": second + 1,
                                "smiles_i": sample.smiles[first],
                                "smiles_j": sample.smiles[second],
                                "name_i": sample.names[first],
                                "name_j": sample.names[second],
                                "temperature_k": sample.temperature_k,
                                "pressure_kpa": sample.pressure_kpa,
                                "x_i": sample.liquid_composition[first],
                                "x_j": sample.liquid_composition[second],
                                "learned_pair_potential": interaction,
                                "absolute_pair_potential": abs(interaction),
                                "normalized_absolute_pair_weight": abs(interaction)
                                / pair_normalizer,
                                "composition_weighted_pair_contribution": sample.liquid_composition[
                                    first
                                ]
                                * sample.liquid_composition[second]
                                * interaction,
                                "component_i_mask_delta_log_gamma": mask_log_gamma[first],
                                "component_j_mask_delta_log_gamma": mask_log_gamma[second],
                                "component_i_mask_delta_y": mask_y[first],
                                "component_j_mask_delta_y": mask_y[second],
                                "component_i_mask_delta_ge_rt": mask_ge[first],
                                "component_j_mask_delta_ge_rt": mask_ge[second],
                                "mean_pair_mask_delta_log_gamma": 0.5
                                * (mask_log_gamma[first] + mask_log_gamma[second]),
                                "mean_pair_mask_delta_y": 0.5
                                * (mask_y[first] + mask_y[second]),
                                "mean_abs_log_gamma": float(torch.mean(torch.abs(log_gamma)).cpu()),
                                "excess_gibbs_rt": float(
                                    output.excess_gibbs_rt[row_index, 0].cpu()
                                ),
                                "mean_abs_log_relative_volatility_shift": float(
                                    np.mean(log_shifts)
                                ),
                                "vle_deviation_from_ideality": float(
                                    torch.mean(
                                        torch.abs(
                                            nonideal_y[row_index, active]
                                            - ideal_y[row_index, active]
                                        )
                                    ).cpu()
                                ),
                                "relative_volatility_ij": float(
                                    torch.exp(
                                        pairwise_log_relative_volatility(
                                            output, first, second
                                        )[row_index].clamp(-20.0, 20.0)
                                    ).cpu()
                                ),
                                "evaluation_partition": "test",
                                "mask_baseline": "mean training-set Uni-Mol token",
                            }
                        )
        del bundle
        if context.device.type == "cuda":
            torch.cuda.empty_cache()
    return pd.DataFrame(records)


def composition_nonideality_table(
    context: InterpretabilityContext,
    representative: dict[str, tuple[str, ...]],
) -> pd.DataFrame:
    groups = grouped_systems(context.best_split.test)
    categories_by_system: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for category, system in representative.items():
        categories_by_system[system].append(category)
    records: list[dict[str, object]] = []
    latent_vectors: list[np.ndarray] = []
    for system, categories in categories_by_system.items():
        rows = groups[system]
        smiles, names, _, _ = canonical_state(rows[0])
        temperature = float(np.median([row.temperature_k for row in rows]))
        pressure = float(np.median([row.pressure_kpa for row in rows]))
        grid = np.linspace(0.01, 0.99, 99)
        compositions = np.column_stack([grid, 1.0 - grid])
        molecules, temperature_t, pressure_t, x, mask = padded_state_tensors(
            smiles,
            context.feature_map,
            np.asarray([temperature]),
            np.asarray([pressure]),
            compositions,
            context.device,
        )
        with torch.no_grad():
            isothermal = solve_isothermal(
                context.full.model,
                molecules,
                temperature_t,
                x,
                mask,
                iterations=48,
                strict=False,
            )
            isobaric = solve_isobaric(
                context.full.model,
                molecules,
                pressure_t,
                x,
                mask,
                iterations=48,
                strict=False,
            )
            outputs = {
                "isothermal": context.full.model(
                    molecules, temperature_t, isothermal.pressure_kpa, x, mask
                ),
                "isobaric": context.full.model(
                    molecules, isobaric.temperature_k, pressure_t, x, mask
                ),
            }
        states = {"isothermal": isothermal, "isobaric": isobaric}
        azeotrope, experimental_x = experimental_azeotrope_proxy(rows)
        category_label = "; ".join(sorted(categories))
        for direction in ("isothermal", "isobaric"):
            state = states[direction]
            output = outputs[direction]
            if output.nonideality_tokens is None or output.excess_gibbs_rt is None:
                raise RuntimeError("Latent nonideality outputs are unavailable")
            weighted_tokens = (
                output.nonideality_tokens[:, :2] * x[:, :2].unsqueeze(-1)
            ).reshape(len(grid), -1)
            for index, value in enumerate(grid):
                latent_vectors.append(weighted_tokens[index].cpu().numpy())
                records.append(
                    {
                        "category": category_label,
                        "system_id": system_id(rows[0]),
                        "chemical_family": system_family(smiles),
                        "direction": direction,
                        "smiles_1": smiles[0],
                        "smiles_2": smiles[1],
                        "name_1": names[0],
                        "name_2": names[1],
                        "input_temperature_k": temperature if direction == "isothermal" else None,
                        "input_pressure_kpa": pressure if direction == "isobaric" else None,
                        "x_1": value,
                        "x_2": 1.0 - value,
                        "pair_interaction_12": float(output.pair_interactions[index, 0, 1].cpu()),
                        "pair_contribution_ge_rt": float(
                            value * (1.0 - value) * output.pair_interactions[index, 0, 1].cpu()
                        ),
                        "latent_nonideality_ge_rt": float(output.excess_gibbs_rt[index, 0].cpu()),
                        "latent_weighted_token_norm": float(
                            torch.linalg.vector_norm(weighted_tokens[index]).cpu()
                        ),
                        "log_gamma_1": float(output.log_gamma[index, 0].cpu()),
                        "log_gamma_2": float(output.log_gamma[index, 1].cpu()),
                        "relative_volatility_12": float(
                            torch.exp(
                                pairwise_log_relative_volatility(output, 0, 1)[index].clamp(
                                    -20.0, 20.0
                                )
                            ).cpu()
                        ),
                        "predicted_temperature_k": float(state.temperature_k[index, 0].cpu()),
                        "predicted_pressure_kpa": float(state.pressure_kpa[index, 0].cpu()),
                        "predicted_y_1": float(state.y[index, 0].cpu()),
                        "predicted_y_2": float(state.y[index, 1].cpu()),
                        "solver_converged": bool(state.converged[index, 0].cpu()),
                        "experimental_azeotrope_proxy": azeotrope,
                        "experimental_azeotrope_x1": experimental_x,
                        "selected_seed": context.best_seed,
                        "selection_partition": "test",
                    }
                )
    scores, explained = stable_pca_scores(np.stack(latent_vectors), components=2)
    for index, record in enumerate(records):
        record["latent_pc1"] = scores[index, 0]
        record["latent_pc2"] = scores[index, 1]
        record["latent_pc1_explained_variance"] = explained[0]
        record["latent_pc2_explained_variance"] = explained[1]
    return pd.DataFrame(records)


def _representative_ternary(
    context: InterpretabilityContext,
) -> tuple[tuple[str, ...], list[VLESample]]:
    eligible = eligible_ternary_systems(context.samples, context.best_split.test)
    if not eligible:
        raise RuntimeError("No held-out ternary has all three experimental binary subsystems")
    groups = grouped_systems(context.best_split.test)
    system = max(eligible, key=lambda key: len(groups[key]))
    return system, groups[system]


def thermodynamic_sensitivity_table(
    context: InterpretabilityContext,
    representative: dict[str, tuple[str, ...]],
) -> pd.DataFrame:
    groups = grouped_systems(context.best_split.test)
    cases: list[tuple[str, tuple[str, ...], Sequence[VLESample]]] = []
    seen = set()
    for category in (
        "lowest-|gE| hydrocarbon candidate",
        "water/alcohol hydrogen bonding",
        "model-inferred positive deviation",
        "model-inferred negative deviation",
    ):
        system = representative[category]
        if system not in seen:
            cases.append((category, system, groups[system]))
            seen.add(system)
    ternary, ternary_rows = _representative_ternary(context)
    cases.append(("complete-subsystem ternary", ternary, ternary_rows))
    records = []
    for category, system, rows in cases:
        smiles, names, _, _ = canonical_state(rows[0])
        count = len(smiles)
        composition = np.full((1, count), 1.0 / count, dtype=float)
        temperature = float(np.median([row.temperature_k for row in rows]))
        molecules, temperature_t, _, x, mask = padded_state_tensors(
            smiles,
            context.feature_map,
            np.asarray([temperature]),
            np.asarray([101.325]),
            composition,
            context.device,
        )
        bundles = [("full", context.full)]
        if count == 3:
            bundles.append(("pairwise-only", context.pairwise))
        for model_kind, bundle in bundles:
            with torch.no_grad():
                state = solve_isothermal(
                    bundle.model,
                    molecules,
                    temperature_t,
                    x,
                    mask,
                    iterations=48,
                    strict=False,
                )
            response, temperature_response = thermodynamic_response_sensitivity(
                bundle.model,
                molecules,
                temperature_t,
                state.pressure_kpa.detach(),
                x,
                mask,
            )
            for affected in range(count):
                for increased in range(count):
                    records.append(
                        {
                            "category": category,
                            "system_id": system_id(rows[0]),
                            "chemical_family": system_family(smiles),
                            "model": model_kind,
                            "component_count": count,
                            "affected_component": affected + 1,
                            "increased_component": increased + 1,
                            "affected_smiles": smiles[affected],
                            "increased_smiles": smiles[increased],
                            "affected_name": names[affected],
                            "increased_name": names[increased],
                            "temperature_k": temperature,
                            "pressure_kpa": float(state.pressure_kpa[0, 0].cpu()),
                            "composition": ";".join(f"{value:.8f}" for value in composition[0]),
                            "d_log_gamma_i_d_closed_x_j": float(
                                response[affected, increased].cpu()
                            ),
                            "d_log_gamma_i_d_temperature_k": float(
                                temperature_response[affected].cpu()
                            ),
                            "response_direction": "increase j; remove from others proportionally",
                            "selected_seed": context.best_seed,
                            "selection_partition": "test",
                        }
                    )
    return pd.DataFrame(records)


def _prediction_system_key(row: pd.Series) -> tuple[str, ...]:
    return tuple(
        sorted(
            str(row[f"component_smiles_{index}"])
            for index in range(1, int(row["component_count"]) + 1)
        )
    )


def _add_relative_volatility_fields(
    record: dict[str, object],
    full_volatility: Sequence[float],
    pairwise_volatility: Sequence[float],
) -> None:
    """Add all ternary pairwise relative volatilities and model corrections."""
    for first, second in ((0, 1), (0, 2), (1, 2)):
        label = f"{first + 1}{second + 1}"
        full_alpha = float(full_volatility[first]) / max(
            float(full_volatility[second]), 1e-30
        )
        pairwise_alpha = float(pairwise_volatility[first]) / max(
            float(pairwise_volatility[second]), 1e-30
        )
        record[f"alpha_{label}_full"] = full_alpha
        record[f"alpha_{label}_pairwise"] = pairwise_alpha
        record[f"delta_log_alpha_{label}_full_minus_pairwise"] = math.log(
            max(full_alpha, 1e-30)
        ) - math.log(max(pairwise_alpha, 1e-30))


def experimental_manybody_rows(context: InterpretabilityContext) -> list[dict[str, object]]:
    eligible = set(eligible_ternary_systems(context.samples, context.samples))
    records: list[dict[str, object]] = []
    for seed in SEEDS:
        full = pd.read_csv(
            context.project_root / "results" / FULL_PROTOCOL / f"seed_{seed}" / "predictions.csv"
        )
        pairwise = pd.read_csv(
            context.project_root
            / "results"
            / "ablation"
            / "runs"
            / PAIRWISE_PROTOCOL
            / f"seed_{seed}"
            / "predictions.csv"
        )
        full = full.loc[full["component_count"].eq(3)].copy()
        pairwise = pairwise.loc[pairwise["component_count"].eq(3)].copy()
        full["eligible"] = full.apply(lambda row: _prediction_system_key(row) in eligible, axis=1)
        pairwise["eligible"] = pairwise.apply(
            lambda row: _prediction_system_key(row) in eligible, axis=1
        )
        full = full.loc[full["eligible"]]
        pairwise = pairwise.loc[pairwise["eligible"]]
        merged = full.merge(
            pairwise,
            on=["sample_id", "direction"],
            suffixes=("_full", "_pairwise"),
            validate="one_to_one",
        )
        for _, row in merged.iterrows():
            system = tuple(
                sorted(str(row[f"component_smiles_{index}_full"]) for index in range(1, 4))
            )
            y_full = np.asarray([float(row[f"y_pred_{index}_full"]) for index in range(1, 4)])
            y_pair = np.asarray(
                [float(row[f"y_pred_{index}_pairwise"]) for index in range(1, 4)]
            )
            y_true = np.asarray([float(row[f"y_true_{index}_full"]) for index in range(1, 4)])
            gamma_full = np.asarray(
                [float(row[f"gamma_pred_{index}_full"]) for index in range(1, 4)]
            )
            gamma_pair = np.asarray(
                [float(row[f"gamma_pred_{index}_pairwise"]) for index in range(1, 4)]
            )
            volatility_full = gamma_full * np.asarray(
                [float(row[f"psat_pred_kpa_{index}_full"]) for index in range(1, 4)]
            )
            volatility_pair = gamma_pair * np.asarray(
                [float(row[f"psat_pred_kpa_{index}_pairwise"]) for index in range(1, 4)]
            )
            direction = str(row["direction"])
            if direction == "isothermal":
                target = float(row["target_pressure_kpa_full"])
                full_state = float(row["predicted_pressure_kpa_full"])
                pair_state = float(row["predicted_pressure_kpa_pairwise"])
                state_unit = "kPa"
            else:
                target = float(row["target_temperature_k_full"])
                full_state = float(row["predicted_temperature_k_full"])
                pair_state = float(row["predicted_temperature_k_pairwise"])
                state_unit = "K"
            record: dict[str, object] = {
                "record_type": "experimental_test",
                "seed": seed,
                "sample_id": row["sample_id"],
                "system_id": row["system_id_full"],
                "chemical_family": system_family(system),
                "direction": direction,
                "state_unit": state_unit,
                "target_state": target,
                "full_predicted_state": full_state,
                "pairwise_predicted_state": pair_state,
                "full_state_abs_error": abs(full_state - target),
                "pairwise_state_abs_error": abs(pair_state - target),
                "delta_state_error_pairwise_minus_full": abs(pair_state - target)
                - abs(full_state - target),
                "full_y_mae": float(np.mean(np.abs(y_full - y_true))),
                "pairwise_y_mae": float(np.mean(np.abs(y_pair - y_true))),
                "delta_y_error_pairwise_minus_full": float(
                    np.mean(np.abs(y_pair - y_true)) - np.mean(np.abs(y_full - y_true))
                ),
                "mean_abs_manybody_delta_log_gamma": float(
                    np.mean(np.abs(np.log(gamma_full) - np.log(gamma_pair)))
                ),
                "selection_rule": "held-out ternary with all three experimental binary subsystems",
            }
            _add_relative_volatility_fields(record, volatility_full, volatility_pair)
            for component in range(3):
                record[f"x_{component + 1}"] = float(row[f"x_{component + 1}_full"])
                record[f"y_true_{component + 1}"] = y_true[component]
                record[f"y_full_{component + 1}"] = y_full[component]
                record[f"y_pairwise_{component + 1}"] = y_pair[component]
                record[f"delta_y_{component + 1}_full_minus_pairwise"] = (
                    y_full[component] - y_pair[component]
                )
                record[f"gamma_full_{component + 1}"] = gamma_full[component]
                record[f"gamma_pairwise_{component + 1}"] = gamma_pair[component]
                record[f"delta_log_gamma_{component + 1}_full_minus_pairwise"] = math.log(
                    max(gamma_full[component], 1e-30)
                ) - math.log(max(gamma_pair[component], 1e-30))
                record[f"smiles_{component + 1}"] = row[
                    f"component_smiles_{component + 1}_full"
                ]
            records.append(record)
    return records


def simplex_manybody_rows(context: InterpretabilityContext) -> list[dict[str, object]]:
    system, rows = _representative_ternary(context)
    smiles, names, _, _ = canonical_state(rows[0])
    temperature = float(np.median([row.temperature_k for row in rows]))
    compositions = []
    for first in np.linspace(0.05, 0.90, 18):
        for second in np.linspace(0.05, 0.90, 18):
            third = 1.0 - first - second
            if third >= 0.05:
                compositions.append((first, second, third))
    composition_array = np.asarray(compositions, dtype=float)
    tensors = padded_state_tensors(
        smiles,
        context.feature_map,
        np.asarray([temperature]),
        np.asarray([101.325]),
        composition_array,
        context.device,
    )
    molecules, temperature_t, _, x, mask = tensors
    states = {}
    with torch.no_grad():
        for label, bundle in (("full", context.full), ("pairwise", context.pairwise)):
            states[label] = solve_isothermal(
                bundle.model,
                molecules,
                temperature_t,
                x,
                mask,
                iterations=48,
                strict=False,
            )
    records = []
    for index, composition in enumerate(compositions):
        full = states["full"]
        pairwise = states["pairwise"]
        log_gamma_full = torch.log(full.gamma[index, :3].clamp_min(1e-30))
        log_gamma_pair = torch.log(pairwise.gamma[index, :3].clamp_min(1e-30))
        alpha_full = full.gamma[index, :3] * full.psat_kpa[index, :3]
        alpha_pair = pairwise.gamma[index, :3] * pairwise.psat_kpa[index, :3]
        record: dict[str, object] = {
            "record_type": "simplex_scan",
            "seed": context.best_seed,
            "sample_id": None,
            "system_id": system_id(rows[0]),
            "chemical_family": system_family(smiles),
            "direction": "isothermal",
            "state_unit": "kPa",
            "target_state": None,
            "full_predicted_state": float(full.pressure_kpa[index, 0].cpu()),
            "pairwise_predicted_state": float(pairwise.pressure_kpa[index, 0].cpu()),
            "full_state_abs_error": None,
            "pairwise_state_abs_error": None,
            "delta_state_error_pairwise_minus_full": None,
            "full_y_mae": None,
            "pairwise_y_mae": None,
            "delta_y_error_pairwise_minus_full": None,
            "mean_abs_manybody_delta_log_gamma": float(
                torch.mean(torch.abs(log_gamma_full - log_gamma_pair)).cpu()
            ),
            "temperature_k": temperature,
            "selection_rule": "most composition-rich held-out eligible ternary in validation-selected seed",
        }
        _add_relative_volatility_fields(
            record,
            alpha_full.detach().cpu().tolist(),
            alpha_pair.detach().cpu().tolist(),
        )
        for component in range(3):
            record[f"x_{component + 1}"] = composition[component]
            record[f"y_true_{component + 1}"] = None
            record[f"y_full_{component + 1}"] = float(full.y[index, component].cpu())
            record[f"y_pairwise_{component + 1}"] = float(
                pairwise.y[index, component].cpu()
            )
            record[f"delta_y_{component + 1}_full_minus_pairwise"] = float(
                full.y[index, component].cpu() - pairwise.y[index, component].cpu()
            )
            record[f"gamma_full_{component + 1}"] = float(
                full.gamma[index, component].cpu()
            )
            record[f"gamma_pairwise_{component + 1}"] = float(
                pairwise.gamma[index, component].cpu()
            )
            record[f"delta_log_gamma_{component + 1}_full_minus_pairwise"] = float(
                log_gamma_full[component].cpu() - log_gamma_pair[component].cpu()
            )
            record[f"smiles_{component + 1}"] = smiles[component]
            record[f"name_{component + 1}"] = names[component]
        record["manybody_y_l1"] = sum(
            abs(float(record[f"delta_y_{component}_full_minus_pairwise"]))
            for component in range(1, 4)
        )
        records.append(record)
    return records


def third_component_path_rows(context: InterpretabilityContext) -> list[dict[str, object]]:
    """Trace addition of component 3 from the corresponding A-B simplex edge."""
    system, rows = _representative_ternary(context)
    smiles, names, _, _ = canonical_state(rows[0])
    temperature = float(np.median([row.temperature_k for row in rows]))
    ab_ratios = []
    for row in rows:
        _, _, liquid, _ = canonical_state(row)
        if liquid[0] + liquid[1] > 1e-8:
            ab_ratios.append(liquid[0] / (liquid[0] + liquid[1]))
    ab_ratio = float(np.median(ab_ratios)) if ab_ratios else 0.5
    third_fractions = np.linspace(0.0, 0.90, 19)
    compositions = np.asarray(
        [
            (ab_ratio * (1.0 - third), (1.0 - ab_ratio) * (1.0 - third), third)
            for third in third_fractions
        ],
        dtype=float,
    )
    molecules, temperature_t, _, x, mask = padded_state_tensors(
        smiles,
        context.feature_map,
        np.asarray([temperature]),
        np.asarray([101.325]),
        compositions,
        context.device,
    )
    states = {}
    with torch.no_grad():
        for label, bundle in (("full", context.full), ("pairwise", context.pairwise)):
            states[label] = solve_isothermal(
                bundle.model,
                molecules,
                temperature_t,
                x,
                mask,
                iterations=48,
                strict=False,
            )
    binary_molecules, binary_temperature, _, binary_x, binary_mask = padded_state_tensors(
        smiles[:2],
        context.feature_map,
        np.asarray([temperature]),
        np.asarray([101.325]),
        np.asarray([[ab_ratio, 1.0 - ab_ratio]], dtype=float),
        context.device,
    )
    binary_states = {}
    with torch.no_grad():
        for label, bundle in (("full", context.full), ("pairwise", context.pairwise)):
            binary_states[label] = solve_isothermal(
                bundle.model,
                binary_molecules,
                binary_temperature,
                binary_x,
                binary_mask,
                iterations=48,
                strict=False,
            )
    baseline_log_gamma = {
        label: torch.log(state.gamma[0, :2].clamp_min(1e-30))
        for label, state in binary_states.items()
    }
    baseline_log_alpha_12 = {
        label: torch.log(
            (state.gamma[0, 0] * state.psat_kpa[0, 0])
            / (state.gamma[0, 1] * state.psat_kpa[0, 1]).clamp_min(1e-30)
        )
        for label, state in binary_states.items()
    }
    boundary_log_gamma = {
        label: torch.log(state.gamma[0, :2].clamp_min(1e-30))
        for label, state in states.items()
    }
    boundary_log_alpha_12 = {
        label: torch.log(
            (state.gamma[0, 0] * state.psat_kpa[0, 0])
            / (state.gamma[0, 1] * state.psat_kpa[0, 1]).clamp_min(1e-30)
        )
        for label, state in states.items()
    }
    records = []
    for index, composition in enumerate(compositions):
        full = states["full"]
        pairwise = states["pairwise"]
        log_gamma_full = torch.log(full.gamma[index, :3].clamp_min(1e-30))
        log_gamma_pair = torch.log(pairwise.gamma[index, :3].clamp_min(1e-30))
        volatility_full = full.gamma[index, :3] * full.psat_kpa[index, :3]
        volatility_pair = pairwise.gamma[index, :3] * pairwise.psat_kpa[index, :3]
        record: dict[str, object] = {
            "record_type": "third_component_path",
            "seed": context.best_seed,
            "sample_id": None,
            "system_id": system_id(rows[0]),
            "chemical_family": system_family(smiles),
            "direction": "isothermal",
            "state_unit": "kPa",
            "target_state": None,
            "full_predicted_state": float(full.pressure_kpa[index, 0].cpu()),
            "pairwise_predicted_state": float(pairwise.pressure_kpa[index, 0].cpu()),
            "temperature_k": temperature,
            "third_component_fraction": float(third_fractions[index]),
            "ab_edge_ratio_x1_over_x1_plus_x2": ab_ratio,
            "selection_rule": "representative eligible ternary; preserve measured median A:B ratio",
            "mean_abs_manybody_delta_log_gamma": float(
                torch.mean(torch.abs(log_gamma_full - log_gamma_pair)).cpu()
            ),
        }
        for label in ("full", "pairwise"):
            for component in range(2):
                record[
                    f"ternary_x3_zero_minus_binary_log_gamma_{component + 1}_{label}"
                ] = float(
                    boundary_log_gamma[label][component].cpu()
                    - baseline_log_gamma[label][component].cpu()
                )
            record[f"ternary_x3_zero_minus_binary_log_alpha_12_{label}"] = float(
                boundary_log_alpha_12[label].cpu() - baseline_log_alpha_12[label].cpu()
            )
        _add_relative_volatility_fields(
            record,
            volatility_full.detach().cpu().tolist(),
            volatility_pair.detach().cpu().tolist(),
        )
        record["delta_log_alpha_12_from_true_binary_full"] = float(
            torch.log(volatility_full[0] / volatility_full[1]).cpu()
            - baseline_log_alpha_12["full"].cpu()
        )
        record["delta_log_alpha_12_from_true_binary_pairwise"] = float(
            torch.log(volatility_pair[0] / volatility_pair[1]).cpu()
            - baseline_log_alpha_12["pairwise"].cpu()
        )
        for component in range(3):
            record[f"x_{component + 1}"] = composition[component]
            record[f"y_true_{component + 1}"] = None
            record[f"y_full_{component + 1}"] = float(full.y[index, component].cpu())
            record[f"y_pairwise_{component + 1}"] = float(pairwise.y[index, component].cpu())
            record[f"delta_y_{component + 1}_full_minus_pairwise"] = float(
                full.y[index, component].cpu() - pairwise.y[index, component].cpu()
            )
            record[f"gamma_full_{component + 1}"] = float(full.gamma[index, component].cpu())
            record[f"gamma_pairwise_{component + 1}"] = float(
                pairwise.gamma[index, component].cpu()
            )
            record[f"delta_log_gamma_{component + 1}_full_minus_pairwise"] = float(
                log_gamma_full[component].cpu() - log_gamma_pair[component].cpu()
            )
            if component < 2:
                record[f"delta_log_gamma_{component + 1}_from_true_binary_full"] = float(
                    log_gamma_full[component].cpu()
                    - baseline_log_gamma["full"][component].cpu()
                )
                record[
                    f"delta_log_gamma_{component + 1}_from_true_binary_pairwise"
                ] = float(
                    log_gamma_pair[component].cpu()
                    - baseline_log_gamma["pairwise"][component].cpu()
                )
            else:
                record[f"delta_log_gamma_{component + 1}_from_true_binary_full"] = None
                record[f"delta_log_gamma_{component + 1}_from_true_binary_pairwise"] = None
            record[f"smiles_{component + 1}"] = smiles[component]
            record[f"name_{component + 1}"] = names[component]
        record["manybody_y_l1"] = sum(
            abs(float(record[f"delta_y_{component}_full_minus_pairwise"]))
            for component in range(1, 4)
        )
        records.append(record)
    return records


def manybody_effects_table(context: InterpretabilityContext) -> pd.DataFrame:
    return pd.DataFrame(
        experimental_manybody_rows(context)
        + simplex_manybody_rows(context)
        + third_component_path_rows(context)
    )
