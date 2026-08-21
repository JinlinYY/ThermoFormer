# ThermoFormer constraint audit

Audit date: 2026-08-21. This audit fixes the ablation definitions before any
ablation result is inspected. A constraint is called *hard* only when the model,
thermodynamic decoder, or numerical parameterization guarantees it for every set
of learned weights. A zero-weight training term is a *soft* ablation.

| Constraint | Type | Implementation location | Mathematical quantity | Training term | Can be ablated alone? |
|---|---|---|---|---|---|
| Gibbs–Duhem consistency | Hard thermodynamic construction | `src/model.py`, scalar `gE/RT` differentiation | `sum_i x_i d ln(gamma_i)=0` along simplex tangents | None | Not as a one-factor soft loss. A5 changes the activity architecture and cannot be interpreted as an isolated P1 estimate. |
| Liquid composition closure | Data and collation guarantee | `src/data.py` | `sum_i x_i=1` | None | No. Removing it would change the problem definition. |
| Vapor composition closure | Hard decoder/solver guarantee | `src/thermo.py`; masked softmax in direct-VLE head | `sum_i y_i=1` | None | No scientifically valid soft ablation. P2 is therefore marked not applicable rather than fabricated. |
| Positive activity and vapor pressure | Hard parameterization | `src/thermo.py` exponentiation and clamping; `src/model.py` Psat branch | `gamma_i>0`, `Psat_i>0` | None | No. |
| Present pure-component activity | Hard excess-Gibbs boundary | `src/model.py`, pair factors `x_i x_j` | `ln(gamma_i)=0` at `x_i=1` | None | No exact-limit ablation without changing the activity architecture. |
| Near-pure behavior | Soft regularization | `src/losses.py::with_pure_boundary` | `|ln(gamma_i)|` at `x_i=0.999` during training | `boundary_weight * L_boundary` | Yes: P3 sets only `boundary_weight=0`. |
| Phase-diagram continuity | Soft regularization | `src/losses.py::with_local_continuity` | local second difference of predicted `y(x)` | `continuity_weight * L_continuity` | Yes: P4 sets only `continuity_weight=0`. |
| Differentiable bubble-solve supervision | Soft training constraint plus numerical solver | `src/losses.py::with_solver_supervision`; `src/thermo.py` | solved `P/y` or `T/y` error and equation residual | `solver_weight * L_solver` | Yes as a loss, but the solver equations remain at inference. It is included in P6 and the existing single-loss `no_solver_loss` diagnostic. |
| Component permutation consistency | Hard architecture | shared component encoders, no component positional encoding, symmetric aggregation | output after inverse permutation is unchanged | None | No. P5 is not run because a permutation loss would be numerically vacuous. |
| Solver convergence | Numerical algorithm guarantee with explicit failure | `src/thermo.py` | bubble-equation residual below absolute/relative tolerance | Indirectly encouraged by `L_solver` | The soft supervision can be removed; convergence checking itself cannot. |

## Fixed ablation interpretation

- **P0:** Full ThermoFormer, using the immutable snapshot in
  `configs/ablation/full_model_reference.yaml`.
- **P1:** Not applicable as an isolated loss ablation. A5 retains the molecular
  interaction, Psat branch, Raoult equation, solver, budget, and other losses, but
  replacing the excess-Gibbs decoder also changes the latent nonideality path; it
  is reported only under architectural ablation.
- **P2:** Not applicable. Vapor closure is a hard output parameterization in both
  thermodynamic and direct heads.
- **P3:** Remove only the near-pure boundary loss.
- **P4:** Remove only the local phase-continuity loss.
- **P5:** Not applicable. Permutation consistency is hard and the previous
  permutation-loss prototype had zero numerical signal.
- **P6:** Remove `continuity`, `boundary`, and differentiable-solver supervision
  together; all hard constraints remain.

## Independent physical criteria

The evaluator in `src/evaluation/thermodynamic_consistency.py` reports autograd
Gibbs–Duhem residuals over dense grids for every test system and a fixed finite-
difference validation subset; x/y closure and bounds; near-pure `ln(gamma)`, y,
bubble-pressure-relative, and bubble-temperature errors at 0.99/0.995/0.999; and
all permutations of every binary/ternary test state. Permutation errors remain
separate in y, kPa, K, gamma, and kPa Psat units. Dense simplex paths cover every
test system and report smoothness, final equation residuals, convergence failures,
and nonphysical rate. Nonmonotonicity is not itself a violation. A gross
equilibrium residual of 0.1 kPa and normalized near-pure VLE error of 0.05 were
fixed before formal results were viewed. Near-pure P/T references are independently
fit from the training partition's pure-endpoint measurements (log P against 1/T);
the direct-VLE head is never used as its own reference. Catalog-backed Antoine or
DIPPR parameters are threaded through the same evaluator whenever configured.
Pure-reference coverage is reported explicitly. For Direct-VLE, incomplete
independent reference coverage makes the aggregate pure-limit failure rate and
combined nonphysical rate unavailable; available-component P/T residuals and the
independent y-limit metric remain visible instead of silently changing criterion.
