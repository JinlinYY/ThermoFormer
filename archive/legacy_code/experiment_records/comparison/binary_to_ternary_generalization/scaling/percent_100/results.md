# binary_to_ternary_scale_1

Status: **completed formal five-seed experiment**.

- Seeds: `0,1,2,3,4`

## Task-resolved predictive performance

### binary_to_ternary_scale_1 — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 4.52 ± 2.88 (n=5) | 5.50 ± 3.48 (n=5) | 0.848 ± 0.104 (n=5) |
| Vapor composition y | 0.0361 ± 0.0129 (n=5) | 0.0481 ± 0.0177 (n=5) | 0.951 ± 0.031 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

### binary_to_ternary_scale_1 — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 5.40 ± 1.10 (n=5) | 6.24 ± 0.76 (n=5) | 0.955 ± 0.012 (n=5) |
| Vapor composition y | 0.0817 ± 0.0113 (n=5) | 0.1220 ± 0.0114 (n=5) | 0.716 ± 0.084 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

## Provenance and pooled diagnostics

- Pooled solver failure rate: 0.00000 ± 0.00000
- Pooled nonphysical rate: 0.00000 ± 0.00000
- Training commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Aggregation commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Formal summary: `results/binary_to_ternary_scale_1/metrics_summary.csv`
- Per-seed predictions: `results/binary_to_ternary_scale_1/seed_*/predictions.csv`

These values are generated from committed fixed splits and should not be replaced by smoke or diagnostic runs.
