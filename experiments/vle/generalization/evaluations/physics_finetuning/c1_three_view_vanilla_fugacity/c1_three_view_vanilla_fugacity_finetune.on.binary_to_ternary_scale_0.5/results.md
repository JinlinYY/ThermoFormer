# C1 fugacity-equilibrium fine-tuning (5 seeds)

Protocol: `binary_to_ternary_scale_0.5`; seeds: `0, 1, 2, 3, 4`; physics fine-tuning: `10` epoch(s); checkpoint selection: validation only.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 1.642552 ± 0.601260 | 2.138237 ± 0.868594 | 0.977919 ± 0.010589 | 1.511816 ± 0.368224 | 2.001081 ± 0.245249 | 0.977823 ± 0.010338 |
| y, isothermal | 0.012308 ± 0.003014 | 0.018094 ± 0.003146 | 0.993479 ± 0.002359 | 0.011593 ± 0.003019 | 0.017467 ± 0.002666 | 0.993624 ± 0.002987 |
| T, isobaric | 1.815511 ± 0.769945 | 2.444149 ± 1.045628 | 0.990549 ± 0.008981 | 1.765499 ± 0.793150 | 2.387929 ± 1.096188 | 0.990750 ± 0.009014 |
| y, isobaric | 0.071688 ± 0.015818 | 0.110517 ± 0.012408 | 0.769580 ± 0.058072 | 0.071888 ± 0.015933 | 0.110896 ± 0.012756 | 0.767722 ± 0.060533 |

Validation selected Stage 2 for **4/5** seeds and Stage 1 for **1/5** seeds.
Teacher-forced fugacity residual: Stage 1 `0.00745066 ± 0.00104448`; Stage 2 `0.00732189 ± 0.0011874`.

## Validation-selected final test metrics

Each seed contributes the checkpoint selected on validation; test data are not used for selection.

| task output | MAE | RMSE | R² | solver failure | nonphysical | coverage |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 1.302735 ± 0.503252 | 1.807832 ± 0.568511 | 0.982438 ± 0.011186 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isothermal | 0.011163 ± 0.002822 | 0.016929 ± 0.002938 | 0.994200 ± 0.002285 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| T, isobaric | 1.813704 ± 0.855209 | 2.434138 ± 1.147956 | 0.990205 ± 0.009787 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |
| y, isobaric | 0.072062 ± 0.015921 | 0.110941 ± 0.012739 | 0.767587 ± 0.060335 | 0.000000 ± 0.000000 | 0.000000 ± 0.000000 | 1.000000 ± 0.000000 |

## Fine-tuned parameters

Total parameters: `2,015,043`; fine-tuned: `260,355` (`12.92%`).

| parameter group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2.00e-05 |
| vapor_pressure | 37,442 | 1.00e-05 |
| film | 111,744 | 5.00e-06 |
| mixture_token | 192 | 5.00e-06 |
