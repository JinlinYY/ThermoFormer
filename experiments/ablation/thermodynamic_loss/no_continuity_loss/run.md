# Run: no continuity loss

Run from the project root:

```powershell
conda activate ggnn39
python scripts/train_thermoformer.py --config experiments/ablation/thermodynamic_loss/no_continuity_loss/config.json
```

This experiment inherits the complete baseline and changes only
`training.continuity_weight=0.0`. The physics-stage epoch count is retained so that
the compute budget and amount of data supervision remain controlled.

Artifacts are written to
`runs/experiments/ablation/thermodynamic_loss/no_continuity_loss/`; the compact
summary is written to `results.md`.
