# C1 fugacity-equilibrium fine-tuning (5 seeds)

Protocol: `state_composition_edge_extrapolation`; seeds: `0, 1, 2, 3, 4`; physics fine-tuning: `10` epoch(s); checkpoint selection: validation only.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 2.745827 ± 0.291468 | 7.045419 ± 1.063269 | 0.992086 ± 0.002393 | 1.906393 ± 0.205481 | 4.980722 ± 0.868833 | 0.996021 ± 0.001384 |
| y, isothermal | 0.009022 ± 0.001492 | 0.017718 ± 0.003449 | 0.998168 ± 0.000773 | 0.007516 ± 0.000650 | 0.014347 ± 0.001155 | 0.998828 ± 0.000193 |
| T, isobaric | 1.249929 ± 0.110388 | 1.701305 ± 0.139912 | 0.996947 ± 0.000489 | 0.920241 ± 0.097582 | 1.370414 ± 0.123787 | 0.998017 ± 0.000346 |
| y, isobaric | 0.015898 ± 0.000373 | 0.039265 ± 0.000643 | 0.990756 ± 0.000301 | 0.015158 ± 0.000316 | 0.038483 ± 0.000431 | 0.991122 ± 0.000198 |

Validation selected Stage 2 for **5/5** seeds and Stage 1 for **0/5** seeds.
Teacher-forced fugacity residual: Stage 1 `0.00192147 ± 0.000219582`; Stage 2 `0.00137176 ± 0.00018007`.

## Validation-selected final test metrics

Each seed contributes the checkpoint selected on validation; test data are not used for selection.

| task output | MAE | RMSE | R² | solver failure | nonphysical | coverage |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 1.906393 ± 0.205481 | 4.980722 ± 0.868833 | 0.996021 ± 0.001384 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isothermal | 0.007516 ± 0.000650 | 0.014347 ± 0.001155 | 0.998828 ± 0.000193 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| T, isobaric | 0.920241 ± 0.097582 | 1.370414 ± 0.123787 | 0.998017 ± 0.000346 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isobaric | 0.015158 ± 0.000316 | 0.038483 ± 0.000431 | 0.991122 ± 0.000198 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |

## Fine-tuned parameters

Total parameters: `2,015,043`; fine-tuned: `260,355` (`12.92%`).

| parameter group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2.00e-05 |
| vapor_pressure | 37,442 | 1.00e-05 |
| film | 111,744 | 5.00e-06 |
| mixture_token | 192 | 5.00e-06 |
