# overall_binary

Status: **completed formal five-seed experiment**.

- Seeds: `0,1,2,3,4`

## Task-resolved predictive performance

### overall_binary — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 17.26 ± 8.42 (n=5) | 35.13 ± 14.93 (n=5) | 0.911 ± 0.051 (n=5) |
| Vapor composition y | 0.0681 ± 0.0146 (n=5) | 0.1023 ± 0.0231 (n=5) | 0.898 ± 0.049 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### overall_binary — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 5.75 ± 1.61 (n=5) | 8.09 ± 2.50 (n=5) | 0.920 ± 0.052 (n=5) |
| Vapor composition y | 0.0638 ± 0.0217 (n=5) | 0.0917 ± 0.0270 (n=5) | 0.908 ± 0.058 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

## Provenance and pooled diagnostics

- Pooled solver failure rate: 0.00000 ± 0.00000
- Pooled nonphysical rate: 0.00000 ± 0.00000
- Training commit: `8c41a1b46d217f5b9714bd5179fe28224b86408c`
- Aggregation commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Formal summary: `results/overall_binary/metrics_summary.csv`
- Per-seed predictions: `results/overall_binary/seed_*/predictions.csv`

These values are generated from committed fixed splits and should not be replaced by smoke or diagnostic runs.
