# v3_functional_group_only

Config: `experiments/multiview/representations/v3_functional_group_only/config.json`.

All staged commands use the shared source `scripts/run_multiview_suite.py` and fixed committed splits.

```powershell
conda run -n ggnn39 python scripts\run_multiview_suite.py --variant v3_functional_group_only --stage screening --exploratory --device cuda
```

This post-hoc representation control is written to `screening_exploratory` and
cannot alter the locked Stage C variant set.
