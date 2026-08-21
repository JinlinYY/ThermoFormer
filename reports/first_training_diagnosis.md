# First Formal Training Diagnosis

Date: 2026-08-21. This report supersedes the earlier single-seed pilot diagnosis. It summarizes 15 protocols × 5 seeds = 75 completed formal runs on an NVIDIA GeForce RTX 3090 Ti in `ggnn39`.

## Convergence and numerical behavior

- Non-finite values in all recorded numeric training/validation curves: **0**.
- Median best/initial experimental validation-loss ratio: **0.037** (lower is better).
- Median validation-minus-training total loss at the selected supervised epoch: **-0.0301**.
- Supervised early stopping before the 80-epoch ceiling occurred in **48/75** runs.
- Physics fine-tuning produced a lower experimental validation objective than the supervised best in **14/75** runs; otherwise the supervised checkpoint was retained as the valid epoch-0 candidate.
- Maximum protocol-mean solver failure rate: **0.1723%**; maximum protocol-mean nonphysical rate: **0.0000%**.

## Physics-loss and gradient scales

Across physics epochs, median raw continuity loss was **2.46e+03**; after the configured 1e-5 weight its median contribution was **0.0246**. Median raw boundary loss was **1.07e-11** (weighted contribution **1.07e-14**), and median raw differentiable-solver loss was **0.00108** (weighted contribution **0.000108**).
The recorded total pre-clipping gradient-norm mean was **36.5** in supervised epochs and **13** in physics epochs. Historical runs did not record a separate gradient norm for each objective, so per-loss gradients cannot be reconstructed exactly from history alone; the weighted loss contributions above are not mislabeled as gradients. A future instrumentation-only run should record those norms explicitly.

## Error gaps and capability boundaries

**Pressure metrics**

| Test subset | MAE (kPa) | RMSE (kPa) | R² |
|---|---:|---:|---:|
| Binary-only model: binary test | 17.26 ± 8.42 (n=5) | 35.13 ± 14.93 (n=5) | 0.911 ± 0.051 (n=5) |
| Joint model: binary test | 18.57 ± 6.40 (n=5) | 40.45 ± 14.09 (n=5) | 0.882 ± 0.052 (n=5) |
| Joint model: ternary test | 4.43 ± 3.39 (n=4) | 5.68 ± 4.07 (n=4) | 0.888 ± 0.130 (n=4) |

**Temperature metrics**

| Test subset | MAE (K) | RMSE (K) | R² |
|---|---:|---:|---:|
| Binary-only model: binary test | 5.75 ± 1.61 (n=5) | 8.09 ± 2.50 (n=5) | 0.920 ± 0.052 (n=5) |
| Joint model: binary test | 5.72 ± 1.56 (n=5) | 8.16 ± 2.02 (n=5) | 0.925 ± 0.025 (n=5) |
| Joint model: ternary test | 2.67 ± 0.46 (n=4) | 3.60 ± 0.80 (n=4) | 0.949 ± 0.040 (n=4) |

**Vapor-composition metrics**

| Test subset | MAE | RMSE | R² |
|---|---:|---:|---:|
| Binary-only model: binary test | 0.0657 ± 0.0176 (n=5) | 0.0970 ± 0.0238 (n=5) | 0.903 ± 0.052 (n=5) |
| Joint model: binary test | 0.0697 ± 0.0160 (n=5) | 0.1031 ± 0.0192 (n=5) | 0.893 ± 0.042 (n=5) |
| Joint model: ternary test | 0.0530 ± 0.0133 (n=5) | 0.0742 ± 0.0193 (n=5) | 0.900 ± 0.049 (n=5) |

**Prediction validity**

| Test subset | Valid coverage |
|---|---:|
| Binary-only model: binary test | 1.0000 ± 0.0000 |
| Joint model: binary test | 1.0000 ± 0.0000 |
| Joint model: ternary test | 1.0000 ± 0.0000 |

**Pressure metrics**

