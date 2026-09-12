# C1 fugacity-equilibrium fine-tuning (5 seeds)

Protocol: `binary_to_ternary_scale_0.1`; seeds: `0, 1, 2, 3, 4`; physics fine-tuning: `10` epoch(s); checkpoint selection: validation only.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 2.219839 ± 0.838425 | 2.691149 ± 0.973688 | 0.957897 ± 0.030463 | 2.202474 ± 0.676503 | 2.620574 ± 0.619573 | 0.957250 ± 0.027366 |
| y, isothermal | 0.016195 ± 0.005470 | 0.022974 ± 0.005348 | 0.988445 ± 0.006805 | 0.012982 ± 0.003933 | 0.018780 ± 0.003980 | 0.992047 ± 0.005469 |
| T, isobaric | 2.254457 ± 0.537461 | 2.845362 ± 0.644575 | 0.989226 ± 0.007207 | 1.980772 ± 0.666125 | 2.515252 ± 0.791050 | 0.990974 ± 0.007383 |
| y, isobaric | 0.072249 ± 0.015317 | 0.110432 ± 0.012393 | 0.770214 ± 0.057467 | 0.072444 ± 0.016491 | 0.110734 ± 0.012990 | 0.768799 ± 0.059497 |

Validation selected Stage 2 for **3/5** seeds and Stage 1 for **2/5** seeds.
Teacher-forced fugacity residual: Stage 1 `0.00778534 ± 0.0012353`; Stage 2 `0.00746122 ± 0.00107032`.

## Validation-selected final test metrics

Each seed contributes the checkpoint selected on validation; test data are not used for selection.

| task output | MAE | RMSE | R² | solver failure | nonphysical | coverage |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 1.927786 ± 0.601842 | 2.353534 ± 0.693307 | 0.968348 ± 0.017890 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isothermal | 0.013601 ± 0.004404 | 0.019565 ± 0.004559 | 0.991023 ± 0.007173 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| T, isobaric | 2.045210 ± 0.539788 | 2.612656 ± 0.645654 | 0.990632 ± 0.007184 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isobaric | 0.072448 ± 0.016529 | 0.110602 ± 0.013220 | 0.769496 ± 0.059405 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |

## Fine-tuned parameters

Total parameters: `2,015,043`; fine-tuned: `260,355` (`12.92%`).

| parameter group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2.00e-05 |
| vapor_pressure | 37,442 | 1.00e-05 |
| film | 111,744 | 5.00e-06 |
| mixture_token | 192 | 5.00e-06 |
