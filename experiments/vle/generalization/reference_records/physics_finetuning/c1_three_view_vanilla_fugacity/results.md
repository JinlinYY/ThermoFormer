# C1 fugacity-equilibrium fine-tuning (5 seeds)

Protocol: `overall_binary_ternary`; seeds: `0, 1, 2, 3, 4`; physics fine-tuning: `10` epoch(s); checkpoint selection: validation only.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 8.204989 ± 3.308622 | 19.018329 ± 7.823497 | 0.969654 ± 0.019383 | 7.621613 ± 3.705912 | 18.211291 ± 8.888451 | 0.972251 ± 0.021806 |
| y, isothermal | 0.026222 ± 0.004596 | 0.045674 ± 0.008894 | 0.979474 ± 0.007333 | 0.024647 ± 0.006357 | 0.044314 ± 0.012051 | 0.980203 ± 0.009862 |
| T, isobaric | 2.512644 ± 0.370953 | 4.145978 ± 0.910616 | 0.978919 ± 0.012083 | 2.398601 ± 0.324137 | 4.202361 ± 0.742409 | 0.978787 ± 0.009841 |
| y, isobaric | 0.030747 ± 0.005083 | 0.054088 ± 0.010236 | 0.968731 ± 0.011814 | 0.029661 ± 0.005693 | 0.053193 ± 0.010783 | 0.969650 ± 0.012380 |

Validation selected Stage 2 for **3/5** seeds and Stage 1 for **2/5** seeds.
Teacher-forced fugacity residual: Stage 1 `0.00923742 ± 0.00390755`; Stage 2 `0.00889811 ± 0.00343954`.

## Validation-selected final test metrics

Each seed contributes the checkpoint selected on validation; test data are not used for selection.

| task output | MAE | RMSE | R² | solver failure | nonphysical | coverage |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 7.747841 ± 3.552033 | 18.175083 ± 8.836911 | 0.972285 ± 0.021808 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isothermal | 0.025054 ± 0.005594 | 0.044365 ± 0.010719 | 0.980354 ± 0.008573 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| T, isobaric | 2.376894 ± 0.325460 | 4.122366 ± 0.831590 | 0.979493 ± 0.010319 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isobaric | 0.029945 ± 0.006004 | 0.053198 ± 0.010742 | 0.969651 ± 0.012326 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |

## Fine-tuned parameters

Total parameters: `2,015,043`; fine-tuned: `260,355` (`12.92%`).

| parameter group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2.00e-05 |
| vapor_pressure | 37,442 | 1.00e-05 |
| film | 111,744 | 5.00e-06 |
| mixture_token | 192 | 5.00e-06 |
