# Demonstration and expected output

## System requirements

The scientific reference environment uses Python 3.9. The deterministic process
demonstration requires only NumPy and SciPy, as specified by
`ThermoAgent/requirements.txt`, and runs on a CPU. Neural inference and training
also need PyTorch, molecular features, and the registered model weights. GPU
training requires a compatible PyTorch/CUDA installation. The optional browser
workbench uses a separate Python 3.11+ environment, Node.js, and pnpm; see its README.
DWSIM export additionally requires Windows, DWSIM Automation, and pythonnet.

The CPU demonstration and three fresh ThermoFormer case evaluations were tested
on Windows with Python 3.9.25, NumPy 1.26.4, SciPy 1.13.1, and PyTorch 2.6.0.
The agent record checks used Pydantic 2.12.4 and httpx 0.28.1. Reproducing the
original UNIFAC calculations requires the recorded `thermo==0.6.1` dependency.
Other operating systems and a completely new installation are not certified by
this reference-environment check.

## Install and run the CPU example

From the repository root in a Python environment:

```bash
python -m pip install -r ThermoAgent/requirements.txt
python ThermoAgent/reproduce.py --output outputs/process_demo
```

This demonstration reconstructs process calculations from the bundled equilibrium
states and verifies them against the released records. It does not perform neural
inference or require API credentials. The reference run took approximately one second;
installation time depends on package availability and network access.

The JSON summary must report:

| Case | Expected checks |
|---|---|
| binary | 16 equilibrium states, 6 design comparisons, 234 reflux calculations |
| extractive | 17 equilibrium states, 3 column configurations, 548 stage states |
| extraction | 12 experimental tie lines, 24 fixed-solvent cascades, 66 allocation cases, 132 single-stage cases, 4 interpolation checks |

`outputs/process_demo/` contains numerical result tables and `verification.json`.
The extractive case retains the reported experimental-coverage limitation.

## Fresh model evaluation

Retrieve Git LFS assets and install the scientific environment from `environment.yml`.
Then run:

```bash
python ThermoAgent/inference.py --case binary_distillation --model thermoformer --output outputs/inference
python ThermoAgent/inference.py --case extractive_distillation --model thermoformer --output outputs/inference
python ThermoAgent/lle_inference.py --model thermoformer --output outputs/inference
```

The first two commands compare new bubble-point calculations with the released
16-state and 17-state records. The third propagates three new liquid-liquid
equilibrium calculations for the selected extraction design. Successful commands
explicitly report agreement with the stored values; missing or mismatched weights
are errors. See `ThermoAgent/readme.md` for complete column and extraction scans.

## Offline agent evaluation

After installing the agent dependencies described in the S8 guide, run:

```bash
python scripts/benchmarks/paper_agent/verify_results.py
```

The output must include `passed: true`, 72 recorded initial requests, 3 fresh
numerical executions, 42 cached numerical executions, and 27 invalid requests
blocked. Recovery/evidence checks cover 27 recoveries and 36 evidence decisions.
Provider-reported median token costs are 2750 for recovery and 508 for decisions.
This command verifies existing records without making paid API calls.

## Complete experiments

Use `python scripts/run_experiments.py list` to discover protocols, and consult
`docs/results/article_experiment_index.md` for methods, source data, scripts, and
result locations. Reproducing training means running the registered five-seed
protocols; verifying released summaries alone is not a substitute for that step.
