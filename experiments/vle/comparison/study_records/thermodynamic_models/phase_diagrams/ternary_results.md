# Test-exposed ternary phase-diagram case study

Status: completed_exploratory.

Four ternary Gibbs-triangle cases were selected after inspecting held-out test predictions. The selection is diagnostic and is not confirmatory evidence.

| Category | Task | System | Condition | n | ThermoFormer state MAE | all-component y MAE | Best available classical model | ThermoFormer score - best classical score | UNIQUAC available |
|---|---|---|---:|---:|---:|---:|---|---:|---|
| Well-predicted | P-x-y | pinacolone + neopentyl alcohol + 2-methoxy-2-methylpropane | 340.00 K | 19 | 1.105 kPa | 0.0046 | Wilson | +0.0117 | no |
| Well-predicted | P-x-y | pinacolone + neopentyl alcohol + 2-methoxy-2-methylpropane | 320.00 K | 14 | 0.201 kPa | 0.0147 | Wilson | -0.0086 | no |
| Representative | P-x-y | 4-methyl-2-pentanone + 2,2,4-trimethylpentane + 2-methyl-1-propanol | 364.15 K | 30 | 1.391 kPa | 0.0097 | NRTL | +0.0061 | no |
| High-error | P-x-y | 3-methyl-2-butanone + 2,3-dimethylbutane + diisopropyl ether | 313.15 K | 28 | 2.027 kPa | 0.0045 | Wilson | +0.0762 | no |

Eligible fixed-condition ternary P-x-y candidates: 3 low-temperature-extrapolation curves and 3 high-temperature-extrapolation curves.

The registered pressure-interpolation/extrapolation test partitions contain no ternary T-x-y samples. Accordingly, no ternary T-x-y panel is fabricated or inferred in this figure.

The score combines state error normalized by the observed state range with the mean squared error over all three vapor-composition components. NRTL and Wilson coverage is required. UNIQUAC is shown only when its fitted parameters and solver output are available; missing predictions are never replaced by ideal-mixture values.

ThermoFormer has a lower normalized curve score than the best available classical model in 1/4 selected cases. The figure selects the minimum-score case in each temperature protocol, the distinct-system case nearest the complete six-case median, and one global maximum-score case. Exactly one panel is labeled high-error.

Gray triangles denote liquid compositions, black circles denote experimental vapor compositions, and gray segments are experimental tie lines. Colored symbols denote model vapor compositions.

Figure: `experiments/vle/comparison/thermodynamic_models/figures/ternary_phase_diagram_cases.pdf`.
