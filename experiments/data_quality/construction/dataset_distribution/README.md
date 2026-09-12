# Phase-equilibrium dataset distribution

Dataset composition, state-space coverage, and molecular-family coverage for the registered VLE and LLE workbooks. These figures describe the source records before training-specific filtering: 27,304 VLE and 19,844 LLE observations.

## Figures

- [VLE dataset overview](figures/vle_dataset_overview.png)
- [LLE dataset overview](figures/lle_dataset_overview.png)

Each overview is available in PNG, PDF, and SVG formats in `figures/`. Numerical source tables are in `results/phase_equilibrium/`; the accompanying analysis is in [reports/phase_equilibrium_dataset_analysis.md](reports/phase_equilibrium_dataset_analysis.md).

## Reproduction

Run from the repository root in the declared Python environment:

```console
python scripts/data/dataset_distribution/plot_phase_equilibrium_dataset_overviews.py
```

The script reads the four workbooks under `datasets/` without modifying them. Components are defined by canonical SMILES and systems by unordered component sets; molecular families use the RDKit/SMARTS rules in `molecular_space.py`. The fixed plotting seed is 42.
