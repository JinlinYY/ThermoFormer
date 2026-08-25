# Manuscript-to-code map

This document maps the current `ThermoFormer.pdf` manuscript to one canonical
implementation and one canonical result source per scientific item. Historical
alternatives are retained under `archive/` and are not manuscript evidence.

## Methods

| Manuscript subsection | Public interface | Primary implementation |
|---|---|---|
| ThermoFormer formulation | `src.thermoformer.ThermoFormer` | `src/thermoformer/models/thermoformer.py` |
| Multiview molecular representation | `build_molecular_features` | `src/thermoformer/features/` |
| Permutation-equivariant multicomponent interaction encoding | `ThermoFormer` | `src/thermoformer/models/interaction.py` and `models/thermoformer.py` |
| State-conditioned molecular interaction learning | `ThermoFormer` | FiLM, mixture token, and symmetric pair potential in `models/thermoformer.py` |
| Excess Gibbs energy and activity coefficients | `ThermoFormer` | `thermodynamics/activity_coefficients.py` |
| Pure-component vapor-pressure branch | `PurePropertyCatalog` | `models/vapor_pressure.py` and `thermodynamics/vapor_pressure.py` |
| Differentiable VLE reconstruction | `solve_isothermal`, `solve_isobaric` | `thermodynamics/vle_solver.py` |
| Supervised and fugacity-constrained optimization | `train_supervised`, `finetune_with_fugacity` | `training/supervised.py`, `training/fugacity_finetuning.py`, and `training/losses.py` |

## Results

| Manuscript item | Canonical experiment or analysis | Machine-readable source | Published artifact |
|---|---|---|---|
| Dataset construction and coverage - Figure 1 | `analysis/dataset_distribution/` | tables under `analysis/dataset_distribution/results/` | `analysis/dataset_distribution/figures/Figure_dataset_overview_v3.{png,pdf,svg}` |
| Predictive performance and generalization - Table 1 | `experiments/predictive_performance/` | `results/performance/c1_fugacity_generalization_by_task.csv` | `reports/c1_fugacity_generalization_report.md` |
| Machine-learning and thermodynamic-model comparison | `experiments/comparisons/` | not evaluated | not reported |
| Ablation analysis - Table 2 | `experiments/ablations/` | `results/c1_ablation/overall_binary_ternary_metrics.csv` and the fugacity stage summary | `reports/c1_ablation_overall_binary_ternary.md` |
| Learned multicomponent thermodynamics - Figure 2 | `experiments/interpretability/` | frozen source record under `analysis/manuscript_figures/` | `analysis/manuscript_figures/Figure_2_interpretability.png` |
| Autonomous separation design | `experiments/separation_design/` | not evaluated | not reported |

Table 1 contains 15 registered protocols: binary-only overall prediction, joint
binary/ternary prediction, six state-generalization protocols, unseen-component
prediction, and six binary-to-ternary settings. Table 2 contains five molecular
representations, three interaction architectures, and the supervised/raw
fine-tuned/validation-selected fugacity comparison.
