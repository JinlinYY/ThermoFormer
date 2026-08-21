# VLE dataset distribution report

Reproducible analysis seed: `42`. Software: Python 3.9.25, pandas 1.5.3, RDKit 2025.03.5.

## Dataset 1 — Binary

- Data points: **23,061**
- Unique unordered systems: **700**
- Unique components: **333**
- Temperature: **153.23–1550.00 K** (-119.92–1276.85 °C)
- Pressure: **0.009999–5.018e+04 kPa**
- Reconstructed liquid/vapor component fractions: **0–1 / 0–1**
- Median points per system: **26.0**

## Dataset 2 — Ternary

- Data points: **5,229**
- Unique unordered systems: **126**
- Unique components: **125**
- Temperature: **253.27–1400.00 K** (-19.88–1126.85 °C)
- Pressure: **0.009999–1.5e+04 kPa**
- Reconstructed liquid/vapor component fractions: **0–1 / 0–1**
- Median points per system: **37.0**

## Cross-dataset relationship

- Binary-only molecules: **241**
- Ternary-only molecules: **33**
- Shared molecules: **92**
- RDKit-parseable unique molecules: **318/366**
- Molecules projected by Morgan-UMAP: **309**; disconnected fingerprint-graph vertices retained outside the 2D map: **9**
- Ternary-only identities without a resolvable structure: **33** (therefore no ternary-only point can be placed in the molecular projection)
- Ternary systems with 3/2/1/0 known binary subsystems: **30/22/69/5**

## Data-quality findings

| issue_type | rows_or_systems |
| --- | --- |
| missing_smiles | 4318 |
| thermodynamic_consistency_failed | 3860 |
| unresolved_component_identity | 48 |
| duplicate_tp_xy_state | 18 |
| component_order_variant | 15 |

Across 28,290 source rows, exact raw-row duplicates are absent, while unordered TPXY normalization identifies the duplicate states listed above. Missing SMILES are retained and resolved through a unique name–formula link when possible; identities without a unique SMILES link remain explicit fallback IDs. Quality code `-1` means not evaluated, not passed. No anomaly is automatically deleted.

Explicit zero findings: no finite composition lies outside [0, 1]; no reconstructed ternary fraction is outside [0, 1]; no T≤0 K or P≤0 record, NaN/Inf thermodynamic value, blank DOI, or RDKit parse failure for a nonblank SMILES was found. The workbooks' data dictionaries consistently define pressure in mmHg, temperature in °C and composition as mol/mol; no contradictory unit field was detected. The 18 duplicate-issue rows form 9 additional canonical TPXY states beyond the first occurrence.

For ternary rows, `x3` and `y3` are not independent workbook fields: they are reconstructed as `1-x1-x2` and `1-y1-y2`. Consequently, closure residuals are algebraically zero up to floating-point precision (maximum 0); out-of-bound reconstructed fractions are the meaningful closure-quality check.

## Scientific interpretation

1. The combined data span a broad temperature interval and about 6.7 orders of magnitude in pressure; pressure is therefore visualized logarithmically. Coverage density is highly nonuniform, so apparent global breadth should not be interpreted as uniform local support.
2. Binary compositions include 18.1% of rows near an `x1` endpoint (≤0.05 or ≥0.95); `|y1-x1|` has median 0.152, upper quartile 0.338 and maximum 0.9972. In the ternary liquid simplex, 68.7% of rows lie in the interior and 7.0% near a vertex; the corresponding vapor-simplex fractions are 36.0% and 12.4%, confirming uneven liquid and vapor coverage.
3. Morgan fingerprints resolve 318 unique molecules; 309 form the connected UMAP projection and 9 isolated fingerprints are retained but not assigned finite 2D coordinates. All 33 ternary-only identities lack a resolvable structure, so the map cannot establish the extent of ternary-exclusive chemical space; unresolved or isolated identities must not be interpreted as absent chemistry.
4. Binary-to-ternary transfer is directly supported for 30 ternary systems with all three constituent binary pairs, while systems with partial or zero pair coverage provide progressively harder compositional generalization tests.
5. Both datasets are long-tailed: 31.7% of binary and 19.0% of ternary systems contain fewer than 20 points. Sparse systems, high-pressure regions, unresolved molecular identities, and ternary simplex regions without complete binary-subsystem support are the most demanding generalization regimes.

## Reproducibility

Run from the project root:

```powershell
conda activate ggnn39
python analysis/dataset_distribution/scripts/analyze_datasets.py
python analysis/dataset_distribution/scripts/plot_dataset_overview.py
```
