# A1 RDKit descriptors

Status: **completed formal five-seed ablation**.

| Benchmark | Direction | Observable | System-wise MAE (mean ± SD) | Seeds |
|---|---|---|---:|---:|
| binary | isothermal | P | 10.548 ± 3.62 | 5 |
| binary | isothermal | y | 0.033441 ± 0.00346 | 5 |
| binary | isobaric | T | 3.807 ± 0.624 | 5 |
| binary | isobaric | y | 0.039242 ± 0.00359 | 5 |
| ternary | isothermal | P | 3.8745 ± 1.16 | 4 |
| ternary | isothermal | y | 0.023777 ± 0.00342 | 4 |
| ternary | isobaric | T | 2.2984 ± 0.546 | 4 |
| ternary | isobaric | y | 0.037038 ± 0.0272 | 4 |
| unseen_mixture | isothermal | P | 10.116 ± 3.43 | 5 |
| unseen_mixture | isothermal | y | 0.032817 ± 0.00385 | 5 |
| unseen_mixture | isobaric | T | 3.6985 ± 0.57 | 5 |
| unseen_mixture | isobaric | y | 0.039331 ± 0.00471 | 5 |

Full machine-readable results: `results/ablation/architecture.csv` and `results/ablation/physical_consistency.csv`.
