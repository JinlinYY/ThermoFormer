# VLE baseline comparison

Each metric reports MAE, RMSE, and R² as mean ± sample SD across completed seed records. Coverage reports isothermal/isobaric test-record percentages.

## Matched binary→binary

| Model | P (kPa), isothermal | y, isothermal | T (K), isobaric | y, isobaric | Coverage (%) |
|---|---|---|---|---|---|
| ThermoFormer | MAE: 10.6722 ± 2.8012<br>RMSE: 24.8619 ± 8.9927<br>R2: 0.9628 ± 0.0232 | MAE: 0.0295 ± 0.0090<br>RMSE: 0.0545 ± 0.0177<br>R2: 0.9706 ± 0.0211 | MAE: 2.3098 ± 0.4622<br>RMSE: 4.0700 ± 1.0666<br>R2: 0.9781 ± 0.0070 | MAE: 0.0285 ± 0.0044<br>RMSE: 0.0476 ± 0.0067<br>R2: 0.9761 ± 0.0058 | Iso: 100.00 ± 0.00%<br>Isob: 100.00 ± 0.00% |
| HANNA adapted | MAE: 6.8884 ± 2.7591<br>RMSE: 18.8300 ± 9.3680<br>R2: 0.9776 ± 0.0223 | MAE: 0.0164 ± 0.0036<br>RMSE: 0.0339 ± 0.0079<br>R2: 0.9890 ± 0.0062 | MAE: 5.7022 ± 1.5325<br>RMSE: 19.0862 ± 9.7434<br>R2: 0.4343 ± 0.5663 | MAE: 0.0592 ± 0.0135<br>RMSE: 0.1365 ± 0.0246<br>R2: 0.8025 ± 0.0783 | Iso: 100.00 ± 0.00%<br>Isob: 96.06 ± 2.36% |
| TeNNet-SAC adapted | MAE: 8.5089 ± 2.2046<br>RMSE: 21.3216 ± 7.2688<br>R2: 0.9735 ± 0.0182 | MAE: 0.0227 ± 0.0049<br>RMSE: 0.0431 ± 0.0109<br>R2: 0.9821 ± 0.0092 | MAE: 6.7393 ± 2.4900<br>RMSE: 19.6995 ± 10.8427<br>R2: 0.4275 ± 0.5812 | MAE: 0.0670 ± 0.0139<br>RMSE: 0.1441 ± 0.0271<br>R2: 0.7804 ± 0.0811 | Iso: 100.00 ± 0.00%<br>Isob: 96.25 ± 1.52% |
| SMILES-RNN | MAE: 85.8780 ± 14.6561<br>RMSE: 117.1789 ± 21.4985<br>R2: 0.2465 ± 0.2040 | MAE: 0.1817 ± 0.0352<br>RMSE: 0.2306 ± 0.0403<br>R2: 0.5214 ± 0.1446 | MAE: 25.9875 ± 5.7669<br>RMSE: 32.7500 ± 7.2620<br>R2: -0.5159 ± 0.7404 | MAE: 0.2287 ± 0.0253<br>RMSE: 0.2722 ± 0.0285<br>R2: 0.2255 ± 0.1343 | Iso: 100.00 ± 0.00%<br>Isob: 100.00 ± 0.00% |
| UALF-GNN | MAE: N/A<br>RMSE: N/A<br>R2: N/A | MAE: N/A<br>RMSE: N/A<br>R2: N/A | MAE: 21.2896 ± 1.8611<br>RMSE: 26.3803 ± 1.6898<br>R2: 0.0614 ± 0.1907 | MAE: 0.1324 ± 0.0179<br>RMSE: 0.1673 ± 0.0213<br>R2: 0.7064 ± 0.0656 | Iso: N/A<br>Isob: 100.00 ± 0.00% |
| Descriptor ANN | MAE: N/A<br>RMSE: N/A<br>R2: N/A | MAE: N/A<br>RMSE: N/A<br>R2: N/A | MAE: N/A<br>RMSE: N/A<br>R2: N/A | MAE: N/A<br>RMSE: N/A<br>R2: N/A | Iso: 0.00 ± 0.00%<br>Isob: 0.00 ± 0.00% |

## Matched ternary→ternary

