# Model checkpoints and manuscript results

This document identifies the model weights used for each reported manuscript
result. Paths are relative to the repository root. All formal checkpoints use
seeds `0, 1, 2, 3, 4` and are stored with Git LFS.

## Checkpoint roles

- **Stage 1** is the validation-best checkpoint from supervised training.
- **Stage 2** is the validation-best checkpoint after 10 epochs of partial
  fine-tuning with the teacher-forced fugacity-equilibrium loss.
- **Final** is selected independently for each seed using validation data only.
  It may therefore contain either the Stage-1 or Stage-2 state. Test data are
  evaluated only after this choice.

For a fugacity-fine-tuned protocol `<protocol>` and seed `<n>`:

```text
checkpoints/experiments/physics_finetuning/c1_three_view_vanilla_fugacity/
  c1_three_view_vanilla_fugacity_finetune.on.<protocol>/seed_<n>/
    best_model.pt          # validation-selected final state used in Table 1
    stage2_best_model.pt   # raw Stage-2 state used in the Stage-2 ablation row
```

`best_model.pt` is a newly serialized final checkpoint payload. When validation
selects Stage 1, its model state is the Stage-1 state even though the file is not
byte-identical to the original Stage-1 checkpoint because its metadata records
the two-stage experiment.

The authoritative per-seed record is:

```text
results/experiments/physics_finetuning/c1_three_view_vanilla_fugacity/
  c1_three_view_vanilla_fugacity_finetune.on.<protocol>/seed_<n>/manifest.json
```

Its `artifacts.checkpoint.sha256` identifies the final weight file, while
`stage_comparison.json` records `selected_stage`, the Stage-1 source checkpoint,
and the validation losses used for selection.

## Table 1: predictive performance and generalization

Every Table-1 value is computed from the validation-selected `best_model.pt`
files in the fugacity-fine-tuning directory above. The consolidated numerical
source is `results/performance/c1_fugacity_generalization_by_task.csv`; the
per-protocol source is the corresponding `metrics_summary.csv` beside each
protocol's aggregate manifest.

`S1` and `S2` below indicate which state is contained in the final checkpoint
for seeds `0, 1, 2, 3, 4`, in that order.

| Manuscript evaluation setting | Protocol identifier | Selected stages for seeds 0--4 |
|---|---|---|
| Binary train -> binary test | `overall_binary` | S2, S2, S1, S2, S2 |
| Binary + ternary train -> binary + ternary test | `overall_binary_ternary` | S2, S1, S2, S2, S1 |
| Composition interpolation | `state_composition_interpolation` | S2, S2, S2, S2, S2 |
| Composition-edge extrapolation | `state_composition_edge_extrapolation` | S2, S2, S2, S2, S2 |
| Low-temperature extrapolation | `state_temperature_low_extrapolation` | S1, S2, S1, S2, S2 |
| High-temperature extrapolation | `state_temperature_high_extrapolation` | S2, S2, S2, S2, S2 |
| Low-pressure extrapolation | `state_pressure_low_extrapolation` | S2, S2, S2, S2, S2 |
| High-pressure extrapolation | `state_pressure_high_extrapolation` | S2, S2, S2, S2, S2 |
| Unseen-component generalization | `unseen_component` | S2, S1, S1, S1, S2 |
| Binary -> ternary, zero-shot | `binary_to_ternary_zero_shot` | S2, S2, S1, S2, S2 |
| Binary -> ternary, 5% ternary systems | `binary_to_ternary_scale_0.05` | S2, S1, S2, S1, S2 |
| Binary -> ternary, 10% ternary systems | `binary_to_ternary_scale_0.1` | S2, S1, S2, S1, S2 |
| Binary -> ternary, 25% ternary systems | `binary_to_ternary_scale_0.25` | S2, S1, S2, S1, S2 |
| Binary -> ternary, 50% ternary systems | `binary_to_ternary_scale_0.5` | S2, S1, S2, S2, S2 |
| Binary -> ternary, 100% ternary systems | `binary_to_ternary_scale_1` | S2, S2, S2, S2, S2 |

The Stage-1 checkpoint pattern is
`checkpoints/<protocol>/seed_<n>/best_model.pt` for all rows except
`overall_binary_ternary`. Its Stage-1 source is the C1 checkpoint described in
the next section.

## Table 2: ablation analysis

