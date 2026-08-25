# state_composition_interpolation

Status: **completed formal five-seed experiment**.

- Seeds: `0,1,2,3,4`

## Task-resolved predictive performance

### state_composition_interpolation — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 4.45 ± 1.03 (n=5) | 10.05 ± 2.37 (n=5) | 0.983 ± 0.008 (n=5) |
| Vapor composition y | 0.0301 ± 0.0065 (n=5) | 0.0427 ± 0.0096 (n=5) | 0.975 ± 0.012 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### state_composition_interpolation — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 1.83 ± 0.45 (n=5) | 2.49 ± 0.58 (n=5) | 0.990 ± 0.005 (n=5) |
| Vapor composition y | 0.0338 ± 0.0077 (n=5) | 0.0501 ± 0.0080 (n=5) | 0.964 ± 0.012 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

## Provenance and pooled diagnostics

- Pooled solver failure rate: 0.00000 ± 0.00000
- Pooled nonphysical rate: 0.00000 ± 0.00000
- Training commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Aggregation commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Formal summary: `results/state_composition_interpolation/metrics_summary.csv`
- Per-seed predictions: `results/state_composition_interpolation/seed_*/predictions.csv`

These values are generated from committed fixed splits and should not be replaced by smoke or diagnostic runs.
