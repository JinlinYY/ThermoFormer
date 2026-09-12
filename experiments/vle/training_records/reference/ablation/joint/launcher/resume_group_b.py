import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\VLE\VLE\.vle_ablation_release_worktree")
PYTHON = Path(r"E:\anaconda\envs\ggnn39\python.exe")
SCRIPT = ROOT / "scripts" / "run_vle_joint_ablations.py"

COMMANDS = [
    [str(PYTHON), str(SCRIPT), "--variant", "v4_rdkit_unimol_naive", "--seeds", "4", "--device", "cuda"],
    [str(PYTHON), str(SCRIPT), "--variant", "c2_chemical_bias_full", "--seeds", "0", "1", "2", "3", "4", "--device", "cuda"],
    [str(PYTHON), str(SCRIPT), "--variant", "c3_no_pair_bias", "--seeds", "0", "1", "2", "3", "4", "--device", "cuda"],
]

for command in COMMANDS:
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode:
        sys.exit(completed.returncode)
