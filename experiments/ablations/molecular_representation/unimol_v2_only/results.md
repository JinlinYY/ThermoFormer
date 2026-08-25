# Uni-Mol vanilla baseline

Setting: `overall_binary_ternary`, seeds 0--4. Values are mean ± sample standard deviation.

| Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| Isobaric | 5.515 ± 1.445 K | 7.882 ± 1.977 K | 0.928 ± 0.024 | 0.0629 ± 0.0162 | 0.0893 ± 0.0183 | 0.914 ± 0.037 | 100.0% |
| Isothermal | 17.092 ± 5.275 kPa | 37.370 ± 12.819 kPa | 0.889 ± 0.050 | 0.0655 ± 0.0192 | 0.0962 ± 0.0255 | 0.906 ± 0.049 | 100.0% |

The three-view C1 model substantially reduces all four prediction errors relative to this Uni-Mol-only vanilla baseline.

Machine-readable source: `results/multiview/chemical_attention/formal/runs/c0_current_vanilla.on.overall_binary_ternary/metrics_summary.csv` (SHA-256 `7f06046047f6404c1f1e66ee7616eaecc6209d91b34c594665fdd2a4400562f2`).
