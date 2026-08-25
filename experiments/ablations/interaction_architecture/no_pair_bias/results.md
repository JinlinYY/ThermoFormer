# Context pair without attention bias

Setting: `overall_binary_ternary`, seeds 0--4. Values are mean ± sample standard deviation.

| Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| Isobaric | 2.475 ± 0.241 K | 4.251 ± 0.693 K | 0.978 ± 0.009 | 0.0286 ± 0.0047 | 0.0509 ± 0.0102 | 0.972 ± 0.011 | 100.0% |
| Isothermal | 8.741 ± 4.253 kPa | 21.551 ± 11.094 kPa | 0.962 ± 0.030 | 0.0251 ± 0.0039 | 0.0445 ± 0.0105 | 0.980 ± 0.009 | 100.0% |

The context-pair variant improves several vapor-composition metrics but has a larger pressure error than C1, so it is not selected as the balanced final model.

Machine-readable source: `results/multiview/chemical_attention/formal/runs/c3_no_pair_bias.on.overall_binary_ternary/metrics_summary.csv` (SHA-256 `b6ae71e9a466fdf57f178231c55256ae995c6c285cf522e277bedcbcdbc8bd00`).
