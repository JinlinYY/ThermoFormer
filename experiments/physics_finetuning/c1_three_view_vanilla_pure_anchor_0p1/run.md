# Run

Configuration: `experiments/physics_finetuning/c1_three_view_vanilla_pure_anchor_0p1/config.json`.

```powershell
conda run --no-capture-output -n ggnn39 python scripts\run_c1_physics_finetune.py --objective pure_anchor_0p1 --device cuda
```

This is an exploratory, test-exposed seed-0 comparison. Add `--smoke` for an
isolated smoke run.
