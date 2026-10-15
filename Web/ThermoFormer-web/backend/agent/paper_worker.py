"""Run paper calculations in the user's ggnn39 environment, not the API interpreter."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from paper_agent.contracts import PaperRequest, PaperRun

ROOT = Path(__file__).resolve().parents[1]


def run_paper_worker(request: PaperRequest) -> PaperRun:
    executable = Path(os.getenv("THERMO_PAPER_PYTHON", sys.executable))
    if not executable.is_file():
        raise RuntimeError("ggnn39 interpreter not found; configure THERMO_PAPER_PYTHON.")
    with TemporaryDirectory(prefix="thermo-paper-") as directory:
        temporary = Path(directory)
        input_path, output_path = temporary / "request.json", temporary / "result.json"
        input_path.write_text(request.model_dump_json(), encoding="utf-8")
        completed = subprocess.run(
            [str(executable), "-m", "paper_agent.cli", "--request", str(input_path), "--output", str(output_path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
        if completed.returncode or not output_path.is_file():
            raise RuntimeError("Paper numerical worker failed; verify ggnn39 dependencies and registered checkpoints.")
        result = PaperRun.model_validate_json(output_path.read_text(encoding="utf-8"))
    archive = ROOT / "outputs/paper_agent/api"
    archive.mkdir(parents=True, exist_ok=True)
    # Exclusive creation preserves immutable snapshots even on a UUID collision.
    with (archive / (result.run_id + ".json")).open("x", encoding="utf-8") as stream:
        stream.write(result.model_dump_json(indent=2))
    return result
