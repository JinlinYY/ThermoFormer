# Optimized C2 formal result

Selected candidate: `o2_headwise` (validation-only score 0.943981).

Evaluation: overall_binary_ternary test partition, seeds 0–4, data supervision only.

| metric | mean | std |
|---|---:|---:|
| P MAE (kPa) | 9.861861 | 5.542604 |
| P RMSE (kPa) | 22.325163 | 12.337449 |
| P R² | 0.959314 | 0.030353 |
| T MAE (K) | 2.531088 | 0.517127 |
| T RMSE (K) | 4.184136 | 1.088976 |
| T R² | 0.978079 | 0.014920 |
| y MAE | 0.028503 | 0.003658 |
| y RMSE | 0.050004 | 0.009531 |
| y R² | 0.974310 | 0.009173 |

## Validation candidate capacity

| candidate | trainable parameters | validation score |
|---|---:|---:|
| o0_original | 2,201,284 | 1.000000 |
| o1_shared_gate | 2,126,981 | 0.974941 |
| o2_headwise | 2,090,679 | 0.943981 |
| o3_headwise_curriculum | 2,128,647 | 0.949509 |
| o4_headwise_curriculum_modality | 2,134,177 | 0.964396 |

## Comparison with the frozen ablation

| variant | parameters | P MAE (kPa) | T MAE (K) | y MAE |
|---|---:|---:|---:|---:|
| C2 optimized headwise | 2,090,679 | 9.8619 | 2.5311 | 0.028503 |
| C1 three-view vanilla | 2,015,043 | 8.2050 | 2.5126 | 0.028803 |
| C2 original | 2,201,284 | 8.3028 | 2.7062 | 0.028568 |
| C3 no attention pair bias | 2,052,675 | 8.7406 | 2.4751 | 0.027141 |

Conclusion: the validation-selected headwise bias is not the overall test winner. It slightly improves y MAE over C1, but degrades pressure, while C3 remains better on T and y. The current ThermoFormer should therefore not be replaced by this C2.
No additional configuration was chosen after observing these test results.
