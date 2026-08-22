# v5_three_view_naive

Config: `experiments/multiview/representations/v5_three_view_naive/config.json`.

All staged commands use the shared source `scripts/run_multiview_suite.py` and fixed committed splits.

```powershell
conda run -n ggnn39 python scripts\run_multiview_suite.py --variant v5_three_view_naive --stage screening --device cuda
```
