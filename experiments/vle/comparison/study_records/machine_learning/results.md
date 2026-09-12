# Machine-learning VLE baseline comparison

Status: five-seed formal execution completed for executable models; unavailable models remain not evaluated.

Trainable baselines used validation-only checkpoint selection. HANNA uses fixed official weights and performs no selection on these data; test labels were used only for evaluation.

HANNA uses the unchanged official ten-model ensemble. It was trained on the authors' binary corpus and applies the official Muggianu projection for ternary inference; its training-system overlap with this dataset is unknown because the official inventory is not published.

HANNA was executed in the project's ggnn39 compatibility environment, not the upstream version-pinned environment. Source, weights, scalers and architecture are unchanged, but exact upstream-environment numerical parity has not been established.

| Baseline | Benchmark | Direction | Components | Status | Valid seeds | State MAE | State RMSE | State R2 | y MAE | y RMSE | y R2 | Coverage | Nonphysical | Solver failure |
|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| descriptor_ann | binary_train_binary_test | isobaric | 2 | blocked_external_assets | 0/5 | N/A | N/A | N/A | N/A | N/A | N/A | 0.0000 +/- 0.0000 | N/A | N/A |
| descriptor_ann | binary_train_binary_test | isothermal | 2 | not_applicable | 0/5 | N/A | N/A | N/A | N/A | N/A | N/A | 0.0000 +/- 0.0000 | N/A | N/A |
| smiles_rnn | binary_train_binary_test | isobaric | 2 | evaluated | 5/5 | 27.6891 +/- 4.7461 | 35.0031 +/- 5.8520 | -0.4300 +/- 0.6147 | 0.1853 +/- 0.0701 | 0.2290 +/- 0.0727 | 0.4252 +/- 0.3560 | 1.0000 +/- 0.0000 | 0.0061 +/- 0.0123 | N/A |
| smiles_rnn | binary_train_binary_test | isothermal | 2 | evaluated | 5/5 | 82.0749 +/- 13.4647 | 112.5852 +/- 20.7355 | 0.0742 +/- 0.2104 | 0.1776 +/- 0.0286 | 0.2268 +/- 0.0397 | 0.5039 +/- 0.1805 | 1.0000 +/- 0.0000 | 0.1133 +/- 0.0712 | N/A |
| ualf_gnn | binary_train_binary_test | isobaric | 2 | evaluated | 5/5 | 21.5128 +/- 1.5970 | 27.7035 +/- 2.8004 | 0.1462 +/- 0.0358 | 0.1366 +/- 0.0155 | 0.1785 +/- 0.0169 | 0.6753 +/- 0.0551 | 1.0000 +/- 0.0000 | 0.0058 +/- 0.0075 | N/A |
| solvgnn | joint_train_joint_test | isobaric | 2 | not_applicable | 0/5 | N/A | N/A | N/A | N/A | N/A | N/A | 0.0000 +/- 0.0000 | N/A | N/A |
| solvgnn | joint_train_joint_test | isobaric | 2+3 | not_applicable | 0/5 | N/A | N/A | N/A | N/A | N/A | N/A | 0.0000 +/- 0.0000 | N/A | N/A |
| solvgnn | joint_train_joint_test | isobaric | 3 | not_applicable | 0/5 | N/A | N/A | N/A | N/A | N/A | N/A | 0.0000 +/- 0.0000 | N/A | N/A |
| solvgnn | joint_train_joint_test | isothermal | 2 | evaluated_partial_seeds | 3/5 | 1.5541 +/- 0.9979 | 1.8483 +/- 1.3513 | 0.9375 +/- 0.0353 | 0.0393 +/- 0.0410 | 0.0558 +/- 0.0637 | 0.8824 +/- 0.1961 | 0.0240 +/- 0.0223 | 0.0000 +/- 0.0000 | N/A |
| solvgnn | joint_train_joint_test | isothermal | 2+3 | evaluated_partial_seeds | 3/5 | 1.5541 +/- 0.9979 | 1.8483 +/- 1.3513 | 0.9375 +/- 0.0353 | 0.0393 +/- 0.0410 | 0.0558 +/- 0.0637 | 0.8824 +/- 0.1961 | 0.0202 +/- 0.0187 | 0.0000 +/- 0.0000 | N/A |
| solvgnn | joint_train_joint_test | isothermal | 3 | not_evaluated_no_298k_coverage | 0/5 | N/A | N/A | N/A | N/A | N/A | N/A | 0.0000 +/- 0.0000 | N/A | N/A |
| gdi_gnn | binary_train_binary_test | isobaric | 2 | not_applicable | 0/5 | N/A | N/A | N/A | N/A | N/A | N/A | 0.0000 +/- 0.0000 | N/A | N/A |
| gdi_gnn | binary_train_binary_test | isothermal | 2 | evaluated_partial_seeds | 3/5 | 2.2651 +/- 1.6080 | 2.7084 +/- 2.0544 | 0.8453 +/- 0.0923 | 0.0409 +/- 0.0391 | 0.0587 +/- 0.0606 | 0.8819 +/- 0.1936 | 0.0240 +/- 0.0223 | 0.0000 +/- 0.0000 | N/A |
| ge_gnn | binary_train_binary_test | isobaric | 2 | not_applicable | 0/5 | N/A | N/A | N/A | N/A | N/A | N/A | 0.0000 +/- 0.0000 | N/A | N/A |
| ge_gnn | binary_train_binary_test | isothermal | 2 | evaluated_partial_seeds | 3/5 | 2.2502 +/- 1.5997 | 2.6854 +/- 2.0534 | 0.8503 +/- 0.0898 | 0.0416 +/- 0.0391 | 0.0595 +/- 0.0604 | 0.8804 +/- 0.1954 | 0.0240 +/- 0.0223 | 0.0000 +/- 0.0000 | N/A |
| hanna | official_pretrained_to_joint_test | isobaric | 2 | evaluated | 5/5 | 8.0988 +/- 2.7814 | 22.1815 +/- 6.5520 | 0.4343 +/- 0.2592 | 0.0791 +/- 0.0229 | 0.1732 +/- 0.0260 | 0.6925 +/- 0.0895 | 0.9654 +/- 0.0202 | 0.0000 +/- 0.0000 | 0.0346 +/- 0.0202 |
| hanna | official_pretrained_to_joint_test | isobaric | 2+3 | evaluated | 5/5 | 8.1393 +/- 3.4184 | 21.8241 +/- 6.6571 | 0.4285 +/- 0.2907 | 0.0804 +/- 0.0309 | 0.1706 +/- 0.0347 | 0.6889 +/- 0.1267 | 0.9677 +/- 0.0208 | 0.0000 +/- 0.0000 | 0.0323 +/- 0.0208 |
| hanna | official_pretrained_to_joint_test | isobaric | 3 | evaluated_partial_seeds | 4/5 | 8.0000 +/- 8.5420 | 13.1382 +/- 13.1704 | -0.7533 +/- 2.9758 | 0.0849 +/- 0.0692 | 0.1283 +/- 0.0944 | 0.6042 +/- 0.4832 | 0.8000 +/- 0.4472 | 0.0000 +/- 0.0000 | 0.0000 +/- 0.0000 |
| hanna | official_pretrained_to_joint_test | isothermal | 2 | evaluated | 5/5 | 5.6156 +/- 4.1224 | 13.8781 +/- 10.8318 | 0.9841 +/- 0.0207 | 0.0152 +/- 0.0043 | 0.0319 +/- 0.0092 | 0.9899 +/- 0.0061 | 1.0000 +/- 0.0000 | 0.0000 +/- 0.0000 | 0.0000 +/- 0.0000 |
| hanna | official_pretrained_to_joint_test | isothermal | 2+3 | evaluated | 5/5 | 4.9461 +/- 3.1478 | 12.8244 +/- 9.3340 | 0.9849 +/- 0.0192 | 0.0137 +/- 0.0027 | 0.0293 +/- 0.0071 | 0.9913 +/- 0.0043 | 1.0000 +/- 0.0000 | 0.0000 +/- 0.0000 | 0.0000 +/- 0.0000 |
| hanna | official_pretrained_to_joint_test | isothermal | 3 | evaluated_partial_seeds | 4/5 | 0.9938 +/- 0.4129 | 1.2966 +/- 0.5820 | 0.9941 +/- 0.0046 | 0.0066 +/- 0.0025 | 0.0107 +/- 0.0023 | 0.9980 +/- 0.0011 | 0.8000 +/- 0.4472 | 0.0000 +/- 0.0000 | 0.0000 +/- 0.0000 |
| tennet_sac | external_fixed_to_joint_test | isobaric | 2 | evaluated | 5/5 | 8.5829 +/- 2.8279 | 21.4168 +/- 4.9855 | 0.4901 +/- 0.1771 | 0.0848 +/- 0.0218 | 0.1754 +/- 0.0252 | 0.6852 +/- 0.0876 | 0.9666 +/- 0.0172 | 0.0000 +/- 0.0000 | 0.0334 +/- 0.0172 |
| tennet_sac | external_fixed_to_joint_test | isobaric | 2+3 | evaluated | 5/5 | 8.4148 +/- 3.1613 | 20.7237 +/- 4.8602 | 0.5050 +/- 0.1875 | 0.0844 +/- 0.0280 | 0.1712 +/- 0.0311 | 0.6885 +/- 0.1110 | 0.9681 +/- 0.0179 | 0.0000 +/- 0.0000 | 0.0319 +/- 0.0179 |
| tennet_sac | external_fixed_to_joint_test | isobaric | 3 | evaluated_partial_seeds | 4/5 | 6.7575 +/- 6.9420 | 10.1700 +/- 9.2820 | 0.0473 +/- 1.4154 | 0.0797 +/- 0.0628 | 0.1198 +/- 0.0865 | 0.6603 +/- 0.4057 | 0.7943 +/- 0.4442 | 0.0000 +/- 0.0000 | 0.0057 +/- 0.0128 |
| tennet_sac | external_fixed_to_joint_test | isothermal | 2 | evaluated | 5/5 | 6.6540 +/- 3.5845 | 15.5397 +/- 9.2337 | 0.9815 +/- 0.0168 | 0.0211 +/- 0.0043 | 0.0412 +/- 0.0113 | 0.9833 +/- 0.0080 | 1.0000 +/- 0.0000 | 0.0000 +/- 0.0000 | 0.0000 +/- 0.0000 |
| tennet_sac | external_fixed_to_joint_test | isothermal | 2+3 | evaluated | 5/5 | 6.0253 +/- 2.7947 | 14.4711 +/- 7.9319 | 0.9822 +/- 0.0155 | 0.0198 +/- 0.0037 | 0.0385 +/- 0.0104 | 0.9850 +/- 0.0071 | 1.0000 +/- 0.0000 | 0.0000 +/- 0.0000 | 0.0000 +/- 0.0000 |
| tennet_sac | external_fixed_to_joint_test | isothermal | 3 | evaluated_partial_seeds | 4/5 | 2.0248 +/- 0.8498 | 2.4194 +/- 0.8875 | 0.9778 +/- 0.0221 | 0.0132 +/- 0.0041 | 0.0183 +/- 0.0058 | 0.9940 +/- 0.0039 | 0.8000 +/- 0.4472 | 0.0000 +/- 0.0000 | 0.0000 +/- 0.0000 |
| spt_nrtl | external_fixed_to_joint_test | isobaric | 2 | evaluated | 5/5 | 10.2447 +/- 2.7904 | 27.9763 +/- 4.3547 | 0.1097 +/- 0.1799 | 0.0867 +/- 0.0232 | 0.1813 +/- 0.0253 | 0.6649 +/- 0.0892 | 0.9670 +/- 0.0152 | 0.0000 +/- 0.0000 | 0.0274 +/- 0.0188 |
| spt_nrtl | external_fixed_to_joint_test | isobaric | 2+3 | evaluated | 5/5 | 10.0959 +/- 3.3223 | 27.4764 +/- 4.4701 | 0.1082 +/- 0.2501 | 0.0865 +/- 0.0305 | 0.1774 +/- 0.0337 | 0.6655 +/- 0.1247 | 0.9690 +/- 0.0157 | 0.0000 +/- 0.0000 | 0.0259 +/- 0.0189 |
| spt_nrtl | external_fixed_to_joint_test | isobaric | 3 | evaluated_partial_seeds | 4/5 | 7.9874 +/- 9.2257 | 13.7563 +/- 17.1788 | -1.4710 +/- 4.6037 | 0.0792 +/- 0.0721 | 0.1155 +/- 0.1022 | 0.6366 +/- 0.5068 | 0.7966 +/- 0.4454 | 0.0000 +/- 0.0000 | 0.0034 +/- 0.0077 |
| spt_nrtl | external_fixed_to_joint_test | isothermal | 2 | evaluated | 5/5 | 5.1319 +/- 3.5255 | 12.3857 +/- 10.0363 | 0.9870 +/- 0.0170 | 0.0193 +/- 0.0038 | 0.0366 +/- 0.0089 | 0.9871 +/- 0.0061 | 0.9459 +/- 0.0343 | 0.0000 +/- 0.0000 | 0.0000 +/- 0.0000 |
| spt_nrtl | external_fixed_to_joint_test | isothermal | 2+3 | evaluated | 5/5 | 4.5628 +/- 2.6711 | 11.4155 +/- 8.5519 | 0.9875 +/- 0.0159 | 0.0183 +/- 0.0024 | 0.0348 +/- 0.0061 | 0.9882 +/- 0.0039 | 0.9519 +/- 0.0311 | 0.0000 +/- 0.0000 | 0.0000 +/- 0.0000 |
| spt_nrtl | external_fixed_to_joint_test | isothermal | 3 | evaluated_partial_seeds | 4/5 | 1.5329 +/- 0.7368 | 2.5071 +/- 1.0305 | 0.9761 +/- 0.0219 | 0.0144 +/- 0.0059 | 0.0240 +/- 0.0114 | 0.9885 +/- 0.0109 | 0.8000 +/- 0.4472 | 0.0000 +/- 0.0000 | 0.0000 +/- 0.0000 |
| spt_nrtl_adapted | joint_train_joint_test | isobaric | 2 | evaluated | 5/5 | 15.2994 +/- 1.4598 | 29.3075 +/- 5.4009 | 0.0376 +/- 0.2482 | 0.1458 +/- 0.0109 | 0.2259 +/- 0.0068 | 0.4796 +/- 0.0349 | 0.9501 +/- 0.0289 | 0.0000 +/- 0.0000 | 0.0499 +/- 0.0289 |
| spt_nrtl_adapted | joint_train_joint_test | isobaric | 2+3 | evaluated | 5/5 | 16.6724 +/- 3.6753 | 31.4836 +/- 8.9330 | -0.2116 +/- 0.7330 | 0.1485 +/- 0.0054 | 0.2279 +/- 0.0141 | 0.4535 +/- 0.0615 | 0.9525 +/- 0.0297 | 0.0000 +/- 0.0000 | 0.0475 +/- 0.0297 |
| spt_nrtl_adapted | joint_train_joint_test | isobaric | 3 | evaluated_partial_seeds | 4/5 | 27.7649 +/- 22.0077 | 37.7381 +/- 33.3590 | -11.8269 +/- 19.7124 | 0.1612 +/- 0.0659 | 0.2241 +/- 0.1096 | 0.0449 +/- 0.5580 | 0.7943 +/- 0.4442 | 0.0000 +/- 0.0000 | 0.0057 +/- 0.0128 |
| spt_nrtl_adapted | joint_train_joint_test | isothermal | 2 | evaluated | 5/5 | 35.0891 +/- 13.9439 | 91.3306 +/- 54.6171 | 0.1831 +/- 0.9733 | 0.0915 +/- 0.0079 | 0.1357 +/- 0.0091 | 0.8265 +/- 0.0268 | 1.0000 +/- 0.0000 | 0.0000 +/- 0.0000 | 0.0000 +/- 0.0000 |
| spt_nrtl_adapted | joint_train_joint_test | isothermal | 2+3 | evaluated | 5/5 | 32.3992 +/- 12.6923 | 86.3058 +/- 51.5257 | 0.1979 +/- 0.9498 | 0.0864 +/- 0.0043 | 0.1283 +/- 0.0059 | 0.8408 +/- 0.0182 | 1.0000 +/- 0.0000 | 0.0000 +/- 0.0000 | 0.0000 +/- 0.0000 |
| spt_nrtl_adapted | joint_train_joint_test | isothermal | 3 | evaluated_partial_seeds | 4/5 | 9.6580 +/- 1.8099 | 11.7574 +/- 2.3242 | 0.6163 +/- 0.1326 | 0.0605 +/- 0.0085 | 0.0774 +/- 0.0137 | 0.9043 +/- 0.0293 | 0.8000 +/- 0.4472 | 0.0000 +/- 0.0000 | 0.0000 +/- 0.0000 |

