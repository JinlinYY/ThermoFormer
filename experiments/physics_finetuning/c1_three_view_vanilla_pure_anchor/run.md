# Run

Configuration: `experiments/physics_finetuning/c1_three_view_vanilla_pure_anchor/config.json`.

```powershell
conda run --no-capture-output -n ggnn39 python scripts\run_c1_physics_finetune.py --objective pure_anchor --device cuda
```

Smoke outputs are isolated by adding `--smoke`.
