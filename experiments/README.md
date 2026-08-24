# ThermoFormer experiment registry

The selected model is **C1 three-view vanilla Transformer**:

- RDKit descriptors + Uni-Mol v2 + SMARTS functional-group counts;
- independent view projections followed by concat projection;
- vanilla component Transformer;
- `chemical_attention_bias=false`;
- `context_pair_interaction=false`;
- the original symmetric `pair_potential` is retained.

The active ablation scope is only `overall_binary_ternary`: binary and ternary
systems are trained jointly and evaluated on the joint binary/ternary test split.

## Retained ablations

| Family | Retained experiments | Entry point |
|---|---|---|
| Molecular representation | RDKit-only, FG-only, RDKit+Uni-Mol, C0 Uni-Mol and full C1 | [`multiview/README.md`](multiview/README.md) |
| Interaction module | C1 vanilla, C2 chemical-biased, C3 context-pair-only | [`multiview/chemical_attention/README.md`](multiview/chemical_attention/README.md) |
| Physics fine-tuning | C1 Stage 1 versus fugacity-only Stage 2 | [`physics_finetuning/c1_three_view_vanilla_fugacity/README.md`](physics_finetuning/c1_three_view_vanilla_fugacity/README.md) |
| Explainability | Five-seed grouped Shapley, pair interaction and thermodynamic sensitivity for final C1 | [`explainability/c1_final/README.md`](explainability/c1_final/README.md) |

Generate the single consolidated report with:

```powershell
conda run -n ggnn39 python scripts\build_c1_ablation_report.py
```

The report is written to `reports/c1_ablation_overall_binary_ternary.md`, with
machine-readable rows under `results/c1_ablation/`.

The remaining `predictive_performance/`, `comparison/`, and
`interpolation_extrapolation/` directories are separate historical/generalization
studies. They are not part of the retained ablation matrix.

Every runnable leaf experiment keeps `config.json`, `run.md`, and `results.md`.
