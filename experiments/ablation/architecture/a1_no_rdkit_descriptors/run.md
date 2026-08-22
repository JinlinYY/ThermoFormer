# A1c Without RDKit descriptors

Runs the five-seed controlled representation ablation with Uni-Mol v2 and functional-group features retained.

Config: `experiments/ablation/architecture/a1_no_rdkit_descriptors/config.json`.

```powershell
conda run -n ggnn39 python scripts\run_ablation_suite.py --variant a1_no_rdkit_descriptors --device cuda
```
