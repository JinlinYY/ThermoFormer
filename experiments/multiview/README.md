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

The current primary representation comparison follows the requested Table-1
layout rather than unseen-component ranking. It uses five seeds for binary
train → binary test and joint binary+ternary train → binary/ternary test:

```powershell
conda run -n ggnn39 python scripts\run_multiview_suite.py --stage predictive --device cuda
conda run -n ggnn39 python scripts\build_representation_outputs.py
```
