# C1 fugacity-equilibrium fine-tuning (5 seeds)

Protocol: `state_pressure_high_extrapolation`; seeds: `0, 1, 2, 3, 4`; physics fine-tuning: `10` epoch(s); checkpoint selection: validation only.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 6.169106 ± 1.469100 | 13.104010 ± 3.617617 | 0.988462 ± 0.005710 | 5.962095 ± 1.349932 | 13.006821 ± 3.062358 | 0.988811 ± 0.005453 |
| y, isothermal | 0.014098 ± 0.003873 | 0.023305 ± 0.006917 | 0.995019 ± 0.002667 | 0.012845 ± 0.004193 | 0.023749 ± 0.009680 | 0.994526 ± 0.004712 |
| T, isobaric | 1.124666 ± 0.317355 | 1.491888 ± 0.383328 | 0.992460 ± 0.003993 | 0.944495 ± 0.191167 | 1.313490 ± 0.244029 | 0.994295 ± 0.002216 |
| y, isobaric | 0.022866 ± 0.006264 | 0.032978 ± 0.008937 | 0.985530 ± 0.008410 | 0.020217 ± 0.005185 | 0.029292 ± 0.005832 | 0.988876 ± 0.004790 |

Validation selected Stage 2 for **5/5** seeds and Stage 1 for **0/5** seeds.
Teacher-forced fugacity residual: Stage 1 `0.00152247 ± 0.000710249`; Stage 2 `0.0013245 ± 0.000761837`.

## Validation-selected final test metrics

Each seed contributes the checkpoint selected on validation; test data are not used for selection.

| task output | MAE | RMSE | R² | solver failure | nonphysical | coverage |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 5.962095 ± 1.349932 | 13.006821 ± 3.062358 | 0.988811 ± 0.005453 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isothermal | 0.012845 ± 0.004193 | 0.023749 ± 0.009680 | 0.994526 ± 0.004712 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| T, isobaric | 0.944495 ± 0.191167 | 1.313490 ± 0.244029 | 0.994295 ± 0.002216 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isobaric | 0.020217 ± 0.005185 | 0.029292 ± 0.005832 | 0.988876 ± 0.004790 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |

## Fine-tuned parameters

Total parameters: `2,015,043`; fine-tuned: `260,355` (`12.92%`).

| parameter group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2.00e-05 |
| vapor_pressure | 37,442 | 1.00e-05 |
| film | 111,744 | 5.00e-06 |
| mixture_token | 192 | 5.00e-06 |
