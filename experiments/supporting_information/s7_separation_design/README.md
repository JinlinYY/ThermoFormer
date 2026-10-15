# S7 separation-design artifacts

This directory collects the reproducibility material for the three separation-design cases in
the ThermoFormer paper and Supporting Information (SI):

1. n-heptane/n-nonane binary distillation;
2. sec-butyl alcohol/sec-butyl acetate/DMF extractive distillation;
3. n-heptane/benzene/furfural crossflow extraction.

The deterministic calculations and acceptance tests remain in [`ThermoAgent/`](../../../ThermoAgent/).
The raw common-vapour-pressure sensitivity output for the extractive-distillation case is archived
under [`results/common-psat-20260928/`](results/common-psat-20260928/). The exact generated DWSIM
binary column for the n-heptane/n-nonane case is in
[`ThermoAgent/cases/dwsim_exports/flowsheets/`](../../../ThermoAgent/cases/dwsim_exports/flowsheets/)
with provenance JSON and a SHA-256 entry in `checksums.json`.

## Coverage and limits

The common-Psat audit preserves the 17-state protocol, the 183-stage column comparison, the Li
2013 reference correlation, and the Huang 2015 sensitivity correlation quoted in the SI. Its
`RESULTS.zh-CN.md` records the numerical outputs and the extrapolation limitations; those values
are archived evidence, not newly generated claims.

The DWSIM archive contains the paper-aligned n-heptane/n-nonane binary flow sheet. No exact
sec-butyl alcohol/sec-butyl acetate/DMF or n-heptane/benzene/furfural DWSIM project was present in
the supplied `D:\VLE` source tree, so the release does not fabricate one. Their deterministic
ThermoFormer protocols remain reproducible from `ThermoAgent/` and the common-Psat outputs.

Run DWSIM exports only on a machine with the external DWSIM Automation API. Recalculate every
archive before interpreting it as an engineering result and inspect convergence, material balance,
equilibrium residuals, property-package coverage, and phase stability.

## Reproduction entry points

- Deterministic cases: [`ThermoAgent/readme.md`](../../../ThermoAgent/readme.md)
- DWSIM bridge and acceptance checks: [`docs/guides/dwsim/`](../../../docs/guides/dwsim/)
- Archived generator sources: [`scripts/reproduce/dwsim_paper_cases/`](../../../scripts/reproduce/dwsim_paper_cases/)
- Plot the common-Psat audit: `python scripts/reproduce/plot_paper_common_psat.py`
