"""Orchestration and artifact export for the interpretability campaign."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from .analysis import (
    composition_nonideality_table,
    interaction_attribution_table,
    load_context,
    manybody_effects_table,
    select_representative_cases,
    thermodynamic_sensitivity_table,
)
from .plotting import build_interpretability_figure
from .reporting import write_interpretability_report


def _atomic_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            frame.to_csv(handle, index=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    text_suffixes = {".csv", ".json", ".md", ".py", ".svg"}
    if path.suffix.lower() in text_suffixes:
        content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        digest.update(content)
        return digest.hexdigest()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_interpretability(
    project_root: Path,
    device_name: str = "auto",
) -> dict[str, object]:
    project_root = project_root.resolve()
    root = project_root / "analysis" / "interpretability"
    results_dir = root / "results"
    figures_dir = root / "figures"
    reports_dir = root / "reports"
    context = load_context(project_root, device_name)
    representative = select_representative_cases(context)

    attribution = interaction_attribution_table(context, representative)
    composition = composition_nonideality_table(context, representative)
    sensitivity = thermodynamic_sensitivity_table(context, representative)
    manybody = manybody_effects_table(context)

    tables = {
        "interaction_attribution": attribution,
        "composition_nonideality": composition,
        "thermodynamic_sensitivity": sensitivity,
        "manybody_effects": manybody,
    }
    table_paths = []
    for name, frame in tables.items():
        path = results_dir / f"{name}.csv"
        _atomic_csv(frame, path)
        table_paths.append(path)

    figure_paths = build_interpretability_figure(
        attribution,
        composition,
        sensitivity,
        manybody,
        figures_dir / "Figure_interpretability",
    )
    report_path = reports_dir / "interpretability_report.md"
    write_interpretability_report(
        report_path,
        context,
        attribution,
        composition,
        sensitivity,
        manybody,
    )
    artifacts = [*table_paths, *figure_paths, report_path]
    input_paths = [
        context.full.checkpoint,
        context.pairwise.checkpoint,
        project_root / "cache" / "unimolv2_84m.npz",
        project_root / "splits" / context.full.protocol / f"seed_{context.best_seed}.json",
        *sorted((project_root / "dataset").rglob("*.xlsx")),
    ]
    code_paths = sorted((project_root / "src" / "interpretability").glob("*.py")) + [
        project_root / "scripts" / "run_interpretability.py"
    ]
    manifest = {
        "status": "completed",
        "analysis": "ThermoFormer interpretability",
        "device": str(context.device),
        "full_protocol": context.full.protocol,
        "pairwise_protocol": context.pairwise.protocol,
        "validation_selected_seed": context.best_seed,
        "full_checkpoint": str(context.full.checkpoint),
        "pairwise_checkpoint": str(context.pairwise.checkpoint),
        "representative_systems": {
            category: list(system) for category, system in representative.items()
        },
        "row_counts": {name: len(frame) for name, frame in tables.items()},
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "device": str(context.device),
        },
        "inputs": {
            str(path.relative_to(project_root)).replace("\\", "/"): _digest(path)
            for path in input_paths
        },
        "analysis_code": {
            str(path.relative_to(project_root)).replace("\\", "/"): _digest(path)
            for path in code_paths
        },
        "artifacts": {
            str(path.relative_to(project_root)).replace("\\", "/"): _digest(path)
            for path in artifacts
        },
    }
    manifest_path = reports_dir / "analysis_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {**manifest, "manifest": str(manifest_path)}
