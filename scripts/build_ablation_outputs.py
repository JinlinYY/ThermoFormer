"""Build fixed-definition ThermoFormer ablation tables, figures, and report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ablation_outputs import build_ablation_outputs


if __name__ == "__main__":
    print(json.dumps(build_ablation_outputs(PROJECT_ROOT), ensure_ascii=False, indent=2))
