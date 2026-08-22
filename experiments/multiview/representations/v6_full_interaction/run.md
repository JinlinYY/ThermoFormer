# v6_full_interaction

Config: `experiments/multiview/representations/v6_full_interaction/config.json`.

All staged commands use the shared source `scripts/run_multiview_suite.py` and fixed committed splits.

```powershell
conda run -n ggnn39 python scripts\run_multiview_suite.py --variant v6_full_interaction --stage screening --device cuda
```
