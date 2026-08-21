# ThermoFormer implementation audit

Audit date: 2026-08-21. Scope: the checked-out repository at commit `47a678e` plus the explicitly documented corrections in `reports/implementation_changes.md`. This is a code-and-data audit; it does not treat unrun experiment templates as evidence.

## Executive verdict

The core ThermoFormer scientific chain is implemented rather than mocked:

`Uni-Mol v2 cls_repr → component/mixture interaction → gE/RT → ln(gamma) → separate Psat(T) → modified Raoult equation → differentiable isothermal/isobaric bubble solve`.

The core implementation and paper experiment framework are now suitable for controlled formal runs. The original legacy runner lacked persisted assignments and paper metrics; the new fixed-split runner closes those engineering gaps. It is **not yet evidence for the requested paper claims** until formal five-seed jobs complete. No unrun template or diagnostic pilot is treated as a performance result.

## Requirement-by-requirement audit

| Requirement | Status | Evidence and limitation |
|---|---|---|
| Uni-Mol v2 molecular base | Pass | `src/representation.py` constructs `UniMolRepr(model_name="unimolv2", model_size="84m")` and consumes `cls_repr`. The installed `ggnn39` environment resolves the real backend. Representations are frozen/precomputed; Uni-Mol weights are not fine-tuned. |
| Binary and ternary only | Pass | Loader rejects `smiles4`; batching pads only to three; model rejects cardinalities outside 2/3. There is no quaternary code path or claim. |
| Unified variable-cardinality model | Pass | One parameter set handles binary and ternary samples using a component mask. |
| Permutation consistency | Pass | There is no component positional encoding; attention, masked pooling, symmetric pair features and excess-Gibbs aggregation are equivariant/invariant as appropriate. Regression tests permute components. |
| Mixture-level interaction | Pass | Optional mixture token plus Transformer permits all present components to exchange information before decoding. Ternary pair terms are conditioned on the global mixture context, so the model is not a sum of isolated binary models. An explicit irreducible triplet basis is not implemented. |
| Real nonideality bottleneck | Pass | `nonideality_tokens` are contextual component features used directly by `pair_potential`; they are not an unused logging tensor. |
| Thermodynamic activity construction | Pass | A scalar learned `gE/RT` is differentiated as `gE + d(gE)/dx_i - Σ_j x_j d(gE)/dx_j`, which couples component activity coefficients and enforces the Gibbs-Duhem-compatible construction on the composition simplex. |
| Pure-limit behavior | Pass | `gE` contains `x_i x_j` factors; the present pure component has `ln(gamma_i)=0` structurally. A near-pure boundary loss is also available. |
| Separate gamma and Psat | Pass with caveat | `PureVaporPressure` depends only on molecular representation and temperature. Antoine/DIPPR 101 parameters, units and validity intervals can override the learned branch. The current project has no external pure-property catalog, so learned Psat is identified from mixture-workbook pure endpoints. |
| Modified Raoult equation | Pass | `src/thermo.py` computes `P = Σ x_i gamma_i Psat_i` and normalized `y_i = x_i gamma_i Psat_i/P`. |
| Differentiable isothermal solver | Pass | Given `T,x`, the fixed-count damped solve predicts bubble `P,y`, retains autograd, records residual/convergence, and can fail strictly. The default initial pressure is a fixed 101.325 kPa, not a label. |
| Differentiable isobaric solver | Pass | Given `P,x`, bracketed Newton/bisection predicts bubble `T,y`, retains autograd, records residual/convergence, and can fail strictly. The default initial temperature is a fixed 350 K, not a label. |
| Two-stage training | Pass after correction | Experimental supervision precedes physics fine-tuning. Both stages are now selected by the same experimental validation objective, and the supervised checkpoint remains the epoch-0 candidate for physics tuning. |
| Physics losses | Pass | Configurable local continuity, pure-boundary and differentiable-solver losses are real forward/backward terms. Permutation consistency is a structural constraint and is correctly not represented by a numerically vacuous loss. |
| Leakage-safe paper splits | Pass | `src/splits.py` writes order-invariant state IDs plus the complete modeling-set SHA-256 and rejects drift/overlap/path traversal. Seventy-five artifacts cover 15 distinguishable protocols × seeds 0–4. Complete pure-reference systems are train-only, so endpoint calibration does not break strict state boundaries or group-disjoint validation. Formal inputs must be Git-tracked. |
| Paper-grade metrics | Pass | `src/evaluation.py` exports every solver attempt and reports P/T/y MAE, RMSE and R²; point-wise, sample-, chemical-component- and equal-system aggregation; convergence/valid/nonphysical coverage; cardinality/direction/subgroup slices. Failed rows remain in the denominator. |
| Requested generalization protocols | Pass as framework | Composition interpolation/edge, low/high T/P, system-disjoint unseen mixtures, at-least-one/strict unseen components, and zero-shot/scaled binary-to-ternary splits are implemented and audited. This status describes code, not completed outcomes. |
| Multi-seed uncertainty | Pass as framework | `scripts/run_paper_suite.py` executes seeds 0–4; `src/results.py` refuses partial/mismatched seed sets and reports sample standard deviation (`ddof=1`). Formal numbers remain pending. |
| Reproducibility metadata | Pass | Every run stores resolved-config, split, dataset, feature-cache, used-feature-subset and runtime-environment hashes; Git commit/dirty state; checkpoint/history/curves/predictions/metrics with artifact hashes; resolved CPU/GPU, CUDA/cuDNN and dependency versions, parameter count and memory. Formal runs reject dirty or untracked code/config/split/data inputs, stale resume requests and path traversal. Multi-seed aggregation requires exactly seeds 0–4, rejects mixed training provenance or changed/missing artifacts, separately records training and aggregation commits, requires five-seed completeness for global/cardinality headline scopes, and labels the exact available seeds for naturally sparse finer subgroups. It commits a final aggregate manifest only after both tables are valid. |

