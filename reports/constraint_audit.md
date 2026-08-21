# ThermoFormer constraint audit

Audit date: 2026-08-21. This audit fixes the ablation definitions before any
ablation result is inspected. A constraint is called *hard* only when the model,
thermodynamic decoder, or numerical parameterization guarantees it for every set
of learned weights. A zero-weight training term is a *soft* ablation.

| Constraint | Type | Implementation location | Mathematical quantity | Training term | Can be ablated alone? |
|---|---|---|---|---|---|
| Gibbs–Duhem consistency | Hard thermodynamic construction | `src/model.py`, scalar `gE/RT` differentiation | `sum_i x_i d ln(gamma_i)=0` along simplex tangents | None | Not as a soft loss. A5/P1 replaces only the activity decoder by direct `ln(gamma)` and is reported as an architectural hard-constraint removal. |
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
- **P1:** The A5 direct-activity run. It is the only controlled way to remove the
  hard Gibbs–Duhem construction while retaining the molecular interaction, Psat
  branch, modified Raoult equation, solver, training budget, and other losses.
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
and finite-difference Gibbs–Duhem residuals, x/y closure and bound violations,
near-pure `ln(gamma)` and VLE errors at 0.99/0.995/0.999, all binary or ternary
component permutations, dense simplex-path smoothness, final bubble-equation
residuals, convergence failures, and a nonphysical rate. Nonmonotonicity is not
itself a violation; continuity metrics use total variation and first/second
derivatives. A gross equilibrium residual is fixed at 0.1 kPa and a near-pure VLE
error at 0.05 before experiments are viewed.
