# ThermoFormer Predictive Performance and Generalization

Date: 2026-08-21. All confirmatory experiments use seeds 0–4, validation-only model selection, fixed committed splits, Uni-Mol v2 84M representations, and the differentiable mode-appropriate bubble solver. Values are mean ± sample standard deviation across seeds. Pressure, temperature, and composition errors are never combined into one scalar.

## Prediction tasks and outputs

ThermoFormer is evaluated as two coupled bubble-point tasks. A row does not predict only one scalar: each task jointly returns the unknown bubble-point state variable and the full vapor-composition vector.

| Task | Known inputs | Joint prediction |
|---|---|---|
| Isothermal P–x–y | Molecules, T, liquid composition x | Bubble pressure P and vapor composition y |
| Isobaric T–x–y | Molecules, P, liquid composition x | Bubble temperature T and vapor composition y |

Full-state TP–x–y records are evaluated in both directions. Pressure metrics therefore use only isothermal solves, temperature metrics use only isobaric solves, and vapor-composition metrics are reported separately for each direction. The number in `(n=...)` is the actual number of contributing seeds.

## Overall predictive performance

### Binary-only model: binary test — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 17.26 ± 8.42 (n=5) | 35.13 ± 14.93 (n=5) | 0.911 ± 0.051 (n=5) |
| Vapor composition y | 0.0681 ± 0.0146 (n=5) | 0.1023 ± 0.0231 (n=5) | 0.898 ± 0.049 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### Binary-only model: binary test — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 5.75 ± 1.61 (n=5) | 8.09 ± 2.50 (n=5) | 0.920 ± 0.052 (n=5) |
| Vapor composition y | 0.0638 ± 0.0217 (n=5) | 0.0917 ± 0.0270 (n=5) | 0.908 ± 0.058 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### Joint model: binary test — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 18.57 ± 6.40 (n=5) | 40.45 ± 14.09 (n=5) | 0.882 ± 0.052 (n=5) |
| Vapor composition y | 0.0720 ± 0.0158 (n=5) | 0.1083 ± 0.0203 (n=5) | 0.887 ± 0.044 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### Joint model: binary test — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 5.72 ± 1.56 (n=5) | 8.16 ± 2.02 (n=5) | 0.925 ± 0.025 (n=5) |
| Vapor composition y | 0.0680 ± 0.0161 (n=5) | 0.0987 ± 0.0176 (n=5) | 0.898 ± 0.039 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### Joint model: ternary test — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 4.43 ± 3.39 (n=4) | 5.68 ± 4.07 (n=4) | 0.888 ± 0.130 (n=4) |
| Vapor composition y | 0.0531 ± 0.0160 (n=4) | 0.0729 ± 0.0197 (n=4) | 0.909 ± 0.048 (n=4) |

Valid coverage: 1.0000 ± 0.0000.

### Joint model: ternary test — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 2.67 ± 0.46 (n=4) | 3.60 ± 0.80 (n=4) | 0.949 ± 0.040 (n=4) |
| Vapor composition y | 0.0504 ± 0.0138 (n=4) | 0.0695 ± 0.0233 (n=4) | 0.891 ± 0.079 (n=4) |

Valid coverage: 1.0000 ± 0.0000.

The joint binary/ternary model is reported by cardinality and task direction rather than as one pooled headline. Independent activity-coefficient error is not reported because the workbooks do not provide a complete trusted pure-property reference needed to invert experimental gamma without reusing the model's learned Psat branch.

## Thermodynamic-state interpolation and extrapolation

