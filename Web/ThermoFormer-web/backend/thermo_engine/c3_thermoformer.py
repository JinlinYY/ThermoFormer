"""Isolated C3 adaptation of the registered ThermoFormer excess-Gibbs branch.

Molecular encoding and all original paper weights remain unchanged. This module
exposes activity coefficients; phase-equilibrium closure belongs to c3 physics.
"""

from __future__ import annotations

import csv
import hashlib
import importlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = PROJECT_ROOT / "lab_models" / "ThermoFormer"
BASE_CHECKPOINT = MODEL_ROOT / "models/vle/prediction/vle_overall_binary/seed_2/best_model.pt"
BASE_SHA256 = "1531e258a1895308bba4640c633f8b2fc0732dfa353d2cd9341f36c8af38fd91"
CASE_ROOT = PROJECT_ROOT / "outputs/paper_agent/c3-propane-propylene-20260928"
COMPONENT_SMILES = ("CC=C", "CCC")
TRAIN_TEMPERATURES = (273.15, 283.15, 303.15, 313.15)
VALIDATION_TEMPERATURES = (278.15,)
TEST_TEMPERATURES = (293.15,)


def _external_module(name: str) -> Any:
    # Adding MODEL_ROOT/src would shadow the installed thermo package with the
    # legacy src/thermo.py adapter. Import through the source package instead.
    source_root = str(MODEL_ROOT)
    if source_root not in sys.path:
        sys.path.insert(0, source_root)
    return importlib.import_module(f"src.thermoformer.{name}")


