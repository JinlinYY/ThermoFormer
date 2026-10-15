# NIST VLE/LLE dataset audit

DATA / Data curation and audit

Source records, registered dataset records, training-filtered records, and independent conditions must be reported separately.

## Protocol and results

Configuration: `configs/data/construction/audit.json`.

- [datasets/vle/manifest.json](../../../../datasets/vle/manifest.json)
- [datasets/vle/validation.json](../../../../datasets/vle/validation.json)
- [datasets/lle/manifest.json](../../../../datasets/lle/manifest.json)
- [experiments/data_quality/construction/dataset_distribution/reports](../dataset_distribution/reports)

Inspect the command with `python scripts/run_experiments.py show data.construction.audit`.
