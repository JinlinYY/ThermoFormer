# state_pressure_low_extrapolation

Status: **completed formal five-seed experiment**.

- Seeds: `0,1,2,3,4`

## Task-resolved predictive performance

### state_pressure_low_extrapolation — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 4.59 ± 1.30 (n=5) | 9.38 ± 1.35 (n=5) | 0.930 ± 0.021 (n=5) |
| Vapor composition y | 0.0673 ± 0.0289 (n=5) | 0.1011 ± 0.0407 (n=5) | 0.890 ± 0.080 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### state_pressure_low_extrapolation — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 5.33 ± 3.11 (n=5) | 6.83 ± 3.84 (n=5) | 0.853 ± 0.142 (n=5) |
| Vapor composition y | 0.0681 ± 0.0260 (n=5) | 0.0879 ± 0.0322 (n=5) | 0.906 ± 0.062 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

## Provenance and pooled diagnostics

- Pooled solver failure rate: 0.00000 ± 0.00000
- Pooled nonphysical rate: 0.00000 ± 0.00000
- Training commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Aggregation commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Formal summary: `results/state_pressure_low_extrapolation/metrics_summary.csv`
- Per-seed predictions: `results/state_pressure_low_extrapolation/seed_*/predictions.csv`

These values are generated from committed fixed splits and should not be replaced by smoke or diagnostic runs.
