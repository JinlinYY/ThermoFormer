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

- `results/`: row-, system-, component-, chemical-space-, and binary-to-ternary coverage tables plus plotting data.
- `reports/`: schema audit, complete statistics, scientific interpretation, and bilingual figure caption.
- `figures/`: vector PDF/SVG and 600 dpi PNG versions of the six-panel overview.
- `scripts/`: schema-aware parsing, identity reconciliation, statistics, molecular analysis, and plotting code.

The requested project-level schema report is also written to `reports/dataset_schema_audit.md`.
