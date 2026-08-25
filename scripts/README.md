# Research entry points

The scripts directory contains supported research commands. Scientific
implementation belongs in `src/`; scripts expose those methods to experiments.

## Data and protocol preparation

- `data/prepare_dataset.py`: public dataset-audit entry point.
- `audit_dataset.py`: dataset filtering and ternary-subsystem audit.
- `generate_splits.py`: registered system-disjoint and within-system state splits.
- `validate_splits.py`: complete split-matrix validation.

## Training and evaluation

- `train.py`: configuration-driven training entry point.
- `run_experiment.py`: one registered protocol and seed.
- `evaluate.py`: evaluate one checkpoint on a compatible registered split.
- `run_paper_suite.py`: registered multi-seed supervised campaigns.
- `run_c1_physics_finetune.py`: C1 fugacity-constrained fine-tuning.
- `aggregate_results.py`: consistency-checked multi-seed statistical aggregation.

## Ablation and interpretation

- `run_multiview_suite.py`: molecular-representation ablations.
- `run_chemical_attention_suite.py`: interaction-architecture ablations.
- `run_interpretability.py`: final C1 interpretation analyses.

## Report generation

- `build_reports.py`: unified generalization and ablation report command.
- `reproduce/`: manuscript-section reproduction commands.
- `build_c1_ablation_report.py`: retained `overall_binary_ternary` ablations.
- `build_c1_generalization_report.py`: final generalization campaign.

Archived one-time data-processing, diagnostic, and early reporting commands are
listed in `archive/legacy_code/README.md`.
