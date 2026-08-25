# Thermodynamic-state generalization

All values are mean ± standard deviation across seeds 0--4. Checkpoint selection uses validation only; test data are evaluated afterward.

| Evaluation setting | subset | task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | n |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Composition interpolation | all | isobaric (molecules,P,x → T,y) | 0.58 ± 0.04 K | 0.86 ± 0.06 K | 0.999 ± 0.000 | 0.0166 ± 0.0009 | 0.0331 ± 0.0007 | 0.985 ± 0.001 | 5 |
| Composition interpolation | all | isothermal (molecules,T,x → P,y) | 1.61 ± 0.20 kPa | 5.37 ± 0.83 kPa | 0.995 ± 0.001 | 0.0095 ± 0.0010 | 0.0142 ± 0.0014 | 0.997 ± 0.001 | 5 |
| Composition edge extrapolation | all | isobaric (molecules,P,x → T,y) | 0.92 ± 0.10 K | 1.37 ± 0.12 K | 0.998 ± 0.000 | 0.0152 ± 0.0003 | 0.0385 ± 0.0004 | 0.991 ± 0.000 | 5 |
| Composition edge extrapolation | all | isothermal (molecules,T,x → P,y) | 1.91 ± 0.21 kPa | 4.98 ± 0.87 kPa | 0.996 ± 0.001 | 0.0075 ± 0.0007 | 0.0143 ± 0.0012 | 0.999 ± 0.000 | 5 |
| Low-temperature extrapolation | all | isobaric (molecules,P,x → T,y) | 1.16 ± 0.16 K | 2.09 ± 0.40 K | 0.992 ± 0.003 | 0.0112 ± 0.0006 | 0.0240 ± 0.0019 | 0.996 ± 0.001 | 5 |
| Low-temperature extrapolation | all | isothermal (molecules,T,x → P,y) | 2.05 ± 0.58 kPa | 3.69 ± 1.31 kPa | 0.997 ± 0.002 | 0.0136 ± 0.0012 | 0.0204 ± 0.0016 | 0.996 ± 0.001 | 5 |
| High-temperature extrapolation | all | isobaric (molecules,P,x → T,y) | 1.11 ± 0.06 K | 1.77 ± 0.09 K | 0.997 ± 0.000 | 0.0219 ± 0.0012 | 0.0399 ± 0.0012 | 0.985 ± 0.001 | 5 |
| High-temperature extrapolation | all | isothermal (molecules,T,x → P,y) | 5.83 ± 0.42 kPa | 13.48 ± 0.59 kPa | 0.988 ± 0.001 | 0.0120 ± 0.0011 | 0.0194 ± 0.0020 | 0.996 ± 0.001 | 5 |
| Low-pressure extrapolation | all | isobaric (molecules,P,x → T,y) | 0.85 ± 0.09 K | 1.19 ± 0.13 K | 0.996 ± 0.001 | 0.0162 ± 0.0041 | 0.0237 ± 0.0051 | 0.994 ± 0.003 | 5 |
| Low-pressure extrapolation | all | isothermal (molecules,T,x → P,y) | 1.15 ± 0.24 kPa | 2.95 ± 0.58 kPa | 0.993 ± 0.002 | 0.0160 ± 0.0039 | 0.0247 ± 0.0062 | 0.994 ± 0.003 | 5 |
| High-pressure extrapolation | all | isobaric (molecules,P,x → T,y) | 0.94 ± 0.19 K | 1.31 ± 0.24 K | 0.994 ± 0.002 | 0.0202 ± 0.0052 | 0.0293 ± 0.0058 | 0.989 ± 0.005 | 5 |
| High-pressure extrapolation | all | isothermal (molecules,T,x → P,y) | 5.96 ± 1.35 kPa | 13.01 ± 3.06 kPa | 0.989 ± 0.005 | 0.0128 ± 0.0042 | 0.0237 ± 0.0097 | 0.995 ± 0.005 | 5 |

Composition interpolation is the most accurate state task. High-temperature and high-pressure extrapolation are more difficult for bubble-pressure prediction.

Machine-readable source: `results/performance/c1_fugacity_generalization_by_task.csv` (SHA-256 `2aebedb9798f5556b5480bd69d06752bf6a48cfc335d46fcd61b2a7649c1452c`).
