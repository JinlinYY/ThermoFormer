# A1 Without pretrained molecular representation

Uni-Mol v2 is replaced by the original 24 fixed, hand-scaled RDKit 2D
descriptors followed by the unchanged learned molecular projection.
The explicit `rdkit_2d_legacy_fixed` representation freezes historical
`scaled24_v1` preprocessing; it cannot silently switch to the train-only
z-scaling used by the newer multi-view V1 experiment.
Config: `experiments/ablation/architecture/a1_rdkit_descriptors/config.json`.

```powershell
conda run -n ggnn39 python scripts\run_ablation_suite.py --variant a1_rdkit_descriptors --device cuda
```
