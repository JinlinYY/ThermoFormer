# A1d Without Uni-Mol v2

Runs the five-seed controlled representation ablation with RDKit descriptors and functional-group features retained.

Config: `experiments/ablation/architecture/a1_no_unimol/config.json`.

```powershell
conda run -n ggnn39 python scripts\run_ablation_suite.py --variant a1_no_unimol --device cuda
```
