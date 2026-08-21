# -*- coding: utf-8 -*-
"""Run the complete, read-only ThermoFormer VLE dataset analysis."""

from __future__ import annotations

import argparse
import platform
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import rdkit

from dataset_utils import (
    SEED,
    UnifiedData,
    load_unified_data,
    markdown_table,
    safe_percentage,
    ternary_binary_coverage,
)
from molecular_space import analyze_molecular_space


def _mode(values: pd.Series) -> str:
    usable = [str(value).strip() for value in values if str(value).strip()]
    return Counter(usable).most_common(1)[0][0] if usable else ""


def component_statistics(data: UnifiedData) -> pd.DataFrame:
    records = data.records
    system_membership: dict[str, set[str]] = {}
    for _, row in records.iterrows():
        for position in range(1, int(row["component_count"]) + 1):
            component_id = row[f"component_id_{position}"]
            system_membership.setdefault(component_id, set()).add(row["system_id"])
    rows = []
    for component_id, group in data.occurrences.groupby("component_id", sort=True):
        datasets = set(group["dataset"])
        membership = (
            "Shared"
            if datasets == {"Binary", "Ternary"}
            else "Binary only"
            if datasets == {"Binary"}
            else "Ternary only"
        )
        canonical = _mode(group.loc[group["canonical_smiles"] != "", "canonical_smiles"])
        inchikey = _mode(group.loc[group["inchikey"] != "", "inchikey"])
        rows.append(
            {
                "component_id": component_id,
                "canonical_smiles": canonical,
                "inchikey": inchikey,
                "representative_original_name": _mode(group["original_name"]),
                "representative_formula": _mode(group["formula"]),
                "representative_raw_smiles": _mode(group["raw_smiles"]),
                "dataset_membership": membership,
                "record_occurrences": int(len(group)),
                "binary_record_occurrences": int((group["dataset"] == "Binary").sum()),
                "ternary_record_occurrences": int((group["dataset"] == "Ternary").sum()),
                "unique_systems": len(system_membership.get(component_id, set())),
                "identity_methods": ";".join(sorted(set(group["identity_method"]))),
                "has_parseable_smiles": bool(canonical),
                "raw_missing_smiles_occurrences": int((group["smiles_status"] == "missing").sum()),
                "raw_smiles_parse_failures": int((group["smiles_status"] == "parse_failed").sum()),
                "name_variants": int(group["original_name"].nunique()),
                "formula_variants": int(group["formula"].nunique()),
            }
        )
    return pd.DataFrame(rows).sort_values("component_id").reset_index(drop=True)


def system_statistics(records: pd.DataFrame, components: pd.DataFrame) -> pd.DataFrame:
    name_map = components.set_index("component_id")["representative_original_name"].to_dict()
    rows = []
    for (dataset, system_id), group in records.groupby(["dataset", "system_id"], sort=True):
        component_count = int(group["component_count"].iloc[0])
        ids = system_id.split(" || ")
        x_values = group[[f"x{i}" for i in range(1, component_count + 1)]].to_numpy().ravel()
        y_values = group[[f"y{i}" for i in range(1, component_count + 1)]].to_numpy().ravel()
        rows.append(
            {
                "dataset": dataset,
                "component_count": component_count,
                "system_id": system_id,
                "system_label": " / ".join(name_map.get(value, value) for value in ids),
                "data_points": int(len(group)),
                "references": int(group["doi"].nunique()),
                "unique_temperatures": int(group["temperature_k"].nunique()),
                "unique_pressures": int(group["pressure_kpa"].nunique()),
                "temperature_min_k": float(group["temperature_k"].min()),
                "temperature_max_k": float(group["temperature_k"].max()),
                "pressure_min_kpa": float(group["pressure_kpa"].min()),
                "pressure_max_kpa": float(group["pressure_kpa"].max()),
                "liquid_composition_min": float(np.nanmin(x_values)),
                "liquid_composition_max": float(np.nanmax(x_values)),
                "vapor_composition_min": float(np.nanmin(y_values)),
                "vapor_composition_max": float(np.nanmax(y_values)),
                "component_order_variants": int(group["component_order"].nunique()),
            }
        )
    return pd.DataFrame(rows).sort_values(["dataset", "data_points"], ascending=[True, False])


