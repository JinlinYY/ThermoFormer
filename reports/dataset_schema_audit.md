# VLE dataset schema audit

This audit was generated from the two workbooks themselves. The source files were opened read-only and were not modified.

## binary_vle_english.xlsx

- Absolute path: `D:\VLE\VLE\dataset\binary_vle_english.xlsx`
- Format: `.xlsx`; size: 1,398,278 bytes
- SHA-256: `d122177fe42b5b41ca2e782cc77b3e6a7a0ebf922bb0e589f18edde622bf3efc`
- Sheets: 2; detected VLE sheet: `binary_vle_data`
- Actual system order: 2 components, inferred from `smiles1...smiles2` and composition columns
- Main-table rows: 23,061; columns: 13
- Exact raw duplicate rows: 0

### Sheet inventory

| name | state | rows_including_header | columns | formula_cells | merged_ranges | hidden_rows | hidden_columns | data_validations | tables |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| binary_vle_data | visible | 23062 | 13 | 0 | 0 | 0 | 0 | 0 | 0 |
| data_dictionary | visible | 14 | 3 | 0 | 0 | 0 | 0 | 0 | 1 |

### Main-table fields

| field | dtype | missing | missing_rate_pct | description | unit_or_codes |
| --- | --- | --- | --- | --- | --- |
| component_1_original_name | object | 0 | 0 | Original source name of component 1; retained without unverified translation | text |
| component_1_formula | object | 0 | 0 | Molecular formula of component 1 | text |
| smiles1 | object | 85 | 0.3686 | SMILES representation of component 1 | text |
| component_2_original_name | object | 0 | 0 | Original source name of component 2; retained without unverified translation | text |
| component_2_formula | object | 0 | 0 | Molecular formula of component 2 | text |
| smiles2 | object | 702 | 3.044 | SMILES representation of component 2 | text |
| quality_check_1 | int64 | 0 | 0 | First thermodynamic consistency check | 1=passed; 0=failed; -1=not evaluated |
| quality_check_2 | int64 | 0 | 0 | Second thermodynamic consistency check | 1=passed; 0=failed; -1=not evaluated |
| pressure_mmhg | float64 | 0 | 0 | Experimental equilibrium pressure | mmHg |
| temperature_c | float64 | 0 | 0 | Experimental equilibrium temperature | degree Celsius |
| x1 | float64 | 0 | 0 | Liquid-phase mole fraction of component 1 | mol/mol |
| y1 | float64 | 0 | 0 | Vapor-phase mole fraction of component 1 | mol/mol |
| doi | object | 0 | 0 | Digital Object Identifier of the source publication | text |

## ternary_vle_english.xlsx

- Absolute path: `D:\VLE\VLE\dataset\ternary_vle_english.xlsx`
- Format: `.xlsx`; size: 442,714 bytes
- SHA-256: `52fe356da44cc5e78f32b881a614ac95ea98e55002aaba464cfcf35069764c67`
- Sheets: 4; detected VLE sheet: `ternary_vle_data`
- Actual system order: 3 components, inferred from `smiles1...smiles3` and composition columns
- Main-table rows: 5,229; columns: 18
- Exact raw duplicate rows: 0

### Sheet inventory

| name | state | rows_including_header | columns | formula_cells | merged_ranges | hidden_rows | hidden_columns | data_validations | tables |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ternary_vle_data | visible | 5230 | 18 | 0 | 0 | 0 | 0 | 0 | 0 |
| system_summary | visible | 127 | 7 | 0 | 0 | 0 | 0 | 0 | 0 |
| dataset_overview | visible | 11 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| data_dictionary | visible | 19 | 3 | 0 | 0 | 0 | 0 | 0 | 1 |

### Main-table fields

| field | dtype | missing | missing_rate_pct | description | unit_or_codes |
| --- | --- | --- | --- | --- | --- |
| component_1_original_name | object | 0 | 0 | Original source name of component 1; retained without unverified translation | text |
| component_1_formula | object | 0 | 0 | Molecular formula of component 1 | text |
| smiles1 | object | 1103 | 21.09 | SMILES representation of component 1 | text |
| component_2_original_name | object | 0 | 0 | Original source name of component 2; retained without unverified translation | text |
| component_2_formula | object | 0 | 0 | Molecular formula of component 2 | text |
| smiles2 | object | 2298 | 43.95 | SMILES representation of component 2 | text |
| component_3_original_name | object | 0 | 0 | Original source name of component 3; retained without unverified translation | text |
| component_3_formula | object | 0 | 0 | Molecular formula of component 3 | text |
| smiles3 | object | 1883 | 36.01 | SMILES representation of component 3 | text |
| quality_check_1 | int64 | 0 | 0 | First thermodynamic consistency check | 1=passed; 0=failed; -1=not evaluated |
| quality_check_2 | int64 | 0 | 0 | Second thermodynamic consistency check | 1=passed; 0=failed; -1=not evaluated |
| pressure_mmhg | float64 | 0 | 0 | Experimental equilibrium pressure | mmHg |
| temperature_c | float64 | 0 | 0 | Experimental equilibrium temperature | degree Celsius |
| x1 | float64 | 0 | 0 | Liquid-phase mole fraction of component 1 | mol/mol |
| x2 | float64 | 0 | 0 | Liquid-phase mole fraction of component 2 | mol/mol |
| y1 | float64 | 0 | 0 | Vapor-phase mole fraction of component 1 | mol/mol |
| y2 | float64 | 0 | 0 | Vapor-phase mole fraction of component 2 | mol/mol |
| doi | object | 0 | 0 | Digital Object Identifier of the source publication | text |

## Unified interpretation

- Temperature is stored in degrees Celsius and converted to kelvin as `T_K = T_C + 273.15`.
- Pressure is stored in mmHg and converted with `1 mmHg = 0.133322368 kPa`.
- Binary tables store independent `x1` and `y1`; component-2 fractions are reconstructed by closure.
- Ternary tables store independent `x1`, `x2`, `y1`, and `y2`; component-3 fractions are reconstructed by closure.
- Quality codes are `1=passed`, `0=failed`, and `-1=not evaluated`; no records are silently removed in this analysis.
- DOI is the publication-level provenance field. No CAS field or explicit InChIKey field exists; InChIKeys are generated only for RDKit-parseable SMILES.
- System identity is an unordered tuple of stable component IDs, so source component order cannot split one chemical system into several identities.
