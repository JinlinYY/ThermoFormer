# ThermoFormer Predictive Performance and Generalization

Date: 2026-08-21. All confirmatory experiments use seeds 0–4, validation-only model selection, fixed committed splits, Uni-Mol v2 84M representations, and the differentiable mode-appropriate bubble solver. Values are mean ± sample standard deviation across seeds. Pressure, temperature, and composition errors are never combined into one scalar.

## Overall predictive performance

**Pressure metrics**

| Test subset | MAE (kPa) | RMSE (kPa) | R² |
|---|---:|---:|---:|
| Binary-only model: binary test | 17.26 ± 8.42 (n=5) | 35.13 ± 14.93 (n=5) | 0.911 ± 0.051 (n=5) |
| Joint model: binary test | 18.57 ± 6.40 (n=5) | 40.45 ± 14.09 (n=5) | 0.882 ± 0.052 (n=5) |
| Joint model: ternary test | 4.43 ± 3.39 (n=4) | 5.68 ± 4.07 (n=4) | 0.888 ± 0.130 (n=4) |

**Temperature metrics**

| Test subset | MAE (K) | RMSE (K) | R² |
|---|---:|---:|---:|
| Binary-only model: binary test | 5.75 ± 1.61 (n=5) | 8.09 ± 2.50 (n=5) | 0.920 ± 0.052 (n=5) |
| Joint model: binary test | 5.72 ± 1.56 (n=5) | 8.16 ± 2.02 (n=5) | 0.925 ± 0.025 (n=5) |
| Joint model: ternary test | 2.67 ± 0.46 (n=4) | 3.60 ± 0.80 (n=4) | 0.949 ± 0.040 (n=4) |

**Vapor-composition metrics**

| Test subset | MAE | RMSE | R² |
|---|---:|---:|---:|
| Binary-only model: binary test | 0.0657 ± 0.0176 (n=5) | 0.0970 ± 0.0238 (n=5) | 0.903 ± 0.052 (n=5) |
| Joint model: binary test | 0.0697 ± 0.0160 (n=5) | 0.1031 ± 0.0192 (n=5) | 0.893 ± 0.042 (n=5) |
| Joint model: ternary test | 0.0530 ± 0.0133 (n=5) | 0.0742 ± 0.0193 (n=5) | 0.900 ± 0.049 (n=5) |

**Prediction validity**

| Test subset | Valid coverage |
|---|---:|
| Binary-only model: binary test | 1.0000 ± 0.0000 |
| Joint model: binary test | 1.0000 ± 0.0000 |
| Joint model: ternary test | 1.0000 ± 0.0000 |

The joint binary/ternary model is reported by cardinality rather than as one pooled headline. Independent activity-coefficient error is not reported because the workbooks do not provide a complete trusted pure-property reference needed to invert experimental gamma without reusing the model's learned Psat branch.

## Thermodynamic-state interpolation and extrapolation

**Pressure metrics**

| Test subset | MAE (kPa) | RMSE (kPa) | R² |
|---|---:|---:|---:|
| State interpolation | 4.45 ± 1.03 (n=5) | 10.05 ± 2.37 (n=5) | 0.983 ± 0.008 (n=5) |
| Composition edge | 10.48 ± 3.35 (n=5) | 24.68 ± 7.10 (n=5) | 0.898 ± 0.059 (n=5) |
| Low temperature | 6.25 ± 2.47 (n=5) | 13.12 ± 7.41 (n=5) | 0.957 ± 0.049 (n=5) |
| High temperature | 15.16 ± 6.81 (n=5) | 32.24 ± 15.31 (n=5) | 0.917 ± 0.068 (n=5) |
| Low pressure | 4.59 ± 1.30 (n=5) | 9.38 ± 1.35 (n=5) | 0.930 ± 0.021 (n=5) |
| High pressure | 26.99 ± 7.49 (n=5) | 55.00 ± 16.09 (n=5) | 0.794 ± 0.096 (n=5) |

**Temperature metrics**

| Test subset | MAE (K) | RMSE (K) | R² |
|---|---:|---:|---:|
| State interpolation | 1.83 ± 0.45 (n=5) | 2.49 ± 0.58 (n=5) | 0.990 ± 0.005 (n=5) |
| Composition edge | 5.75 ± 3.35 (n=5) | 7.81 ± 4.65 (n=5) | 0.918 ± 0.105 (n=5) |
| Low temperature | 3.03 ± 1.14 (n=5) | 4.21 ± 1.53 (n=5) | 0.963 ± 0.029 (n=5) |
| High temperature | 5.15 ± 3.38 (n=5) | 6.98 ± 4.61 (n=5) | 0.927 ± 0.091 (n=5) |
| Low pressure | 5.33 ± 3.11 (n=5) | 6.83 ± 3.84 (n=5) | 0.853 ± 0.142 (n=5) |
| High pressure | 4.96 ± 1.24 (n=5) | 6.34 ± 1.51 (n=5) | 0.865 ± 0.057 (n=5) |

