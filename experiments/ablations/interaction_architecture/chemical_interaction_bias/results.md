# Chemical-interaction-biased Transformer

Setting: `overall_binary_ternary`, seeds 0--4. Values are mean ± sample standard deviation.

| Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| Isobaric | 2.706 ± 0.574 K | 4.648 ± 1.232 K | 0.973 ± 0.018 | 0.0300 ± 0.0055 | 0.0537 ± 0.0132 | 0.969 ± 0.015 | 100.0% |
| Isothermal | 8.303 ± 3.748 kPa | 19.761 ± 9.406 kPa | 0.968 ± 0.022 | 0.0267 ± 0.0054 | 0.0466 ± 0.0118 | 0.978 ± 0.010 | 100.0% |

The chemical-attention bias does not consistently improve the three-view vanilla model and is not retained in the final architecture.

Machine-readable source: `results/multiview/chemical_attention/formal/runs/c2_chemical_bias_full.on.overall_binary_ternary/metrics_summary.csv` (SHA-256 `32d8cf09f3f58c450f1519df6b23e1490c47d67798a41892b0cc0e1f60cb274d`).
