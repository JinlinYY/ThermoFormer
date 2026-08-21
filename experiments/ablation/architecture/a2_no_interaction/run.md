# A2 Without multicomponent interaction

Each component contributes an independently decoded unary nonideality potential;
no learned term reads another component identity.
Config: `experiments/ablation/architecture/a2_no_interaction/config.json`.

```powershell
conda run -n ggnn39 python scripts\run_ablation_suite.py --variant a2_no_interaction --device cuda
```