**Vapor-composition metrics**

| Test subset | MAE | RMSE | R² |
|---|---:|---:|---:|
| State interpolation | 0.0324 ± 0.0071 (n=5) | 0.0473 ± 0.0083 (n=5) | 0.969 ± 0.012 (n=5) |
| Composition edge | 0.0331 ± 0.0115 (n=5) | 0.0618 ± 0.0210 (n=5) | 0.976 ± 0.018 (n=5) |
| Low temperature | 0.0380 ± 0.0116 (n=5) | 0.0583 ± 0.0193 (n=5) | 0.971 ± 0.018 (n=5) |
| High temperature | 0.0478 ± 0.0150 (n=5) | 0.0726 ± 0.0228 (n=5) | 0.942 ± 0.035 (n=5) |
| Low pressure | 0.0676 ± 0.0278 (n=5) | 0.0965 ± 0.0377 (n=5) | 0.896 ± 0.073 (n=5) |
| High pressure | 0.0519 ± 0.0141 (n=5) | 0.0738 ± 0.0187 (n=5) | 0.944 ± 0.022 (n=5) |

**Prediction validity**

| Test subset | Valid coverage |
|---|---:|
| State interpolation | 1.0000 ± 0.0000 |
| Composition edge | 1.0000 ± 0.0000 |
| Low temperature | 1.0000 ± 0.0000 |
| High temperature | 1.0000 ± 0.0000 |
| Low pressure | 1.0000 ± 0.0000 |
| High pressure | 0.9996 ± 0.0009 |

Eligible test-system counts are: State interpolation=170; Composition edge=171; Low temperature=139; High temperature=139; Low pressure=68; High pressure=68. Distance-binned results are stored in `results/generalization/extrapolation_distance.csv`; strict split audit confirms that extrapolation test states lie beyond both validation and training boundaries for each mixture.

## Unseen mixtures and components

**Pressure metrics**

| Test subset | MAE (kPa) | RMSE (kPa) | R² |
|---|---:|---:|---:|
| State interpolation | 4.45 ± 1.03 (n=5) | 10.05 ± 2.37 (n=5) | 0.983 ± 0.008 (n=5) |
| Unseen mixture | 16.99 ± 5.88 (n=5) | 38.24 ± 13.89 (n=5) | 0.884 ± 0.052 (n=5) |
| Unseen component | 27.40 ± 0.87 (n=5) | 71.92 ± 5.21 (n=5) | 0.460 ± 0.076 (n=5) |

**Temperature metrics**

| Test subset | MAE (K) | RMSE (K) | R² |
|---|---:|---:|---:|
| State interpolation | 1.83 ± 0.45 (n=5) | 2.49 ± 0.58 (n=5) | 0.990 ± 0.005 (n=5) |
| Unseen mixture | 5.46 ± 1.48 (n=5) | 7.88 ± 2.01 (n=5) | 0.928 ± 0.025 (n=5) |
| Unseen component | 37.87 ± 3.63 (n=5) | 48.63 ± 4.10 (n=5) | 0.415 ± 0.098 (n=5) |

**Vapor-composition metrics**

| Test subset | MAE | RMSE | R² |
|---|---:|---:|---:|
| State interpolation | 0.0324 ± 0.0071 (n=5) | 0.0473 ± 0.0083 (n=5) | 0.969 ± 0.012 (n=5) |
| Unseen mixture | 0.0671 ± 0.0144 (n=5) | 0.0996 ± 0.0173 (n=5) | 0.898 ± 0.037 (n=5) |
| Unseen component | 0.0931 ± 0.0180 (n=5) | 0.1390 ± 0.0235 (n=5) | 0.846 ± 0.055 (n=5) |

**Prediction validity**

| Test subset | Valid coverage |
|---|---:|
| State interpolation | 1.0000 ± 0.0000 |
| Unseen mixture | 1.0000 ± 0.0000 |
| Unseen component | 0.9983 ± 0.0021 |

The sharp degradation for held-out components is the clearest present limitation. System-disjoint unseen mixtures remain substantially easier when their constituent molecules have appeared elsewhere.

## Binary-to-ternary transfer

**Pressure metrics**

