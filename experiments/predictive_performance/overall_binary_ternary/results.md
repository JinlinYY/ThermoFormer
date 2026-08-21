# overall_binary_ternary

Status: **completed formal five-seed experiment**.

- Seeds: `0,1,2,3,4`

## Task-resolved predictive performance

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

## Provenance and pooled diagnostics

- Pooled solver failure rate: 0.00000 ± 0.00000
- Pooled nonphysical rate: 0.00000 ± 0.00000
- Training commit: `8c41a1b46d217f5b9714bd5179fe28224b86408c`
- Aggregation commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Formal summary: `results/overall_binary_ternary/metrics_summary.csv`
- Per-seed predictions: `results/overall_binary_ternary/seed_*/predictions.csv`

These values are generated from committed fixed splits and should not be replaced by smoke or diagnostic runs.