## Joint-trained residual adaptations of external activity models

The official HANNA and TeNNet-SAC rows remain unchanged. The following additional
rows freeze every official base-model parameter and train only a 1,345-parameter
permutation-equivariant residual head on the registered joint binary/ternary training
partition. Checkpoints are selected by validation activity-coefficient loss; the test
partition is used once for final VLE evaluation.

| Model | Direction | State MAE / RMSE / R² | y MAE / RMSE / R² | Coverage | Solver failure |
|---|---|---|---|---:|---:|
| HANNA adapted | Isothermal | P: 5.169 ± 3.038 kPa / 12.826 ± 9.545 kPa / 0.985 ± 0.020 | 0.0137 ± 0.0027 / 0.0293 ± 0.0071 / 0.991 ± 0.004 | 100.0 ± 0.0% | 0.0 ± 0.0% |
| HANNA adapted | Isobaric | T: 8.337 ± 3.553 K / 24.199 ± 12.480 K / 0.255 ± 0.655 | 0.0803 ± 0.0314 / 0.1694 ± 0.0357 / 0.691 ± 0.131 | 96.7 ± 2.0% | 3.3 ± 2.0% |
| TeNNet-SAC adapted | Isothermal | P: 6.182 ± 2.549 kPa / 14.536 ± 7.740 kPa / 0.982 ± 0.015 | 0.0193 ± 0.0042 / 0.0380 ± 0.0109 / 0.985 ± 0.007 | 100.0 ± 0.0% | 0.0 ± 0.0% |
| TeNNet-SAC adapted | Isobaric | T: 8.278 ± 3.081 K / 20.535 ± 4.400 K / 0.501 ± 0.208 | 0.0835 ± 0.0284 / 0.1686 ± 0.0329 / 0.696 ± 0.116 | 96.7 ± 2.1% | 3.3 ± 2.1% |

Relative to the fixed official model, HANNA adaptation does not provide a consistent
improvement: isothermal pressure and isobaric temperature errors increase slightly,
while composition changes are negligible. TeNNet-SAC adaptation gives small gains in
isothermal and isobaric composition MAE and in isobaric temperature MAE, but slightly
worsens isothermal pressure MAE. The differences are modest relative to seed-to-seed
variation; neither adapted row establishes a broad statistically clear advantage over
its official frozen counterpart.
