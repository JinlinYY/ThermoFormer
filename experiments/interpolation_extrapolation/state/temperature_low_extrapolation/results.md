# state_temperature_low_extrapolation

Status: **completed formal five-seed experiment**.

- Seeds: `0,1,2,3,4`

## Task-resolved predictive performance

### state_temperature_low_extrapolation — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 6.25 ± 2.47 (n=5) | 13.12 ± 7.41 (n=5) | 0.957 ± 0.049 (n=5) |
| Vapor composition y | 0.0495 ± 0.0176 (n=5) | 0.0731 ± 0.0286 (n=5) | 0.943 ± 0.040 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### state_temperature_low_extrapolation — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 3.03 ± 1.14 (n=5) | 4.21 ± 1.53 (n=5) | 0.963 ± 0.029 (n=5) |
| Vapor composition y | 0.0297 ± 0.0085 (n=5) | 0.0441 ± 0.0109 (n=5) | 0.986 ± 0.007 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

## Provenance and pooled diagnostics

- Pooled solver failure rate: 0.00000 ± 0.00000
- Pooled nonphysical rate: 0.00000 ± 0.00000
- Training commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Aggregation commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Formal summary: `results/state_temperature_low_extrapolation/metrics_summary.csv`
- Per-seed predictions: `results/state_temperature_low_extrapolation/seed_*/predictions.csv`

These values are generated from committed fixed splits and should not be replaced by smoke or diagnostic runs.
