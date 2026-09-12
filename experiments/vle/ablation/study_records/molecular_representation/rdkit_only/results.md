# RDKit-only representation

Setting: `overall_binary_ternary`, seeds 0--4. Values are mean ± sample standard deviation.

| Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| Isobaric | 2.650 ± 0.352 K | 4.500 ± 1.235 K | 0.974 ± 0.018 | 0.0306 ± 0.0047 | 0.0540 ± 0.0124 | 0.968 ± 0.014 | 100.0% |
| Isothermal | 8.515 ± 3.180 kPa | 19.010 ± 7.582 kPa | 0.971 ± 0.017 | 0.0275 ± 0.0032 | 0.0482 ± 0.0089 | 0.977 ± 0.008 | 100.0% |

RDKit descriptors provide a strong low-dimensional baseline, but the complete three-view model gives lower pressure and isobaric-temperature errors.

Machine-readable source: `experiments/vle/ablation/multiview/formal/runs/v1_rdkit_only.on.overall_binary_ternary/metrics_summary.csv` (SHA-256 `7d2dc9b845d5dd51b94f32350b2f8d72850b0be7934ff2e8ac6638a57a18ba2d`).