| Model | P (kPa), isothermal | y, isothermal | T (K), isobaric | y, isobaric | Coverage (%) |
|---|---|---|---|---|---|
| ThermoFormer | MAE: 6.5990 ± 4.9530<br>RMSE: 8.6563 ± 6.5786<br>R2: 0.7043 ± 0.3151 | MAE: 0.0540 ± 0.0441<br>RMSE: 0.0733 ± 0.0532<br>R2: 0.9129 ± 0.0826 | MAE: 7.3148 ± 7.2670<br>RMSE: 9.8211 ± 9.1680<br>R2: -0.0181 ± 1.5378 | MAE: 0.0670 ± 0.0461<br>RMSE: 0.0920 ± 0.0573<br>R2: 0.8412 ± 0.1614 | Iso: 100.00 ± 0.00%<br>Isob: 100.00 ± 0.00% |
| HANNA adapted | MAE: 9.3475 ± 10.1817<br>RMSE: 29.8054 ± 50.1609<br>R2: -5.6394 ± 13.0886 | MAE: 0.0166 ± 0.0126<br>RMSE: 0.0357 ± 0.0443<br>R2: 0.9605 ± 0.0736 | MAE: 11.4993 ± 9.4794<br>RMSE: 20.8687 ± 16.3649<br>R2: -8.6839 ± 15.0009 | MAE: 0.1379 ± 0.1230<br>RMSE: 0.2059 ± 0.1229<br>R2: 0.3759 ± 0.5656 | Iso: 80.00 ± 44.72%<br>Isob: 83.20 ± 18.36% |
| TeNNet-SAC adapted | MAE: 5.3448 ± 2.8168<br>RMSE: 7.4282 ± 4.6804<br>R2: 0.8104 ± 0.1554 | MAE: 0.0197 ± 0.0033<br>RMSE: 0.0328 ± 0.0156<br>R2: 0.9823 ± 0.0174 | MAE: 10.3136 ± 9.3846<br>RMSE: 20.8735 ± 17.0788<br>R2: -14.9321 ± 31.6588 | MAE: 0.1340 ± 0.1186<br>RMSE: 0.1950 ± 0.1230<br>R2: 0.4331 ± 0.5562 | Iso: 80.00 ± 44.72%<br>Isob: 82.44 ± 18.69% |

## Matched joint→ternary

| Model | P (kPa), isothermal | y, isothermal | T (K), isobaric | y, isobaric | Coverage (%) |
|---|---|---|---|---|---|
| ThermoFormer | MAE: 1.6401 ± 0.5421<br>RMSE: 2.1672 ± 0.6266<br>R2: 0.9841 ± 0.0108 | MAE: 0.0176 ± 0.0098<br>RMSE: 0.0257 ± 0.0132<br>R2: 0.9905 ± 0.0056 | MAE: 3.5838 ± 4.0673<br>RMSE: 4.7654 ± 5.1691<br>R2: 0.7281 ± 0.5302 | MAE: 0.0465 ± 0.0475<br>RMSE: 0.0647 ± 0.0575<br>R2: 0.9067 ± 0.1399 | Iso: 100.00 ± 0.00%<br>Isob: 100.00 ± 0.00% |
| HANNA adapted | MAE: 7.5190 ± 12.5800<br>RMSE: 31.4648 ± 60.0387<br>R2: -7.8124 ± 17.6088 | MAE: 0.0166 ± 0.0126<br>RMSE: 0.0360 ± 0.0449<br>R2: 0.9596 ± 0.0755 | MAE: 11.0403 ± 11.0678<br>RMSE: 18.1354 ± 12.7574<br>R2: -9.3629 ± 20.2840 | MAE: 0.1378 ± 0.1340<br>RMSE: 0.1998 ± 0.1360<br>R2: 0.3931 ± 0.6511 | Iso: 80.00 ± 44.72%<br>Isob: 81.67 ± 18.37% |
| TeNNet-SAC adapted | MAE: 3.2123 ± 1.4866<br>RMSE: 4.8563 ± 3.0492<br>R2: 0.9181 ± 0.0734 | MAE: 0.0184 ± 0.0019<br>RMSE: 0.0299 ± 0.0135<br>R2: 0.9850 ± 0.0143 | MAE: 8.4809 ± 7.6943<br>RMSE: 11.6316 ± 6.8331<br>R2: -2.3535 ± 6.8000 | MAE: 0.1337 ± 0.1257<br>RMSE: 0.1845 ± 0.1384<br>R2: 0.4519 ± 0.6119 | Iso: 80.00 ± 44.72%<br>Isob: 81.07 ± 19.77% |
| SPT-NRTL adapted | MAE: 13.8148 ± 11.6402<br>RMSE: 15.9773 ± 11.8381<br>R2: 0.0361 ± 0.9932 | MAE: 0.0617 ± 0.0291<br>RMSE: 0.0841 ± 0.0331<br>R2: 0.8922 ± 0.0742 | MAE: 29.3970 ± 16.4384<br>RMSE: 34.6477 ± 18.6627<br>R2: -29.4812 ± 55.8841 | MAE: 0.2379 ± 0.1299<br>RMSE: 0.3079 ± 0.1397<br>R2: -0.3689 ± 0.7904 | Iso: 80.00 ± 44.72%<br>Isob: 72.35 ± 19.88% |

