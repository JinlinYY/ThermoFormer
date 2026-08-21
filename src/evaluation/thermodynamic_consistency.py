"""Independent physical-validity metrics for ThermoFormer ablations."""

from __future__ import annotations

import itertools
from collections import OrderedDict
from typing import Any, Sequence

import numpy as np
import torch
from torch import Tensor, nn

from ..data import VLESample, VLETensorDataset, collate_vle
from ..splits import system_id
from ..thermo import equilibrium_at_tp, solve_isobaric, solve_isothermal


def simplex_tangent_directions(
    component_count: int,
    *,
    dtype: torch.dtype = torch.float32,
    device: torch.device | None = None,
) -> Tensor:
    """Return an orthonormal basis whose directions preserve ``sum(x)=1``."""
    if component_count < 2:
        raise ValueError("A composition simplex needs at least two components")
    basis = torch.zeros(
        component_count,
        component_count - 1,
        dtype=dtype,
        device=device,
    )
    for index in range(component_count - 1):
        basis[index, index] = 1.0
        basis[-1, index] = -1.0
    orthonormal, _ = torch.linalg.qr(basis, mode="reduced")
    return orthonormal.T


def gibbs_duhem_residuals(
    model: nn.Module,
    molecules: Tensor,
    temperature_k: Tensor,
    pressure_kpa: Tensor,
    x: Tensor,
    mask: Tensor,
) -> Tensor:
    """Evaluate directional ``sum_i x_i d ln(gamma_i)`` using autograd."""
    residuals: list[Tensor] = []
    for sample_index in range(x.shape[0]):
        count = int(mask[sample_index].sum().item())
        sample_x = x[sample_index : sample_index + 1].detach().clone().requires_grad_(True)
        output = model(
            molecules[sample_index : sample_index + 1],
            temperature_k[sample_index : sample_index + 1],
            pressure_kpa[sample_index : sample_index + 1],
            sample_x,
            mask[sample_index : sample_index + 1],
        )
        directions = simplex_tangent_directions(
            count,
            dtype=sample_x.dtype,
            device=sample_x.device,
        )
        for direction in directions:
            derivatives = []
            for component in range(count):
                value = output.log_gamma[0, component]
                if value.requires_grad:
                    gradient = torch.autograd.grad(
                        value,
                        sample_x,
                        retain_graph=True,
                        create_graph=False,
                        allow_unused=True,
                    )[0]
                else:
                    gradient = None
                derivative = (
                    (gradient[0, :count] * direction).sum()
                    if gradient is not None
                    else sample_x.sum() * 0.0
                )
                derivatives.append(derivative)
            residuals.append(
                (
                    sample_x[0, :count]
                    * torch.stack(derivatives)
                ).sum().abs()
            )
    if not residuals:
        return torch.empty(0, dtype=x.dtype, device=x.device)
    return torch.stack(residuals)


def gibbs_duhem_residuals_finite_difference(
    model: nn.Module,
    molecules: Tensor,
    temperature_k: Tensor,
    pressure_kpa: Tensor,
    x: Tensor,
    mask: Tensor,
    step: float = 1e-4,
) -> Tensor:
    """Finite-difference validation of the tangent autograd residual."""
    residuals: list[Tensor] = []
    with torch.no_grad():
        for sample_index in range(x.shape[0]):
            count = int(mask[sample_index].sum().item())
            directions = simplex_tangent_directions(
                count, dtype=x.dtype, device=x.device
            )
            for direction in directions:
                padded = torch.zeros_like(x[sample_index])
                padded[:count] = direction
                upper_x = x[sample_index : sample_index + 1] + step * padded
                lower_x = x[sample_index : sample_index + 1] - step * padded
                if bool((upper_x[:, :count] <= 0.0).any()) or bool(
                    (lower_x[:, :count] <= 0.0).any()
                ):
                    continue
                upper = model(
                    molecules[sample_index : sample_index + 1],
                    temperature_k[sample_index : sample_index + 1],
                    pressure_kpa[sample_index : sample_index + 1],
                    upper_x,
                    mask[sample_index : sample_index + 1],
                ).log_gamma[0, :count]
                lower = model(
                    molecules[sample_index : sample_index + 1],
                    temperature_k[sample_index : sample_index + 1],
                    pressure_kpa[sample_index : sample_index + 1],
                    lower_x,
                    mask[sample_index : sample_index + 1],
                ).log_gamma[0, :count]
                derivative = (upper - lower) / (2.0 * step)
                residuals.append(
                    (x[sample_index, :count] * derivative).sum().abs()
                )
    if not residuals:
        return torch.empty(0, dtype=x.dtype, device=x.device)
    return torch.stack(residuals)