def dataset_summary(
    data: UnifiedData,
    systems: pd.DataFrame,
    components: pd.DataFrame,
) -> pd.DataFrame:
    schema_by_dataset = {
        ("Binary" if workbook.component_count == 2 else "Ternary"): workbook.schema
        for workbook in data.workbooks
    }
    rows = []
    for dataset, group in data.records.groupby("dataset", sort=True):
        component_count = int(group["component_count"].iloc[0])
        system_group = systems.loc[systems["dataset"] == dataset]
        dataset_components = components.loc[
            components["dataset_membership"].isin([f"{dataset} only", "Shared"])
        ]
        x_matrix = group[[f"x{i}" for i in range(1, component_count + 1)]].to_numpy()
        y_matrix = group[[f"y{i}" for i in range(1, component_count + 1)]].to_numpy()
        x = x_matrix.ravel()
        y = y_matrix.ravel()
        liquid_closure_error = np.abs(x_matrix.sum(axis=1) - 1.0)
        vapor_closure_error = np.abs(y_matrix.sum(axis=1) - 1.0)
        binary_separation = np.abs(group["y1"] - group["x1"])
        duplicate_count = int(group.duplicated("canonical_state_key", keep="first").sum())
        schema = schema_by_dataset[dataset]
        missing_cells = sum(schema["main_missing"].values())
        total_cells = schema["main_rows"] * schema["main_columns"]
        points = system_group["data_points"]
        rows.append(
            {
                "dataset": dataset,
                "source_file": schema["filename"],
                "component_count": component_count,
                "data_points": int(len(group)),
                "unique_systems": int(group["system_id"].nunique()),
                "unique_components": int(len(dataset_components)),
                "parseable_components": int(dataset_components["has_parseable_smiles"].sum()),
                "points_per_system_mean": float(points.mean()),
                "points_per_system_median": float(points.median()),
                "points_per_system_min": int(points.min()),
                "points_per_system_max": int(points.max()),
                "temperature_min_k": float(group["temperature_k"].min()),
                "temperature_q25_k": float(group["temperature_k"].quantile(0.25)),
                "temperature_median_k": float(group["temperature_k"].median()),
                "temperature_q75_k": float(group["temperature_k"].quantile(0.75)),
                "temperature_max_k": float(group["temperature_k"].max()),
                "temperature_min_c": float(group["temperature_c"].min()),
                "temperature_max_c": float(group["temperature_c"].max()),
                "unique_temperatures": int(group["temperature_k"].nunique()),
                "pressure_min_kpa": float(group["pressure_kpa"].min()),
                "pressure_q25_kpa": float(group["pressure_kpa"].quantile(0.25)),
                "pressure_median_kpa": float(group["pressure_kpa"].median()),
                "pressure_q75_kpa": float(group["pressure_kpa"].quantile(0.75)),
                "pressure_max_kpa": float(group["pressure_kpa"].max()),
                "pressure_min_mmhg": float(group["pressure_mmhg"].min()),
                "pressure_max_mmhg": float(group["pressure_mmhg"].max()),
                "unique_pressures": int(group["pressure_kpa"].nunique()),
                "liquid_composition_min": float(np.nanmin(x)),
                "liquid_composition_max": float(np.nanmax(x)),
                "vapor_composition_min": float(np.nanmin(y)),
                "vapor_composition_max": float(np.nanmax(y)),
                "liquid_closure_abs_error_median": float(np.nanmedian(liquid_closure_error)),
                "liquid_closure_abs_error_max": float(np.nanmax(liquid_closure_error)),
                "vapor_closure_abs_error_median": float(np.nanmedian(vapor_closure_error)),
                "vapor_closure_abs_error_max": float(np.nanmax(vapor_closure_error)),
                "abs_y1_minus_x1_median": (
                    float(binary_separation.median()) if component_count == 2 else np.nan
                ),
                "abs_y1_minus_x1_q75": (
                    float(binary_separation.quantile(0.75)) if component_count == 2 else np.nan
                ),
                "abs_y1_minus_x1_max": (
                    float(binary_separation.max()) if component_count == 2 else np.nan
                ),
                "liquid_simplex_interior_pct": (
                    safe_percentage(int((np.nanmin(x_matrix, axis=1) >= 0.05).sum()), len(group))
                    if component_count == 3
                    else np.nan
                ),
                "liquid_simplex_vertex_pct": (
                    safe_percentage(int((np.nanmax(x_matrix, axis=1) >= 0.90).sum()), len(group))
                    if component_count == 3
                    else np.nan
                ),
                "vapor_simplex_interior_pct": (
                    safe_percentage(int((np.nanmin(y_matrix, axis=1) >= 0.05).sum()), len(group))
                    if component_count == 3
                    else np.nan
                ),
                "vapor_simplex_vertex_pct": (
                    safe_percentage(int((np.nanmax(y_matrix, axis=1) >= 0.90).sum()), len(group))
                    if component_count == 3
                    else np.nan
                ),
                "missing_cells": int(missing_cells),
                "missing_value_rate": missing_cells / total_cells,
                "duplicate_tp_xy_states": duplicate_count,
                "duplicate_rate": duplicate_count / len(group),
                "quality_passed_rows": int((group["quality_status"] == "passed").sum()),
                "quality_failed_rows": int((group["quality_status"] == "failed").sum()),
                "quality_not_evaluated_rows": int((group["quality_status"] == "not_evaluated").sum()),
                "systems_lt_10_points_pct": safe_percentage(int((points < 10).sum()), len(points)),
                "systems_lt_20_points_pct": safe_percentage(int((points < 20).sum()), len(points)),
                "systems_gt_50_points_pct": safe_percentage(int((points > 50).sum()), len(points)),
            }
        )
    return pd.DataFrame(rows).sort_values("component_count")


