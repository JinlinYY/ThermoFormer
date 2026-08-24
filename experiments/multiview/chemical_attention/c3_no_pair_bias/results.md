# c3_no_pair_bias formal results

Status: supervised-only seeds 0--4 completed on `overall_binary_ternary`.

| Task output | MAE | RMSE | R² |
|---|---:|---:|---:|
| P, isothermal | 8.741 ± 4.253 kPa | 21.551 ± 11.094 kPa | 0.962 ± 0.030 |
| y, isothermal | 0.0251 ± 0.0039 | 0.0445 ± 0.0105 | 0.980 ± 0.009 |
| T, isobaric | 2.475 ± 0.241 K | 4.251 ± 0.693 K | 0.978 ± 0.009 |
| y, isobaric | 0.0286 ± 0.0047 | 0.0509 ± 0.0102 | 0.972 ± 0.011 |

Best T MAE and y metrics, but weaker pressure metrics. See `reports/c1_ablation_overall_binary_ternary.md`.
