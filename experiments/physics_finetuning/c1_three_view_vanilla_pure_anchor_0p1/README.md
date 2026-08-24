# Exploratory C1 pure-anchor weight 0.1

This experiment changes only the Stage-2 additional pure-component
vapor-pressure anchor from `0.5` to `0.1`. The retained supervised anchor is
`0.5`, giving an effective coefficient of `0.55` in epoch 1 and `0.6` from
epoch 2 onward. All other thermodynamic loss weights remain zero.

Because the earlier seed-0 test results influenced this choice, this run is
explicitly exploratory/test-exposed. It must not be presented as independent
confirmatory evidence or used to claim that `0.1` is an optimized weight.
