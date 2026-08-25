# Configuration organization

Runnable experiment configurations are colocated with their scientific records
under `experiments/`. Each JSON or YAML configuration is accompanied by the
corresponding command and reported results.

This directory stores shared configuration declarations:

- `ablation/full_model_reference.yaml`: full-model reference definition.
- `experiments/README.md`: configuration inheritance conventions.

Configuration loading is strict: unknown sections, unknown fields, malformed
overrides, and inheritance cycles are rejected.

The manuscript-facing inheritance chain is:

- `model/c1_three_view_vanilla.yaml`: final molecular representation and architecture;
- `training/supervised.yaml`: Stage-1 supervised training;
- `training/fugacity_finetuning.yaml`: validation-gated 10-epoch Stage 2;
- `protocols/*.yaml`: protocol-family entry points.

YAML configurations are parsed with `PyYAML`; JSON is also supported.
