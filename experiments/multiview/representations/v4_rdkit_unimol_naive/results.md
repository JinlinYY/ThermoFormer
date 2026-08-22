# v4_rdkit_unimol_naive results

Status: completed Table-1-style five-seed evaluation.

| Evaluation setting | Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² |
|---|---|---:|---:|---:|---:|---:|---:|
| Binary train → binary test | isothermal (P+y) | 9.5504 ± 5.2142 kPa | 21.7252 ± 11.4696 kPa | 0.9640 ± 0.0272 | 0.0292 ± 0.0033 | 0.0506 ± 0.0090 | 0.9756 ± 0.0078 |
| Binary train → binary test | isobaric (T+y) | 2.7548 ± 0.4052 K | 4.5460 ± 0.8914 K | 0.9758 ± 0.0114 | 0.0305 ± 0.0023 | 0.0520 ± 0.0050 | 0.9724 ± 0.0049 |
| Binary+ternary train → binary test | isothermal (P+y) | 10.4519 ± 5.9742 kPa | 23.5401 ± 14.4578 kPa | 0.9553 ± 0.0403 | 0.0294 ± 0.0041 | 0.0517 ± 0.0102 | 0.9743 ± 0.0093 |
| Binary+ternary train → binary test | isobaric (T+y) | 2.6616 ± 0.4308 K | 4.2809 ± 1.1366 K | 0.9773 ± 0.0165 | 0.0302 ± 0.0042 | 0.0516 ± 0.0085 | 0.9724 ± 0.0085 |
| Binary+ternary train → ternary test | isothermal (P+y) | 1.4589 ± 0.6041 kPa | 2.1139 ± 0.7701 kPa | 0.9850 ± 0.0096 | 0.0166 ± 0.0045 | 0.0244 ± 0.0057 | 0.9896 ± 0.0067 |
| Binary+ternary train → ternary test | isobaric (T+y) | 1.4720 ± 0.6904 K | 1.9975 ± 1.1673 K | 0.9763 ± 0.0371 | 0.0313 ± 0.0194 | 0.0516 ± 0.0395 | 0.9211 ± 0.0823 |

Machine-readable source: `results/multiview/predictive/representation_performance.csv`.