### State interpolation — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 4.45 ± 1.03 (n=5) | 10.05 ± 2.37 (n=5) | 0.983 ± 0.008 (n=5) |
| Vapor composition y | 0.0301 ± 0.0065 (n=5) | 0.0427 ± 0.0096 (n=5) | 0.975 ± 0.012 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### State interpolation — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 1.83 ± 0.45 (n=5) | 2.49 ± 0.58 (n=5) | 0.990 ± 0.005 (n=5) |
| Vapor composition y | 0.0338 ± 0.0077 (n=5) | 0.0501 ± 0.0080 (n=5) | 0.964 ± 0.012 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### Composition edge — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 10.48 ± 3.35 (n=5) | 24.68 ± 7.10 (n=5) | 0.898 ± 0.059 (n=5) |
| Vapor composition y | 0.0275 ± 0.0072 (n=5) | 0.0551 ± 0.0143 (n=5) | 0.982 ± 0.010 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### Composition edge — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 5.75 ± 3.35 (n=5) | 7.81 ± 4.65 (n=5) | 0.918 ± 0.105 (n=5) |
| Vapor composition y | 0.0369 ± 0.0148 (n=5) | 0.0657 ± 0.0253 (n=5) | 0.971 ± 0.025 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### Low temperature — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 6.25 ± 2.47 (n=5) | 13.12 ± 7.41 (n=5) | 0.957 ± 0.049 (n=5) |
| Vapor composition y | 0.0495 ± 0.0176 (n=5) | 0.0731 ± 0.0286 (n=5) | 0.943 ± 0.040 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### Low temperature — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 3.03 ± 1.14 (n=5) | 4.21 ± 1.53 (n=5) | 0.963 ± 0.029 (n=5) |
| Vapor composition y | 0.0297 ± 0.0085 (n=5) | 0.0441 ± 0.0109 (n=5) | 0.986 ± 0.007 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### High temperature — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 15.16 ± 6.81 (n=5) | 32.24 ± 15.31 (n=5) | 0.917 ± 0.068 (n=5) |
| Vapor composition y | 0.0435 ± 0.0119 (n=5) | 0.0652 ± 0.0189 (n=5) | 0.949 ± 0.028 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### High temperature — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 5.15 ± 3.38 (n=5) | 6.98 ± 4.61 (n=5) | 0.927 ± 0.091 (n=5) |
| Vapor composition y | 0.0507 ± 0.0175 (n=5) | 0.0769 ± 0.0259 (n=5) | 0.939 ± 0.040 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### Low pressure — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 4.59 ± 1.30 (n=5) | 9.38 ± 1.35 (n=5) | 0.930 ± 0.021 (n=5) |
| Vapor composition y | 0.0673 ± 0.0289 (n=5) | 0.1011 ± 0.0407 (n=5) | 0.890 ± 0.080 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### Low pressure — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 5.33 ± 3.11 (n=5) | 6.83 ± 3.84 (n=5) | 0.853 ± 0.142 (n=5) |
| Vapor composition y | 0.0681 ± 0.0260 (n=5) | 0.0879 ± 0.0322 (n=5) | 0.906 ± 0.062 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### High pressure — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 26.99 ± 7.49 (n=5) | 55.00 ± 16.09 (n=5) | 0.794 ± 0.096 (n=5) |
| Vapor composition y | 0.0412 ± 0.0118 (n=5) | 0.0566 ± 0.0142 (n=5) | 0.971 ± 0.012 (n=5) |

Valid coverage: 0.9993 ± 0.0015.

### High pressure — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 4.96 ± 1.24 (n=5) | 6.34 ± 1.51 (n=5) | 0.865 ± 0.057 (n=5) |
| Vapor composition y | 0.0678 ± 0.0202 (n=5) | 0.0936 ± 0.0252 (n=5) | 0.883 ± 0.050 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

Eligible test-system counts are: State interpolation=170; Composition edge=171; Low temperature=139; High temperature=139; Low pressure=68; High pressure=68. Distance-binned results are stored in `results/generalization/extrapolation_distance.csv`; strict split audit confirms that extrapolation test states lie beyond both validation and training boundaries for each mixture.

## Unseen mixtures and components

### State interpolation — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 4.45 ± 1.03 (n=5) | 10.05 ± 2.37 (n=5) | 0.983 ± 0.008 (n=5) |
| Vapor composition y | 0.0301 ± 0.0065 (n=5) | 0.0427 ± 0.0096 (n=5) | 0.975 ± 0.012 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### State interpolation — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 1.83 ± 0.45 (n=5) | 2.49 ± 0.58 (n=5) | 0.990 ± 0.005 (n=5) |
| Vapor composition y | 0.0338 ± 0.0077 (n=5) | 0.0501 ± 0.0080 (n=5) | 0.964 ± 0.012 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### Unseen mixture — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 16.99 ± 5.88 (n=5) | 38.24 ± 13.89 (n=5) | 0.884 ± 0.052 (n=5) |
| Vapor composition y | 0.0685 ± 0.0148 (n=5) | 0.1032 ± 0.0188 (n=5) | 0.895 ± 0.041 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### Unseen mixture — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 5.46 ± 1.48 (n=5) | 7.88 ± 2.01 (n=5) | 0.928 ± 0.025 (n=5) |
| Vapor composition y | 0.0659 ± 0.0142 (n=5) | 0.0965 ± 0.0155 (n=5) | 0.901 ± 0.033 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### Unseen component — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 27.40 ± 0.87 (n=5) | 71.92 ± 5.21 (n=5) | 0.460 ± 0.076 (n=5) |
| Vapor composition y | 0.0789 ± 0.0180 (n=5) | 0.1229 ± 0.0244 (n=5) | 0.876 ± 0.051 (n=5) |

Valid coverage: 0.9975 ± 0.0030.

### Unseen component — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 37.87 ± 3.63 (n=5) | 48.63 ± 4.10 (n=5) | 0.415 ± 0.098 (n=5) |
| Vapor composition y | 0.1266 ± 0.0194 (n=5) | 0.1708 ± 0.0237 (n=5) | 0.776 ± 0.065 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

The sharp degradation for held-out components is the clearest present limitation. System-disjoint unseen mixtures remain substantially easier when their constituent molecules have appeared elsewhere.

## Binary-to-ternary transfer

