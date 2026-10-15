# Research repository architecture

The repository follows the scientific flow from molecular data through a registered
training protocol to model checkpoints, equilibrium predictions, diagnostics, and
process-design results.

| Directory | Role |
|---|---|
| configs | Model, training, split, and experiment definitions |
| datasets | Experimental records, molecular features, thermodynamic references, fixed splits |
| src/thermoformer | Feature encoders, VLE/LLE models, thermodynamic solvers, training, evaluation |
| scripts | Data, training, analysis, and experiment command-line entry points |
| models | Validation-selected checkpoints and checkpoint registry |
| experiments | Final scientific outputs and section-level navigation |
| results | Summary tables and result indexes |
| ThermoAgent | Deterministic separation-design calculations and DWSIM examples |
| Web/ThermoFormer-web | API, language-model orchestration, numerical adapters, browser interface |
| docs | Installation, scientific architecture, workflows, and attribution |
| tests | Scientific and interface validation |

`configs/catalog.json` declares the available studies. Use
`python scripts/run_experiments.py list` and `show <experiment-id>` to inspect a
study before running it. Numerical identities are recorded by data/split hashes,
configuration, checkpoint, and random seed. The same scientific input may support
more than one paper panel; the paper index links those panels to a canonical path.

Directories such as `training_records/v1/` hold the registered final five-seed
scientific outputs for that protocol. A stage history or a per-seed prediction is
part of the reproducibility evidence, including when it is needed for a staged
optimization ablation. Unsupported parameter combinations must remain explicit.
