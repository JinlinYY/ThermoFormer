# Contributing to ThermoFormer

Contributions should preserve the paper-aligned experiment contract.

## Before opening a change

1. Read the relevant guide in `docs/` and the experiment entry in
   `docs/reproducibility/article_experiment_index.md`.
2. Keep scientific inputs, configurations, checkpoints, and result records in
   their existing top-level directories.
3. Do not commit credentials, machine-specific absolute paths, runtime caches,
   or unreviewed generated outputs.
4. Add or update a focused regression test when a public interface or a
   scientific calculation changes.

## Validation

Run the repository checks from the root:

```bash
python scripts/run_experiments.py verify
python -m pytest -q
```

For changes to a registered study, also run its `--dry-run` command and record
the configuration and dataset identity in the associated experiment guide.
Results must retain explicit failure or unavailable states; do not fill missing
parameters or failed solver outputs with fabricated values.
