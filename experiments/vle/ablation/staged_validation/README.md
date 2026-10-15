# Stage 0–3 validation-only physical diagnostics

VLE / Controlled ablations

Validation-only recomputation from the original validation-selected Stage 0–3 checkpoints. No retraining, checkpoint reselection, or test-set evaluation.

## Protocol and results

Configuration: `configs/vle/ablation/staged_validation.json`.

- [experiments/vle/ablation/staged_validation](.)
- [models/vle/prediction/vle_overall_binary_ternary](../../../../models/vle/prediction/vle_overall_binary_ternary)

Inspect the command with `python scripts/run_experiments.py show vle.ablation.staged_validation`.
