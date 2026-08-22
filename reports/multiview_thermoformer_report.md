# Multi-view ThermoFormer report

## 1. Implementation summary

The frozen thermodynamic backbone is unchanged: pair interactions still form `sum(x_i x_j phi_ij)`, activity coefficients still come from composition autograd, and the same differentiable isothermal/isobaric solvers and physics losses are used.

V6 uses 24 train-only-standardized RDKit descriptors, 768 frozen Uni-Mol v2 features, and 28 audited SMARTS occurrence counts (820 raw features total). Independent view projections feed the existing mixture Transformer; three symmetric pair branches and a mixture/state-conditioned softmax gate form `phi_ij`. No additional GNN was introduced.

New modules/assets are under `src/multiview_*`, `assets/`, `scripts/*multiview*`, and `experiments/multiview/`; runner/config/model/representation/provenance seams were extended without changing committed splits.

| Variant | Parameters | Formal runs | Train seconds/run | Peak GPU MB mean / max |
|---|---:|---:|---:|---:|
| V0 Legacy Uni-Mol v2 | 1,780,419 | 15 | 169.7 ± 34.0 | 1650.4 / 1695.3 |
| V1 RDKit descriptors only | 1,637,571 | 15 | 99.8 ± 17.8 | 1633.3 / 1734.3 |
| V5 Three-view naive fusion | 2,015,043 | 15 | 105.2 ± 15.6 | 1905.9 / 2007.3 |
| V6 Interaction-specific multi-view fusion | 2,613,896 | 15 | 194.7 ± 27.4 | 8870.3 / 9912.5 |

## 2. Representation ablation

V0--V6 are implemented. V2 is interface-equivalent to V0. V3 was run as a later, isolated seed-0 exploratory diagnostic to complete the functional-group-only control; it did not influence the locked Stage C matrix. Full seed-0 tables are in `reports/multiview_screening_report.md`.

Exploratory screening showed V1 strongest on unseen components; V4 and V5 degraded that primary target, so simple feature addition was insufficient. V6 improved selected overall/zero-shot directions but did not pass the unseen-component gate. Per the predeclared rule, no further V6 branch ablations were run because V6 had no clear primary-target benefit.

Seed-0 unseen-component representation diagnostic (exploratory; V2 equals V0 by interface):

| Variant | Task | State MAE | y MAE | Coverage |
|---|---|---:|---:|---:|
| V0 Legacy Uni-Mol v2 | isobaric (T+y) | 40.9916 K | 0.1149 | 1.000 |
| V0 Legacy Uni-Mol v2 | isothermal (P+y) | 27.7285 kPa | 0.0808 | 0.998 |
| V1 RDKit descriptors only | isobaric (T+y) | 25.7650 K | 0.0999 | 1.000 |
| V1 RDKit descriptors only | isothermal (P+y) | 20.9613 kPa | 0.0858 | 1.000 |
| V4 RDKit + Uni-Mol naive fusion | isobaric (T+y) | 35.6889 K | 0.1095 | 1.000 |
| V4 RDKit + Uni-Mol naive fusion | isothermal (P+y) | 25.6072 kPa | 0.0950 | 1.000 |
| V5 Three-view naive fusion | isobaric (T+y) | 37.1878 K | 0.1129 | 1.000 |
| V5 Three-view naive fusion | isothermal (P+y) | 29.6872 kPa | 0.1065 | 1.000 |
| V6 Interaction-specific multi-view fusion | isobaric (T+y) | 35.0374 K | 0.1020 | 1.000 |
| V6 Interaction-specific multi-view fusion | isothermal (P+y) | 36.4023 kPa | 0.1147 | 1.000 |
| V3 Functional groups only | isobaric (T+y) | 127.9842 K | 0.1616 | 0.912 |
| V3 Functional groups only | isothermal (P+y) | 14662742.9560 kPa | 0.1942 | 0.698 |

V3 FG-only was numerically weak: its unseen-component isothermal pressure MAE was extremely large and coverage was only about 0.70. This negative control indicates that sparse motif counts cannot replace molecular physicochemical/structural information.

## 3. Overall performance

