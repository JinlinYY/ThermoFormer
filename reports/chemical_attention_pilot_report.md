# Chemical-interaction-biased Transformer pilot

Seed-0 diagnostic on frozen committed splits. This report is a screening result, not five-seed confirmatory evidence.

No dataset split, thermodynamic equation, differentiable solver, physics loss, or evaluation metric was changed.

## Architecture variants

| Variant | Molecular views | Attention | Pair interaction | Parameters |
|---|---|---|---|---:|
| C0 Current Uni-Mol vanilla Transformer | Uni-Mol | vanilla | legacy symmetric pair | 1,780,419 |
| C1 RDKit + Uni-Mol + FG, vanilla Transformer | RDKit + Uni-Mol + FG | vanilla | legacy symmetric pair | 2,015,043 |
| C2 Three-view chemical-biased Transformer | RDKit + Uni-Mol + FG | chemical pair bias | context-conditioned phi | 2,201,284 |
| C3 Full model without attention pair bias | RDKit + Uni-Mol + FG | vanilla | context-conditioned phi | 2,052,675 |
| C4 Full model without functional-group branch | RDKit + Uni-Mol | chemical pair bias | context-conditioned phi | 2,084,164 |

## Predictive performance

### overall_binary

Each cell lists MAE / RMSE / R².

| Variant | P (kPa) | T (K) | y | valid coverage |
|---|---:|---:|---:|---:|
| C0 Current Uni-Mol vanilla Transformer | 9.047 / 20.273 / 0.957 | 4.401 / 6.222 / 0.969 | 0.0541 / 0.0831 / 0.932 | 1.000 |
| C1 RDKit + Uni-Mol + FG, vanilla Transformer | 4.646 / 9.005 / 0.991 | 3.395 / 5.216 / 0.978 | 0.0307 / 0.0520 / 0.973 | 1.000 |
| C2 Three-view chemical-biased Transformer | 6.078 / 15.299 / 0.975 | 3.071 / 4.950 / 0.980 | 0.0349 / 0.0588 / 0.966 | 1.000 |
| C3 Full model without attention pair bias | 4.857 / 10.027 / 0.989 | 2.772 / 4.181 / 0.986 | 0.0298 / 0.0527 / 0.973 | 1.000 |
| C4 Full model without functional-group branch | 4.309 / 8.207 / 0.993 | 2.956 / 4.906 / 0.981 | 0.0340 / 0.0558 / 0.969 | 1.000 |

### overall_binary_ternary

Each cell lists MAE / RMSE / R².

| Variant | P (kPa) | T (K) | y | valid coverage |
|---|---:|---:|---:|---:|
| C0 Current Uni-Mol vanilla Transformer | 14.342 / 31.290 / 0.883 | 8.075 / 11.219 / 0.896 | 0.0913 / 0.1278 / 0.838 | 1.000 |
| C1 RDKit + Uni-Mol + FG, vanilla Transformer | 5.737 / 16.258 / 0.968 | 2.624 / 4.283 / 0.985 | 0.0309 / 0.0519 / 0.973 | 1.000 |
| C2 Three-view chemical-biased Transformer | 4.576 / 8.920 / 0.990 | 3.000 / 4.811 / 0.981 | 0.0275 / 0.0470 / 0.978 | 1.000 |
| C3 Full model without attention pair bias | 5.471 / 12.604 / 0.981 | 2.877 / 4.421 / 0.984 | 0.0289 / 0.0476 / 0.978 | 1.000 |
| C4 Full model without functional-group branch | 3.670 / 7.001 / 0.994 | 2.393 / 3.899 / 0.987 | 0.0305 / 0.0491 / 0.976 | 1.000 |

### unseen_component

Each cell lists MAE / RMSE / R².

| Variant | P (kPa) | T (K) | y | valid coverage |
|---|---:|---:|---:|---:|
| C0 Current Uni-Mol vanilla Transformer | 27.729 / 74.007 / 0.429 | 40.992 / 51.921 / 0.337 | 0.0910 / 0.1329 / 0.862 | 0.998 |
| C1 RDKit + Uni-Mol + FG, vanilla Transformer | 29.687 / 59.948 / 0.627 | 37.188 / 47.467 / 0.446 | 0.1084 / 0.1683 / 0.779 | 1.000 |
| C2 Three-view chemical-biased Transformer | 30.673 / 60.218 / 0.623 | 35.869 / 46.425 / 0.470 | 0.1112 / 0.1770 / 0.755 | 1.000 |
| C3 Full model without attention pair bias | 35.602 / 71.313 / 0.472 | 37.552 / 48.557 / 0.420 | 0.1127 / 0.1759 / 0.758 | 1.000 |
| C4 Full model without functional-group branch | 34.269 / 63.253 / 0.584 | 35.684 / 46.194 / 0.475 | 0.1123 / 0.1663 / 0.784 | 1.000 |

### binary_to_ternary_zero_shot

Each cell lists MAE / RMSE / R².

| Variant | P (kPa) | T (K) | y | valid coverage |
|---|---:|---:|---:|---:|
| C0 Current Uni-Mol vanilla Transformer | 3.324 / 4.145 / 0.961 | 8.305 / 9.037 / 0.928 | 0.0603 / 0.0958 / 0.846 | 1.000 |
| C1 RDKit + Uni-Mol + FG, vanilla Transformer | 1.382 / 1.767 / 0.993 | 1.674 / 2.134 / 0.996 | 0.0390 / 0.0776 / 0.899 | 1.000 |
| C2 Three-view chemical-biased Transformer | 2.079 / 2.915 / 0.981 | 2.058 / 2.378 / 0.995 | 0.0458 / 0.0818 / 0.888 | 1.000 |
| C3 Full model without attention pair bias | 2.185 / 3.368 / 0.974 | 2.129 / 2.415 / 0.995 | 0.0404 / 0.0799 / 0.893 | 1.000 |
| C4 Full model without functional-group branch | 3.088 / 3.527 / 0.972 | 1.514 / 1.871 / 0.997 | 0.0458 / 0.0840 / 0.882 | 1.000 |

## Pilot decision

Against the three-view vanilla control (C1), the full chemical-biased model (C2) improves only 1 of 6 MAEs across the two generalization protocols.
Within the context-conditioned decoder family, adding attention pair bias (C2 versus C3) improves 5 of 6 generalization MAEs, but does not beat the simpler C1 control overall.
The functional-group branch is not consistently beneficial: C2 improves 4 of 6 generalization MAEs versus C4.

**Go/no-go:** do not replace the current interaction module or start the five-seed campaign on the evidence from this pilot. The useful result is the three-view representation itself (C1); the chemical attention/context module needs redesign or a stronger pilot result before confirmatory training.

## Interpretation boundary

C2 versus C1 isolates the complete interaction-module change; C2 versus C3 isolates attention pair bias; C2 versus C4 isolates the functional-group branch. Seed 0 is sufficient for a go/no-go pilot only. Any replacement claim requires the locked seeds 0--4 campaign.
