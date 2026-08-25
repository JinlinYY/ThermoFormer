# binary_to_ternary_scale_0.05

Status: **completed formal five-seed experiment**.

- Seeds: `0,1,2,3,4`

## Task-resolved predictive performance

### binary_to_ternary_scale_0.05 — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 4.23 ± 1.58 (n=5) | 5.07 ± 1.67 (n=5) | 0.867 ± 0.070 (n=5) |
| Vapor composition y | 0.0358 ± 0.0074 (n=5) | 0.0490 ± 0.0116 (n=5) | 0.952 ± 0.020 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### binary_to_ternary_scale_0.05 — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 4.98 ± 2.10 (n=5) | 6.15 ± 2.49 (n=5) | 0.952 ± 0.027 (n=5) |
| Vapor composition y | 0.0840 ± 0.0135 (n=5) | 0.1215 ± 0.0133 (n=5) | 0.718 ± 0.083 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

## Provenance and pooled diagnostics

- Pooled solver failure rate: 0.00000 ± 0.00000
- Pooled nonphysical rate: 0.00000 ± 0.00000
- Training commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Aggregation commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Formal summary: `results/binary_to_ternary_scale_0.05/metrics_summary.csv`
- Per-seed predictions: `results/binary_to_ternary_scale_0.05/seed_*/predictions.csv`

These values are generated from committed fixed splits and should not be replaced by smoke or diagnostic runs.
