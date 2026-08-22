# Multi-view ThermoFormer experiments

This campaign is isolated from all historical formal artifacts. V0–V3 are
single-view controls, V4/V5 are naive view-specific projection baselines, and V6
uses interaction-specific RDKit/Uni-Mol/functional-group branches with a symmetric
mixture-conditioned gate.

Execution is staged: smoke, seed-0 exploratory screening, then a five-seed
selection-aware comparison. All stages reuse the committed paper splits and
preserve the existing excess-Gibbs, activity-coefficient, physics-loss, and
differentiable-solver definitions.

Stage B followed the requested fixed-split protocol and inspected seed-0 held-out
test metrics before Stage C variants were selected. Consequently Stage C is not
described as an untouched-test confirmatory estimate. Off-matrix diagnostics
require `--exploratory` and are stored in a separate namespace; V3 FG-only is one
such post-hoc representation control.

Published formal manifests use repository-relative artifact paths and include the
referenced histories/curves, so SHA validation and aggregation survive relocation.
