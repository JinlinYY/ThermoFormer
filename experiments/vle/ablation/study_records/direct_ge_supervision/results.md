# Direct-GE three-stage ThermoFormer: five-seed formal comparison

Protocol: `overall_binary_ternary`; seeds 0--4; validation-only checkpoint selection; test used once after checkpoint locking.

## Validation-selected and diagnostic results

| Variant | Scope | P MAE / RMSE / R2 | y isothermal MAE / RMSE / R2 | T MAE / RMSE / R2 | y isobaric MAE / RMSE / R2 | Coverage iso / isob |
|---|---|---|---|---|---|---|
| Original C1 | joint | 8.0072 +/- 3.8042 / 20.6096 +/- 8.1930 / 0.9651 +/- 0.0204 | 0.0242 +/- 0.0052 / 0.0445 +/- 0.0107 / 0.9803 +/- 0.0088 | 2.3006 +/- 0.3492 / 4.0025 +/- 0.6362 / 0.9810 +/- 0.0075 | 0.0291 +/- 0.0046 / 0.0534 +/- 0.0095 / 0.9696 +/- 0.0107 | 1.0000 +/- 0.0000 / 1.0000 +/- 0.0000 |
| Original C1 | binary | 8.9185 +/- 4.8312 / 22.0851 +/- 9.7300 / 0.9640 +/- 0.0223 | 0.0254 +/- 0.0052 / 0.0470 +/- 0.0112 / 0.9786 +/- 0.0093 | 2.3524 +/- 0.3311 / 4.1146 +/- 0.5877 / 0.9805 +/- 0.0072 | 0.0283 +/- 0.0039 / 0.0517 +/- 0.0063 / 0.9726 +/- 0.0061 | 1.0000 +/- 0.0000 / 1.0000 +/- 0.0000 |
| Original C1 | ternary | 1.9311 +/- 0.5060 / 2.5919 +/- 0.7181 / 0.9787 +/- 0.0144 | 0.0165 +/- 0.0045 / 0.0242 +/- 0.0071 / 0.9904 +/- 0.0051 | 1.6297 +/- 0.3442 / 2.0784 +/- 0.6780 / 0.9787 +/- 0.0246 | 0.0313 +/- 0.0188 / 0.0518 +/- 0.0369 / 0.9219 +/- 0.0793 | 1.0000 +/- 0.0000 / 1.0000 +/- 0.0000 |
| Validation-selected final | joint | 8.0072 +/- 3.8042 / 20.6096 +/- 8.1930 / 0.9651 +/- 0.0204 | 0.0242 +/- 0.0052 / 0.0445 +/- 0.0107 / 0.9803 +/- 0.0088 | 2.3006 +/- 0.3492 / 4.0025 +/- 0.6362 / 0.9810 +/- 0.0075 | 0.0291 +/- 0.0046 / 0.0534 +/- 0.0095 / 0.9696 +/- 0.0107 | 1.0000 +/- 0.0000 / 1.0000 +/- 0.0000 |
| Validation-selected final | binary | 8.9185 +/- 4.8312 / 22.0851 +/- 9.7300 / 0.9640 +/- 0.0223 | 0.0254 +/- 0.0052 / 0.0470 +/- 0.0112 / 0.9786 +/- 0.0093 | 2.3524 +/- 0.3311 / 4.1146 +/- 0.5877 / 0.9805 +/- 0.0072 | 0.0283 +/- 0.0039 / 0.0517 +/- 0.0063 / 0.9726 +/- 0.0061 | 1.0000 +/- 0.0000 / 1.0000 +/- 0.0000 |
| Validation-selected final | ternary | 1.9311 +/- 0.5060 / 2.5919 +/- 0.7181 / 0.9787 +/- 0.0144 | 0.0165 +/- 0.0045 / 0.0242 +/- 0.0071 / 0.9904 +/- 0.0051 | 1.6297 +/- 0.3442 / 2.0784 +/- 0.6780 / 0.9787 +/- 0.0246 | 0.0313 +/- 0.0188 / 0.0518 +/- 0.0369 / 0.9219 +/- 0.0793 | 1.0000 +/- 0.0000 / 1.0000 +/- 0.0000 |
| Stage 3 diagnostic | joint | 7.3846 +/- 4.0464 / 17.5698 +/- 8.6913 / 0.9744 +/- 0.0164 | 0.0243 +/- 0.0063 / 0.0467 +/- 0.0149 / 0.9776 +/- 0.0134 | 2.6463 +/- 1.4692 / 4.5796 +/- 1.7670 / 0.9711 +/- 0.0280 | 0.0339 +/- 0.0142 / 0.0580 +/- 0.0188 / 0.9622 +/- 0.0241 | 1.0000 +/- 0.0000 / 1.0000 +/- 0.0000 |
| Stage 3 diagnostic | binary | 8.0513 +/- 4.4616 / 18.5696 +/- 9.0004 / 0.9739 +/- 0.0166 | 0.0249 +/- 0.0062 / 0.0480 +/- 0.0151 / 0.9769 +/- 0.0137 | 2.6769 +/- 1.4509 / 4.6979 +/- 1.7086 / 0.9705 +/- 0.0277 | 0.0327 +/- 0.0144 / 0.0556 +/- 0.0177 / 0.9660 +/- 0.0241 | 1.0000 +/- 0.0000 / 1.0000 +/- 0.0000 |
| Stage 3 diagnostic | ternary | 1.8669 +/- 1.2207 / 2.4499 +/- 1.4687 / 0.9791 +/- 0.0251 | 0.0182 +/- 0.0060 / 0.0289 +/- 0.0131 / 0.9857 +/- 0.0121 | 1.5690 +/- 0.5701 / 1.9971 +/- 0.8252 / 0.9817 +/- 0.0241 | 0.0330 +/- 0.0181 / 0.0544 +/- 0.0374 / 0.9139 +/- 0.0879 | 1.0000 +/- 0.0000 / 1.0000 +/- 0.0000 |

