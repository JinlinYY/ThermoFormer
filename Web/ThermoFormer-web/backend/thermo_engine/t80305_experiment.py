"""Auditable industrial-C3 comparison, isolated from the three original paper cases.

The full multicomponent plant is deliberately not replaced by a fitted binary column.
This experiment rates explicitly reduced, constant-molar-overflow (CMO) columns.
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import time
from pathlib import Path
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
from scipy.interpolate import PchipInterpolator
from scipy.linalg import solve_banded

from thermo_engine.c3_engineering_study import load_model, write_json
from thermo_engine.c3_pressure_check import PRPressureReference
from thermo_engine.c3_tf_extrapolation import TFExtrapolation
from thermo_engine.c3_thermodynamics import _properties, _vapor_phi, property_provenance
from thermo_engine.c3_thermoformer import BASE_CHECKPOINT, file_sha256
from thermo_engine.paper_validation import validate_equilibrium_result

ROOT = Path(__file__).resolve().parents[1]
AUDIT_ROOT = ROOT / "outputs/paper_agent/t80305ab-20261011"
DEFAULT_OUTPUT = ROOT / "outputs/paper_agent/t80305ab-validation-20261014"
PRESSURES = (1890.0, 1920.0, 1950.0, 1980.0, 2010.0)
LIMITS = [
    "Design-document comparison, not measured plant validation.",
    "C3-only projection excludes hydrogen, other light gases and heavy lumps.",
    "Vent and side product are aggregated; product is not the actual side-draw purity.",
    "CMO with prescribed feed quality: no stage energy balance, heat-duty or hydraulic prediction.",
    "Multiple reboilers and separate shells are not resolved; an imposed pressure profile is retained.",
    "Overall tray efficiencies are declared scenarios, not measured or fitted values.",
    "TF means the frozen C3-adapted head, not the unadapted manuscript model.",
    "Industrial temperatures and pressures exceed the registered C3 experimental coverage.",
    "PR is a model comparator, not experimental truth; model differences are not accuracy errors.",
]


class ColumnInput(BaseModel):
    """Separate operating inputs from forward-predicted outlet compositions."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    stages: int = Field(ge=3, le=500)
    feed_stage: int = Field(ge=2)
    feed_propene: float = Field(gt=0, lt=1)
    distillate_fraction: float = Field(gt=0, lt=1)
    reflux_ratio: float = Field(gt=0)
    q: float = Field(default=1.0, ge=0.8, le=1.2)
    top_pressure_kpa: float = Field(default=1890, ge=1890, le=2010)
    bottom_pressure_kpa: float = Field(default=2010, ge=1890, le=2010)

    @model_validator(mode="after")
    def check_column(self) -> ColumnInput:
        if self.feed_stage >= self.stages:
            raise ValueError("The feed must be interior")
        if self.bottom_pressure_kpa < self.top_pressure_kpa:
            raise ValueError("Pressure must not decrease toward the bottom")
        if (self.reflux_ratio + 1) * self.distillate_fraction - (1 - self.q) <= 0:
            raise ValueError("Nonpositive stripping vapor flow")
        return self


class IndustrialTF(TFExtrapolation):
    """Explicit new study window; original production/research gates stay unchanged."""

    def __init__(self, model: Any, pressure_kpa: float, *, opt_in: bool) -> None:
        if not opt_in or not 1890 <= pressure_kpa <= 2010:
            raise ValueError("Industrial extrapolation needs opt-in and 1890–2010 kPaA")
        super().__init__(model, allow_extrapolation=True, pressure_kpa=2000)
        self.pressure_kpa = pressure_kpa
        self.reference = PRPressureReference(pressure_kpa)


class Thermodynamics:
    """Cached real model instances; PR only initializes TF, never replaces its answer."""

    def __init__(self) -> None:
        self.tf, self.signature = load_model()
        self.instances: dict[tuple[str, float], Any] = {}

    def model(self, name: str, pressure: float) -> Any:
        key = (name, pressure)
        if key in self.instances:
            return self.instances[key]
        if name == "TF":
            instance: Any = IndustrialTF(self.tf, pressure, opt_in=True)
        elif name == "PR":
            instance = PRPressureReference(pressure)
        else:
            raise ValueError("Unknown thermodynamic backend")
        self.instances[key] = instance
        return instance

    def bubble(self, name: str, pressure: float, x: float) -> dict[str, Any]:
        return dict(self.model(name, float(pressure)).bubble(float(x)))


