# ThermoEqui-Agent: separation-design case studies

Numerical code, equilibrium data, process results, and figures for the three
applications in **ThermoFormer, Section 2.2 and Supplementary Information S7**.
The case studies couple ThermoFormer phase-equilibrium predictions to material
balances and equilibrium-stage calculations. This directory contains the
deterministic scientific calculations underlying those applications.

| Case | Experimental reference | Process calculation | Paper location |
|---|---|---|---|
| [n-Heptane / n-nonane](cases/binary_distillation/README.md) | 16 isobaric VLE states | Binary distillation; common reflux ratio; interpolation and reflux sensitivity | Fig. 2a; S7.2; Fig. S3 |
| [sec-Butyl alcohol / sec-butyl acetate / DMF](cases/extractive_distillation/README.md) | 17 ternary VLE states | Extractive distillation; 182/183-stage boundary; common-column UNIFAC comparison | Fig. 2b; S7.3; Fig. S4 |
| [n-Heptane / benzene / furfural](cases/crossflow_extraction/README.md) | Six tie lines at each of two temperatures | Crossflow extraction; stage count, solvent allocation, and solvent dosage | Fig. 2c; S7.4; Fig. S5 |

All cases use **101.3 kPa** and a fresh nonsolvent feed of **1 mol/s**.
Compositions are mole fractions unless explicitly reported as mol%.

## Reproduce the reported process results

Run from the repository root with Python 3.10 or later:

```bash
python -m pip install -r ThermoAgent/requirements.txt
python ThermoAgent/reproduce.py
python -m unittest discover -s ThermoAgent/tests -v
```

The default calculation uses the bundled, unrounded equilibrium predictions.
It recalculates binary stage stepping, ternary column balances and performance,
and all crossflow material balances, including fresh interpolation of the
experimental tie lines. It checks the results against the reported values and
writes JSON tables to `ThermoAgent/generated/`. No model weights or API keys are
needed for this mode. Use `--case binary`, `--case extractive`, or `--case extraction`
to run a single study, and `--output PATH` to select an output directory.

This is a process-level reproduction from archived equilibrium states, not a
fresh neural-network evaluation. The recorded LLE endpoint interface accepts
only covered model/feed/temperature combinations and rejects unmatched states;
it is not a general-purpose property package.

## Fresh model evaluation and column solution

