# C1 fugacity-equilibrium fine-tuning (5 seeds)

Protocol: `state_composition_interpolation`; seeds: `0, 1, 2, 3, 4`; physics fine-tuning: `10` epoch(s); checkpoint selection: validation only.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 2.496679 ± 0.171314 | 6.579951 ± 0.866752 | 0.992963 ± 0.001862 | 1.612711 ± 0.201174 | 5.373341 ± 0.832512 | 0.995282 ± 0.001418 |
| y, isothermal | 0.012275 ± 0.001114 | 0.017404 ± 0.001868 | 0.995927 ± 0.000900 | 0.009550 ± 0.001017 | 0.014155 ± 0.001391 | 0.997310 ± 0.000531 |
| T, isobaric | 0.972140 ± 0.099470 | 1.365041 ± 0.089105 | 0.997200 ± 0.000364 | 0.578311 ± 0.035773 | 0.856707 ± 0.057297 | 0.998897 ± 0.000152 |
| y, isobaric | 0.019494 ± 0.001028 | 0.035790 ± 0.000971 | 0.982144 ± 0.000977 | 0.016618 ± 0.000890 | 0.033133 ± 0.000728 | 0.984700 ± 0.000671 |

Validation selected Stage 2 for **5/5** seeds and Stage 1 for **0/5** seeds.
Teacher-forced fugacity residual: Stage 1 `0.00125538 ± 0.000117026`; Stage 2 `0.000802377 ± 7.80608e-05`.

## Validation-selected final test metrics

Each seed contributes the checkpoint selected on validation; test data are not used for selection.

| task output | MAE | RMSE | R² | solver failure | nonphysical | coverage |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 1.612711 ± 0.201174 | 5.373341 ± 0.832512 | 0.995282 ± 0.001418 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isothermal | 0.009550 ± 0.001017 | 0.014155 ± 0.001391 | 0.997310 ± 0.000531 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| T, isobaric | 0.578311 ± 0.035773 | 0.856707 ± 0.057297 | 0.998897 ± 0.000152 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isobaric | 0.016618 ± 0.000890 | 0.033133 ± 0.000728 | 0.984700 ± 0.000671 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |

## Fine-tuned parameters

Total parameters: `2,015,043`; fine-tuned: `260,355` (`12.92%`).

| parameter group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2.00e-05 |
| vapor_pressure | 37,442 | 1.00e-05 |
| film | 111,744 | 5.00e-06 |
| mixture_token | 192 | 5.00e-06 |
