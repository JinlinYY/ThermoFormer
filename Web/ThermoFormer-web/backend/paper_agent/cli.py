"""Run one request in the ggnn39 environment: python -m paper_agent.cli."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paper_agent.contracts import PaperRequest
from paper_agent.runtime import configure_runtime


def main() -> None:
    configure_runtime()
    from paper_agent.runner import run_design

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    request = PaperRequest.model_validate_json(args.request.read_text(encoding="utf-8"))
    result = run_design(request)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    print(json.dumps({"run_id": result.run_id, "outcome": result.outcome, "calls": result.calls}))


if __name__ == "__main__":
    main()
