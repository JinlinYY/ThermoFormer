# Model architecture

## Inputs and outputs

For each mixture, the model receives up to three molecular feature vectors, a
component mask, liquid composition `x`, and one specified thermodynamic state.

| Inference direction | Known inputs | Joint outputs |
|---|---|---|
| Isothermal P--x--y | molecules, `T`, `x` | bubble pressure `P`, vapor composition `y` |
| Isobaric T--x--y | molecules, `P`, `x` | bubble temperature `T`, vapor composition `y` |

Padding is masked, and component permutations produce the corresponding output
permutation.

## Molecular views

- RDKit: 24 split-train standardized physical and topological descriptors.
- Uni-Mol v2: frozen 768-dimensional molecular embedding from the 84M model.
- Functional groups: 28 deterministic SMARTS counts.

Each view has an independent projection. The projected views are concatenated
and projected to the Transformer hidden dimension.

## Thermodynamic decoder

The model uses a component-permutation-equivariant Transformer, a mixture token,
state FiLM, and symmetric, composition-dependent effective pair potentials.
The registered molecular and interaction ablations are defined separately in
`configs/vle/ablation/`.

The excess Gibbs energy is

```text
gE/RT = sum_(i<j) x_i x_j I_ij.
```

Activity coefficients are computed from the complete composition derivative of
this scalar. Pure-component vapor pressure depends only on the molecular
representation and temperature, unless a valid Antoine or DIPPR 101 correlation
is supplied.

The active implementation is organized as follows:

| Scientific responsibility | Module |
|---|---|
| Dataset schema, loading, and split logic | `src.thermoformer.data` |
| RDKit, Uni-Mol v2, functional groups, and fusion | `src.thermoformer.features` |
| Molecular interaction and vapor-pressure heads | `src.thermoformer.models` |
| Activity coefficients and differentiable VLE solvers | `src.thermoformer.thermodynamics` |
| Supervised and fugacity-constrained optimization | `src.thermoformer.training` |
| Prediction metrics and consistency analysis | `src.thermoformer.evaluation` |

## Liquid-liquid equilibrium

The LLE decoder receives molecular features, temperature, and pressure. It returns
an unordered pair of binary coexistence endpoints or a ternary tie-line family;
an overall feed composition is required only for a downstream phase-split calculation.
Binary surfaces use a two-parameter Redlich-Kister expansion. Ternary surfaces use
a continuous binodal with parallel tie lines. Activity equality, endpoint separation,
and finite-grid tangent-plane-distance checks screen candidate states. A finite
grid does not certify global stability over the continuous simplex.

The implementation is in `src/thermoformer/lle_tp/model.py`,
`hybrid_binodal_model.py`, `binodal_model.py`, and `solver_certified.py`.

## Training and agent interfaces

The manuscript's staged thermodynamic objectives are implemented in
`src/thermoformer/training/direct_ge_pipeline.py` and `direct_ge.py`;
see [training](../guides/training.md) for initialization, the three losses,
checkpoint selection, and the separate fine-tuning comparison protocol.

The task compiler, unit/source checks, and evidence-linked reports are implemented
in `Web/ThermoFormer-web/backend/paper_agent/reliability.py`. Numerical calls go
through `Web/ThermoFormer-web/backend/thermo_engine/paper_reliability.py` and
`paper_tools.py`. Clarification recovery and evidence-action experiments are
defined in `scripts/benchmarks/paper_agent/main_figure_experiment.py`.
