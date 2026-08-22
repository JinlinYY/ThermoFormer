# Multi-view ThermoFormer seed-0 screening

All rows use committed seed-0 splits and validation-only checkpoint selection. Because Stage B inspected held-out test metrics before the repeated five-seed Stage C evaluation, this table is test-exposed exploratory evidence, not an independent confirmatory test. V3 was added later in the isolated `screening_exploratory` namespace and did not affect Stage C evaluation.

| Variant | Protocol | Task | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | Valid coverage | Train s | Params |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V0 Legacy Uni-Mol v2 | overall_binary | isobaric (T+y) | 4.4013 K | 6.2220 K | 0.9691 | 0.0432 | 0.0636 | 0.9581 | 1.000 | 124.1 | 1,780,419 |
| V0 Legacy Uni-Mol v2 | overall_binary | isothermal (P+y) | 9.0466 kPa | 20.2742 kPa | 0.9567 | 0.0661 | 0.1004 | 0.9066 | 1.000 | 124.1 | 1,780,419 |
| V0 Legacy Uni-Mol v2 | overall_binary_ternary | isobaric (T+y) | 8.0748 K | 11.2196 K | 0.8956 | 0.0894 | 0.1212 | 0.8487 | 1.000 | 129.7 | 1,780,419 |
| V0 Legacy Uni-Mol v2 | overall_binary_ternary | isothermal (P+y) | 14.3419 kPa | 31.2910 kPa | 0.8828 | 0.0932 | 0.1341 | 0.8277 | 1.000 | 129.7 | 1,780,419 |
| V0 Legacy Uni-Mol v2 | state_composition_interpolation | isobaric (T+y) | 1.7498 K | 2.2765 K | 0.9922 | 0.0336 | 0.0491 | 0.9664 | 1.000 | 247.0 | 1,780,419 |
| V0 Legacy Uni-Mol v2 | state_composition_interpolation | isothermal (P+y) | 4.6069 kPa | 8.7672 kPa | 0.9877 | 0.0275 | 0.0367 | 0.9821 | 1.000 | 247.0 | 1,780,419 |
| V0 Legacy Uni-Mol v2 | unseen_component | isobaric (T+y) | 40.9916 K | 51.9206 K | 0.3371 | 0.1149 | 0.1570 | 0.8137 | 1.000 | 155.9 | 1,780,419 |
| V0 Legacy Uni-Mol v2 | unseen_component | isothermal (P+y) | 27.7285 kPa | 74.0068 kPa | 0.4288 | 0.0808 | 0.1213 | 0.8835 | 0.998 | 155.9 | 1,780,419 |
| V0 Legacy Uni-Mol v2 | binary_to_ternary_zero_shot | isobaric (T+y) | 8.3064 K | 9.0387 K | 0.9280 | 0.1002 | 0.1444 | 0.5751 | 1.000 | 179.3 | 1,780,419 |
| V0 Legacy Uni-Mol v2 | binary_to_ternary_zero_shot | isothermal (P+y) | 3.3236 kPa | 4.1450 kPa | 0.9613 | 0.0371 | 0.0488 | 0.9639 | 1.000 | 179.3 | 1,780,419 |
| V1 RDKit descriptors only | overall_binary | isobaric (T+y) | 2.4312 K | 4.5582 K | 0.9834 | 0.0287 | 0.0449 | 0.9791 | 1.000 | 90.1 | 1,637,571 |
| V1 RDKit descriptors only | overall_binary | isothermal (P+y) | 5.1714 kPa | 13.1407 kPa | 0.9818 | 0.0290 | 0.0563 | 0.9706 | 1.000 | 90.1 | 1,637,571 |
| V1 RDKit descriptors only | overall_binary_ternary | isobaric (T+y) | 2.5167 K | 3.8900 K | 0.9874 | 0.0257 | 0.0407 | 0.9829 | 1.000 | 107.3 | 1,637,571 |
| V1 RDKit descriptors only | overall_binary_ternary | isothermal (P+y) | 6.0039 kPa | 14.5443 kPa | 0.9747 | 0.0256 | 0.0526 | 0.9735 | 1.000 | 107.3 | 1,637,571 |
| V1 RDKit descriptors only | state_composition_interpolation | isobaric (T+y) | 1.0210 K | 1.3156 K | 0.9974 | 0.0186 | 0.0347 | 0.9832 | 1.000 | 121.9 | 1,637,571 |
| V1 RDKit descriptors only | state_composition_interpolation | isothermal (P+y) | 2.5077 kPa | 5.9868 kPa | 0.9943 | 0.0132 | 0.0172 | 0.9960 | 1.000 | 121.9 | 1,637,571 |
| V1 RDKit descriptors only | unseen_component | isobaric (T+y) | 25.7650 K | 35.5523 K | 0.6892 | 0.0999 | 0.1488 | 0.8327 | 1.000 | 118.8 | 1,637,571 |
| V1 RDKit descriptors only | unseen_component | isothermal (P+y) | 20.9613 kPa | 51.5833 kPa | 0.7236 | 0.0858 | 0.1327 | 0.8603 | 1.000 | 118.8 | 1,637,571 |
| V1 RDKit descriptors only | binary_to_ternary_zero_shot | isobaric (T+y) | 3.8118 K | 4.2385 K | 0.9842 | 0.0897 | 0.1265 | 0.6743 | 1.000 | 149.7 | 1,637,571 |
| V1 RDKit descriptors only | binary_to_ternary_zero_shot | isothermal (P+y) | 3.9390 kPa | 4.5383 kPa | 0.9536 | 0.0198 | 0.0254 | 0.9902 | 1.000 | 149.7 | 1,637,571 |
| V4 RDKit + Uni-Mol naive fusion | overall_binary | isobaric (T+y) | 2.8412 K | 5.0239 K | 0.9799 | 0.0331 | 0.0558 | 0.9677 | 1.000 | 97.1 | 1,934,787 |
| V4 RDKit + Uni-Mol naive fusion | overall_binary | isothermal (P+y) | 4.0626 kPa | 8.4306 kPa | 0.9925 | 0.0328 | 0.0587 | 0.9680 | 1.000 | 97.1 | 1,934,787 |
| V4 RDKit + Uni-Mol naive fusion | overall_binary_ternary | isobaric (T+y) | 2.7917 K | 4.2023 K | 0.9854 | 0.0299 | 0.0503 | 0.9739 | 1.000 | 107.7 | 1,934,787 |
| V4 RDKit + Uni-Mol naive fusion | overall_binary_ternary | isothermal (P+y) | 4.1558 kPa | 7.3650 kPa | 0.9935 | 0.0286 | 0.0497 | 0.9763 | 1.000 | 107.7 | 1,934,787 |
| V4 RDKit + Uni-Mol naive fusion | state_composition_interpolation | isobaric (T+y) | 0.9913 K | 1.3438 K | 0.9973 | 0.0203 | 0.0359 | 0.9821 | 1.000 | 121.5 | 1,934,787 |
| V4 RDKit + Uni-Mol naive fusion | state_composition_interpolation | isothermal (P+y) | 2.5702 kPa | 6.0404 kPa | 0.9942 | 0.0144 | 0.0208 | 0.9942 | 1.000 | 121.5 | 1,934,787 |
| V4 RDKit + Uni-Mol naive fusion | unseen_component | isobaric (T+y) | 35.6889 K | 46.4964 K | 0.4683 | 0.1095 | 0.1598 | 0.8071 | 1.000 | 105.7 | 1,934,787 |
| V4 RDKit + Uni-Mol naive fusion | unseen_component | isothermal (P+y) | 25.6072 kPa | 55.4138 kPa | 0.6810 | 0.0950 | 0.1438 | 0.8357 | 1.000 | 105.7 | 1,934,787 |
| V4 RDKit + Uni-Mol naive fusion | binary_to_ternary_zero_shot | isobaric (T+y) | 2.1868 K | 3.1000 K | 0.9915 | 0.0911 | 0.1288 | 0.6620 | 1.000 | 185.3 | 1,934,787 |
| V4 RDKit + Uni-Mol naive fusion | binary_to_ternary_zero_shot | isothermal (P+y) | 1.2517 kPa | 1.7867 kPa | 0.9928 | 0.0119 | 0.0170 | 0.9956 | 1.000 | 185.3 | 1,934,787 |
| V5 Three-view naive fusion | overall_binary | isobaric (T+y) | 3.3952 K | 5.2158 K | 0.9783 | 0.0322 | 0.0514 | 0.9726 | 1.000 | 97.1 | 2,015,043 |
| V5 Three-view naive fusion | overall_binary | isothermal (P+y) | 4.6452 kPa | 9.0042 kPa | 0.9915 | 0.0290 | 0.0525 | 0.9744 | 1.000 | 97.1 | 2,015,043 |
| V5 Three-view naive fusion | overall_binary_ternary | isobaric (T+y) | 2.6242 K | 4.2825 K | 0.9848 | 0.0313 | 0.0517 | 0.9725 | 1.000 | 95.0 | 2,015,043 |
| V5 Three-view naive fusion | overall_binary_ternary | isothermal (P+y) | 5.7368 kPa | 16.2566 kPa | 0.9684 | 0.0304 | 0.0522 | 0.9739 | 1.000 | 95.0 | 2,015,043 |
| V5 Three-view naive fusion | state_composition_interpolation | isobaric (T+y) | 0.9604 K | 1.3544 K | 0.9973 | 0.0184 | 0.0352 | 0.9827 | 1.000 | 116.3 | 2,015,043 |
| V5 Three-view naive fusion | state_composition_interpolation | isothermal (P+y) | 2.3391 kPa | 5.9309 kPa | 0.9944 | 0.0128 | 0.0179 | 0.9957 | 1.000 | 116.3 | 2,015,043 |
| V5 Three-view naive fusion | unseen_component | isobaric (T+y) | 37.1878 K | 47.4671 K | 0.4459 | 0.1129 | 0.1604 | 0.8057 | 1.000 | 111.4 | 2,015,043 |
| V5 Three-view naive fusion | unseen_component | isothermal (P+y) | 29.6872 kPa | 59.9483 kPa | 0.6267 | 0.1065 | 0.1715 | 0.7665 | 1.000 | 111.4 | 2,015,043 |
| V5 Three-view naive fusion | binary_to_ternary_zero_shot | isobaric (T+y) | 1.6741 K | 2.1343 K | 0.9960 | 0.0861 | 0.1260 | 0.6768 | 1.000 | 147.1 | 2,015,043 |
| V5 Three-view naive fusion | binary_to_ternary_zero_shot | isothermal (P+y) | 1.3820 kPa | 1.7669 kPa | 0.9930 | 0.0116 | 0.0177 | 0.9953 | 1.000 | 147.1 | 2,015,043 |
| V6 Interaction-specific multi-view fusion | overall_binary | isobaric (T+y) | 2.5403 K | 4.4124 K | 0.9845 | 0.0269 | 0.0448 | 0.9792 | 1.000 | 163.0 | 2,613,896 |
| V6 Interaction-specific multi-view fusion | overall_binary | isothermal (P+y) | 5.1819 kPa | 12.1258 kPa | 0.9845 | 0.0287 | 0.0508 | 0.9761 | 1.000 | 163.0 | 2,613,896 |
| V6 Interaction-specific multi-view fusion | overall_binary_ternary | isobaric (T+y) | 2.4044 K | 4.1763 K | 0.9855 | 0.0314 | 0.0494 | 0.9748 | 1.000 | 184.4 | 2,613,896 |
| V6 Interaction-specific multi-view fusion | overall_binary_ternary | isothermal (P+y) | 4.6470 kPa | 9.6617 kPa | 0.9888 | 0.0252 | 0.0461 | 0.9796 | 1.000 | 184.4 | 2,613,896 |
| V6 Interaction-specific multi-view fusion | state_composition_interpolation | isobaric (T+y) | 0.9893 K | 1.3831 K | 0.9971 | 0.0217 | 0.0413 | 0.9762 | 1.000 | 192.9 | 2,613,896 |
| V6 Interaction-specific multi-view fusion | state_composition_interpolation | isothermal (P+y) | 2.4786 kPa | 5.9345 kPa | 0.9944 | 0.0143 | 0.0198 | 0.9948 | 1.000 | 192.9 | 2,613,896 |
| V6 Interaction-specific multi-view fusion | unseen_component | isobaric (T+y) | 35.0374 K | 45.2927 K | 0.4955 | 0.1020 | 0.1467 | 0.8375 | 1.000 | 175.9 | 2,613,896 |
| V6 Interaction-specific multi-view fusion | unseen_component | isothermal (P+y) | 36.4023 kPa | 72.8665 kPa | 0.4485 | 0.1147 | 0.1837 | 0.7320 | 1.000 | 175.9 | 2,613,896 |
| V6 Interaction-specific multi-view fusion | binary_to_ternary_zero_shot | isobaric (T+y) | 3.1022 K | 3.9331 K | 0.9864 | 0.0998 | 0.1361 | 0.6229 | 1.000 | 205.4 | 2,613,896 |
| V6 Interaction-specific multi-view fusion | binary_to_ternary_zero_shot | isothermal (P+y) | 1.3505 kPa | 1.8614 kPa | 0.9922 | 0.0073 | 0.0105 | 0.9983 | 1.000 | 205.4 | 2,613,896 |
| V3 Functional groups only | overall_binary | isobaric (T+y) | 48.9937 K | 90.6761 K | -5.4688 | 0.2438 | 0.3313 | -0.1540 | 0.981 | 72.4 | 1,638,339 |
| V3 Functional groups only | overall_binary | isothermal (P+y) | 59.7814 kPa | 108.5581 kPa | -0.2976 | 0.1423 | 0.2132 | 0.6685 | 0.534 | 72.4 | 1,638,339 |
| V3 Functional groups only | overall_binary_ternary | isobaric (T+y) | 24.1535 K | 38.3833 K | -0.2200 | 0.1956 | 0.2687 | 0.2537 | 0.998 | 56.4 | 1,638,339 |
| V3 Functional groups only | overall_binary_ternary | isothermal (P+y) | 35.8824 kPa | 114.7978 kPa | -0.6892 | 0.1757 | 0.2688 | 0.4151 | 0.651 | 56.4 | 1,638,339 |
| V3 Functional groups only | state_composition_interpolation | isobaric (T+y) | 14.7785 K | 20.3383 K | 0.3777 | 0.1917 | 0.2424 | 0.1826 | 0.974 | 76.8 | 1,638,339 |
| V3 Functional groups only | state_composition_interpolation | isothermal (P+y) | 31.4111 kPa | 66.7078 kPa | 0.4720 | 0.1614 | 0.2283 | 0.4726 | 0.340 | 76.8 | 1,638,339 |
| V3 Functional groups only | unseen_component | isobaric (T+y) | 127.9842 K | 158.0213 K | -4.7137 | 0.1616 | 0.2381 | 0.5775 | 0.912 | 126.3 | 1,638,339 |
| V3 Functional groups only | unseen_component | isothermal (P+y) | 14662742.9560 kPa | 108349349.5734 kPa | -1011689041750.7903 | 0.1942 | 0.2908 | 0.3617 | 0.698 | 126.3 | 1,638,339 |
| V3 Functional groups only | binary_to_ternary_zero_shot | isobaric (T+y) | 9.3092 K | 11.6083 K | 0.8812 | 0.2085 | 0.2461 | -0.2332 | 1.000 | 63.8 | 1,638,339 |
| V3 Functional groups only | binary_to_ternary_zero_shot | isothermal (P+y) | 13.0944 kPa | 17.5753 kPa | 0.0162 | 0.1289 | 0.2260 | 0.4675 | 0.229 | 63.8 | 1,638,339 |

Primary exploratory criterion: unseen-component P/T/y performance. Overall, state-interpolation, and binary-to-ternary rows are retained as non-degradation constraints; no test row is removed. The five-seed table must therefore be interpreted as selection-aware evidence, not an untouched-test confirmation.
