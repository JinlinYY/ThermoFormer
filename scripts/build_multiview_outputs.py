"""Build machine-derived multi-view screening and final reports."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.multiview_outputs import (
    atomic_csv,
    formal_seed_table,
    formal_table,
    screening_table,
    write_final_report,
    write_screening_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("screening", "formal"), required=True)
    args = parser.parse_args()
    screening = screening_table(PROJECT_ROOT)
    screening_path = PROJECT_ROOT / "results" / "multiview" / "screening" / "screening_metrics.csv"
    screening_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_csv(screening_path, screening)
    report = write_screening_report(PROJECT_ROOT, screening)
    outputs = [screening_path, report]
    if args.stage == "formal":
        formal = formal_table(PROJECT_ROOT)
        formal_seeds = formal_seed_table(PROJECT_ROOT)
        formal_path = PROJECT_ROOT / "results" / "multiview" / "formal" / "formal_metrics.csv"
        seed_path = PROJECT_ROOT / "results" / "multiview" / "formal" / "formal_metrics_by_seed.csv"
        atomic_csv(formal_path, formal)
        atomic_csv(seed_path, formal_seeds)
        outputs.extend(
            [formal_path, seed_path, write_final_report(PROJECT_ROOT, screening, formal, formal_seeds)]
        )
    print(json.dumps({"outputs": [str(path) for path in outputs]}))


if __name__ == "__main__":
    main()
