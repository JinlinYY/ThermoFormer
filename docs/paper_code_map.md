# Manuscript-to-code map

| Manuscript Methods subsection | Stable module interface | Primary implementation |
|---|---|---|
| ThermoFormer formulation | `src.thermoformer.model` | `src/model.py` |
| Multiview molecular representation | `src.thermoformer.features` | `src/representation.py` |
| Permutation-equivariant interaction encoding | `src.thermoformer.model` | `ThermoFormer._structural_context` and Transformer layers |
| State-conditioned molecular interactions | `src.thermoformer.model` | FiLM, mixture token, and symmetric pair potential |
| Excess Gibbs energy and activity coefficients | `src.thermoformer.model` | `ThermoFormer.forward` |
| Pure-component vapor pressure | `src.thermoformer.thermodynamics` | `src/pure_properties.py` and `PureVaporPressure` |
| Differentiable VLE reconstruction | `src.thermoformer.thermodynamics` | `src/thermo.py` |
| Supervised and fugacity-constrained optimization | `src.thermoformer.training` | `src/training.py`, `src/losses.py`, and `src/physics_finetuning.py` |

| Manuscript Results subsection | Experiment registry | Aggregate report |
|---|---|---|
| Predictive performance and generalization | `experiments/predictive_performance/`, `experiments/interpolation_extrapolation/`, `experiments/comparison/binary_to_ternary_generalization/` | `reports/c1_fugacity_generalization_report.md` |
| Ablation analysis | `experiments/multiview/` and `experiments/physics_finetuning/` | `reports/c1_ablation_overall_binary_ternary.md` |
| Learned thermodynamic interactions | `experiments/explainability/c1_final/` | `analysis/interpretability/reports/interpretability_report.md` |
| Autonomous separation design | Not registered | Not evaluated |
