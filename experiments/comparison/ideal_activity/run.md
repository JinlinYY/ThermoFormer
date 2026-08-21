# Run: ideal activity baseline

Run from the project root:

```powershell
conda activate ggnn39
python scripts/train_thermoformer.py --config experiments/comparison/ideal_activity/config.json
```

This experiment inherits the full baseline and changes only
`model.activity_mode="ideal"`. Artifacts are written to
`runs/experiments/comparison/ideal_activity/`; the summary is written to `results.md`.
