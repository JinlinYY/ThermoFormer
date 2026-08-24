# Run

Configuration: `experiments/physics_finetuning/c1_three_view_vanilla_fugacity/config.json`.

```powershell
conda run --no-capture-output -n ggnn39 python scripts\run_c1_physics_finetune.py --device cuda --seeds 0 1 2 3 4
```

With no `--protocol` argument, this command runs `overall_binary_ternary` and
is locked to seeds `0--4`.

For another registered protocol, first generate and commit its supervised C1
checkpoints with `scripts/run_paper_suite.py`, then run:

```powershell
conda run -n ggnn39 python scripts/run_c1_physics_finetune.py --protocol unseen_component --device cuda
```

The physics runner accepts one registered protocol per invocation and defaults
to seeds `0--4`.  This keeps each protocol's aggregation and report transaction
independent.
