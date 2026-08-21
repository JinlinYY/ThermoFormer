# ThermoFormer experiment registry

Concrete experiments must never be placed directly under `experiments/`. They are
organized first by scientific purpose, then by experiment name.

```text
experiments/
  baseline/
    thermoformer_base/
  ablation/
    architecture/                    # formal A0--A6 controls
    thermodynamic_constraint/        # formal P0--P6 campaign
    component/
      no_film/
      no_transformer/
      no_mixture_token/
    thermodynamic_loss/
      no_continuity_loss/
      no_boundary_loss/
      no_solver_loss/
  comparison/
    ideal_activity/
    binary_to_ternary_generalization/
      zero_shot/
      scaling/percent_05...percent_100/
  predictive_performance/
    overall_binary/
    overall_binary_ternary/
  interpolation_extrapolation/
    state/
      composition_interpolation/
      composition_edge_extrapolation/
      temperature_low_extrapolation/
      temperature_high_extrapolation/
      pressure_low_extrapolation/
      pressure_high_extrapolation/
    chemical_space/unseen_component/
  explainability/
```

Every runnable experiment directory contains:

- `config.json`: complete configuration or strict baseline override;
- `run.md`: exact `ggnn39` command;
- `results.md`: honest current status, automatically replaced after a successful run.

## Experiment index

The formal paper ablation matrix is indexed in
[`ablation/README.md`](ablation/README.md). The `component/` and
`thermodynamic_loss/` rows below are retained preliminary diagnostics and must not
be mixed with the formal five-seed campaign.

| Category | Experiment | Purpose | Command | Results |
|---|---|---|---|---|
| Baseline | `thermoformer_base` | Full model, default 5-fold CV | [run](baseline/thermoformer_base/run.md) | [results](baseline/thermoformer_base/results.md) |
| Component ablation | `no_film` | Remove FiLM conditioning | [run](ablation/component/no_film/run.md) | [results](ablation/component/no_film/results.md) |
| Component ablation | `no_transformer` | Remove interaction Transformer | [run](ablation/component/no_transformer/run.md) | [results](ablation/component/no_transformer/results.md) |
| Component ablation | `no_mixture_token` | Remove global mixture token | [run](ablation/component/no_mixture_token/run.md) | [results](ablation/component/no_mixture_token/results.md) |
| Thermodynamic-loss ablation | `no_continuity_loss` | Remove local continuity loss | [run](ablation/thermodynamic_loss/no_continuity_loss/run.md) | [results](ablation/thermodynamic_loss/no_continuity_loss/results.md) |
| Thermodynamic-loss ablation | `no_boundary_loss` | Remove near-pure boundary loss | [run](ablation/thermodynamic_loss/no_boundary_loss/run.md) | [results](ablation/thermodynamic_loss/no_boundary_loss/results.md) |
| Thermodynamic-loss ablation | `no_solver_loss` | Remove differentiable bubble-solver supervision | [run](ablation/thermodynamic_loss/no_solver_loss/run.md) | [results](ablation/thermodynamic_loss/no_solver_loss/results.md) |
| Comparison | `ideal_activity` | Ideal activity-coefficient baseline | [run](comparison/ideal_activity/run.md) | [results](comparison/ideal_activity/results.md) |
| Predictive performance | `overall_binary` | Binary-only grouped 70/15/15 evaluation | [run](predictive_performance/overall_binary/run.md) | [results](predictive_performance/overall_binary/results.md) |
| Predictive performance | `overall_binary_ternary` | Unified binary/ternary and unseen-mixture evaluation | [run](predictive_performance/overall_binary_ternary/run.md) | [results](predictive_performance/overall_binary_ternary/results.md) |
| State generalization | six fixed state protocols | Composition interpolation/edge and low/high T/P tails | [index](interpolation_extrapolation/state/README.md) | per-protocol `results.md` |
| Chemical generalization | `unseen_component` | At-least-one and strict all-component holdouts | [run](interpolation_extrapolation/chemical_space/unseen_component/run.md) | [results](interpolation_extrapolation/chemical_space/unseen_component/results.md) |
| Binary → ternary | zero-shot + five positive scaling levels | Controlled ternary data-scaling curve and binary-subsystem coverage | [index](comparison/binary_to_ternary_generalization/README.md) | per-protocol `results.md` |

`explainability/` remains a scoped plan and does not claim unrun results. Paper
checkpoints, curves and predictions are separated into `checkpoints/`, `runs/paper/`
and `results/`; diagnostic pilots stay under `runs/` and are never promoted to formal
tables. Pre-reorganization outputs remain isolated under `runs/legacy/`.
