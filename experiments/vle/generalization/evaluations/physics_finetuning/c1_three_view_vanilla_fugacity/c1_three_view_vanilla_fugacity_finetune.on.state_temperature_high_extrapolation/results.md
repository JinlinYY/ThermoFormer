# C1 fugacity-equilibrium fine-tuning (5 seeds)

Protocol: `state_temperature_high_extrapolation`; seeds: `0, 1, 2, 3, 4`; physics fine-tuning: `10` epoch(s); checkpoint selection: validation only.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 5.979184 ± 1.243920 | 13.319363 ± 3.627835 | 0.987264 ± 0.006251 | 5.826721 ± 0.419791 | 13.477425 ± 0.593204 | 0.987672 ± 0.001075 |
| y, isothermal | 0.013853 ± 0.001518 | 0.021840 ± 0.002718 | 0.994535 ± 0.001357 | 0.012003 ± 0.001089 | 0.019442 ± 0.002021 | 0.995685 ± 0.000891 |
| T, isobaric | 1.340233 ± 0.065520 | 1.979648 ± 0.091590 | 0.995627 ± 0.000407 | 1.113093 ± 0.059755 | 1.765311 ± 0.093577 | 0.996521 ± 0.000369 |
| y, isobaric | 0.023385 ± 0.001220 | 0.041514 ± 0.001367 | 0.983582 ± 0.001087 | 0.021854 ± 0.001205 | 0.039861 ± 0.001176 | 0.984866 ± 0.000896 |

Validation selected Stage 2 for **5/5** seeds and Stage 1 for **0/5** seeds.
Teacher-forced fugacity residual: Stage 1 `0.00184434 ± 0.000185407`; Stage 2 `0.00146303 ± 0.000137622`.

## Validation-selected final test metrics

Each seed contributes the checkpoint selected on validation; test data are not used for selection.

| task output | MAE | RMSE | R² | solver failure | nonphysical | coverage |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 5.826721 ± 0.419791 | 13.477425 ± 0.593204 | 0.987672 ± 0.001075 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isothermal | 0.012003 ± 0.001089 | 0.019442 ± 0.002021 | 0.995685 ± 0.000891 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| T, isobaric | 1.113093 ± 0.059755 | 1.765311 ± 0.093577 | 0.996521 ± 0.000369 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isobaric | 0.021854 ± 0.001205 | 0.039861 ± 0.001176 | 0.984866 ± 0.000896 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |

## Fine-tuned parameters

Total parameters: `2,015,043`; fine-tuned: `260,355` (`12.92%`).

| parameter group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2.00e-05 |
| vapor_pressure | 37,442 | 1.00e-05 |
| film | 111,744 | 5.00e-06 |
| mixture_token | 192 | 5.00e-06 |
