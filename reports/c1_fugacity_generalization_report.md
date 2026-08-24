# C1 Three-View Vanilla ThermoFormer: Predictive Performance and Generalization

Final architecture: RDKit descriptors + Uni-Mol v2 + functional-group features, independent projections and fusion, vanilla Transformer, original pair potential. Stage 2 retains supervised loss and adds only the teacher-forced fugacity-equilibrium loss.

All values are mean ± standard deviation across seeds 0--4. Checkpoint selection uses validation only; the test partition is evaluated after selection. Isothermal inference is `molecules,T,x -> P,y`; isobaric inference is `molecules,P,x -> T,y`.

## Overall predictive performance

| Evaluation setting | subset | task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | n |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Binary train -> binary test | all | isobaric (molecules,P,x → T,y) | 2.45 ± 0.15 K | 4.29 ± 0.52 K | 0.979 ± 0.008 | 0.0284 ± 0.0043 | 0.0499 ± 0.0058 | 0.975 ± 0.005 | 5 |
| Binary train -> binary test | all | isothermal (molecules,T,x → P,y) | 8.98 ± 5.20 kPa | 20.58 ± 11.95 kPa | 0.968 ± 0.027 | 0.0262 ± 0.0056 | 0.0476 ± 0.0120 | 0.978 ± 0.010 | 5 |
| Binary+ternary train -> joint test | binary | isobaric (molecules,P,x → T,y) | 2.45 ± 0.31 K | 4.23 ± 0.79 K | 0.979 ± 0.010 | 0.0293 ± 0.0055 | 0.0513 ± 0.0079 | 0.973 ± 0.008 | 5 |
| Binary+ternary train -> joint test | ternary | isobaric (molecules,P,x → T,y) | 1.41 ± 0.61 K | 1.95 ± 1.00 K | 0.979 ± 0.032 | 0.0317 ± 0.0181 | 0.0536 ± 0.0369 | 0.919 ± 0.079 | 4 |
| Binary+ternary train -> joint test | binary | isothermal (molecules,T,x → P,y) | 8.68 ± 4.71 kPa | 19.55 ± 10.47 kPa | 0.971 ± 0.024 | 0.0265 ± 0.0058 | 0.0470 ± 0.0112 | 0.979 ± 0.009 | 5 |
| Binary+ternary train -> joint test | ternary | isothermal (molecules,T,x → P,y) | 1.85 ± 0.27 kPa | 2.44 ± 0.31 kPa | 0.984 ± 0.004 | 0.0168 ± 0.0052 | 0.0239 ± 0.0082 | 0.991 ± 0.006 | 4 |

## State interpolation and extrapolation

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

## Unseen-component generalization

| Evaluation setting | subset | task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | n |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Unseen component | all | isobaric (molecules,P,x → T,y) | 36.45 ± 1.49 K | 46.99 ± 1.94 K | 0.456 ± 0.044 | 0.1191 ± 0.0062 | 0.1659 ± 0.0047 | 0.792 ± 0.012 | 5 |
| Unseen component | all | isothermal (molecules,T,x → P,y) | 32.39 ± 11.31 kPa | 68.32 ± 15.80 kPa | 0.494 ± 0.242 | 0.1057 ± 0.0179 | 0.1694 ± 0.0250 | 0.768 ± 0.066 | 5 |

## Binary-to-ternary transfer

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

## Fugacity fine-tuning selection

Across 15 protocols × 5 seeds, validation retained Stage 1 for **16/75** runs and selected Stage 2 for **59/75** runs. The teacher-forced fugacity residual decreased after Stage 2 in **14/15** protocol means.

As a post-selection descriptive comparison, raw Stage 2 test means improved over raw Stage 1 in **146/180** direction-resolved MAE/RMSE/R² cells. This comparison was not used to tune the loss or select checkpoints.

This is evidence for using validation-gated fugacity fine-tuning, not a claim that Stage 2 uniformly improves every predictive metric or every random seed.

## Numerical diagnostics

Maximum mean solver-failure rate: `0.000000`; maximum mean nonphysical rate: `0.000000`; minimum valid coverage: `1.000000`.

Machine-readable task metrics and Stage-1/Stage-2 selection diagnostics are stored in `results/performance/c1_fugacity_generalization_by_task.csv` and `results/performance/c1_fugacity_stage_selection.csv`.
