# A4 Condition concatenation

Status: **completed formal five-seed ablation**.

| Benchmark | Direction | Observable | System-wise MAE (mean ± SD) | Seeds |
|---|---|---|---:|---:|
| binary | isothermal | P | 27.592 ± 25.2 | 5 |
| binary | isothermal | y | 0.074244 ± 0.033 | 5 |
| binary | isobaric | T | 8.0294 ± 4.39 | 5 |
| binary | isobaric | y | 0.085564 ± 0.0254 | 5 |
| ternary | isothermal | P | 3.7037 ± 0.444 | 4 |
| ternary | isothermal | y | 0.053952 ± 0.00862 | 4 |
| ternary | isobaric | T | 8.1587 ± 4.99 | 4 |
| ternary | isobaric | y | 0.079938 ± 0.0392 | 4 |
| unseen_mixture | isothermal | P | 26.546 ± 25.4 | 5 |
| unseen_mixture | isothermal | y | 0.073793 ± 0.033 | 5 |
| unseen_mixture | isobaric | T | 7.9416 ± 4.15 | 5 |
| unseen_mixture | isobaric | y | 0.085105 ± 0.0254 | 5 |

Full machine-readable results: `results/ablation/architecture.csv` and `results/ablation/physical_consistency.csv`.
