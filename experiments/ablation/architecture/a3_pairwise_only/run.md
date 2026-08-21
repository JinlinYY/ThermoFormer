# A3 Pairwise-only interaction

Each i-j potential sees only the two molecular/component states in that pair.
Pair potentials are summed invariantly and cannot access the third identity.
Config: `experiments/ablation/architecture/a3_pairwise_only/config.json`.

```powershell
conda run -n ggnn39 python scripts\run_ablation_suite.py --variant a3_pairwise_only --device cuda
```
