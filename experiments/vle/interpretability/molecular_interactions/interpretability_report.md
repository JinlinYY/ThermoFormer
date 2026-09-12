# VLE molecular interpretability

This analysis uses the curated VLE dataset, the `vle_overall_binary` split, and the validation-selected three-stage ThermoFormer checkpoints for seeds 0–4. Test labels are not used for checkpoint selection or attribution sampling.

Selected checkpoints: seed 0: stage2, seed 1: stage1, seed 2: stage2, seed 3: stage2, seed 4: stage2.

## Molecular-view attribution

| Output | Molecular view | Grouped-|Shapley| share, mean ± sample SD |
|---|---|---:|
| $G^E/RT$ | Functional groups | 35.5% ± 7.4% |
| $G^E/RT$ | RDKit descriptors | 49.4% ± 7.0% |
| $G^E/RT$ | Uni-Mol v2 | 15.0% ± 1.1% |
| mean $|\ln\alpha|$ | Functional groups | 35.4% ± 3.1% |
| mean $|\ln\alpha|$ | RDKit descriptors | 53.6% ± 3.2% |
| mean $|\ln\alpha|$ | Uni-Mol v2 | 11.0% ± 2.2% |
| mean $|\ln\gamma|$ | Functional groups | 36.0% ± 5.7% |
| mean $|\ln\gamma|$ | RDKit descriptors | 50.4% ± 5.9% |
| mean $|\ln\gamma|$ | Uni-Mol v2 | 13.7% ± 1.2% |
| mean $|I_{ij}|$ | Functional groups | 35.8% ± 5.9% |
| mean $|I_{ij}|$ | RDKit descriptors | 50.2% ± 6.0% |
| mean $|I_{ij}|$ | Uni-Mol v2 | 14.0% ± 1.3% |

## Cross-view interactions

| Output | View pair | Signed interaction, mean ± sample SD |
|---|---|---:|
| $G^E/RT$ | RDKit descriptors × Functional groups | -0.005094 ± 0.00935 |
| $G^E/RT$ | RDKit descriptors × Uni-Mol v2 | 0.007635 ± 0.00565 |
| $G^E/RT$ | Uni-Mol v2 × Functional groups | -0.00381 ± 0.00811 |
| mean $|\ln\alpha|$ | RDKit descriptors × Functional groups | -0.1097 ± 0.104 |
| mean $|\ln\alpha|$ | RDKit descriptors × Uni-Mol v2 | 0.03131 ± 0.068 |
| mean $|\ln\alpha|$ | Uni-Mol v2 × Functional groups | 0.01796 ± 0.0733 |
| mean $|\ln\gamma|$ | RDKit descriptors × Functional groups | 0.0312 ± 0.0288 |
| mean $|\ln\gamma|$ | RDKit descriptors × Uni-Mol v2 | 0.03529 ± 0.0179 |
| mean $|\ln\gamma|$ | Uni-Mol v2 × Functional groups | 0.001683 ± 0.0099 |
| mean $|I_{ij}|$ | RDKit descriptors × Functional groups | 0.08028 ± 0.0801 |
| mean $|I_{ij}|$ | RDKit descriptors × Uni-Mol v2 | 0.09349 ± 0.0469 |
| mean $|I_{ij}|$ | Uni-Mol v2 × Functional groups | 0.003237 ± 0.0287 |

## Named features

- **Functional groups**: alcohol (0.188), fluoro (0.188), ether (0.171), chloro (0.0803), ketone (0.077)
- **RDKit descriptors**: BalabanJ (0.225), TPSA (0.204), MinPartialCharge (0.176), NumRotatableBonds (0.174), FractionCSP3 (0.171)

## Dominant binary molecular-family pairs

- alcohol/polyol × alkane/cycloalkane: 20.9%
- alcohol/polyol × ether/carbonyl: 19.5%
- alcohol/polyol × water: 9.9%
- alkane/cycloalkane × halogenated: 9.6%
- halogenated × nitrogen-containing: 5.7%

## Molecular structure heatmaps

The structure heatmaps use the seed-0 validation-selected checkpoint and held-out binary test cases. Scores are local signed SMARTS-view occlusion contributions to mean |ln alpha|. They are distributed over atoms matched by each functional-group pattern. Uncolored parts of a molecule have no atom-resolved SMARTS attribution. RDKit descriptors and pooled Uni-Mol vectors remain in the global view analysis because their stored molecule-level representations do not provide a defensible atom mapping.

## Interpretation limits

- Grouped Shapley, feature occlusion, and pair-potential terms explain model responses at observed T, P, and x.
- The values do not measure causal chemical mechanisms, bond energies, or experimental interaction energies.
- Correlated descriptors can share predictive information, so individual occlusion effects are not independent causal effects.
- All five-seed summaries use sample standard deviation across independently initialized models.

## Reproduction outputs

- `experiments/reference_results/modality_shapley.csv`: grouped molecular-view attribution
- `experiments/reference_results/view_synergy.csv`: exact cross-view Shapley interactions
- `experiments/reference_results/feature_occlusion.csv`: named RDKit and functional-group occlusion
- `experiments/reference_results/component_pair_attribution.csv`: learned pair decomposition
- `experiments/reference_results/explicit_case_studies.csv`: held-out binary composition paths
- `experiments/reference_results/molecular_structure_attribution.csv`: atom-level SMARTS-view source values
- `figures/vle_interpretability_complete.png`: combined publication figure
