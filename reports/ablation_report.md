# ThermoFormer Ablation and Thermodynamic Consistency

All comparisons use the committed main-experiment splits, preprocessing, seeds 0–4, training budget, and validation-only model-selection rule. No test set or hyperparameter was selected after viewing ablation results. P1, P2, and P5 are not independently run because Gibbs–Duhem consistency, composition closure, and permutation consistency are hard constructions; fabricating zero-signal losses would not be a scientific ablation.

## Architectural ablation

The primary ternary comparison uses system-wise vapor-composition MAE. State-variable P and T results remain separate in `results/ablation/architecture.csv`.

| Variant | Ternary y MAE | Difference from Full |
|---|---:|---:|
| Full | 0.05591 | 0 |
| RDKit descriptors | 0.02378 | -0.03213 |
| No interaction | 0.08941 | 0.0335 |
| Pairwise-only | 0.09614 | 0.04023 |
| Condition concatenation | 0.05395 | -0.001957 |
| Direct activity | 0.0424 | -0.0135 |
| Direct VLE | 0.08069 | 0.02478 |

The following fixed isothermal y metric is shown for compactness; P/T and isobaric-y results remain separate in the machine-readable table.

| Variant | Binary y MAE | Ternary y MAE | Unseen-mixture | Unseen-component | Binary-to-ternary | Parameters (M) | Inference (ms/attempt) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full | 0.07154 | 0.05591 | 0.07033 | 0.08381 | 0.03379 | 1.78 | 7.94 |
| RDKit | 0.03344 | 0.02378 | 0.03282 | not available | not available | 1.64 | 8.69 |
| Independent | 0.08059 | 0.08941 | 0.08123 | 0.09285 | 0.06219 | 0.372 | 4.02 |
| Pairwise | 0.08078 | 0.09614 | 0.08133 | 0.08623 | 0.0691 | 0.446 | 7.33 |
| Condition concat. | 0.07424 | 0.05395 | 0.07379 | not available | not available | 1.74 | 8.48 |
| Direct gamma | 0.05524 | 0.0424 | 0.05416 | not available | not available | 1.74 | 4.68 |
| Direct VLE | 0.08851 | 0.08069 | 0.08833 | 0.1102 | 0.06839 | 1.74 | 0.246 |

## Thermodynamic-constraint ablation

P1 is marked not applicable as a one-factor loss ablation because Gibbs–Duhem consistency is the hard excess-Gibbs construction. A5 changes that decoder and is reported only as an architectural intervention, not as an isolated P1 causal estimate. P3/P4 remove one soft loss; P6 removes all removable soft losses while retaining every hard equation and output constraint.

The largest absolute predictive change among removable/controlled physics variants is **p6_no_soft_physics** (Δ system-wise isothermal y MAE -0.009958). The largest change in nonphysical prediction rate is **p4_no_phase_continuity** (Δ -0.007542).

## Many-body evidence

Across all coverage-stratified ternary system/direction rows, Pairwise−Full y MAE has mean **0.03123**, median **0.02228**, and is positive for **76.9%** of rows. A paired Wilcoxon signed-rank test gives **p=0.0134**. The complete distribution, including negative cases, is retained in `results/ablation/manybody_system_effects.csv`.

## Accuracy–consistency relationship

The trade-off figure keeps predictive y MAE, Gibbs–Duhem residual, permutation error, and nonphysical rate as separate axes. A direct-VLE model has no activity coefficients, so Gibbs–Duhem and equilibrium-equation residuals are reported as not available rather than assigned zero.

## Answers to the fixed questions

1. **Pretrained representation:** necessity is **not supported** on the evaluated in-distribution split: RDKit−Full ternary y MAE is -0.03213. A1 was not run on unseen-component or binary-to-ternary, so this negative result does not establish broad superiority of RDKit.
2. **Multicomponent interaction:** it is supported on ternary prediction: No-interaction−Full ternary y MAE is +0.0335.
3. **Full versus pairwise:** the degradation is larger for ternary than binary states under the same isothermal y metric (Pairwise−Full 0.04023 versus 0.009241). The paired ternary-system analysis is consistent with a many-body contribution, while retaining all pairwise wins.
4. **Latent nonideality bottleneck:** its value is physical rather than predictive in this experiment. Direct-gamma improves ternary y MAE by 0.0135, but increases mean Gibbs–Duhem residual from 3.936e-08 to 0.2407 (about 6.12e+06×).
5. **Thermodynamic versus direct decoding:** Full is better than Direct VLE on ternary, unseen-component, and binary-to-ternary isothermal y MAE by 0.02478, 0.02639, and 0.03461, respectively. Direct VLE cannot provide activity-coefficient or equilibrium-equation consistency metrics.
6. **Largest accuracy effect:** removing all soft physics (P6) changes unseen-mixture isothermal y MAE by -0.009958; here the sign is an accuracy improvement, so the soft losses did not improve this predictive metric.
7. **Physical-validity effect:** P4 has the largest composite nonphysical-rate change (-0.007542), but removal worsens the targeted smoothness diagnostics: derivative jump 1.368→1.83 and curvature 8.325→10.09. Thus the continuity loss constrains local roughness, not the composite failure rate.
8. **Trade-off:** yes. Removing P4/P6 improves the selected y MAE while worsening phase smoothness; Direct-gamma improves y MAE while severely violating Gibbs–Duhem consistency.
9. **Many-body claim:** supported only to the degree quantified by the full paired distribution (mean Δ=0.03123, p=0.0134); no favorable-only systems were selected.
10. **Placement:** Full/Pairwise/No-interaction/Direct-VLE and P6 belong in the main text; RDKit, condition concatenation, direct-gamma/A5, individual soft-loss removals, hard-constraint non-applicability, full physical metric definitions, and all per-system rows belong in SI.

## Scope and negative results

Conclusions remain limited to binary/ternary low-pressure VLE below 500 kPa. Missing observables, failed solves, negative deltas, and non-monotonic outcomes are preserved. The absent `reports/model_comparison_report.md` was not used as evidence.
