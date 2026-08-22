# v0_legacy_unimol

Config: `experiments/multiview/representations/v0_legacy_unimol/config.json`.

All staged commands use the shared source `scripts/run_multiview_suite.py` and fixed committed splits.

```powershell
conda run -n ggnn39 python scripts\run_multiview_suite.py --variant v0_legacy_unimol --stage screening --device cuda
```
