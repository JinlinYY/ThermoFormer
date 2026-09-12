# Joint binary--ternary model phase-diagram cases

Status: completed_exploratory.

The cases come from the formal `overall_binary_ternary` seed-0 test partition. The five formal seeds use different system-disjoint test assignments, so predictions are not combined across seeds at the case level. Case selection inspected test errors and is diagnostic rather than confirmatory.

| Test subset | Category | Task | System | Condition | n | State MAE | all-component y MAE |
|---|---|---|---|---:|---:|---:|---:|
| 2-component test | Well-predicted | P-x-y | 3-methyl-2-butanone + 2,3-dimethylbutane | 333.15 K | 17 | 1.915 kPa | 0.0117 |
| 2-component test | Well-predicted | T-x-y | n,n-dimethylformamide + dimethyl sulfoxide | 101.30 kPa | 31 | 0.569 K | 0.0103 |
| 2-component test | Representative | P-x-y | 1-propanol + ethanol | 403.20 K | 5 | 18.178 kPa | 0.0343 |
| 2-component test | Well-predicted | P-x-y | propyl acetate + ethanol | 348.15 K | 15 | 1.170 kPa | 0.0115 |
| 2-component test | Well-predicted | T-x-y | octane + methyl formate | 101.32 kPa | 31 | 1.520 K | 0.0066 |
| 2-component test | High-error | P-x-y | isobutane + propanenitrile | 307.86 K | 6 | 50.380 kPa | 0.0015 |
| 3-component test | Well-predicted | P-x-y | 3-methyl-2-butanone + 2,3-dimethylbutane + diisopropyl ether | 333.15 K | 27 | 1.518 kPa | 0.0076 |
| 3-component test | Well-predicted | T-x-y | isobutyl acetate + 2-methyl-1-propanol + 1-hexanol | 101.30 kPa | 42 | 0.997 K | 0.0164 |
| 3-component test | Representative | P-x-y | methylcyclohexane + cyclohexylamine + aniline | 333.15 K | 10 | 1.240 kPa | 0.0279 |
| 3-component test | Well-predicted | P-x-y | 3-methyl-2-butanone + 2,3-dimethylbutane + diisopropyl ether | 323.15 K | 29 | 1.191 kPa | 0.0105 |
| 3-component test | Well-predicted | T-x-y | 1-methyl-2-pyrrolidinone + benzene + thiophene | 101.30 kPa | 21 | 0.665 K | 0.0049 |
| 3-component test | High-error | P-x-y | methylcyclohexane + cyclohexylamine + aniline | 363.15 K | 11 | 5.129 kPa | 0.0335 |

## Post-hoc fitted classical-model comparison

NRTL, Wilson, and UNIQUAC are evaluated with the open-source Phasepy backend. Interaction parameters are fitted separately for each displayed chemical system using every matching experimental row in the complete curated dataset, irrespective of its previous train/validation/test assignment; Phasepy `bubblePy` and `bubbleTy` then calculate the displayed bubble states. Pure-component vapor pressures use external DIPPR, Antoine, Wagner, VDI, or HEOS correlations from the `thermo` property database, injected through Phasepy's Psat callback. Each selected correlation must cover every fit and solver temperature, reports native Pa and output kPa units, and satisfy dPsat/dT > 0 throughout the required range. Components without a valid correlation are marked unavailable rather than extrapolated. UNIQUAC r and q use DDBST UNIFAC subgroup assignments resolved by compound identity. These are fully data-exposed, in-sample descriptive fits—not predictive baselines for unseen mixtures.
Classical-model isothermal outputs are connected as fitted branches. Classical-model isobaric outputs are shown as discrete hollow points because independent bubble-temperature solves can select different mathematical roots; no post-hoc smoothing is applied.

Validated external vapor-pressure coverage: 18/21 displayed components (85.7%). Selected methods: ANTOINE_WEBBOOK: 1, DIPPR_PERRY_8E: 16, WAGNER_POLING: 1.
Full-dataset lookup found 0 additional rows beyond the registered overall test rows across the 10 unique displayed systems. Because the overall split is system-disjoint, zero additional rows means all same-system rows were already in its test partition; the present recalculation changes only the pure-property source and the refitted classical-model parameters.

