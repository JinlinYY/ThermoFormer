# Curated DWSIM flow examples

These `.dwxmz` files are named examples from the ThermoFormer separation-design workflow. They are binary DWSIM project archives, so they are kept byte-for-byte and are accompanied by [`checksums.json`](checksums.json). The files are starting points for inspection and recalculation in DWSIM, not pre-validated engineering designs.

The files cover binary VLE, ternary extractive distillation, and LLE/extraction demonstrations. Some names contain `backup` or `prev`; those are retained because they document the corresponding export variants used during the study. Runtime timestamped exports and failed diagnostic files are not included.

To generate a new file, see [`docs/guides/dwsim/`](../../../docs/guides/dwsim/) and the scripts in [`Web/ThermoFormer-web/backend/scripts/dwsim/`](../../../Web/ThermoFormer-web/backend/scripts/dwsim/). Generated outputs belong under the ignored backend `data/exports/` directory rather than this curated archive.

Before using an example, open it in the installed DWSIM version, recalculate it, and review the property-package parameters, column specifications, material balance, equilibrium residuals, and phase split. DWSIM version changes may require selecting a compatible flash algorithm or completing condenser/reboiler specifications in the GUI.

