# A1 Without pretrained molecular representation

Uni-Mol v2 is replaced by 24 fixed, scaled RDKit 2D descriptors followed by the
unchanged learned molecular projection.
Config: `experiments/ablation/architecture/a1_rdkit_descriptors/config.json`.

```powershell
conda run -n ggnn39 python scripts\run_ablation_suite.py --variant a1_rdkit_descriptors --device cuda
```
