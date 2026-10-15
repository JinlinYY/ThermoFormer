# Common saturation-pressure results

Final data for SI S7.3 and Table S7. The column configuration is identical across
the comparisons; ThermoFormer weights and UNIFAC parameters are frozen.

| Saturation-pressure reference | Activity model | Ester purity (mol%) | Ester recovery (%) |
|---|---|---:|---:|
| Original backend | UNIFAC | 26.4519 | 26.0531 |
| Original backend | ThermoFormer | 99.5086 | 98.0085 |
| Common A (Li 2013) | UNIFAC | 99.2187 | 97.7229 |
| Common A (Li 2013) | ThermoFormer | 9.9563 | 9.8062 |
| Common B (Huang 2015) | UNIFAC | 99.9838 | 98.4765 |
| Common B (Huang 2015) | ThermoFormer | 43.6897 | 43.0311 |

Exact values, VLE errors, targets, and acceptance checks are in `summary.csv`,
`summary.json`, and the four reference/model subdirectories. The ranking reverses
when a common external pressure reference is used. The original process-level
difference therefore cannot be attributed to the activity-coefficient model alone.
At fixed distillate flow, recovery and purity are proportional and are not
independent pieces of evidence.

Reference A is extrapolated above 384 K, including all 17 mixture bubble states.
Reference B's validation range is unverified. The source table and units for
reference A remain subject to independent checking against the original full text.
The column trajectories extend beyond the measured mixture coverage. These
calculations diagnose coupled gamma/Psat sensitivity; they do not validate a
physical operating column or demonstrate the superiority of an isolated model branch.

Both initializations reach the same accepted final column within the recorded
tolerances. Direct bubble and material-balance checks are stored with each result.
Numerical continuation profiles are solver evidence for the final column, not
alternative process-design claims.

| File | Contents |
|---|---|
| `PROTOCOL.md` | Conditions, equations, reference sources, acceptance criteria |
| `pure_pressure_checks.json` | Pure-component measurements, curves, coefficients, versions |
| `fixed_state_decomposition.json` | Activity/pressure ratios at fixed composition and temperature |
| `sources/` | Source measurement table with units |
| `li2013_*`, `huang2015_*` | 17-state predictions, column profiles, validation |
| `figures/` | Saturation-pressure, VLE, and column comparison plots |

From the repository root, set `PYTHONPATH` to `Web/ThermoFormer-web/backend` and run
`python -m thermo_engine.paper_common_psat --output outputs/common_psat` for fresh
calculations. Use the scientific environment plus the agent dependencies. Plot the
distributed final values with `python scripts/reproduce/plot_paper_common_psat.py`.