## Data and target semantics

- Isothermal rows use inputs `(molecule identities, T, x)` and predict `(P, y)` through the bubble-pressure solver.
- Isobaric rows use `(molecule identities, P, x)` and predict `(T, y)` through the bubble-temperature solver.
- `full_state` rows are evaluated in both directions and are not silently relabeled.
- Direct evaluation at observed `(T,P,x)` is a teacher-forced diagnostic. It must not be used as the headline generalization metric.
- The model does not directly regress experimental activity coefficients. Because no independently verified Psat catalog is configured, experimental gamma error is unavailable and must not be fabricated.

## Scientific risks to carry into experiment interpretation

1. **Quality composition:** 8,916/11,014 retained rows are marked unverified and receive weight 0.5. Report sensitivity to passed-only data where sample size permits.
2. **Anchor selection bias:** enforcing two pure-endpoint temperatures removes 5,225 otherwise loaded rows. Main-set performance applies to the resulting anchored chemical domain.
3. **Mode provenance:** most mode labels are inferred from repeated T/P series rather than explicit workbook fields. Coverage and confidence must accompany mode-specific metrics.
4. **Unseen-component Psat:** a component held completely out has no endpoint anchor in training. Its Psat is an extrapolation from Uni-Mol features through the shared pure-property head, not a catalog lookup.
5. **Sparse ternary domain:** only 26 ternary systems and 1,109 retained ternary points are available. Ternary claims need system-level uncertainty and coverage-stratified reporting; broad chemical-universality language is unsupported.
6. **Low-pressure scope:** rows above 500 kPa are excluded and no vapor-phase EOS is present. Conclusions must remain explicitly low-pressure.

## Audit gate before formal training

All listed automation gates are now implemented and covered by the full unit/integration suite plus real-GPU smoke diagnostics. Formal jobs may start from a clean commit. Until all five seeds of a protocol complete and aggregate successfully, its `results.md` must remain “not run”; partial results are artifacts, not claims.
