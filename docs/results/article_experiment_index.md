# Article experiment index

This index connects the supplied manuscript and Supporting Information (SI)
to the public repository. Commands are run from the repository root after the
environment in `environment.yml` is activated.

| Paper location | Scientific question | Code and configuration | Evidence |
|---|---|---|---|
| Main Section 2.1; SI S7.2 | Binary n-heptane/n-nonane distillation | `ThermoAgent/reproduce.py --case binary` | `ThermoAgent/cases/binary_distillation/` and `experiments/vle/separation_design/` |
| Main Section 2.1; SI S7.3 | DMF-assisted extractive distillation | `ThermoAgent/reproduce.py --case extractive` | `ThermoAgent/cases/extractive_distillation/` |
| Main Section 2.1; SI S7.4 | Furfural crossflow extraction | `ThermoAgent/reproduce.py --case extraction` | `ThermoAgent/cases/crossflow_extraction/` |
| Main Section 3; SI S3 | VLE prediction and state/system generalization | `scripts/run_experiments.py` with `configs/vle/prediction/` and `configs/vle/generalization/` | `experiments/vle/prediction/` and `experiments/vle/generalization/` |
| Main Section 3; SI S3 | LLE prediction, extrapolation, and stability | `scripts/run_experiments.py` with `configs/lle/` | `experiments/lle/` |
| Main Section 3; SI S4 and S6 | Comparison with thermodynamic and learned baselines | `configs/vle/comparison/` and `scripts/run_ml_baselines_formal.py` | `experiments/vle/comparison/` |
| Main Section 3; SI S5 | Molecular, interaction, and staged-optimization ablations | `configs/vle/ablation/` and `scripts/run_*ablation*.py` | `experiments/vle/ablation/` |
| Main Section 3; SI S2 | Molecular interaction interpretation | `scripts/benchmarks/vle/generate_interpretability.py` | `experiments/vle/interpretability/` |
| SI S1 and S5 | Dataset coverage, construction, and audit | `scripts/audit_dataset.py` and `scripts/data/` | `experiments/data_quality/` and `datasets/` |
| SI S8 | Agent execution reliability and evidence review | `ThermoAgent/` case and reliability records | `ThermoAgent/tests/` and `ThermoAgent/cases/` |

## Reproduction boundaries

The three separation-design cases can be recalculated from the bundled
equilibrium states without model weights. Fresh neural-network evaluation uses
the registered checkpoints and Git LFS assets. The LLM orchestration layer and
external DWSIM installation are integration components; the numerical case
reproduction remains deterministic and does not require API credentials.

Every result directory records the dataset identity, split protocol, seed,
configuration, and artifact hashes. A missing checkpoint or unsupported
thermodynamic parameter is reported as unavailable and is never silently
replaced by a different model.
