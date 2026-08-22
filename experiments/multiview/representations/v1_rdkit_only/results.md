# v1_rdkit_only results

Status: completed Table-1-style five-seed evaluation.

| Evaluation setting | Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² |
|---|---|---:|---:|---:|---:|---:|---:|
| Binary train → binary test | isothermal (P+y) | 9.1861 ± 4.7614 kPa | 18.8484 ± 8.7083 kPa | 0.9746 ± 0.0155 | 0.0268 ± 0.0029 | 0.0468 ± 0.0106 | 0.9788 ± 0.0093 |
| Binary train → binary test | isobaric (T+y) | 2.7516 ± 0.2931 K | 4.7817 ± 0.7704 K | 0.9729 ± 0.0128 | 0.0304 ± 0.0021 | 0.0534 ± 0.0077 | 0.9707 ± 0.0079 |
| Binary+ternary train → binary test | isothermal (P+y) | 9.4678 ± 4.1070 kPa | 20.3637 ± 9.0130 kPa | 0.9699 ± 0.0187 | 0.0287 ± 0.0024 | 0.0506 ± 0.0085 | 0.9756 ± 0.0078 |
| Binary+ternary train → binary test | isobaric (T+y) | 2.7321 ± 0.3197 K | 4.6286 ± 1.1729 K | 0.9733 ± 0.0182 | 0.0297 ± 0.0029 | 0.0524 ± 0.0096 | 0.9715 ± 0.0099 |
| Binary+ternary train → ternary test | isothermal (P+y) | 1.9444 ± 0.4631 kPa | 2.7920 ± 0.5485 kPa | 0.9754 ± 0.0166 | 0.0220 ± 0.0075 | 0.0302 ± 0.0096 | 0.9834 ± 0.0133 |
| Binary+ternary train → ternary test | isobaric (T+y) | 1.5368 ± 0.6196 K | 1.9780 ± 0.9695 K | 0.9779 ± 0.0327 | 0.0343 ± 0.0173 | 0.0540 ± 0.0349 | 0.9197 ± 0.0791 |

Machine-readable source: `results/multiview/predictive/representation_performance.csv`.