def composition_closure_metrics(x: Tensor, y: Tensor, mask: Tensor) -> dict[str, float]:
    """Report liquid/vapor closure and component-bound violations."""
    present_x = x * mask
    present_y = y * mask
    values = y[mask.bool()]
    return {
        "x_closure_mean_abs": float((present_x.sum(-1) - 1.0).abs().mean()),
        "y_closure_mean_abs": float((present_y.sum(-1) - 1.0).abs().mean()),
        "fraction_y_below_zero": float((values < 0.0).float().mean()),
        "fraction_y_above_one": float((values > 1.0).float().mean()),
    }


def phase_curve_smoothness(
    coordinate: np.ndarray,
    values: np.ndarray,
) -> dict[str, float]:
    """Measure smoothness without treating physically nonmonotonic curves as invalid."""
    coordinate = np.asarray(coordinate, dtype=float)
    values = np.asarray(values, dtype=float)
    if coordinate.ndim != 1 or values.shape[0] != coordinate.size or coordinate.size < 4:
        raise ValueError("A phase curve needs one coordinate and at least four states")
    if values.ndim == 1:
        values = values[:, None]
    segment = np.diff(values, axis=0)
    total_variation = float(np.linalg.norm(segment, axis=1).sum())
    first = np.gradient(values, coordinate, axis=0, edge_order=2)
    first_jump = np.linalg.norm(np.diff(first, axis=0), axis=1)
    second = np.gradient(first, coordinate, axis=0, edge_order=2)
    second_magnitude = np.linalg.norm(second, axis=1)
    return {
        "total_variation": total_variation,
        "first_derivative_jump_p95": float(np.percentile(first_jump, 95.0)),
        "second_derivative_magnitude_mean": float(second_magnitude.mean()),
    }


def summarize_absolute(values: Tensor | np.ndarray, prefix: str) -> dict[str, Any]:
    """Summarize a residual distribution without hiding an empty observable."""
    array = np.asarray(
        values.detach().cpu().numpy() if isinstance(values, Tensor) else values,
        dtype=float,
    )
    array = np.abs(array[np.isfinite(array)])
    if array.size == 0:
        return {f"{prefix}_mean_abs": None, f"{prefix}_p95_abs": None, f"{prefix}_max_abs": None}
    return {
        f"{prefix}_mean_abs": float(array.mean()),
        f"{prefix}_p95_abs": float(np.percentile(array, 95.0)),
        f"{prefix}_max_abs": float(array.max()),
    }


def combined_nonphysical_rate(
    ordinary_failures: int,
    ordinary_predictions: int,
    pure_limit_errors: Sequence[float],
    pure_limit_threshold: float,
) -> float | None:
    """Combine observed-state and synthetic near-pure prediction checks."""
    pure = np.asarray(pure_limit_errors, dtype=float)
    pure_failures = int(
        np.sum(~np.isfinite(pure) | (np.abs(pure) > pure_limit_threshold))
    )
    total = int(ordinary_predictions) + int(pure.size)
    return (int(ordinary_failures) + pure_failures) / total if total else None


def _representative_samples(
    samples: Sequence[VLESample], max_systems: int
) -> list[VLESample]:
    by_system: "OrderedDict[str, VLESample]" = OrderedDict()
    for sample in sorted(samples, key=lambda row: (system_id(row), row.temperature_k, row.pressure_kpa)):
        by_system.setdefault(system_id(sample), sample)
    return list(by_system.values())[:max_systems]


def _batch(
    samples: Sequence[VLESample],
    feature_map: dict[str, np.ndarray],
    device: torch.device,
):
    dataset = VLETensorDataset(samples, feature_map)
    return collate_vle([dataset[index] for index in range(len(dataset))]).to(device)


