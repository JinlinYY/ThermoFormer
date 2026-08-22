# Multi-view smoke-test report

These seed-0, three-epoch runs are isolated numerical diagnostics. They are not performance estimates and were not aggregated with formal results.

| Variant | Epochs | Train loss first → last | Finite | Last gradient norm | Solver coverage P / T | Train s | Peak GPU MB | Parameters |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| V1 RDKit descriptors only | 3 | 1.5849 → 0.3854 | True | 9.0314 | 0.000 / 0.943 | 8.0 | 468.3 | 1,637,571 |
| V4 RDKit + Uni-Mol naive fusion | 3 | 1.4777 → 0.2882 | True | 7.7023 | 0.000 / 0.882 | 7.2 | 514.7 | 1,934,787 |
| V5 Three-view naive fusion | 3 | 1.3063 → 0.2562 | True | 6.6956 | 0.001 / 0.876 | 7.5 | 534.7 | 2,015,043 |
| V6 Interaction-specific multi-view fusion | 3 | 1.3224 → 0.2765 | True | 7.2207 | 0.000 / 0.817 | 13.7 | 2307.5 | 2,613,896 |

The deliberately short solver evaluation used four iterations, so coverage is a stability signal only; the formal campaign used 48 iterations.