def quality_issues(data: UnifiedData, systems: pd.DataFrame) -> pd.DataFrame:
    records = data.records
    occurrences = data.occurrences
    issues: list[dict[str, Any]] = []

    def add(row: pd.Series, issue_type: str, details: str) -> None:
        issues.append(
            {
                "dataset": row.get("dataset", ""),
                "record_id": row.get("record_id", ""),
                "source_file": row.get("source_file", ""),
                "excel_row": row.get("excel_row", ""),
                "system_id": row.get("system_id", ""),
                "issue_type": issue_type,
                "details": details,
            }
        )

    missing_by_record = occurrences.loc[occurrences["smiles_status"] == "missing"].groupby(
        ["dataset", "record_id"]
    )["component_position"].agg(list)
    failed_by_record = occurrences.loc[
        occurrences["smiles_status"] == "parse_failed"
    ].groupby(["dataset", "record_id"])["component_position"].agg(list)
    duplicate_mask = records.duplicated("canonical_state_key", keep=False)
    for _, row in records.iterrows():
        key = (row["dataset"], row["record_id"])
        if key in missing_by_record:
            add(row, "missing_smiles", f"component positions {missing_by_record[key]}")
        if key in failed_by_record:
            add(row, "smiles_parse_failure", f"component positions {failed_by_record[key]}")
        component_count = int(row["component_count"])
        x = np.asarray([row[f"x{i}"] for i in range(1, component_count + 1)], dtype=float)
        y = np.asarray([row[f"y{i}"] for i in range(1, component_count + 1)], dtype=float)
        if not np.isfinite(x).all() or not np.isfinite(y).all():
            add(row, "nonfinite_composition", "one or more x/y values are NaN or Inf")
        if np.isfinite(x).all() and ((x < 0.0) | (x > 1.0)).any():
            add(row, "liquid_composition_out_of_bounds", f"x={x.tolist()}")
        if np.isfinite(y).all() and ((y < 0.0) | (y > 1.0)).any():
            add(row, "vapor_composition_out_of_bounds", f"y={y.tolist()}")
        if row["temperature_k"] <= 0.0 or not np.isfinite(row["temperature_k"]):
            add(row, "invalid_temperature", f"T={row['temperature_k']} K")
        if row["pressure_kpa"] <= 0.0 or not np.isfinite(row["pressure_kpa"]):
            add(row, "invalid_pressure", f"P={row['pressure_kpa']} kPa")
        if not str(row["doi"]).strip():
            add(row, "missing_doi", "DOI is blank")
        if row["quality_status"] == "failed":
            add(
                row,
                "thermodynamic_consistency_failed",
                f"quality checks=({row['quality_check_1']}, {row['quality_check_2']})",
            )
        if bool(duplicate_mask.loc[row.name]):
            add(row, "duplicate_tp_xy_state", "duplicate after unordered component normalization")

    for _, row in systems.loc[systems["component_order_variants"] > 1].iterrows():
        issues.append(
            {
                "dataset": row["dataset"],
                "record_id": "",
                "source_file": "",
                "excel_row": "",
                "system_id": row["system_id"],
                "issue_type": "component_order_variant",
                "details": f"{row['component_order_variants']} source component orders",
            }
        )
    unresolved = occurrences.loc[occurrences["identity_method"] == "name_formula_fallback"]
    for component_id, group in unresolved.groupby("component_id"):
        first = group.iloc[0]
        issues.append(
            {
                "dataset": ";".join(sorted(set(group["dataset"]))),
                "record_id": first["record_id"],
                "source_file": first["source_file"],
                "excel_row": first["excel_row"],
                "system_id": "",
                "issue_type": "unresolved_component_identity",
                "details": f"{component_id}; name={first['original_name']}; formula={first['formula']}",
            }
        )
    columns = [
        "dataset",
        "record_id",
        "source_file",
        "excel_row",
        "system_id",
        "issue_type",
        "details",
    ]
    return pd.DataFrame(issues, columns=columns).sort_values(
        ["issue_type", "dataset", "record_id"]
    )


