# unseen_component

Status: **completed formal five-seed experiment**.

- Seeds: `0,1,2,3,4`

## Task-resolved predictive performance

### unseen_component — Isothermal P–x–y

- Known inputs: **Molecules, T, x**.
- Joint prediction: **Bubble pressure P and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble pressure P (kPa) | 27.40 ± 0.87 (n=5) | 71.92 ± 5.21 (n=5) | 0.460 ± 0.076 (n=5) |
| Vapor composition y | 0.0789 ± 0.0180 (n=5) | 0.1229 ± 0.0244 (n=5) | 0.876 ± 0.051 (n=5) |

Valid coverage: 0.9975 ± 0.0030.

### unseen_component — Isobaric T–x–y

- Known inputs: **Molecules, P, x**.
- Joint prediction: **Bubble temperature T and vapor composition y**.

| Predicted quantity | MAE | RMSE | R² |
|---|---:|---:|---:|
| Bubble temperature T (K) | 37.87 ± 3.63 (n=5) | 48.63 ± 4.10 (n=5) | 0.415 ± 0.098 (n=5) |
| Vapor composition y | 0.1266 ± 0.0194 (n=5) | 0.1708 ± 0.0237 (n=5) | 0.776 ± 0.065 (n=5) |

Valid coverage: 1.0000 ± 0.0000.

## Provenance and pooled diagnostics

- Pooled solver failure rate: 0.00172 ± 0.00211
- Pooled nonphysical rate: 0.00000 ± 0.00000
- Training commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Aggregation commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Formal summary: `results/unseen_component/metrics_summary.csv`
- Per-seed predictions: `results/unseen_component/seed_*/predictions.csv`

These values are generated from committed fixed splits and should not be replaced by smoke or diagnostic runs.
