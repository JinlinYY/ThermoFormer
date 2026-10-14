# C1 fugacity-equilibrium fine-tuning (5 seeds)

Protocol: `unseen_component`; seeds: `0, 1, 2, 3, 4`; physics fine-tuning: `10` epoch(s); checkpoint selection: validation only.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 32.869127 ± 11.836031 | 69.179969 ± 17.183456 | 0.478348 ± 0.270741 | 32.856002 ± 11.632502 | 68.929383 ± 16.131647 | 0.484855 ± 0.245795 |
| y, isothermal | 0.105864 ± 0.017631 | 0.170024 ± 0.025016 | 0.766503 ± 0.065913 | 0.105958 ± 0.019352 | 0.169546 ± 0.026996 | 0.767138 ± 0.071296 |
| T, isobaric | 36.559516 ± 1.535684 | 47.120652 ± 1.996195 | 0.453183 ± 0.045057 | 36.675942 ± 0.832604 | 47.185355 ± 1.291343 | 0.452138 ± 0.029584 |
| y, isobaric | 0.119190 ± 0.005380 | 0.166938 ± 0.003995 | 0.789415 ± 0.009982 | 0.118708 ± 0.005974 | 0.166030 ± 0.004862 | 0.791652 ± 0.011982 |

Validation selected Stage 2 for **2/5** seeds and Stage 1 for **3/5** seeds.
Teacher-forced fugacity residual: Stage 1 `7.60215 ± 1.75143`; Stage 2 `7.46014 ± 1.56701`.

## Validation-selected final test metrics

Each seed contributes the checkpoint selected on validation; test data are not used for selection.

| task output | MAE | RMSE | R² | solver failure | nonphysical | coverage |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 32.390449 ± 11.312909 | 68.316313 ± 15.798351 | 0.494479 ± 0.242076 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isothermal | 0.105699 ± 0.017912 | 0.169407 ± 0.025015 | 0.768165 ± 0.066036 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| T, isobaric | 36.445656 ± 1.486010 | 46.990164 ± 1.942452 | 0.456245 ± 0.043806 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isobaric | 0.119061 ± 0.006244 | 0.165904 ± 0.004705 | 0.791977 ± 0.011576 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |

## Fine-tuned parameters

Total parameters: `2,015,043`; fine-tuned: `260,355` (`12.92%`).

| parameter group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2.00e-05 |
| vapor_pressure | 37,442 | 1.00e-05 |
| film | 111,744 | 5.00e-06 |
| mixture_token | 192 | 5.00e-06 |