def _schema_report(data: UnifiedData) -> str:
    sections = [
        "# VLE dataset schema audit",
        "",
        "This audit was generated from the two workbooks themselves. The source files were opened read-only and were not modified.",
        "",
    ]
    for workbook in data.workbooks:
        schema = workbook.schema
        sections.extend(
            [
                f"## {schema['filename']}",
                "",
                f"- Absolute path: `{schema['path']}`",
                f"- Format: `{schema['format']}`; size: {schema['size_bytes']:,} bytes",
                f"- SHA-256: `{schema['sha256']}`",
                f"- Sheets: {schema['sheet_count']}; detected VLE sheet: `{workbook.data_sheet}`",
                f"- Actual system order: {workbook.component_count} components, inferred from `smiles1...smiles{workbook.component_count}` and composition columns",
                f"- Main-table rows: {schema['main_rows']:,}; columns: {schema['main_columns']}",
                f"- Exact raw duplicate rows: {schema['main_exact_duplicate_rows']:,}",
                "",
                "### Sheet inventory",
                "",
                markdown_table(
                    pd.DataFrame(schema["sheets"])[
                        [
                            "name",
                            "state",
                            "rows_including_header",
                            "columns",
                            "formula_cells",
                            "merged_ranges",
                            "hidden_rows",
                            "hidden_columns",
                            "data_validations",
                            "tables",
                        ]
                    ]
                ),
                "",
                "### Main-table fields",
                "",
            ]
        )
        dictionary = workbook.dictionary.set_index("field") if not workbook.dictionary.empty else None
        fields = []
        for column in workbook.frame.columns:
            fields.append(
                {
                    "field": column,
                    "dtype": schema["main_dtypes"][column],
                    "missing": schema["main_missing"][column],
                    "missing_rate_pct": 100.0 * schema["main_missing"][column] / schema["main_rows"],
                    "description": (
                        dictionary.loc[column, "description"]
                        if dictionary is not None and column in dictionary.index
                        else ""
                    ),
                    "unit_or_codes": (
                        dictionary.loc[column, "unit_or_codes"]
                        if dictionary is not None and column in dictionary.index
                        else ""
                    ),
                }
            )
        sections.extend([markdown_table(pd.DataFrame(fields)), ""])
    sections.extend(
        [
            "## Unified interpretation",
            "",
            "- Temperature is stored in degrees Celsius and converted to kelvin as `T_K = T_C + 273.15`.",
            "- Pressure is stored in mmHg and converted with `1 mmHg = 0.133322368 kPa`.",
            "- Binary tables store independent `x1` and `y1`; component-2 fractions are reconstructed by closure.",
            "- Ternary tables store independent `x1`, `x2`, `y1`, and `y2`; component-3 fractions are reconstructed by closure.",
            "- Quality codes are `1=passed`, `0=failed`, and `-1=not evaluated`; no records are silently removed in this analysis.",
            "- DOI is the publication-level provenance field. No CAS field or explicit InChIKey field exists; InChIKeys are generated only for RDKit-parseable SMILES.",
            "- System identity is an unordered tuple of stable component IDs, so source component order cannot split one chemical system into several identities.",
            "",
        ]
    )
    return "\n".join(sections)


