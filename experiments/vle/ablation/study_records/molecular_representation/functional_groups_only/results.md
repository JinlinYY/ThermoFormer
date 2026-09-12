# Functional-group-only representation

Setting: `overall_binary_ternary`, seeds 0--4. Values are mean ± sample standard deviation.

| Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| Isobaric | 31.677 ± 14.469 K | 69.908 ± 50.412 K | -7.715 ± 11.096 | 0.2024 ± 0.0224 | 0.2660 ± 0.0270 | 0.252 ± 0.143 | 96.7% |
| Isothermal | 85588.710 ± 191265.386 kPa | 1759267.139 ± 3933474.961 kPa | -773507701.574 ± 1729615797.541 | 0.1544 ± 0.0191 | 0.2294 ± 0.0265 | 0.564 ± 0.102 | 63.4% |

Functional-group counts alone are insufficient for VLE prediction. The error values must be interpreted with their reduced valid coverage.

Machine-readable source: `experiments/vle/ablation/multiview/predictive/runs/v3_functional_group_only.on.overall_binary_ternary/metrics_summary.csv` (SHA-256 `b92734427b5ae73b72800d2567ee9df25865a3f0d253410cffb2f743eb80e94f`).
