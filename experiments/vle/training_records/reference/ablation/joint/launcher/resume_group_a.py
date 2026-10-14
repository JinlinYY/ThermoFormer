import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[7]
PYTHON = Path(sys.executable)
SCRIPT = ROOT / "scripts" / "run_vle_joint_ablations.py"

COMMANDS = [
    [str(PYTHON), str(SCRIPT), "--variant", "c0_current_vanilla", "--seeds", "4", "--device", "cuda"],
    [str(PYTHON), str(SCRIPT), "--variant", "v1_rdkit_only", "--seeds", "0", "1", "2", "3", "4", "--device", "cuda"],
]

for command in COMMANDS:
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode:
        sys.exit(completed.returncode)