For fresh ThermoFormer evaluation, install the repository's model environment
and retrieve the registered weights with Git LFS as described in the
[repository installation guide](../README.md#installation). Original UNIFAC
reproduction requires `thermo==0.6.1`. Molecular input vectors for these case
components are included, together with their feature-cache and checkpoint
identifiers; model weights remain in the repository's `models/` directory.

```bash
python -m pip install thermo==0.6.1
python ThermoAgent/inference.py --case binary_distillation --model thermoformer
python ThermoAgent/inference.py --case binary_distillation --model unifac
python ThermoAgent/inference.py --case extractive_distillation --model thermoformer --column-states
python ThermoAgent/inference.py --case extractive_distillation --model unifac --column-states
python ThermoAgent/solve_column.py --model thermoformer --stages 182
python ThermoAgent/solve_column.py --model thermoformer --stages 183
python ThermoAgent/solve_column.py --model unifac --stages 183
python ThermoAgent/lle_inference.py --model thermoformer --all
python ThermoAgent/lle_inference.py --model unifac --all
```

`inference.py` independently solves for bubble temperatures at the measured
liquid compositions and fixed pressure, then checks the saved predictions.
`--column-states` additionally evaluates every local column composition.
`solve_column.py` uses a smooth equilibrium grid and the published trajectory
as a continuation initial guess, re-solves the component balances, and refines
against direct bubble calculations until the stage residual is below
1e-8 mol/s. It reproduces the reported configurations; it does not repeat a
global design optimization. `--repository PATH` selects another checkout
containing the registered weights and `src/thermoformer`.

`lle_inference.py` computes new coexistence endpoints at each source's own feed
and propagates the resulting raffinate. The ThermoFormer path evaluates the
checkpoint's continuous ternary binodal and checks the feed lever rule,
chemical-potential equality and finite-grid TPD. The UNIFAC-LLE path uses the
LLE-specific interaction table, Gibbs-grid initialization, common-tangent
correction and a local TPD screen. No measured endpoints enter either model
calculation. `--all` evaluates 74 configurations per model (8 stage-count
designs, 22 allocations and 44 single-stage dosages); omitting it runs the
retained three-stage design at 303.15 K. Failed split searches are not
interpreted as single-phase classifications.

## Results and interpretation

| Reported comparison | Experimental-data reference | ThermoFormer | UNIFAC |
|---|---:|---:|---:|
| Binary distillation, PCHIP: stages / feed stage | 11 / 5 | 12 / 6 | 12 / 6 |
| Binary distillation, linear interpolation: stages | 11 | 13 | 12 |
| Extractive distillation, common 183-stage column: ester purity (mol%) | — | 99.508632 | 26.451879 |
| Extractive distillation, common 183-stage column: ester recovery (%) | — | 98.008502 | 26.053107 |
| Three-stage extraction at 303.15 K: benzene recovery (%) | 72.33 | 71.15 | 78.69 |
| Three-stage extraction at 303.15 K: heptane retention (%) | 82.81 | 81.15 | 81.60 |

The experimental references are process calculations derived from measured
phase-equilibrium data, not measurements of operating columns or extractors.
The ternary distillation comparison has no experimental column trajectory.
All 183 stages of its selected ThermoFormer trajectory lie outside the
composition convex hull and temperature interval of the 17 measured states.
Its results therefore describe model-based extrapolative process calculations.

Distillation assumes constant molar overflow, saturated-liquid feeds, a total
condenser, and an equilibrium reboiler. Counts include the reboiler and exclude
the condenser. Crossflow extraction is isothermal and isobaric; every source
propagates its own raffinate. These are preliminary equilibrium-stage designs.

## Figures and data organization

Each case has `data/`, `results/`, an English method/data guide, and a `plot.py`
script. `figures/` contains the corresponding SI composite in PNG, PDF, and SVG.
To regenerate the figures:

```bash
python ThermoAgent/cases/binary_distillation/plot.py
python ThermoAgent/cases/extractive_distillation/plot.py
python ThermoAgent/cases/crossflow_extraction/plot.py
```

The PDF and SVG outputs retain vector graphics; appearance can vary slightly
with locally available fonts. Figure scripts read the complete archived data.
`provenance.json` records sources, checkpoint hashes, and component identities;
`checksums.json` records SHA-256 hashes of the numerical inputs and result tables.
Generated files are ignored by Git except for the supplied SI figure assets.

## Experimental sources

1. Gupta, B. S.; Lee, M.-J. Isobaric vapor–liquid equilibrium for binary systems
   of toluene + o-xylene, benzene + o-xylene, nonane + benzene and nonane + heptane
   at 101.3 kPa. *Fluid Phase Equilibria* **352**, 86–92 (2013).
   [DOI: 10.1016/j.fluid.2013.05.016](https://doi.org/10.1016/j.fluid.2013.05.016).
2. Zhang, X.; Liu, Y.; Jian, C.; Wei, Y.; Liu, H. Experimental isobaric vapor–liquid
   equilibrium for ternary system of sec-butyl alcohol + sec-butyl acetate +
   N,N-dimethyl formamide at 101.3 kPa. *Fluid Phase Equilibria* **383**, 5–10 (2014).
   [DOI: 10.1016/j.fluid.2014.09.021](https://doi.org/10.1016/j.fluid.2014.09.021).
3. Kumar, U. K. A.; Mohan, R. Liquid–liquid equilibria measurement of systems
   involving alkanes (heptane and dodecane), aromatics (benzene or toluene), and
   furfural. *Journal of Chemical & Engineering Data* **56**, 485–490 (2011).
   [DOI: 10.1021/je100908f](https://doi.org/10.1021/je100908f).

These papers provide the equilibrium measurements. The separation tasks,
specifications, and computed designs are the ThermoFormer application studies.
