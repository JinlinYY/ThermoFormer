# A5 Direct activity decoding

Status: **completed formal five-seed ablation**.

| Benchmark | Direction | Observable | System-wise MAE (mean ± SD) | Seeds |
|---|---|---|---:|---:|
| binary | isothermal | P | 17.833 ± 7.86 | 5 |
| binary | isothermal | y | 0.055237 ± 0.00895 | 5 |
| binary | isobaric | T | 5.7863 ± 1.11 | 5 |
| binary | isobaric | y | 0.055696 ± 0.0125 | 5 |
| ternary | isothermal | P | 5.6362 ± 3.25 | 4 |
| ternary | isothermal | y | 0.042405 ± 0.012 | 4 |
| ternary | isobaric | T | 3.4521 ± 1.38 | 4 |
| ternary | isobaric | y | 0.050153 ± 0.0235 | 4 |
| unseen_mixture | isothermal | P | 16.87 ± 6.66 | 5 |
| unseen_mixture | isothermal | y | 0.054161 ± 0.0078 | 5 |
| unseen_mixture | isobaric | T | 5.6661 ± 1.08 | 5 |
| unseen_mixture | isobaric | y | 0.055859 ± 0.0122 | 5 |

Full machine-readable results: `results/ablation/architecture.csv` and `results/ablation/physical_consistency.csv`.
