# ThermoFormer

ThermoFormer predicts binary and ternary vapour–liquid and liquid–liquid phase equilibria from molecular representations and thermodynamic state variables. The repository provides model implementations, datasets, registered experiments, and separation-design examples.

## Scientific scope

The release supports VLE prediction, LLE prediction, state and composition generalization, thermodynamic consistency, baseline comparison, ablation, molecular-interaction interpretation, and the separation-design cases reported in the manuscript and Supporting Information. Numerical equilibrium values are produced by the registered ThermoFormer or thermodynamic backends; unavailable external parameters remain explicitly marked.

## Repository navigation

| I want to… | Start here |
|---|---|
| Install and run a checkpoint | [`docs/getting_started/`](docs/getting_started/) |
| Understand the model and interfaces | [`docs/architecture/`](docs/architecture/) |
| Prepare data or train/evaluate a model | [`docs/guides/`](docs/guides/) |
| Use the optional DWSIM bridge | [`docs/guides/dwsim/`](docs/guides/dwsim/) and [`ThermoAgent/cases/dwsim_exports/`](ThermoAgent/cases/dwsim_exports/) |
| Find code for a paper or SI section | [`experiments/`](experiments/) and [`docs/results/article_experiment_index.md`](docs/results/article_experiment_index.md) |
| Inspect canonical metrics and tables | [`results/`](results/) and [`experiments/summary/`](experiments/summary/) |
| Inspect configurations and registries | [`configs/`](configs/) |
| Inspect datasets and fixed splits | [`datasets/`](datasets/) |
| Run separation-design reproductions | [`ThermoAgent/`](ThermoAgent/) |
| Run the browser workbench | [`Web/ThermoFormer-web/`](Web/ThermoFormer-web/) |
| Run regression checks | [`tests/`](tests/) |
| Run a CPU demonstration with expected output | [`docs/getting_started/demo.md`](docs/getting_started/demo.md) |
| Inspect agent recovery and evidence decisions | [`experiments/supporting_information/s8_agent_reliability/`](experiments/supporting_information/s8_agent_reliability/) |

## Directory map

| Directory | Contents |
|---|---|
| `configs/` | Dataset, model, training, protocol, baseline, and checkpoint configurations |
| `datasets/` | VLE/LLE workbooks, molecular features, labels, parameters, and fixed splits |
| `src/` | Importable ThermoFormer models, data pipelines, solvers, training, evaluation, and baselines |
| `scripts/` | Training, evaluation, analysis, experiment, and visualization entry points |
| `models/` | Validation-selected checkpoints and pretrained resources |
| `experiments/` | Executable task studies plus paper-section and Supporting Information navigation |
| `results/` | Public-facing summary tables, manifests, and result navigation |
| `docs/` | Getting-started guides, architecture, workflows, references, results, contribution guidelines, and legal notes |
| `ThermoAgent/` | Deterministic separation-design case reproductions from the manuscript and SI |
| `Web/ThermoFormer-web/` | Runnable FastAPI + Next.js engineering workbench, with validated numerical tools |
| `tests/` | Scientific, interface, and repository-quality regression tests |

## Installation

```bash
git lfs install
git clone https://github.com/JinlinYY/ThermoFormer.git
cd ThermoFormer
git lfs pull
conda env create -f environment.yml
conda activate ggnn39
```

For a CPU-only environment, use `environment-cpu.yml` and follow [`docs/getting_started/installation.md`](docs/getting_started/installation.md).

## Quick start

Run commands from the repository root:

```bash
python scripts/run_experiments.py list
python scripts/run_experiments.py show vle.prediction.binary
python scripts/run_experiments.py run vle.prediction.binary --seeds 0 1 2 3 4 --device cuda --run-id v2
python scripts/run_experiments.py run lle.prediction.binary_random --seeds 0 1 2 3 4 --device cuda --run-id v2
```

Use `--dry-run` to inspect a command, `--check-splits-only` to audit registered splits, and `--resume` to continue a matching recorded execution.

## Browser workbench

Follow [`Web/ThermoFormer-web/README.md`](Web/ThermoFormer-web/README.md) to install the FastAPI and Next.js dependencies, start both services, and run the web-package checks. The backend reuses the same deterministic thermodynamic engine and validation contracts as the scientific release.

## Data and experiment contract

VLE and LLE data, molecular features, thermodynamic labels, split manifests, and provenance are versioned under `datasets/`. Configuration files under `configs/` bind each study to a dataset identity, model, protocol, seed set, and checkpoint registry. The task-organized directories under `experiments/vle/` and `experiments/lle/` remain the executable evidence paths. The paper-aligned navigation under `experiments/section_2_results/` and `experiments/supporting_information/` links each manuscript claim to those canonical paths.

## Results and verification

The public summary bundle is under `results/main_text/summary/`; the task-level evidence remains under `experiments/`. Verify checkpoints and scientific artifacts with:

```bash
python scripts/validate_checkpoint_catalog.py --load
python scripts/verify_phase_equilibrium_results.py
python scripts/run_experiments.py verify
python -m pytest -q
```

The complete article/SI mapping is recorded in [`docs/results/article_experiment_index.md`](docs/results/article_experiment_index.md). Deterministic separation-design reproduction is documented in [`ThermoAgent/readme.md`](ThermoAgent/readme.md).

## Open-source policy

Public releases exclude API keys, private paths, local caches, and unpublished working directories. Dataset measurements, baseline implementations, and pretrained resources retain their cited attribution and reuse conditions. See [`CONTRIBUTING.md`](CONTRIBUTING.md), [`CITATION.cff`](CITATION.cff), and [`LICENSE`](LICENSE).
