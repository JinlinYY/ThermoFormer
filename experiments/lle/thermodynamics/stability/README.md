# Activity residuals and finite-grid TPD (same predictions)

LLE / Equilibrium and stability diagnostics

Diagnostics already produced in each LLE evaluation; index, do not train an extra experiment. Accepted roots: activity RMS ≤0.001, grid TPD ≥−0.0001 plus original separation checks. Two-phase prior and parallel-line approximation apply.

## Protocol and results

Configuration: `configs/lle/thermodynamics/stability.json`.

- [experiments/lle/training_records/v1/formal](../../training_records/v1/formal)
- [experiments/summary/LLE_results_table.md](../../../summary/LLE_results_table.md)

Inspect the command with `python scripts/run_experiments.py show lle.thermodynamics.stability`.
