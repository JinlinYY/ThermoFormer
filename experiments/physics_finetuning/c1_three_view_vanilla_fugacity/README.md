# C1 fugacity-equilibrium fine-tuning

This experiment reuses the committed seed-0 supervised C1 checkpoint and the
registered `overall_binary_ternary` split. Stage 2 keeps the supervised loss and
adds only the dimensionless **teacher-forced** component fugacity-equilibrium loss

`mean_i[((x_i gamma_i Psat_i - y_i P) / P)^2]`.

Here `T`, `P`, `x`, and `y` are the observed state; this is a training residual,
not a free solver prediction. Continuity, boundary, differentiable-solver, and
chemical-attention-bias loss weights are all exactly zero. The teacher-forced
fugacity weight is `1.0`, with the same
two-epoch linear warmup, five-epoch budget, partial unfreezing, and
validation-only Stage 1 fallback used by the preceding experiment.
