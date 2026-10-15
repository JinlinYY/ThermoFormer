"""Independent closure bounds and temperature/initialization audits for the C3 study."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from thermo_engine.c3_engineering_study import write_json
from thermo_engine.c3_thermoformer import file_sha256
from thermo_engine.paper_validation import validate_equilibrium_result
from thermo_engine.t80305_experiment import DEFAULT_OUTPUT, ColumnInput, Surface, Thermodynamics, rate_reduced_column


def mass_balance_bound(z: float, d: float) -> dict[str, Any]:
    """Necessary binary material-balance bound, independent of VLE or stage count."""
    if not 0 < z < 1 or not 0 < d < 1:
        raise ValueError("Normalized feed and distillate fraction required")
    raw = (z - d) / (1 - d)
    lower = max(0.0, raw)
    top = (z - (1 - d) * lower) / d
    check = validate_equilibrium_result(
        [[top, 1 - top], [lower, 1 - lower]], 0, material_residual=abs(d * top + (1 - d) * lower - z)
    )
    if not check["passed"]:
        raise ValueError("Mass bound failed arithmetic validation")
    return {
        "minimum_possible_bottom_propene": lower,
        "at_top_propene": top,
        "bottom_less_than_one_percent_possible_at_fixed_split": lower < 0.01,
        "necessary_D_over_F_for_bottom_below_one_percent": (z - 0.01) / (1 - 0.01),
        "condition": "Necessary only: xD <= 1; bottom < 0.01 requires D/F strictly above threshold",
        "validation": check,
    }


def run_diagnostics(output: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    audit = json.loads((output / "source_audit.json").read_text(encoding="utf-8"))
    grid = json.loads((output / "equilibrium_grid.json").read_text(encoding="utf-8"))
    thermo = Thermodynamics()
    bounds = [{"basis": b["basis"], **mass_balance_bound(b["z"], b["d_fraction"])} for b in audit["binary_cases"]]
    temperature = []
    # Condenser/reflux stream327 is subcooled and is intentionally not used as a bubble-point reference.
    for stream_id in ("328", "329"):
        stream = audit["streams"][stream_id]
        for name in ("TF", "PR"):
            state = thermo.bubble(name, stream["pressure_kpa_abs"], stream["C3_propene_fraction"])
            temperature.append(
                {
                    "stream": stream_id,
                    "model": name,
                    "state": state,
                    "document_temperature_c": stream["temperature_c"],
                    "predicted_bubble_temperature_c": state["T_K"] - 273.15,
                    "difference_K": state["T_K"] - 273.15 - stream["temperature_c"],
                    "interpretation": (
                        "C3-projected bubble temperature vs multicomponent design temperature; "
                        "not an experimental error"
                    ),
                }
            )
    initialization = []
    columns = json.loads((output / "columns.json").read_text(encoding="utf-8"))
    for name in ("TF", "PR"):
        base = next(
            r
            for r in columns
            if r["model"] == name and r["basis"] == "feed_anchored" and r["efficiency_scenario"] == 0.65
        )
        spec = ColumnInput.model_validate(base["input"])
        surface = Surface(grid, name, np.linspace(1890, 2010, spec.stages))
        replay = rate_reduced_column(
            spec, surface, initial=np.linspace(0.9, 0.1, spec.stages), thermo=thermo, name=name, direct=True
        )
        initialization.append(
            {
                "model": name,
                "reference_candidate": base["candidate_id"],
                "alternative_initialization": "linear 0.9 to 0.1, versus uniform feed composition",
                "absolute_top_difference": abs(
                    replay["metrics"]["aggregate_top_propene"] - base["metrics"]["aggregate_top_propene"]
                ),
                "absolute_bottom_difference": abs(
                    replay["metrics"]["bottom_propene"] - base["metrics"]["bottom_propene"]
                ),
                "replay": replay,
            }
        )
    result = {
        "material_balance_bounds": bounds,
        "temperature_comparison": temperature,
        "initialization_audit": initialization,
        "grid_sha256": file_sha256(output / "equilibrium_grid.json"),
        "model_signature": thermo.signature,
    }
    write_json(output / "additional_diagnostics.json", result)
    return result


if __name__ == "__main__":
    result = run_diagnostics()
    print(
        json.dumps(
            {
                "bounds": result["material_balance_bounds"],
                "temperature": [
                    {k: r[k] for k in ("stream", "model", "difference_K")} for r in result["temperature_comparison"]
                ],
            }
        )
    )
