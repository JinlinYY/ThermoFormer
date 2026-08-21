# state_pressure_high_extrapolation

Status: **completed formal five-seed experiment**.

- Seeds: `0,1,2,3,4`
- Point-wise pressure: MAE 26.995 ± 7.489 (n=5) kPa; RMSE 55.002 ± 16.094 (n=5) kPa; R² 0.7944 ± 0.0958 (n=5).
- Point-wise temperature: MAE 4.959 ± 1.240 (n=5) K; RMSE 6.343 ± 1.510 (n=5) K; R² 0.8647 ± 0.0571 (n=5).
- Point-wise vapor composition: MAE 0.0519 ± 0.0141 (n=5); RMSE 0.0738 ± 0.0187 (n=5); R² 0.9441 ± 0.0224 (n=5).
- Valid coverage: 0.99962 ± 0.00086
- Solver failure rate: 0.00038 ± 0.00086
- Training commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Aggregation commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Formal summary: `results/state_pressure_high_extrapolation/metrics_summary.csv`
- Per-seed predictions: `results/state_pressure_high_extrapolation/seed_*/predictions.csv`

These values are generated from committed fixed splits and should not be replaced by smoke or diagnostic runs.
