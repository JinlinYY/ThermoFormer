# Joint binary--ternary molecular and interaction ablation

VLE / Controlled ablations

All variants use identical release-data split assignments. The completed C1 main-benchmark result is reused; five unique variants are trained.

## Protocol and results

Configuration: `configs/vle/ablation/joint.json`.

- [configs/vle/ablation/studies/vle_joint](../../../../configs/vle/ablation/studies/vle_joint)
- [experiments/vle/ablation/joint](.)
- [experiments/vle/training_records/v1/three/results/thermoformer_vle_three_stage.on.vle_overall_binary_ternary](../../training_records/v1/three/results/thermoformer_vle_three_stage.on.vle_overall_binary_ternary)
- [models/vle/prediction/vle_overall_binary_ternary](../../../../models/vle/prediction/vle_overall_binary_ternary)

Inspect the command with `python scripts/run_experiments.py show vle.ablation.joint`.
