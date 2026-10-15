# S8 agent reliability artifacts

This directory releases the reliability protocol and records used for the ThermoFormer agent
evaluation described in the paper/SI. The final development batch is
[`results/reliability-20260926-v3/`](results/reliability-20260926-v3/); v1 and v2 are retained in
[`results/historical/`](results/historical/) as development history.

The v3 batch contains 72 real DeepSeek requests: 15 equivalent requests and 9 challenge requests
for each of binary distillation, extractive distillation, and crossflow extraction, with three
repeats. It records 45/45 complete valid-task pipelines, 27/27 invalid-task blocks, and 12/27
LLM clarification decisions. The structured reports contain the raw runs, numerical evidence,
source snapshots, hashes, and audit files; they do not constitute an open-ended guarantee about
unseen prompts.

The source runners and task definitions are collected in
[`scripts/benchmarks/paper_agent/`](../../../scripts/benchmarks/paper_agent/). The production
agent and deterministic thermodynamic boundary remain under
[`Web/ThermoFormer-web/backend/paper_agent/`](../../../Web/ThermoFormer-web/backend/paper_agent/)
and [`Web/ThermoFormer-web/backend/thermo_engine/`](../../../Web/ThermoFormer-web/backend/thermo_engine/).

## Reproduction notes

The archived records were generated in the source worktree under `D:\VLE` with the frozen
protocol, source hashes, and configured model endpoint. Re-running the live benchmark requires
the corresponding API configuration and dependencies; credentials must remain in the local
environment and must never be committed. Use the release runner only after checking its paths and
environment, then audit the resulting batch with `audit_reliability.py`.

The final result report explicitly separates fresh protocol executions from cached, hash-bound
replays. Numerical values must continue to come from `thermo_engine` and pass its validation
boundary.
