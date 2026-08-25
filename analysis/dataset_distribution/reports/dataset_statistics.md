# Dataset statistics

| dataset | data_points | unique_systems | unique_components | points_per_system_mean | points_per_system_median | points_per_system_min | points_per_system_max | temperature_min_k | temperature_max_k | pressure_min_kpa | pressure_max_kpa | liquid_composition_min | liquid_composition_max | vapor_composition_min | vapor_composition_max | missing_value_rate | duplicate_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Binary | 23061 | 700 | 333 | 32.94 | 26 | 1 | 209 | 153.2 | 1550 | 0.009999 | 5.018e+04 | 0 | 1 | 0 | 1 | 0.002625 | 0.0003903 |
| Ternary | 5229 | 126 | 125 | 41.5 | 37 | 9 | 138 | 253.3 | 1400 | 0.009999 | 1.5e+04 | 0 | 1 | 0 | 1 | 0.05614 | 0 |

## Composition-space statistics

| dataset | liquid_closure_abs_error_max | vapor_closure_abs_error_max | abs_y1_minus_x1_median | abs_y1_minus_x1_q75 | abs_y1_minus_x1_max | liquid_simplex_interior_pct | liquid_simplex_vertex_pct | vapor_simplex_interior_pct | vapor_simplex_vertex_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Binary | 0 | 0 | 0.152 | 0.338 | 0.9972 |  |  |  |  |
| Ternary | 0 | 0 |  |  |  | 68.71 | 7.038 | 36.01 | 12.39 |

## Top 10 binary systems by data-point count

| system_label | data_points | references |
| --- | --- | --- |
| 1,1,1,2-四氟乙烷 / 二氟甲烷 | 209 | 4 |
| 氟乙烷 / 二氟甲烷 | 151 | 2 |
| 乙醇 / 水 | 149 | 7 |
| 1,1-二氟乙烷 / 丁烷 | 147 | 2 |
| 二氧化碳 / 一氧化碳 | 139 | 2 |
| 丙烷 / 二氧化碳 | 138 | 2 |
| 正庚烷 / 氮气 | 136 | 1 |
| 二氧化碳 / 氩气 | 133 | 2 |
| 丁烷 / 乙醇 | 122 | 3 |
| 1-十一醇 / 二氧化碳 | 120 | 1 |

## Top 10 binary component-family pair incidences

| family_pair | unique_systems | total_data_points | median_points_per_system |
| --- | --- | --- | --- |
| halogenated + hydrocarbon | 55 | 2548 | 40 |
| alcohol + ester | 39 | 1302 | 22 |
| halogenated + halogenated | 38 | 1929 | 40 |
| alcohol + ether | 36 | 1080 | 26.5 |
| alcohol + hydrocarbon | 34 | 1368 | 27 |
| alcohol + alcohol | 33 | 722 | 20 |
| ester + hydrocarbon | 30 | 957 | 27 |
| hydrocarbon + sulfur-containing | 30 | 676 | 18 |
| alcohol + other | 29 | 945 | 27 |
| ether + halogenated | 27 | 1021 | 33 |

## Top 10 binary system-family combinations

| system_family_class | unique_systems | system_share_pct | total_data_points | median_points_per_system |
| --- | --- | --- | --- | --- |
| halogenated + hydrocarbon | 55 | 7.857 | 2548 | 40 |
| alcohol + ester | 39 | 5.571 | 1302 | 22 |
| halogenated + halogenated | 38 | 5.429 | 1929 | 40 |
| alcohol + ether | 36 | 5.143 | 1080 | 26.5 |
| alcohol + hydrocarbon | 34 | 4.857 | 1368 | 27 |
| alcohol + alcohol | 33 | 4.714 | 722 | 20 |
| ester + hydrocarbon | 30 | 4.286 | 957 | 27 |
| hydrocarbon + sulfur-containing | 30 | 4.286 | 676 | 18 |
| alcohol + other | 29 | 4.143 | 945 | 27 |
| ether + halogenated | 27 | 3.857 | 1021 | 33 |

## Top 10 ternary systems by data-point count

| system_label | data_points | references |
| --- | --- | --- |
| 2-乙氧基乙醇 / 甲醇 / 碳酸二甲酯 | 138 | 1 |
| 环己烷 / 乙醇 / 丙酸乙酯 | 124 | 1 |
| 正己烷 / 乙醇 / 丙酸乙酯 | 120 | 1 |
| 正辛烷 / 乙醇 / 丙酸乙酯 | 120 | 1 |
| 4-甲基-2-戊酮 / 甲醇 / 碳酸二甲酯 | 110 | 1 |
| 乙基-1,1-二甲基丙基醚 / 甲醇 / 水 | 99 | 1 |
| 1-ethyl-3-methylimidazolium dicyanamide / 2-甲基-2-丙醇 / 水 | 95 | 1 |
| 乙醇 / 乙基-1,1-二甲基丙基醚 / 水 | 94 | 1 |
| 4-甲基-2-戊酮 / 2-丙醇 / 二异丙醚 | 90 | 1 |
| 4-甲基-2-戊酮 / 异辛烷 / 2-甲基-1-丙醇 | 85 | 1 |

## Top 10 ternary component-family pair incidences

| family_pair | unique_systems | total_data_points | median_points_per_system |
| --- | --- | --- | --- |
| alcohol + unresolved | 48 | 1919 | 39.5 |
| alcohol + ester | 25 | 1202 | 33 |
| alcohol + water | 24 | 1226 | 45 |
| unresolved + water | 19 | 745 | 36 |
| other + unresolved | 18 | 585 | 31.5 |
| alcohol + ketone | 16 | 857 | 48.5 |
| alcohol + other | 13 | 427 | 35 |
| alcohol + hydrocarbon | 12 | 843 | 59.5 |
| alcohol + ether | 12 | 726 | 53.5 |
| ester + unresolved | 12 | 399 | 33 |

## Top 10 ternary system-family combinations

| system_family_class | unique_systems | system_share_pct | total_data_points | median_points_per_system |
| --- | --- | --- | --- | --- |
| alcohol + unresolved + water | 12 | 9.524 | 550 | 43.5 |
| alcohol + other + unresolved | 10 | 7.937 | 368 | 36 |
| alcohol + ester + unresolved | 10 | 7.937 | 334 | 33 |
| alcohol + ketone + unresolved | 8 | 6.349 | 285 | 41 |
| alcohol + hydrocarbon + ketone | 5 | 3.968 | 320 | 64 |
| alcohol + ether + water | 4 | 3.175 | 335 | 89.5 |
| other + unresolved + water | 4 | 3.175 | 112 | 25.5 |
| amine + hydrocarbon + water | 4 | 3.175 | 79 | 19.5 |
| alcohol + ester + hydrocarbon | 3 | 2.381 | 364 | 120 |
| alcohol + aromatic + unresolved | 3 | 2.381 | 169 | 57 |

## Ternary-to-binary subsystem coverage

| known_binary_subsystems | ternary_systems | percentage |
| --- | --- | --- |
| 3 | 30 | 23.81 |
| 2 | 22 | 17.46 |
| 1 | 69 | 54.76 |
| 0 | 5 | 3.968 |