These five-seed results use fixed splits and complete seed coverage, but the seed-0 test metrics were inspected during Stage B. They are therefore selection-aware evaluation results rather than an untouched-test confirmatory estimate.

| Variant | Protocol | Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | Coverage |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| V0 Legacy Uni-Mol v2 | overall_binary_ternary | isobaric (T+y) | 5.4566 ± 1.4836 K | 7.8774 ± 2.0071 K | 0.9283 ± 0.0254 | 0.0659 ± 0.0142 | 0.0965 ± 0.0155 | 0.9005 ± 0.0327 | 1.000 ± 0.000 |
| V0 Legacy Uni-Mol v2 | overall_binary_ternary | isothermal (P+y) | 16.9887 ± 5.8781 kPa | 38.2395 ± 13.8932 kPa | 0.8845 ± 0.0518 | 0.0685 ± 0.0148 | 0.1032 ± 0.0188 | 0.8947 ± 0.0405 | 1.000 ± 0.000 |
| V0 Legacy Uni-Mol v2 | unseen_component | isobaric (T+y) | 37.8732 ± 3.6302 K | 48.6310 ± 4.1006 K | 0.4151 ± 0.0977 | 0.1266 ± 0.0194 | 0.1708 ± 0.0237 | 0.7761 ± 0.0655 | 1.000 ± 0.000 |
| V0 Legacy Uni-Mol v2 | unseen_component | isothermal (P+y) | 27.3989 ± 0.8662 kPa | 71.9183 ± 5.2130 kPa | 0.4600 ± 0.0764 | 0.0789 ± 0.0180 | 0.1229 ± 0.0244 | 0.8764 ± 0.0512 | 0.998 ± 0.003 |
| V0 Legacy Uni-Mol v2 | binary_to_ternary_zero_shot | isobaric (T+y) | 5.5837 ± 2.0812 K | 6.2417 ± 2.0819 K | 0.9500 ± 0.0303 | 0.0828 ± 0.0153 | 0.1225 ± 0.0164 | 0.7143 ± 0.0889 | 1.000 ± 0.000 |
| V0 Legacy Uni-Mol v2 | binary_to_ternary_zero_shot | isothermal (P+y) | 5.0257 ± 2.9048 kPa | 5.8621 ± 3.1227 kPa | 0.7486 ± 0.2873 | 0.0318 ± 0.0031 | 0.0409 ± 0.0048 | 0.9664 ± 0.0112 | 1.000 ± 0.000 |
| V1 RDKit descriptors only | overall_binary_ternary | isobaric (T+y) | 2.6502 ± 0.3520 K | 4.4997 ± 1.2346 K | 0.9740 ± 0.0185 | 0.0306 ± 0.0047 | 0.0540 ± 0.0124 | 0.9684 ± 0.0138 | 1.000 ± 0.000 |
| V1 RDKit descriptors only | overall_binary_ternary | isothermal (P+y) | 8.5146 ± 3.1801 kPa | 19.0101 ± 7.5815 kPa | 0.9709 ± 0.0170 | 0.0275 ± 0.0032 | 0.0482 ± 0.0089 | 0.9772 ± 0.0079 | 1.000 ± 0.000 |
| V1 RDKit descriptors only | unseen_component | isobaric (T+y) | 28.2520 ± 2.8413 K | 38.0592 ± 3.1515 K | 0.6418 ± 0.0604 | 0.1011 ± 0.0045 | 0.1428 ± 0.0045 | 0.8459 ± 0.0097 | 1.000 ± 0.000 |
| V1 RDKit descriptors only | unseen_component | isothermal (P+y) | 23.0828 ± 2.2172 kPa | 52.5165 ± 2.2055 kPa | 0.7131 ± 0.0243 | 0.0925 ± 0.0050 | 0.1421 ± 0.0071 | 0.8393 ± 0.0159 | 1.000 ± 0.000 |
| V1 RDKit descriptors only | binary_to_ternary_zero_shot | isobaric (T+y) | 2.9256 ± 0.6540 K | 3.5290 ± 0.6933 K | 0.9841 ± 0.0091 | 0.0778 ± 0.0123 | 0.1129 ± 0.0116 | 0.7605 ± 0.0531 | 1.000 ± 0.000 |
| V1 RDKit descriptors only | binary_to_ternary_zero_shot | isothermal (P+y) | 2.9611 ± 1.1353 kPa | 3.3975 ± 1.1373 kPa | 0.9306 ± 0.0673 | 0.0240 ± 0.0028 | 0.0319 ± 0.0039 | 0.9782 ± 0.0118 | 1.000 ± 0.000 |
| V5 Three-view naive fusion | overall_binary_ternary | isobaric (T+y) | 2.5126 ± 0.3710 K | 4.1460 ± 0.9107 K | 0.9789 ± 0.0121 | 0.0307 ± 0.0051 | 0.0541 ± 0.0102 | 0.9687 ± 0.0118 | 1.000 ± 0.000 |
| V5 Three-view naive fusion | overall_binary_ternary | isothermal (P+y) | 8.2046 ± 3.3088 kPa | 19.0171 ± 7.8243 kPa | 0.9697 ± 0.0194 | 0.0262 ± 0.0046 | 0.0457 ± 0.0089 | 0.9795 ± 0.0073 | 1.000 ± 0.000 |
| V5 Three-view naive fusion | unseen_component | isobaric (T+y) | 36.3334 ± 1.5461 K | 46.9445 ± 2.0072 K | 0.4572 ± 0.0455 | 0.1193 ± 0.0043 | 0.1684 ± 0.0061 | 0.7855 ± 0.0156 | 1.000 ± 0.000 |
| V5 Three-view naive fusion | unseen_component | isothermal (P+y) | 28.9055 ± 7.1440 kPa | 63.4726 ± 8.6856 kPa | 0.5753 ± 0.1166 | 0.1012 ± 0.0156 | 0.1606 ± 0.0229 | 0.7919 ± 0.0594 | 1.000 ± 0.000 |
| V5 Three-view naive fusion | binary_to_ternary_zero_shot | isobaric (T+y) | 1.9663 ± 0.7879 K | 2.5768 ± 1.0845 K | 0.9893 ± 0.0107 | 0.0722 ± 0.0159 | 0.1101 ± 0.0133 | 0.7717 ± 0.0587 | 1.000 ± 0.000 |
| V5 Three-view naive fusion | binary_to_ternary_zero_shot | isothermal (P+y) | 1.7929 ± 0.4701 kPa | 2.1828 ± 0.5199 kPa | 0.9707 ± 0.0194 | 0.0149 ± 0.0023 | 0.0206 ± 0.0020 | 0.9914 ± 0.0034 | 1.000 ± 0.000 |
| V6 Interaction-specific multi-view fusion | overall_binary_ternary | isobaric (T+y) | 2.7010 ± 0.4539 K | 4.6408 ± 1.0909 K | 0.9729 ± 0.0164 | 0.0319 ± 0.0058 | 0.0577 ± 0.0140 | 0.9639 ± 0.0166 | 1.000 ± 0.000 |
| V6 Interaction-specific multi-view fusion | overall_binary_ternary | isothermal (P+y) | 7.0342 ± 2.0512 kPa | 14.8414 ± 3.8018 kPa | 0.9825 ± 0.0051 | 0.0232 ± 0.0044 | 0.0420 ± 0.0127 | 0.9821 ± 0.0102 | 1.000 ± 0.000 |
| V6 Interaction-specific multi-view fusion | unseen_component | isobaric (T+y) | 36.7037 ± 1.8896 K | 47.2096 ± 1.9731 K | 0.4511 ± 0.0465 | 0.1112 ± 0.0065 | 0.1529 ± 0.0075 | 0.8230 ± 0.0177 | 1.000 ± 0.000 |
| V6 Interaction-specific multi-view fusion | unseen_component | isothermal (P+y) | 31.7126 ± 8.0805 kPa | 67.6307 ± 9.6256 kPa | 0.5172 ± 0.1382 | 0.1033 ± 0.0210 | 0.1663 ± 0.0326 | 0.7738 ± 0.0860 | 1.000 ± 0.000 |
| V6 Interaction-specific multi-view fusion | binary_to_ternary_zero_shot | isobaric (T+y) | 2.8789 ± 0.8865 K | 3.6999 ± 1.2084 K | 0.9817 ± 0.0112 | 0.0829 ± 0.0140 | 0.1169 ± 0.0142 | 0.7417 ± 0.0717 | 1.000 ± 0.000 |
| V6 Interaction-specific multi-view fusion | binary_to_ternary_zero_shot | isothermal (P+y) | 2.2206 ± 0.7344 kPa | 2.7687 ± 0.9292 kPa | 0.9538 ± 0.0312 | 0.0164 ± 0.0115 | 0.0219 ± 0.0152 | 0.9879 ± 0.0155 | 1.000 ± 0.000 |

