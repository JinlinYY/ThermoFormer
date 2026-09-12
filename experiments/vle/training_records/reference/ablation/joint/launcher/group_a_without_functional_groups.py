import subprocess
import sys
from pathlib import Path
root = Path(r"D:\VLE\VLE\.vle_ablation_release_worktree")
python = r"E:\anaconda\envs\ggnn39\python.exe"
script = "scripts/run_vle_joint_ablations.py"
out_path = root / "experiments/vle/training_records/reference/ablation/joint/launcher/group_a.out.log"
err_path = root / "experiments/vle/training_records/reference/ablation/joint/launcher/group_a.err.log"
commands = [
    [python, script, "--variant", "c0_current_vanilla", "--seeds", "1", "2", "3", "4", "--device", "cuda", "--overwrite"],
    [python, script, "--variant", "c0_current_vanilla", "--seeds", "0", "1", "2", "3", "4", "--device", "cuda"],
    [python, script, "--variant", "v1_rdkit_only", "--seeds", "0", "1", "2", "3", "4", "--device", "cuda"],
]
with out_path.open("a", encoding="utf-8") as out, err_path.open("a", encoding="utf-8") as err:
    out.write("\n[queue revised] functional-group-only variant removed; resuming c0 seeds 1-4, then v1 seeds 0-4\n")
    out.flush()
    for command in commands:
        completed = subprocess.run(command, cwd=root, stdout=out, stderr=err)
        if completed.returncode:
            sys.exit(completed.returncode)
