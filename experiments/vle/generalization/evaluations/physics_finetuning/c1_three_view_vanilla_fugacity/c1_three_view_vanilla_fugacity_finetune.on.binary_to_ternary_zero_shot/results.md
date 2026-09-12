# C1 fugacity-equilibrium fine-tuning (5 seeds)

Protocol: `binary_to_ternary_zero_shot`; seeds: `0, 1, 2, 3, 4`; physics fine-tuning: `10` epoch(s); checkpoint selection: validation only.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 1.792807 ± 0.469788 | 2.182744 ± 0.519599 | 0.970703 ± 0.019437 | 1.649787 ± 0.356353 | 2.123899 ± 0.414283 | 0.975238 ± 0.013560 |
| y, isothermal | 0.014905 ± 0.002265 | 0.020560 ± 0.002023 | 0.991351 ± 0.003398 | 0.013143 ± 0.003746 | 0.019281 ± 0.002656 | 0.991970 ± 0.004686 |
| T, isobaric | 1.966343 ± 0.787898 | 2.576824 ± 1.084569 | 0.989344 ± 0.010663 | 2.003688 ± 0.985363 | 2.663892 ± 1.300901 | 0.987934 ± 0.012608 |
| y, isobaric | 0.072155 ± 0.015859 | 0.110086 ± 0.013295 | 0.771732 ± 0.058705 | 0.071465 ± 0.016821 | 0.109527 ± 0.013831 | 0.774020 ± 0.059426 |

Validation selected Stage 2 for **4/5** seeds and Stage 1 for **1/5** seeds.
Teacher-forced fugacity residual: Stage 1 `0.00756844 ± 0.00140036`; Stage 2 `0.00756292 ± 0.00160445`.

## Validation-selected final test metrics

Each seed contributes the checkpoint selected on validation; test data are not used for selection.

| task output | MAE | RMSE | R² | solver failure | nonphysical | coverage |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 1.620025 ± 0.382669 | 2.087622 ± 0.452993 | 0.975830 ± 0.014109 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isothermal | 0.012895 ± 0.003355 | 0.019000 ± 0.002232 | 0.992212 ± 0.004582 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| T, isobaric | 1.912037 ± 0.894793 | 2.558066 ± 1.179546 | 0.989087 ± 0.011528 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isobaric | 0.071352 ± 0.016667 | 0.109437 ± 0.013733 | 0.774373 ± 0.059344 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |

## Fine-tuned parameters

Total parameters: `2,015,043`; fine-tuned: `260,355` (`12.92%`).

| parameter group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2.00e-05 |
| vapor_pressure | 37,442 | 1.00e-05 |
| film | 111,744 | 5.00e-06 |
| mixture_token | 192 | 5.00e-06 |
