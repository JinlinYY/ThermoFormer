# state_temperature_high_extrapolation

Status: **completed formal five-seed experiment**.

- Seeds: `0,1,2,3,4`

## Task-resolved predictive performance

### state_temperature_high_extrapolation — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 15.16 ± 6.81 (n=5) | 32.24 ± 15.31 (n=5) | 0.917 ± 0.068 (n=5) |
| Vapor composition y | 0.0435 ± 0.0119 (n=5) | 0.0652 ± 0.0189 (n=5) | 0.949 ± 0.028 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### state_temperature_high_extrapolation — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 5.15 ± 3.38 (n=5) | 6.98 ± 4.61 (n=5) | 0.927 ± 0.091 (n=5) |
| Vapor composition y | 0.0507 ± 0.0175 (n=5) | 0.0769 ± 0.0259 (n=5) | 0.939 ± 0.040 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

## Provenance and pooled diagnostics

- Pooled solver failure rate: 0.00000 ± 0.00000
- Pooled nonphysical rate: 0.00000 ± 0.00000
- Training commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Aggregation commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Formal summary: `results/state_temperature_high_extrapolation/metrics_summary.csv`
- Per-seed predictions: `results/state_temperature_high_extrapolation/seed_*/predictions.csv`

These values are generated from committed fixed splits and should not be replaced by smoke or diagnostic runs.