def audit_sources() -> dict[str, Any]:
    """Read original workbook, record exact cells, and expose rather than fix nonclosure."""
    from openpyxl import load_workbook  # type: ignore[import-untyped]

    contract = json.loads((AUDIT_ROOT / "case_contract.json").read_text(encoding="utf-8"))
    source = Path(contract["source_root"])
    path = source / "附件5-物流数据表-190426.xlsx"
    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet = workbook["300#(3)"]
    constants, _, _ = _properties()
    mw = np.asarray(constants.MWs)
    streams: dict[str, Any] = {}
    for col in "FGHIJ":
        component_mass = np.array([sheet[f"{col}21"].value, sheet[f"{col}22"].value], dtype=float)
        molar = component_mass / mw * 1000 / 3600
        fraction = molar / molar.sum()
        validation = validate_equilibrium_result([fraction], 0)
        if not validation["passed"]:
            raise ValueError("Source composition normalization failed")
        identity = str(sheet[f"{col}3"].value)
        streams[identity] = {
            "total_mass_kg_h": float(sheet[f"{col}9"].value),
            "temperature_c": float(sheet[f"{col}6"].value),
            "pressure_kpa_abs": float(sheet[f"{col}7"].value),
            "component_mass_kg_h": component_mass.tolist(),
            "C3_flow_mol_s": float(molar.sum()),
            "C3_propene_fraction": float(fraction[0]),
            "C3_molar_components": molar.tolist(),
            "source": {"path": str(path), "sheet": sheet.title, "range": f"{col}3:{col}36"},
            "arithmetic_validation": validation,
        }
    workbook.close()
    feed = streams["325"]
    outs = [streams[i] for i in ("326", "328", "329")]
    mass_gap = feed["total_mass_kg_h"] - sum(s["total_mass_kg_h"] for s in outs)
    top = np.sum([streams[i]["C3_molar_components"] for i in ("326", "328")], axis=0)
    bottom = np.asarray(streams["329"]["C3_molar_components"])
    d, b = float(top.sum()), float(bottom.sum())
    reflux = streams["327"]["C3_flow_mol_s"]
    cases = []
    for basis in ("feed_anchored", "products_anchored"):
        f = feed["C3_flow_mol_s"] if basis == "feed_anchored" else d + b
        z = feed["C3_propene_fraction"] if basis == "feed_anchored" else float((top[0] + bottom[0]) / f)
        cases.append(
            {
                "basis": basis,
                "feed_mol_s": f,
                "z": z,
                "d_fraction": d / f,
                "reflux_ratio": reflux / d,
                "implied_bottom_mol_s": f - d,
                "reference_aggregate_top_x": float(top[0] / d),
                "reference_bottom_x": float(bottom[0] / b),
                "closure_assumption": (
                    "Keep source feed and aggregate top flow; bottom total flow is balance-derived."
                    if basis == "feed_anchored"
                    else "Keep source outlet C3 flows/compositions; feed flow and composition are balance-derived."
                ),
            }
        )
    return {
        "streams": streams,
        "binary_cases": cases,
        "contract": contract,
        "total_mass_gap_kg_h": mass_gap,
        "total_mass_gap_fraction": mass_gap / feed["total_mass_kg_h"],
        "source_hashes": {p.name: file_sha256(p) for p in source.iterdir() if p.suffix in (".pdf", ".xlsx", ".dwg")},
        "full_plant_status": "missing_parameters",
        "missing_parameters": [
            "tray_efficiency",
            "individual_reboiler_duties",
            "resolved_stream_balance",
            "molecular_definition_of_heavy_lumps",
            "inlet_valve_enthalpy_specification",
        ],
        "observed_data_are_plant_measurements": False,
        "source_pressure_conflict": "A-top: equipment header 1900, PFD and stream354 1950 kPaA",
    }


def build_grid(thermo: Thermodynamics, output: Path) -> dict[str, Any]:
    """Prespecified dense grids include product tails; every knot is fugacity-checked."""
    tail = np.geomspace(1e-6, 0.05, 51)
    xs = np.unique(np.r_[0, tail, np.linspace(0.05, 0.95, 301), 1 - tail, 1, 0.996, 0.01])
    grid: dict[str, Any] = {"pressures_kpa": PRESSURES, "x": xs.tolist(), "models": {}}
    for name in ("TF", "PR"):
        rows = []
        for pressure in PRESSURES:
            started = time.perf_counter()
            states = [thermo.bubble(name, pressure, float(x)) for x in xs]
            if not all(s["validation"]["passed"] for s in states):
                raise ValueError("A grid state failed validation")
            rows.append(states)
            print(
                json.dumps(
                    {
                        "grid_model": name,
                        "pressure": pressure,
                        "states": len(xs),
                        "seconds": time.perf_counter() - started,
                    }
                ),
                flush=True,
            )
        grid["models"][name] = rows
    write_json(output / "equilibrium_grid.json", grid)
    return grid


