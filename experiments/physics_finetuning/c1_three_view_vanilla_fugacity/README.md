# C1 fugacity-equilibrium fine-tuning

This experiment reuses the committed seeds 0--4 supervised C1 checkpoints and
the registered `overall_binary_ternary` splits. Stage 2 keeps the supervised loss and
adds only the dimensionless **teacher-forced** component fugacity-equilibrium loss

`mean_i[((x_i gamma_i Psat_i - y_i P) / P)^2]`.

Here `T`, `P`, `x`, and `y` are the observed state; this is a training residual,
not a free solver prediction. No continuity, boundary, differentiable-solver,
chemical-bias or additional pure-anchor loss exists in the active Stage-2 code.
The teacher-forced fugacity weight is `1.0`, with a two-epoch linear warmup,
ten-epoch budget, partial unfreezing, and validation-only Stage 1 fallback.

The pure-endpoint `P_sat` term in Stage 1 remains part of the supervised data
objective and is not an additional Stage-2 physics loss.

The same frozen Stage-1/Stage-2 procedure can be applied to any protocol in
`src/paper_protocols.py`.  Non-overall reports are isolated beside their
machine artifacts under the corresponding `results/...on.<protocol>/results.md`;
the original `overall_binary_ternary` report remains at this directory's
`results.md`.  A protocol must first have a
committed supervised C1 checkpoint generated from its registered split before
formal fugacity fine-tuning can start.
