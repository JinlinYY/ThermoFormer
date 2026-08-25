# Legacy code inventory

This directory contains preserved programs that are not part of the supported
ThermoFormer workflow.

| Directory | Contents | Active replacement |
|---|---|---|
| `data_preparation/` | One-time acquisition, workbook formatting, consistency checking, validation, and repair programs used before the English release dataset was frozen | `dataset/*.xlsx`, `scripts/audit_dataset.py`, and `src/data.py` |
| `reporting/` | Report generator for an earlier model and its command-line entry point | `scripts/build_c1_generalization_report.py` and `scripts/build_c1_ablation_report.py` |
| `diagnostics/` | One-off solver-iteration study | Formal evaluation through `src.thermoformer.evaluation` and `src/evaluation/__init__.py` |
| `tests/` | Tests coupled to archived report-generation code | Active tests under `tests/` |

Historical data-preparation programs preserve original workbook field names and
literal paths because translating those values would alter their behavior. The
archive directory names and inventory are English, and none of these programs is
imported by active code.
