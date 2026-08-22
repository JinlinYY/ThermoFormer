# A0 Full ThermoFormer

This is the current Full hybrid model and must be trained for the new campaign. Its
architecture snapshot is `configs/ablation/full_model_reference.yaml`.
Config: `experiments/ablation/architecture/a0_full/config.json`.

```powershell
conda run -n ggnn39 python scripts\run_ablation_suite.py --variant a0_full --device cuda
```
