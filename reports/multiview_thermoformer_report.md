# ThermoFormer molecular-representation comparison

## Evaluation protocol

This report uses only the requested Table-1-style settings: binary train → binary test, binary+ternary train → binary test, and binary+ternary train → ternary test. It does not use unseen-component ranking. All values are mean ± sample standard deviation across five fixed random seeds. Each metric cell lists MAE, RMSE, and R² from top to bottom; pressure and temperature errors use kPa and K, while vapor-composition errors are dimensionless.

V2 is an explicit interface-equivalent alias of V0 and is shown for completeness, not counted as an independent experiment. A dagger marks a metric with fewer than five contributing seeds.

## Predictive performance

| Representation | Evaluation setting | P (kPa), isothermal | y, isothermal | T (K), isobaric | y, isobaric |
|---|---|---:|---:|---:|---:|
| V0 Legacy Uni-Mol v2 | Binary train → binary test | 17.26 ± 8.42 kPa<br>35.13 ± 14.93 kPa<br>0.911 ± 0.051 | 0.0681 ± 0.0146<br>0.1023 ± 0.0231<br>0.898 ± 0.049 | 5.75 ± 1.61 K<br>8.09 ± 2.50 K<br>0.920 ± 0.052 | 0.0638 ± 0.0217<br>0.0917 ± 0.0270<br>0.908 ± 0.058 |
| V0 Legacy Uni-Mol v2 | Binary+ternary train → binary test | 18.57 ± 6.40 kPa<br>40.45 ± 14.09 kPa<br>0.882 ± 0.052 | 0.0720 ± 0.0158<br>0.1083 ± 0.0203<br>0.887 ± 0.044 | 5.72 ± 1.56 K<br>8.16 ± 2.02 K<br>0.925 ± 0.025 | 0.0680 ± 0.0161<br>0.0987 ± 0.0176<br>0.898 ± 0.039 |
| V0 Legacy Uni-Mol v2 | Binary+ternary train → ternary test | 4.43 ± 3.39 kPa<br>5.68 ± 4.07 kPa<br>0.888 ± 0.130† | 0.0531 ± 0.0160<br>0.0729 ± 0.0197<br>0.909 ± 0.048† | 2.67 ± 0.46 K<br>3.60 ± 0.80 K<br>0.949 ± 0.040† | 0.0504 ± 0.0138<br>0.0695 ± 0.0233<br>0.891 ± 0.079† |
| V1 RDKit descriptors only | Binary train → binary test | 9.19 ± 4.76 kPa<br>18.85 ± 8.71 kPa<br>0.975 ± 0.015 | 0.0268 ± 0.0029<br>0.0468 ± 0.0106<br>0.979 ± 0.009 | 2.75 ± 0.29 K<br>4.78 ± 0.77 K<br>0.973 ± 0.013 | 0.0304 ± 0.0021<br>0.0534 ± 0.0077<br>0.971 ± 0.008 |
| V1 RDKit descriptors only | Binary+ternary train → binary test | 9.47 ± 4.11 kPa<br>20.36 ± 9.01 kPa<br>0.970 ± 0.019 | 0.0287 ± 0.0024<br>0.0506 ± 0.0085<br>0.976 ± 0.008 | 2.73 ± 0.32 K<br>4.63 ± 1.17 K<br>0.973 ± 0.018 | 0.0297 ± 0.0029<br>0.0524 ± 0.0096<br>0.972 ± 0.010 |
| V1 RDKit descriptors only | Binary+ternary train → ternary test | 1.94 ± 0.46 kPa<br>2.79 ± 0.55 kPa<br>0.975 ± 0.017† | 0.0220 ± 0.0075<br>0.0302 ± 0.0096<br>0.983 ± 0.013† | 1.54 ± 0.62 K<br>1.98 ± 0.97 K<br>0.978 ± 0.033† | 0.0343 ± 0.0173<br>0.0540 ± 0.0349<br>0.920 ± 0.079† |
| V2 Uni-Mol v2 unified interface (alias of V0) | Binary train → binary test | 17.26 ± 8.42 kPa<br>35.13 ± 14.93 kPa<br>0.911 ± 0.051 | 0.0681 ± 0.0146<br>0.1023 ± 0.0231<br>0.898 ± 0.049 | 5.75 ± 1.61 K<br>8.09 ± 2.50 K<br>0.920 ± 0.052 | 0.0638 ± 0.0217<br>0.0917 ± 0.0270<br>0.908 ± 0.058 |
| V2 Uni-Mol v2 unified interface (alias of V0) | Binary+ternary train → binary test | 18.57 ± 6.40 kPa<br>40.45 ± 14.09 kPa<br>0.882 ± 0.052 | 0.0720 ± 0.0158<br>0.1083 ± 0.0203<br>0.887 ± 0.044 | 5.72 ± 1.56 K<br>8.16 ± 2.02 K<br>0.925 ± 0.025 | 0.0680 ± 0.0161<br>0.0987 ± 0.0176<br>0.898 ± 0.039 |
| V2 Uni-Mol v2 unified interface (alias of V0) | Binary+ternary train → ternary test | 4.43 ± 3.39 kPa<br>5.68 ± 4.07 kPa<br>0.888 ± 0.130† | 0.0531 ± 0.0160<br>0.0729 ± 0.0197<br>0.909 ± 0.048† | 2.67 ± 0.46 K<br>3.60 ± 0.80 K<br>0.949 ± 0.040† | 0.0504 ± 0.0138<br>0.0695 ± 0.0233<br>0.891 ± 0.079† |
| V3 Functional groups only | Binary train → binary test | 21497.19 ± 47933.77 kPa<br>510164.56 ± 1140512.65 kPa<br>-133210773.173 ± 297868344.404 | 0.1414 ± 0.0175<br>0.2132 ± 0.0346<br>0.640 ± 0.113 | 36.61 ± 9.52 K<br>69.64 ± 14.51 K<br>-4.447 ± 1.605 | 0.2135 ± 0.0314<br>0.2849 ± 0.0427<br>0.149 ± 0.275 |
| V3 Functional groups only | Binary+ternary train → binary test | 100838.92 ± 225363.66 kPa<br>1909645.01 ± 4269724.72 kPa<br>-811715524.841 ± 1815051087.620 | 0.1560 ± 0.0191<br>0.2313 ± 0.0252<br>0.560 ± 0.094 | 32.22 ± 14.14 K<br>70.44 ± 49.53 K<br>-7.555 ± 10.968 | 0.2073 ± 0.0216<br>0.2731 ± 0.0261<br>0.233 ± 0.146 |
| V3 Functional groups only | Binary+ternary train → ternary test | 23.05 ± 9.80 kPa<br>31.33 ± 19.63 kPa<br>-3.671 ± 5.403† | 0.1409 ± 0.0418<br>0.2016 ± 0.0663<br>0.481 ± 0.310† | 20.10 ± 10.47 K<br>40.70 ± 44.50 K<br>-17.722 ± 35.106† | 0.1628 ± 0.0191<br>0.2032 ± 0.0169<br>0.167 ± 0.233† |
| V4 RDKit + Uni-Mol naive fusion | Binary train → binary test | 9.55 ± 5.21 kPa<br>21.73 ± 11.47 kPa<br>0.964 ± 0.027 | 0.0292 ± 0.0033<br>0.0506 ± 0.0090<br>0.976 ± 0.008 | 2.75 ± 0.41 K<br>4.55 ± 0.89 K<br>0.976 ± 0.011 | 0.0305 ± 0.0023<br>0.0520 ± 0.0050<br>0.972 ± 0.005 |
| V4 RDKit + Uni-Mol naive fusion | Binary+ternary train → binary test | 10.45 ± 5.97 kPa<br>23.54 ± 14.46 kPa<br>0.955 ± 0.040 | 0.0294 ± 0.0041<br>0.0517 ± 0.0102<br>0.974 ± 0.009 | 2.66 ± 0.43 K<br>4.28 ± 1.14 K<br>0.977 ± 0.016 | 0.0302 ± 0.0042<br>0.0516 ± 0.0085<br>0.972 ± 0.009 |
| V4 RDKit + Uni-Mol naive fusion | Binary+ternary train → ternary test | 1.46 ± 0.60 kPa<br>2.11 ± 0.77 kPa<br>0.985 ± 0.010† | 0.0166 ± 0.0045<br>0.0244 ± 0.0057<br>0.990 ± 0.007† | 1.47 ± 0.69 K<br>2.00 ± 1.17 K<br>0.976 ± 0.037† | 0.0313 ± 0.0194<br>0.0516 ± 0.0395<br>0.921 ± 0.082† |
| V5 Three-view naive fusion | Binary train → binary test | 9.62 ± 5.09 kPa<br>20.97 ± 10.61 kPa<br>0.968 ± 0.022 | 0.0283 ± 0.0047<br>0.0487 ± 0.0108<br>0.977 ± 0.010 | 2.75 ± 0.52 K<br>4.54 ± 0.50 K<br>0.977 ± 0.006 | 0.0294 ± 0.0054<br>0.0510 ± 0.0079<br>0.973 ± 0.008 |
| V5 Three-view naive fusion | Binary+ternary train → binary test | 9.03 ± 4.32 kPa<br>20.41 ± 9.39 kPa<br>0.969 ± 0.021 | 0.0274 ± 0.0046<br>0.0482 ± 0.0093<br>0.978 ± 0.008 | 2.57 ± 0.33 K<br>4.25 ± 0.86 K<br>0.979 ± 0.012 | 0.0300 ± 0.0045<br>0.0523 ± 0.0070<br>0.972 ± 0.007 |
| V5 Three-view naive fusion | Binary+ternary train → ternary test | 2.85 ± 1.01 kPa<br>3.40 ± 1.10 kPa<br>0.966 ± 0.018† | 0.0196 ± 0.0043<br>0.0267 ± 0.0066<br>0.988 ± 0.005† | 1.69 ± 0.46 K<br>2.21 ± 0.79 K<br>0.975 ± 0.030† | 0.0332 ± 0.0189<br>0.0534 ± 0.0371<br>0.919 ± 0.079† |
| V6 Interaction-specific multi-view fusion | Binary train → binary test | 10.05 ± 5.92 kPa<br>20.65 ± 9.79 kPa<br>0.969 ± 0.022 | 0.0279 ± 0.0043<br>0.0475 ± 0.0111<br>0.978 ± 0.010 | 2.84 ± 0.40 K<br>4.75 ± 1.00 K<br>0.972 ± 0.016 | 0.0315 ± 0.0063<br>0.0572 ± 0.0137<br>0.966 ± 0.016 |
| V6 Interaction-specific multi-view fusion | Binary+ternary train → binary test | 7.71 ± 2.56 kPa<br>15.80 ± 4.48 kPa<br>0.982 ± 0.006 | 0.0253 ± 0.0049<br>0.0448 ± 0.0125<br>0.980 ± 0.010 | 2.74 ± 0.44 K<br>4.76 ± 1.04 K<br>0.972 ± 0.016 | 0.0312 ± 0.0040<br>0.0563 ± 0.0115<br>0.967 ± 0.013 |
| V6 Interaction-specific multi-view fusion | Binary+ternary train → ternary test | 2.10 ± 0.46 kPa<br>2.65 ± 0.69 kPa<br>0.978 ± 0.013† | 0.0119 ± 0.0042<br>0.0171 ± 0.0051<br>0.995 ± 0.003† | 2.21 ± 0.60 K<br>2.83 ± 0.88 K<br>0.963 ± 0.036† | 0.0348 ± 0.0163<br>0.0572 ± 0.0347<br>0.912 ± 0.086† |