def _permutation_errors(model: nn.Module, batch, direct: bool) -> list[float]:
    errors: list[float] = []
    for index in range(batch.x.shape[0]):
        count = int(batch.mask[index].sum().item())
        molecules = batch.molecules[index : index + 1]
        temperature = batch.temperature_k[index : index + 1]
        pressure = batch.pressure_kpa[index : index + 1]
        x = batch.x[index : index + 1]
        mask = batch.mask[index : index + 1]
        if direct:
            originals = {
                direction: model.predict_direct(
                    molecules,
                    temperature,
                    pressure,
                    x,
                    mask,
                    direction=direction,
                )
                for direction in ("isothermal", "isobaric")
            }
        else:
            original = equilibrium_at_tp(model, molecules, temperature, pressure, x, mask)
        for permutation in itertools.permutations(range(count)):
            if permutation == tuple(range(count)):
                continue
            order = torch.tensor(permutation, device=x.device)
            padded_order = torch.cat(
                [order, torch.arange(count, x.shape[1], device=x.device)]
            )
            if direct:
                for direction, baseline in originals.items():
                    permuted = model.predict_direct(
                        molecules[:, padded_order],
                        temperature,
                        pressure,
                        x[:, padded_order],
                        mask[:, padded_order],
                        direction=direction,
                    )
                    errors.extend(
                        (permuted.y[:, :count] - baseline.y[:, order]).abs().flatten().tolist()
                    )
                    state_error = (
                        (permuted.pressure_kpa - baseline.pressure_kpa).abs()
                        if direction == "isothermal"
                        else (permuted.temperature_k - baseline.temperature_k).abs() / 100.0
                    )
                    errors.extend(state_error.flatten().tolist())
            else:
                permuted = equilibrium_at_tp(
                    model,
                    molecules[:, padded_order],
                    temperature,
                    pressure,
                    x[:, padded_order],
                    mask[:, padded_order],
                )
                for permuted_value, baseline_value in (
                    (permuted.y[:, :count], original.y[:, order]),
                    (permuted.gamma[:, :count], original.gamma[:, order]),
                    (permuted.psat_kpa[:, :count], original.psat_kpa[:, order]),
                ):
                    scale = baseline_value.abs().clamp_min(1.0)
                    errors.extend(((permuted_value - baseline_value).abs() / scale).flatten().tolist())
    return errors


def _pure_limit_errors(model: nn.Module, batch, direct: bool) -> tuple[list[float], list[float]]:
    activity_errors: list[float] = []
    vle_errors: list[float] = []
    for sample_index in range(batch.x.shape[0]):
        count = int(batch.mask[sample_index].sum().item())
        compositions = []
        target_indices = []
        for epsilon in (0.01, 0.005, 0.001):
            for component in range(count):
                composition = torch.zeros(batch.x.shape[1], dtype=batch.x.dtype, device=batch.x.device)
                composition[:count] = epsilon / (count - 1)
                composition[component] = 1.0 - epsilon
                compositions.append(composition)
                target_indices.append(component)
        x = torch.stack(compositions)
        repeats = x.shape[0]
        molecules = batch.molecules[sample_index : sample_index + 1].expand(repeats, -1, -1)
        temperature = batch.temperature_k[sample_index : sample_index + 1].expand(repeats, -1)
        pressure = batch.pressure_kpa[sample_index : sample_index + 1].expand(repeats, -1)
        mask = batch.mask[sample_index : sample_index + 1].expand(repeats, -1)
        targets = torch.tensor(target_indices, device=x.device)
        if direct:
            for direction in ("isothermal", "isobaric"):
                predicted = model.predict_direct(
                    molecules, temperature, pressure, x, mask, direction=direction
                )
                target_y = predicted.y.gather(1, targets[:, None]).squeeze(1)
                vle_errors.extend((1.0 - target_y).abs().tolist())
        else:
            output = model(molecules, temperature, pressure, x, mask)
            target_log_gamma = output.log_gamma.gather(1, targets[:, None]).squeeze(1)
            activity_errors.extend(target_log_gamma.abs().tolist())
            state = equilibrium_at_tp(model, molecules, temperature, pressure, x, mask)
            target_y = state.y.gather(1, targets[:, None]).squeeze(1)
            vle_errors.extend((1.0 - target_y).abs().tolist())
    return activity_errors, vle_errors