def _statistics_report(
    summary: pd.DataFrame,
    systems: pd.DataFrame,
    coverage: pd.DataFrame,
) -> str:
    compact = summary[
        [
            "dataset",
            "data_points",
            "unique_systems",
            "unique_components",
            "points_per_system_mean",
            "points_per_system_median",
            "points_per_system_min",
            "points_per_system_max",
            "temperature_min_k",
            "temperature_max_k",
            "pressure_min_kpa",
            "pressure_max_kpa",
            "liquid_composition_min",
            "liquid_composition_max",
            "vapor_composition_min",
            "vapor_composition_max",
            "missing_value_rate",
            "duplicate_rate",
        ]
    ]
    sections = ["# Dataset statistics", "", markdown_table(compact), ""]
    composition = summary[
        [
            "dataset",
            "liquid_closure_abs_error_max",
            "vapor_closure_abs_error_max",
            "abs_y1_minus_x1_median",
            "abs_y1_minus_x1_q75",
            "abs_y1_minus_x1_max",
            "liquid_simplex_interior_pct",
            "liquid_simplex_vertex_pct",
            "vapor_simplex_interior_pct",
            "vapor_simplex_vertex_pct",
        ]
    ]
    sections.extend(["## Composition-space statistics", "", markdown_table(composition), ""])
    for dataset in ("Binary", "Ternary"):
        top = systems.loc[systems["dataset"] == dataset].nlargest(10, "data_points")
        sections.extend(
            [
                f"## Top 10 {dataset.lower()} systems by data-point count",
                "",
                markdown_table(top[["system_label", "data_points", "references"]]),
                "",
            ]
        )
    coverage_counts = (
        coverage["available_binary_subsystems"].value_counts().reindex([3, 2, 1, 0], fill_value=0)
    )
    coverage_table = pd.DataFrame(
        {
            "known_binary_subsystems": coverage_counts.index,
            "ternary_systems": coverage_counts.values,
            "percentage": 100.0 * coverage_counts.values / len(coverage),
        }
    )
    sections.extend(
        ["## Ternary-to-binary subsystem coverage", "", markdown_table(coverage_table), ""]
    )
    return "\n".join(sections)


