# C1 fugacity-equilibrium fine-tuning (5 seeds)

Protocol: `state_temperature_low_extrapolation`; seeds: `0, 1, 2, 3, 4`; physics fine-tuning: `10` epoch(s); checkpoint selection: validation only.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 2.433652 ± 0.567323 | 5.106324 ± 1.659418 | 0.994339 ± 0.002983 | 2.049237 ± 0.305195 | 4.116965 ± 1.061480 | 0.996426 ± 0.001821 |
| y, isothermal | 0.014363 ± 0.001720 | 0.021844 ± 0.002891 | 0.995383 ± 0.001235 | 0.013746 ± 0.000988 | 0.020613 ± 0.001378 | 0.995931 ± 0.000533 |
| T, isobaric | 1.302764 ± 0.180267 | 2.182077 ± 0.400129 | 0.990849 ± 0.003157 | 1.299725 ± 0.353062 | 2.922194 ± 1.606928 | 0.980152 ± 0.020786 |
| y, isobaric | 0.011776 ± 0.000670 | 0.024542 ± 0.001290 | 0.995825 ± 0.000438 | 0.011020 ± 0.000580 | 0.023096 ± 0.001511 | 0.996298 ± 0.000498 |

Validation selected Stage 2 for **3/5** seeds and Stage 1 for **2/5** seeds.
Teacher-forced fugacity residual: Stage 1 `0.00186642 ± 0.000337454`; Stage 2 `0.0018344 ± 0.000477647`.

## Validation-selected final test metrics

Each seed contributes the checkpoint selected on validation; test data are not used for selection.

| task output | MAE | RMSE | R² | solver failure | nonphysical | coverage |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 2.050831 ± 0.582625 | 3.686019 ± 1.311212 | 0.997005 ± 0.002247 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isothermal | 0.013638 ± 0.001181 | 0.020420 ± 0.001618 | 0.996001 ± 0.000624 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| T, isobaric | 1.161874 ± 0.161780 | 2.094474 ± 0.399628 | 0.991551 ± 0.003266 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isobaric | 0.011248 ± 0.000632 | 0.023993 ± 0.001897 | 0.995998 ± 0.000625 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |

## Fine-tuned parameters

Total parameters: `2,015,043`; fine-tuned: `260,355` (`12.92%`).

| parameter group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2.00e-05 |
| vapor_pressure | 37,442 | 1.00e-05 |
| film | 111,744 | 5.00e-06 |
| mixture_token | 192 | 5.00e-06 |
