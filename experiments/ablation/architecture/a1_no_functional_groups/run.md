# A1e Without functional-group features

Runs the five-seed controlled representation ablation with RDKit descriptors and Uni-Mol v2 retained.

Config: `experiments/ablation/architecture/a1_no_functional_groups/config.json`.

```powershell
conda run -n ggnn39 python scripts\run_ablation_suite.py --variant a1_no_functional_groups --device cuda
```
