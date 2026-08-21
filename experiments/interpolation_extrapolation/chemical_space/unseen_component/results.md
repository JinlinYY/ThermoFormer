# unseen_component

Status: **completed formal five-seed experiment**.

- Seeds: `0,1,2,3,4`
- Point-wise pressure: MAE 27.399 ± 0.866 (n=5) kPa; RMSE 71.918 ± 5.213 (n=5) kPa; R² 0.4600 ± 0.0764 (n=5).
- Point-wise temperature: MAE 37.873 ± 3.630 (n=5) K; RMSE 48.631 ± 4.101 (n=5) K; R² 0.4151 ± 0.0977 (n=5).
- Point-wise vapor composition: MAE 0.0931 ± 0.0180 (n=5); RMSE 0.1390 ± 0.0235 (n=5); R² 0.8455 ± 0.0550 (n=5).
- Valid coverage: 0.99828 ± 0.00211
- Solver failure rate: 0.00172 ± 0.00211
- Training commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Aggregation commit: `704458163ee2afd9e2c0a681ea4a670a287b6778`
- Formal summary: `results/unseen_component/metrics_summary.csv`
- Per-seed predictions: `results/unseen_component/seed_*/predictions.csv`

These values are generated from committed fixed splits and should not be replaced by smoke or diagnostic runs.
