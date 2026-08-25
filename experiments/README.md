# ThermoFormer manuscript experiment registry

The active registry follows the Results section of the current manuscript. Every
runnable experiment leaf contains `config.yaml` or `config.json`, `run.md`, and
`results.md`. Historical experiment records are retained under
`archive/legacy_code/experiment_records/`.

| Manuscript result | Active path | Status |
|---|---|---|
| Figure 1 - Dataset construction and coverage | `analysis/dataset_distribution/` | evaluated |
| Table 1 - Predictive performance and generalization | `predictive_performance/` | evaluated |
| Model comparisons | `comparisons/` | not evaluated |
| Table 2 - Molecular representation ablation | `ablations/molecular_representation/` | evaluated |
| Table 2 - Interaction architecture ablation | `ablations/interaction_architecture/` | evaluated |
| Table 2 - Fugacity fine-tuning ablation | `ablations/fugacity_finetuning/` | evaluated |
| Figure 2 - Learned multicomponent thermodynamics | `interpretability/` and `analysis/manuscript_figures/` | frozen published artifact |
| Autonomous separation design | `separation_design/` | not evaluated |

All evaluated predictive and ablation results report seeds 0--4 and use
validation-only checkpoint selection. Machine-readable values are generated from
committed aggregate artifacts; no values are inferred from the manuscript text.
