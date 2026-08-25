# VLE dataset distribution analysis

This directory contains the reproducible, data-first audit and publication figure for the two Excel workbooks in `dataset/`. Source workbooks are opened read-only by the schema audit and are never modified.

## Reproduce

Run from the project root in the project environment:

```powershell
conda activate ggnn39
python analysis/dataset_distribution/scripts/analyze_datasets.py
python analysis/dataset_distribution/scripts/plot_dataset_overview.py
```

The fixed random seed is 42. Molecular space uses RDKit radius-2, 2,048-bit Morgan fingerprints and UMAP 0.5.6 with Jaccard distance. The 9 single-atom or very small fingerprints disconnected from the UMAP neighbour graph are retained in `molecular_space.csv` with `umap_status=disconnected`; they are not assigned misleading coordinates.

## Outputs

- `results/`: row-, system-, component-, chemical-space-, system-family-class, and binary-to-ternary coverage tables plus plotting data. `system_class_by_system.csv` lists all 826 exact systems; `system_class_statistics.csv` summarizes complete family combinations; `system_family_pair_by_system.csv` and `system_family_pair_statistics.csv` support the binary family-pair matrix; `ternary_family_triplets.csv` retains all 49 ternary family triplets.
- `reports/`: schema audit, complete statistics, scientific interpretation, visual QA, and bilingual figure captions. `Figure_dataset_overview_v3_caption.md` is the caption for the current five-panel manuscript figure.
- `figures/`: `Figure_dataset_overview_v3.*` is the current 180 × 180 mm five-panel manuscript figure in PDF/SVG/600 dpi PNG. `SI/Figure_S_ternary_family_triplets.*` contains the standalone two-dimensional triplet figure. Superseded v1 and v2 figures are retained under `figures/archive/`.
- `figures/Figure_dataset_overview_v3.source.json`: records the frozen manuscript PDF and embedded-image identities; the generated PNG and manuscript object have identical RGB pixels.
- `reports/`: the active v3 caption and manuscript text; superseded v1/v2 captions are retained under `reports/archive/`.
- `scripts/`: schema-aware parsing, identity reconciliation, statistics, molecular analysis, and plotting code.

The requested project-level schema report is also written to `reports/dataset_schema_audit.md`.
