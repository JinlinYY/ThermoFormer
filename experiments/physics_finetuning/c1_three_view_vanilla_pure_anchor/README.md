# C1 pure-vapor-pressure-anchor-only fine-tuning

This controlled seed-0 experiment reuses the committed C1 supervised checkpoint
and registered `overall_binary_ternary` split. Stage 2 retains the complete
supervised objective and adds only `0.5` extra weight on the endpoint
pure-component vapor-pressure anchor. The existing supervised anchor weight is
`0.5`, so the effective coefficient is `0.75` in physics epoch 1 and `1.0` from
epoch 2 onward.

Teacher-forced fugacity, continuity, boundary, differentiable-solver, and
chemical-attention-bias weights are all zero. Selection uses validation data;
the test partition is evaluated only after selection.
