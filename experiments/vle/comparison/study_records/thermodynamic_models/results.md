# NRTL, Wilson, and UNIQUAC state-generalization results

Status: completed.

The classical models use shared ordered molecular-pair parameters fitted directly to pressure and vapor-composition residuals in the registered training partition. Validation and test labels are not used for fitting. Composition interpolation uses its five distinct data splits. The other state protocols have one deterministic partition and are fitted once; ThermoFormer values retain five neural-network seeds.

## All systems: P-x-y

| Protocol | Model | P MAE (kPa) | P RMSE (kPa) | P R² | y MAE | y RMSE | y R² | Valid coverage | Parameter coverage |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Composition interpolation | NRTL | 1.081 ± 0.061 | 3.568 ± 0.354 | 0.9979 ± 0.0004 | 0.0080 ± 0.0001 | 0.0135 ± 0.0004 | 0.9976 ± 0.0002 | 1.000 ± 0.000 | 1.000 |
| Composition interpolation | Wilson | 1.210 ± 0.067 | 4.235 ± 0.341 | 0.9971 ± 0.0005 | 0.0078 ± 0.0001 | 0.0130 ± 0.0004 | 0.9977 ± 0.0001 | 1.000 ± 0.000 | 1.000 |
| Composition interpolation | UNIQUAC | 1.941 ± 0.097 | 5.381 ± 0.492 | 0.9977 ± 0.0004 | 0.0095 ± 0.0001 | 0.0136 ± 0.0001 | 0.9971 ± 0.0001 | 0.320 ± 0.000 | 0.418 |
| Composition interpolation | ThermoFormer C1 + fugacity | 1.613 ± 0.201 | 5.373 ± 0.833 | 0.9953 ± 0.0014 | 0.0095 ± 0.0010 | 0.0142 ± 0.0014 | 0.9973 ± 0.0005 | 1.000 ± 0.000 | 1.000 |
| Composition-edge extrapolation | NRTL | 1.064 | 3.835 | 0.9977 | 0.0073 | 0.0174 | 0.9983 | 1.000 | 1.000 |
| Composition-edge extrapolation | Wilson | 1.089 | 4.101 | 0.9974 | 0.0063 | 0.0160 | 0.9985 | 1.000 | 1.000 |
| Composition-edge extrapolation | UNIQUAC | 1.605 | 5.150 | 0.9974 | 0.0088 | 0.0205 | 0.9978 | 0.311 | 0.415 |
| Composition-edge extrapolation | ThermoFormer C1 + fugacity | 1.906 ± 0.205 | 4.981 ± 0.869 | 0.9960 ± 0.0014 | 0.0075 ± 0.0007 | 0.0143 ± 0.0012 | 0.9988 ± 0.0002 | 1.000 ± 0.000 | 1.000 |
| Low-temperature extrapolation | NRTL | 1.702 | 6.527 | 0.9915 | 0.0112 | 0.0280 | 0.9925 | 1.000 | 1.000 |
| Low-temperature extrapolation | Wilson | 1.737 | 6.263 | 0.9921 | 0.0111 | 0.0281 | 0.9924 | 1.000 | 1.000 |
| Low-temperature extrapolation | UNIQUAC | 1.664 | 3.100 | 0.9992 | 0.0092 | 0.0128 | 0.9982 | 0.316 | 0.424 |
| Low-temperature extrapolation | ThermoFormer C1 + fugacity | 2.051 ± 0.583 | 3.686 ± 1.311 | 0.9970 ± 0.0022 | 0.0136 ± 0.0012 | 0.0204 ± 0.0016 | 0.9960 ± 0.0006 | 1.000 ± 0.000 | 1.000 |
| High-temperature extrapolation | NRTL | 3.314 | 9.594 | 0.9938 | 0.0103 | 0.0250 | 0.9929 | 1.000 | 1.000 |
| High-temperature extrapolation | Wilson | 3.427 | 10.137 | 0.9930 | 0.0099 | 0.0248 | 0.9930 | 1.000 | 1.000 |
| High-temperature extrapolation | UNIQUAC | 4.393 | 9.612 | 0.9959 | 0.0106 | 0.0144 | 0.9973 | 0.360 | 0.424 |
| High-temperature extrapolation | ThermoFormer C1 + fugacity | 5.827 ± 0.420 | 13.477 ± 0.593 | 0.9877 ± 0.0011 | 0.0120 ± 0.0011 | 0.0194 ± 0.0020 | 0.9957 ± 0.0009 | 1.000 ± 0.000 | 1.000 |
| Low-pressure extrapolation | NRTL | 0.648 | 1.936 | 0.9971 | 0.0103 | 0.0257 | 0.9937 | 1.000 | 1.000 |
| Low-pressure extrapolation | Wilson | 0.618 | 1.748 | 0.9976 | 0.0100 | 0.0232 | 0.9949 | 1.000 | 1.000 |
| Low-pressure extrapolation | UNIQUAC | 0.594 | 0.840 | 0.9993 | 0.0124 | 0.0241 | 0.9947 | 0.289 | 0.397 |
| Low-pressure extrapolation | ThermoFormer C1 + fugacity | 1.152 ± 0.236 | 2.952 ± 0.579 | 0.9930 ± 0.0025 | 0.0160 ± 0.0039 | 0.0247 ± 0.0062 | 0.9939 ± 0.0029 | 1.000 ± 0.000 | 1.000 |
| High-pressure extrapolation | NRTL | 2.946 | 8.376 | 0.9956 | 0.0073 | 0.0125 | 0.9987 | 1.000 | 1.000 |
| High-pressure extrapolation | Wilson | 3.012 | 8.747 | 0.9952 | 0.0067 | 0.0117 | 0.9988 | 1.000 | 1.000 |
| High-pressure extrapolation | UNIQUAC | 3.634 | 8.373 | 0.9972 | 0.0099 | 0.0144 | 0.9978 | 0.350 | 0.397 |
| High-pressure extrapolation | ThermoFormer C1 + fugacity | 5.962 ± 1.350 | 13.007 ± 3.062 | 0.9888 ± 0.0055 | 0.0128 ± 0.0042 | 0.0237 ± 0.0097 | 0.9945 ± 0.0047 | 1.000 ± 0.000 | 1.000 |

## All systems: T-x-y

