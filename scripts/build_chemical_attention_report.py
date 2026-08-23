"""Build the seed-0 chemical-attention pilot report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.chemical_attention_outputs import write_pilot_outputs


if __name__ == "__main__":
    outputs = write_pilot_outputs(PROJECT_ROOT)
    print(json.dumps({"outputs": [str(path) for path in outputs]}))

