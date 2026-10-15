# Article experiment index

Run commands from the repository root. The scientific environment is specified in
`environment.yml`; the browser workbench has a separate Python 3.11+ environment.

| Paper location | Method or experiment | Implementation / entry point | Final evidence |
|---|---|---|---|
| Methods 4.1-4.2; Fig. 1 | Task contract, source and unit checks, tools, evidence-linked reports | `Web/ThermoFormer-web/backend/paper_agent/reliability.py`, `thermo_engine/paper_reliability.py` | S8 result packages |
| Methods 4.3; SI S2 | Multiview encoding, mixture Transformer, gE/activity derivatives, VLE inversion, LLE coexistence and TPD | `src/thermoformer/features/`, `models/`, `thermodynamics/`, `lle_tp/` | Scientific tests and registered model configurations |
| Methods 4.3.5; SI S2.5, S5 | Thermodynamic-reference, equilibrium, and fugacity training stages | `src/thermoformer/training/direct_ge_pipeline.py`, `scripts/evaluate_staged_thermodynamic_optimization.py` | `experiments/vle/ablation/` |
| Section 2.1; Fig. 2; SI S7.2, Fig. S4 | n-Heptane/n-nonane binary distillation | `python ThermoAgent/reproduce.py --case binary` | `ThermoAgent/cases/binary_distillation/` |
| Section 2.1; SI S7.3, Fig. S5 | Alcohol/ester/DMF extractive distillation | `python ThermoAgent/reproduce.py --case extractive`, `ThermoAgent/solve_column.py` | `ThermoAgent/cases/extractive_distillation/` |
| SI S7.3; Table S7 | Common-Psat sensitivity | `Web/ThermoFormer-web/backend/thermo_engine/paper_common_psat.py`, `scripts/reproduce/plot_paper_common_psat.py` | `experiments/supporting_information/s7_separation_design/results/` |
| Section 2.1; SI S7.4, Fig. S6 | Furfural crossflow extraction | `python ThermoAgent/reproduce.py --case extraction`, `ThermoAgent/lle_inference.py` | `ThermoAgent/cases/crossflow_extraction/` |
| Section 2.2; Fig. 3; SI S8 | Equivalent requests, paired input gates, clarification recovery, evidence decisions, token costs | `scripts/benchmarks/paper_agent/reliability_run.py`, `main_figure_experiment.py`, `agent_publication_figure.py` | `experiments/supporting_information/s8_agent_reliability/` |
| Section 2.3; Fig. 4; SI S3, Tables S1-S3 | VLE/LLE prediction and state/composition/component generalization | `scripts/benchmarks/vle/run_prediction.py`, `run_generalization.py`; corresponding `lle/` entries | `experiments/vle/prediction/`, `generalization/`; `experiments/lle/`; `experiments/summary/` |
| Section 2.3.1; SI S4, S6; Table S4 | Eight learned baselines and thermodynamic models | `configs/vle/comparison/`, `src/thermoformer/baselines/` | `experiments/vle/comparison/` |
| Section 2.3.2; SI S5, Tables S5-S6 | Molecular, interaction, training-stage ablations and thermodynamic diagnostics | `configs/vle/ablation/`, `scripts/benchmarks/vle/run_ablation.py` | `experiments/vle/ablation/` |
| Section 2.3.2; Fig. 4 | Molecular-view and composition-dependent interaction interpretation | `scripts/benchmarks/vle/generate_interpretability.py` | `experiments/vle/interpretability/` |
| SI S1; Figs. S1-S2 | Dataset composition and subsystem coverage | `scripts/audit_dataset.py`, `scripts/data/` | `datasets/`, `experiments/data_quality/` |

## Reproduction modes

The deterministic process demonstration uses bundled equilibrium states and needs
no API key or model weights. Fresh neural evaluation requires materialized Git LFS
assets and the registered checkpoints. Live agent interaction additionally requires
the configured language-model endpoint. DWSIM exports require an external Windows
DWSIM installation and independent recalculation in that installation.

Prediction/generalization checkpoints are indexed in `models/registry.json`.
Comparison and ablation source code and final results are included; their optional
model weights and any third-party baseline resources must be obtained or trained
as specified by the corresponding protocol. Finite-grid TPD screens are not proofs
of global phase stability. A matched archived result is not a fresh inference run.
