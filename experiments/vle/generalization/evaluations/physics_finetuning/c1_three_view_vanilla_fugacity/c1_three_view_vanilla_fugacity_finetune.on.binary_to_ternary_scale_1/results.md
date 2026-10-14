# C1 fugacity-equilibrium fine-tuning (5 seeds)

Protocol: `binary_to_ternary_scale_1`; seeds: `0, 1, 2, 3, 4`; physics fine-tuning: `10` epoch(s); checkpoint selection: validation only.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 1.986345 ± 0.631418 | 2.360239 ± 0.740548 | 0.970845 ± 0.018678 | 1.467856 ± 0.384370 | 1.873325 ± 0.435962 | 0.981811 ± 0.008166 |
| y, isothermal | 0.014378 ± 0.002886 | 0.020165 ± 0.002903 | 0.991749 ± 0.003089 | 0.012830 ± 0.002805 | 0.018747 ± 0.003434 | 0.993005 ± 0.002656 |
| T, isobaric | 1.878906 ± 0.365843 | 2.458851 ± 0.486551 | 0.992038 ± 0.005099 | 1.777779 ± 0.535490 | 2.380429 ± 0.735490 | 0.991752 ± 0.007045 |
| y, isobaric | 0.073226 ± 0.014898 | 0.111225 ± 0.012438 | 0.767013 ± 0.055741 | 0.073554 ± 0.015580 | 0.111209 ± 0.012439 | 0.767414 ± 0.053894 |

Validation selected Stage 2 for **5/5** seeds and Stage 1 for **0/5** seeds.
Teacher-forced fugacity residual: Stage 1 `0.0075488 ± 0.000892213`; Stage 2 `0.00740697 ± 0.00125641`.

## Validation-selected final test metrics

Each seed contributes the checkpoint selected on validation; test data are not used for selection.

| task output | MAE | RMSE | R² | solver failure | nonphysical | coverage |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 1.467856 ± 0.384370 | 1.873325 ± 0.435962 | 0.981811 ± 0.008166 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isothermal | 0.012830 ± 0.002805 | 0.018747 ± 0.003434 | 0.993005 ± 0.002656 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| T, isobaric | 1.777779 ± 0.535490 | 2.380429 ± 0.735490 | 0.991752 ± 0.007045 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isobaric | 0.073554 ± 0.015580 | 0.111209 ± 0.012439 | 0.767414 ± 0.053894 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |

## Fine-tuned parameters

Total parameters: `2,015,043`; fine-tuned: `260,355` (`12.92%`).

| parameter group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2.00e-05 |
| vapor_pressure | 37,442 | 1.00e-05 |
| film | 111,744 | 5.00e-06 |
| mixture_token | 192 | 5.00e-06 |
