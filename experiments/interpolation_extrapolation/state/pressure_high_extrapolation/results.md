# state_pressure_high_extrapolation

Status: **completed formal five-seed experiment**.

- Seeds: `0,1,2,3,4`

## Task-resolved predictive performance

### state_pressure_high_extrapolation — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 26.99 ± 7.49 (n=5) | 55.00 ± 16.09 (n=5) | 0.794 ± 0.096 (n=5) |
| Vapor composition y | 0.0412 ± 0.0118 (n=5) | 0.0566 ± 0.0142 (n=5) | 0.971 ± 0.012 (n=5) |

Valid coverage: 0.9993 ± 0.0015.

### state_pressure_high_extrapolation — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 4.96 ± 1.24 (n=5) | 6.34 ± 1.51 (n=5) | 0.865 ± 0.057 (n=5) |
| Vapor composition y | 0.0678 ± 0.0202 (n=5) | 0.0936 ± 0.0252 (n=5) | 0.883 ± 0.050 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

## Provenance and pooled diagnostics

- Pooled solver failure rate: 0.00038 ± 0.00086
- Pooled nonphysical rate: 0.00000 ± 0.00000
- Training commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Aggregation commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Formal summary: `results/state_pressure_high_extrapolation/metrics_summary.csv`
- Per-seed predictions: `results/state_pressure_high_extrapolation/seed_*/predictions.csv`

These values are generated from committed fixed splits and should not be replaced by smoke or diagnostic runs.
