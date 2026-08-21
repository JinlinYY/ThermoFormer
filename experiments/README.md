# ThermoFormer experiment registry

Concrete experiments must never be placed directly under `experiments/`. They are
organized first by scientific purpose, then by experiment name.

```text
experiments/
  baseline/
    thermoformer_base/
  ablation/
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
  interpolation_extrapolation/
  explainability/
```

Every runnable experiment directory contains:

- `config.json`: complete configuration or strict baseline override;
- `run.md`: exact `ggnn39` command;
- `results.md`: honest current status, automatically replaced after a successful run.

## Experiment index

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

`interpolation_extrapolation/` and `explainability/` currently contain scoped plans
only; they do not claim unrun results. Binary checkpoints and machine-readable
histories belong under the matching path in `runs/experiments/`. Pre-reorganization
outputs remain isolated under `runs/legacy/`.
