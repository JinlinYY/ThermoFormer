# C1 fugacity + pure-vapor-pressure-anchor fine-tuning

Protocol: `overall_binary_ternary`; seed: `0`; checkpoint selection: validation only.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 5.737222 | 16.257956 | 0.968370 | 5.367646 | 14.444393 | 0.975033 |
| y, isothermal | 0.030446 | 0.052214 | 0.973879 | 0.029520 | 0.052709 | 0.973381 |
| T, isobaric | 2.624327 | 4.282521 | 0.984785 | 2.583207 | 4.516979 | 0.983074 |
| y, isobaric | 0.031279 | 0.051688 | 0.972479 | 0.030810 | 0.050624 | 0.973600 |

| diagnostic | Stage 1 | Stage 2 |
|---|---:|---:|
| solver failure rate | 0 | 0 |
| nonphysical rate | 0 | 0 |
| pure-vapor-pressure anchor loss | 0.0156017 | 0.0132736 |
| teacher-forced fugacity-equilibrium residual | 0.00784219 | 0.008313 |

Thermodynamic loss weights: `additional_pure_vapor_pressure_anchor=0.5`, `boundary=0`, `continuity=0`, `solver=0`, `teacher_forced_fugacity=1`.

## Comparison with fugacity-only Stage 2

| task output | metric | Fugacity only | Fugacity + anchor | delta |
|---|---|---:|---:|---:|
| P, isothermal | MAE | 5.369718 | 5.367646 | -0.002073 |
| P, isothermal | RMSE | 14.488111 | 14.444393 | -0.043719 |
| P, isothermal | R² | 0.974881 | 0.975033 | +0.000151 |
| y, isothermal | MAE | 0.029451 | 0.029520 | +0.000069 |
| y, isothermal | RMSE | 0.052778 | 0.052709 | -0.000069 |
| y, isothermal | R² | 0.973312 | 0.973381 | +0.000070 |
| T, isobaric | MAE | 2.583149 | 2.583207 | +0.000058 |
| T, isobaric | RMSE | 4.489982 | 4.516979 | +0.026997 |
| T, isobaric | R² | 0.983276 | 0.983074 | -0.000202 |
| y, isobaric | MAE | 0.030751 | 0.030810 | +0.000059 |
| y, isobaric | RMSE | 0.050542 | 0.050624 | +0.000082 |
| y, isobaric | R² | 0.973686 | 0.973600 | -0.000086 |

Only 5 of 12 predictive metrics improve. The seed-0 effect is mixed, so the stronger anchor is not an overall predictive improvement over fugacity-only fine-tuning.
Reference stage-comparison SHA-256: `40b335e56f722ebea1b74d7d89e7a1573af244fb91b2145f472f00e6a6292cfb`.

Total parameters: **2,015,043**.
Fine-tuned parameters: **260,355** (**12.921%**).

| unfrozen group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2e-05 |
| vapor_pressure | 37,442 | 1e-05 |
| film | 111,744 | 5e-06 |
| mixture_token | 192 | 5e-06 |

Stage 1 validation loss: `0.017084085`.
Stage 2 validation loss: `0.015712205`.
Selected final checkpoint: **stage2**.

The test partition was evaluated only after validation-only checkpoint selection.
