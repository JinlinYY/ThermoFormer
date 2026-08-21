# Run: no FiLM

Run from the project root:

```powershell
conda activate ggnn39
python scripts/train_thermoformer.py --config experiments/ablation/component/no_film/config.json
```

This experiment inherits the full baseline and changes only `model.use_film=false`.
Artifacts are written to `runs/experiments/ablation/component/no_film/`; the summary is written to
`results.md`.
