# ThermoFormer interpretability analysis

This directory contains the locked-checkpoint analyses for learned multicomponent thermodynamics. The workflow uses the validation-selected full ThermoFormer and the matching pairwise-only ablation; test metrics never select a checkpoint or displayed system.

Run from the project root in the `ggnn39` environment:

```powershell
conda activate ggnn39
python scripts/run_interpretability.py --device cuda
```

The four machine-readable tables are under `results/`, the vector and 600 dpi main figures are under `figures/`, and the quantitative interpretation plus input/output hashes are under `reports/`. Pair potentials and latent coordinates are treated as model-internal variables. Their physical interpretation is limited by the independent masking and held-out thermodynamic checks documented in the report.