### Molecular representation and interaction architecture

These rows use validation-best supervised checkpoints; no fugacity fine-tuning
is applied. Each path pattern contains five checkpoints, one for every seed.

| Table-2 model | Checkpoint pattern |
|---|---|
| C0: Uni-Mol v2 + vanilla Transformer | `checkpoints/multiview/chemical_attention/formal/c0_current_vanilla.on.overall_binary_ternary/seed_<n>/best_model.pt` |
| V1: RDKit descriptors only | `checkpoints/multiview/formal/v1_rdkit_only.on.overall_binary_ternary/seed_<n>/best_model.pt` |
| V3: functional groups only | `checkpoints/multiview/predictive/v3_functional_group_only.on.overall_binary_ternary/seed_<n>/best_model.pt` |
| V4: RDKit + Uni-Mol v2 | `checkpoints/multiview/predictive/v4_rdkit_unimol_naive.on.overall_binary_ternary/seed_<n>/best_model.pt` |
| C1: RDKit + Uni-Mol v2 + functional groups + vanilla Transformer | `checkpoints/multiview/chemical_attention/formal/c1_three_view_vanilla.on.overall_binary_ternary/seed_<n>/best_model.pt` |
| C2: chemical-biased Transformer + context pair interaction | `checkpoints/multiview/chemical_attention/formal/c2_chemical_bias_full.on.overall_binary_ternary/seed_<n>/best_model.pt` |
| C3: context pair interaction without attention bias | `checkpoints/multiview/chemical_attention/formal/c3_no_pair_bias.on.overall_binary_ternary/seed_<n>/best_model.pt` |

The machine-readable values for these rows are in
`results/c1_ablation/overall_binary_ternary_metrics.csv`. Its input manifest,
`results/c1_ablation/report_manifest.json`, records the aggregate manifest and
metrics-summary SHA-256 digest for every variant.

### Fugacity-loss fine-tuning

The fugacity ablation uses the `overall_binary_ternary` protocol:

| Table-2 row | Weight file used |
|---|---|
| Stage 1: supervised C1 | `checkpoints/multiview/chemical_attention/formal/c1_three_view_vanilla.on.overall_binary_ternary/seed_<n>/best_model.pt` |
| Stage 2: raw fugacity-fine-tuned C1 | `checkpoints/experiments/physics_finetuning/c1_three_view_vanilla_fugacity/c1_three_view_vanilla_fugacity_finetune.on.overall_binary_ternary/seed_<n>/stage2_best_model.pt` |
| Final validation-selected C1 | `checkpoints/experiments/physics_finetuning/c1_three_view_vanilla_fugacity/c1_three_view_vanilla_fugacity_finetune.on.overall_binary_ternary/seed_<n>/best_model.pt` |

For the final row, validation selected `S2, S1, S2, S2, S1` for seeds 0--4.
The corresponding aggregate is stored at:

```text
results/experiments/physics_finetuning/c1_three_view_vanilla_fugacity/
  c1_three_view_vanilla_fugacity_finetune.on.overall_binary_ternary/
  metrics_summary.csv
```

## Figure 2: learned multicomponent thermodynamics

The exact six-panel manuscript figure is
`analysis/manuscript_figures/Figure_2_interpretability.png`, with its frozen
source record in `Figure_2_interpretability.source.json`.

The figure concerns the final C1 model family, but the current repository does
not contain the original six-panel assembly program or a source manifest that
binds individual panels to checkpoint SHA-256 digests. Consequently, no
seed-specific checkpoint is claimed here as the verifiable source of the exact
published Figure 2. The archived four-panel C1 interpretability analysis did use
the five validation-selected `overall_binary_ternary` final checkpoints listed
above, but it is a scientifically different artifact and must not be substituted
for Figure 2.

## Loading a manuscript checkpoint

Materialize Git-LFS files after cloning:

```bash
git lfs install
git lfs pull
```

Use the validation-selected `best_model.pt` for reproducing Table-1 final
metrics. Use `stage2_best_model.pt` only when reproducing the raw Stage-2 row in
Table 2. Before inference, verify the file against its per-seed manifest; the
manifest also binds the dataset, split, configuration, feature definitions, and
software environment used by that checkpoint.

Checkpoint directories not listed in this document belong to diagnostic,
exploratory, or superseded studies and are not sources for the current
manuscript tables.
