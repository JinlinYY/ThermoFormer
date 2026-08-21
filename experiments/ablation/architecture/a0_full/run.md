# A0 Full ThermoFormer

This is an immutable reference to the existing formal runs. Its exact snapshot is
`configs/ablation/full_model_reference.yaml`; the ablation suite reuses those artifacts.
Config: `experiments/ablation/architecture/a0_full/config.json`.

```powershell
conda run -n ggnn39 python scripts\run_ablation_suite.py --variant a0_full --device cuda
```
