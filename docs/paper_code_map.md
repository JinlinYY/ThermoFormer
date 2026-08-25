# Manuscript-to-code map

| Manuscript Methods subsection | Public interface | Primary implementation |
|---|---|---|
| ThermoFormer formulation | `src.thermoformer.ThermoFormer` | `src/thermoformer/models/thermoformer.py` |
| Multiview molecular representation | `build_molecular_features` | `src/thermoformer/features/` |
| Permutation-equivariant interaction encoding | `ThermoFormer` | `src/thermoformer/models/interaction.py` and `models/thermoformer.py` |
| State-conditioned molecular interactions | `ThermoFormer` | FiLM, mixture token, and symmetric pair potential in `models/thermoformer.py` |
| Excess Gibbs energy and activity coefficients | `ThermoFormer` | `thermodynamics/activity_coefficients.py` |
| Pure-component vapor pressure | `PurePropertyCatalog` | `models/vapor_pressure.py` and `thermodynamics/vapor_pressure.py` |
| Differentiable VLE reconstruction | `solve_isothermal`, `solve_isobaric` | `thermodynamics/vle_solver.py` |
| Supervised optimization | `train_supervised` | `training/supervised.py` and `training/losses.py` |
| Fugacity-constrained fine-tuning | `finetune_with_fugacity` | `training/fugacity_finetuning.py` |

| Manuscript Results subsection | Experiment registry | Aggregate report |
|---|---|---|
| Predictive performance and generalization | `experiments/predictive_performance/` | `reports/c1_fugacity_generalization_report.md` |
| Ablation analysis | `experiments/ablations/` | `reports/c1_ablation_overall_binary_ternary.md` |
| Learned thermodynamic interactions | `experiments/interpretability/` | `analysis/interpretability/reports/interpretability_report.md` |
| Model comparisons | `experiments/comparisons/` | Not evaluated |
| Autonomous separation design | `experiments/separation_design/` | Not evaluated |
