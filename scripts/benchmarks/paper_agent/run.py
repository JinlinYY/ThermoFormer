"""Execute the frozen pilot, retaining every run including failures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmarks.paper_agent.tasks import pilot_tasks
from paper_agent.contracts import PaperRequest, PaperRun
from paper_agent.runtime import configure_runtime


def main() -> None:
    configure_runtime()
    from paper_agent.runner import run_design

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--modes", nargs="+", choices=["fixed", "rule", "llm", "rule_guided", "llm_guided"], default=["fixed", "rule"]
    )
    parser.add_argument("--llm-repeats", type=int, default=3)
    parser.add_argument("--case", choices=["binary", "extractive", "extraction"])
    parser.add_argument(
        "--resume", action="store_true", help="Continue the exact saved task set without replacing runs."
    )
    args = parser.parse_args()
    if not 1 <= args.llm_repeats <= 10:
        parser.error("LLM repeats must be between 1 and 10")
    args.output.mkdir(parents=True, exist_ok=True)
    tasks = [task for task in pilot_tasks() if args.case is None or task.case == args.case]
    manifest = args.output / "tasks.json"
    if manifest.exists() and not args.resume:
        parser.error("Use a fresh output directory to preserve immutable experiment records.")
    expected = [t.model_dump() for t in tasks]
    if manifest.exists():
        if json.loads(manifest.read_text(encoding="utf-8")) != expected:
            parser.error("Saved task set differs; use a new output directory.")
    else:
        manifest.write_text(json.dumps(expected, indent=2), encoding="utf-8")
    summary = []
    protocol = args.output / "protocol"
    protocol.mkdir(exist_ok=True)
    experiment = {"modes": args.modes, "llm_repeats": args.llm_repeats}
    identity = protocol / "experiment.json"
    if identity.exists() and json.loads(identity.read_text()) != experiment:
        parser.error("Saved experiment modes/repeats differ; use a new output directory.")
    identity.write_text(json.dumps(experiment, indent=2), encoding="utf-8")
    for mode in args.modes:
        provider_failed = False
        for repeat in range(args.llm_repeats if mode in {"llm", "llm_guided"} else 1):
            for task in tasks:
                destination = args.output / (task.task_id + "-" + mode + "-" + str(repeat) + ".json")
                if destination.exists():
                    run = PaperRun.model_validate_json(destination.read_text(encoding="utf-8"))
                    if run.task != task or run.mode != mode or run.repeat != repeat:
                        raise ValueError("Saved run does not match its request")
                else:
                    run = run_design(PaperRequest(task=task, mode=mode, repeat=repeat))
                    destination.write_text(run.model_dump_json(indent=2), encoding="utf-8")
                summary.append(
                    dict(
                        task_id=task.task_id,
                        case=task.case,
                        mode=mode,
                        repeat=repeat,
                        outcome=run.outcome,
                        calls=run.calls,
                        elapsed_s=run.elapsed_s,
                        **run.assessment,
                    )
                )
                print(task.task_id, mode, repeat, run.outcome, run.calls, flush=True)
                if run.outcome == "provider_error":
                    provider_failed = True
                    break
            if provider_failed:
                break
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
