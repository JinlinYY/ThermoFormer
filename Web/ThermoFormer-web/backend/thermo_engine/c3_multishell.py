"""Height screening and section balances for archived C3 column profiles.

This is an ideal zero-pressure-drop packaging calculation, not a hydraulic or
full-energy multicolumn simulation. No trained model or old result is changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from thermo_engine.paper_validation import validate_equilibrium_result


class HeightBasis(BaseModel):
    """Explicit layout assumptions, not measured efficiency or vendor sizing."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    maximum_height_m: float = Field(default=40, gt=0, allow_inf_nan=False)
    overall_tray_efficiency: float = Field(default=0.70, gt=0, le=1, allow_inf_nan=False)
    tray_spacing_m: float = Field(default=0.50, gt=0, allow_inf_nan=False)
    non_contact_height_m: float = Field(default=8, ge=0, allow_inf_nan=False)


def partition_candidate(record: dict[str, Any], shells: int, basis: HeightBasis) -> dict[str, Any]:
    """Map a reviewed equilibrium profile to serial, bidirectionally coupled shells."""
    candidate = record["candidate"]
    direct = candidate.get("verification", {}).get("direct_column_validation", {})
    if not candidate["numerical_checks"]["passed"] or not candidate.get("verified") or not direct.get("passed"):
        raise ValueError("A numerically and directly reviewed source candidate is required")
    metrics, profile, spec = candidate["metrics"], candidate["profiles"], record["specification"]
    n = int(metrics["stages_including_reboiler"])
    if not 1 <= shells <= n - 1:
        raise ValueError("Shell count must be between one and the number of contact stages")
    x = np.asarray(profile["x_propene"], dtype=float)
    y = np.asarray(profile["y_propene"], dtype=float)
    temperature = np.asarray(profile["temperature_k"], dtype=float)
    if any(v.shape != (n,) for v in (x, y, temperature)):
        raise ValueError("Archived profile lengths do not match stage count")
    f, z = float(spec["feed_flow_mol_s"]), float(spec["feed_propene"])
    feed = int(metrics["feed_stage_from_top"])
    d, b = float(metrics["distillate_flow_mol_s"]), float(metrics["bottoms_flow_mol_s"])
    liquid, vapor = float(metrics["reflux_ratio"]) * d, (float(metrics["reflux_ratio"]) + 1) * d
    q, remainder = divmod(n - 1, shells)  # External reboiler is not a tray.
    sizes = [q + int(i < remainder) for i in range(shells)]
    sections: list[dict[str, Any]] = []
    interfaces: list[dict[str, Any]] = []
    start = 1
    for i, size in enumerate(sizes):
        end = start + size - 1
        last = i == shells - 1
        lin = liquid + (f if start > feed else 0)
        lout = liquid + (f if end >= feed else 0)
        local_feed = start <= feed <= end
        liquid_in_x = float(y[0] if start == 1 else x[start - 2])
        vapor_in = 0.0 if last else vapor
        vapor_in_y = 0.0 if last else float(y[end])
        liquid_out = b if last else lout
        liquid_out_x = float(x[-1] if last else x[end - 1])
        total_error = abs(lin + vapor_in + (f if local_feed else 0) - liquid_out - vapor) / f
        component_error = (
            abs(
                lin * liquid_in_x
                + vapor_in * vapor_in_y
                + (f * z if local_feed else 0)
                - liquid_out * liquid_out_x
                - vapor * float(y[start - 1])
            )
            / f
        )
        trays = math.ceil(size / basis.overall_tray_efficiency)
        # N*s is a conservative layout allowance, rather than the N-1 gaps alone.
        height = trays * basis.tray_spacing_m + basis.non_contact_height_m
        sections.append(
            {
                "shell": f"T-{101 + i}",
                "global_start": start,
                "global_end": end,
                "contact_equilibrium_stages": size,
                "external_reboiler_attached": last,
                "feed_local_equilibrium_stage": feed - start + 1 if local_feed else None,
                "estimated_actual_trays": trays,
                "estimated_height_m": height,
                "within_declared_height_screen": height <= basis.maximum_height_m,
                "total_molar_balance_residual": total_error,
                "propene_balance_residual": component_error,
                "last_shell_balance_includes_external_reboiler": last,
            }
        )
        if not last:
            interfaces.append(
                {
                    "upper_shell": f"T-{101 + i}",
                    "lower_shell": f"T-{102 + i}",
                    "cut_after_global_stage": end,
                    "liquid_upper_to_lower_mol_s": lout,
                    "liquid_propene_fraction": float(x[end - 1]),
                    "vapor_lower_to_upper_mol_s": vapor,
                    "vapor_propene_fraction": float(y[end]),
                    "liquid_transfer_pump_required_for_same_grade_layout": True,
                }
            )
        start = end + 1
    worst_balance = max(max(s["total_molar_balance_residual"], s["propene_balance_residual"]) for s in sections)
    validation = validate_equilibrium_result(
        np.r_[np.c_[x, 1 - x], np.c_[y, 1 - y]],
        float(direct["numerical_residual"]),
        material_residual=max(worst_balance, float(direct["material_residual"])),
        temperatures=temperature,
    )
    if not validation["passed"]:
        raise ValueError("Mapped sections fail inherited equilibrium or new section-balance checks")
    return {
        "candidate_id": record["candidate_id"],
        "shell_count": shells,
        "height_basis": basis.model_dump(),
        "sections": sections,
        "interfaces": interfaces,
        "maximum_estimated_height_m": max(s["estimated_height_m"] for s in sections),
        "height_screen_passed": all(s["within_declared_height_screen"] for s in sections),
        "numerical_validation": validation,
        "maximum_section_balance_residual": worst_balance,
        "metrics_reused_from_archive": metrics,
        "equilibrium_calculation_reused": True,
        "new_equilibrium_solve": False,
        "scope": "zero-pressure-drop CMO section mapping; not a pressure-coupled MESH solution",
        "hydraulic_height_verified": False,
        "industrial_performance_guaranteed": False,
    }


