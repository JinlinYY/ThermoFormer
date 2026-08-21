# Thermodynamic-consistency loss ablations

These experiments preserve the ThermoFormer architecture and training budget while
removing one thermodynamic-consistency objective.

- [`no_continuity_loss`](no_continuity_loss/run.md): sets the local phase-diagram continuity loss weight to zero.
- [`no_boundary_loss`](no_boundary_loss/run.md): disables near-pure activity-coefficient boundary supervision.
- [`no_solver_loss`](no_solver_loss/run.md): disables mode-specific differentiable bubble-solver supervision.

Component permutation equivariance is enforced by the architecture and covered by
regression tests. It is not represented as a near-zero auxiliary loss, so there is
no scientifically vacuous permutation-loss ablation.

Future loss ablations should be added as sibling experiment directories rather than
placed directly under `experiments/`.
