# ThermoFormer

ThermoFormer predicts binary and ternary phase equilibria from molecular representations and thermodynamic state variables.

- **VLE:** SMILES, temperature and liquid composition to pressure and vapor composition; or SMILES, pressure and liquid composition to temperature and vapor composition.
- **LLE:** SMILES, temperature and pressure to liquid coexistence endpoints. Ternary predictions are unordered tie-line sets.
- Baseline comparison, ablation and interpretability studies apply to VLE. LLE benchmarks cover prediction, generalization and thermodynamic stability.

This release accompanies *Agent-driven separation-process design with
mixture-conditioned molecular thermodynamics*. It follows a paper-aligned
research-release layout: executable code is in `src/` and `scripts/`, inputs
and registries are in `configs/` and `datasets/`, and reported studies are
indexed under `experiments/`. The supplied Supporting Information is mapped in
[the article experiment index](docs/reproducibility/article_experiment_index.md).

## Installation

Install Git LFS before cloning to download the model weights and molecular feature arrays:

```bash
git lfs install
git clone https://github.com/JinlinYY/ThermoFormer.git
cd ThermoFormer
git lfs pull
```

```bash
conda env create -f environment.yml
conda activate ggnn39
```

## Repository organization

| Directory | Contents |
|---|---|
| `configs/` | Experiment registry, model settings and training configurations |
| `datasets/` | VLE/LLE workbooks, split assignments, molecular resources and thermodynamic labels |
| `src/thermoformer/` | Scientific models, solvers, training, evaluation and baseline adapters |
| `scripts/` | Experiment, inference, evaluation and plotting entry points |
| `models/` | Validation-selected checkpoints and required pretrained resources |
| `experiments/` | Predictions, metrics, figures and reproducibility records, organized by task and study |
| `docs/` | Method, dataset, baseline and reproduction documentation |
| `tests/` | Scientific and interface regression tests |

## Experiments

Run commands from the repository root:

```bash
python scripts/run_experiments.py list
python scripts/run_experiments.py show vle.prediction.binary
python scripts/run_experiments.py run vle.prediction.binary --seeds 0 1 2 3 4 --device cuda --run-id v2
python scripts/run_experiments.py run lle.prediction.binary_random --seeds 0 1 2 3 4 --device cuda --run-id v2
```

Use `--dry-run` to inspect a command, `--check-splits-only` to audit supported campaign splits, and `--resume` for a matching recorded execution. Use a new run identifier for a new experiment.

The principal VLE and LLE result tables and all five-seed summaries are in `experiments/summary/`. Task-specific results and figures are under `experiments/vle/` and `experiments/lle/`. Read [the experiment directory guide](docs/experiment_layout.md) for their organization.

The [constituent binary-pair coverage study](experiments/vle/ablation/binary_pair_coverage/) provides the controlled mixed-training results in Fig. 3i-l and Supplementary Table S2, together with the F01 source data in Fig. 3h,m, fixed splits, selected checkpoints and reproduction commands.

## Checkpoints and verification

`models/registry.json` identifies 50 VLE and 55 LLE final checkpoints selected using validation data. Mixed-training models are shared across their binary, ternary and joint test subsets. Baseline-specific weights are obtained separately from their cited upstream sources.

```bash
python scripts/validate_checkpoint_catalog.py --load
python scripts/verify_phase_equilibrium_results.py
python scripts/run_experiments.py verify
python -m pytest -q
```

LLE uses a two-phase prior, binary RK free-energy parameterization and a continuous parallel tie-line approximation for ternary systems. Finite-grid TPD certification is a numerical stability diagnostic, not a global proof over the continuous composition simplex. Compare metrics only when dataset identity, split protocol and evaluation targets agree.

## Paper and supporting-information map

| Manuscript or SI section | Release entry point |
|---|---|
| Main Section 2.1, SI S7 | `ThermoAgent/` and `experiments/vle/separation_design/` |
| Main Section 3, SI S3 | `experiments/vle/prediction/`, `experiments/vle/generalization/`, `experiments/lle/` |
| Main Section 3 comparison, SI S4 and S6 | `experiments/vle/comparison/`, `src/thermoformer/baselines/` |
| Main Section 3 ablations, SI S5 | `experiments/vle/ablation/`, `configs/vle/ablation/` |
| Main Section 3 interpretation, SI S2 | `experiments/vle/interpretability/`, `src/thermoformer/interpretability/` |
| SI S1 and S5 | `experiments/data_quality/`, `datasets/`, `docs/dataset.md` |
| SI S8 | `ThermoAgent/` reliability and case-study records |

The release contains deterministic numerical workflows and archived evidence
for the reported studies. API keys, private paths, local caches, and
unpublished raw working directories are excluded.
