# Training protocols

## Manuscript three-stage optimization

The VLE thermodynamic references are inferred from experimental states and
temperature-valid external saturation-pressure correlations. They are not
independently measured activity coefficients. Reference masks exclude unidentifiable
activities and retain exact pure endpoints as described in SI S2.5.

Supervised initialization minimizes the equilibrium-data objective before the three stages:

| Stage | Objective | Epoch budget |
|---|---|---:|
| 1 | L_thermo = SmoothL1(gE - gE_ref) + 0.5 SmoothL1(ln gamma - ln gamma_ref) | 20 |
| 2 | L_thermo + L_VLE | 80 |
| 3 | L_thermo + L_VLE + lambda(e) L_fug | 10 |

L_VLE combines vapor-composition error, squared logarithmic pressure error, and
0.5 times the pure-component pressure objective. L_fug uses the observed T, P, x,
and y, with pressure-normalized component fugacity residuals. The Stage-3 weight
is `0.01 * min(1, e / 2)`. Bubble temperature is obtained by inversion rather than
as an independent temperature regression target.

Stage 1 freezes the vapor-pressure branch. Stage 2 restores joint optimization.
Stage 3 updates selected interaction, FiLM, mixture-token, and vapor-pressure
parameters while freezing the molecular projections and Transformer. Each stage
starts from the preceding validation-selected checkpoint; test data do not select it.

Implementation: `src/thermoformer/training/direct_ge.py` and
`direct_ge_pipeline.py`. Registered configurations:
`configs/vle/ablation/studies/overall_binary_three_stage/` and
`configs/vle/ablation/studies/three_stage_training/`.

## Supervised/fugacity fine-tuning comparison

The separate supervised-plus-fugacity comparison uses `supervised.py` and
`fugacity_finetuning.py`. Its two optimization steps must not be confused with
the three-stage thermodynamic-reference protocol above. The fine-tuning branch
uses 10 epochs, a two-epoch warmup, and the following parameter groups:

| Parameter group | Learning rate |
|---|---:|
| pair_potential | 2e-5 |
| vapor_pressure | 1e-5 |
| film | 5e-6 |
| mixture_token | 5e-6 |

The initial checkpoint remains a validation candidate. The test partition is
evaluated after selection. Fixed splits, feature scaling fitted on training
data, and seeds 0-4 are required for the five-seed comparisons.
