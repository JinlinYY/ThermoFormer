# v2_unimol_only

Config: `experiments/multiview/representations/v2_unimol_only/config.json`.

All staged commands use the shared source `scripts/run_multiview_suite.py` and fixed committed splits.

```powershell
conda run -n ggnn39 python scripts\run_multiview_suite.py --variant v2_unimol_only --stage screening --exploratory --device cuda
```