Each cell reports state MAE / all-component vapor-composition MAE.

| Subset | Task and system | ThermoFormer | NRTL fitted | Wilson fitted | UNIQUAC fitted |
|---|---|---:|---:|---:|---:|
| 2-component | P-x-y; 3-methyl-2-butanone + 2,3-dimethylbutane | 1.915 kPa / 0.0117 | 0.246 kPa / 0.0030 | 0.201 kPa / 0.0034 | 0.258 kPa / 0.0032 |
| 2-component | T-x-y; n,n-dimethylformamide + dimethyl sulfoxide | 0.569 K / 0.0103 | 0.413 K / 0.0105 | 0.420 K / 0.0102 | 0.416 K / 0.0104 |
| 2-component | P-x-y; 1-propanol + ethanol | 18.178 kPa / 0.0343 | 2.454 kPa / 0.0086 | 2.420 kPa / 0.0086 | 2.420 kPa / 0.0085 |
| 2-component | P-x-y; propyl acetate + ethanol | 1.170 kPa / 0.0115 | 0.367 kPa / 0.0058 | 0.387 kPa / 0.0060 | 0.408 kPa / 0.0063 |
| 2-component | T-x-y; octane + methyl formate | 1.520 K / 0.0066 | 0.347 K / 0.0037 | 0.581 K / 0.0042 | 0.468 K / 0.0030 |
| 2-component | P-x-y; isobutane + propanenitrile | 50.380 kPa / 0.0015 | 7.071 kPa / 0.0029 | 6.800 kPa / 0.0045 | 7.995 kPa / 0.0028 |
| 3-component | P-x-y; 3-methyl-2-butanone + 2,3-dimethylbutane + diisopropyl ether | 1.518 kPa / 0.0076 | 0.232 kPa / 0.0029 | 0.250 kPa / 0.0027 | 0.247 kPa / 0.0031 |
| 3-component | T-x-y; isobutyl acetate + 2-methyl-1-propanol + 1-hexanol | 0.997 K / 0.0164 | N/A | N/A | N/A |
| 3-component | P-x-y; methylcyclohexane + cyclohexylamine + aniline | 1.240 kPa / 0.0279 | N/A | N/A | N/A |
| 3-component | P-x-y; 3-methyl-2-butanone + 2,3-dimethylbutane + diisopropyl ether | 1.191 kPa / 0.0105 | 0.123 kPa / 0.0021 | 0.114 kPa / 0.0020 | 0.113 kPa / 0.0023 |
| 3-component | T-x-y; 1-methyl-2-pyrrolidinone + benzene + thiophene | 0.665 K / 0.0049 | N/A | N/A | N/A |
| 3-component | P-x-y; methylcyclohexane + cyclohexylamine + aniline | 5.129 kPa / 0.0335 | N/A | N/A | N/A |

Descriptive win counts (lower error):
- ThermoFormer has lower state MAE than NRTL in 0/8 covered cases and lower vapor-composition MAE in 2/8 covered cases.
- ThermoFormer has lower state MAE than Wilson in 0/8 covered cases and lower vapor-composition MAE in 1/8 covered cases.
- ThermoFormer has lower state MAE than UNIQUAC in 0/8 covered cases and lower vapor-composition MAE in 2/8 covered cases.

These counts describe the selected, data-exposed cases only. They are not a statistical model ranking, and the classical models had access to all available dataset rows for the displayed systems during parameter fitting.

Eligible fixed-condition curves: 92 binary and 7 ternary.

Within each test subset, the figure contains the two lowest-error isothermal cases, the two lowest-error isobaric cases, one remaining case nearest the candidate-score median, and one global maximum-error case. Thus each figure contains exactly one high-error panel.

The normalized score combines state RMSE divided by the observed state range with all-component vapor-composition RMSE. Pressure and temperature ranges use lower bounds of 5 kPa and 5 K.

Article figure: `experiments/vle/prediction/study_records/overall_binary_ternary/phase_diagrams/combined_binary_ternary_phase_diagram_cases.png`.

Classical fit parameters and optimizer audit: `experiments/vle/prediction/case_studies/overall_binary_ternary/phase_diagrams/classical_system_fit_audit.json`.
