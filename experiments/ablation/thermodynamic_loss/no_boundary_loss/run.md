# Run: no pure-boundary loss

Run from the project root:

```powershell
conda activate ggnn39
python scripts/train_thermoformer.py --config experiments/ablation/thermodynamic_loss/no_boundary_loss/config.json
```

This experiment inherits the complete baseline and changes only
`training.boundary_weight=0.0`. Artifacts are written to
`runs/experiments/ablation/thermodynamic_loss/no_boundary_loss/`.
