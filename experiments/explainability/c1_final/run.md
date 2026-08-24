# Run command

```powershell
conda run --no-capture-output -n ggnn39 python scripts\run_interpretability.py --device cuda
```

This command explains the five validation-selected final C1 checkpoints on `overall_binary_ternary` only.
The inherited model definition is recorded in `experiments/explainability/c1_final/config.json`;
analysis settings are fixed by the command defaults (256 states per seed, batch size 64).
