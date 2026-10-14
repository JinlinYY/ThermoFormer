# Test-exposed phase-diagram case study

Status: completed_exploratory.

Cases were selected after inspecting held-out test predictions. They diagnose low- and high-error behavior and are not preregistered or confirmatory evidence.

## Selected cases

| Category | Task | Protocol | System | Condition | Points | ThermoFormer state MAE | y MAE | Best classical model | ThermoFormer score − best classical score |
|---|---|---|---|---:|---:|---:|---:|---|---:|
| Well-predicted | P-x-y | Low-temperature extrapolation | butane + diethyl sulfide | 317.60 K | 26 | 3.695 kPa | 0.0042 | UNIQUAC | -0.0068 |
| Well-predicted | T-x-y | Low-pressure extrapolation | tetrahydropyran + 2-butanol | 50.00 kPa | 21 | 0.220 K | 0.0090 | Wilson | -0.0047 |
| Representative | T-x-y | High-pressure extrapolation | 2-methoxyethanol + water | 134.00 kPa | 8 | 0.958 K | 0.0175 | UNIQUAC | +0.0420 |
| High-error | P-x-y | High-temperature extrapolation | 1-propanol + water | 403.20 K | 13 | 38.471 kPa | 0.0440 | UNIQUAC | +0.1831 |

The curve score is the root mean square of state error normalized by the observed state range and the dimensionless vapor-composition error. Pressure and temperature ranges use 5 kPa and 5 K lower bounds, respectively. The figure selects the minimum-score case in each task, the distinct-system case nearest the complete candidate-set median, and one global maximum-score case.

The complete eligible set contains 16 isothermal and 14 isobaric curves. Exactly one selected panel is labeled high-error; the other three show well-predicted or median-representative behavior.

Figure: `experiments/vle/comparison/thermodynamic_models/figures/phase_diagram_cases.pdf`.

Solid lines are bubble branches plotted against liquid composition; dashed lines are dew branches plotted against predicted vapor composition. The ThermoFormer envelope is ±1 standard deviation over seeds 0--4. Classical models use the deterministic seed-0 fit.
