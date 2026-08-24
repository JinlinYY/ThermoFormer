# C1 partial physics fine-tuning

Protocol: `overall_binary_ternary`; seed: `0`; checkpoint selection: validation only.

| task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Stage 2 MAE | Stage 2 RMSE | Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 5.737222 | 16.257956 | 0.968370 | 8.050702 | 21.713285 | 0.943581 |
| y, isothermal | 0.030446 | 0.052214 | 0.973879 | 0.037091 | 0.065485 | 0.958913 |
| T, isobaric | 2.624327 | 4.282521 | 0.984785 | 3.159277 | 4.770578 | 0.981120 |
| y, isobaric | 0.031279 | 0.051688 | 0.972479 | 0.035638 | 0.059740 | 0.963236 |

| diagnostic | Stage 1 | Stage 2 |
|---|---:|---:|
| solver failure rate | 0 | 0 |
| nonphysical rate | 0 | 0 |
| continuity residual | 41164.8 | 18311.9 |
| boundary residual | 1.35037e-12 | 8.0481e-13 |
| solver residual | 0.0108199 | 0.014097 |

Total parameters: **2,015,043**.
Fine-tuned parameters: **260,355** (**12.921%**).

| unfrozen group | parameters | learning rate |
|---|---:|---:|
| pair_potential | 110,977 | 2e-05 |
| vapor_pressure | 37,442 | 1e-05 |
| film | 111,744 | 5e-06 |
| mixture_token | 192 | 5e-06 |

Stage 1 validation loss: `0.017084085`.
Stage 2 validation loss: `0.024780439`.
Selected final checkpoint: **stage1**.

The test partition was evaluated only after validation-only checkpoint selection.
