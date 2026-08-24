# Run

Configuration: `experiments/physics_finetuning/c1_three_view_vanilla/config.json`.

```powershell
conda run --no-capture-output -n ggnn39 python scripts\run_c1_physics_finetune.py --device cuda
```

For an isolated numerical smoke run, add `--smoke`.