class Surface:
    """PCHIP in composition and linear pressure interpolation, bounded to the grid."""

    def __init__(self, grid: dict[str, Any], name: str, pressures: Any) -> None:
        self.pressures = np.asarray(pressures)
        ps = np.asarray(grid["pressures_kpa"])
        if self.pressures.min() < ps[0] or self.pressures.max() > ps[-1]:
            raise ValueError("Pressure surface extrapolation forbidden")
        self.lower = np.clip(np.searchsorted(ps, self.pressures) - 1, 0, len(ps) - 2)
        self.weights = (self.pressures - ps[self.lower]) / (ps[self.lower + 1] - ps[self.lower])
        self.ys = [
            PchipInterpolator(grid["x"], [s["y"][0] for s in row], extrapolate=False) for row in grid["models"][name]
        ]
        self.ts = [
            PchipInterpolator(grid["x"], [s["T_K"] for s in row], extrapolate=False) for row in grid["models"][name]
        ]

    def evaluate(self, x: Any, kind: Literal["y", "t", "dy"] = "y") -> Any:
        interpolators = self.ts if kind == "t" else self.ys
        values = np.array([(f.derivative() if kind == "dy" else f)(x) for f in interpolators])
        indices = np.arange(len(self.pressures))
        return values[self.lower, indices] * (1 - self.weights) + values[self.lower + 1, indices] * self.weights


def _flows(spec: ColumnInput) -> tuple[Any, Any, Any, Any]:
    n, k = spec.stages, spec.feed_stage - 1
    lr = spec.reflux_ratio * spec.distillate_fraction
    vr = lr + spec.distillate_fraction
    idx = np.arange(n)
    lin = lr + spec.q * (idx > k)
    lout = lr + spec.q * (idx >= k)
    vin = vr - (1 - spec.q) * (idx >= k)
    vout = vr - (1 - spec.q) * (idx > k)
    return lin, lout, vin, vout


def _balances(spec: ColumnInput, x: Any, y: Any) -> Any:
    lin, lout, vin, vout = _flows(spec)
    d, b = spec.distillate_fraction, 1 - spec.distillate_fraction
    values = np.zeros(spec.stages)
    values[0] = vin[0] * y[1] - lout[0] * x[0] - d * y[0]
    values[1:-1] = lin[1:-1] * x[:-2] + vin[1:-1] * y[2:] - lout[1:-1] * x[1:-1] - vout[1:-1] * y[1:-1]
    values[spec.feed_stage - 1] += spec.feed_propene
    values[-1] = lin[-1] * x[-2] - b * x[-1] - vout[-1] * y[-1]
    return values


def _jacobian(spec: ColumnInput, dy: Any) -> Any:
    lin, lout, vin, vout = _flows(spec)
    diagonal = -lout - vout * dy
    diagonal[0] = -lout[0] - spec.distillate_fraction * dy[0]
    diagonal[-1] = -(1 - spec.distillate_fraction) - vout[-1] * dy[-1]
    bands = np.zeros((3, spec.stages))
    bands[0, 1:] = vin[:-1] * dy[1:]
    bands[1] = diagonal
    bands[2, :-1] = lin[1:]
    return bands