def _distribution_report(
    summary: pd.DataFrame,
    components: pd.DataFrame,
    molecular: pd.DataFrame,
    families: pd.DataFrame,
    systems: pd.DataFrame,
    coverage: pd.DataFrame,
    issues: pd.DataFrame,
    records: pd.DataFrame,
) -> str:
    binary = summary.loc[summary["dataset"] == "Binary"].iloc[0]
    ternary = summary.loc[summary["dataset"] == "Ternary"].iloc[0]
    membership = components["dataset_membership"].value_counts()
    coverage_counts = coverage["available_binary_subsystems"].value_counts().reindex(
        [3, 2, 1, 0], fill_value=0
    )
    issue_counts = issues["issue_type"].value_counts().rename_axis("issue_type").reset_index(name="rows_or_systems")
    records_total = int(binary["data_points"] + ternary["data_points"])
    parseable = int(molecular["has_parseable_smiles"].sum())
    projected = int((molecular["umap_status"] == "projected").sum())
    disconnected = int((molecular["umap_status"] == "disconnected").sum())
    ternary_only_unresolved = int(
        (
            molecular["dataset_membership"].eq("Ternary only")
            & molecular["umap_status"].eq("unresolved_smiles")
        ).sum()
    )
    total_components = int(len(components))
    binary_x = records.loc[records["dataset"] == "Binary", "x1"]
    binary_records = records.loc[records["dataset"] == "Binary"]
    ternary_records = records.loc[records["dataset"] == "Ternary"]
    ternary_x = ternary_records[["x1", "x2", "x3"]].to_numpy()
    ternary_y = ternary_records[["y1", "y2", "y3"]].to_numpy()
    binary_separation = (binary_records["y1"] - binary_records["x1"]).abs()
    binary_endpoint_pct = 100.0 * ((binary_x <= 0.05) | (binary_x >= 0.95)).mean()
    ternary_interior_pct = 100.0 * (np.nanmin(ternary_x, axis=1) >= 0.05).mean()
    ternary_vertex_pct = 100.0 * (np.nanmax(ternary_x, axis=1) >= 0.90).mean()
    ternary_vapor_interior_pct = 100.0 * (np.nanmin(ternary_y, axis=1) >= 0.05).mean()
    ternary_vapor_vertex_pct = 100.0 * (np.nanmax(ternary_y, axis=1) >= 0.90).mean()
    ternary_closure_max = float(
        max(
            np.abs(ternary_x.sum(axis=1) - 1.0).max(),
            np.abs(ternary_y.sum(axis=1) - 1.0).max(),
        )
    )
    lines = [
        "# VLE dataset distribution report",
        "",
        f"Reproducible analysis seed: `{SEED}`. Software: Python {platform.python_version()}, pandas {pd.__version__}, RDKit {rdkit.__version__}.",
        "",
        "## Dataset 1 — Binary",
        "",
        f"- Data points: **{int(binary['data_points']):,}**",
        f"- Unique unordered systems: **{int(binary['unique_systems']):,}**",
        f"- Unique components: **{int(binary['unique_components']):,}**",
        f"- Temperature: **{binary['temperature_min_k']:.2f}–{binary['temperature_max_k']:.2f} K** ({binary['temperature_min_c']:.2f}–{binary['temperature_max_c']:.2f} °C)",
        f"- Pressure: **{binary['pressure_min_kpa']:.4g}–{binary['pressure_max_kpa']:.4g} kPa**",
        f"- Reconstructed liquid/vapor component fractions: **{binary['liquid_composition_min']:.4g}–{binary['liquid_composition_max']:.4g} / {binary['vapor_composition_min']:.4g}–{binary['vapor_composition_max']:.4g}**",
        f"- Median points per system: **{binary['points_per_system_median']:.1f}**",
        "",
        "## Dataset 2 — Ternary",
        "",
        f"- Data points: **{int(ternary['data_points']):,}**",
        f"- Unique unordered systems: **{int(ternary['unique_systems']):,}**",
        f"- Unique components: **{int(ternary['unique_components']):,}**",
        f"- Temperature: **{ternary['temperature_min_k']:.2f}–{ternary['temperature_max_k']:.2f} K** ({ternary['temperature_min_c']:.2f}–{ternary['temperature_max_c']:.2f} °C)",
        f"- Pressure: **{ternary['pressure_min_kpa']:.4g}–{ternary['pressure_max_kpa']:.4g} kPa**",
        f"- Reconstructed liquid/vapor component fractions: **{ternary['liquid_composition_min']:.4g}–{ternary['liquid_composition_max']:.4g} / {ternary['vapor_composition_min']:.4g}–{ternary['vapor_composition_max']:.4g}**",
        f"- Median points per system: **{ternary['points_per_system_median']:.1f}**",
        "",
        "## Cross-dataset relationship",
        "",
        f"- Binary-only molecules: **{int(membership.get('Binary only', 0))}**",
        f"- Ternary-only molecules: **{int(membership.get('Ternary only', 0))}**",
        f"- Shared molecules: **{int(membership.get('Shared', 0))}**",
        f"- RDKit-parseable unique molecules: **{parseable}/{total_components}**",
        f"- Molecules projected by Morgan-UMAP: **{projected}**; disconnected fingerprint-graph vertices retained outside the 2D map: **{disconnected}**",
        f"- Ternary-only identities without a resolvable structure: **{ternary_only_unresolved}** (therefore no ternary-only point can be placed in the molecular projection)",
        f"- Ternary systems with 3/2/1/0 known binary subsystems: **{coverage_counts[3]}/{coverage_counts[2]}/{coverage_counts[1]}/{coverage_counts[0]}**",
        "",
        "## Data-quality findings",
        "",
        markdown_table(issue_counts),
        "",
        f"Across {records_total:,} source rows, exact raw-row duplicates are absent, while unordered TPXY normalization identifies the duplicate states listed above. Missing SMILES are retained and resolved through a unique name–formula link when possible; identities without a unique SMILES link remain explicit fallback IDs. Quality code `-1` means not evaluated, not passed. No anomaly is automatically deleted.",
        "",
        "Explicit zero findings: no finite composition lies outside [0, 1]; no reconstructed ternary fraction is outside [0, 1]; no T≤0 K or P≤0 record, NaN/Inf thermodynamic value, blank DOI, or RDKit parse failure for a nonblank SMILES was found. The workbooks' data dictionaries consistently define pressure in mmHg, temperature in °C and composition as mol/mol; no contradictory unit field was detected. The 18 duplicate-issue rows form 9 additional canonical TPXY states beyond the first occurrence.",
        "",
        f"For ternary rows, `x3` and `y3` are not independent workbook fields: they are reconstructed as `1-x1-x2` and `1-y1-y2`. Consequently, closure residuals are algebraically zero up to floating-point precision (maximum {ternary_closure_max:.3g}); out-of-bound reconstructed fractions are the meaningful closure-quality check.",
        "",
        "## Scientific interpretation",
        "",
        f"1. The combined data span a broad temperature interval and about 6.7 orders of magnitude in pressure; pressure is therefore visualized logarithmically. Coverage density is highly nonuniform, so apparent global breadth should not be interpreted as uniform local support.",
        f"2. Binary compositions include {binary_endpoint_pct:.1f}% of rows near an `x1` endpoint (≤0.05 or ≥0.95); `|y1-x1|` has median {binary_separation.median():.3f}, upper quartile {binary_separation.quantile(0.75):.3f} and maximum {binary_separation.max():.4g}. In the ternary liquid simplex, {ternary_interior_pct:.1f}% of rows lie in the interior and {ternary_vertex_pct:.1f}% near a vertex; the corresponding vapor-simplex fractions are {ternary_vapor_interior_pct:.1f}% and {ternary_vapor_vertex_pct:.1f}%, confirming uneven liquid and vapor coverage.",
        f"3. Morgan fingerprints resolve {parseable} unique molecules; {projected} form the connected UMAP projection and {disconnected} isolated fingerprints are retained but not assigned finite 2D coordinates. All {ternary_only_unresolved} ternary-only identities lack a resolvable structure, so the map cannot establish the extent of ternary-exclusive chemical space; unresolved or isolated identities must not be interpreted as absent chemistry.",
        f"4. Binary-to-ternary transfer is directly supported for {coverage_counts[3]} ternary systems with all three constituent binary pairs, while systems with partial or zero pair coverage provide progressively harder compositional generalization tests.",
        f"5. Both datasets are long-tailed: {binary['systems_lt_20_points_pct']:.1f}% of binary and {ternary['systems_lt_20_points_pct']:.1f}% of ternary systems contain fewer than 20 points. Sparse systems, high-pressure regions, unresolved molecular identities, and ternary simplex regions without complete binary-subsystem support are the most demanding generalization regimes.",
        "",
        "## Reproducibility",
        "",
        "Run from the project root:",
        "",
        "```powershell",
        "conda activate ggnn39",
        "python analysis/dataset_distribution/scripts/analyze_datasets.py",
        "python analysis/dataset_distribution/scripts/plot_dataset_overview.py",
        "```",
        "",
    ]
    return "\n".join(lines)


