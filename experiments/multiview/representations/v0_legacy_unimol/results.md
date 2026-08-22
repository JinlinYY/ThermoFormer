# v0_legacy_unimol results

Status: completed Table-1-style five-seed evaluation.

| Evaluation setting | Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² |
|---|---|---:|---:|---:|---:|---:|---:|
| Binary train → binary test | isothermal (P+y) | 17.2621 ± 8.4166 kPa | 35.1277 ± 14.9344 kPa | 0.9109 ± 0.0512 | 0.0681 ± 0.0146 | 0.1023 ± 0.0231 | 0.8979 ± 0.0490 |
| Binary train → binary test | isobaric (T+y) | 5.7524 ± 1.6082 K | 8.0851 ± 2.5033 K | 0.9196 ± 0.0517 | 0.0638 ± 0.0217 | 0.0917 ± 0.0270 | 0.9085 ± 0.0576 |
| Binary+ternary train → binary test | isothermal (P+y) | 18.5682 ± 6.4038 kPa | 40.4512 ± 14.0889 kPa | 0.8825 ± 0.0517 | 0.0720 ± 0.0158 | 0.1083 ± 0.0203 | 0.8872 ± 0.0439 |
| Binary+ternary train → binary test | isobaric (T+y) | 5.7234 ± 1.5598 K | 8.1552 ± 2.0199 K | 0.9255 ± 0.0247 | 0.0680 ± 0.0161 | 0.0987 ± 0.0176 | 0.8980 ± 0.0393 |
| Binary+ternary train → ternary test | isothermal (P+y) | 4.4322 ± 3.3948 kPa | 5.6826 ± 4.0729 kPa | 0.8879 ± 0.1295 | 0.0531 ± 0.0160 | 0.0729 ± 0.0197 | 0.9093 ± 0.0481 |
| Binary+ternary train → ternary test | isobaric (T+y) | 2.6687 ± 0.4595 K | 3.6043 ± 0.7954 K | 0.9487 ± 0.0396 | 0.0504 ± 0.0138 | 0.0695 ± 0.0233 | 0.8913 ± 0.0790 |

Machine-readable source: `results/multiview/predictive/representation_performance.csv`.
