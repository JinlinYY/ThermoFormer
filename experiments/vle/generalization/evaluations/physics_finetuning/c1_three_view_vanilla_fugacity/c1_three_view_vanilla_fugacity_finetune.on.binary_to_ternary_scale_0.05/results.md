# C1 fugacity-equilibrium fine-tuning (5 seeds)

Protocol: `binary_to_ternary_scale_0.05`; seeds: `0, 1, 2, 3, 4`; physics fine-tuning: `10` epoch(s); checkpoint selection: validation only.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 2.368881 ± 0.806322 | 2.833253 ± 0.815983 | 0.951149 ± 0.035682 | 2.078457 ± 0.922991 | 2.520655 ± 0.816429 | 0.954829 ± 0.044147 |
| y, isothermal | 0.014332 ± 0.004329 | 0.019670 ± 0.004236 | 0.991362 ± 0.005644 | 0.013674 ± 0.004495 | 0.019841 ± 0.004521 | 0.991141 ± 0.005891 |
| T, isobaric | 1.919431 ± 0.524734 | 2.471162 ± 0.628029 | 0.991509 ± 0.006618 | 1.831853 ± 0.503883 | 2.526625 ± 0.770295 | 0.991080 ± 0.006757 |
| y, isobaric | 0.073940 ± 0.016431 | 0.111458 ± 0.013147 | 0.765521 ± 0.062091 | 0.073184 ± 0.017902 | 0.111005 ± 0.014000 | 0.767125 ± 0.064715 |

Validation selected Stage 2 for **3/5** seeds and Stage 1 for **2/5** seeds.
Teacher-forced fugacity residual: Stage 1 `0.00785762 ± 0.0010374`; Stage 2 `0.00763882 ± 0.00101219`.

## Validation-selected final test metrics

Each seed contributes the checkpoint selected on validation; test data are not used for selection.

| task output | MAE | RMSE | R² | solver failure | nonphysical | coverage |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 2.152320 ± 0.894266 | 2.619275 ± 0.935833 | 0.953304 ± 0.038383 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isothermal | 0.014449 ± 0.004196 | 0.020218 ± 0.004026 | 0.991038 ± 0.005308 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| T, isobaric | 1.974670 ± 0.517524 | 2.673031 ± 0.664628 | 0.990259 ± 0.007021 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isobaric | 0.074303 ± 0.016908 | 0.111765 ± 0.013498 | 0.764226 ± 0.062922 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |

## Fine-tuned parameters

Total parameters: `2,015,043`; fine-tuned: `260,355` (`12.92%`).

| parameter group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2.00e-05 |
| vapor_pressure | 37,442 | 1.00e-05 |
| film | 111,744 | 5.00e-06 |
| mixture_token | 192 | 5.00e-06 |
