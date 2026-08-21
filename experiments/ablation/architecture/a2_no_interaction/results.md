# A2 No multicomponent interaction

Status: **completed formal five-seed ablation**.

| Benchmark | Direction | Observable | System-wise MAE (mean ± SD) | Seeds |
|---|---|---|---:|---:|
| binary | isothermal | P | 17.993 ± 1.96 | 5 |
| binary | isothermal | y | 0.080588 ± 0.0187 | 5 |
| binary | isobaric | T | 9.0512 ± 3.54 | 5 |
| binary | isobaric | y | 0.088921 ± 0.0163 | 5 |
| ternary | isothermal | P | 5.0148 ± 1.7 | 4 |
| ternary | isothermal | y | 0.089412 ± 0.0428 | 4 |
| ternary | isobaric | T | 7.2807 ± 4.36 | 4 |
| ternary | isobaric | y | 0.057332 ± 0.0154 | 4 |
| unseen_mixture | isothermal | P | 17.073 ± 1.55 | 5 |
| unseen_mixture | isothermal | y | 0.081232 ± 0.0197 | 5 |
| unseen_mixture | isobaric | T | 8.8704 ± 3.57 | 5 |
| unseen_mixture | isobaric | y | 0.086586 ± 0.016 | 5 |
| unseen_component | isothermal | P | 44.664 ± 2.14 | 5 |
| unseen_component | isothermal | y | 0.092855 ± 0.0138 | 5 |
| unseen_component | isobaric | T | 32.691 ± 1.67 | 5 |
| unseen_component | isobaric | y | 0.1132 ± 0.00261 | 5 |
| binary_to_ternary | isothermal | P | 6.9634 ± 3.58 | 5 |
| binary_to_ternary | isothermal | y | 0.062191 ± 0.0203 | 5 |
| binary_to_ternary | isobaric | T | 3.7965 ± 1.93 | 5 |
| binary_to_ternary | isobaric | y | 0.073666 ± 0.0228 | 5 |

Full machine-readable results: `results/ablation/architecture.csv` and `results/ablation/physical_consistency.csv`.
