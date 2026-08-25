# ThermoFormer experiment registry

This registry contains the configurations, commands, and validated outputs used
to evaluate the manuscript model. Every runnable leaf contains `config.json` or
`config.yaml`, together with `run.md` and `results.md`.

The paper-oriented navigation layer is
[`paper/README.md`](paper/README.md). It maps the scientific questions in the
Results section to their registered experiments.

## Predictive performance and generalization

| Scientific question | Experiment family |
|---|---|
| Binary and joint binary/ternary performance | [`predictive_performance/`](predictive_performance/README.md) |
| Thermodynamic-state interpolation and extrapolation | [`predictive_performance/state_generalization/`](predictive_performance/state_generalization/) |
| Unseen-component generalization | [`predictive_performance/unseen_components/`](predictive_performance/unseen_components/) |
| Binary-to-ternary transfer | [`predictive_performance/binary_to_ternary/`](predictive_performance/binary_to_ternary/) |

## Ablation analysis

All retained ablations use `overall_binary_ternary` with seeds 0--4.

| Scientific question | Experiment family |
|---|---|
| Molecular representation | [`ablations/molecular_representation/`](ablations/molecular_representation/README.md) |
| Multicomponent interaction architecture | [`ablations/interaction_architecture/`](ablations/interaction_architecture/README.md) |
| Fugacity-constrained fine-tuning | [`ablations/fugacity_finetuning/`](ablations/fugacity_finetuning/) |

The consolidated result is
[`../reports/c1_ablation_overall_binary_ternary.md`](../reports/c1_ablation_overall_binary_ternary.md).

The manuscript-aligned ablation entry points are grouped under
[`ablations/`](ablations/). Each variant provides its configuration, execution
command, and result record.

## Interpretability

The final C1 interpretation questions are indexed under
[`interpretability/`](interpretability/). The complete analysis is registered
under [`explainability/c1_final/`](explainability/c1_final/README.md) and includes
grouped molecular-view attribution, pair-interaction analysis, and
thermodynamic sensitivity.

The three manuscript interpretation questions are indexed under
[`interpretability/`](interpretability/): molecular views, composition-dependent
pair interactions, and the effect of fugacity fine-tuning.

## Model comparisons and separation design

The ideal-activity reference is retained under
[`comparison/ideal_activity/`](comparison/ideal_activity/). Additional machine-
learning baselines, established thermodynamic-model comparisons, and autonomous
separation design have not been evaluated and therefore have no reported
performance values.

Planned comparison placeholders are under [`comparisons/`](comparisons/), and
the unevaluated separation-design section is under
[`separation_design/`](separation_design/README.md).