| Protocol | Model | T MAE (K) | T RMSE (K) | T R² | y MAE | y RMSE | y R² | Valid coverage | Parameter coverage |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Composition interpolation | NRTL | 9.156 ± 1.100 | 40.406 ± 5.924 | -1.4882 ± 0.7295 | 0.0633 ± 0.0004 | 0.1391 ± 0.0007 | 0.7292 ± 0.0026 | 0.995 ± 0.003 | 1.000 |
| Composition interpolation | Wilson | 5.118 ± 0.187 | 26.017 ± 1.633 | -0.0154 ± 0.1301 | 0.0553 ± 0.0003 | 0.1242 ± 0.0007 | 0.7842 ± 0.0025 | 0.998 ± 0.000 | 1.000 |
| Composition interpolation | UNIQUAC | 0.841 ± 0.029 | 2.180 ± 0.268 | 0.9917 ± 0.0021 | 0.0263 ± 0.0003 | 0.0586 ± 0.0006 | 0.9494 ± 0.0011 | 0.495 ± 0.000 | 0.418 |
| Composition interpolation | ThermoFormer C1 + fugacity | 0.578 ± 0.036 | 0.857 ± 0.057 | 0.9989 ± 0.0002 | 0.0166 ± 0.0009 | 0.0331 ± 0.0007 | 0.9847 ± 0.0007 | 1.000 ± 0.000 | 1.000 |
| Composition-edge extrapolation | NRTL | 4.054 | 18.459 | 0.6365 | 0.0368 | 0.0947 | 0.9457 | 0.970 | 1.000 |
| Composition-edge extrapolation | Wilson | 7.051 | 33.680 | -0.2257 | 0.0343 | 0.0832 | 0.9583 | 0.985 | 1.000 |
| Composition-edge extrapolation | UNIQUAC | 1.130 | 7.608 | 0.9210 | 0.0164 | 0.0393 | 0.9914 | 0.486 | 0.415 |
| Composition-edge extrapolation | ThermoFormer C1 + fugacity | 0.920 ± 0.098 | 1.370 ± 0.124 | 0.9980 ± 0.0003 | 0.0152 ± 0.0003 | 0.0385 ± 0.0004 | 0.9911 ± 0.0002 | 1.000 ± 0.000 | 1.000 |
| Low-temperature extrapolation | NRTL | 5.605 | 27.536 | -0.4285 | 0.0301 | 0.0893 | 0.9443 | 0.982 | 1.000 |
| Low-temperature extrapolation | Wilson | 6.265 | 33.398 | -1.0836 | 0.0278 | 0.0782 | 0.9574 | 0.988 | 1.000 |
| Low-temperature extrapolation | UNIQUAC | 0.598 | 0.865 | 0.9983 | 0.0143 | 0.0317 | 0.9924 | 0.497 | 0.424 |
| Low-temperature extrapolation | ThermoFormer C1 + fugacity | 1.162 ± 0.162 | 2.094 ± 0.400 | 0.9916 ± 0.0033 | 0.0112 ± 0.0006 | 0.0240 ± 0.0019 | 0.9960 ± 0.0006 | 1.000 ± 0.000 | 1.000 |
| High-temperature extrapolation | NRTL | 5.368 | 20.926 | 0.4991 | 0.0523 | 0.1116 | 0.8791 | 0.976 | 1.000 |
| High-temperature extrapolation | Wilson | 6.640 | 24.763 | 0.2957 | 0.0490 | 0.0949 | 0.9133 | 0.983 | 1.000 |
| High-temperature extrapolation | UNIQUAC | 1.643 | 4.096 | 0.9774 | 0.0305 | 0.0570 | 0.9683 | 0.474 | 0.424 |
| High-temperature extrapolation | ThermoFormer C1 + fugacity | 1.113 ± 0.060 | 1.765 ± 0.094 | 0.9965 ± 0.0004 | 0.0219 ± 0.0012 | 0.0399 ± 0.0012 | 0.9849 ± 0.0009 | 1.000 ± 0.000 | 1.000 |
| Low-pressure extrapolation | NRTL | 1.920 | 13.830 | 0.5317 | 0.0161 | 0.0358 | 0.9856 | 0.974 | 1.000 |
| Low-pressure extrapolation | Wilson | 2.715 | 19.788 | 0.0402 | 0.0172 | 0.0633 | 0.9552 | 0.963 | 1.000 |
| Low-pressure extrapolation | UNIQUAC | 0.770 | 1.111 | 0.9975 | 0.0131 | 0.0206 | 0.9951 | 0.705 | 0.397 |
| Low-pressure extrapolation | ThermoFormer C1 + fugacity | 0.847 ± 0.094 | 1.186 ± 0.126 | 0.9964 ± 0.0007 | 0.0162 ± 0.0041 | 0.0237 ± 0.0051 | 0.9936 ± 0.0026 | 1.000 ± 0.000 | 1.000 |
| High-pressure extrapolation | NRTL | 7.835 | 29.982 | -1.9271 | 0.0544 | 0.1461 | 0.7356 | 0.982 | 1.000 |
| High-pressure extrapolation | Wilson | 7.196 | 28.726 | -1.6869 | 0.0519 | 0.1379 | 0.7645 | 0.982 | 1.000 |
| High-pressure extrapolation | UNIQUAC | 0.845 | 1.203 | 0.9945 | 0.0173 | 0.0260 | 0.9909 | 0.601 | 0.397 |
| High-pressure extrapolation | ThermoFormer C1 + fugacity | 0.944 ± 0.191 | 1.313 ± 0.244 | 0.9943 ± 0.0022 | 0.0202 ± 0.0052 | 0.0293 ± 0.0058 | 0.9889 ± 0.0048 | 1.000 ± 0.000 | 1.000 |

## Binary systems: P-x-y

