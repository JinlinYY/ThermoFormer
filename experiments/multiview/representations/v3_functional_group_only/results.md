# v3_functional_group_only results

Status: completed Table-1-style five-seed evaluation.

| Evaluation setting | Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² |
|---|---|---:|---:|---:|---:|---:|---:|
| Binary train → binary test | isothermal (P+y) | 21497.1882 ± 47933.7661 kPa | 510164.5609 ± 1140512.6464 kPa | -133210773.1731 ± 297868344.4044 | 0.1414 ± 0.0175 | 0.2132 ± 0.0346 | 0.6396 ± 0.1134 |
| Binary train → binary test | isobaric (T+y) | 36.6105 ± 9.5189 K | 69.6412 ± 14.5064 K | -4.4467 ± 1.6052 | 0.2135 ± 0.0314 | 0.2849 ± 0.0427 | 0.1489 ± 0.2750 |
| Binary+ternary train → binary test | isothermal (P+y) | 100838.9173 ± 225363.6643 kPa | 1909645.0141 ± 4269724.7227 kPa | -811715524.8406 ± 1815051087.6204 | 0.1560 ± 0.0191 | 0.2313 ± 0.0252 | 0.5602 ± 0.0944 |
| Binary+ternary train → binary test | isobaric (T+y) | 32.2170 ± 14.1407 K | 70.4439 ± 49.5263 K | -7.5548 ± 10.9676 | 0.2073 ± 0.0216 | 0.2731 ± 0.0261 | 0.2328 ± 0.1461 |
| Binary+ternary train → ternary test | isothermal (P+y) | 23.0517 ± 9.7981 kPa | 31.3271 ± 19.6298 kPa | -3.6708 ± 5.4026 | 0.1409 ± 0.0418 | 0.2016 ± 0.0663 | 0.4808 ± 0.3104 |
| Binary+ternary train → ternary test | isobaric (T+y) | 20.1029 ± 10.4725 K | 40.7046 ± 44.4991 K | -17.7215 ± 35.1058 | 0.1628 ± 0.0191 | 0.2032 ± 0.0169 | 0.1669 ± 0.2328 |

Machine-readable source: `results/multiview/predictive/representation_performance.csv`.