def _phase_paths(count: int, grid_points: int, device: torch.device) -> list[tuple[Tensor, Tensor]]:
    coordinate = torch.linspace(0.01, 0.99, grid_points, device=device)
    if count == 2:
        return [(coordinate, torch.stack([coordinate, 1.0 - coordinate], dim=-1))]
    paths = []
    for component in range(count):
        x = torch.full((grid_points, count), 0.0, device=device)
        x[:] = ((1.0 - coordinate) / (count - 1)).unsqueeze(-1)
        x[:, component] = coordinate
        paths.append((coordinate, x))
    return paths


def _phase_metrics(
    model: nn.Module,
    samples: Sequence[VLESample],
    feature_map: dict[str, np.ndarray],
    device: torch.device,
    direct: bool,
    grid_points: int,
    solver_iterations: int,
) -> list[dict[str, float]]:
    metrics: list[dict[str, float]] = []
    for sample in samples:
        count = sample.component_count
        molecule_features = torch.zeros(1, 3, len(next(iter(feature_map.values()))), device=device)
        for index, smiles in enumerate(sample.smiles):
            molecule_features[0, index] = torch.as_tensor(feature_map[smiles], device=device)
        mask = torch.zeros(1, 3, device=device)
        mask[:, :count] = 1.0
        for coordinate, path in _phase_paths(count, grid_points, device):
            padded_x = torch.zeros(grid_points, 3, device=device)
            padded_x[:, :count] = path
            molecules = molecule_features.expand(grid_points, -1, -1)
            masks = mask.expand(grid_points, -1)
            temperature = torch.full((grid_points, 1), sample.temperature_k, device=device)
            pressure = torch.full((grid_points, 1), sample.pressure_kpa, device=device)
            if direct:
                predictions = (
                    model.predict_direct(
                        molecules, temperature, pressure, padded_x, masks, direction="isothermal"
                    ),
                    model.predict_direct(
                        molecules, temperature, pressure, padded_x, masks, direction="isobaric"
                    ),
                )
                curves = (
                    torch.cat([torch.log(predictions[0].pressure_kpa), predictions[0].y[:, :count]], dim=-1),
                    torch.cat([predictions[1].temperature_k / 100.0, predictions[1].y[:, :count]], dim=-1),
                )
            else:
                isothermal = solve_isothermal(
                    model,
                    molecules,
                    temperature,
                    padded_x,
                    masks,
                    iterations=solver_iterations,
                    strict=False,
                )
                isobaric = solve_isobaric(
                    model,
                    molecules,
                    pressure,
                    padded_x,
                    masks,
                    iterations=solver_iterations,
                    strict=False,
                )
                curves = (
                    torch.cat([torch.log(isothermal.pressure_kpa), isothermal.y[:, :count]], dim=-1),
                    torch.cat([isobaric.temperature_k / 100.0, isobaric.y[:, :count]], dim=-1),
                )
            for curve in curves:
                metrics.append(
                    phase_curve_smoothness(
                        coordinate.detach().cpu().numpy(),
                        curve.detach().cpu().numpy(),
                    )
                )
    return metrics


