# Run

Formal seed-0 comparison:

Configuration: `experiments/physics_finetuning/c1_three_view_vanilla_fugacity_pure_anchor/config.json`.

```powershell
conda run --no-capture-output -n ggnn39 python scripts\run_c1_physics_finetune.py --objective fugacity_pure_anchor --device cuda
```

Smoke outputs are isolated from formal outputs:

```powershell
conda run --no-capture-output -n ggnn39 python scripts\run_c1_physics_finetune.py --objective fugacity_pure_anchor --device cuda --smoke
```
