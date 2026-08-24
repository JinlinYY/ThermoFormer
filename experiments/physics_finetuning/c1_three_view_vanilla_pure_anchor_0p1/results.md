# C1 pure-vapor-pressure-anchor fine-tuning

Protocol: `overall_binary_ternary`; seed: `0`; checkpoint selection: validation only.

**Exploratory analysis:** this weight was proposed after prior seed-0 test results were inspected and is not independent confirmatory evidence.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 5.737222 | 16.257956 | 0.968370 | 5.373507 | 14.474202 | 0.974930 |
| y, isothermal | 0.030446 | 0.052214 | 0.973879 | 0.029608 | 0.052817 | 0.973272 |
| T, isobaric | 2.624327 | 4.282521 | 0.984785 | 2.583733 | 4.502861 | 0.983179 |
| y, isobaric | 0.031279 | 0.051688 | 0.972479 | 0.030791 | 0.050600 | 0.973626 |

| diagnostic | Stage 1 | Stage 2 |
|---|---:|---:|
| solver failure rate | 0 | 0 |
| nonphysical rate | 0 | 0 |
| pure-vapor-pressure anchor loss | 0.0156017 | 0.0132696 |

Thermodynamic loss weights: `additional_pure_vapor_pressure_anchor=0.1`, `boundary=0`, `continuity=0`, `solver=0`, `teacher_forced_fugacity=0`.

## Comparison with Extra anchor 0.5

| task output | metric | Extra anchor 0.5 | Extra anchor 0.1 | delta |
|---|---|---:|---:|---:|
| P, isothermal | MAE | 5.372313 | 5.373507 | +0.001195 |
| P, isothermal | RMSE | 14.435983 | 14.474202 | +0.038219 |
| P, isothermal | R² | 0.975062 | 0.974930 | -0.000132 |
| y, isothermal | MAE | 0.029663 | 0.029608 | -0.000055 |
| y, isothermal | RMSE | 0.052749 | 0.052817 | +0.000069 |
| y, isothermal | R² | 0.973341 | 0.973272 | -0.000069 |
| T, isobaric | MAE | 2.584539 | 2.583733 | -0.000806 |
| T, isobaric | RMSE | 4.527799 | 4.502861 | -0.024938 |
| T, isobaric | R² | 0.982993 | 0.983179 | +0.000187 |
| y, isobaric | MAE | 0.030850 | 0.030791 | -0.000059 |
| y, isobaric | RMSE | 0.050684 | 0.050600 | -0.000084 |
| y, isobaric | R² | 0.973538 | 0.973626 | +0.000088 |

Only 7 of 12 predictive metrics improve. The seed-0 effect is mixed, so the current setting is not a consistent predictive improvement over its reference.
Reference stage-comparison SHA-256: `a0c5ca55c92d2557ba95b659da2f04bc025b27411ed67a8441528f82fccd355c`.

Total parameters: **2,015,043**.
Fine-tuned parameters: **260,355** (**12.921%**).

| unfrozen group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2e-05 |
| vapor_pressure | 37,442 | 1e-05 |
| film | 111,744 | 5e-06 |
| mixture_token | 192 | 5e-06 |

Stage 1 validation loss: `0.017084085`.
Stage 2 validation loss: `0.01566864`.
Selected final checkpoint: **stage2**.

The test partition was evaluated only after validation-only checkpoint selection.
