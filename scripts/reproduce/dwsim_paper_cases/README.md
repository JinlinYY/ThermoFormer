# Paper-aligned DWSIM generator sources

These scripts are the source-tree generators for the n-heptane/n-nonane S7 DWSIM artifacts. They
are preserved with the curated `.dwxmz` export so a reader can inspect the generation logic and
provenance. They require Windows, a local DWSIM Automation API, `pythonnet`, and the supporting
source data described in the script comments.

The byte-preserved flow sheet is
[`ThermoAgent/cases/dwsim_exports/flowsheets/n_heptane_n_nonane_binary_column_x0p466.dwxmz`](../../../ThermoAgent/cases/dwsim_exports/flowsheets/n_heptane_n_nonane_binary_column_x0p466.dwxmz).
Its metadata and checksum are kept next to the archive. A DWSIM recalculation is required before
using any result; the repository does not claim convergence from the presence of a `.dwxmz` file.

The generator files retain their original source-tree imports and are intended as provenance. For
the maintained bridge and general-purpose examples, use `Web/ThermoFormer-web/backend/scripts/dwsim/`
and [`docs/guides/dwsim/`](../../../docs/guides/dwsim/).
