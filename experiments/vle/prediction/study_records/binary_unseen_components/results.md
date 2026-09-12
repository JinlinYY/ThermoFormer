# Binary-only unseen-component generalization

All values are mean ± standard deviation across seeds 0--4. Training, validation, and test contain binary VLE rows only. Checkpoint selection uses validation data; test data are evaluated afterward.

| Evaluation setting | Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | Solver failure rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Unseen components | molecules,P,x → T,y | 34.27 ± 3.34 K | 46.54 ± 3.06 K | 0.440 ± 0.043 | 0.1087 ± 0.0081 | 0.1593 ± 0.0074 | 0.802 ± 0.019 | 0.0000 ± 0.0000 |
| Unseen components | molecules,T,x → P,y | 16.34 ± 2.44 kPa | 47.88 ± 9.22 kPa | 0.771 ± 0.093 | 0.0678 ± 0.0106 | 0.1247 ± 0.0231 | 0.874 ± 0.048 | 0.0000 ± 0.0000 |

Validation-selected checkpoints: stage0=3, stage2=1, stage3=1

The model uses Stage 1 direct GE/RT and ln(gamma) supervision, Stage 2 joint VLE supervision, and Stage 3 ten-epoch fugacity fine-tuning.
