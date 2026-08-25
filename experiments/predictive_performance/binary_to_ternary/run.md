# Binary-to-ternary transfer

```powershell
conda run -n ggnn39 python scripts\run_c1_physics_finetune.py --protocol binary_to_ternary_zero_shot --seeds 0 1 2 3 4
conda run -n ggnn39 python scripts\run_c1_physics_finetune.py --protocol binary_to_ternary_scale_0.05 --seeds 0 1 2 3 4
conda run -n ggnn39 python scripts\run_c1_physics_finetune.py --protocol binary_to_ternary_scale_0.1 --seeds 0 1 2 3 4
conda run -n ggnn39 python scripts\run_c1_physics_finetune.py --protocol binary_to_ternary_scale_0.25 --seeds 0 1 2 3 4
conda run -n ggnn39 python scripts\run_c1_physics_finetune.py --protocol binary_to_ternary_scale_0.5 --seeds 0 1 2 3 4
conda run -n ggnn39 python scripts\run_c1_physics_finetune.py --protocol binary_to_ternary_scale_1 --seeds 0 1 2 3 4
```

All six protocols share the same ternary test systems for a given seed.
