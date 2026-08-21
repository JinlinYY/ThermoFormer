# P6 Without all soft thermodynamic losses

All three removable physics-stage losses are zero. Hard Gibbs-Duhem, permutation,
composition normalization, pure-limit structure, and numerical solver equations remain.
Config: `experiments/ablation/thermodynamic_constraint/p6_no_soft_physics/config.json`.

```powershell
conda run -n ggnn39 python scripts\run_ablation_suite.py --variant p6_no_soft_physics --device cuda
```