## Matched joint→joint

| Model | P (kPa), isothermal | y, isothermal | T (K), isobaric | y, isobaric | Coverage (%) |
|---|---|---|---|---|---|
| ThermoFormer | MAE: 10.1185 ± 2.4539<br>RMSE: 26.8630 ± 8.2319<br>R2: 0.9504 ± 0.0288 | MAE: 0.0245 ± 0.0028<br>RMSE: 0.0451 ± 0.0080<br>R2: 0.9801 ± 0.0094 | MAE: 2.2032 ± 0.5408<br>RMSE: 3.9209 ± 1.1295<br>R2: 0.9788 ± 0.0093 | MAE: 0.0281 ± 0.0052<br>RMSE: 0.0477 ± 0.0097<br>R2: 0.9754 ± 0.0086 | Iso: 100.00 ± 0.00%<br>Isob: 100.00 ± 0.00% |
| HANNA adapted | MAE: 7.5386 ± 4.7170<br>RMSE: 25.1558 ± 23.5029<br>R2: 0.9291 ± 0.1296 | MAE: 0.0161 ± 0.0055<br>RMSE: 0.0368 ± 0.0185<br>R2: 0.9842 ± 0.0188 | MAE: 5.9293 ± 1.5130<br>RMSE: 20.6453 ± 9.0664<br>R2: 0.3015 ± 0.5813 | MAE: 0.0645 ± 0.0166<br>RMSE: 0.1412 ± 0.0272<br>R2: 0.7860 ± 0.0779 | Iso: 100.00 ± 0.00%<br>Isob: 95.29 ± 2.81% |
| TeNNet-SAC adapted | MAE: 8.5518 ± 1.7171<br>RMSE: 20.9257 ± 6.8150<br>R2: 0.9715 ± 0.0201 | MAE: 0.0211 ± 0.0037<br>RMSE: 0.0400 ± 0.0090<br>R2: 0.9841 ± 0.0081 | MAE: 6.8764 ± 2.4359<br>RMSE: 18.7934 ± 9.2587<br>R2: 0.4794 ± 0.4712 | MAE: 0.0721 ± 0.0171<br>RMSE: 0.1476 ± 0.0301<br>R2: 0.7658 ± 0.0834 | Iso: 100.00 ± 0.00%<br>Isob: 95.61 ± 2.16% |
| SPT-NRTL adapted | MAE: 35.0072 ± 12.0839<br>RMSE: 81.6309 ± 28.6232<br>R2: 0.5906 ± 0.2041 | MAE: 0.0739 ± 0.0096<br>RMSE: 0.1177 ± 0.0080<br>R2: 0.8711 ± 0.0260 | MAE: 14.1737 ± 2.3405<br>RMSE: 24.5689 ± 5.0250<br>R2: 0.1828 ± 0.2051 | MAE: 0.1437 ± 0.0164<br>RMSE: 0.2146 ± 0.0261<br>R2: 0.5105 ± 0.0965 | Iso: 100.00 ± 0.00%<br>Isob: 90.94 ± 5.40% |

## External direct→ternary

| Model | P (kPa), isothermal | y, isothermal | T (K), isobaric | y, isobaric | Coverage (%) |
|---|---|---|---|---|---|
| HANNA official | MAE: 7.7641 ± 13.6227<br>RMSE: 33.9129 ± 65.5135<br>R2: -9.4231 ± 20.8362 | MAE: 0.0167 ± 0.0127<br>RMSE: 0.0362 ± 0.0452<br>R2: 0.9591 ± 0.0764 | MAE: 11.5791 ± 11.9774<br>RMSE: 18.9834 ± 13.8750<br>R2: -10.9268 ± 23.7104 | MAE: 0.1398 ± 0.1376<br>RMSE: 0.2022 ± 0.1399<br>R2: 0.3750 ± 0.6835 | Iso: 80.00 ± 44.72%<br>Isob: 81.44 ± 18.18% |
| TeNNet-SAC official | MAE: 3.8331 ± 1.9275<br>RMSE: 7.2729 ± 7.7363<br>R2: 0.7601 ± 0.3962 | MAE: 0.0202 ± 0.0036<br>RMSE: 0.0340 ± 0.0174<br>R2: 0.9803 ± 0.0208 | MAE: 8.2858 ± 7.1557<br>RMSE: 11.5401 ± 6.1737<br>R2: -1.9277 ± 5.8134 | MAE: 0.1322 ± 0.1225<br>RMSE: 0.1828 ± 0.1336<br>R2: 0.4664 ± 0.5739 | Iso: 80.00 ± 44.72%<br>Isob: 80.92 ± 19.65% |
| SPT-NRTL official | MAE: 1.9146 ± 0.6411<br>RMSE: 2.7982 ± 1.0911<br>R2: 0.9721 ± 0.0202 | MAE: 0.0161 ± 0.0081<br>RMSE: 0.0264 ± 0.0175<br>R2: 0.9857 ± 0.0135 | MAE: 23.3396 ± 26.4137<br>RMSE: 37.1529 ± 37.3285<br>R2: -27.6986 ± 51.3952 | MAE: 0.1703 ± 0.1535<br>RMSE: 0.2524 ± 0.1667<br>R2: -0.0664 ± 1.1099 | Iso: 60.00 ± 54.77%<br>Isob: 91.32 ± 6.28% |

