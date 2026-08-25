# ThermoFormer Interpretability: Learned Multicomponent Thermodynamics

This report interprets the locked full ThermoFormer and pairwise-only ablation. The full latent analysis uses the seed selected solely by minimum validation loss; attribution and full-versus-pairwise test statistics retain seeds 0–4. No test metric was used to choose a checkpoint.

## Scope and safeguards

- Validation-selected full-model seed: **1** (validation loss 0.036415).
- Matching pairwise-only seed: **1** (validation loss 0.028792).
- `pair_interactions` is the learned scalar pair potential used inside the excess-Gibbs decoder. It is not called a physical bond strength or mechanism. Mean-training-token masking is an independent perturbation cross-check, but remains an embedding-space intervention.
- Latent PCA coordinates are descriptive axes from one checkpoint. Raw latent coordinates are not compared across independently trained seeds because those spaces are not identifiable.
- All selected molecular systems are held-out test systems for the selected seed.

## Molecular interaction attribution across chemical environments

| Representative environment | Test states | Mean $|h_{ij}|$ | Mean masking Δy | Mean $|\ln \gamma|$ | Mean nonideal−ideal Δy |
|---|---:|---:|---:|---:|---:|
| experimental azeotrope proxy | 111 | 1.07 | 0.049 | 0.395 | 0.063 |
| lowest-|gE| hydrocarbon candidate | 14 | 0.606 | 0.139 | 0.222 | 0.0347 |
| model-inferred negative deviation | 16 | 0.395 | 0.152 | 0.138 | 0.0209 |
| model-inferred positive deviation | 35 | 2.59 | 0.236 | 1 | 0.135 |
| water/alcohol hydrogen bonding | 111 | 1.07 | 0.049 | 0.395 | 0.063 |

Across the complete test attribution table, seed-wise Spearman correlations (mean ± SD across n=5 seeds) are: |h_ij| versus masking Δy **-0.0248 ± 0.0679**; versus |ln γ| **0.853 ± 0.0681**; versus the activity contribution to log relative volatility **0.602 ± 0.0587**; and versus nonideal−ideal vapor shift **0.411 ± 0.104**.
The corresponding |h_ij| versus masking Δlnγ correlation is **0.16 ± 0.264**.

The pair potential tracks thermodynamic nonideality, but the independent masking response is essentially uncorrelated and the masking−log-gamma association is seed dependent. Therefore the perturbation experiment does **not** validate h_ij as a causal molecular-interaction attribution. It remains a decoder-internal thermodynamic signal, not a measured interaction strength.

The water/alcohol and experimental-azeotrope labels refer to the same held-out system and are not counted as independent chemical examples. The hydrocarbon label denotes the lowest-|gE| composition-complete hydrocarbon available in the selected test split; its residual nonideality is retained rather than calling it strictly ideal.

## Composition-dependent evolution of molecular nonideality

| Environment | Max latent PC step | Median step | ρ(gE, mean |lnγ|) | ρ(gE, ln α12) |
|---|---:|---:|---:|---:|
| experimental azeotrope proxy; water/alcohol hydrogen bonding | 0.0506 | 0.0364 | -0.974 | 0.142 |
| lowest-|gE| hydrocarbon candidate | 0.166 | 0.129 | -0.448 | -0.513 |
| model-inferred negative deviation | 0.0755 | 0.0574 | 0.263 | -0.0482 |
| model-inferred positive deviation | 0.327 | 0.186 | -0.798 | -0.223 |

All trajectories were evaluated on the fixed x1=0.01–0.99 grid in both isothermal (predict P and y) and isobaric (predict T and y) directions; the table summarizes the isothermal path. Finite adjacent PC steps and smooth decoded observables show continuous composition response; correlation signs vary by chemistry, so one universal one-dimensional latent-to-volatility law is not claimed.

For the experimentally detected azeotrope proxy, the observed y1−x1 crossing is at x1≈**0.674**. The model's closest α12=1 point is at x1=**0.910**. The local latent trajectory is shown without asserting that a bend or turning point is itself an azeotrope mechanism.

## Thermodynamic response sensitivity

Sensitivities are closed-simplex directional derivatives: increasing component j removes the same differential amount from all other components in proportion to their current fractions. This avoids reporting unconstrained derivatives that violate Σx=1.