| Test subset | MAE (kPa) | RMSE (kPa) | R² |
|---|---:|---:|---:|
| 0% | 5.03 ± 2.90 (n=5) | 5.86 ± 3.12 (n=5) | 0.749 ± 0.287 (n=5) |
| 5.56% | 4.23 ± 1.58 (n=5) | 5.07 ± 1.67 (n=5) | 0.867 ± 0.070 (n=5) |
| 10% | 4.68 ± 3.70 (n=5) | 5.51 ± 4.26 (n=5) | 0.850 ± 0.142 (n=5) |
| 25% | 5.11 ± 3.60 (n=5) | 6.38 ± 4.37 (n=5) | 0.679 ± 0.470 (n=5) |
| 50% | 5.18 ± 2.38 (n=5) | 6.35 ± 2.79 (n=5) | 0.778 ± 0.166 (n=5) |
| 100% | 4.52 ± 2.88 (n=5) | 5.50 ± 3.48 (n=5) | 0.848 ± 0.104 (n=5) |

**Temperature metrics**

| Test subset | MAE (K) | RMSE (K) | R² |
|---|---:|---:|---:|
| 0% | 5.58 ± 2.08 (n=5) | 6.24 ± 2.08 (n=5) | 0.950 ± 0.030 (n=5) |
| 5.56% | 4.98 ± 2.10 (n=5) | 6.15 ± 2.49 (n=5) | 0.952 ± 0.027 (n=5) |
| 10% | 7.43 ± 4.13 (n=5) | 9.21 ± 5.75 (n=5) | 0.854 ± 0.198 (n=5) |
| 25% | 5.31 ± 1.08 (n=5) | 6.33 ± 1.26 (n=5) | 0.955 ± 0.012 (n=5) |
| 50% | 5.99 ± 3.10 (n=5) | 6.86 ± 3.51 (n=5) | 0.942 ± 0.050 (n=5) |
| 100% | 5.40 ± 1.10 (n=5) | 6.24 ± 0.76 (n=5) | 0.955 ± 0.012 (n=5) |

**Vapor-composition metrics**

| Test subset | MAE | RMSE | R² |
|---|---:|---:|---:|
| 0% | 0.0581 ± 0.0039 (n=5) | 0.0927 ± 0.0043 (n=5) | 0.843 ± 0.008 (n=5) |
| 5.56% | 0.0602 ± 0.0079 (n=5) | 0.0939 ± 0.0084 (n=5) | 0.837 ± 0.035 (n=5) |
| 10% | 0.0698 ± 0.0279 (n=5) | 0.1063 ± 0.0282 (n=5) | 0.783 ± 0.121 (n=5) |
| 25% | 0.0689 ± 0.0105 (n=5) | 0.1002 ± 0.0085 (n=5) | 0.814 ± 0.039 (n=5) |
| 50% | 0.0721 ± 0.0202 (n=5) | 0.1070 ± 0.0206 (n=5) | 0.784 ± 0.087 (n=5) |
| 100% | 0.0587 ± 0.0060 (n=5) | 0.0942 ± 0.0052 (n=5) | 0.836 ± 0.028 (n=5) |

**Prediction validity**

| Test subset | Valid coverage |
|---|---:|
| 0% | 1.0000 ± 0.0000 |
| 5.56% | 1.0000 ± 0.0000 |
| 10% | 1.0000 ± 0.0000 |
| 25% | 1.0000 ± 0.0000 |
| 50% | 1.0000 ± 0.0000 |
| 100% | 1.0000 ± 0.0000 |

The fixed-test scaling curve is non-monotonic. With only 18 candidate ternary training systems, subset identity and seed variability dominate several nominal fractions; added ternary labels do not consistently improve vapor-composition MAE over binary-only zero-shot transfer. This negative result is retained rather than smoothed or selectively reported.

Coverage-controlled metrics for 0/3 through 3/3 observed binary subsystems are in `results/generalization/binary_subsystem_controlled.csv`. They use only binary systems present in the actual training partition when assigning coverage.

## Solver validity and scope

Most protocols have 100% valid coverage. High-pressure extrapolation and unseen-component tests contain small, explicitly reported failure fractions; failed rows remain in attempted-sample denominators. No nonphysical predictions were observed in aggregate summaries. The supported claim is limited to low-pressure binary and ternary VLE below the configured 500 kPa cutoff. There are no quaternary data or quaternary claims.

## Recommendation

Do not expand the architecture solely to improve the first formal metrics. First add strong thermodynamic and data-driven baselines on the identical committed splits, instrument per-objective gradient diagnostics during training, and investigate held-out-component representation/calibration and the non-monotonic ternary scaling subsets. Any method-changing modification should be proposed separately and preserve these first-round results.
