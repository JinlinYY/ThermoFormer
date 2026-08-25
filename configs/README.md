# Configuration organization

Runnable experiment configurations are colocated with their experiment records
under `experiments/`. This keeps each `config.json`, `run.md`, and `results.md`
together and preserves the paths recorded by formal manifests.

This directory stores shared or frozen configuration declarations that are not
owned by one experiment leaf:

- `ablation/full_model_reference.yaml`: frozen reference metadata.
- `experiments/README.md`: configuration inheritance and snapshot conventions.

Configuration loading is strict: unknown sections, unknown fields, malformed
overrides, and inheritance cycles are rejected.
