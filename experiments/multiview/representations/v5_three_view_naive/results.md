# v5_three_view_naive results

Status: completed formal evaluation (seeds 0--4).

| Protocol | Task | State MAE | y MAE | Coverage |
|---|---|---:|---:|---:|
| overall_binary_ternary | isobaric (T+y) | 2.5126 ± 0.3710 K | 0.0307 ± 0.0051 | 1.000 ± 0.000 |
| overall_binary_ternary | isothermal (P+y) | 8.2046 ± 3.3088 kPa | 0.0262 ± 0.0046 | 1.000 ± 0.000 |
| unseen_component | isobaric (T+y) | 36.3334 ± 1.5461 K | 0.1193 ± 0.0043 | 1.000 ± 0.000 |
| unseen_component | isothermal (P+y) | 28.9055 ± 7.1440 kPa | 0.1012 ± 0.0156 | 1.000 ± 0.000 |
| binary_to_ternary_zero_shot | isobaric (T+y) | 1.9663 ± 0.7879 K | 0.0722 ± 0.0159 | 1.000 ± 0.000 |
| binary_to_ternary_zero_shot | isothermal (P+y) | 1.7929 ± 0.4701 kPa | 0.0149 ± 0.0023 | 1.000 ± 0.000 |

Machine-readable source: `results/multiview/`.
