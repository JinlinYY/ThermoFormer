# C1 fugacity-equilibrium fine-tuning (5 seeds)

Protocol: `state_pressure_low_extrapolation`; seeds: `0, 1, 2, 3, 4`; physics fine-tuning: `10` epoch(s); checkpoint selection: validation only.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 1.301649 ± 0.336615 | 3.855171 ± 1.436177 | 0.987103 ± 0.007880 | 1.151851 ± 0.236179 | 2.951700 ± 0.579252 | 0.992985 ± 0.002455 |
| y, isothermal | 0.019365 ± 0.003790 | 0.030094 ± 0.006282 | 0.991087 ± 0.003463 | 0.015983 ± 0.003898 | 0.024727 ± 0.006217 | 0.993892 ± 0.002858 |
| T, isobaric | 1.003548 ± 0.153605 | 1.281900 ± 0.221617 | 0.995783 ± 0.001360 | 0.847012 ± 0.094040 | 1.186440 ± 0.125740 | 0.996441 ± 0.000695 |
| y, isobaric | 0.018385 ± 0.004536 | 0.026097 ± 0.006301 | 0.992157 ± 0.003450 | 0.016230 ± 0.004148 | 0.023670 ± 0.005149 | 0.993602 ± 0.002589 |

Validation selected Stage 2 for **5/5** seeds and Stage 1 for **0/5** seeds.
Teacher-forced fugacity residual: Stage 1 `0.00248796 ± 0.000918515`; Stage 2 `0.00203046 ± 0.000847243`.

## Validation-selected final test metrics

Each seed contributes the checkpoint selected on validation; test data are not used for selection.

| task output | MAE | RMSE | R² | solver failure | nonphysical | coverage |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 1.151851 ± 0.236179 | 2.951700 ± 0.579252 | 0.992985 ± 0.002455 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isothermal | 0.015983 ± 0.003898 | 0.024727 ± 0.006217 | 0.993892 ± 0.002858 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| T, isobaric | 0.847012 ± 0.094040 | 1.186440 ± 0.125740 | 0.996441 ± 0.000695 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isobaric | 0.016230 ± 0.004148 | 0.023670 ± 0.005149 | 0.993602 ± 0.002589 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |

## Fine-tuned parameters

Total parameters: `2,015,043`; fine-tuned: `260,355` (`12.92%`).

| parameter group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2.00e-05 |
| vapor_pressure | 37,442 | 1.00e-05 |
| film | 111,744 | 5.00e-06 |
| mixture_token | 192 | 5.00e-06 |
