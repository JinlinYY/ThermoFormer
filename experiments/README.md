# ThermoFormer experiment registry

This registry contains the configurations, commands, and validated outputs used
to evaluate the manuscript model. Every runnable leaf contains `config.json`,
`run.md`, and `results.md`.

The paper-oriented navigation layer is
[`paper/README.md`](paper/README.md). It maps the scientific questions in the
Results section to the existing provenance-preserving experiment paths.

## Predictive performance and generalization

| Scientific question | Experiment family |
|---|---|
| Binary and joint binary/ternary performance | [`predictive_performance/`](predictive_performance/README.md) |
| Thermodynamic-state interpolation and extrapolation | [`interpolation_extrapolation/state/`](interpolation_extrapolation/state/README.md) |
| Unseen-component generalization | [`interpolation_extrapolation/chemical_space/`](interpolation_extrapolation/chemical_space/README.md) |
| Binary-to-ternary transfer | [`comparison/binary_to_ternary_generalization/`](comparison/binary_to_ternary_generalization/README.md) |

## Ablation analysis

All retained ablations use `overall_binary_ternary` with seeds 0--4.

| Scientific question | Experiment family |
|---|---|
| Molecular representation | [`multiview/representations/`](multiview/README.md) |
| Multicomponent interaction architecture | [`multiview/chemical_attention/`](multiview/chemical_attention/README.md) |
| Fugacity-constrained fine-tuning | [`physics_finetuning/c1_three_view_vanilla_fugacity/`](physics_finetuning/c1_three_view_vanilla_fugacity/README.md) |

The consolidated result is
[`../reports/c1_ablation_overall_binary_ternary.md`](../reports/c1_ablation_overall_binary_ternary.md).

## Interpretability

The final C1 interpretation study is registered under
[`explainability/c1_final/`](explainability/c1_final/README.md). It includes
grouped molecular-view attribution, pair-interaction analysis, and
thermodynamic sensitivity.

## Model comparisons and separation design

The ideal-activity reference is retained under
[`comparison/ideal_activity/`](comparison/ideal_activity/). Additional machine-
learning baselines, established thermodynamic-model comparisons, and autonomous
separation design have not been evaluated and therefore have no reported
performance values.