## External direct→joint

| Model | P (kPa), isothermal | y, isothermal | T (K), isobaric | y, isobaric | Coverage (%) |
|---|---|---|---|---|---|
| HANNA official | MAE: 6.7299 ± 4.5743<br>RMSE: 25.5570 ± 25.3981<br>R2: 0.9222 ± 0.1471 | MAE: 0.0160 ± 0.0056<br>RMSE: 0.0367 ± 0.0187<br>R2: 0.9841 ± 0.0191 | MAE: 5.8948 ± 1.7356<br>RMSE: 17.6024 ± 6.7361<br>R2: 0.5476 ± 0.3168 | MAE: 0.0639 ± 0.0172<br>RMSE: 0.1408 ± 0.0283<br>R2: 0.7881 ± 0.0811 | Iso: 100.00 ± 0.00%<br>Isob: 95.22 ± 2.91% |
| TeNNet-SAC official | MAE: 7.4945 ± 1.4237<br>RMSE: 19.5322 ± 6.0313<br>R2: 0.9753 ± 0.0163 | MAE: 0.0221 ± 0.0039<br>RMSE: 0.0421 ± 0.0106<br>R2: 0.9823 ± 0.0094 | MAE: 6.4333 ± 1.8740<br>RMSE: 16.8295 ± 4.9119<br>R2: 0.6176 ± 0.1586 | MAE: 0.0720 ± 0.0173<br>RMSE: 0.1478 ± 0.0308<br>R2: 0.7661 ± 0.0857 | Iso: 100.00 ± 0.00%<br>Isob: 95.56 ± 2.15% |
| SPT-NRTL official | MAE: 5.4175 ± 1.9815<br>RMSE: 15.9184 ± 7.6429<br>R2: 0.9823 ± 0.0148 | MAE: 0.0186 ± 0.0045<br>RMSE: 0.0356 ± 0.0082<br>R2: 0.9875 ± 0.0070 | MAE: 7.1613 ± 2.4492<br>RMSE: 20.2236 ± 6.8344<br>R2: 0.4095 ± 0.3151 | MAE: 0.0728 ± 0.0187<br>RMSE: 0.1544 ± 0.0341<br>R2: 0.7425 ± 0.0953 | Iso: 96.68 ± 3.24%<br>Isob: 95.07 ± 2.25% |

## Local-temperature reference 298.15±0.5 K

| Model | P (kPa), isothermal | y, isothermal | T (K), isobaric | y, isobaric | Coverage (%) |
|---|---|---|---|---|---|
| SolvGNN | MAE: 0.9350 ± 0.3399<br>RMSE: 1.0679 ± 0.4342<br>R2: -3.5880 ± 7.5750 | MAE: 0.0523 ± 0.0396<br>RMSE: 0.0723 ± 0.0565<br>R2: 0.8705 ± 0.1307 | MAE: N/A<br>RMSE: N/A<br>R2: N/A | MAE: N/A<br>RMSE: N/A<br>R2: N/A | Iso: 2.48 ± 2.18%<br>Isob: 0.00 ± 0.00% |
| GDI-GNN | MAE: 1.4520 ± 0.5170<br>RMSE: 1.6458 ± 0.4292<br>R2: -21.8678 ± 39.0954 | MAE: 0.0628 ± 0.0429<br>RMSE: 0.0857 ± 0.0616<br>R2: 0.8263 ± 0.1482 | MAE: N/A<br>RMSE: N/A<br>R2: N/A | MAE: N/A<br>RMSE: N/A<br>R2: N/A | Iso: 2.29 ± 2.38%<br>Isob: 0.00 ± 0.00% |
| GE-GNN | MAE: 1.9300 ± 1.3418<br>RMSE: 2.0999 ± 1.1982<br>R2: -60.3433 ± 105.7365 | MAE: 0.0603 ± 0.0485<br>RMSE: 0.0830 ± 0.0674<br>R2: 0.8252 ± 0.1511 | MAE: N/A<br>RMSE: N/A<br>R2: N/A | MAE: N/A<br>RMSE: N/A<br>R2: N/A | Iso: 2.29 ± 2.38%<br>Isob: 0.00 ± 0.00% |