def build_study(source: Path, output: Path) -> dict[str, Any]:
    """Screen three reviewed designs under two declared height assumptions."""
    archive = json.loads(source.read_text(encoding="utf-8-sig"))
    bases = {
        "screening_70pct_500mm": HeightBasis(),
        "conditional_80pct_450mm": HeightBasis(overall_tray_efficiency=0.8, tray_spacing_m=0.45),
    }
    comparisons: list[dict[str, Any]] = []
    layouts: dict[str, Any] = {}
    for identity in archive["frontier_candidate_ids"]:
        record = next(r for r in archive["records"] if r["candidate_id"] == identity)
        if not record["robustness"]["passed"] or not record["utilities"]["validation"]["passed"]:
            raise ValueError("Required archived robustness/utility review missing")
        for basis_name, basis in bases.items():
            for count in range(1, 21):
                mapped = partition_candidate(record, count, basis)
                if mapped["height_screen_passed"]:
                    layouts[f"{identity}_{basis_name}"] = mapped
                    comparisons.append(
                        {
                            "candidate_id": identity,
                            "basis": basis_name,
                            "equilibrium_stages_including_reboiler": record["candidate"]["metrics"][
                                "stages_including_reboiler"
                            ],
                            "reflux_ratio": record["candidate"]["metrics"]["reflux_ratio"],
                            "shell_count": count,
                            "maximum_estimated_height_m": mapped["maximum_estimated_height_m"],
                            "reboiler_duty_kw_reused": record["utilities"]["reboiler"]["duty_w"] / 1000,
                        }
                    )
                    break
            else:
                raise ValueError("No height-screened arrangement in the declared search")
    chosen = "p1200_scenario_r2p0"
    record = next(r for r in archive["records"] if r["candidate_id"] == chosen)
    base_record = next(r for r in archive["records"] if r["candidate_id"] == archive["selected_candidate_id"])
    result = {
        "user_height_limit_m": 40,
        "basis_status": "declared_unverified_layout_assumptions",
        "source_path": str(source.resolve()),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "numerical_module_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "comparisons": comparisons,
        "layouts": layouts,
        "proposed_layout": f"{chosen}_screening_70pct_500mm",
        "selection": "deterministic fewer-shell preference at 40 m; not a new LLM run or economic optimum",
        "proposed_record": record,
        "reboiler_duty_increase_percent": 100
        * (record["utilities"]["reboiler"]["duty_w"] / base_record["utilities"]["reboiler"]["duty_w"] - 1),
        "limitations": [
            "All shells share ideal 1.2 MPa; physical pressure gradients and pump heat not solved.",
            "Original model/stress product results are reused, not industrial multicolumn predictions.",
            "Efficiency, spacing and non-contact height need vendor and mechanical verification.",
            "Pressure drop, heat loss, tower diameter, flooding, controls and pump duty remain uncalculated.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_study(args.source, args.output)
    print(json.dumps({"comparisons": result["comparisons"], "proposed_layout": result["proposed_layout"]}))


if __name__ == "__main__":
    main()