def evaluate_thermodynamic_consistency(
    model: nn.Module,
    samples: Sequence[VLESample],
    feature_map: dict[str, np.ndarray],
    device: torch.device,
    *,
    prediction_records: Sequence[dict[str, Any]] | None = None,
    solver_iterations: int = 24,
    grid_points: int = 21,
    max_systems: int = 32,
) -> dict[str, Any]:
    """Evaluate physical validity independently of target prediction errors."""
    if not samples:
        raise ValueError("Thermodynamic consistency evaluation needs test samples")
    if grid_points < 5 or max_systems < 1:
        raise ValueError("grid_points must be at least five and max_systems positive")
    from . import predict_vle

    model.to(device).eval()
    direct = getattr(getattr(model, "config", None), "decoder_mode", None) == "direct_vle"
    representatives = _representative_samples(samples, max_systems)
    batch = _batch(representatives, feature_map, device)
    interior_x = batch.x.clamp_min(1e-3) * batch.mask
    interior_x = interior_x / interior_x.sum(-1, keepdim=True)
    if direct:
        gd = torch.empty(0)
        gd_fd = torch.empty(0)
    else:
        gd = gibbs_duhem_residuals(
            model,
            batch.molecules,
            batch.temperature_k,
            batch.pressure_kpa,
            interior_x,
            batch.mask,
        )
        gd_fd = gibbs_duhem_residuals_finite_difference(
            model,
            batch.molecules[: min(8, len(representatives))],
            batch.temperature_k[: min(8, len(representatives))],
            batch.pressure_kpa[: min(8, len(representatives))],
            interior_x[: min(8, len(representatives))],
            batch.mask[: min(8, len(representatives))],
        )
    with torch.no_grad():
        permutation = _permutation_errors(model, batch, direct)
        pure_activity, pure_vle = _pure_limit_errors(model, batch, direct)
        phase = _phase_metrics(
            model,
            representatives,
            feature_map,
            device,
            direct,
            grid_points,
            solver_iterations,
        )
    records = list(prediction_records) if prediction_records is not None else predict_vle(
        model,
        samples,
        feature_map,
        batch_size=128,
        device=device,
        solver_iterations=solver_iterations,
    )
    x_rows = []
    y_rows = []
    masks = []
    residuals = []
    nonphysical = 0
    pure_failure_threshold = 0.05
    for record in records:
        count = int(record["component_count"])
        x_rows.append([record.get(f"x_{index + 1}") or 0.0 for index in range(3)])
        y_rows.append([record.get(f"y_pred_{index + 1}") or 0.0 for index in range(3)])
        masks.append([1.0 if index < count else 0.0 for index in range(3)])
        residual = record.get("pressure_residual_kpa")
        if residual is not None and np.isfinite(float(residual)):
            residuals.append(float(residual))
        gross_residual = residual is not None and abs(float(residual)) > 0.1
        if bool(record.get("nonphysical")) or not bool(record.get("converged")) or gross_residual:
            nonphysical += 1
    closure = composition_closure_metrics(
        torch.tensor(x_rows), torch.tensor(y_rows), torch.tensor(masks)
    )
    equilibrium = summarize_absolute(residuals, "equilibrium_residual")
    result: dict[str, Any] = {
        "evaluated_systems": len(representatives),
        "evaluated_predictions": len(records),
        **summarize_absolute(gd, "gibbs_duhem"),
        **summarize_absolute(gd_fd, "gibbs_duhem_finite_difference"),
        **closure,
        **summarize_absolute(permutation, "permutation"),
        **summarize_absolute(pure_activity, "pure_limit_log_gamma"),
        **summarize_absolute(pure_vle, "pure_limit_vle"),
        "equilibrium_residual_mean_abs_kpa": equilibrium["equilibrium_residual_mean_abs"],
        "equilibrium_residual_p95_abs_kpa": equilibrium["equilibrium_residual_p95_abs"],
        "equilibrium_residual_max_abs_kpa": equilibrium["equilibrium_residual_max_abs"],
        "solver_convergence_failure_rate": float(
            np.mean([not bool(record.get("converged")) for record in records])
        ),
        "pure_limit_failure_rate": float(
            np.mean(np.asarray(pure_vle) > pure_failure_threshold)
        ) if pure_vle else None,
        "ordinary_nonphysical_prediction_rate": (
            nonphysical / len(records) if records else None
        ),
        "nonphysical_prediction_rate": combined_nonphysical_rate(
            nonphysical,
            len(records),
            pure_vle,
            pure_failure_threshold,
        ),
        "physical_criteria": {
            "gross_equilibrium_residual_kpa": 0.1,
            "pure_limit_vle_error": pure_failure_threshold,
        },
    }
    for name in (
        "total_variation",
        "first_derivative_jump_p95",
        "second_derivative_magnitude_mean",
    ):
        values = [row[name] for row in phase]
        result[f"phase_{name}_mean"] = float(np.mean(values)) if values else None
        result[f"phase_{name}_p95"] = float(np.percentile(values, 95.0)) if values else None
    return result
