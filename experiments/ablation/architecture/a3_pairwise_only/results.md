# A3 Pairwise-only interaction

Status: **completed formal five-seed ablation**.

| Benchmark | Direction | Observable | System-wise MAE (mean ± SD) | Seeds |
|---|---|---|---:|---:|
| binary | isothermal | P | 22.431 ± 9.63 | 5 |
| binary | isothermal | y | 0.080783 ± 0.0221 | 5 |
| binary | isobaric | T | 9.9357 ± 4.52 | 5 |
| binary | isobaric | y | 0.091444 ± 0.028 | 5 |
| ternary | isothermal | P | 7.5396 ± 3.05 | 4 |
| ternary | isothermal | y | 0.09614 ± 0.0446 | 4 |
| ternary | isobaric | T | 4.5253 ± 2.12 | 4 |
| ternary | isobaric | y | 0.05975 ± 0.0317 | 4 |
| unseen_mixture | isothermal | P | 21.147 ± 7.91 | 5 |
| unseen_mixture | isothermal | y | 0.081331 ± 0.0229 | 5 |
| unseen_mixture | isobaric | T | 9.6444 ± 4.41 | 5 |
| unseen_mixture | isobaric | y | 0.090161 ± 0.0271 | 5 |
| unseen_component | isothermal | P | 51.907 ± 1.66 | 5 |
| unseen_component | isothermal | y | 0.086226 ± 0.0217 | 5 |
| unseen_component | isobaric | T | 34.42 ± 6.04 | 5 |
| unseen_component | isobaric | y | 0.11241 ± 0.00947 | 5 |
| binary_to_ternary | isothermal | P | 8.3016 ± 5.51 | 5 |
| binary_to_ternary | isothermal | y | 0.069099 ± 0.0551 | 5 |
| binary_to_ternary | isobaric | T | 6.2202 ± 4.71 | 5 |
| binary_to_ternary | isobaric | y | 0.090569 ± 0.0331 | 5 |

Full machine-readable results: `results/ablation/architecture.csv` and `results/ablation/physical_consistency.csv`.
