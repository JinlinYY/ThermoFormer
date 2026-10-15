"""Read-only audit of the paper's sec-butanol/acetate/DMF UNIFAC baseline.

This research CLI preserves the paper data and solver modules. It can load an
isolated pure-Python dependency copy without changing the ggnn39 environment.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import sys
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import brentq

from thermo_engine.paper_validation import validate_equilibrium_result

ROOT = Path(__file__).resolve().parents[4]
LEGACY = ROOT / "ThermoAgent"
CASE = LEGACY / "cases/extractive_distillation"
CAS = ["78-92-2", "105-46-4", "68-12-2"]
PRESSURE_PA = 101300.0


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


class UNIFACAuditBackend:
    """Fresh original-UNIFAC states with explicit parameter and residual checks."""

    def __init__(self) -> None:
        from thermo import Chemical
        from thermo.unifac import UFIP, UFSG, UNIFAC, UNIFAC_gammas, UNIFAC_group_assignment_DDBST

        self.chemicals = [Chemical(c) for c in CAS]
        self.groups = [UNIFAC_group_assignment_DDBST(c, "UNIFAC") for c in CAS]
        self.functional = UNIFAC_gammas
        self.object_model = UNIFAC
        self.ufsg, self.ufip = UFSG, UFIP
        mains = sorted({UFSG[k].main_group_id for g in self.groups for k in g})
        self.interactions = [
            dict(main_i=i, main_j=j, a_K=UFIP.get(i, {}).get(j)) for i in mains for j in mains if i != j
        ]
        if not all(self.groups) or any(r["a_K"] is None for r in self.interactions):
            raise ValueError("missing_parameters: original UNIFAC groups/interactions")

    def psat(self, temperatures: Any) -> Any:
        return np.array([[c.VaporPressure(float(t)) for c in self.chemicals] for t in temperatures])

    def gammas(self, x: Any, temperatures: Any) -> Any:
        if len(x) != len(temperatures):
            raise ValueError("Composition and temperature batch sizes differ")
        return np.array(
            [
                self.functional(T=float(temperatures[i]), xs=xi.tolist(), chemgroups=self.groups)
                for i, xi in enumerate(x)
            ]
        )

    def bubble(self, x: Any) -> tuple[Any, Any]:
        temperatures, vapors = [], []
        for xi in np.asarray(x):

            def raw(t: float, composition: Any = xi) -> Any:
                return composition * self.gammas(np.asarray([composition]), [t])[0] * self.psat([t])[0] / PRESSURE_PA

            t = brentq(lambda value: float(raw(value).sum() - 1), 340, 460, xtol=1e-10)
            temperatures.append(t)
            vapors.append(raw(t))
        ts, ys = np.array(temperatures), np.array(vapors)
        gate = validate_equilibrium_result(np.r_[x, ys], float(abs(ys.sum(axis=1) - 1).max()), temperatures=ts)
        if not gate["passed"]:
            raise ValueError(gate)
        return ts, ys

    def state(self, rs: Any) -> tuple[Any, Any, Any]:
        r, s = np.asarray(rs).T
        x = np.c_[(1 - r) * (1 - s), r * (1 - s), s]
        t, y = self.bubble(x)
        return x, y, t

    def provenance(self) -> dict[str, Any]:
        components = []
        for index, c in enumerate(self.chemicals):
            groups = self.groups[index]
            components.append(
                dict(
                    CAS=c.CAS,
                    name=c.name,
                    smiles=c.smiles,
                    formula=c.formula,
                    molecular_weight=c.MW,
                    groups={
                        str(k): dict(name=self.ufsg[k].group, count=n, main=self.ufsg[k].main_group_id)
                        for k, n in groups.items()
                    },
                    vapor_pressure_method=c.VaporPressure.method,
                    vapor_pressure_methods=sorted(c.VaporPressure.all_methods),
                    temperature_limits_K=[c.VaporPressure.Tmin, c.VaporPressure.Tmax],
                )
            )
        return dict(
            python=sys.executable,
            versions={k: version(k) for k in ["thermo", "chemicals", "fluids", "numpy", "scipy"]},
            components=components,
            interactions=self.interactions,
        )


def stage_checks(
    record: dict[str, Any], x: Any, y: Any, temperatures: Any, equilibrium_residual: float
) -> dict[str, Any]:
    """Independently assemble every component balance from stream definitions."""
    n, d, solvent, reflux = record["N"], record["D"], record["S"], record["R"]
    feeds = np.zeros((n, 3))
    feeds[record["nf"] - 1] = [0.5, 0.5, 0]
    feeds[record["ns"] - 1] += [0, 0, solvent]
    liquids = reflux * d + np.cumsum(feeds.sum(axis=1))
    vapor = (reflux + 1) * d
    bottoms = 1 + solvent - d
    balance = feeds - liquids[:, None] * x - vapor * y
    balance[1:] += liquids[:-1, None] * x[:-1]
    balance[:-1] += vapor * y[1:]
    balance[0] += reflux * d * y[0]
    balance[-1] += (liquids[-1] - bottoms) * x[-1]
    global_balance = np.array([0.5, 0.5, solvent]) - d * y[0] - bottoms * x[-1]
    residual = float(abs(balance).max())
    gate = validate_equilibrium_result(
        np.r_[x, y],
        equilibrium_residual,
        material_residual=max(residual, float(abs(global_balance).max())),
        temperatures=temperatures,
    )
    return dict(
        validation=gate,
        maximum_stage_balance_mol_s=residual,
        global_balance_mol_s=global_balance.tolist(),
        xD=y[0].tolist(),
        xB=x[-1].tolist(),
        ester_purity=float(y[0, 1]),
        ester_recovery=float(d * y[0, 1] / 0.5),
        temperature_range_K=[float(min(temperatures)), float(max(temperatures))],
    )


def audit_base(backend: UNIFACAuditBackend, output: Path) -> dict[str, Any]:
    with (CASE / "data/equilibrium.csv").open(encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    components = ["alcohol", "ester", "DMF"]
    x = np.array([[float(r["x_" + c]) for c in components] for r in rows])
    experimental_y = np.array([[float(r["y_exp_" + c]) for c in components] for r in rows])
    experimental_t = np.array([float(r["T_exp_K"]) for r in rows])
    old_y = np.array([[float(r["y_unifac_" + c]) for c in components] for r in rows])
    old_t = np.array([float(r["T_unifac_K"]) for r in rows])
    t, y = backend.bubble(x)
    gamma = backend.gammas(x, t)
    object_gamma = np.array(
        [
            backend.object_model.from_subgroups(
                T=float(t[index]),
                xs=xi.tolist(),
                chemgroups=backend.groups,
                subgroups=backend.ufsg,
                interaction_data=backend.ufip,
                version=0,
            ).gammas()
            for index, xi in enumerate(x)
        ]
    )
    alpha = (y[:, 1] / x[:, 1]) / (y[:, 0] / x[:, 0])
    alpha_exp = (experimental_y[:, 1] / x[:, 1]) / (experimental_y[:, 0] / x[:, 0])
    reference = dict(
        n=len(x),
        gamma_implementations_max_abs_difference=float(abs(gamma - object_gamma).max()),
        published_y_max_difference=float(abs(y - old_y).max()),
        published_T_max_difference_K=float(abs(t - old_t).max()),
        y_MAE=float(abs(y - experimental_y).mean()),
        T_MAE_K=float(abs(t - experimental_t).mean()),
        volatility_direction_agreement=int(np.sum((alpha > 1) == (alpha_exp > 1))),
        alpha_UNIFAC_range=[float(min(alpha)), float(max(alpha))],
        alpha_experiment_range=[float(min(alpha_exp)), float(max(alpha_exp))],
    )
    columns = {}
    for key in ["unifac_183", "thermoformer_183"]:
        r = read(CASE / "data" / (key + ".json"))
        xx, yy, tt = [np.asarray(r[k]) for k in ["x", "y", "T"]]
        if key.startswith("unifac"):
            new_t, new_y = backend.bubble(xx)
            raw = xx * backend.gammas(xx, tt) * backend.psat(tt) / PRESSURE_PA
            eq_res = float(abs(raw - yy).max())
            result = stage_checks(r, xx, new_y, new_t, eq_res)
            result.update(
                published_y_max_difference=float(abs(new_y - yy).max()),
                published_T_max_difference_K=float(abs(new_t - tt).max()),
            )
        else:
            raw = xx * np.array(r["gamma"]) * np.array(r["psat_kPa"]) / 101.3
            eq_res = float(abs(raw - yy).max())
            result = stage_checks(r, xx, yy, tt, eq_res)
        result["configuration"] = {k: r[k] for k in ["N", "nf", "ns", "R", "S", "D", "B"]}
        if not result["validation"]["passed"]:
            raise ValueError(result)
        columns[key] = result
    # Same-x/T decomposition on selected TF stage states. Diagnostic K ratios
    # are not presented as a new equilibrium state or an experimental result.
    r = read(CASE / "data/thermoformer_183.json")
    decomposition = []
    for j in [0, 15, 89, 158, 182]:
        xx, tt = np.array([r["x"][j]]), np.array([r["T"][j]])
        gu = backend.gammas(xx, tt)[0]
        pu = backend.psat(tt)[0] / 1000
        gt, pt = np.asarray(r["gamma"][j]), np.asarray(r["psat_kPa"][j])
        decomposition.append(
            dict(
                stage=j + 1,
                x=xx[0].tolist(),
                temperature_K=float(tt[0]),
                gamma_UNIFAC=gu.tolist(),
                gamma_ThermoFormer=gt.tolist(),
                psat_UNIFAC_kPa=pu.tolist(),
                psat_ThermoFormer_kPa=pt.tolist(),
                alpha_UNIFAC=float(gu[1] * pu[1] / gu[0] / pu[0]),
                alpha_ThermoFormer=float(gt[1] * pt[1] / gt[0] / pt[0]),
                alpha_UNIFAC_common_TF_psat=float(gu[1] * pt[1] / gu[0] / pt[0]),
                alpha_TF_common_UNIFAC_psat=float(gt[1] * pu[1] / gt[0] / pu[0]),
            )
        )
    pure = []
    for c in backend.chemicals:
        tb = brentq(lambda tt, chemical=c: chemical.VaporPressure(tt) - PRESSURE_PA, 340, 460)
        pure.append(
            dict(
                CAS=c.CAS,
                method=c.VaporPressure.method,
                predicted_boil_K=tb,
                vapor_pressure_kPa={str(tt): c.VaporPressure(tt) / 1000 for tt in [375, 385, 400, 415, 425]},
            )
        )
    result = dict(
        provenance=backend.provenance(),
        experimental_point_reproduction=reference,
        column_checks=columns,
        fixed_state_decomposition=decomposition,
        pure_vapor_pressures=pure,
    )
    write(output / ("audit_thermo_" + version("thermo") + ".json"), result)
    return result


def audit_columns(backend: UNIFACAuditBackend, output: Path) -> dict[str, Any]:
    sys.path.insert(0, str(LEGACY))
    column = importlib.import_module("column")
    surface_type = importlib.import_module("solve_column").Surface
    archived = read(CASE / "data/unifac_183.json")
    tf_record = read(CASE / "data/thermoformer_183.json")
    histories = []
    for label, initial in [
        ("generic_initial_profile", None),
        ("thermoformer_profile", column.rs_from_x(np.array(tf_record["x"]))),
    ]:
        start = time.perf_counter()
        surface = surface_type(CASE / "data/unifac_surface.json")
        history = []
        accepted = False
        for iteration in range(20):
            solved = column.solve(surface, 183, 159, 16, 48, archived["S"], archived["D"], init=initial, maxeval=300)
            initial = np.array(solved["rs"])
            x, grid_y, grid_t = surface.state(initial)
            t, y = backend.bubble(x)
            check = stage_checks(archived, x, y, t, float(abs(y.sum(axis=1) - 1).max()))
            history.append(dict(iteration=iteration, solver_passed=solved["success"], **check))
            if check["validation"]["passed"] and check["maximum_stage_balance_mol_s"] < 1e-8:
                accepted = True
                break
            surface.delta += np.log(y / grid_y)
            surface.dt += t - grid_t
        answer = dict(
            initialization=label,
            accepted=accepted,
            elapsed_s=time.perf_counter() - start,
            history=history,
            x=x.tolist(),
            y=y.tolist(),
            T=t.tolist(),
        )
        write(output / ("column_" + label + ".json"), answer)
        histories.append({k: v for k, v in answer.items() if k not in ["x", "y", "T"]})
        print(
            json.dumps(dict(initialization=label, accepted=accepted, seconds=answer["elapsed_s"], final=history[-1])),
            flush=True,
        )
    write(output / "column_restarts.json", histories)
    if not all(run["accepted"] for run in histories):
        raise RuntimeError("Column audit did not pass direct-equilibrium and material-balance checks")
    return {"runs": histories}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dependency-root", type=Path)
    parser.add_argument("--columns", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/paper_agent/unifac-audit-20260928")
    args = parser.parse_args()
    if args.dependency_root:
        sys.path.insert(0, str(args.dependency_root.resolve()))
    files = [p for p in CASE.rglob("*") if p.is_file() and p.suffix in {".json", ".csv"}]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    backend = UNIFACAuditBackend()
    result = audit_base(backend, args.output)
    print(
        json.dumps(
            {
                "versions": result["provenance"]["versions"],
                "reference": result["experimental_point_reproduction"],
                "columns": result["column_checks"],
                "decomposition": result["fixed_state_decomposition"],
            }
        ),
        flush=True,
    )
    if args.columns:
        audit_columns(backend, args.output)
    write(
        args.output / ("integrity_" + version("thermo") + ".json"),
        dict(
            source_hashes=hashes,
            unchanged=all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == value for p, value in hashes.items()),
        ),
    )


if __name__ == "__main__":
    main()