def file_sha256(path: Path) -> str:
    """Return a byte-for-byte digest without altering the source artifact."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class C3Observation:
    """A traceable original C3 observation in propene/propane order."""

    temperature_k: float
    pressure_kpa: float
    x_propene: float
    y_propene: float
    source_csv_line: int
    doi: str
    partition: str

    @property
    def interior(self) -> bool:
        return 0.0 < self.x_propene < 1.0 and 0.0 < self.y_propene < 1.0


def load_c3_observations(path: Path = CASE_ROOT / "c3_vle_source_records.csv") -> list[C3Observation]:
    """Load registered source observations and keep complete isotherms together."""
    observations: list[C3Observation] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if (row["smiles1"], row["smiles2"]) != COMPONENT_SMILES:
                raise ValueError("C3 source order must be propene then propane")
            temperature = float(row["source_temperature_k"])
            if any(abs(temperature - value) < 1e-7 for value in TRAIN_TEMPERATURES):
                partition = "train"
            elif any(abs(temperature - value) < 1e-7 for value in VALIDATION_TEMPERATURES):
                partition = "validation"
            elif any(abs(temperature - value) < 1e-7 for value in TEST_TEMPERATURES):
                partition = "test"
            else:
                raise ValueError(f"Unregistered C3 temperature: {temperature}")
            observations.append(
                C3Observation(
                    temperature,
                    float(row["source_pressure_kpa"]),
                    float(row["x1"]),
                    float(row["y1"]),
                    int(row["source_csv_line"]),
                    row["doi"],
                    partition,
                )
            )
    if len(observations) != 90:
        raise ValueError("The registered C3 case requires exactly 90 source observations")
    return observations


def prepare_c3_features(output_dir: Path) -> dict[str, Any]:
    """Encode two C3 molecules with the original frozen molecular representation."""
    torch = importlib.import_module("torch")

    output_dir.mkdir(parents=True, exist_ok=True)
    if file_sha256(BASE_CHECKPOINT) != BASE_SHA256:
        raise ValueError("Original binary seed-2 checkpoint digest mismatch")
    payload = torch.load(BASE_CHECKPOINT, map_location="cpu", weights_only=True)
    cache = output_dir / "features" / "c3_hybrid_raw.npz"
    encoder = _external_module("features").HybridMolecularEncoder(
        cache, batch_size=2, model_size="84m", use_cuda=torch.cuda.is_available()
    )
    features = encoder.encode(COMPONENT_SMILES)
    raw = np.stack([features[value] for value in COMPONENT_SMILES]).astype(np.float32)
    if raw.shape != (2, 820) or not np.isfinite(raw).all():
        raise ValueError("C3 frozen molecular encoding must be finite and have shape (2, 820)")
    scaler = payload["molecular_feature_preprocessing"]["rdkit_scaler"]
    transformed = raw.copy()
    transformed[:, :24] = (transformed[:, :24] - np.asarray(scaler["mean"], dtype=np.float32)) / np.asarray(
        scaler["std"], dtype=np.float32
    )
    feature_path = output_dir / "features" / "c3_model_features.npz"
    if feature_path.exists():
        with np.load(feature_path, allow_pickle=False) as existing:
            if not np.array_equal(existing["raw"], raw) or not np.array_equal(existing["transformed"], transformed):
                raise ValueError("Existing C3 feature artifact differs; use a separate output directory")
    else:
        np.savez_compressed(feature_path, smiles=np.asarray(COMPONENT_SMILES), raw=raw, transformed=transformed)
    metadata: dict[str, Any] = {
        "component_order": ["propene", "propane"],
        "smiles": list(COMPONENT_SMILES),
        "base_checkpoint": str(BASE_CHECKPOINT),
        "base_checkpoint_sha256": BASE_SHA256,
        "raw_cache_sha256": file_sha256(cache),
        "feature_sha256": file_sha256(feature_path),
        "feature_shape": [2, 820],
        "branch_dimensions": {"rdkit": 24, "unimol": 768, "functional_groups": 28},
        "scaler_source": "Original binary seed-2 checkpoint; no C3 refitting",
        "encoder_trainable": False,
        "source_vle_used_for_molecular_features": False,
    }
    (output_dir / "features" / "manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


class C3ThermoFormer:
    """Registered real ThermoFormer with a separately saved C3 interaction head."""

    def __init__(self, feature_path: Path, adapted_checkpoint: Path | None = None, device: str = "cpu") -> None:
        torch = importlib.import_module("torch")

        if file_sha256(BASE_CHECKPOINT) != BASE_SHA256:
            raise ValueError("Original ThermoFormer checkpoint digest mismatch")
        payload = torch.load(BASE_CHECKPOINT, map_location="cpu", weights_only=True)
        models = _external_module("models")
        self.model = models.ThermoFormer(models.ThermoFormerConfig(**payload["model_config"]))
        self.model.load_state_dict(payload["model"], strict=True)
        self.model = self.model.double().to(device).eval()
        with np.load(feature_path, allow_pickle=False) as data:
            if tuple(data["smiles"].astype(str)) != COMPONENT_SMILES:
                raise ValueError("C3 feature order mismatch")
            values = np.asarray(data["transformed"], dtype=np.float64)
        self.features = torch.as_tensor(values, dtype=torch.float64, device=device).unsqueeze(0)
        self.feature_path = feature_path
        self.device = device
        self.torch = torch
        self.adaptation: dict[str, Any] | None = None
        if adapted_checkpoint is not None:
            self.adaptation = torch.load(adapted_checkpoint, map_location="cpu", weights_only=True)
            if self.adaptation["base_checkpoint_sha256"] != BASE_SHA256:
                raise ValueError("C3 adaptation belongs to a different base checkpoint")
            if self.adaptation["feature_sha256"] != file_sha256(feature_path):
                raise ValueError("C3 adapted feature digest mismatch")
            self.model.pair_potential[2].load_state_dict(self.adaptation["interaction_last_layer"], strict=True)
        self.model.requires_grad_(False)

    def enable_small_head_training(self) -> int:
        """Unfreeze only the 193-parameter final excess-Gibbs pair projection."""
        self.model.requires_grad_(False)
        self.model.pair_potential[2].requires_grad_(True)
        return int(sum(p.numel() for p in self.model.parameters() if p.requires_grad))

    def log_gamma_tensor(self, temperature: Any, pressure: Any, x_propene: Any) -> Any:
        """Return differentiable log-gamma values; all numerical work stays in tools."""
        torch = self.torch
        t = torch.as_tensor(temperature, dtype=torch.float64, device=self.device).reshape(-1, 1)
        p = torch.as_tensor(pressure, dtype=torch.float64, device=self.device).reshape(-1, 1)
        first = torch.as_tensor(x_propene, dtype=torch.float64, device=self.device).reshape(-1)
        x = torch.stack((first, 1.0 - first), dim=1)
        output = self.model(self.features.expand(len(first), -1, -1), t, p, x, torch.ones_like(x, dtype=torch.bool))
        return output.log_gamma

    def log_gamma(self, temperature_k: float, pressure_kpa: float, x_propene: Any) -> NDArray[np.float64]:
        """Scalar-state callback in propene/propane order for the gamma-phi solver."""
        values = np.asarray(x_propene, dtype=float).reshape(-1)
        if len(values) not in (1, 2):
            raise ValueError("Expected one propene fraction or a binary composition")
        x = float(values[0])
        if not (np.isfinite(temperature_k) and np.isfinite(pressure_kpa) and 0.0 <= x <= 1.0):
            raise ValueError("Invalid C3 thermodynamic state")
        with self.torch.no_grad():
            result = self.log_gamma_tensor([temperature_k], [pressure_kpa], [x]).detach().cpu().numpy()[0]
        if not np.isfinite(result).all():
            raise ValueError("Nonfinite ThermoFormer activity coefficients")
        return np.asarray(result, dtype=np.float64)


def summarize_c3_predictions(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize all attempts, with endpoint and mixture errors kept separate."""
    metrics: list[dict[str, Any]] = []
    for model_name in sorted({str(row["model"]) for row in predictions}):
        for partition in ("train", "validation", "test"):
            for scope in ("mixture_interior", "pure_endpoint", "all"):
                selected = [
                    row
                    for row in predictions
                    if row["model"] == model_name
                    and row["partition"] == partition
                    and (scope == "all" or bool(row["interior"]) == (scope == "mixture_interior"))
                ]
                successful = [row for row in selected if row["solver_returned"] and row["validation"]["passed"]]
                entry: dict[str, Any] = {
                    "model": model_name,
                    "partition": partition,
                    "scope": scope,
                    "attempted": len(selected),
                    "validated": len(successful),
                    "failed": len(selected) - len(successful),
                    "error_statistic_denominator": "validated states only; failures reported separately",
                }
                if successful:
                    pressure_error = np.asarray(
                        [row["predicted_pressure_kpa"] - row["pressure_kpa"] for row in successful]
                    )
                    vapor_error = np.asarray([row["predicted_y_propene"] - row["y_propene"] for row in successful])
                    entry.update(
                        pressure_mae_kpa=float(np.abs(pressure_error).mean()),
                        pressure_rmse_kpa=float(np.sqrt(np.square(pressure_error).mean())),
                        y_propene_mae=float(np.abs(vapor_error).mean()),
                        y_propene_rmse=float(np.sqrt(np.square(vapor_error).mean())),
                        maximum_equilibrium_residual=float(
                            max(row["validation"]["numerical_residual"] for row in successful)
                        ),
                    )
                metrics.append(entry)
    return {
        "metrics": metrics,
        "model_comparison": "Both models use the same sourced gamma-phi backend; only the TF interaction head differs",
        "test_used_for_selection": False,
        "test_scope": "293.15 K isotherm in the same chemical pair and source DOI",
        "independent_source_validation": False,
        "high_purity_interior_experimental_validation": False,
        "global_phase_stability_certified": False,
        "pure_endpoints_are_not_high_purity_mixture_evidence": True,
    }


