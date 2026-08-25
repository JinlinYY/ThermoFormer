# binary_to_ternary_scale_0.5

Status: **completed formal five-seed experiment**.

- Seeds: `0,1,2,3,4`

## Task-resolved predictive performance

### binary_to_ternary_scale_0.5 — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 5.18 ± 2.38 (n=5) | 6.35 ± 2.79 (n=5) | 0.778 ± 0.166 (n=5) |
| Vapor composition y | 0.0532 ± 0.0288 (n=5) | 0.0738 ± 0.0372 (n=5) | 0.882 ± 0.101 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### binary_to_ternary_scale_0.5 — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 5.99 ± 3.10 (n=5) | 6.86 ± 3.51 (n=5) | 0.942 ± 0.050 (n=5) |
| Vapor composition y | 0.0924 ± 0.0245 (n=5) | 0.1294 ± 0.0228 (n=5) | 0.670 ± 0.152 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

## Provenance and pooled diagnostics

- Pooled solver failure rate: 0.00000 ± 0.00000
- Pooled nonphysical rate: 0.00000 ± 0.00000
- Training commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Aggregation commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Formal summary: `results/binary_to_ternary_scale_0.5/metrics_summary.csv`
- Per-seed predictions: `results/binary_to_ternary_scale_0.5/seed_*/predictions.csv`

These values are generated from committed fixed splits and should not be replaced by smoke or diagnostic runs.
