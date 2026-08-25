# Final C1 overall binary/ternary evaluation

All values are mean ± standard deviation across seeds 0--4. Checkpoint selection uses validation only; test data are evaluated afterward.

| Evaluation setting | subset | task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | n |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Binary+ternary train -> joint test | binary | isobaric (molecules,P,x → T,y) | 2.45 ± 0.31 K | 4.23 ± 0.79 K | 0.979 ± 0.010 | 0.0293 ± 0.0055 | 0.0513 ± 0.0079 | 0.973 ± 0.008 | 5 |
| Binary+ternary train -> joint test | ternary | isobaric (molecules,P,x → T,y) | 1.41 ± 0.61 K | 1.95 ± 1.00 K | 0.979 ± 0.032 | 0.0317 ± 0.0181 | 0.0536 ± 0.0369 | 0.919 ± 0.079 | 4 |
| Binary+ternary train -> joint test | binary | isothermal (molecules,T,x → P,y) | 8.68 ± 4.71 kPa | 19.55 ± 10.47 kPa | 0.971 ± 0.024 | 0.0265 ± 0.0058 | 0.0470 ± 0.0112 | 0.979 ± 0.009 | 5 |
| Binary+ternary train -> joint test | ternary | isothermal (molecules,T,x → P,y) | 1.85 ± 0.27 kPa | 2.44 ± 0.31 kPa | 0.984 ± 0.004 | 0.0168 ± 0.0052 | 0.0239 ± 0.0082 | 0.991 ± 0.006 | 4 |

The joint model retains strong binary performance and provides accurate ternary state predictions; ternary task availability is four seeds for several outputs.

Machine-readable source: `results/performance/c1_fugacity_generalization_by_task.csv` (SHA-256 `2aebedb9798f5556b5480bd69d06752bf6a48cfc335d46fcd61b2a7649c1452c`).
