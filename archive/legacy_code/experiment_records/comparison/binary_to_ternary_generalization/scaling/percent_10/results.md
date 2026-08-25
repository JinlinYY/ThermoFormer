# binary_to_ternary_scale_0.1

Status: **completed formal five-seed experiment**.

- Seeds: `0,1,2,3,4`

## Task-resolved predictive performance

### binary_to_ternary_scale_0.1 — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 4.68 ± 3.70 (n=5) | 5.51 ± 4.26 (n=5) | 0.850 ± 0.142 (n=5) |
| Vapor composition y | 0.0500 ± 0.0353 (n=5) | 0.0655 ± 0.0476 (n=5) | 0.879 ± 0.180 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### binary_to_ternary_scale_0.1 — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 7.43 ± 4.13 (n=5) | 9.21 ± 5.75 (n=5) | 0.854 ± 0.198 (n=5) |
| Vapor composition y | 0.0883 ± 0.0248 (n=5) | 0.1296 ± 0.0204 (n=5) | 0.683 ± 0.088 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

## Provenance and pooled diagnostics

- Pooled solver failure rate: 0.00000 ± 0.00000
- Pooled nonphysical rate: 0.00000 ± 0.00000
- Training commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Aggregation commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Formal summary: `results/binary_to_ternary_scale_0.1/metrics_summary.csv`
- Per-seed predictions: `results/binary_to_ternary_scale_0.1/seed_*/predictions.csv`

These values are generated from committed fixed splits and should not be replaced by smoke or diagnostic runs.