### 0% — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 5.03 ± 2.90 (n=5) | 5.86 ± 3.12 (n=5) | 0.749 ± 0.287 (n=5) |
| Vapor composition y | 0.0318 ± 0.0031 (n=5) | 0.0409 ± 0.0048 (n=5) | 0.966 ± 0.011 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### 0% — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 5.58 ± 2.08 (n=5) | 6.24 ± 2.08 (n=5) | 0.950 ± 0.030 (n=5) |
| Vapor composition y | 0.0828 ± 0.0153 (n=5) | 0.1225 ± 0.0164 (n=5) | 0.714 ± 0.089 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### 5.56% — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 4.23 ± 1.58 (n=5) | 5.07 ± 1.67 (n=5) | 0.867 ± 0.070 (n=5) |
| Vapor composition y | 0.0358 ± 0.0074 (n=5) | 0.0490 ± 0.0116 (n=5) | 0.952 ± 0.020 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### 5.56% — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 4.98 ± 2.10 (n=5) | 6.15 ± 2.49 (n=5) | 0.952 ± 0.027 (n=5) |
| Vapor composition y | 0.0840 ± 0.0135 (n=5) | 0.1215 ± 0.0133 (n=5) | 0.718 ± 0.083 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### 10% — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 4.68 ± 3.70 (n=5) | 5.51 ± 4.26 (n=5) | 0.850 ± 0.142 (n=5) |
| Vapor composition y | 0.0500 ± 0.0353 (n=5) | 0.0655 ± 0.0476 (n=5) | 0.879 ± 0.180 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### 10% — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 7.43 ± 4.13 (n=5) | 9.21 ± 5.75 (n=5) | 0.854 ± 0.198 (n=5) |
| Vapor composition y | 0.0883 ± 0.0248 (n=5) | 0.1296 ± 0.0204 (n=5) | 0.683 ± 0.088 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### 25% — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 5.11 ± 3.60 (n=5) | 6.38 ± 4.37 (n=5) | 0.679 ± 0.470 (n=5) |
| Vapor composition y | 0.0498 ± 0.0134 (n=5) | 0.0637 ± 0.0169 (n=5) | 0.912 ± 0.049 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### 25% — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 5.31 ± 1.08 (n=5) | 6.33 ± 1.26 (n=5) | 0.955 ± 0.012 (n=5) |
| Vapor composition y | 0.0878 ± 0.0158 (n=5) | 0.1245 ± 0.0128 (n=5) | 0.702 ± 0.086 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### 50% — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 5.18 ± 2.38 (n=5) | 6.35 ± 2.79 (n=5) | 0.778 ± 0.166 (n=5) |
| Vapor composition y | 0.0532 ± 0.0288 (n=5) | 0.0738 ± 0.0372 (n=5) | 0.882 ± 0.101 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### 50% — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 5.99 ± 3.10 (n=5) | 6.86 ± 3.51 (n=5) | 0.942 ± 0.050 (n=5) |
| Vapor composition y | 0.0924 ± 0.0245 (n=5) | 0.1294 ± 0.0228 (n=5) | 0.670 ± 0.152 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### 100% — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 4.52 ± 2.88 (n=5) | 5.50 ± 3.48 (n=5) | 0.848 ± 0.104 (n=5) |
| Vapor composition y | 0.0361 ± 0.0129 (n=5) | 0.0481 ± 0.0177 (n=5) | 0.951 ± 0.031 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### 100% — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 5.40 ± 1.10 (n=5) | 6.24 ± 0.76 (n=5) | 0.955 ± 0.012 (n=5) |
| Vapor composition y | 0.0817 ± 0.0113 (n=5) | 0.1220 ± 0.0114 (n=5) | 0.716 ± 0.084 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

The fixed-test scaling curve is non-monotonic. With only 18 candidate ternary training systems, subset identity and seed variability dominate several nominal fractions; added ternary labels do not consistently improve vapor-composition MAE over binary-only zero-shot transfer. This negative result is retained rather than smoothed or selectively reported.

Coverage-controlled metrics for 0/3 through 3/3 observed binary subsystems are in `results/generalization/binary_subsystem_controlled.csv`. They use only binary systems present in the actual training partition when assigning coverage.

## Solver validity and scope

Most protocols have 100% valid coverage. High-pressure extrapolation and unseen-component tests contain small, explicitly reported failure fractions; failed rows remain in attempted-sample denominators. No nonphysical predictions were observed in aggregate summaries. The supported claim is limited to low-pressure binary and ternary VLE below the configured 500 kPa cutoff. There are no quaternary data or quaternary claims.

## Recommendation

Do not expand the architecture solely to improve the first formal metrics. First add strong thermodynamic and data-driven baselines on the identical committed splits, instrument per-objective gradient diagnostics during training, and investigate held-out-component representation/calibration and the non-monotonic ternary scaling subsets. Any method-changing modification should be proposed separately and preserve these first-round results.
