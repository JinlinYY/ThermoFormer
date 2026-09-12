# Binary-only state-space generalization

All values are mean ± standard deviation across seeds 0--4. Training, validation, and test contain binary VLE rows only. Checkpoint selection uses validation data; test data are evaluated afterward.

| Evaluation setting | Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | Solver failure rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Composition interpolation | molecules,P,x → T,y | 0.65 ± 0.05 K | 1.10 ± 0.30 K | 0.998 ± 0.001 | 0.0128 ± 0.0004 | 0.0206 ± 0.0008 | 0.994 ± 0.000 | 0.0000 ± 0.0000 |
| Composition interpolation | molecules,T,x → P,y | 1.66 ± 0.13 kPa | 6.18 ± 0.45 kPa | 0.995 ± 0.001 | 0.0079 ± 0.0005 | 0.0117 ± 0.0008 | 0.998 ± 0.000 | 0.0000 ± 0.0000 |
| Composition-edge extrapolation | molecules,P,x → T,y | 0.64 ± 0.03 K | 1.13 ± 0.07 K | 0.999 ± 0.000 | 0.0095 ± 0.0003 | 0.0225 ± 0.0005 | 0.997 ± 0.000 | 0.0000 ± 0.0000 |
| Composition-edge extrapolation | molecules,T,x → P,y | 1.83 ± 0.15 kPa | 6.46 ± 0.84 kPa | 0.995 ± 0.001 | 0.0038 ± 0.0001 | 0.0094 ± 0.0002 | 1.000 ± 0.000 | 0.0000 ± 0.0000 |
| Low-temperature extrapolation | molecules,P,x → T,y | 1.06 ± 0.32 K | 2.59 ± 1.30 K | 0.985 ± 0.016 | 0.0074 ± 0.0005 | 0.0172 ± 0.0015 | 0.998 ± 0.000 | 0.0000 ± 0.0000 |
| Low-temperature extrapolation | molecules,T,x → P,y | 2.70 ± 0.52 kPa | 5.87 ± 1.26 kPa | 0.994 ± 0.003 | 0.0118 ± 0.0008 | 0.0218 ± 0.0030 | 0.996 ± 0.001 | 0.0000 ± 0.0000 |
| High-temperature extrapolation | molecules,P,x → T,y | 1.03 ± 0.12 K | 1.69 ± 0.15 K | 0.997 ± 0.001 | 0.0194 ± 0.0009 | 0.0321 ± 0.0012 | 0.992 ± 0.001 | 0.0000 ± 0.0000 |
| High-temperature extrapolation | molecules,T,x → P,y | 5.26 ± 1.27 kPa | 13.66 ± 3.32 kPa | 0.989 ± 0.005 | 0.0111 ± 0.0010 | 0.0173 ± 0.0012 | 0.997 ± 0.000 | 0.0000 ± 0.0000 |
| Low-pressure extrapolation | molecules,P,x → T,y | 0.59 ± 0.03 K | 0.84 ± 0.03 K | 0.998 ± 0.000 | 0.0119 ± 0.0006 | 0.0186 ± 0.0011 | 0.996 ± 0.000 | 0.0000 ± 0.0000 |
| Low-pressure extrapolation | molecules,T,x → P,y | 1.40 ± 0.24 kPa | 4.83 ± 1.27 kPa | 0.985 ± 0.007 | 0.0121 ± 0.0007 | 0.0219 ± 0.0018 | 0.996 ± 0.001 | 0.0000 ± 0.0000 |
| High-pressure extrapolation | molecules,P,x → T,y | 0.85 ± 0.07 K | 1.27 ± 0.04 K | 0.995 ± 0.000 | 0.0154 ± 0.0013 | 0.0233 ± 0.0018 | 0.993 ± 0.001 | 0.0000 ± 0.0000 |
| High-pressure extrapolation | molecules,T,x → P,y | 3.63 ± 0.38 kPa | 10.51 ± 1.22 kPa | 0.994 ± 0.001 | 0.0073 ± 0.0002 | 0.0123 ± 0.0007 | 0.999 ± 0.000 | 0.0000 ± 0.0000 |

Validation-selected checkpoints: stage2=3, stage3=27

The model uses Stage 1 direct GE/RT and ln(gamma) supervision, Stage 2 joint VLE supervision, and Stage 3 ten-epoch fugacity fine-tuning.
