# C2 validation-only optimization

These candidates implement the bounded matrix in the design note. They are
selected only on the committed `overall_binary_ternary` validation partition
for seeds 0, 1, and 2. The test partition is never evaluated in this stage.

The locked selection score is the mean, over seeds, of the six validation
MAE/RMSE ratios (P, T, and y) relative to `o0_original`. Lower is better. After
one candidate is selected, its configuration is frozen before the five-seed
test evaluation.

All candidates use data supervision only (`epochs_physics=0`).

```powershell
conda run --no-capture-output -n ggnn39 python scripts\run_c2_optimization.py --device cuda
```

After reviewing and committing the generated selection manifest and report:

```powershell
conda run --no-capture-output -n ggnn39 python scripts\run_c2_selected_formal.py --device cuda --confirm-selection-reviewed
```