| Protocol | Model | P MAE (kPa) | P RMSE (kPa) | P R² | y MAE | y RMSE | y R² | Valid coverage | Parameter coverage |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Composition interpolation | NRTL | 1.260 ± 0.083 | 4.092 ± 0.414 | 0.9979 ± 0.0004 | 0.0082 ± 0.0001 | 0.0131 ± 0.0005 | 0.9978 ± 0.0002 | 1.000 ± 0.000 | 1.000 |
| Composition interpolation | Wilson | 1.435 ± 0.091 | 4.865 ± 0.399 | 0.9970 ± 0.0005 | 0.0081 ± 0.0001 | 0.0126 ± 0.0006 | 0.9979 ± 0.0002 | 1.000 ± 0.000 | 1.000 |
| Composition interpolation | UNIQUAC | 1.941 ± 0.097 | 5.381 ± 0.492 | 0.9977 ± 0.0004 | 0.0095 ± 0.0001 | 0.0136 ± 0.0001 | 0.9971 ± 0.0001 | 0.427 ± 0.000 | 0.451 |
| Composition interpolation | ThermoFormer C1 + fugacity | 1.953 ± 0.254 | 6.188 ± 0.964 | 0.9951 ± 0.0015 | 0.0102 ± 0.0013 | 0.0149 ± 0.0020 | 0.9971 ± 0.0008 | 1.000 ± 0.000 | 1.000 |
| Composition-edge extrapolation | NRTL | 1.171 | 4.374 | 0.9977 | 0.0062 | 0.0166 | 0.9987 | 1.000 | 1.000 |
| Composition-edge extrapolation | Wilson | 1.211 | 4.693 | 0.9973 | 0.0050 | 0.0148 | 0.9989 | 1.000 | 1.000 |
| Composition-edge extrapolation | UNIQUAC | 1.605 | 5.150 | 0.9974 | 0.0088 | 0.0205 | 0.9978 | 0.419 | 0.448 |
| Composition-edge extrapolation | ThermoFormer C1 + fugacity | 2.235 ± 0.256 | 5.726 ± 1.016 | 0.9959 ± 0.0015 | 0.0065 ± 0.0007 | 0.0145 ± 0.0014 | 0.9990 ± 0.0002 | 1.000 ± 0.000 | 1.000 |
| Low-temperature extrapolation | NRTL | 2.049 | 7.280 | 0.9912 | 0.0125 | 0.0314 | 0.9912 | 1.000 | 1.000 |
| Low-temperature extrapolation | Wilson | 2.091 | 6.984 | 0.9919 | 0.0124 | 0.0316 | 0.9911 | 1.000 | 1.000 |
| Low-temperature extrapolation | UNIQUAC | 1.664 | 3.100 | 0.9992 | 0.0092 | 0.0128 | 0.9982 | 0.394 | 0.449 |
| Low-temperature extrapolation | ThermoFormer C1 + fugacity | 2.268 ± 0.674 | 4.038 ± 1.467 | 0.9970 ± 0.0023 | 0.0142 ± 0.0011 | 0.0211 ± 0.0015 | 0.9960 ± 0.0006 | 1.000 ± 0.000 | 1.000 |
| High-temperature extrapolation | NRTL | 4.196 | 11.023 | 0.9934 | 0.0124 | 0.0299 | 0.9903 | 1.000 | 1.000 |
| High-temperature extrapolation | Wilson | 4.300 | 11.642 | 0.9927 | 0.0118 | 0.0296 | 0.9905 | 1.000 | 1.000 |
| High-temperature extrapolation | UNIQUAC | 4.393 | 9.612 | 0.9959 | 0.0106 | 0.0144 | 0.9973 | 0.477 | 0.449 |
| High-temperature extrapolation | ThermoFormer C1 + fugacity | 7.156 ± 0.441 | 15.454 ± 0.699 | 0.9871 ± 0.0012 | 0.0143 ± 0.0016 | 0.0225 ± 0.0025 | 0.9945 ± 0.0012 | 1.000 ± 0.000 | 1.000 |
| Low-pressure extrapolation | NRTL | 0.715 | 2.163 | 0.9972 | 0.0112 | 0.0279 | 0.9934 | 1.000 | 1.000 |
| Low-pressure extrapolation | Wilson | 0.676 | 1.928 | 0.9978 | 0.0112 | 0.0255 | 0.9945 | 1.000 | 1.000 |
| Low-pressure extrapolation | UNIQUAC | 0.594 | 0.840 | 0.9993 | 0.0124 | 0.0241 | 0.9947 | 0.390 | 0.450 |
| Low-pressure extrapolation | ThermoFormer C1 + fugacity | 1.333 ± 0.299 | 3.377 ± 0.678 | 0.9930 ± 0.0025 | 0.0173 ± 0.0047 | 0.0266 ± 0.0074 | 0.9937 ± 0.0032 | 1.000 ± 0.000 | 1.000 |
| High-pressure extrapolation | NRTL | 3.560 | 9.618 | 0.9953 | 0.0075 | 0.0132 | 0.9987 | 1.000 | 1.000 |
| High-pressure extrapolation | Wilson | 3.626 | 10.046 | 0.9949 | 0.0070 | 0.0124 | 0.9988 | 1.000 | 1.000 |
| High-pressure extrapolation | UNIQUAC | 3.634 | 8.373 | 0.9972 | 0.0099 | 0.0144 | 0.9978 | 0.466 | 0.450 |
| High-pressure extrapolation | ThermoFormer C1 + fugacity | 7.231 ± 1.693 | 14.933 ± 3.532 | 0.9882 ± 0.0058 | 0.0148 ± 0.0057 | 0.0274 ± 0.0121 | 0.9933 ± 0.0062 | 1.000 ± 0.000 | 1.000 |

## Binary systems: T-x-y

| Protocol | Model | T MAE (K) | T RMSE (K) | T R² | y MAE | y RMSE | y R² | Valid coverage | Parameter coverage |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Composition interpolation | NRTL | 9.703 ± 1.384 | 41.784 ± 7.181 | -1.5947 ± 0.8904 | 0.0607 ± 0.0006 | 0.1468 ± 0.0009 | 0.7086 ± 0.0033 | 0.993 ± 0.004 | 1.000 |
| Composition interpolation | Wilson | 5.263 ± 0.457 | 26.127 ± 2.939 | 0.0009 ± 0.2350 | 0.0515 ± 0.0001 | 0.1299 ± 0.0003 | 0.7721 ± 0.0011 | 0.997 ± 0.000 | 1.000 |
| Composition interpolation | UNIQUAC | 0.827 ± 0.037 | 2.258 ± 0.310 | 0.9918 ± 0.0023 | 0.0214 ± 0.0004 | 0.0468 ± 0.0006 | 0.9687 ± 0.0009 | 0.523 ± 0.000 | 0.451 |
| Composition interpolation | ThermoFormer C1 + fugacity | 0.573 ± 0.037 | 0.845 ± 0.071 | 0.9990 ± 0.0002 | 0.0130 ± 0.0008 | 0.0192 ± 0.0011 | 0.9950 ± 0.0006 | 1.000 ± 0.000 | 1.000 |
| Composition-edge extrapolation | NRTL | 4.629 | 20.723 | 0.5733 | 0.0261 | 0.0837 | 0.9641 | 0.964 | 1.000 |
| Composition-edge extrapolation | Wilson | 8.211 | 37.747 | -0.4359 | 0.0233 | 0.0692 | 0.9756 | 0.981 | 1.000 |
| Composition-edge extrapolation | UNIQUAC | 1.119 | 8.273 | 0.9146 | 0.0111 | 0.0266 | 0.9966 | 0.514 | 0.448 |
| Composition-edge extrapolation | ThermoFormer C1 + fugacity | 0.910 ± 0.108 | 1.330 ± 0.144 | 0.9983 ± 0.0004 | 0.0096 ± 0.0005 | 0.0215 ± 0.0007 | 0.9976 ± 0.0001 | 1.000 ± 0.000 | 1.000 |
| Low-temperature extrapolation | NRTL | 5.813 | 29.393 | -0.6553 | 0.0205 | 0.0816 | 0.9584 | 0.977 | 1.000 |
| Low-temperature extrapolation | Wilson | 6.397 | 35.427 | -1.3754 | 0.0180 | 0.0669 | 0.9722 | 0.985 | 1.000 |
| Low-temperature extrapolation | UNIQUAC | 0.547 | 0.783 | 0.9988 | 0.0085 | 0.0120 | 0.9990 | 0.524 | 0.449 |
| Low-temperature extrapolation | ThermoFormer C1 + fugacity | 1.261 ± 0.188 | 2.272 ± 0.447 | 0.9899 ± 0.0040 | 0.0079 ± 0.0006 | 0.0179 ± 0.0023 | 0.9980 ± 0.0005 | 1.000 ± 0.000 | 1.000 |
| High-temperature extrapolation | NRTL | 6.144 | 23.418 | 0.3863 | 0.0437 | 0.1052 | 0.9078 | 0.970 | 1.000 |
| High-temperature extrapolation | Wilson | 7.506 | 27.512 | 0.1489 | 0.0400 | 0.0839 | 0.9419 | 0.978 | 1.000 |
| High-temperature extrapolation | UNIQUAC | 1.638 | 4.347 | 0.9756 | 0.0256 | 0.0448 | 0.9830 | 0.496 | 0.449 |
| High-temperature extrapolation | ThermoFormer C1 + fugacity | 1.072 ± 0.077 | 1.761 ± 0.125 | 0.9966 ± 0.0005 | 0.0180 ± 0.0013 | 0.0298 ± 0.0017 | 0.9927 ± 0.0008 | 1.000 ± 0.000 | 1.000 |
| Low-pressure extrapolation | NRTL | 1.920 | 13.830 | 0.5317 | 0.0161 | 0.0358 | 0.9856 | 0.974 | 1.000 |
| Low-pressure extrapolation | Wilson | 2.715 | 19.788 | 0.0402 | 0.0172 | 0.0633 | 0.9552 | 0.963 | 1.000 |
| Low-pressure extrapolation | UNIQUAC | 0.770 | 1.111 | 0.9975 | 0.0131 | 0.0206 | 0.9951 | 0.705 | 0.450 |
| Low-pressure extrapolation | ThermoFormer C1 + fugacity | 0.847 ± 0.094 | 1.186 ± 0.126 | 0.9964 ± 0.0007 | 0.0162 ± 0.0041 | 0.0237 ± 0.0051 | 0.9936 ± 0.0026 | 1.000 ± 0.000 | 1.000 |
| High-pressure extrapolation | NRTL | 7.835 | 29.982 | -1.9271 | 0.0544 | 0.1461 | 0.7356 | 0.982 | 1.000 |
| High-pressure extrapolation | Wilson | 7.196 | 28.726 | -1.6869 | 0.0519 | 0.1379 | 0.7645 | 0.982 | 1.000 |
| High-pressure extrapolation | UNIQUAC | 0.845 | 1.203 | 0.9945 | 0.0173 | 0.0260 | 0.9909 | 0.601 | 0.450 |
| High-pressure extrapolation | ThermoFormer C1 + fugacity | 0.944 ± 0.191 | 1.313 ± 0.244 | 0.9943 ± 0.0022 | 0.0202 ± 0.0052 | 0.0293 ± 0.0058 | 0.9889 ± 0.0048 | 1.000 ± 0.000 | 1.000 |