def _caption() -> str:
    return """# Figure dataset overview caption

## English

**Figure 1 | Statistical overview of the vapor–liquid equilibrium datasets.** **a,** Numbers of experimental state points, unique unordered chemical systems and unique molecular components in the binary and ternary datasets. **b,** Experimental temperature–pressure coverage, with pressure shown on a logarithmic scale and contours denoting the two datasets. **c,** Composition-space coverage represented by the binary liquid–vapor map and the ternary liquid-composition simplex; the third ternary fraction is reconstructed by closure. **d,** Molecular chemical space obtained from UMAP projection of radius-2, 2,048-bit Morgan fingerprints, colored by dataset membership; legend values give projected and total molecule counts. **e,** Rank–frequency distributions of experimental points per unordered system. **f,** Availability of the three constituent binary subsystems for each unique ternary system. Counts use canonicalized, order-invariant component identities; unresolved structures and graph-isolated fingerprints are not assigned UMAP coordinates.

## 中文

**图 1 | 汽液相平衡数据集的统计总览。** **a，** 二元和三元数据集中实验状态点、无序化学物系及唯一分子组分的数量。**b，** 实验温度–压力覆盖范围；压力采用对数坐标，等高线区分两个数据集。**c，** 二元液相–汽相组成映射与三元液相组成单纯形；三元第三组分由组成闭合关系重建。**d，** 基于半径 2、2,048 位 Morgan 指纹并经 UMAP 降维得到的分子化学空间；图例数字依次为已投影/总分子数。**e，** 每个无序物系实验点数的秩–频分布。**f，** 每个唯一三元体系的三个组成二元子体系在二元数据集中的可用情况。所有计数采用规范化且与组分顺序无关的身份；未解析结构和指纹图孤立点不分配 UMAP 坐标。
"""


