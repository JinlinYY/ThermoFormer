"""Build the focused overall_binary_ternary C1 ablation report."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.c1_ablation_outputs import write_c1_ablation_outputs


if __name__ == "__main__":
    for output in write_c1_ablation_outputs(PROJECT_ROOT):
        print(output)
