"""Run real LLM input/trace reliability with immutable paper-protocol calculations."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from benchmarks.paper_agent.reliability_tasks import reliability_tasks
from paper_agent.policy import ProviderFailure
from paper_agent.reliability import PLANS, ReliabilityLLM, audit_report, compile_task
from paper_agent.runtime import configure_runtime

ROOT = Path(__file__).resolve().parents[2]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects both failures and successful raw records.
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def sources() -> dict[str, str]:
    upstream = ROOT / "lab_models/ThermoFormer/ThermoAgent"
    paths = list((ROOT / "paper_agent").glob("*.py"))
    paths += list((ROOT / "benchmarks/paper_agent").glob("reliability*.py"))
    paths += list((ROOT / "thermo_engine").glob("paper*.py"))
    paths += list(upstream.glob("*.py")) + [upstream / "provenance.json"]
    paths += [p for p in (upstream / "cases").rglob("*") if p.suffix in {".json", ".csv"}]
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}


def run_one(task: dict[str, Any], repeat: int, output: Path, cache: dict[str, Any]) -> dict[str, Any]:
    from thermo_engine.paper_reliability import execute_frozen_protocol

    llm = ReliabilityLLM()
    started = time.monotonic()
    run: dict[str, Any] = dict(
        task_id=task["task_id"],
        case=task["case"],
        kind=task["kind"],
        repeat=repeat,
        request=task["prompt"],
        started_utc=datetime.now(timezone.utc).isoformat(),  # noqa: UP017 -- Python 3.9 worker
        trace=[],
        provider_calls=llm.calls,
        outcome="failed",
        metrics=dict(
            parse_correct=False,
            plan_correct=False,
            clarification_correct=False,
            gate_blocks_invalid=False,
            tool_execution_correct=False,
            result_consistent=False,
            report_grounded=False,
        ),
    )
    trace, metrics = run["trace"], run["metrics"]
    try:
        parsed = llm.parse(task["prompt"])
        run["parsed"] = parsed.model_dump()
        trace.append(dict(step="requirement", output=parsed.model_dump(), origin="live_LLM"))
        compiled = compile_task(parsed, task["prompt"])
        run["compiled"] = compiled.model_dump()
        trace.append(dict(step="contract_gate", output=compiled.model_dump(), origin="deterministic_validation"))
        expected = task["expected_values"]
        if expected is not None:
            metrics["parse_correct"] = (
                parsed.status == "ready"
                and parsed.protocol == task["case"]
                and set(compiled.normalized) == set(expected)
                and all(math.isclose(compiled.normalized[k], v, rel_tol=0, abs_tol=1e-8) for k, v in expected.items())
                and compiled.status == "ready"
            )
            metrics["plan_correct"] = parsed.protocol == task["case"] and parsed.plan == PLANS[task["case"]]
        else:
            metrics["clarification_correct"] = parsed.status == "clarify" and any(
                issue.field in task["expected_issue_fields"] and issue.kind == task["kind"] for issue in parsed.issues
            )
            metrics["gate_blocks_invalid"] = compiled.status != "ready"
        if compiled.status != "ready":
            run["outcome"] = compiled.status
            return run
        assert compiled.contract is not None
        contract = compiled.contract
        trace.append(dict(step="plan", actions=parsed.plan, origin="live_LLM"))
        key = contract.identity()
        tick = time.monotonic()
        if key in cache:
            bundle = cache[key]
            cache_hit = True
        else:
            bundle = execute_frozen_protocol(contract)
            save(output / "numerical" / (key + ".json"), bundle)
            cache[key] = bundle
            cache_hit = False
        artifact = output / "numerical" / (key + ".json")
        run["numerical_artifact"] = str(artifact.relative_to(output))
        run["numerical_sha256"] = digest(artifact)
        run["cache_hit"] = cache_hit
        run["final"] = bundle["final"]
        run["paper_agreement"] = bundle["paper_agreement"]
        trace.append(
            dict(
                step="tool",
                action=parsed.plan[0],
                origin="cached_frozen_protocol_result" if cache_hit else "fresh_frozen_protocol_execution",
                artifact=run["numerical_artifact"],
                artifact_sha256=run["numerical_sha256"],
                elapsed_s=time.monotonic() - tick,
                final=bundle["final"],
            )
        )
        metrics["tool_execution_correct"] = bool(
            bundle["protocol"] == parsed.protocol
            and bundle["contract_id"] == key
            and all(r["status"] == "valid" for r in bundle["observations"])
        )
        metrics["result_consistent"] = bool(metrics["parse_correct"] and bundle["paper_agreement"]["passed"])
        # A recorded deterministic audit operation interprets the solver evidence.
        trace.append(
            dict(
                step="tool",
                action=parsed.plan[1],
                origin="audit_of_numerical_tool_evidence",
                evidence=bundle["evidence"],
            )
        )
        report = llm.report(bundle["evidence"], bundle["claim_catalog"])
        assessed = audit_report(report, bundle["supported_claims"])
        run["raw_report"], run["report_audit"] = report.model_dump(), assessed
        metrics["report_grounded"] = assessed["fully_grounded"]
        trace.append(dict(step="review", origin="live_LLM", output=report.model_dump(), audit=assessed))
        # Only strictly grounded reports are rendered. Raw failures remain in the record.
        run["outcome"] = "reported" if assessed["fully_grounded"] else "report_blocked"
        rendered = {k: bundle["claim_catalog"][k] for k in assessed["supported_claims"]}
        trace.append(
            dict(
                step="report",
                origin="deterministic_evidence_renderer",
                status=run["outcome"],
                numerical_values=bundle["final"] if run["outcome"] == "reported" else None,
                supported_statements=rendered,
                limits_retained=True,
            )
        )
    except ProviderFailure as exc:
        run.update(outcome="provider_error", error=str(exc))
    except (ValidationError, ValueError, RuntimeError, KeyError) as exc:
        # No substitution by a rule policy or fabricated thermodynamic observation.
        run.update(outcome="execution_error", error=type(exc).__name__ + ": " + str(exc))
    finally:
        run["elapsed_s"] = time.monotonic() - started
        run["llm_tokens"] = sum(c.get("usage", {}).get("total_tokens", 0) for c in llm.calls)
    return run


def main() -> None:
    configure_runtime()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.repeats <= 5:
        parser.error("repeats must be 1-5")
    tasks = reliability_tasks()
    identity = dict(
        tasks=tasks,
        repeats=args.repeats,
        sources=sources(),
        design="15 equivalent + 9 missing/conflicting/ambiguous requests; independent LLM contexts",
        temperature=0,
        python=sys.executable,
        python_version=platform.python_version(),
        scoring="before deterministic report gate; no hidden fallback; all attempted failures retained",
        tolerance={
            "input_normalization_abs": 1e-8,
            "binary_stage_counts": "exact",
            "extractive_fraction_abs": 2e-6,
            "extraction_fraction_abs": 1e-7,
        },
        scope="within-three-case development pilot; not held-out chemical generalization or search performance",
    )
    manifest = args.output / "manifest.json"
    if manifest.exists():
        if not args.resume or json.loads(manifest.read_text(encoding="utf-8")) != identity:
            parser.error("Existing experiment differs or resume was not requested; choose a new output directory.")
    else:
        save(manifest, identity)
        for path in identity["sources"]:
            if path.endswith(".py") and not path.startswith("lab_models"):
                target = args.output / "protocol_snapshot" / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / path).read_bytes())
    cache: dict[str, Any] = {}
    for artifact in (args.output / "numerical").glob("*.json"):
        bundle = json.loads(artifact.read_text(encoding="utf-8"))
        cache[bundle["contract_id"]] = bundle
    for repeat in range(args.repeats):
        for task in tasks:
            destination = args.output / "runs" / (task["task_id"] + f"-r{repeat}.json")
            if destination.exists():
                continue
            run = run_one(task, repeat, args.output, cache)
            save(destination, run)
            print(
                task["task_id"], repeat, run["outcome"], "cache=" + str(run.get("cache_hit", "not_called")), flush=True
            )
            if run["outcome"] == "provider_error":
                print("Provider failure retained; stopping batch without rule substitution.", flush=True)
                return
    unchanged = identity["sources"] == sources()
    check = args.output / "source_integrity.json"
    if not check.exists():
        save(check, dict(unchanged=unchanged, checked_utc=datetime.now(timezone.utc).isoformat()))  # noqa: UP017
    if not unchanged:
        raise RuntimeError("Source files changed while running the experiment")


if __name__ == "__main__":
    main()
