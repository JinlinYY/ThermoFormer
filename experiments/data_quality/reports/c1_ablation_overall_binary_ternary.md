# C1 three-view vanilla ablation results

All representation and interaction ablations use the fixed `overall_binary_ternary` protocol with joint binary and ternary training and joint-set evaluation. Values are the mean ± sample standard deviation over seeds 0--4.

## Molecular-representation ablation

### Isothermal task: molecules, T, x -> P, y

| Variant | P (kPa) MAE | P (kPa) RMSE | P (kPa) R² | y MAE | y RMSE | y R² | Valid coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| C0 Uni-Mol v2 vanilla | 17.092 ± 5.275 | 37.370 ± 12.819 | 0.889 ± 0.050 | 0.0655 ± 0.0192 | 0.0962 ± 0.0255 | 0.906 ± 0.049 | 100.0% |
| V1 RDKit descriptors only | 8.515 ± 3.180 | 19.010 ± 7.582 | 0.971 ± 0.017 | 0.0275 ± 0.0032 | 0.0482 ± 0.0089 | 0.977 ± 0.008 | 100.0% |
| V3 functional groups only | 85588.710 ± 191265.386 | 1759267.139 ± 3933474.961 | -773507701.574 ± 1729615797.541 | 0.1544 ± 0.0191 | 0.2294 ± 0.0265 | 0.564 ± 0.102 | 63.4% |
| V4 RDKit + Uni-Mol | 9.297 ± 4.681 | 21.945 ± 12.623 | 0.957 ± 0.038 | 0.0272 ± 0.0033 | 0.0485 ± 0.0098 | 0.977 ± 0.009 | 100.0% |
| C1 RDKit + Uni-Mol + FG vanilla | 8.205 ± 3.309 | 19.018 ± 7.823 | 0.970 ± 0.019 | 0.0262 ± 0.0046 | 0.0457 ± 0.0089 | 0.979 ± 0.007 | 100.0% |

### Isobaric task: molecules, P, x -> T, y

| Variant | T (K) MAE | T (K) RMSE | T (K) R² | y MAE | y RMSE | y R² | Valid coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| C0 Uni-Mol v2 vanilla | 5.515 ± 1.445 | 7.882 ± 1.977 | 0.928 ± 0.024 | 0.0629 ± 0.0162 | 0.0893 ± 0.0183 | 0.914 ± 0.037 | 100.0% |
| V1 RDKit descriptors only | 2.650 ± 0.352 | 4.500 ± 1.235 | 0.974 ± 0.018 | 0.0306 ± 0.0047 | 0.0540 ± 0.0124 | 0.968 ± 0.014 | 100.0% |
| V3 functional groups only | 31.677 ± 14.469 | 69.908 ± 50.412 | -7.715 ± 11.096 | 0.2024 ± 0.0224 | 0.2660 ± 0.0270 | 0.252 ± 0.143 | 96.7% |
| V4 RDKit + Uni-Mol | 2.578 ± 0.450 | 4.182 ± 1.194 | 0.978 ± 0.017 | 0.0308 ± 0.0045 | 0.0539 ± 0.0104 | 0.969 ± 0.011 | 100.0% |
| C1 RDKit + Uni-Mol + FG vanilla | 2.513 ± 0.371 | 4.146 ± 0.911 | 0.979 ± 0.012 | 0.0307 ± 0.0051 | 0.0541 ± 0.0102 | 0.969 ± 0.012 | 100.0% |

The three-view C1 model reduces all four prediction errors relative to Uni-Mol only. Functional groups alone reach only 63.4%/96.7% valid isothermal/isobaric coverage, so errors must be interpreted together with coverage. Adding functional groups to RDKit and Uni-Mol improves P and isobaric T, with smaller changes in y.

## Component-interaction ablation

### Isothermal task