## MAE winners by setting

V2 is excluded from winner selection because it duplicates V0. Lower is better.

| Evaluation setting | P winner | Isothermal y winner | T winner | Isobaric y winner |
|---|---|---|---|---|
| Binary train → binary test | V1 RDKit descriptors only (9.19 kPa) | V1 RDKit descriptors only (0.0268) | V5 Three-view naive fusion (2.75 K) | V5 Three-view naive fusion (0.0294) |
| Binary+ternary train → binary test | V6 Interaction-specific multi-view fusion (7.71 kPa) | V6 Interaction-specific multi-view fusion (0.0253) | V5 Three-view naive fusion (2.57 K) | V1 RDKit descriptors only (0.0297) |
| Binary+ternary train → ternary test | V4 RDKit + Uni-Mol naive fusion (1.46 kPa) | V6 Interaction-specific multi-view fusion (0.0119) | V4 RDKit + Uni-Mol naive fusion (1.47 K) | V4 RDKit + Uni-Mol naive fusion (0.0313) |

## Interpretation boundary

The table supports comparisons only under these three grouped random-seed settings. It does not establish unseen-component extrapolation. The raw per-seed metrics, checkpoints, manifests, and resolved configurations remain the source of record under `results/`, `checkpoints/`, and `runs/`.
