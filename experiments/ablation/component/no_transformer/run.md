# Run: no interaction Transformer

Run from the project root:

```powershell
conda activate ggnn39
python scripts/train_thermoformer.py --config experiments/ablation/component/no_transformer/config.json
```

This experiment inherits the full baseline, disables the component-interaction
Transformer, and sets its layer count to zero. Artifacts are written to
`runs/experiments/ablation/component/no_transformer/`; the summary is written to `results.md`.
