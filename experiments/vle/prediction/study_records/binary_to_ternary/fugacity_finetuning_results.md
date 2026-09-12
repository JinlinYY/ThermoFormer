# Binary-to-ternary transfer

All values are mean ± standard deviation across seeds 0--4. Checkpoint selection uses validation only; test data are evaluated afterward.

| Evaluation setting | subset | task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | n |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 0% ternary (zero-shot) | all | isobaric (molecules,P,x → T,y) | 1.91 ± 0.89 K | 2.56 ± 1.18 K | 0.989 ± 0.012 | 0.0714 ± 0.0167 | 0.1094 ± 0.0137 | 0.774 ± 0.059 | 5 |
| 0% ternary (zero-shot) | all | isothermal (molecules,T,x → P,y) | 1.62 ± 0.38 kPa | 2.09 ± 0.45 kPa | 0.976 ± 0.014 | 0.0129 ± 0.0034 | 0.0190 ± 0.0022 | 0.992 ± 0.005 | 5 |
| 5.56% ternary | all | isobaric (molecules,P,x → T,y) | 1.97 ± 0.52 K | 2.67 ± 0.66 K | 0.990 ± 0.007 | 0.0743 ± 0.0169 | 0.1118 ± 0.0135 | 0.764 ± 0.063 | 5 |
| 5.56% ternary | all | isothermal (molecules,T,x → P,y) | 2.15 ± 0.89 kPa | 2.62 ± 0.94 kPa | 0.953 ± 0.038 | 0.0144 ± 0.0042 | 0.0202 ± 0.0040 | 0.991 ± 0.005 | 5 |
| 10% ternary | all | isobaric (molecules,P,x → T,y) | 2.05 ± 0.54 K | 2.61 ± 0.65 K | 0.991 ± 0.007 | 0.0724 ± 0.0165 | 0.1106 ± 0.0132 | 0.769 ± 0.059 | 5 |
| 10% ternary | all | isothermal (molecules,T,x → P,y) | 1.93 ± 0.60 kPa | 2.35 ± 0.69 kPa | 0.968 ± 0.018 | 0.0136 ± 0.0044 | 0.0196 ± 0.0046 | 0.991 ± 0.007 | 5 |
| 25% ternary | all | isobaric (molecules,P,x → T,y) | 1.86 ± 1.18 K | 2.47 ± 1.37 K | 0.989 ± 0.013 | 0.0723 ± 0.0165 | 0.1109 ± 0.0132 | 0.768 ± 0.060 | 5 |
| 25% ternary | all | isothermal (molecules,T,x → P,y) | 1.80 ± 0.61 kPa | 2.39 ± 0.65 kPa | 0.964 ± 0.021 | 0.0140 ± 0.0026 | 0.0200 ± 0.0027 | 0.992 ± 0.004 | 5 |
| 50% ternary | all | isobaric (molecules,P,x → T,y) | 1.81 ± 0.86 K | 2.43 ± 1.15 K | 0.990 ± 0.010 | 0.0721 ± 0.0159 | 0.1109 ± 0.0127 | 0.768 ± 0.060 | 5 |
| 50% ternary | all | isothermal (molecules,T,x → P,y) | 1.30 ± 0.50 kPa | 1.81 ± 0.57 kPa | 0.982 ± 0.011 | 0.0112 ± 0.0028 | 0.0169 ± 0.0029 | 0.994 ± 0.002 | 5 |
| 100% ternary | all | isobaric (molecules,P,x → T,y) | 1.78 ± 0.54 K | 2.38 ± 0.74 K | 0.992 ± 0.007 | 0.0736 ± 0.0156 | 0.1112 ± 0.0124 | 0.767 ± 0.054 | 5 |
| 100% ternary | all | isothermal (molecules,T,x → P,y) | 1.47 ± 0.38 kPa | 1.87 ± 0.44 kPa | 0.982 ± 0.008 | 0.0128 ± 0.0028 | 0.0187 ± 0.0034 | 0.993 ± 0.003 | 5 |

Zero-shot ternary state prediction is useful, while isobaric vapor-composition prediction remains the main transfer limitation; performance is not monotonic with ternary training fraction.

Machine-readable source: `experiments/vle/prediction/summary/c1_fugacity_generalization_by_task.csv` (SHA-256 `2aebedb9798f5556b5480bd69d06752bf6a48cfc335d46fcd61b2a7649c1452c`).