## Ternary systems: P-x-y

| Protocol | Model | P MAE (kPa) | P RMSE (kPa) | P R² | y MAE | y RMSE | y R² | Valid coverage | Parameter coverage |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Composition interpolation | NRTL | 0.549 ± 0.008 | 0.884 ± 0.030 | 0.9981 ± 0.0001 | 0.0075 ± 0.0002 | 0.0143 ± 0.0004 | 0.9960 ± 0.0002 | 1.000 ± 0.000 | 1.000 |
| Composition interpolation | Wilson | 0.543 ± 0.017 | 0.937 ± 0.071 | 0.9979 ± 0.0003 | 0.0072 ± 0.0001 | 0.0138 ± 0.0004 | 0.9963 ± 0.0002 | 1.000 ± 0.000 | 1.000 |
| Composition interpolation | UNIQUAC | N/A | N/A | N/A | N/A | N/A | N/A | 0.000 ± 0.000 | 0.231 |
| Composition interpolation | ThermoFormer C1 + fugacity | 0.601 ± 0.091 | 0.917 ± 0.135 | 0.9979 ± 0.0006 | 0.0084 ± 0.0008 | 0.0124 ± 0.0009 | 0.9969 ± 0.0004 | 1.000 ± 0.000 | 1.000 |
| Composition-edge extrapolation | NRTL | 0.758 | 1.426 | 0.9951 | 0.0094 | 0.0189 | 0.9964 | 1.000 | 1.000 |
| Composition-edge extrapolation | Wilson | 0.738 | 1.380 | 0.9954 | 0.0088 | 0.0180 | 0.9967 | 1.000 | 1.000 |
| Composition-edge extrapolation | UNIQUAC | N/A | N/A | N/A | N/A | N/A | N/A | 0.000 | 0.231 |
| Composition-edge extrapolation | ThermoFormer C1 + fugacity | 0.965 ± 0.105 | 1.385 ± 0.123 | 0.9953 ± 0.0008 | 0.0094 ± 0.0013 | 0.0139 ± 0.0015 | 0.9980 ± 0.0004 | 1.000 ± 0.000 | 1.000 |
| Low-temperature extrapolation | NRTL | 0.287 | 0.370 | 0.9989 | 0.0077 | 0.0154 | 0.9964 | 1.000 | 1.000 |
| Low-temperature extrapolation | Wilson | 0.290 | 0.376 | 0.9989 | 0.0077 | 0.0154 | 0.9964 | 1.000 | 1.000 |
| Low-temperature extrapolation | UNIQUAC | N/A | N/A | N/A | N/A | N/A | N/A | 0.000 | 0.286 |
| Low-temperature extrapolation | ThermoFormer C1 + fugacity | 1.162 ± 0.273 | 1.527 ± 0.369 | 0.9804 ± 0.0093 | 0.0120 ± 0.0015 | 0.0185 ± 0.0022 | 0.9947 ± 0.0012 | 1.000 ± 0.000 | 1.000 |
| High-temperature extrapolation | NRTL | 0.590 | 0.966 | 0.9978 | 0.0058 | 0.0087 | 0.9988 | 1.000 | 1.000 |
| High-temperature extrapolation | Wilson | 0.728 | 1.161 | 0.9968 | 0.0062 | 0.0090 | 0.9987 | 1.000 | 1.000 |
| High-temperature extrapolation | UNIQUAC | N/A | N/A | N/A | N/A | N/A | N/A | 0.000 | 0.286 |
| High-temperature extrapolation | ThermoFormer C1 + fugacity | 1.717 ± 0.583 | 2.114 ± 0.647 | 0.9885 ± 0.0069 | 0.0073 ± 0.0006 | 0.0107 ± 0.0012 | 0.9981 ± 0.0004 | 1.000 ± 0.000 | 1.000 |
| Low-pressure extrapolation | NRTL | 0.454 | 1.035 | 0.9864 | 0.0086 | 0.0209 | 0.9929 | 1.000 | 1.000 |
| Low-pressure extrapolation | Wilson | 0.452 | 1.074 | 0.9853 | 0.0079 | 0.0179 | 0.9948 | 1.000 | 1.000 |
| Low-pressure extrapolation | UNIQUAC | N/A | N/A | N/A | N/A | N/A | N/A | 0.000 | 0.000 |
| Low-pressure extrapolation | ThermoFormer C1 + fugacity | 0.631 ± 0.086 | 0.957 ± 0.182 | 0.9880 ± 0.0048 | 0.0136 ± 0.0024 | 0.0206 ± 0.0038 | 0.9929 ± 0.0024 | 1.000 ± 0.000 | 1.000 |
| High-pressure extrapolation | NRTL | 1.099 | 1.677 | 0.9865 | 0.0070 | 0.0110 | 0.9984 | 1.000 | 1.000 |
| High-pressure extrapolation | Wilson | 1.162 | 1.709 | 0.9860 | 0.0061 | 0.0101 | 0.9986 | 1.000 | 1.000 |
| High-pressure extrapolation | UNIQUAC | N/A | N/A | N/A | N/A | N/A | N/A | 0.000 | 0.000 |
| High-pressure extrapolation | ThermoFormer C1 + fugacity | 2.139 ± 0.401 | 2.619 ± 0.485 | 0.9662 ± 0.0110 | 0.0089 ± 0.0015 | 0.0134 ± 0.0021 | 0.9975 ± 0.0008 | 1.000 ± 0.000 | 1.000 |

