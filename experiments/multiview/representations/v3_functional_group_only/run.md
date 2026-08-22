# v3_functional_group_only

Config: `experiments/multiview/representations/v3_functional_group_only/config.json`.

All staged commands use the shared source `scripts/run_multiview_suite.py` and fixed committed splits.

```powershell
conda run -n ggnn39 python scripts\run_multiview_suite.py --stage predictive --variant v3_functional_group_only --device cuda
```

The earlier seed-0 diagnostic remains in `screening_exploratory`; the predictive
stage is a separate five-seed Table-1-style comparison.
