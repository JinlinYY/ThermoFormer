# v1_rdkit_only

Config: `experiments/multiview/representations/v1_rdkit_only/config.json`.

All staged commands use the shared source `scripts/run_multiview_suite.py` and fixed committed splits.

```powershell
conda run -n ggnn39 python scripts\run_multiview_suite.py --variant v1_rdkit_only --stage screening --device cuda
```
