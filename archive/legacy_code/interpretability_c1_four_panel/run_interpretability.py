"""Run the final C1 five-seed interpretability analysis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.thermoformer.interpretability.c1_final import run_c1_final_interpretability


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--max-samples-per-seed", type=int, default=256)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--smoke", action="store_true")
    arguments = parser.parse_args()
    maximum = 12 if arguments.smoke and arguments.max_samples_per_seed == 256 else arguments.max_samples_per_seed
    result = run_c1_final_interpretability(
        PROJECT_ROOT,
        device_name=arguments.device,
        max_samples_per_seed=maximum,
        batch_size=arguments.batch_size,
        output_root=(
            PROJECT_ROOT / "runs/interpretability_smoke/analysis/interpretability_c1_final"
            if arguments.smoke
            else None
        ),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