## 4. Unseen-component generalization

The unseen-component rows above are the primary evidence. Every seed is shown below; no seed is excluded.

| Variant | Seed | Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | Coverage |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| V0 Legacy Uni-Mol v2 | 0 | isobaric (T+y) | 40.9916 K | 51.9206 K | 0.3371 | 0.1149 | 0.1570 | 0.8137 | 1.000 |
| V0 Legacy Uni-Mol v2 | 0 | isothermal (P+y) | 27.7285 kPa | 74.0068 kPa | 0.4288 | 0.0808 | 0.1213 | 0.8835 | 0.998 |
| V0 Legacy Uni-Mol v2 | 1 | isobaric (T+y) | 35.4455 K | 45.5517 K | 0.4897 | 0.1197 | 0.1621 | 0.8014 | 1.000 |
| V0 Legacy Uni-Mol v2 | 1 | isothermal (P+y) | 28.0726 kPa | 77.0332 kPa | 0.3836 | 0.0750 | 0.1186 | 0.8883 | 1.000 |
| V0 Legacy Uni-Mol v2 | 2 | isobaric (T+y) | 32.9162 K | 43.5629 K | 0.5333 | 0.1103 | 0.1510 | 0.8279 | 1.000 |
| V0 Legacy Uni-Mol v2 | 2 | isothermal (P+y) | 25.9619 kPa | 71.6823 kPa | 0.4641 | 0.0586 | 0.0951 | 0.9283 | 0.998 |
| V0 Legacy Uni-Mol v2 | 3 | isobaric (T+y) | 41.3141 K | 53.2359 K | 0.3030 | 0.1590 | 0.2107 | 0.6648 | 1.000 |
| V0 Legacy Uni-Mol v2 | 3 | isothermal (P+y) | 27.2423 kPa | 63.2457 kPa | 0.5864 | 0.1077 | 0.1623 | 0.7906 | 0.993 |
| V0 Legacy Uni-Mol v2 | 4 | isobaric (T+y) | 38.6988 K | 48.8841 K | 0.4123 | 0.1292 | 0.1734 | 0.7728 | 1.000 |
| V0 Legacy Uni-Mol v2 | 4 | isothermal (P+y) | 27.9896 kPa | 73.6233 kPa | 0.4370 | 0.0725 | 0.1170 | 0.8913 | 1.000 |
| V1 RDKit descriptors only | 0 | isobaric (T+y) | 25.7650 K | 35.5523 K | 0.6892 | 0.0999 | 0.1488 | 0.8327 | 1.000 |
| V1 RDKit descriptors only | 0 | isothermal (P+y) | 20.9613 kPa | 51.5833 kPa | 0.7236 | 0.0858 | 0.1327 | 0.8603 | 1.000 |
| V1 RDKit descriptors only | 1 | isobaric (T+y) | 27.0593 K | 36.1743 K | 0.6782 | 0.0974 | 0.1442 | 0.8430 | 1.000 |
| V1 RDKit descriptors only | 1 | isothermal (P+y) | 22.1077 kPa | 50.1054 kPa | 0.7392 | 0.0899 | 0.1390 | 0.8466 | 1.000 |
| V1 RDKit descriptors only | 2 | isobaric (T+y) | 29.8520 K | 40.0243 K | 0.6060 | 0.1039 | 0.1435 | 0.8445 | 1.000 |
| V1 RDKit descriptors only | 2 | isothermal (P+y) | 26.4683 kPa | 55.6370 kPa | 0.6785 | 0.0973 | 0.1454 | 0.8321 | 1.000 |
| V1 RDKit descriptors only | 3 | isobaric (T+y) | 32.4511 K | 42.6700 K | 0.5522 | 0.1074 | 0.1407 | 0.8504 | 1.000 |
| V1 RDKit descriptors only | 3 | isothermal (P+y) | 21.7747 kPa | 51.4017 kPa | 0.7256 | 0.0923 | 0.1419 | 0.8401 | 1.000 |
| V1 RDKit descriptors only | 4 | isobaric (T+y) | 26.1326 K | 35.8750 K | 0.6835 | 0.0968 | 0.1367 | 0.8589 | 1.000 |
| V1 RDKit descriptors only | 4 | isothermal (P+y) | 24.1022 kPa | 53.8553 kPa | 0.6987 | 0.0973 | 0.1516 | 0.8176 | 1.000 |
| V5 Three-view naive fusion | 0 | isobaric (T+y) | 37.1878 K | 47.4671 K | 0.4459 | 0.1129 | 0.1604 | 0.8057 | 1.000 |
| V5 Three-view naive fusion | 0 | isothermal (P+y) | 29.6872 kPa | 59.9483 kPa | 0.6267 | 0.1065 | 0.1715 | 0.7665 | 1.000 |
| V5 Three-view naive fusion | 1 | isobaric (T+y) | 33.8394 K | 43.6100 K | 0.5323 | 0.1175 | 0.1678 | 0.7874 | 1.000 |
| V5 Three-view naive fusion | 1 | isothermal (P+y) | 39.3275 kPa | 76.1047 kPa | 0.3984 | 0.1233 | 0.1924 | 0.7060 | 1.000 |
| V5 Three-view naive fusion | 2 | isobaric (T+y) | 37.8120 K | 48.8853 K | 0.4123 | 0.1236 | 0.1744 | 0.7703 | 1.000 |
| V5 Three-view naive fusion | 2 | isothermal (P+y) | 25.6469 kPa | 65.9427 kPa | 0.5483 | 0.0833 | 0.1344 | 0.8565 | 1.000 |
| V5 Three-view naive fusion | 3 | isobaric (T+y) | 36.8675 K | 47.9172 K | 0.4354 | 0.1206 | 0.1746 | 0.7697 | 1.000 |
| V5 Three-view naive fusion | 3 | isothermal (P+y) | 19.7978 kPa | 52.3620 kPa | 0.7152 | 0.0896 | 0.1439 | 0.8356 | 1.000 |
| V5 Three-view naive fusion | 4 | isobaric (T+y) | 35.9602 K | 46.8432 K | 0.4604 | 0.1221 | 0.1650 | 0.7943 | 1.000 |
| V5 Three-view naive fusion | 4 | isothermal (P+y) | 30.0683 kPa | 63.0056 kPa | 0.5877 | 0.1033 | 0.1607 | 0.7950 | 1.000 |
| V6 Interaction-specific multi-view fusion | 0 | isobaric (T+y) | 35.0374 K | 45.2927 K | 0.4955 | 0.1020 | 0.1467 | 0.8375 | 1.000 |
| V6 Interaction-specific multi-view fusion | 0 | isothermal (P+y) | 36.4023 kPa | 72.8665 kPa | 0.4485 | 0.1147 | 0.1837 | 0.7320 | 1.000 |
| V6 Interaction-specific multi-view fusion | 1 | isobaric (T+y) | 37.5797 K | 47.8776 K | 0.4363 | 0.1084 | 0.1499 | 0.8302 | 1.000 |
| V6 Interaction-specific multi-view fusion | 1 | isothermal (P+y) | 42.3219 kPa | 81.0675 kPa | 0.3174 | 0.1306 | 0.2083 | 0.6556 | 1.000 |
| V6 Interaction-specific multi-view fusion | 2 | isobaric (T+y) | 35.3584 K | 46.1668 K | 0.4759 | 0.1154 | 0.1568 | 0.8142 | 1.000 |
| V6 Interaction-specific multi-view fusion | 2 | isothermal (P+y) | 24.4357 kPa | 60.5344 kPa | 0.6194 | 0.0863 | 0.1483 | 0.8253 | 1.000 |
| V6 Interaction-specific multi-view fusion | 3 | isobaric (T+y) | 39.5947 K | 50.3225 K | 0.3772 | 0.1188 | 0.1642 | 0.7963 | 1.000 |
| V6 Interaction-specific multi-view fusion | 3 | isothermal (P+y) | 23.1464 kPa | 57.0842 kPa | 0.6615 | 0.0789 | 0.1232 | 0.8795 | 1.000 |
| V6 Interaction-specific multi-view fusion | 4 | isobaric (T+y) | 35.9483 K | 46.3884 K | 0.4708 | 0.1116 | 0.1469 | 0.8370 | 1.000 |
| V6 Interaction-specific multi-view fusion | 4 | isothermal (P+y) | 32.2565 kPa | 66.6007 kPa | 0.5393 | 0.1061 | 0.1678 | 0.7763 | 1.000 |

