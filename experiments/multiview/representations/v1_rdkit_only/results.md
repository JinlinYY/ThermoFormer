# v1_rdkit_only results

Status: completed formal evaluation (seeds 0--4).

| Protocol | Task | State MAE | y MAE | Coverage |
|---|---|---:|---:|---:|
| overall_binary_ternary | isobaric (T+y) | 2.6502 ± 0.3520 K | 0.0306 ± 0.0047 | 1.000 ± 0.000 |
| overall_binary_ternary | isothermal (P+y) | 8.5146 ± 3.1801 kPa | 0.0275 ± 0.0032 | 1.000 ± 0.000 |
| unseen_component | isobaric (T+y) | 28.2520 ± 2.8413 K | 0.1011 ± 0.0045 | 1.000 ± 0.000 |
| unseen_component | isothermal (P+y) | 23.0828 ± 2.2172 kPa | 0.0925 ± 0.0050 | 1.000 ± 0.000 |
| binary_to_ternary_zero_shot | isobaric (T+y) | 2.9256 ± 0.6540 K | 0.0778 ± 0.0123 | 1.000 ± 0.000 |
| binary_to_ternary_zero_shot | isothermal (P+y) | 2.9611 ± 1.1353 kPa | 0.0240 ± 0.0028 | 1.000 ± 0.000 |

Machine-readable source: `results/multiview/`.
