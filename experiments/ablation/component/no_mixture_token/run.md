# Run: no mixture token

Run from the project root:

```powershell
conda activate ggnn39
python scripts/train_thermoformer.py --config experiments/ablation/component/no_mixture_token/config.json
```

This experiment inherits the full baseline and changes only
`model.use_mixture_token=false`. Artifacts are written to
`runs/experiments/ablation/component/no_mixture_token/`; the summary is written to `results.md`.