def rate_reduced_column(
    spec: ColumnInput,
    surface: Surface,
    *,
    initial: Any = None,
    thermo: Thermodynamics | None = None,
    name: str = "TF",
    direct: bool = False,
) -> dict[str, Any]:
    """Forward rating at fixed flows and N; direct closure corrects interpolation defects."""
    x = np.asarray(initial if initial is not None else np.full(spec.stages, spec.feed_propene), dtype=float)
    history = []
    states: list[dict[str, Any]] = []
    converged = False

    for mode in [False, True] if direct else [False]:
        for iteration in range(60 if not mode else 8):
            if mode:
                if thermo is None:
                    raise ValueError("Direct review requires actual backend")
                states = [thermo.bubble(name, float(p), float(v)) for p, v in zip(surface.pressures, x)]  # noqa: B905
                y = np.array([s["y"][0] for s in states])
            else:
                y = surface.evaluate(x)
            values = _balances(spec, x, y)
            error = float(np.max(abs(values)))
            history.append({"direct": mode, "iteration": iteration, "stage_balance_per_feed": error})
            if error < 5e-9:
                converged = True
                break
            converged = False
            dx = solve_banded((1, 1), _jacobian(spec, surface.evaluate(x, "dy")), -values)
            step = 1.0
            while np.any(x + step * dx <= 0) or np.any(x + step * dx >= 1):
                step *= 0.5
                if step < 1e-10:
                    break
            if step < 1e-10:
                break
            if not mode:
                while (
                    step > 1e-8 and np.max(abs(_balances(spec, x + step * dx, surface.evaluate(x + step * dx)))) > error
                ):
                    step *= 0.5
            x = x + step * dx
        if not converged:
            break
    # Evaluate at the final iterate, including nonconverged runs; never retain stale residuals.
    if direct and converged:
        assert thermo is not None
        states = [thermo.bubble(name, float(p), float(v)) for p, v in zip(surface.pressures, x)]  # noqa: B905
        y = np.array([s["y"][0] for s in states])
        t = np.array([s["T_K"] for s in states])
        residual = max(s["equilibrium_residual"] for s in states)
    else:
        y, t = surface.evaluate(x), surface.evaluate(x, "t")
        residual = 0.0  # interpolation relation only; explicitly not direct thermodynamic closure
    balances = _balances(spec, x, y)
    material = abs(spec.distillate_fraction * y[0] + (1 - spec.distillate_fraction) * x[-1] - spec.feed_propene)
    check = validate_equilibrium_result(
        np.r_[np.c_[x, 1 - x], np.c_[y, 1 - y]],
        residual,
        material_residual=max(float(material), float(np.max(abs(balances)))),
        temperatures=t,
    )
    check["passed"] = bool(check["passed"] and converged)
    check["direct_fugacity_checked"] = bool(direct and converged)
    check["relation"] = "direct_gamma_phi_or_phi_phi" if direct and converged else "interpolated_VLE_only"
    return {
        "input": spec.model_dump(),
        "validation": check,
        "converged": converged,
        "metrics": {
            "aggregate_top_propene": float(y[0]),
            "bottom_propene": float(x[-1]),
            "aggregate_propene_recovery": float(spec.distillate_fraction * y[0] / spec.feed_propene),
            "top_tray_temperature_c": float(t[0] - 273.15),
            "bottom_temperature_c": float(t[-1] - 273.15),
            "vapor_mol_per_mol_feed": (spec.reflux_ratio + 1) * spec.distillate_fraction,
            "reduced_targets_met": bool(y[0] >= 0.996 and x[-1] < 0.01),
        },
        "profile": {
            "x_propene": x.tolist(),
            "y_propene": y.tolist(),
            "temperature_k": t.tolist(),
            "pressure_kpa": surface.pressures.tolist(),
        },
        "iterations": history,
        "plant_validated": False,
        "full_MESH": False,
    }


def sampled_stability(thermo: Thermodynamics, name: str, state: dict[str, Any]) -> dict[str, Any]:
    """Sample both phase tangent planes; a pass is not global stability certification."""
    t, p, x = state["T_K"], state["P_kPa"], np.asarray(state["x"])
    model = thermo.model(name, p)
    if name == "TF":

        def liquid_logf(z: Any) -> Any:
            return np.log(z) + thermo.tf.log_gamma(t, p, float(z[0])) + np.log(model.pure_reference(t))
    else:

        def liquid_logf(z: Any) -> Any:
            phase = model.eos(**model.kwargs, T=t, P=p * 1000, zs=list(z))
            return np.log(z) + np.log(phase.phis_l) + np.log(p * 1000)

    mu = liquid_logf(x)
    scan = np.unique(np.r_[np.linspace(1e-6, 1 - 1e-6, 151), x[0], state["y"][0]])
    liquid, vapor = [], []
    for w in scan:
        z = np.array([w, 1 - w])
        liquid.append(float(z @ (liquid_logf(z) - mu)))
        vapor.append(float(z @ (np.log(z) + np.log(_vapor_phi(t, p, z)) + np.log(p * 1000) - mu)))
    return {
        "minimum_liquid_TPD_RT": min(liquid),
        "minimum_vapor_TPD_RT": min(vapor),
        "negative_sample_found": min(liquid + vapor) < -1e-7,
        "trial_compositions": len(scan),
        "global_stability_certified": False,
    }


