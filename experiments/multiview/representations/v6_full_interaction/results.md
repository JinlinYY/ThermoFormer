# v6_full_interaction results

Status: completed Table-1-style five-seed evaluation.

| Evaluation setting | Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² |
|---|---|---:|---:|---:|---:|---:|---:|
| Binary train → binary test | isothermal (P+y) | 10.0465 ± 5.9190 kPa | 20.6507 ± 9.7903 kPa | 0.9687 ± 0.0222 | 0.0279 ± 0.0043 | 0.0475 ± 0.0111 | 0.9781 ± 0.0098 |
| Binary train → binary test | isobaric (T+y) | 2.8447 ± 0.4011 K | 4.7527 ± 0.9970 K | 0.9725 ± 0.0160 | 0.0315 ± 0.0063 | 0.0572 ± 0.0137 | 0.9655 ± 0.0158 |
| Binary+ternary train → binary test | isothermal (P+y) | 7.7115 ± 2.5628 kPa | 15.7985 ± 4.4817 kPa | 0.9821 ± 0.0056 | 0.0253 ± 0.0049 | 0.0448 ± 0.0125 | 0.9802 ± 0.0102 |
| Binary+ternary train → binary test | isobaric (T+y) | 2.7448 ± 0.4355 K | 4.7575 ± 1.0392 K | 0.9723 ± 0.0162 | 0.0312 ± 0.0040 | 0.0563 ± 0.0115 | 0.9669 ± 0.0130 |
| Binary+ternary train → ternary test | isothermal (P+y) | 2.0972 ± 0.4598 kPa | 2.6514 ± 0.6928 kPa | 0.9777 ± 0.0134 | 0.0119 ± 0.0042 | 0.0171 ± 0.0051 | 0.9949 ± 0.0034 |
| Binary+ternary train → ternary test | isobaric (T+y) | 2.2121 ± 0.6019 K | 2.8255 ± 0.8824 K | 0.9634 ± 0.0359 | 0.0348 ± 0.0163 | 0.0572 ± 0.0347 | 0.9125 ± 0.0863 |

Machine-readable source: `results/multiview/predictive/representation_performance.csv`.
