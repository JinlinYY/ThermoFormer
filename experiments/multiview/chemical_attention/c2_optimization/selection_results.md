# C2 validation-only optimization results

The candidates were selected on the committed validation partitions for seeds 0–2. No test prediction was generated in this stage. Training was data-supervised only.

The locked score is the mean of the six P/T/y MAE and RMSE ratios relative to the original C2 within each seed; lower is better.

| candidate | validation score | selected |
|---|---:|:---:|
| o0_original | 1.000000 |  |
| o1_shared_gate | 0.974941 |  |
| o2_headwise | 0.943981 | yes |
| o3_headwise_curriculum | 0.949509 |  |
| o4_headwise_curriculum_modality | 0.964396 |  |

Locked candidate: `o2_headwise`.
