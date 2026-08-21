# state_composition_edge_extrapolation

Status: **completed formal five-seed experiment**.

- Seeds: `0,1,2,3,4`

## Task-resolved predictive performance

### state_composition_edge_extrapolation — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 10.48 ± 3.35 (n=5) | 24.68 ± 7.10 (n=5) | 0.898 ± 0.059 (n=5) |
| Vapor composition y | 0.0275 ± 0.0072 (n=5) | 0.0551 ± 0.0143 (n=5) | 0.982 ± 0.010 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### state_composition_edge_extrapolation — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 5.75 ± 3.35 (n=5) | 7.81 ± 4.65 (n=5) | 0.918 ± 0.105 (n=5) |
| Vapor composition y | 0.0369 ± 0.0148 (n=5) | 0.0657 ± 0.0253 (n=5) | 0.971 ± 0.025 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

## Provenance and pooled diagnostics

- Pooled solver failure rate: 0.00000 ± 0.00000
- Pooled nonphysical rate: 0.00000 ± 0.00000
- Training commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Aggregation commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Formal summary: `results/state_composition_edge_extrapolation/metrics_summary.csv`
- Per-seed predictions: `results/state_composition_edge_extrapolation/seed_*/predictions.csv`

These values are generated from committed fixed splits and should not be replaced by smoke or diagnostic runs.
