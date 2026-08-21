# ThermoFormer Predictive Performance and Generalization

Date: 2026-08-21. All confirmatory experiments use seeds 0–4, validation-only model selection, fixed committed splits, Uni-Mol v2 84M representations, and the differentiable mode-appropriate bubble solver. Values are mean ± sample standard deviation across seeds. Pressure, temperature, and composition errors are never combined into one scalar.

## Overall predictive performance

| Test subset | P MAE (kPa) | T MAE (K) | y MAE | Coverage |
|---|---:|---:|---:|---:|
| Binary-only model: binary test | 17.26 ± 8.42 | 5.75 ± 1.61 | 0.0657 ± 0.0176 | 1.0000 ± 0.0000 |
| Joint model: binary test | 18.57 ± 6.40 | 5.72 ± 1.56 | 0.0697 ± 0.0160 | 1.0000 ± 0.0000 |
| Joint model: ternary test | 4.43 ± 3.39 | 2.67 ± 0.46 | 0.0530 ± 0.0133 | 1.0000 ± 0.0000 |

The joint binary/ternary model is reported by cardinality rather than as one pooled headline. Independent activity-coefficient error is not reported because the workbooks do not provide a complete trusted pure-property reference needed to invert experimental gamma without reusing the model's learned Psat branch.

## Thermodynamic-state interpolation and extrapolation

| Test subset | P MAE (kPa) | T MAE (K) | y MAE | Coverage |
|---|---:|---:|---:|---:|
| State interpolation | 4.45 ± 1.03 | 1.83 ± 0.45 | 0.0324 ± 0.0071 | 1.0000 ± 0.0000 |
| Composition edge | 10.48 ± 3.35 | 5.75 ± 3.35 | 0.0331 ± 0.0115 | 1.0000 ± 0.0000 |
| Low temperature | 6.25 ± 2.47 | 3.03 ± 1.14 | 0.0380 ± 0.0116 | 1.0000 ± 0.0000 |
| High temperature | 15.16 ± 6.81 | 5.15 ± 3.38 | 0.0478 ± 0.0150 | 1.0000 ± 0.0000 |
| Low pressure | 4.59 ± 1.30 | 5.33 ± 3.11 | 0.0676 ± 0.0278 | 1.0000 ± 0.0000 |
| High pressure | 26.99 ± 7.49 | 4.96 ± 1.24 | 0.0519 ± 0.0141 | 0.9996 ± 0.0009 |

Eligible test-system counts are: State interpolation=170; Composition edge=171; Low temperature=139; High temperature=139; Low pressure=68; High pressure=68. Distance-binned results are stored in `results/generalization/extrapolation_distance.csv`; strict split audit confirms that extrapolation test states lie beyond both validation and training boundaries for each mixture.

## Unseen mixtures and components

| Test subset | P MAE (kPa) | T MAE (K) | y MAE | Coverage |
|---|---:|---:|---:|---:|
| State interpolation | 4.45 ± 1.03 | 1.83 ± 0.45 | 0.0324 ± 0.0071 | 1.0000 ± 0.0000 |
| Unseen mixture | 16.99 ± 5.88 | 5.46 ± 1.48 | 0.0671 ± 0.0144 | 1.0000 ± 0.0000 |
| Unseen component | 27.40 ± 0.87 | 37.87 ± 3.63 | 0.0931 ± 0.0180 | 0.9983 ± 0.0021 |

The sharp degradation for held-out components is the clearest present limitation. System-disjoint unseen mixtures remain substantially easier when their constituent molecules have appeared elsewhere.

## Binary-to-ternary transfer

| Test subset | P MAE (kPa) | T MAE (K) | y MAE | Coverage |
|---|---:|---:|---:|---:|
| 0% | 5.03 ± 2.90 | 5.58 ± 2.08 | 0.0581 ± 0.0039 | 1.0000 ± 0.0000 |
| 5.56% | 4.23 ± 1.58 | 4.98 ± 2.10 | 0.0602 ± 0.0079 | 1.0000 ± 0.0000 |
| 10% | 4.68 ± 3.70 | 7.43 ± 4.13 | 0.0698 ± 0.0279 | 1.0000 ± 0.0000 |
| 25% | 5.11 ± 3.60 | 5.31 ± 1.08 | 0.0689 ± 0.0105 | 1.0000 ± 0.0000 |
| 50% | 5.18 ± 2.38 | 5.99 ± 3.10 | 0.0721 ± 0.0202 | 1.0000 ± 0.0000 |
| 100% | 4.52 ± 2.88 | 5.40 ± 1.10 | 0.0587 ± 0.0060 | 1.0000 ± 0.0000 |

The fixed-test scaling curve is non-monotonic. With only 18 candidate ternary training systems, subset identity and seed variability dominate several nominal fractions; added ternary labels do not consistently improve vapor-composition MAE over binary-only zero-shot transfer. This negative result is retained rather than smoothed or selectively reported.

Coverage-controlled metrics for 0/3 through 3/3 observed binary subsystems are in `results/generalization/binary_subsystem_controlled.csv`. They use only binary systems present in the actual training partition when assigning coverage.

## Solver validity and scope

Most protocols have 100% valid coverage. High-pressure extrapolation and unseen-component tests contain small, explicitly reported failure fractions; failed rows remain in attempted-sample denominators. No nonphysical predictions were observed in aggregate summaries. The supported claim is limited to low-pressure binary and ternary VLE below the configured 500 kPa cutoff. There are no quaternary data or quaternary claims.

## Recommendation

Do not expand the architecture solely to improve the first formal metrics. First add strong thermodynamic and data-driven baselines on the identical committed splits, instrument per-objective gradient diagnostics during training, and investigate held-out-component representation/calibration and the non-monotonic ternary scaling subsets. Any method-changing modification should be proposed separately and preserve these first-round results.