## Ternary systems: T-x-y

| Protocol | Model | T MAE (K) | T RMSE (K) | T R² | y MAE | y RMSE | y R² | Valid coverage | Parameter coverage |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Composition interpolation | NRTL | 7.055 ± 0.091 | 34.271 ± 0.488 | -1.0087 ± 0.0570 | 0.0700 ± 0.0003 | 0.1172 ± 0.0002 | 0.6958 ± 0.0010 | 1.000 ± 0.000 | 1.000 |
| Composition interpolation | Wilson | 4.562 ± 0.982 | 24.887 ± 4.881 | -0.0918 ± 0.3631 | 0.0651 ± 0.0012 | 0.1084 ± 0.0027 | 0.7397 ± 0.0129 | 1.000 ± 0.000 | 1.000 |
| Composition interpolation | UNIQUAC | 0.920 ± 0.020 | 1.697 ± 0.027 | 0.9887 ± 0.0004 | 0.0436 ± 0.0009 | 0.0883 ± 0.0013 | 0.7975 ± 0.0060 | 0.383 ± 0.000 | 0.231 |
| Composition interpolation | ThermoFormer C1 + fugacity | 0.598 ± 0.043 | 0.899 ± 0.057 | 0.9986 ± 0.0002 | 0.0259 ± 0.0013 | 0.0545 ± 0.0010 | 0.9341 ± 0.0024 | 1.000 ± 0.000 | 1.000 |
| Composition-edge extrapolation | NRTL | 1.939 | 3.816 | 0.9776 | 0.0629 | 0.1172 | 0.8049 | 0.990 | 1.000 |
| Composition-edge extrapolation | Wilson | 2.758 | 7.705 | 0.9077 | 0.0615 | 0.1104 | 0.8298 | 1.000 | 1.000 |
| Composition-edge extrapolation | UNIQUAC | 1.186 | 2.047 | 0.9837 | 0.0340 | 0.0662 | 0.9358 | 0.381 | 0.231 |
| Composition-edge extrapolation | ThermoFormer C1 + fugacity | 0.960 ± 0.071 | 1.510 ± 0.086 | 0.9964 ± 0.0004 | 0.0292 ± 0.0004 | 0.0636 ± 0.0005 | 0.9436 ± 0.0010 | 1.000 ± 0.000 | 1.000 |
| Low-temperature extrapolation | NRTL | 4.743 | 17.941 | 0.3920 | 0.0567 | 0.1078 | 0.8477 | 1.000 | 1.000 |
| Low-temperature extrapolation | Wilson | 5.713 | 23.122 | -0.0099 | 0.0548 | 0.1035 | 0.8597 | 1.000 | 1.000 |
| Low-temperature extrapolation | UNIQUAC | 0.889 | 1.237 | 0.9904 | 0.0365 | 0.0658 | 0.9255 | 0.383 | 0.286 |
| Low-temperature extrapolation | ThermoFormer C1 + fugacity | 0.745 ± 0.095 | 1.044 ± 0.141 | 0.9979 ± 0.0006 | 0.0206 ± 0.0015 | 0.0358 ± 0.0029 | 0.9831 ± 0.0029 | 1.000 ± 0.000 | 1.000 |
| High-temperature extrapolation | NRTL | 2.445 | 4.635 | 0.9699 | 0.0740 | 0.1264 | 0.6078 | 1.000 | 1.000 |
| High-temperature extrapolation | Wilson | 3.351 | 8.193 | 0.9060 | 0.0716 | 0.1184 | 0.6559 | 1.000 | 1.000 |
| High-temperature extrapolation | UNIQUAC | 1.667 | 2.512 | 0.9804 | 0.0469 | 0.0857 | 0.7562 | 0.389 | 0.286 |
| High-temperature extrapolation | ThermoFormer C1 + fugacity | 1.274 ± 0.031 | 1.778 ± 0.054 | 0.9956 ± 0.0003 | 0.0319 ± 0.0019 | 0.0584 ± 0.0012 | 0.9164 ± 0.0034 | 1.000 ± 0.000 | 1.000 |

## System-macro errors

