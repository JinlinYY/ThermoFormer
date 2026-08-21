# A6 Direct VLE prediction

The thermodynamic gamma/Psat/Raoult/solver path is replaced by capacity-comparable
shared MLP heads. Masked softmax bounds y; positive pressure and bounded temperature
heads provide only basic numerical ranges.
Config: `experiments/ablation/architecture/a6_direct_vle/config.json`.

```powershell
conda run -n ggnn39 python scripts\run_ablation_suite.py --variant a6_direct_vle --device cuda
```
