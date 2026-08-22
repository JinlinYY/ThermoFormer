"""Build Table-1-style molecular-representation result tables."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.multiview_outputs import atomic_csv
from src.representation_outputs import (
    representation_predictive_table,
    write_representation_report,
    write_variant_predictive_pages,
)


def main() -> None:
    table = representation_predictive_table(PROJECT_ROOT)
    table_path = (
        PROJECT_ROOT / "results" / "multiview" / "predictive"
        / "representation_performance.csv"
    )
    atomic_csv(table_path, table)
    outputs = [table_path, write_representation_report(PROJECT_ROOT, table)]
    outputs.extend(write_variant_predictive_pages(PROJECT_ROOT, table))
    print(json.dumps({"outputs": [str(path) for path in outputs]}))


if __name__ == "__main__":
    main()
