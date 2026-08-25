# Final C1 binary-only evaluation

All values are mean ± standard deviation across seeds 0--4. Checkpoint selection uses validation only; test data are evaluated afterward.

| Evaluation setting | subset | task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | n |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Binary train -> binary test | all | isobaric (molecules,P,x → T,y) | 2.45 ± 0.15 K | 4.29 ± 0.52 K | 0.979 ± 0.008 | 0.0284 ± 0.0043 | 0.0499 ± 0.0058 | 0.975 ± 0.005 | 5 |
| Binary train -> binary test | all | isothermal (molecules,T,x → P,y) | 8.98 ± 5.20 kPa | 20.58 ± 11.95 kPa | 0.968 ± 0.027 | 0.0262 ± 0.0056 | 0.0476 ± 0.0120 | 0.978 ± 0.010 | 5 |

The binary-only C1 model provides the first overall-performance row of manuscript Table 1.

Machine-readable source: `results/performance/c1_fugacity_generalization_by_task.csv` (SHA-256 `2aebedb9798f5556b5480bd69d06752bf6a48cfc335d46fcd61b2a7649c1452c`).