| Test subset | MAE (kPa) | RMSE (kPa) | R² |
|---|---:|---:|---:|
| State interpolation | 4.45 ± 1.03 (n=5) | 10.05 ± 2.37 (n=5) | 0.983 ± 0.008 (n=5) |
| Unseen mixture | 16.99 ± 5.88 (n=5) | 38.24 ± 13.89 (n=5) | 0.884 ± 0.052 (n=5) |
| Unseen component | 27.40 ± 0.87 (n=5) | 71.92 ± 5.21 (n=5) | 0.460 ± 0.076 (n=5) |

**Temperature metrics**

| Test subset | MAE (K) | RMSE (K) | R² |
|---|---:|---:|---:|
| State interpolation | 1.83 ± 0.45 (n=5) | 2.49 ± 0.58 (n=5) | 0.990 ± 0.005 (n=5) |
| Unseen mixture | 5.46 ± 1.48 (n=5) | 7.88 ± 2.01 (n=5) | 0.928 ± 0.025 (n=5) |
| Unseen component | 37.87 ± 3.63 (n=5) | 48.63 ± 4.10 (n=5) | 0.415 ± 0.098 (n=5) |

**Vapor-composition metrics**

| Test subset | MAE | RMSE | R² |
|---|---:|---:|---:|
| State interpolation | 0.0324 ± 0.0071 (n=5) | 0.0473 ± 0.0083 (n=5) | 0.969 ± 0.012 (n=5) |
| Unseen mixture | 0.0671 ± 0.0144 (n=5) | 0.0996 ± 0.0173 (n=5) | 0.898 ± 0.037 (n=5) |
| Unseen component | 0.0931 ± 0.0180 (n=5) | 0.1390 ± 0.0235 (n=5) | 0.846 ± 0.055 (n=5) |

**Prediction validity**

| Test subset | Valid coverage |
|---|---:|
| State interpolation | 1.0000 ± 0.0000 |
| Unseen mixture | 1.0000 ± 0.0000 |
| Unseen component | 0.9983 ± 0.0021 |

The joint-model ternary subset is not uniformly harder than its binary subset, but the unseen-component protocol is dramatically harder than both state interpolation and system-disjoint unseen mixtures. Binary-to-ternary zero-shot transfer is viable on the fixed four-system test sets, whereas adding small ternary subsets gives a non-monotonic response.

## Best and worst systems in the joint binary/ternary benchmark

| Metric | Extreme | System | Components | Mean absolute error |
|---|---|---|---|---:|
| pressure_abs_error_kpa | best | `2c_d7eb8d723543d918ecd0` | `ClC(Cl)C(Cl)Cl | O=C1CCCCC1` | 0.57778 |
| temperature_abs_error_k | best | `2c_3c1769052d07951ac3d7` | `CC(C)O | CCOC(C)=O` | 0.80657 |
| y_abs_error | best | `2c_acbe0e6e906b285e5990` | `CCCCCO | CCCOCCC` | 0.0045636 |
| pressure_abs_error_kpa | worst | `2c_ae514b5a938c4d83d1c9` | `CCCC | CCO` | 136.83 |
| temperature_abs_error_k | worst | `2c_1423cf5c6cbb9a123e33` | `CC(=O)O | CS(C)=O` | 27.52 |
| y_abs_error | worst | `2c_303f5d258da9140f9795` | `CCOC(=O)OCC | O` | 0.25639 |

## Diagnosis

- **Data limitation:** only 18 ternary training systems are available for the scaling pool, so nominal fractions correspond to very small discrete subsets and strong selection variance.
- **Optimization issue:** several scaling seeds degrade despite more ternary systems, suggesting multi-task/cardinality optimization conflict or sensitivity to subset composition; this should be tested before changing architecture.
- **Architectural limitation:** the large unseen-component gap indicates that learned pure-property/nonideality extrapolation outside observed molecular support remains weak.
- **Implementation bug:** no new bug is indicated by the formal runs; NaN checks, strict split audit, artifact hashes, solver convergence flags, and provenance gates behaved as designed.

Recommendation: proceed first to baseline comparisons on the exact splits and add instrumentation/diagnostics. Do not add layers, hidden dimensions, or new loss terms solely in response to this first round. If a method change is later justified, write `reports/proposed_model_change.md` before implementation and retain these results as the unchanged reference.
