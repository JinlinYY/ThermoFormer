# A4 Condition concatenation

T, P, and x remain available but FiLM modulation is replaced by an ordinary
concatenation MLP.
Config: `experiments/ablation/architecture/a4_condition_concatenation/config.json`.

```powershell
conda run -n ggnn39 python scripts\run_ablation_suite.py --variant a4_condition_concatenation --device cuda
```
