# C1 molecular-view ablations

Only the `overall_binary_ternary` protocol is retained. The runnable view
controls are:

- `v1_rdkit_only`;
- `v3_functional_group_only`;
- `v4_rdkit_unimol_naive`.

The Uni-Mol-only control is `chemical_attention/c0_current_vanilla`; the full
three-view final model is `chemical_attention/c1_three_view_vanilla`.

```powershell
conda run -n ggnn39 python scripts\run_multiview_suite.py --device cuda
conda run -n ggnn39 python scripts\run_chemical_attention_suite.py --device cuda
conda run -n ggnn39 python scripts\build_c1_ablation_report.py
```

All view/interaction experiments use supervised training only. The fugacity
Stage 2 comparison is isolated under `experiments/physics_finetuning/`.
