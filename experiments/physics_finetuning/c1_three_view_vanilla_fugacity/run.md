# Run

Configuration: `experiments/physics_finetuning/c1_three_view_vanilla_fugacity/config.json`.

```powershell
conda run --no-capture-output -n ggnn39 python scripts\run_c1_physics_finetune.py --device cuda --seeds 0 1 2 3 4
```

This command is locked to `overall_binary_ternary`, seeds `0--4`.
