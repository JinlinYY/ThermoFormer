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

| Test subset | P MAE (kPa) | T MAE (K) | y MAE | Coverage |
|---|---:|---:|---:|---:|
| Binary-only model: binary test | 17.26 ± 8.42 | 5.75 ± 1.61 | 0.0657 ± 0.0176 | 1.0000 ± 0.0000 |
| Joint model: binary test | 18.57 ± 6.40 | 5.72 ± 1.56 | 0.0697 ± 0.0160 | 1.0000 ± 0.0000 |
| Joint model: ternary test | 4.43 ± 3.39 | 2.67 ± 0.46 | 0.0530 ± 0.0133 | 1.0000 ± 0.0000 |

| Test subset | P MAE (kPa) | T MAE (K) | y MAE | Coverage |
|---|---:|---:|---:|---:|
| State interpolation | 4.45 ± 1.03 | 1.83 ± 0.45 | 0.0324 ± 0.0071 | 1.0000 ± 0.0000 |
| Unseen mixture | 16.99 ± 5.88 | 5.46 ± 1.48 | 0.0671 ± 0.0144 | 1.0000 ± 0.0000 |
| Unseen component | 27.40 ± 0.87 | 37.87 ± 3.63 | 0.0931 ± 0.0180 | 0.9983 ± 0.0021 |

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
