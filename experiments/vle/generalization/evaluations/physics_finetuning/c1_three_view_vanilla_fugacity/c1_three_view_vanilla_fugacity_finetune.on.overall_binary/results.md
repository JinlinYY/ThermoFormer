# C1 fugacity-equilibrium fine-tuning (5 seeds)

Protocol: `overall_binary`; seeds: `0, 1, 2, 3, 4`; physics fine-tuning: `10` epoch(s); checkpoint selection: validation only.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 10.047403 ± 5.240079 | 21.790984 ± 10.924291 | 0.964945 ± 0.022850 | 8.606112 ± 5.392557 | 19.659125 ± 12.192490 | 0.970688 ± 0.026884 |
| y, isothermal | 0.028044 ± 0.005295 | 0.048695 ± 0.011116 | 0.977027 ± 0.010140 | 0.026198 ± 0.005582 | 0.047309 ± 0.012231 | 0.978095 ± 0.010618 |
| T, isobaric | 2.742328 ± 0.476346 | 4.560601 ± 0.528801 | 0.976516 ± 0.005424 | 2.407344 ± 0.221485 | 4.265846 ± 0.505625 | 0.978850 ± 0.007886 |
| y, isobaric | 0.029072 ± 0.004705 | 0.050930 ± 0.006705 | 0.973421 ± 0.006359 | 0.027950 ± 0.005154 | 0.049639 ± 0.006152 | 0.974785 ± 0.005602 |

Validation selected Stage 2 for **4/5** seeds and Stage 1 for **1/5** seeds.
Teacher-forced fugacity residual: Stage 1 `0.0105685 ± 0.00331003`; Stage 2 `0.00937359 ± 0.00424843`.

## Validation-selected final test metrics

Each seed contributes the checkpoint selected on validation; test data are not used for selection.

| task output | MAE | RMSE | R² | solver failure | nonphysical | coverage |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 8.979321 ± 5.203604 | 20.575643 ± 11.954160 | 0.967526 ± 0.026883 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isothermal | 0.026237 ± 0.005550 | 0.047553 ± 0.011980 | 0.977922 ± 0.010439 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| T, isobaric | 2.445077 ± 0.146457 | 4.292867 ± 0.517941 | 0.978590 ± 0.007893 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isobaric | 0.028435 ± 0.004258 | 0.049855 ± 0.005773 | 0.974600 ± 0.005277 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |

## Fine-tuned parameters

Total parameters: `2,015,043`; fine-tuned: `260,355` (`12.92%`).

| parameter group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2.00e-05 |
| vapor_pressure | 37,442 | 1.00e-05 |
| film | 111,744 | 5.00e-06 |
| mixture_token | 192 | 5.00e-06 |