def train_c3_thermoformer(
    output_dir: Path,
    *,
    epochs: int = 600,
    learning_rate: float = 0.002,
    patience: int = 80,
    seed: int = 0,
) -> dict[str, Any]:
    """Fit only a small G^E head, select on validation, then evaluate locked test.

    Targets are inferred from original observed VLE using the fixed, explicitly
    sourced gamma-phi reference. They are not direct measurements of gamma.
    """
    torch = importlib.import_module("torch")

    from thermo_engine.c3_thermodynamics import bubble_pressure, c3_reference_terms, property_provenance

    if epochs <= 0 or patience <= 0 or learning_rate <= 0:
        raise ValueError("Positive epochs, patience, and learning rate are required")
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "c3_adapted_head.pt"
    if checkpoint_path.exists():
        raise FileExistsError("An adapted head already exists; use a separate output directory")
    torch.set_num_threads(1)
    torch.manual_seed(seed)
    np.random.seed(seed)
    feature_metadata = prepare_c3_features(output_dir)
    observations = load_c3_observations()
    feature_path = output_dir / "features" / "c3_model_features.npz"
    model = C3ThermoFormer(feature_path)
    trainable = model.enable_small_head_training()
    if trainable != 193:
        raise ValueError("Unexpected size of the registered C3 adaptation head")
    parameter_origin = {
        name: value.detach().clone() for name, value in model.model.named_parameters() if value.requires_grad
    }
    physics_source = sys.modules[c3_reference_terms.__module__].__file__
    if physics_source is None:
        raise RuntimeError("Missing source path for the C3 physics module")
    recipe: dict[str, Any] = {
        "status": "fixed_before_optimization",
        "base_checkpoint_sha256": BASE_SHA256,
        "source_csv_sha256": file_sha256(CASE_ROOT / "c3_vle_source_records.csv"),
        "physics_module_sha256": file_sha256(Path(physics_source)),
        "feature_manifest": feature_metadata,
        "temperature_groups_k": {
            "train": list(TRAIN_TEMPERATURES),
            "validation": list(VALIDATION_TEMPERATURES),
            "test": list(TEST_TEMPERATURES),
        },
        "partitions": {
            name: [asdict(row) for row in observations if row.partition == name]
            for name in ("train", "validation", "test")
        },
        "seed": seed,
        "epochs_maximum": epochs,
        "learning_rate": learning_rate,
        "patience": patience,
        "early_stopping_minimum_improvement": 1e-10,
        "optimizer": "Adam, full batch, CPU float64",
        "selection": "minimum validation mean squared log-fugacity residual at observed states",
        "trainable_parameters": trainable,
        "trainable_names": list(parameter_origin),
        "parameter_anchor_weight": 1e-6,
        "test_used_for_selection": False,
        "pure_endpoints": "held with their temperature group; excluded from activity-target loss",
        "liquid_reference": "Fixed external pure properties plus saturation fugacity and Poynting correction",
        "evaluation_scope": "Within one chemical pair and one DOI; complete-isotherm holdout",
    }
    (output_dir / "training_recipe.json").write_text(json.dumps(recipe, indent=2), encoding="utf-8")
    (output_dir / "thermodynamic_reference_provenance.json").write_text(
        json.dumps(property_provenance(), indent=2), encoding="utf-8"
    )
    batches: dict[str, dict[str, Any]] = {}
    target_rows: list[dict[str, Any]] = []
    for partition in ("train", "validation"):
        selected = [row for row in observations if row.partition == partition and row.interior]
        targets: list[Any] = []
        for row in selected:
            reference = c3_reference_terms(
                row.temperature_k,
                row.pressure_kpa,
                [row.x_propene, 1.0 - row.x_propene],
                [row.y_propene, 1.0 - row.y_propene],
            )
            values = np.asarray(reference["log_gamma_target"], dtype=float)
            if values.shape != (2,) or not np.isfinite(values).all():
                raise ValueError("Unavailable finite gamma-phi target for an interior C3 state")
            targets.append(values)
            target_rows.append({**asdict(row), "derived_log_gamma": values.tolist()})
        batches[partition] = {
            "temperature": [row.temperature_k for row in selected],
            "pressure": [row.pressure_kpa for row in selected],
            "x": [row.x_propene for row in selected],
            "target": torch.as_tensor(np.stack(targets), dtype=torch.float64),
        }
    (output_dir / "development_activity_targets.json").write_text(json.dumps(target_rows, indent=2), encoding="utf-8")

    def loss_for(partition: str) -> Any:
        batch = batches[partition]
        prediction = model.log_gamma_tensor(batch["temperature"], batch["pressure"], batch["x"])
        return (prediction - batch["target"]).square().mean()

    optimizer = torch.optim.Adam((p for p in model.model.parameters() if p.requires_grad), lr=learning_rate)
    with torch.no_grad():
        base_validation = float(loss_for("validation"))
        base_training = float(loss_for("train"))
    best_value = base_validation
    best_epoch = 0
    best_state = {
        key: value.detach().cpu().clone() for key, value in model.model.pair_potential[2].state_dict().items()
    }
    history: list[dict[str, Any]] = [{"epoch": 0, "training_loss": base_training, "validation_loss": base_validation}]
    stale_epochs = 0
    for epoch in range(1, epochs + 1):
        optimizer.zero_grad(set_to_none=True)
        fit_loss = loss_for("train")
        anchor = sum(
            (value - parameter_origin[name]).square().mean()
            for name, value in model.model.named_parameters()
            if value.requires_grad
        )
        total_loss = fit_loss + 1e-6 * anchor
        if not torch.isfinite(total_loss):
            raise RuntimeError("Nonfinite C3 development loss")
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_([p for p in model.model.parameters() if p.requires_grad], 1.0)
        optimizer.step()
        with torch.no_grad():
            training_value = float(loss_for("train"))
            validation_value = float(loss_for("validation"))
        history.append({"epoch": epoch, "training_loss": training_value, "validation_loss": validation_value})
        if validation_value < best_value - 1e-10:
            best_value, best_epoch, stale_epochs = validation_value, epoch, 0
            best_state = {
                key: value.detach().cpu().clone() for key, value in model.model.pair_potential[2].state_dict().items()
            }
        else:
            stale_epochs += 1
        if epoch % 50 == 0:
            print(f"epoch={epoch} training={training_value:.8g} validation={validation_value:.8g}", flush=True)
        if stale_epochs >= patience:
            break
    payload = {
        "base_checkpoint_sha256": BASE_SHA256,
        "feature_sha256": file_sha256(feature_path),
        "interaction_last_layer": best_state,
        "selected_epoch": best_epoch,
        "validation_loss": best_value,
        "seed": seed,
        "trainable_parameters": trainable,
        "model_role": "Real ThermoFormer G^E branch, frozen molecular encoding and 193-parameter adapted head",
    }
    torch.save(payload, checkpoint_path)
    with (output_dir / "training_history.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(history[0]))
        writer.writeheader()
        writer.writerows(history)

    # Test performance is first scored after model selection ends.
    prediction_rows: list[dict[str, Any]] = []
    model_versions = {
        "frozen_thermoformer": C3ThermoFormer(feature_path),
        "adapted_thermoformer": C3ThermoFormer(feature_path, checkpoint_path),
    }
    for name, predictor in model_versions.items():
        for index, row in enumerate(observations):
            prediction: dict[str, Any] = {"model": name, **asdict(row), "interior": row.interior}
            try:
                result = bubble_pressure(row.temperature_k, row.x_propene, predictor.log_gamma)
                prediction.update(
                    predicted_pressure_kpa=float(result["P_kPa"]),
                    predicted_y_propene=float(np.asarray(result["y"])[0]),
                    validation=result["validation"],
                    solver_returned=True,
                )
            except (ValueError, RuntimeError, FloatingPointError) as error:
                prediction.update(solver_returned=False, error=f"{type(error).__name__}: {error}")
            prediction_rows.append(prediction)
            if (index + 1) % 30 == 0:
                print(f"evaluation {name}: {index + 1}/{len(observations)}", flush=True)
        (output_dir / "closed_equilibrium_predictions.json").write_text(
            json.dumps(prediction_rows, indent=2), encoding="utf-8"
        )
    summary = {
        "status": "completed",
        "selected_epoch": best_epoch,
        "epochs_executed": len(history) - 1,
        "base_validation_log_fugacity_mse": base_validation,
        "adapted_validation_log_fugacity_mse": best_value,
        "checkpoint": str(checkpoint_path),
        "checkpoint_sha256": file_sha256(checkpoint_path),
        "original_checkpoint_unchanged": file_sha256(BASE_CHECKPOINT) == BASE_SHA256,
        "trained_parameters": trainable,
        "test_used_for_selection": False,
        "closed_equilibrium_predictions": len(prediction_rows),
    }
    (output_dir / "equilibrium_metrics.json").write_text(
        json.dumps(summarize_c3_predictions(prediction_rows), indent=2), encoding="utf-8"
    )
    (output_dir / "training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
