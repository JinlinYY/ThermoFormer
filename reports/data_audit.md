# ThermoFormer data audit

This report is generated from the two English workbooks under `dataset/` using the same loader and default low-pressure/quality filters as training. The modeling set additionally applies the current requirement of at least two pure-endpoint temperatures per retained component. Counts below are observations, not inferred sample-size claims.

## Row-accounting ledger

| Workbook | Raw rows | Loaded after row filters/dedup | Duplicates removed |
|---|---:|---:|---:|
| binary_vle_english.xlsx | 23,061 | 14,704 | 7 |
| ternary_vle_english.xlsx | 5,229 | 1,535 | 0 |
| **Combined** | **28,290** | **16,239** | **7** |

Combined rejection ledger: failed quality `1,254`, missing SMILES `4,318`, invalid state/composition `0`, pressure above 500 kPa `6,472`, invalid explicit mode `0`. The pure-anchor filter then removes `5,225` rows, leaving **11,014** modeling rows.

## Modeling-set coverage

| Cardinality | Rows | Unordered systems |
|---|---:|---:|
| 2-component | 9,905 | 321 |
| 3-component | 1,109 | 26 |

- Canonical components: **138**; invalid SMILES: **0**; raw-to-canonical collisions: **0**.
- Temperature range: **253.1500–559.0100 K**; pressure range: **0.1000–498.9000 kPa**.
- Liquid mole-fraction range: **0.0000–1.0000**; vapor mole-fraction range: **0.0000–1.0000**.
- Points/system: median **26.0**, IQR **17.0–42.0**, range **3–149**.
- Systems/component: median **3.0**, IQR **2.0–7.0**, range **1–28**.
- Quality labels: `{"passed": 2098, "unverified": 8916}`; modes: `{"full_state": 138, "isobaric": 6034, "isothermal": 4842}`.
- Non-empty unique DOI strings: **209**; rows with missing DOI: **0**.

## Ternary-to-binary subsystem coverage

Coverage is computed by canonical molecular identity. Each ternary system is assigned according to how many of its three binary subsystems occur anywhere in the retained modeling set.

| Binary subsystems present | Ternary systems |
|---|---:|
| 0/3 | 2 |
| 1/3 | 2 |
| 2/3 | 7 |
| 3/3 | 15 |

The row-level mapping is saved as `reports/ternary_binary_subsystem_coverage.csv`. This dataset-wide table describes availability in the modeling corpus. Every binary-to-ternary experiment independently recomputes coverage from that seed's **actual binary training partition** before stratification and subgroup evaluation.

## Leakage and identifiability audit

- Reversed component order is canonicalized for duplicate detection and stable IDs; A–B and B–A cannot cross a system-disjoint split.
- The legacy CLI generates grouped splits in memory. Paper experiments instead use 75 versioned JSON artifacts under `splits/`; the runner refuses dataset-digest mismatch, duplicate/unknown IDs, unsafe protocol names and row overlap. The complete audit is in `reports/split_audit.md`/`.json`.
- Pure endpoints are part of mixture workbooks rather than an independent pure-property source. Main random-system experiments protect reference systems on the training side. In unseen-component experiments, moving a test component's endpoint system into training would be leakage and is prohibited; learned `P_i^sat(T)` therefore becomes a genuine molecular extrapolation.
- No experimental uncertainty columns or repeat-level variance are available in the current workbooks. Training weights reflect quality flags, not calibrated measurement uncertainty.
- There are no quaternary rows. The supported and auditable scope is binary and ternary VLE only.

## Reproducibility record

- Loaded-set SHA-256: `f8a6f4a46c92603f2497621fc2a645261a694f1fac78339dc9adcbe275ed2bce`
- Modeling-set SHA-256: `cd264320244c3c17637b61c09cda24a907d68700ba571d76240dcfb388c3272e`
- Stable component identities use RDKit canonical isomeric SMILES; split files store hashed state IDs plus the complete modeling-set digest.

Machine-readable audit details are saved in `reports/data_audit.json`.

## Raw-workbook distribution analysis

`analysis/dataset_distribution/` separately audits all **28,290 raw workbook rows** before the sequential quality, SMILES, pressure and anchor filters above. Its 23,061 binary and 5,229 ternary raw-row counts therefore must not be compared directly with the 11,014-row modeling set. The scripts, source-resolution ledger, derived CSVs, bilingual caption and publication-quality overview are reproducible in `ggnn39`; source Excel files are opened read-only and never modified.
