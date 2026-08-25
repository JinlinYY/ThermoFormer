# Manuscript experiment map

This directory is a navigation layer. It does not duplicate configurations or
results, because formal manifests bind the original experiment paths.

| Manuscript Results subsection | Registered experiments | Status |
|---|---|---|
| Dataset construction and coverage | `analysis/dataset_distribution/` and `scripts/audit_dataset.py` | Evaluated |
| Overall predictive performance | `experiments/predictive_performance/` | Evaluated |
| Thermodynamic-state generalization | `experiments/interpolation_extrapolation/state/` | Evaluated |
| Unseen-component generalization | `experiments/interpolation_extrapolation/chemical_space/unseen_component/` | Evaluated |
| Binary-to-ternary transfer | `experiments/comparison/binary_to_ternary_generalization/` | Evaluated |
| Machine-learning comparison | -- | Not evaluated |
| Thermodynamic-model comparison | `experiments/comparison/ideal_activity/` provides one reference | Incomplete |
| Molecular-representation ablation | `experiments/multiview/representations/` | Evaluated |
| Interaction-architecture ablation | `experiments/multiview/chemical_attention/` | Evaluated |
| Fugacity fine-tuning ablation | `experiments/physics_finetuning/c1_three_view_vanilla_fugacity/` | Evaluated |
| Learned thermodynamic interactions | `experiments/explainability/c1_final/` | Evaluated |
| Autonomous separation design | -- | Not evaluated |

Only rows marked **Evaluated** support quantitative claims. Incomplete or
unevaluated sections remain explicit so that future experiments can be added
without changing the meaning of the published evidence.
