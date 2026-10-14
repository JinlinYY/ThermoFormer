# C1 fugacity-equilibrium fine-tuning (5 seeds)

Protocol: `binary_to_ternary_scale_0.25`; seeds: `0, 1, 2, 3, 4`; physics fine-tuning: `10` epoch(s); checkpoint selection: validation only.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 1.953259 ± 0.557640 | 2.509560 ± 0.722372 | 0.960816 ± 0.020812 | 1.856631 ± 0.678895 | 2.414026 ± 0.630103 | 0.962348 ± 0.024028 |
| y, isothermal | 0.014372 ± 0.003256 | 0.020538 ± 0.003806 | 0.990981 ± 0.004727 | 0.014352 ± 0.002207 | 0.020237 ± 0.002385 | 0.991571 ± 0.003502 |
| T, isobaric | 1.744296 ± 1.136666 | 2.234753 ± 1.246857 | 0.990742 ± 0.012411 | 1.761081 ± 0.968837 | 2.384462 ± 1.173187 | 0.990457 ± 0.009738 |
| y, isobaric | 0.071198 ± 0.016297 | 0.110449 ± 0.012617 | 0.770018 ± 0.057949 | 0.072000 ± 0.016554 | 0.110628 ± 0.013197 | 0.768651 ± 0.061907 |

Validation selected Stage 2 for **3/5** seeds and Stage 1 for **2/5** seeds.
Teacher-forced fugacity residual: Stage 1 `0.00745538 ± 0.00150456`; Stage 2 `0.00750408 ± 0.00127116`.

## Validation-selected final test metrics

Each seed contributes the checkpoint selected on validation; test data are not used for selection.

| task output | MAE | RMSE | R² | solver failure | nonphysical | coverage |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 1.796015 ± 0.609550 | 2.386786 ± 0.648242 | 0.964188 ± 0.020507 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isothermal | 0.014000 ± 0.002601 | 0.020034 ± 0.002712 | 0.991507 ± 0.004417 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| T, isobaric | 1.861976 ± 1.181547 | 2.474975 ± 1.366263 | 0.988987 ± 0.012589 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isobaric | 0.072286 ± 0.016503 | 0.110897 ± 0.013162 | 0.767966 ± 0.060438 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |

## Fine-tuned parameters

Total parameters: `2,015,043`; fine-tuned: `260,355` (`12.92%`).

| parameter group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2.00e-05 |
| vapor_pressure | 37,442 | 1.00e-05 |
| film | 111,744 | 5.00e-06 |
| mixture_token | 192 | 5.00e-06 |
