# DWSIM integration and exported flowsheets

This guide documents the optional DWSIM bridge in the ThermoFormer web workbench. The bridge builds a flowsheet through the local DWSIM Automation API and lets DWSIM perform the flash or column calculation. ThermoFormer does not invent equilibrium values and a generated file is not evidence of convergence until it passes the acceptance checks below.

## What is included

| Area | Public location |
|---|---|
| Automation wrapper and column exporters | [`Web/ThermoFormer-web/backend/thermo_engine/`](../../../Web/ThermoFormer-web/backend/thermo_engine/) |
| Request parsing and extractive-distillation orchestration | [`Web/ThermoFormer-web/backend/agent/extractive_distillation.py`](../../../Web/ThermoFormer-web/backend/agent/extractive_distillation.py) |
| Reusable DWSIM generation scripts | [`Web/ThermoFormer-web/backend/scripts/dwsim/`](../../../Web/ThermoFormer-web/backend/scripts/dwsim/) |
| Curated `.dwxmz` examples | [`ThermoAgent/cases/dwsim_exports/flowsheets/`](../../../ThermoAgent/cases/dwsim_exports/flowsheets/) |
| API and format notes | The four documents in this directory |

The repository keeps the 19 named flow examples generated for the paper workflow, including the
paper-aligned n-heptane/n-nonane binary column
(`n_heptane_n_nonane_binary_column_x0p466.dwxmz`) and its provenance JSON. The 186 timestamped
files under the working tree's `data/exports/extractive/` directory are runtime outputs and are
intentionally excluded from the release.

The exact sec-butyl alcohol/sec-butyl acetate/DMF and n-heptane/benzene/furfural flow sheets from
the SI are not distributed. Their
deterministic ThermoFormer protocols and common-Psat results are available under the S7 guide.

## Prerequisites

Run the scripts on Windows with a local DWSIM installation and `pythonnet`. Set `DWSIM_HOME` to the directory that contains `DWSIM.Automation.dll`; keep this value in a local `.env` or process environment and never commit it. DWSIM version differences can change compound keys, flash algorithms, and rigorous-column specification names.

The web backend itself remains usable without DWSIM. The Automation assembly is loaded lazily only when an export is requested. A missing installation or missing parameter coverage must be reported as an explicit failure.

## Reusable scripts

Run from the repository root after installing the web backend requirements:

```powershell
python Web/ThermoFormer-web/backend/scripts/dwsim/generate_dwsim_ipa_water.py
python Web/ThermoFormer-web/backend/scripts/dwsim/generate_binary_lle_dwsim.py
python Web/ThermoFormer-web/backend/scripts/dwsim/run_water_butanol_dwsim.py
python Web/ThermoFormer-web/backend/scripts/dwsim/generate_eac_npac_dmso_extractive_tf.py --dry-run
```

Generated files are written beneath `Web/ThermoFormer-web/backend/data/exports/`, which is ignored by Git. Open a generated file in DWSIM before using it as an engineering result.

## Acceptance checks

For every exported file:

1. Verify component names, order, and mole-fraction normalization.
2. Verify temperature is in kelvin and pressure has been converted to pascal at the DWSIM boundary.
3. Verify the selected property package has the required binary parameters; missing coverage is not replaced with zero parameters.
4. Verify all feed, product, and energy connections and both independent rigorous-column specifications.
5. Recalculate in DWSIM and check convergence, material balance, equilibrium residuals, and phase stability. A solver status by itself is insufficient.
6. For LLE or extraction, confirm that the heavy-liquid or extract flow is positive before interpreting a split.

The export path creates a structurally useful file even when DWSIM cannot solve it automatically. The extractive-distillation guide explains the manual condenser and reboiler specification step required by DWSIM builds whose Automation API does not expose those fields.

