# Chemical-interaction-biased Transformer

This experiment family changes only molecular representation and interaction modules. Dataset workbooks, committed splits, thermodynamic equations, differentiable solvers, and evaluation metrics remain frozen.

The current comparison uses data-supervised training only (`epochs_physics=0`). The formal ablation is restricted to binary+ternary training and the joint binary+ternary test (`overall_binary_ternary`); no other protocol belongs to this campaign.

Pilot (seed 0 only):

```powershell
conda run --no-capture-output -n ggnn39 python scripts\run_chemical_attention_suite.py --stage pilot --device cuda
```

The five-seed formal stage must only be launched after reviewing the pilot report with the project owner.

```powershell
conda run --no-capture-output -n ggnn39 python scripts\run_chemical_attention_suite.py --stage formal --protocol overall_binary_ternary --confirm-pilot-reviewed --device cuda
```
