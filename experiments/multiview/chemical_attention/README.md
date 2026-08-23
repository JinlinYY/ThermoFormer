# Chemical-interaction-biased Transformer

This experiment family changes only molecular representation and interaction modules. Dataset workbooks, committed splits, thermodynamic equations, differentiable solvers, physics losses, and evaluation metrics remain frozen.

Pilot (seed 0 only):

```powershell
conda run --no-capture-output -n ggnn39 python scripts\run_chemical_attention_suite.py --stage pilot --device cuda
```

The five-seed formal stage must only be launched after reviewing the pilot report with the project owner.

```powershell
conda run --no-capture-output -n ggnn39 python scripts\run_chemical_attention_suite.py --stage formal --confirm-pilot-reviewed --device cuda
```