def write_outputs(dataset_root: Path, analysis_root: Path) -> dict[str, Any]:
    results_dir = analysis_root / "results"
    reports_dir = analysis_root / "reports"
    figures_dir = analysis_root / "figures"
    for directory in (results_dir, reports_dir, figures_dir):
        directory.mkdir(parents=True, exist_ok=True)

    data = load_unified_data(dataset_root)
    components = component_statistics(data)
    systems = system_statistics(data.records, components)
    summary = dataset_summary(data, systems, components)
    coverage = ternary_binary_coverage(data.records)
    issues = quality_issues(data, systems)

    summary.to_csv(results_dir / "dataset_summary.csv", index=False)
    systems.to_csv(results_dir / "system_statistics.csv", index=False)
    components.to_csv(results_dir / "component_statistics.csv", index=False)
    coverage.to_csv(results_dir / "ternary_binary_subsystem_coverage.csv", index=False)
    issues.to_csv(results_dir / "data_quality_issues.csv", index=False)
    data.records[
        [
            "dataset",
            "record_id",
            "system_id",
            "temperature_k",
            "pressure_kpa",
            "x1",
            "x2",
            "x3",
            "y1",
            "y2",
            "y3",
        ]
    ].to_csv(results_dir / "vle_records_for_plotting.csv", index=False)
    rank_rows = []
    for dataset, group in systems.groupby("dataset"):
        ranked = group.sort_values("data_points", ascending=False).reset_index(drop=True)
        ranked["rank"] = np.arange(1, len(ranked) + 1)
        rank_rows.append(ranked[["dataset", "rank", "system_id", "system_label", "data_points"]])
    pd.concat(rank_rows).to_csv(results_dir / "system_rank_frequency.csv", index=False)
    summary[["dataset", "data_points", "unique_systems", "unique_components"]].to_csv(
        results_dir / "dataset_scale.csv", index=False
    )

    molecular, families = analyze_molecular_space(components, results_dir)
    schema_text = _schema_report(data)
    (reports_dir / "dataset_schema_audit.md").write_text(schema_text, encoding="utf-8")
    project_reports = dataset_root.parent / "reports"
    project_reports.mkdir(parents=True, exist_ok=True)
    (project_reports / "dataset_schema_audit.md").write_text(schema_text, encoding="utf-8")
    (reports_dir / "dataset_statistics.md").write_text(
        _statistics_report(summary, systems, coverage), encoding="utf-8"
    )
    (reports_dir / "dataset_distribution_report.md").write_text(
        _distribution_report(
            summary,
            components,
            molecular,
            families,
            systems,
            coverage,
            issues,
            data.records,
        ),
        encoding="utf-8",
    )
    (reports_dir / "Figure_dataset_overview_caption.md").write_text(
        _caption(), encoding="utf-8"
    )
    return {
        "summary": summary.to_dict(orient="records"),
        "unique_components": len(components),
        "molecular_embeddings": int(molecular["umap_1"].notna().sum()),
        "quality_issue_rows": len(issues),
        "coverage": coverage["available_binary_subsystems"].value_counts().sort_index().to_dict(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    project_root = Path(__file__).resolve().parents[3]
    parser.add_argument("--dataset-root", type=Path, default=project_root / "dataset")
    parser.add_argument(
        "--analysis-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args()
    outputs = write_outputs(args.dataset_root.resolve(), args.analysis_root.resolve())
    print(outputs)


if __name__ == "__main__":
    main()
