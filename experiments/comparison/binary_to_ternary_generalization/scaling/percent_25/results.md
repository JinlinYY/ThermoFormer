# binary_to_ternary_scale_0.25

Status: **completed formal five-seed experiment**.

- Seeds: `0,1,2,3,4`

## Task-resolved predictive performance

### binary_to_ternary_scale_0.25 — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 5.11 ± 3.60 (n=5) | 6.38 ± 4.37 (n=5) | 0.679 ± 0.470 (n=5) |
| Vapor composition y | 0.0498 ± 0.0134 (n=5) | 0.0637 ± 0.0169 (n=5) | 0.912 ± 0.049 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### binary_to_ternary_scale_0.25 — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 5.31 ± 1.08 (n=5) | 6.33 ± 1.26 (n=5) | 0.955 ± 0.012 (n=5) |
| Vapor composition y | 0.0878 ± 0.0158 (n=5) | 0.1245 ± 0.0128 (n=5) | 0.702 ± 0.086 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

## Provenance and pooled diagnostics

- Pooled solver failure rate: 0.00000 ± 0.00000
- Pooled nonphysical rate: 0.00000 ± 0.00000
- Training commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Aggregation commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Formal summary: `results/binary_to_ternary_scale_0.25/metrics_summary.csv`
- Per-seed predictions: `results/binary_to_ternary_scale_0.25/seed_*/predictions.csv`

These values are generated from committed fixed splits and should not be replaced by smoke or diagnostic runs.