def run_thermo(output: Path, thermo: Thermodynamics) -> dict[str, Any]:
    grid = build_grid(thermo, output)
    comparisons, stability = [], []
    for pressure in (1890.0, 1950.0, 2010.0):
        for x in (0.01, 0.0211, 0.35, 0.69337, 0.95, 0.996):
            pair = {name: thermo.bubble(name, pressure, x) for name in ("TF", "PR")}
            alphas = {n: s["y"][0] / (1 - s["y"][0]) * (1 - x) / x for n, s in pair.items()}
            comparisons.append(
                {
                    "pressure_kpa": pressure,
                    "x_propene": x,
                    "states": pair,
                    "alpha": alphas,
                    "delta_y_TF_minus_PR": pair["TF"]["y"][0] - pair["PR"]["y"][0],
                    "delta_T_K_TF_minus_PR": pair["TF"]["T_K"] - pair["PR"]["T_K"],
                }
            )
            for name, state in pair.items():
                stability.append(
                    {"model": name, "pressure_kpa": pressure, "x": x, **sampled_stability(thermo, name, state)}
                )
    write_json(output / "thermodynamic_comparison.json", comparisons)
    write_json(output / "sampled_phase_stability.json", stability)
    return grid


def run_columns(
    output: Path, thermo: Thermodynamics, grid: dict[str, Any], audit: dict[str, Any]
) -> list[dict[str, Any]]:
    records = []
    for basis in audit["binary_cases"]:
        for name in ("TF", "PR"):
            for efficiency in (0.5, 0.65, 0.8, 1.0):
                n = round(240 * efficiency) + 1
                spec = ColumnInput(
                    stages=n,
                    feed_stage=round(185 * efficiency),
                    feed_propene=basis["z"],
                    distillate_fraction=basis["d_fraction"],
                    reflux_ratio=basis["reflux_ratio"],
                )
                surface = Surface(grid, name, np.linspace(1890, 2010, n))
                result = rate_reduced_column(spec, surface, thermo=thermo, name=name, direct=True)
                record = {
                    "candidate_id": f"{basis['basis']}_{name}_eta{efficiency}",
                    "basis": basis["basis"],
                    "model": name,
                    "efficiency_scenario": efficiency,
                    "kind": "baseline",
                    **result,
                }
                records.append(record)
                write_json(output / "columns.json", records)
                print(
                    json.dumps(
                        {
                            "candidate": record["candidate_id"],
                            "validation": result["validation"],
                            "metrics": result["metrics"],
                        }
                    ),
                    flush=True,
                )
    return records


def run_improvements(
    output: Path, thermo: Thermodynamics, grid: dict[str, Any], audit: dict[str, Any]
) -> list[dict[str, Any]]:
    """Finite design screen at assumed eta=0.65, independently forward rated.

    D/F is defined by nominal target mass balance, not by prescribing rated products.
    """
    records = []
    basis = audit["binary_cases"][0]
    d = (basis["z"] - 0.009) / (0.997 - 0.009)
    for name in ("TF", "PR"):
        for reflux in (25.0, 35.0, 50.0, 70.0, 100.0):
            for feed_stage in (95, 110, 120, 130, 140):
                spec = ColumnInput(
                    stages=157,
                    feed_stage=feed_stage,
                    feed_propene=basis["z"],
                    distillate_fraction=d,
                    reflux_ratio=reflux,
                )
                surface = Surface(grid, name, np.linspace(1890, 2010, spec.stages))
                result = rate_reduced_column(spec, surface)
                records.append(
                    {
                        "candidate_id": f"improve_{name}_R{reflux}_F{feed_stage}",
                        "model": name,
                        "kind": "improvement",
                        "efficiency_scenario": 0.65,
                        **result,
                    }
                )
    # Directly audit every apparent passing candidate, so selection never rests on interpolation alone.
    for row in records:
        if row["validation"]["passed"] and row["metrics"]["reduced_targets_met"]:
            spec = ColumnInput.model_validate(row["input"])
            surface = Surface(grid, row["model"], np.linspace(1890, 2010, spec.stages))
            verified = rate_reduced_column(
                spec, surface, initial=row["profile"]["x_propene"], thermo=thermo, name=row["model"], direct=True
            )
            row.update(verified)
    write_json(output / "improvement_screen.json", records)
    print(
        json.dumps(
            {
                "improvement_candidates": len(records),
                "verified_passing": sum(
                    r["validation"]["passed"]
                    and r["validation"]["direct_fugacity_checked"]
                    and r["metrics"]["reduced_targets_met"]
                    for r in records
                ),
            }
        ),
        flush=True,
    )
    return records


