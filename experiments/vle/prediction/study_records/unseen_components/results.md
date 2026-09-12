# Unseen-component generalization

All values are mean ± standard deviation across seeds 0--4. Checkpoint selection uses validation only; test data are evaluated afterward.

| Evaluation setting | subset | task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | n |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Unseen component | all | isobaric (molecules,P,x → T,y) | 36.45 ± 1.49 K | 46.99 ± 1.94 K | 0.456 ± 0.044 | 0.1191 ± 0.0062 | 0.1659 ± 0.0047 | 0.792 ± 0.012 | 5 |
| Unseen component | all | isothermal (molecules,T,x → P,y) | 32.39 ± 11.31 kPa | 68.32 ± 15.80 kPa | 0.494 ± 0.242 | 0.1057 ± 0.0179 | 0.1694 ± 0.0250 | 0.768 ± 0.066 | 5 |

Unseen-component prediction is the clearest limitation of the current model and is substantially harder than within-system state generalization.

Machine-readable source: `experiments/vle/prediction/summary/c1_fugacity_generalization_by_task.csv` (SHA-256 `2aebedb9798f5556b5480bd69d06752bf6a48cfc335d46fcd61b2a7649c1452c`).
