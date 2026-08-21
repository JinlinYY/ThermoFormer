# binary_to_ternary_zero_shot

Status: **completed formal five-seed experiment**.

- Seeds: `0,1,2,3,4`

## Task-resolved predictive performance

### binary_to_ternary_zero_shot — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 5.03 ± 2.90 (n=5) | 5.86 ± 3.12 (n=5) | 0.749 ± 0.287 (n=5) |
| Vapor composition y | 0.0318 ± 0.0031 (n=5) | 0.0409 ± 0.0048 (n=5) | 0.966 ± 0.011 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### binary_to_ternary_zero_shot — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 5.58 ± 2.08 (n=5) | 6.24 ± 2.08 (n=5) | 0.950 ± 0.030 (n=5) |
| Vapor composition y | 0.0828 ± 0.0153 (n=5) | 0.1225 ± 0.0164 (n=5) | 0.714 ± 0.089 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

## Provenance and pooled diagnostics

- Pooled solver failure rate: 0.00000 ± 0.00000
- Pooled nonphysical rate: 0.00000 ± 0.00000
- Training commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Aggregation commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Formal summary: `results/binary_to_ternary_zero_shot/metrics_summary.csv`
- Per-seed predictions: `results/binary_to_ternary_zero_shot/seed_*/predictions.csv`

These values are generated from committed fixed splits and should not be replaced by smoke or diagnostic runs.
