# Common saturation-pressure comparison

This controlled comparison freezes ThermoFormer weights, original UNIFAC parameters,
and the 183-stage extractive-distillation configuration. Both activity models use
the same external component saturation-pressure correlations. Only the activity
coefficient source changes within a given reference configuration.

| Component | Common reference |
|---|---|
| sec-Butyl alcohol | WAGNER_MCGARRY, McGarry (1983), thermo 0.6.1 |
| sec-Butyl acetate, reference A | Li et al. (2013), Table 3: log10(P/kPa) = 4.36 - 487.96/(T/K - 175.67) |
| sec-Butyl acetate, reference B | Huang et al. (2015), quoted by Yin et al. (2019), Table 3: log10(P/kPa) = 6.52785 - 1550.251/(T/K - 42.1408) |
| DMF | DIPPR_PERRY_8E |

Reference A has a reported fit interval of 329-384 K. Its 16 source measurements
span 329.75-384.25 K. Reference B's validation interval is unverified. Applying
these references above their measured coverage is an explicitly extrapolative
sensitivity calculation, not an experimental validation at column temperatures.
Published coefficients are used without refitting to mixture labels or process targets.

The column uses 101.3 kPa, an equimolar alcohol/ester feed of 1 mol/s, pure DMF at
a solvent/feed mass ratio of 32, reflux 48, feed stage 159, solvent stage 16, and
183 stages including the reboiler but excluding the total condenser. Both feeds
are saturated liquids. The distillate flow is fixed at 0.5*0.98/0.995 mol/s.

Each configuration starts from both registered column profiles. Equilibrium grids
support internal iteration; final acceptance requires direct bubble recalculation,
normalized compositions, equilibrium residual checks, and component material
balances at every stage and over the whole column. The stage balance tolerance
is 1e-8 mol/s. Small residuals do not establish global phase stability or experimental accuracy.

Outputs include all 17 measured mixture compositions, bubble temperatures and
vapor compositions, full column trajectories, performance, reference coverage,
and a fixed-composition/temperature decomposition of gamma and Psat ratios.

References: [Li et al. (2013)](https://doi.org/10.1016/S1004-9541(13)60534-0),
[Huang et al. (2015)](https://doi.org/10.1016/j.fluid.2015.05.032),
[Yin et al. (2019)](https://doi.org/10.1021/acs.jced.9b00430),
[McGarry (1983)](https://doi.org/10.1021/i200021a023).
