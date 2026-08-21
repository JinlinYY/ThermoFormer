# Run

Config: `experiments/predictive_performance/overall_binary_ternary/config.json`.

```powershell
conda activate ggnn39
python scripts/run_paper_suite.py --protocol overall_binary_ternary --device cuda
```

The system-disjoint test set is also the unseen-mixture evaluation. Binary and ternary metric rows are emitted separately.
