# C1 fugacity-equilibrium fine-tuning

Protocol: `overall_binary_ternary`; seed: `0`; checkpoint selection: validation only.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 5.737222 | 16.257956 | 0.968370 | 5.369718 | 14.488111 | 0.974881 |
| y, isothermal | 0.030446 | 0.052214 | 0.973879 | 0.029451 | 0.052778 | 0.973312 |
| T, isobaric | 2.624327 | 4.282521 | 0.984785 | 2.583149 | 4.489982 | 0.983276 |
| y, isobaric | 0.031279 | 0.051688 | 0.972479 | 0.030751 | 0.050542 | 0.973686 |

| diagnostic | Stage 1 | Stage 2 |
|---|---:|---:|
| solver failure rate | 0 | 0 |
| nonphysical rate | 0 | 0 |
| teacher-forced fugacity-equilibrium residual | 0.00784219 | 0.00820832 |

Thermodynamic loss weights: `teacher_forced_fugacity=1`.

Total parameters: **2,015,043**.
Fine-tuned parameters: **260,355** (**12.921%**).

| unfrozen group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2e-05 |
| vapor_pressure | 37,442 | 1e-05 |
| film | 111,744 | 5e-06 |
| mixture_token | 192 | 5e-06 |

Stage 1 validation loss: `0.017084085`.
Stage 2 validation loss: `0.015736597`.
Selected final checkpoint: **stage2**.

The test partition was evaluated only after validation-only checkpoint selection.
