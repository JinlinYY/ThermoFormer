# A5 Direct activity-coefficient decoding

Mixture-aware tokens directly decode log-gamma. The Psat branch and VLE solver are
retained, but the scalar excess-Gibbs bottleneck and its hard Gibbs-Duhem construction
are removed. Because this changes the latent decoder as well as the hard
Gibbs--Duhem construction, it is not interpreted as an isolated P1 estimate.
Config: `experiments/ablation/architecture/a5_direct_activity/config.json`.

```powershell
conda run -n ggnn39 python scripts\run_ablation_suite.py --variant a5_direct_activity --device cuda
```
