# A6 Direct VLE prediction

Status: **completed formal five-seed ablation**.

| Benchmark | Direction | Observable | System-wise MAE (mean ± SD) | Seeds |
|---|---|---|---:|---:|
| binary | isothermal | P | 30.251 ± 12.2 | 5 |
| binary | isothermal | y | 0.088514 ± 0.0157 | 5 |
| binary | isobaric | T | 15.992 ± 3.86 | 5 |
| binary | isobaric | y | 0.089261 ± 0.00845 | 5 |
| ternary | isothermal | P | 6.9167 ± 1.43 | 4 |
| ternary | isothermal | y | 0.080686 ± 0.0257 | 4 |
| ternary | isobaric | T | 6.8076 ± 1.28 | 4 |
| ternary | isobaric | y | 0.082147 ± 0.0215 | 4 |
| unseen_mixture | isothermal | P | 28.421 ± 10.2 | 5 |
| unseen_mixture | isothermal | y | 0.088334 ± 0.0148 | 5 |
| unseen_mixture | isobaric | T | 15.375 ± 3.77 | 5 |
| unseen_mixture | isobaric | y | 0.088839 ± 0.00639 | 5 |
| unseen_component | isothermal | P | 61.66 ± 3.79 | 5 |
| unseen_component | isothermal | y | 0.11021 ± 0.0046 | 5 |
| unseen_component | isobaric | T | 61.337 ± 2.84 | 5 |
| unseen_component | isobaric | y | 0.11327 ± 0.00672 | 5 |
| binary_to_ternary | isothermal | P | 4.9595 ± 2.47 | 5 |
| binary_to_ternary | isothermal | y | 0.068394 ± 0.0163 | 5 |
| binary_to_ternary | isobaric | T | 10.243 ± 2.68 | 5 |
| binary_to_ternary | isobaric | y | 0.11038 ± 0.0166 | 5 |

Full machine-readable results: `results/ablation/architecture.csv` and `results/ablation/physical_consistency.csv`.
