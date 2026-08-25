# RDKit + Uni-Mol representation

Setting: `overall_binary_ternary`, seeds 0--4. Values are mean ± sample standard deviation.

| Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| Isobaric | 2.578 ± 0.450 K | 4.182 ± 1.194 K | 0.978 ± 0.017 | 0.0308 ± 0.0045 | 0.0539 ± 0.0104 | 0.969 ± 0.011 | 100.0% |
| Isothermal | 9.297 ± 4.681 kPa | 21.945 ± 12.623 kPa | 0.957 ± 0.038 | 0.0272 ± 0.0033 | 0.0485 ± 0.0098 | 0.977 ± 0.009 | 100.0% |

Adding the functional-group view to this two-view model improves pressure and isobaric-temperature MAE, while vapor-composition changes are small.

Machine-readable source: `results/multiview/predictive/runs/v4_rdkit_unimol_naive.on.overall_binary_ternary/metrics_summary.csv` (SHA-256 `19b8ef2ea6a6c9df9e28fc8c01855a53d0628484d9339b7da2c6a7b477f2334f`).
