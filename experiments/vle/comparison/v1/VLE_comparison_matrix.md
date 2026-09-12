# VLE current-data paper comparison matrix

All values are mean ± sample standard deviation across frozen seeds 0–4. Model selection uses validation only; test labels are used only for final evaluation.

Joint adapted rows with component scopes `3` and `2+3` are two reports from the same per-seed joint checkpoint, not separately selected models.

UALF-GNN isothermal P/y remains N/A: its registered native direction is isobaric only, and its executable input/target contract is `(P, x) -> (T, y)`.

| Model | Train → test | Direction | Components | Status | Seeds | State MAE | State RMSE | State R² | y MAE | y RMSE | y R² | Coverage | Solver failure |
|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Descriptor ANN | binary → binary | isobaric | 2 | blocked_external_assets | 0/5 | N/A | N/A | N/A | N/A | N/A | N/A | 0.0000 ± 0.0000 | N/A |
| Descriptor ANN | binary → binary | isothermal | 2 | not_applicable | 0/5 | N/A | N/A | N/A | N/A | N/A | N/A | 0.0000 ± 0.0000 | N/A |
| GDI-GNN | binary → binary | isobaric | 2 | not_applicable | 0/5 | N/A | N/A | N/A | N/A | N/A | N/A | 0.0000 ± 0.0000 | N/A |
| GDI-GNN | binary → binary | isothermal | 2 | evaluated_partial_seeds | 3/5 | 1.4520 ± 0.5170 | 1.6458 ± 0.4292 | -21.8678 ± 39.0954 | 0.0628 ± 0.0429 | 0.0857 ± 0.0616 | 0.8263 ± 0.1482 | 0.0229 ± 0.0238 | N/A |
| GE-GNN | binary → binary | isobaric | 2 | not_applicable | 0/5 | N/A | N/A | N/A | N/A | N/A | N/A | 0.0000 ± 0.0000 | N/A |
| GE-GNN | binary → binary | isothermal | 2 | evaluated_partial_seeds | 3/5 | 1.9300 ± 1.3418 | 2.0999 ± 1.1982 | -60.3433 ± 105.7365 | 0.0603 ± 0.0485 | 0.0830 ± 0.0674 | 0.8252 ± 0.1511 | 0.0229 ± 0.0238 | N/A |
| HANNA adapted | binary → binary | isobaric | 2 | evaluated | 5/5 | 5.7022 ± 1.5325 | 19.0862 ± 9.7434 | 0.4343 ± 0.5663 | 0.0592 ± 0.0135 | 0.1365 ± 0.0246 | 0.8025 ± 0.0783 | 0.9606 ± 0.0236 | 0.0394 ± 0.0236 |
| HANNA adapted | binary → binary | isothermal | 2 | evaluated | 5/5 | 6.8884 ± 2.7591 | 18.8300 ± 9.3680 | 0.9776 ± 0.0223 | 0.0164 ± 0.0036 | 0.0339 ± 0.0079 | 0.9890 ± 0.0062 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| SMILES-RNN | binary → binary | isobaric | 2 | evaluated | 5/5 | 25.9875 ± 5.7669 | 32.7500 ± 7.2620 | -0.5159 ± 0.7404 | 0.2287 ± 0.0253 | 0.2722 ± 0.0285 | 0.2255 ± 0.1343 | 1.0000 ± 0.0000 | N/A |
| SMILES-RNN | binary → binary | isothermal | 2 | evaluated | 5/5 | 85.8780 ± 14.6561 | 117.1789 ± 21.4985 | 0.2465 ± 0.2040 | 0.1817 ± 0.0352 | 0.2306 ± 0.0403 | 0.5214 ± 0.1446 | 1.0000 ± 0.0000 | N/A |
| TeNNet-SAC adapted | binary → binary | isobaric | 2 | evaluated | 5/5 | 6.7393 ± 2.4900 | 19.6995 ± 10.8427 | 0.4275 ± 0.5812 | 0.0670 ± 0.0139 | 0.1441 ± 0.0271 | 0.7804 ± 0.0811 | 0.9625 ± 0.0152 | 0.0375 ± 0.0152 |
| TeNNet-SAC adapted | binary → binary | isothermal | 2 | evaluated | 5/5 | 8.5089 ± 2.2046 | 21.3216 ± 7.2688 | 0.9735 ± 0.0182 | 0.0227 ± 0.0049 | 0.0431 ± 0.0109 | 0.9821 ± 0.0092 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| ThermoFormer | binary → binary | isobaric | 2 | evaluated | 5/5 | 2.3098 ± 0.4622 | 4.0700 ± 1.0666 | 0.9781 ± 0.0070 | 0.0285 ± 0.0044 | 0.0476 ± 0.0067 | 0.9761 ± 0.0058 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| ThermoFormer | binary → binary | isothermal | 2 | evaluated | 5/5 | 10.6722 ± 2.8012 | 24.8619 ± 8.9927 | 0.9628 ± 0.0232 | 0.0295 ± 0.0090 | 0.0545 ± 0.0177 | 0.9706 ± 0.0211 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| UALF-GNN | binary → binary | isobaric | 2 | evaluated | 5/5 | 21.2896 ± 1.8611 | 26.3803 ± 1.6898 | 0.0614 ± 0.1907 | 0.1324 ± 0.0179 | 0.1673 ± 0.0213 | 0.7064 ± 0.0656 | 1.0000 ± 0.0000 | N/A |
| UALF-GNN | binary → binary | isothermal | 2 | not_applicable_native_direction_isobaric_only | 0/5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| HANNA official | external → joint | isobaric | 2+3 | evaluated | 5/5 | 5.8948 ± 1.7356 | 17.6024 ± 6.7361 | 0.5476 ± 0.3168 | 0.0639 ± 0.0172 | 0.1408 ± 0.0283 | 0.7881 ± 0.0811 | 0.9522 ± 0.0291 | 0.0478 ± 0.0291 |
| HANNA official | external → joint | isothermal | 2+3 | evaluated | 5/5 | 6.7299 ± 4.5743 | 25.5570 ± 25.3981 | 0.9222 ± 0.1471 | 0.0160 ± 0.0056 | 0.0367 ± 0.0187 | 0.9841 ± 0.0191 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| HANNA official | external → joint | isobaric | 3 | evaluated | 5/5 | 11.5791 ± 11.9774 | 18.9834 ± 13.8750 | -10.9268 ± 23.7104 | 0.1398 ± 0.1376 | 0.2022 ± 0.1399 | 0.3750 ± 0.6835 | 0.8144 ± 0.1818 | 0.1856 ± 0.1818 |
| HANNA official | external → joint | isothermal | 3 | evaluated_partial_seeds | 4/5 | 7.7641 ± 13.6227 | 33.9129 ± 65.5135 | -9.4231 ± 20.8362 | 0.0167 ± 0.0127 | 0.0362 ± 0.0452 | 0.9591 ± 0.0764 | 0.8000 ± 0.4472 | 0.0000 ± 0.0000 |
| SPT-NRTL official | external → joint | isobaric | 2+3 | evaluated | 5/5 | 7.1613 ± 2.4492 | 20.2236 ± 6.8344 | 0.4095 ± 0.3151 | 0.0728 ± 0.0187 | 0.1544 ± 0.0341 | 0.7425 ± 0.0953 | 0.9507 ± 0.0225 | 0.0377 ± 0.0177 |
| SPT-NRTL official | external → joint | isothermal | 2+3 | evaluated | 5/5 | 5.4175 ± 1.9815 | 15.9184 ± 7.6429 | 0.9823 ± 0.0148 | 0.0186 ± 0.0045 | 0.0356 ± 0.0082 | 0.9875 ± 0.0070 | 0.9668 ± 0.0324 | 0.0000 ± 0.0000 |
| SPT-NRTL official | external → joint | isobaric | 3 | evaluated | 5/5 | 23.3396 ± 26.4137 | 37.1529 ± 37.3285 | -27.6986 ± 51.3952 | 0.1703 ± 0.1535 | 0.2524 ± 0.1667 | -0.0664 ± 1.1099 | 0.9132 ± 0.0628 | 0.0868 ± 0.0628 |
| SPT-NRTL official | external → joint | isothermal | 3 | evaluated_partial_seeds | 3/5 | 1.9146 ± 0.6411 | 2.7982 ± 1.0911 | 0.9721 ± 0.0202 | 0.0161 ± 0.0081 | 0.0264 ± 0.0175 | 0.9857 ± 0.0135 | 0.6000 ± 0.5477 | 0.0000 ± 0.0000 |
| TeNNet-SAC official | external → joint | isobaric | 2+3 | evaluated | 5/5 | 6.4333 ± 1.8740 | 16.8295 ± 4.9119 | 0.6176 ± 0.1586 | 0.0720 ± 0.0173 | 0.1478 ± 0.0308 | 0.7661 ± 0.0857 | 0.9556 ± 0.0215 | 0.0444 ± 0.0215 |
| TeNNet-SAC official | external → joint | isothermal | 2+3 | evaluated | 5/5 | 7.4945 ± 1.4237 | 19.5322 ± 6.0313 | 0.9753 ± 0.0163 | 0.0221 ± 0.0039 | 0.0421 ± 0.0106 | 0.9823 ± 0.0094 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| TeNNet-SAC official | external → joint | isobaric | 3 | evaluated | 5/5 | 8.2858 ± 7.1557 | 11.5401 ± 6.1737 | -1.9277 ± 5.8134 | 0.1322 ± 0.1225 | 0.1828 ± 0.1336 | 0.4664 ± 0.5739 | 0.8092 ± 0.1965 | 0.1908 ± 0.1965 |
| TeNNet-SAC official | external → joint | isothermal | 3 | evaluated_partial_seeds | 4/5 | 3.8331 ± 1.9275 | 7.2729 ± 7.7363 | 0.7601 ± 0.3962 | 0.0202 ± 0.0036 | 0.0340 ± 0.0174 | 0.9803 ± 0.0208 | 0.8000 ± 0.4472 | 0.0000 ± 0.0000 |
| ThermoFormer | joint → binary | isobaric | 2 | evaluated | 5/5 | 2.1721 ± 0.4957 | 3.8770 ± 0.9962 | 0.9798 ± 0.0083 | 0.0273 ± 0.0029 | 0.0456 ± 0.0048 | 0.9783 ± 0.0039 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| ThermoFormer | joint → binary | isothermal | 2 | evaluated | 5/5 | 11.6388 ± 3.8551 | 29.0346 ± 9.8729 | 0.9484 ± 0.0306 | 0.0273 ± 0.0064 | 0.0489 ± 0.0123 | 0.9768 ± 0.0134 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| HANNA adapted | joint → joint | isobaric | 2+3 | evaluated | 5/5 | 5.9293 ± 1.5130 | 20.6453 ± 9.0664 | 0.3015 ± 0.5813 | 0.0645 ± 0.0166 | 0.1412 ± 0.0272 | 0.7860 ± 0.0779 | 0.9529 ± 0.0281 | 0.0471 ± 0.0281 |
| HANNA adapted | joint → joint | isothermal | 2+3 | evaluated | 5/5 | 7.5386 ± 4.7170 | 25.1558 ± 23.5029 | 0.9291 ± 0.1296 | 0.0161 ± 0.0055 | 0.0368 ± 0.0185 | 0.9842 ± 0.0188 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| HANNA adapted | joint → joint | isobaric | 3 | evaluated | 5/5 | 11.0403 ± 11.0678 | 18.1354 ± 12.7574 | -9.3629 ± 20.2840 | 0.1378 ± 0.1340 | 0.1998 ± 0.1360 | 0.3931 ± 0.6511 | 0.8167 ± 0.1837 | 0.1833 ± 0.1837 |
| HANNA adapted | joint → joint | isothermal | 3 | evaluated_partial_seeds | 4/5 | 7.5190 ± 12.5800 | 31.4648 ± 60.0387 | -7.8124 ± 17.6088 | 0.0166 ± 0.0126 | 0.0360 ± 0.0449 | 0.9596 ± 0.0755 | 0.8000 ± 0.4472 | 0.0000 ± 0.0000 |
| SPT-NRTL adapted | joint → joint | isobaric | 2+3 | evaluated | 5/5 | 14.1737 ± 2.3405 | 24.5689 ± 5.0250 | 0.1828 ± 0.2051 | 0.1437 ± 0.0164 | 0.2146 ± 0.0261 | 0.5105 ± 0.0965 | 0.9094 ± 0.0540 | 0.0906 ± 0.0540 |
| SPT-NRTL adapted | joint → joint | isothermal | 2+3 | evaluated | 5/5 | 35.0072 ± 12.0839 | 81.6309 ± 28.6232 | 0.5906 ± 0.2041 | 0.0739 ± 0.0096 | 0.1177 ± 0.0080 | 0.8711 ± 0.0260 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| SPT-NRTL adapted | joint → joint | isobaric | 3 | evaluated | 5/5 | 29.3970 ± 16.4384 | 34.6477 ± 18.6627 | -29.4812 ± 55.8841 | 0.2379 ± 0.1299 | 0.3079 ± 0.1397 | -0.3689 ± 0.7904 | 0.7235 ± 0.1988 | 0.2765 ± 0.1988 |
| SPT-NRTL adapted | joint → joint | isothermal | 3 | evaluated_partial_seeds | 4/5 | 13.8148 ± 11.6402 | 15.9773 ± 11.8381 | 0.0361 ± 0.9932 | 0.0617 ± 0.0291 | 0.0841 ± 0.0331 | 0.8922 ± 0.0742 | 0.8000 ± 0.4472 | 0.0000 ± 0.0000 |
| SolvGNN | joint → joint | isobaric | 2 | not_applicable | 0/5 | N/A | N/A | N/A | N/A | N/A | N/A | 0.0000 ± 0.0000 | N/A |
| SolvGNN | joint → joint | isothermal | 2 | evaluated_partial_seeds | 3/5 | 0.9350 ± 0.3399 | 1.0679 ± 0.4342 | -3.5880 ± 7.5750 | 0.0523 ± 0.0396 | 0.0723 ± 0.0565 | 0.8705 ± 0.1307 | 0.0229 ± 0.0238 | N/A |
| SolvGNN | joint → joint | isobaric | 2+3 | not_applicable | 0/5 | N/A | N/A | N/A | N/A | N/A | N/A | 0.0000 ± 0.0000 | N/A |
| SolvGNN | joint → joint | isothermal | 2+3 | evaluated_partial_seeds | 3/4 | 0.9350 ± 0.3399 | 1.0679 ± 0.4342 | -3.5880 ± 7.5750 | 0.0523 ± 0.0396 | 0.0723 ± 0.0565 | 0.8705 ± 0.1307 | 0.0248 ± 0.0218 | N/A |
| SolvGNN | joint → joint | isobaric | 3 | not_applicable | 0/5 | N/A | N/A | N/A | N/A | N/A | N/A | 0.0000 ± 0.0000 | N/A |
| SolvGNN | joint → joint | isothermal | 3 | not_evaluated_no_298k_coverage | 0/5 | N/A | N/A | N/A | N/A | N/A | N/A | 0.0000 ± 0.0000 | N/A |
| TeNNet-SAC adapted | joint → joint | isobaric | 2+3 | evaluated | 5/5 | 6.8764 ± 2.4359 | 18.7934 ± 9.2587 | 0.4794 ± 0.4712 | 0.0721 ± 0.0171 | 0.1476 ± 0.0301 | 0.7658 ± 0.0834 | 0.9561 ± 0.0216 | 0.0439 ± 0.0216 |
| TeNNet-SAC adapted | joint → joint | isothermal | 2+3 | evaluated | 5/5 | 8.5518 ± 1.7171 | 20.9257 ± 6.8150 | 0.9715 ± 0.0201 | 0.0211 ± 0.0037 | 0.0400 ± 0.0090 | 0.9841 ± 0.0081 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| TeNNet-SAC adapted | joint → joint | isobaric | 3 | evaluated | 5/5 | 8.4809 ± 7.6943 | 11.6316 ± 6.8331 | -2.3535 ± 6.8000 | 0.1337 ± 0.1257 | 0.1845 ± 0.1384 | 0.4519 ± 0.6119 | 0.8107 ± 0.1977 | 0.1893 ± 0.1977 |
| TeNNet-SAC adapted | joint → joint | isothermal | 3 | evaluated_partial_seeds | 4/5 | 3.2123 ± 1.4866 | 4.8563 ± 3.0492 | 0.9181 ± 0.0734 | 0.0184 ± 0.0019 | 0.0299 ± 0.0135 | 0.9850 ± 0.0143 | 0.8000 ± 0.4472 | 0.0000 ± 0.0000 |
| ThermoFormer | joint → joint | isobaric | 2+3 | evaluated | 5/5 | 2.2032 ± 0.5408 | 3.9209 ± 1.1295 | 0.9788 ± 0.0093 | 0.0281 ± 0.0052 | 0.0477 ± 0.0097 | 0.9754 ± 0.0086 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| ThermoFormer | joint → joint | isothermal | 2+3 | evaluated | 5/5 | 10.1185 ± 2.4539 | 26.8630 ± 8.2319 | 0.9504 ± 0.0288 | 0.0245 ± 0.0028 | 0.0451 ± 0.0080 | 0.9801 ± 0.0094 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| ThermoFormer | joint → ternary | isobaric | 3 | evaluated | 5/5 | 3.5838 ± 4.0673 | 4.7654 ± 5.1691 | 0.7281 ± 0.5302 | 0.0465 ± 0.0475 | 0.0647 ± 0.0575 | 0.9067 ± 0.1399 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| ThermoFormer | joint → ternary | isothermal | 3 | evaluated | 5/5 | 1.6401 ± 0.5421 | 2.1672 ± 0.6266 | 0.9841 ± 0.0108 | 0.0176 ± 0.0098 | 0.0257 ± 0.0132 | 0.9905 ± 0.0056 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| HANNA adapted | ternary → ternary | isobaric | 3 | evaluated | 5/5 | 11.4993 ± 9.4794 | 20.8687 ± 16.3649 | -8.6839 ± 15.0009 | 0.1379 ± 0.1230 | 0.2059 ± 0.1229 | 0.3759 ± 0.5656 | 0.8320 ± 0.1836 | 0.1680 ± 0.1836 |
| HANNA adapted | ternary → ternary | isothermal | 3 | evaluated_partial_seeds | 4/5 | 9.3475 ± 10.1817 | 29.8054 ± 50.1609 | -5.6394 ± 13.0886 | 0.0166 ± 0.0126 | 0.0357 ± 0.0443 | 0.9605 ± 0.0736 | 0.8000 ± 0.4472 | 0.0000 ± 0.0000 |
| TeNNet-SAC adapted | ternary → ternary | isobaric | 3 | evaluated | 5/5 | 10.3136 ± 9.3846 | 20.8735 ± 17.0788 | -14.9321 ± 31.6588 | 0.1340 ± 0.1186 | 0.1950 ± 0.1230 | 0.4331 ± 0.5562 | 0.8244 ± 0.1869 | 0.1756 ± 0.1869 |
| TeNNet-SAC adapted | ternary → ternary | isothermal | 3 | evaluated_partial_seeds | 4/5 | 5.3448 ± 2.8168 | 7.4282 ± 4.6804 | 0.8104 ± 0.1554 | 0.0197 ± 0.0033 | 0.0328 ± 0.0156 | 0.9823 ± 0.0174 | 0.8000 ± 0.4472 | 0.0000 ± 0.0000 |
| ThermoFormer | ternary → ternary | isobaric | 3 | evaluated | 5/5 | 7.3148 ± 7.2670 | 9.8211 ± 9.1680 | -0.0181 ± 1.5378 | 0.0670 ± 0.0461 | 0.0920 ± 0.0573 | 0.8412 ± 0.1614 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| ThermoFormer | ternary → ternary | isothermal | 3 | evaluated | 5/5 | 6.5990 ± 4.9530 | 8.6563 ± 6.5786 | 0.7043 ± 0.3151 | 0.0540 ± 0.0441 | 0.0733 ± 0.0532 | 0.9129 ± 0.0826 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
