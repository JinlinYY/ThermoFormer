# Multi-view ThermoFormer experiments

This campaign is isolated from all historical formal artifacts. V0–V3 are
single-view controls, V4/V5 are naive view-specific projection baselines, and V6
uses interaction-specific RDKit/Uni-Mol/functional-group branches with a symmetric
mixture-conditioned gate.

Execution is staged: smoke, seed-0 screening, then a five-seed formal comparison.
All stages reuse the committed paper splits and preserve the existing excess-Gibbs,
activity-coefficient, physics-loss, and differentiable-solver definitions.
