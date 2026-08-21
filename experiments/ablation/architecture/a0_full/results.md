# A0 Full ThermoFormer

Status: **immutable reference reused from completed formal runs**.

| Benchmark | Direction | Observable | System-wise MAE (mean ± SD) | Seeds |
|---|---|---|---:|---:|
| binary | isothermal | P | 17.837 ± 5.49 | 5 |
| binary | isothermal | y | 0.071542 ± 0.0183 | 5 |
| binary | isobaric | T | 6.5408 ± 1.87 | 5 |
| binary | isobaric | y | 0.068676 ± 0.0146 | 5 |
| ternary | isothermal | P | 3.9798 ± 2.16 | 4 |
| ternary | isothermal | y | 0.055909 ± 0.019 | 4 |
| ternary | isobaric | T | 2.8296 ± 0.772 | 4 |
| ternary | isobaric | y | 0.056131 ± 0.0228 | 4 |
| unseen_mixture | isothermal | P | 16.952 ± 5.41 | 5 |
| unseen_mixture | isothermal | y | 0.070327 ± 0.0178 | 5 |
| unseen_mixture | isobaric | T | 6.3074 ± 1.82 | 5 |
| unseen_mixture | isobaric | y | 0.068128 ± 0.0136 | 5 |
| unseen_component | isothermal | P | 48.598 ± 4.87 | 5 |
| unseen_component | isothermal | y | 0.083815 ± 0.0133 | 5 |
| unseen_component | isobaric | T | 32.934 ± 4.14 | 5 |
| unseen_component | isobaric | y | 0.11626 ± 0.0143 | 5 |
| binary_to_ternary | isothermal | P | 5.1804 ± 2.8 | 5 |
| binary_to_ternary | isothermal | y | 0.033788 ± 0.00663 | 5 |
| binary_to_ternary | isobaric | T | 5.2496 ± 1.65 | 5 |
| binary_to_ternary | isobaric | y | 0.074314 ± 0.0142 | 5 |

Full machine-readable results: `results/ablation/architecture.csv` and `results/ablation/physical_consistency.csv`.
