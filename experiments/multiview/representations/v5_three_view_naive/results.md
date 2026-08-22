# v5_three_view_naive results

Status: completed Table-1-style five-seed evaluation.

| Evaluation setting | Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² |
|---|---|---:|---:|---:|---:|---:|---:|
| Binary train → binary test | isothermal (P+y) | 9.6229 ± 5.0862 kPa | 20.9714 ± 10.6076 kPa | 0.9676 ± 0.0219 | 0.0283 ± 0.0047 | 0.0487 ± 0.0108 | 0.9771 ± 0.0098 |
| Binary train → binary test | isobaric (T+y) | 2.7491 ± 0.5189 K | 4.5396 ± 0.4999 K | 0.9767 ± 0.0056 | 0.0294 ± 0.0054 | 0.0510 ± 0.0079 | 0.9732 ± 0.0076 |
| Binary+ternary train → binary test | isothermal (P+y) | 9.0343 ± 4.3181 kPa | 20.4080 ± 9.3877 kPa | 0.9687 ± 0.0210 | 0.0274 ± 0.0046 | 0.0482 ± 0.0093 | 0.9777 ± 0.0079 |
| Binary+ternary train → binary test | isobaric (T+y) | 2.5746 ± 0.3312 K | 4.2451 ± 0.8648 K | 0.9785 ± 0.0119 | 0.0300 ± 0.0045 | 0.0523 ± 0.0070 | 0.9719 ± 0.0069 |
| Binary+ternary train → ternary test | isothermal (P+y) | 2.8492 ± 1.0131 kPa | 3.3963 ± 1.0962 kPa | 0.9663 ± 0.0180 | 0.0196 ± 0.0043 | 0.0267 ± 0.0066 | 0.9884 ± 0.0053 |
| Binary+ternary train → ternary test | isobaric (T+y) | 1.6859 ± 0.4630 K | 2.2112 ± 0.7945 K | 0.9750 ± 0.0304 | 0.0332 ± 0.0189 | 0.0534 ± 0.0371 | 0.9189 ± 0.0786 |

Machine-readable source: `results/multiview/predictive/representation_performance.csv`.