Validation-selected stage counts: stage0: 5.
The Stage 3 row is pre-registered diagnostic evidence and is never selected using test metrics.

## Same-protocol baseline comparison

Only joint 2+3 test rows are shown. External and partial-coverage references are labelled and do not enter a same-data overall-winner claim.

| Model | Group | P MAE | y isothermal MAE | T MAE | y isobaric MAE | Coverage iso / isob | Provenance |
|---|---|---:|---:|---:|---:|---:|---|
| SPT-NRTL adapted | same registered train/split | 32.3992 +/- 12.6923 | 0.0864 +/- 0.0043 | 16.6724 +/- 3.6753 | 0.1485 +/- 0.0054 | 1.0000 +/- 0.0000 / 0.9525 +/- 0.0297 | hash_verified |
| HANNA adapted | external frozen representation | 5.1691 +/- 3.0385 | 0.0137 +/- 0.0027 | 8.3368 +/- 3.5527 | 0.0803 +/- 0.0314 | 1.0000 +/- 0.0000 / 0.9668 +/- 0.0205 | registered_id_audited |
| TeNNet-SAC adapted | external frozen representation | 6.1823 +/- 2.5493 | 0.0193 +/- 0.0042 | 8.2778 +/- 3.0806 | 0.0835 +/- 0.0284 | 1.0000 +/- 0.0000 / 0.9667 +/- 0.0207 | registered_id_audited |
| HANNA official | external pretrained reference | 4.9461 +/- 3.1478 | 0.0137 +/- 0.0027 | 8.1393 +/- 3.4184 | 0.0804 +/- 0.0309 | 1.0000 +/- 0.0000 / 0.9677 +/- 0.0208 | hash_verified |
| TeNNet-SAC official | external pretrained reference | 6.0253 +/- 2.7947 | 0.0198 +/- 0.0037 | 8.4148 +/- 3.1613 | 0.0844 +/- 0.0280 | 1.0000 +/- 0.0000 / 0.9681 +/- 0.0179 | hash_verified |
| SPT-NRTL external | external database reference | 4.5628 +/- 2.6711 | 0.0183 +/- 0.0024 | 10.0959 +/- 3.3223 | 0.0865 +/- 0.0305 | 0.9519 +/- 0.0311 / 0.9690 +/- 0.0157 | hash_verified |
| SolvGNN | 298 K partial-coverage reference | 1.5541 +/- 0.9979 | 0.0393 +/- 0.0410 | N/A | N/A | 0.0337 +/- 0.0040 / N/A | hash_verified |

SolvGNN remains a 298.15 +/- 0.5 K partial-coverage reference and is excluded from full-test ranking. Binary-only baselines remain in their registered binary table and are not ranked against this joint protocol.

## Resources

Training time per seed: 2141.4190 +/- 594.4674 s; peak allocated GPU memory: 174.6851 +/- 0.0000 MB.
Total parameters: 2,015,043; Stage-3 trainable parameters: 260,355.