The largest absolute response in the retained binary/ternary cases is **2.48** for affected component 1 when component 1 is increased in `model-inferred positive deviation`. For the representative ternary, the Frobenius norm between Full and Pairwise-only sensitivity matrices is **1.42**, quantifying how multicomponent context changes cross-component response.

For the representative ternary (1-丙醇 / 二丙醚 / 2-乙氧基乙醇), increasing component 3 gives Full responses (0.232, 0.333, -0.566) for lnγ1–3, compared with Pairwise-only (0.215, 1.02, -1.23). The full multicomponent context mainly damps the pairwise-only response of components 2 and 3 in this case; this is a model response, not proof of a specific complex.

## Binary-to-ternary many-body interaction effects

The analysis contains **5** distinct held-out ternary systems for which A-B, A-C, and B-C experimental systems all exist. Every eligible test row and every seed is retained.

Across 5 seed/system/direction aggregates, Pairwise−Full vapor-composition MAE has mean **0.00796**, median **0.00123**, and is positive in **60.0%** of aggregates (paired Wilcoxon p=**0.812**). Positive means the full model is better; negative cases remain in the CSV and figure.

Only **4** seeds contain at least one eligible held-out ternary, and the 5 aggregate comparisons are low-powered. With p far above 0.05 and only 60.0% positive deltas, the current experiment does **not** demonstrate a stable Full-model advantage over Pairwise-only. It demonstrates composition-dependent corrections whose benefits are system specific.

| Chemical-family stratum | Systems | Mean Δy error (Pair−Full) | Mean Δstate error (Pair−Full) |
|---|---:|---:|---:|
| alcohol/polyol + alcohol/polyol + alcohol/polyol | 1 | -0.0305 | 10.6 |
| alcohol/polyol + alcohol/polyol + ether/carbonyl | 1 | 0.00123 | -0.426 |
| alcohol/polyol + alkane/cycloalkane + ether/carbonyl | 3 | 0.023 | 2.01 |

The simplex panel uses the eligible held-out ternary with the richest measured composition coverage, not the largest Full-model improvement. Its strongest computed vapor correction is Σ|Δy_i|=**0.139** at composition (0.05, 0.05, 0.90). Activity-coefficient and relative-volatility corrections for every simplex point are stored alongside the vapor correction.

A separate path compares a true two-token A-B input with the three-token ternary boundary at x3=0, then raises the third-component fraction to 0.90 while preserving the median measured A:B ratio. For the Full model, the ternary x3=0 context differs from the true binary input in lnγ1, lnγ2, and lnα12 by 0.0285, -0.00192, and 0.0304, respectively. At the endpoint, the Full model changes lnγ1 and lnγ2 relative to the true binary values by 0.188 and 0.207; its lnα12 change is -0.0194. The table also contains the corresponding Pairwise-only path and all α12, α13, and α23 corrections.

## Optional methyl acetate + methanol + DMSO case

The exact methyl acetate + methanol + DMSO ternary is absent from the current retained dataset; no mechanism result is fabricated.

## Answers to the manuscript questions

1. **Different interaction patterns:** chemistry-stratified pair potentials differ, but weak masking agreement prevents treating those differences as validated causal interaction attributions.
2. **Continuous latent nonideality:** all selected x scans yield continuous latent and decoded trajectories, with no discrete state jumps.
3. **Thermodynamic correspondence:** latent gE/RT is associated with activity and volatility responses, but the direction and monotonicity are chemistry dependent.
4. **Third-component response:** the closed-simplex sensitivity matrix and true-binary-to-ternary path quantify both the context discontinuity at x3=0 and subsequent changes in lnγ1, lnγ2, and α12 as component 3 is added.
5. **Stable Full-model advantage:** not supported by the present 5 eligible aggregate comparisons (60.0% positive; Wilcoxon p reported above).
6. **Mechanistic interpretation:** the evidence supports model-level interaction hypotheses that can motivate experiments. It does not identify hydrogen bonds, complexes, or azeotrope mechanisms uniquely.

## Reproducibility

- Full table: `analysis/interpretability/results/interaction_attribution.csv`
- Composition scans: `analysis/interpretability/results/composition_nonideality.csv`
- Sensitivities: `analysis/interpretability/results/thermodynamic_sensitivity.csv`
- Many-body comparisons: `analysis/interpretability/results/manybody_effects.csv`
- Main figure: `analysis/interpretability/figures/Figure_interpretability.{pdf,svg,png}`
