# C1 fugacity + stronger pure-vapor-pressure anchoring

This seed-0 experiment uses the registered `overall_binary_ternary` split and
the same committed supervised C1 checkpoint as the fugacity-only comparison.

The retained supervised objective already applies the endpoint pure-component
vapor-pressure anchor with weight `0.5`. During Stage 2 only, this variant adds
another anchor weight of `0.5`, under the same two-epoch warmup. The effective
anchor coefficient is therefore `0.75` in physics epoch 1 and `1.0` from epoch
2 onward. The teacher-forced fugacity-equilibrium weight remains `1.0`;
continuity, boundary, differentiable-solver, and chemical-bias weights remain
zero. Checkpoint selection uses validation data only.