| Scope | Protocol | Model | Direction | State macro MAE | State macro RMSE | y macro MAE | y macro RMSE |
|---|---|---|---|---:|---:|---:|---:|
| All | Composition interpolation | NRTL | isothermal | 1.347 ± 0.122 | 4.124 ± 0.487 | 0.0095 ± 0.0003 | 0.0155 ± 0.0009 |
| All | Composition interpolation | NRTL | isobaric | 11.288 ± 1.738 | 45.440 ± 8.388 | 0.0779 ± 0.0006 | 0.1632 ± 0.0009 |
| All | Composition interpolation | Wilson | isothermal | 1.659 ± 0.184 | 5.279 ± 0.658 | 0.0093 ± 0.0002 | 0.0149 ± 0.0009 |
| All | Composition interpolation | Wilson | isobaric | 6.212 ± 0.211 | 28.808 ± 1.817 | 0.0671 ± 0.0003 | 0.1449 ± 0.0005 |
| All | Composition interpolation | UNIQUAC | isothermal | 2.416 ± 0.239 | 6.343 ± 0.835 | 0.0102 ± 0.0003 | 0.0142 ± 0.0002 |
| All | Composition interpolation | UNIQUAC | isobaric | 1.040 ± 0.046 | 2.673 ± 0.328 | 0.0315 ± 0.0004 | 0.0680 ± 0.0006 |
| All | Composition interpolation | ThermoFormer C1 + fugacity | isothermal | 2.404 ± 0.424 | 7.761 ± 1.842 | 0.0105 ± 0.0010 | 0.0151 ± 0.0015 |
| All | Composition interpolation | ThermoFormer C1 + fugacity | isobaric | 0.621 ± 0.043 | 0.898 ± 0.075 | 0.0163 ± 0.0008 | 0.0310 ± 0.0007 |
| All | Composition-edge extrapolation | NRTL | isothermal | 1.157 | 4.211 | 0.0079 | 0.0197 |
| All | Composition-edge extrapolation | NRTL | isobaric | 6.259 | 24.232 | 0.0419 | 0.1097 |
| All | Composition-edge extrapolation | Wilson | isothermal | 1.233 | 4.508 | 0.0072 | 0.0190 |
| All | Composition-edge extrapolation | Wilson | isobaric | 11.312 | 47.818 | 0.0372 | 0.0913 |
| All | Composition-edge extrapolation | UNIQUAC | isothermal | 1.359 | 4.609 | 0.0083 | 0.0215 |
| All | Composition-edge extrapolation | UNIQUAC | isobaric | 1.358 | 9.100 | 0.0168 | 0.0432 |
| All | Composition-edge extrapolation | ThermoFormer C1 + fugacity | isothermal | 2.533 ± 0.345 | 6.606 ± 1.487 | 0.0074 ± 0.0006 | 0.0152 ± 0.0011 |
| All | Composition-edge extrapolation | ThermoFormer C1 + fugacity | isobaric | 1.007 ± 0.118 | 1.480 ± 0.137 | 0.0140 ± 0.0005 | 0.0342 ± 0.0005 |
| All | Low-temperature extrapolation | NRTL | isothermal | 2.956 | 11.259 | 0.0174 | 0.0470 |
| All | Low-temperature extrapolation | NRTL | isobaric | 7.189 | 31.463 | 0.0317 | 0.0967 |
| All | Low-temperature extrapolation | Wilson | isothermal | 2.887 | 10.484 | 0.0175 | 0.0475 |
| All | Low-temperature extrapolation | Wilson | isobaric | 8.505 | 41.097 | 0.0288 | 0.0815 |
| All | Low-temperature extrapolation | UNIQUAC | isothermal | 1.191 | 2.347 | 0.0094 | 0.0130 |
| All | Low-temperature extrapolation | UNIQUAC | isobaric | 0.539 | 0.848 | 0.0124 | 0.0288 |
| All | Low-temperature extrapolation | ThermoFormer C1 + fugacity | isothermal | 1.857 ± 0.461 | 3.561 ± 1.176 | 0.0149 ± 0.0012 | 0.0218 ± 0.0016 |
| All | Low-temperature extrapolation | ThermoFormer C1 + fugacity | isobaric | 1.001 ± 0.109 | 1.676 ± 0.251 | 0.0109 ± 0.0005 | 0.0246 ± 0.0021 |
| All | High-temperature extrapolation | NRTL | isothermal | 6.296 | 15.676 | 0.0153 | 0.0421 |
| All | High-temperature extrapolation | NRTL | isobaric | 7.833 | 25.743 | 0.0613 | 0.1267 |
| All | High-temperature extrapolation | Wilson | isothermal | 6.382 | 16.045 | 0.0153 | 0.0427 |
| All | High-temperature extrapolation | Wilson | isobaric | 8.325 | 27.248 | 0.0539 | 0.1046 |
| All | High-temperature extrapolation | UNIQUAC | isothermal | 4.113 | 9.102 | 0.0103 | 0.0138 |
| All | High-temperature extrapolation | UNIQUAC | isobaric | 1.910 | 4.822 | 0.0313 | 0.0599 |
| All | High-temperature extrapolation | ThermoFormer C1 + fugacity | isothermal | 7.733 ± 0.685 | 17.974 ± 2.825 | 0.0130 ± 0.0008 | 0.0199 ± 0.0014 |
| All | High-temperature extrapolation | ThermoFormer C1 + fugacity | isobaric | 1.216 ± 0.077 | 2.027 ± 0.143 | 0.0213 ± 0.0013 | 0.0383 ± 0.0014 |
| All | Low-pressure extrapolation | NRTL | isothermal | 0.937 | 2.863 | 0.0137 | 0.0362 |
| All | Low-pressure extrapolation | NRTL | isobaric | 4.441 | 24.240 | 0.0238 | 0.0564 |
| All | Low-pressure extrapolation | Wilson | isothermal | 0.874 | 2.557 | 0.0131 | 0.0321 |
| All | Low-pressure extrapolation | Wilson | isobaric | 11.143 | 44.576 | 0.0461 | 0.1393 |
| All | Low-pressure extrapolation | UNIQUAC | isothermal | 0.623 | 0.835 | 0.0121 | 0.0259 |
| All | Low-pressure extrapolation | UNIQUAC | isobaric | 0.782 | 1.171 | 0.0152 | 0.0234 |
| All | Low-pressure extrapolation | ThermoFormer C1 + fugacity | isothermal | 1.892 ± 0.380 | 4.956 ± 0.867 | 0.0158 ± 0.0037 | 0.0257 ± 0.0060 |
| All | Low-pressure extrapolation | ThermoFormer C1 + fugacity | isobaric | 0.916 ± 0.164 | 1.357 ± 0.372 | 0.0187 ± 0.0033 | 0.0285 ± 0.0053 |
| All | High-pressure extrapolation | NRTL | isothermal | 4.186 | 10.973 | 0.0076 | 0.0131 |
| All | High-pressure extrapolation | NRTL | isobaric | 10.266 | 33.356 | 0.0711 | 0.1688 |
| All | High-pressure extrapolation | Wilson | isothermal | 4.766 | 12.041 | 0.0078 | 0.0144 |
| All | High-pressure extrapolation | Wilson | isobaric | 9.522 | 31.980 | 0.0680 | 0.1601 |
| All | High-pressure extrapolation | UNIQUAC | isothermal | 3.331 | 7.723 | 0.0106 | 0.0159 |
| All | High-pressure extrapolation | UNIQUAC | isobaric | 1.013 | 1.416 | 0.0211 | 0.0298 |
| All | High-pressure extrapolation | ThermoFormer C1 + fugacity | isothermal | 6.610 ± 1.481 | 14.843 ± 3.363 | 0.0116 ± 0.0029 | 0.0206 ± 0.0062 |
| All | High-pressure extrapolation | ThermoFormer C1 + fugacity | isobaric | 1.324 ± 0.148 | 1.942 ± 0.207 | 0.0221 ± 0.0064 | 0.0318 ± 0.0069 |
| Binary | Composition interpolation | NRTL | isothermal | 1.444 ± 0.142 | 4.407 ± 0.527 | 0.0093 ± 0.0003 | 0.0149 ± 0.0009 |
| Binary | Composition interpolation | NRTL | isobaric | 11.582 ± 2.056 | 46.381 ± 9.685 | 0.0752 ± 0.0006 | 0.1667 ± 0.0010 |
| Binary | Composition interpolation | Wilson | isothermal | 1.803 ± 0.213 | 5.648 ± 0.712 | 0.0092 ± 0.0002 | 0.0144 ± 0.0011 |
| Binary | Composition interpolation | Wilson | isobaric | 5.996 ± 0.522 | 27.802 ± 3.265 | 0.0637 ± 0.0003 | 0.1472 ± 0.0004 |
| Binary | Composition interpolation | UNIQUAC | isothermal | 2.416 ± 0.239 | 6.343 ± 0.835 | 0.0102 ± 0.0003 | 0.0142 ± 0.0002 |
| Binary | Composition interpolation | UNIQUAC | isobaric | 1.021 ± 0.054 | 2.739 ± 0.364 | 0.0271 ± 0.0005 | 0.0585 ± 0.0007 |
| Binary | Composition interpolation | ThermoFormer C1 + fugacity | isothermal | 2.658 ± 0.478 | 8.323 ± 1.980 | 0.0105 ± 0.0012 | 0.0151 ± 0.0019 |
| Binary | Composition interpolation | ThermoFormer C1 + fugacity | isobaric | 0.617 ± 0.047 | 0.889 ± 0.087 | 0.0137 ± 0.0008 | 0.0201 ± 0.0011 |
| Binary | Composition-edge extrapolation | NRTL | isothermal | 1.213 | 4.476 | 0.0076 | 0.0197 |
| Binary | Composition-edge extrapolation | NRTL | isobaric | 6.871 | 26.233 | 0.0341 | 0.1025 |
| Binary | Composition-edge extrapolation | Wilson | isothermal | 1.300 | 4.799 | 0.0069 | 0.0190 |
| Binary | Composition-edge extrapolation | Wilson | isobaric | 12.566 | 51.731 | 0.0292 | 0.0809 |
| Binary | Composition-edge extrapolation | UNIQUAC | isothermal | 1.359 | 4.609 | 0.0083 | 0.0215 |
| Binary | Composition-edge extrapolation | UNIQUAC | isobaric | 1.338 | 9.638 | 0.0117 | 0.0286 |
| Binary | Composition-edge extrapolation | ThermoFormer C1 + fugacity | isothermal | 2.760 ± 0.384 | 7.056 ± 1.596 | 0.0070 ± 0.0007 | 0.0152 ± 0.0011 |
| Binary | Composition-edge extrapolation | ThermoFormer C1 + fugacity | isobaric | 0.988 ± 0.126 | 1.424 ± 0.147 | 0.0106 ± 0.0006 | 0.0232 ± 0.0008 |
| Binary | Low-temperature extrapolation | NRTL | isothermal | 3.307 | 11.970 | 0.0184 | 0.0495 |
| Binary | Low-temperature extrapolation | NRTL | isobaric | 7.094 | 32.717 | 0.0231 | 0.0877 |
| Binary | Low-temperature extrapolation | Wilson | isothermal | 3.228 | 11.146 | 0.0184 | 0.0500 |
| Binary | Low-temperature extrapolation | Wilson | isobaric | 8.366 | 42.781 | 0.0202 | 0.0687 |
| Binary | Low-temperature extrapolation | UNIQUAC | isothermal | 1.191 | 2.347 | 0.0094 | 0.0130 |
| Binary | Low-temperature extrapolation | UNIQUAC | isobaric | 0.487 | 0.778 | 0.0076 | 0.0118 |
| Binary | Low-temperature extrapolation | ThermoFormer C1 + fugacity | isothermal | 1.965 ± 0.496 | 3.751 ± 1.252 | 0.0152 ± 0.0012 | 0.0221 ± 0.0017 |
| Binary | Low-temperature extrapolation | ThermoFormer C1 + fugacity | isobaric | 1.033 ± 0.117 | 1.753 ± 0.283 | 0.0086 ± 0.0005 | 0.0202 ± 0.0027 |
| Binary | High-temperature extrapolation | NRTL | isothermal | 7.079 | 16.708 | 0.0166 | 0.0448 |
| Binary | High-temperature extrapolation | NRTL | isobaric | 8.678 | 27.874 | 0.0552 | 0.1223 |
| Binary | High-temperature extrapolation | Wilson | isothermal | 7.161 | 17.099 | 0.0165 | 0.0454 |
| Binary | High-temperature extrapolation | Wilson | isobaric | 9.002 | 29.168 | 0.0476 | 0.0976 |
| Binary | High-temperature extrapolation | UNIQUAC | isothermal | 4.113 | 9.102 | 0.0103 | 0.0138 |
| Binary | High-temperature extrapolation | UNIQUAC | isobaric | 1.902 | 5.033 | 0.0264 | 0.0485 |
| Binary | High-temperature extrapolation | ThermoFormer C1 + fugacity | isothermal | 8.560 ± 0.833 | 19.142 ± 3.026 | 0.0138 ± 0.0009 | 0.0209 ± 0.0015 |
| Binary | High-temperature extrapolation | ThermoFormer C1 + fugacity | isobaric | 1.199 ± 0.080 | 2.061 ± 0.161 | 0.0188 ± 0.0014 | 0.0315 ± 0.0020 |
| Binary | Low-pressure extrapolation | NRTL | isothermal | 0.964 | 3.005 | 0.0134 | 0.0365 |
| Binary | Low-pressure extrapolation | NRTL | isobaric | 4.441 | 24.240 | 0.0238 | 0.0564 |
| Binary | Low-pressure extrapolation | Wilson | isothermal | 0.889 | 2.658 | 0.0130 | 0.0326 |
| Binary | Low-pressure extrapolation | Wilson | isobaric | 11.143 | 44.576 | 0.0461 | 0.1393 |
| Binary | Low-pressure extrapolation | UNIQUAC | isothermal | 0.623 | 0.835 | 0.0121 | 0.0259 |
| Binary | Low-pressure extrapolation | UNIQUAC | isobaric | 0.782 | 1.171 | 0.0152 | 0.0234 |
| Binary | Low-pressure extrapolation | ThermoFormer C1 + fugacity | isothermal | 2.050 ± 0.435 | 5.302 ± 0.933 | 0.0156 ± 0.0040 | 0.0256 ± 0.0068 |
| Binary | Low-pressure extrapolation | ThermoFormer C1 + fugacity | isobaric | 0.916 ± 0.164 | 1.357 ± 0.372 | 0.0187 ± 0.0033 | 0.0285 ± 0.0053 |
| Binary | High-pressure extrapolation | NRTL | isothermal | 4.698 | 11.816 | 0.0076 | 0.0134 |
| Binary | High-pressure extrapolation | NRTL | isobaric | 10.266 | 33.356 | 0.0711 | 0.1688 |
| Binary | High-pressure extrapolation | Wilson | isothermal | 5.358 | 12.970 | 0.0080 | 0.0150 |
| Binary | High-pressure extrapolation | Wilson | isobaric | 9.522 | 31.980 | 0.0680 | 0.1601 |
| Binary | High-pressure extrapolation | UNIQUAC | isothermal | 3.331 | 7.723 | 0.0106 | 0.0159 |
| Binary | High-pressure extrapolation | UNIQUAC | isobaric | 1.013 | 1.416 | 0.0211 | 0.0298 |
| Binary | High-pressure extrapolation | ThermoFormer C1 + fugacity | isothermal | 7.313 ± 1.665 | 15.967 ± 3.623 | 0.0119 ± 0.0032 | 0.0215 ± 0.0068 |
| Binary | High-pressure extrapolation | ThermoFormer C1 + fugacity | isobaric | 1.324 ± 0.148 | 1.942 ± 0.207 | 0.0221 ± 0.0064 | 0.0318 ± 0.0069 |
| Ternary | Composition interpolation | NRTL | isothermal | 0.711 ± 0.025 | 1.135 ± 0.059 | 0.0106 ± 0.0005 | 0.0186 ± 0.0010 |
| Ternary | Composition interpolation | NRTL | isobaric | 9.688 ± 0.145 | 39.351 ± 0.565 | 0.0925 ± 0.0003 | 0.1426 ± 0.0002 |
| Ternary | Composition interpolation | Wilson | isothermal | 0.717 ± 0.056 | 1.241 ± 0.157 | 0.0102 ± 0.0004 | 0.0177 ± 0.0008 |
| Ternary | Composition interpolation | Wilson | isobaric | 7.389 ± 1.735 | 32.819 ± 6.448 | 0.0852 ± 0.0020 | 0.1316 ± 0.0038 |
| Ternary | Composition interpolation | UNIQUAC | isothermal | N/A | N/A | N/A | N/A |
| Ternary | Composition interpolation | UNIQUAC | isobaric | 1.188 ± 0.021 | 2.077 ± 0.028 | 0.0648 ± 0.0009 | 0.1177 ± 0.0010 |
| Ternary | Composition interpolation | ThermoFormer C1 + fugacity | isothermal | 0.754 ± 0.119 | 1.216 ± 0.200 | 0.0102 ± 0.0007 | 0.0149 ± 0.0011 |
| Ternary | Composition interpolation | ThermoFormer C1 + fugacity | isobaric | 0.641 ± 0.052 | 0.939 ± 0.084 | 0.0301 ± 0.0011 | 0.0633 ± 0.0013 |
| Ternary | Composition-edge extrapolation | NRTL | isothermal | 0.775 | 1.465 | 0.0101 | 0.0196 |
| Ternary | Composition-edge extrapolation | NRTL | isobaric | 2.894 | 5.629 | 0.0847 | 0.1432 |
| Ternary | Composition-edge extrapolation | Wilson | isothermal | 0.785 | 1.427 | 0.0092 | 0.0186 |
| Ternary | Composition-edge extrapolation | Wilson | isobaric | 4.346 | 11.059 | 0.0819 | 0.1351 |
| Ternary | Composition-edge extrapolation | UNIQUAC | isothermal | N/A | N/A | N/A | N/A |
| Ternary | Composition-edge extrapolation | UNIQUAC | isobaric | 1.516 | 2.352 | 0.0557 | 0.0993 |
| Ternary | Composition-edge extrapolation | ThermoFormer C1 + fugacity | isothermal | 1.006 ± 0.112 | 1.416 ± 0.136 | 0.0102 ± 0.0016 | 0.0148 ± 0.0019 |
| Ternary | Composition-edge extrapolation | ThermoFormer C1 + fugacity | isobaric | 1.113 ± 0.080 | 1.757 ± 0.110 | 0.0325 ± 0.0004 | 0.0685 ± 0.0008 |
| Ternary | Low-temperature extrapolation | NRTL | isothermal | 0.271 | 0.356 | 0.0099 | 0.0190 |
| Ternary | Low-temperature extrapolation | NRTL | isobaric | 7.685 | 23.772 | 0.0772 | 0.1345 |
| Ternary | Low-temperature extrapolation | Wilson | isothermal | 0.274 | 0.360 | 0.0100 | 0.0190 |
| Ternary | Low-temperature extrapolation | Wilson | isobaric | 9.245 | 30.587 | 0.0749 | 0.1303 |
| Ternary | Low-temperature extrapolation | UNIQUAC | isothermal | N/A | N/A | N/A | N/A |
| Ternary | Low-temperature extrapolation | UNIQUAC | isobaric | 0.925 | 1.250 | 0.0481 | 0.0776 |
| Ternary | Low-temperature extrapolation | ThermoFormer C1 + fugacity | isothermal | 1.022 ± 0.233 | 1.398 ± 0.336 | 0.0126 ± 0.0012 | 0.0194 ± 0.0017 |
| Ternary | Low-temperature extrapolation | ThermoFormer C1 + fugacity | isobaric | 0.827 ± 0.114 | 1.157 ± 0.181 | 0.0234 ± 0.0014 | 0.0407 ± 0.0025 |
| Ternary | High-temperature extrapolation | NRTL | isothermal | 0.557 | 0.913 | 0.0055 | 0.0082 |
| Ternary | High-temperature extrapolation | NRTL | isobaric | 3.229 | 6.372 | 0.0943 | 0.1486 |
| Ternary | High-temperature extrapolation | Wilson | isothermal | 0.671 | 1.086 | 0.0058 | 0.0085 |
| Ternary | High-temperature extrapolation | Wilson | isobaric | 4.643 | 12.358 | 0.0879 | 0.1369 |
| Ternary | High-temperature extrapolation | UNIQUAC | isothermal | N/A | N/A | N/A | N/A |
| Ternary | High-temperature extrapolation | UNIQUAC | isobaric | 1.973 | 2.764 | 0.0681 | 0.1131 |
| Ternary | High-temperature extrapolation | ThermoFormer C1 + fugacity | isothermal | 1.670 ± 0.619 | 2.057 ± 0.676 | 0.0070 ± 0.0006 | 0.0102 ± 0.0011 |
| Ternary | High-temperature extrapolation | ThermoFormer C1 + fugacity | isobaric | 1.309 ± 0.075 | 1.823 ± 0.082 | 0.0351 ± 0.0016 | 0.0638 ± 0.0011 |
| Ternary | Low-pressure extrapolation | NRTL | isothermal | 0.767 | 1.706 | 0.0154 | 0.0343 |
| Ternary | Low-pressure extrapolation | Wilson | isothermal | 0.778 | 1.780 | 0.0137 | 0.0288 |
| Ternary | Low-pressure extrapolation | UNIQUAC | isothermal | N/A | N/A | N/A | N/A |
| Ternary | Low-pressure extrapolation | ThermoFormer C1 + fugacity | isothermal | 0.882 ± 0.160 | 1.356 ± 0.385 | 0.0169 ± 0.0018 | 0.0256 ± 0.0028 |
| Ternary | High-pressure extrapolation | NRTL | isothermal | 1.055 | 1.657 | 0.0075 | 0.0116 |
| Ternary | High-pressure extrapolation | Wilson | isothermal | 1.136 | 1.673 | 0.0066 | 0.0107 |
| Ternary | High-pressure extrapolation | UNIQUAC | isothermal | N/A | N/A | N/A | N/A |
| Ternary | High-pressure extrapolation | ThermoFormer C1 + fugacity | isothermal | 2.299 ± 0.478 | 2.831 ± 0.639 | 0.0093 ± 0.0014 | 0.0138 ± 0.0020 |

## Interpretation boundary

These are within-system state-generalization baselines. They do not establish predictive performance for an unseen chemical system. Each ordered molecular-pair parameter is shared wherever that pair occurs, including binary and ternary training rows. UNIQUAC coverage is lower when standard UNIFAC-derived molecular size parameters are unavailable; missing systems remain failures rather than ideal substitutions.

## Reproducibility

Machine-readable summary: `experiments/vle/comparison/reference_evaluations/thermodynamic_models/metrics_summary.csv`.