## 5. Binary-to-ternary zero-shot

The zero-shot rows use the unchanged fixed ternary test set and train-only binary subsystem coverage.

## 6. Gate analysis

| Protocol | View | Mean weight across seeds | Seed SD |
|---|---|---:|---:|
| binary_to_ternary_zero_shot | functional_group | 0.0107 | 0.0214 |
| binary_to_ternary_zero_shot | rdkit | 0.8032 | 0.4366 |
| binary_to_ternary_zero_shot | unimol | 0.1861 | 0.4153 |
| overall_binary_ternary | functional_group | 0.0400 | 0.0540 |
| overall_binary_ternary | rdkit | 0.9548 | 0.0593 |
| overall_binary_ternary | unimol | 0.0052 | 0.0065 |
| state_composition_interpolation | functional_group | 0.0015 | NA |
| state_composition_interpolation | rdkit | 0.9982 | NA |
| state_composition_interpolation | unimol | 0.0003 | NA |
| unseen_component | functional_group | 0.0652 | 0.0579 |
| unseen_component | rdkit | 0.9213 | 0.0561 |
| unseen_component | unimol | 0.0134 | 0.0137 |

The gate largely collapsed onto RDKit (about 0.95 overall and 0.92 for unseen components); functional-group weights remained small and Uni-Mol was usually near zero. Zero-shot was seed-unstable: seed 4 switched to approximately 0.93 Uni-Mol while the other seeds were nearly all RDKit. The state-interpolation seed-0 diagnostic supplies the known-mixture stratum; it is not pooled as five-seed evidence. These are learned associations, not causal feature importance. Full known/unseen, chemical-family, and composition-region strata are in `results/multiview/analysis/multiview_gate_statistics.csv`.

## 7. Conclusion

1. **Why RDKit can beat Uni-Mol-only:** the compact descriptors expose molecular size, polarity, hydrogen bonding, topology and charge in a low-data-friendly form. Formally, V1 improved unseen-component P/T and isobaric y over V0, although V0 retained better isothermal y.
2. **Does Uni-Mol add robust value on top of RDKit?** Not for the primary target in the tested fusion schemes. V4 screening and V5/V6 formal unseen-component results were worse than V1.
3. **Do functional-group interactions improve unseen components?** No. V5 degraded all four primary MAE outputs relative to V1; V6 also remained worse, and its learned functional-group gate weight was small.
4. **Is interaction-specific fusion better than naive concatenation?** Only conditionally. V6 improved V5's overall isothermal P/y, but it was worse on unseen-component P/T and did not beat V5 zero-shot. It also used more parameters and roughly doubled training time.
5. **Should V6 replace ThermoFormer?** No. The predeclared primary objective failed and seed variance increased. V1 is the preferred candidate when unseen-component state prediction is primary; retain V0 when isothermal vapor-composition accuracy is paramount, and V5 when fixed-molecule binary-to-ternary transfer is the sole target. No single model dominates every task.
