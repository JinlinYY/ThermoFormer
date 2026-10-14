# Experiment outputs

All result data, tables, and figures are stored under [`../../experiments/`](../../experiments/) and summarized under [`../../results/`](../../results/).

- `experiments/vle/prediction/` and `experiments/vle/generalization/`: VLE predictive and extrapolation evaluations.
- `experiments/vle/comparison/`, `experiments/vle/ablation/`, and `experiments/vle/interpretability/`: reference models, controlled experiments, and molecular analysis.
- `experiments/vle/separation_design/`: registered separation-design cases and availability records.
- `experiments/lle/`: liquid coexistence benchmarks and thermodynamic diagnostics.
- `experiments/summary/`: cross-task five-seed tables in CSV, Markdown, and LaTeX.
- `experiments/data_quality/`: data and split audits.

Final checkpoint paths are supplied by [`../../models/registry.json`](../../models/registry.json); configuration paths are supplied by [`../../configs/catalog.json`](../../configs/catalog.json). Split assignments are under [`../../datasets/splits/`](../../datasets/splits/).
