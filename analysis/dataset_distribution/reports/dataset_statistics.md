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

## Ternary-to-binary subsystem coverage

| known_binary_subsystems | ternary_systems | percentage |
| --- | --- | --- |
| 3 | 30 | 23.81 |
| 2 | 22 | 17.46 |
| 1 | 69 | 54.76 |
| 0 | 5 | 3.968 |
