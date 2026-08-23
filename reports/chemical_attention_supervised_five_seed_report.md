# Supervised-only chemical-attention ablation

Formal evaluation on the frozen `overall_binary_ternary` protocol: binary+ternary training followed by a joint binary+ternary test. Values are mean ± sample standard deviation over seeds 0--4. Training contains the experimental supervised loss only; all 25 histories contain zero physics-stage rows.

| Variant | Parameters | P MAE (kPa) | P RMSE (kPa) | P R² | T MAE (K) | T RMSE (K) | T R² | y MAE | y RMSE | y R² |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C0 Uni-Mol vanilla | 1,780,419 | 17.09 ± 5.28 | 37.37 ± 12.82 | 0.889 ± 0.050 | 5.52 ± 1.44 | 7.88 ± 1.98 | 0.928 ± 0.024 | 0.0641 ± 0.0176 | 0.0927 ± 0.0214 | 0.910 ± 0.043 |
| C1 RDKit + Uni-Mol + FG vanilla | 2,015,043 | **8.20 ± 3.31** | **19.02 ± 7.82** | **0.970 ± 0.019** | 2.51 ± 0.37 | **4.15 ± 0.91** | **0.979 ± 0.012** | 0.0288 ± 0.0050 | 0.0507 ± 0.0099 | 0.974 ± 0.010 |
| C2 full chemical-biased Transformer | 2,201,284 | 8.30 ± 3.75 | 19.76 ± 9.41 | 0.968 ± 0.022 | 2.71 ± 0.57 | 4.65 ± 1.23 | 0.973 ± 0.018 | 0.0286 ± 0.0055 | 0.0508 ± 0.0121 | 0.973 ± 0.012 |
| C3 full model without attention pair bias | 2,052,675 | 8.74 ± 4.25 | 21.55 ± 11.09 | 0.962 ± 0.030 | **2.48 ± 0.24** | 4.25 ± 0.69 | 0.978 ± 0.009 | **0.0271 ± 0.0043** | **0.0483 ± 0.0104** | **0.976 ± 0.010** |
| C4 full model without functional groups | 2,084,164 | 8.37 ± 4.43 | 19.13 ± 11.16 | 0.968 ± 0.029 | 2.56 ± 0.44 | 4.29 ± 1.48 | 0.975 ± 0.022 | 0.0289 ± 0.0043 | 0.0499 ± 0.0095 | 0.974 ± 0.009 |

All variants have valid coverage 1.000 and solver failure rate 0.000.

## Interpretation

The three-view representation is decisively useful: C1 reduces P, T, and y MAE by approximately 52.0%, 54.4%, and 55.1% relative to C0.

The full chemical-biased model C2 is not the best controlled variant. C1 has the best pressure metrics and the best T RMSE/R², while C3 has the best T MAE and all three y metrics. Relative to C1, C2 changes P/T/y MAE by +1.2%, +7.7%, and -0.8%, respectively; this does not justify its additional parameters and slower higher-order attention training.

Removing attention pair bias (C3) improves T and y but worsens pressure. Removing functional groups (C4) also does not cause a consistent degradation. Therefore the current evidence supports the simple RDKit + Uni-Mol + FG vanilla Transformer as the balanced choice, not the full chemical-interaction-biased Transformer. If y MAE is the sole target, C3 is best.

This campaign does not include any other evaluation protocol and should not be combined with the earlier seed-0 two-stage pilot.
