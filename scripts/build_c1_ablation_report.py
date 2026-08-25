"""Build the focused overall_binary_ternary C1 ablation report."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.thermoformer.reporting.c1_ablation import write_c1_ablation_outputs


def main() -> None:
    """Build all retained C1 ablation tables and reports."""
    for output in write_c1_ablation_outputs(PROJECT_ROOT):
        print(output)


if __name__ == "__main__":
    main()