def run_sensitivities(
    output: Path, thermo: Thermodynamics, grid: dict[str, Any], audit: dict[str, Any]
) -> list[dict[str, Any]]:
    records = []
    basis = audit["binary_cases"][0]
    for name in ("TF", "PR"):
        for q, top, bottom, label in (
            (0.9, 1890, 2010, "q0.9"),
            (1.1, 1890, 2010, "q1.1"),
            (1.0, 1950, 1950, "uniform_pressure"),
        ):
            spec = ColumnInput(
                stages=157,
                feed_stage=120,
                feed_propene=basis["z"],
                distillate_fraction=basis["d_fraction"],
                reflux_ratio=basis["reflux_ratio"],
                q=q,
                top_pressure_kpa=top,
                bottom_pressure_kpa=bottom,
            )
            surface = Surface(grid, name, np.linspace(top, bottom, spec.stages))
            result = rate_reduced_column(spec, surface, thermo=thermo, name=name, direct=True)
            records.append({"candidate_id": f"sensitivity_{name}_{label}", "model": name, "kind": label, **result})
    write_json(output / "sensitivity.json", records)
    return records


def write_tables(output: Path, records: list[dict[str, Any]]) -> None:
    rows = []
    for r in records:
        rows.append(
            {
                "candidate_id": r["candidate_id"],
                "model": r["model"],
                "kind": r["kind"],
                "basis": r.get("basis", "feed_anchored"),
                "efficiency_scenario": r.get("efficiency_scenario", 0.65),
                **r["input"],
                **r["metrics"],
                "numerical_pass": r["validation"]["passed"],
                "direct_fugacity_checked": r["validation"]["direct_fugacity_checked"],
                "plant_validated": False,
            }
        )
    with (output / "candidate_table.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--stage", choices=["audit", "thermo", "columns", "all"], default="all")
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    audit = audit_sources()
    write_json(output / "source_audit.json", audit)
    if args.stage == "audit":
        print(json.dumps({"status": audit["full_plant_status"], "mass_gap_kg_h": audit["total_mass_gap_kg_h"]}))
        return
    thermo = Thermodynamics()
    signature = {**thermo.signature, "actual_base_sha256": file_sha256(BASE_CHECKPOINT)}
    protocol = {
        "signature": signature,
        "limits": LIMITS,
        "python": platform.python_version(),
        "study_type": "exploratory_engineering_document_comparison",
        "weights_updated": False,
        "pressures_kpa": PRESSURES,
        "efficiency_scenarios": [0.5, 0.65, 0.8, 1],
        "feed_qualities": [0.9, 1.0, 1.1],
        "full_plant_status": "missing_parameters",
        "source_audit_sha256": file_sha256(output / "source_audit.json"),
        "code_sha256": file_sha256(Path(__file__)),
        "comparison_models": ["frozen_C3_adapted_ThermoFormer_gamma_phi", "ChemSep_PR_phi_phi"],
        "property_provenance": property_provenance(),
        "TF_volume_override": "DIPPR_PERRY_8E; checked at every direct state; original globals unchanged",
    }
    write_json(output / "protocol.json", protocol)
    if args.stage in ("all", "thermo"):
        grid = run_thermo(output, thermo)
    else:
        grid = json.loads((output / "equilibrium_grid.json").read_text(encoding="utf-8"))
    if args.stage in ("all", "columns"):
        records = run_columns(output, thermo, grid, audit)
        records += run_improvements(output, thermo, grid, audit)
        records += run_sensitivities(output, thermo, grid, audit)
        write_tables(output, records)
    if file_sha256(BASE_CHECKPOINT) != signature["actual_base_sha256"] or load_model()[1] != thermo.signature:
        raise ValueError("Checkpoint/provenance changed during experiment")
    write_json(
        output / "run_complete.json",
        {"stage": args.stage, "weights_unchanged": True, "full_plant_reproduction": "missing_parameters"},
    )


if __name__ == "__main__":
    main()