| Variant | P (kPa) MAE | P (kPa) RMSE | P (kPa) R² | y MAE | y RMSE | y R² | Valid coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| C1 RDKit + Uni-Mol + FG vanilla | 8.205 ± 3.309 | 19.018 ± 7.823 | 0.970 ± 0.019 | 0.0262 ± 0.0046 | 0.0457 ± 0.0089 | 0.979 ± 0.007 | 100.0% |
| C2 chemical-biased + context pair | 8.303 ± 3.748 | 19.761 ± 9.406 | 0.968 ± 0.022 | 0.0267 ± 0.0054 | 0.0466 ± 0.0118 | 0.978 ± 0.010 | 100.0% |
| C3 context pair without attention bias | 8.741 ± 4.253 | 21.551 ± 11.094 | 0.962 ± 0.030 | 0.0251 ± 0.0039 | 0.0445 ± 0.0105 | 0.980 ± 0.009 | 100.0% |

### Isobaric task

| Variant | T (K) MAE | T (K) RMSE | T (K) R² | y MAE | y RMSE | y R² | Valid coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| C1 RDKit + Uni-Mol + FG vanilla | 2.513 ± 0.371 | 4.146 ± 0.911 | 0.979 ± 0.012 | 0.0307 ± 0.0051 | 0.0541 ± 0.0102 | 0.969 ± 0.012 | 100.0% |
| C2 chemical-biased + context pair | 2.706 ± 0.574 | 4.648 ± 1.232 | 0.973 ± 0.018 | 0.0300 ± 0.0055 | 0.0537 ± 0.0132 | 0.969 ± 0.015 | 100.0% |
| C3 context pair without attention bias | 2.475 ± 0.241 | 4.251 ± 0.693 | 0.978 ± 0.009 | 0.0286 ± 0.0047 | 0.0509 ± 0.0102 | 0.972 ± 0.011 | 100.0% |

The C2 chemically biased Transformer does not consistently outperform C1. C3 performs better for T/y but substantially worse for pressure. Across P, T, y, and parameter complexity, C1 provides the most balanced architecture.

## Fugacity-loss fine-tuning ablation (seeds 0--4)

Stage 1 is the validation-best checkpoint after C1 supervised training. Stage 2 retains the supervised loss, adds only the teacher-forced fugacity-equilibrium loss, and fine-tunes for 10 epochs. Checkpoints are selected only on validation data.

| Task output | Stage 1 MAE | Stage 1 RMSE | Stage 1 R² | Fugacity Stage 2 MAE | Fugacity Stage 2 RMSE | Fugacity Stage 2 R² |
|---|---:|---:|---:|---:|---:|---:|
| P, isothermal | 8.204989 ± 3.308622 | 19.018329 ± 7.823497 | 0.969654 ± 0.019383 | 7.621613 ± 3.705912 | 18.211291 ± 8.888451 | 0.972251 ± 0.021806 |
| y, isothermal | 0.026222 ± 0.004596 | 0.045674 ± 0.008894 | 0.979474 ± 0.007333 | 0.024647 ± 0.006357 | 0.044314 ± 0.012051 | 0.980203 ± 0.009862 |
| T, isobaric | 2.512644 ± 0.370953 | 4.145978 ± 0.910616 | 0.978919 ± 0.012083 | 2.398601 ± 0.324137 | 4.202361 ± 0.742409 | 0.978787 ± 0.009841 |
| y, isobaric | 0.030747 ± 0.005083 | 0.054088 ± 0.010236 | 0.968731 ± 0.011814 | 0.029661 ± 0.005693 | 0.053193 ± 0.010783 | 0.969650 ± 0.012380 |

Validation selects Stage 2 for **3/5** seeds and retains Stage 1 for **2/5** seeds.
The mean teacher-forced fugacity residual on the test set decreases from `0.00923742 ± 0.00390755` to `0.00889811 ± 0.00343954`.
Across five-seed means, 10 of 12 P/T/y metrics improve; T RMSE and T R² deteriorate slightly. Fugacity fine-tuning provides an overall benefit but does not improve every seed, so the final workflow retains the validation-selected Stage 1 fallback.

## Final selection

The selected model is **C1 RDKit descriptors + Uni-Mol v2 + functional groups + vanilla Transformer**. Stage 2 adds only the teacher-forced fugacity-equilibrium loss. The pure-endpoint Psat term remains part of data supervision and is not an additional physics fine-tuning loss.
