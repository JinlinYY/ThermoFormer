# Run: ThermoFormer baseline

Run from the project root:

```powershell
conda activate ggnn39
python scripts/train_thermoformer.py --config experiments/baseline/thermoformer_base/config.json
```

This runs the complete model with the default 5-fold grouped cross-validation and
independent test split. Checkpoints and machine-readable records are written to
`runs/experiments/baseline/thermoformer_base/`; the final summary is written to `results.md`.
