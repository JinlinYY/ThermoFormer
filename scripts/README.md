# Research entry points

The scripts directory contains supported repository-level commands. Scientific
implementation belongs in `src/`; scripts parse arguments and call those module
interfaces.

## Data and protocol preparation

- `audit_dataset.py`: dataset filtering and ternary-subsystem audit.
- `generate_splits.py`: registered group-disjoint split generation.
- `validate_splits.py`: complete split-matrix validation.

## Training and evaluation

- `train_thermoformer.py`: configuration-driven training entry point.
- `run_paper_experiment.py`: one registered protocol and seed.
- `run_paper_suite.py`: registered multi-seed supervised campaigns.
- `run_c1_physics_finetune.py`: C1 fugacity-constrained fine-tuning.
- `aggregate_results.py`: provenance-checked multi-seed aggregation.

## Ablation and interpretation

- `run_multiview_suite.py`: molecular-representation ablations.
- `run_chemical_attention_suite.py`: interaction-architecture ablations.
- `run_interpretability.py`: final C1 interpretation analyses.

## Report generation

- `build_c1_ablation_report.py`: retained `overall_binary_ternary` ablations.
- `build_c1_generalization_report.py`: final generalization campaign.

Archived one-time data-processing, diagnostic, and early reporting commands are
listed in `archive/legacy_code/README.md`.
