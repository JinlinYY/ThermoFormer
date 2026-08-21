# Run

Config: `experiments/predictive_performance/overall_binary/config.json`.

```powershell
conda activate ggnn39
python scripts/run_paper_suite.py --protocol overall_binary --device cuda
```

The command consumes `splits/overall_binary/seed_0.json` through `seed_4.json`; it never regenerates a split during training.
