"""Read-only consistency audit of requests, snapshots, cached artifacts and sources."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from paper_agent.reliability import TaskContract

ROOT = Path(__file__).resolve().parents[2]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(directory: Path) -> dict[str, Any]:
    directory = directory.resolve()
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    tasks = {t["task_id"]: t for t in manifest["tasks"]}
    errors: list[str] = []
    seen: set[tuple[str, int]] = set()
    fresh, cached, blocked = 0, 0, 0
    bundles: dict[str, Any] = {}
    for relative, expected in manifest["sources"].items():
        snapshot = directory / "protocol_snapshot" / relative
        if relative.startswith("lab_models"):
            target = ROOT / relative
        elif snapshot.exists():
            target = snapshot
        else:
            target = ROOT / relative
        if sha(target) != expected:
            errors.append("source/snapshot mismatch: " + relative)
    for path in sorted((directory / "runs").glob("*.json")):
        run = json.loads(path.read_text(encoding="utf-8"))
        key = run["task_id"], run["repeat"]
        if key in seen or key[0] not in tasks or not 0 <= key[1] < manifest["repeats"]:
            errors.append("invalid or duplicate run identity: " + path.name)
        seen.add(key)
        if run["request"] != tasks[key[0]]["prompt"]:
            errors.append("request differs from manifest: " + path.name)
        calls = run["provider_calls"]
        if not calls or json.loads(calls[0]["messages"][1]["content"]) != {"request": run["request"]}:
            errors.append("actual provider input differs: " + path.name)
        if any(c.get("http_status") != 200 or c.get("finish_reason") != "stop" for c in calls):
            errors.append("provider error/truncation: " + path.name)
        tools = [t for t in run["trace"] if t["step"] == "tool"]
        if run["kind"] != "equivalent":
            blocked += not tools
            if tools:
                errors.append("invalid input entered a numerical tool: " + path.name)
        if not tools:
            continue
        artifact = (directory / run["numerical_artifact"]).resolve()
        artifact.relative_to(directory)  # Reject escaping paths, even for reads.
        if sha(artifact) != run["numerical_sha256"]:
            errors.append("numerical artifact was modified: " + path.name)
        bundle = json.loads(artifact.read_text(encoding="utf-8"))
        bundles[bundle["protocol"]] = bundle
        contract = TaskContract.model_validate(run["compiled"]["contract"])
        if contract.identity() != bundle["contract_id"] or run["final"] != bundle["final"]:
            errors.append("cache/contract/output mismatch: " + path.name)
        expected_origin = "cached_frozen_protocol_result" if run["cache_hit"] else "fresh_frozen_protocol_execution"
        if tools[0]["origin"] != expected_origin or len(tools) != 2:
            errors.append("incorrect execution origin or tool count: " + path.name)
        cached += run["cache_hit"]
        fresh += not run["cache_hit"]
        if any(r["status"] != "valid" or not r["numerical_checks"]["passed"] for r in bundle["observations"]):
            errors.append("unvalidated solver output: " + path.name)
        if "raw_report" in run and json.loads(calls[-1]["response"]) != run["raw_report"]:
            errors.append("recorded report differs from provider response: " + path.name)
    for case, bundle in bundles.items():
        provenance = bundle["provenance"]
        checkpoint = ROOT / "lab_models/ThermoFormer" / provenance["checkpoint"]
        if sha(checkpoint) != provenance["checkpoint_sha256"]:
            errors.append("checkpoint mismatch: " + case)
        if not bundle["paper_agreement"]["passed"]:
            errors.append("paper results changed: " + case)
        if "ggnn39" not in provenance["python"].lower():
            errors.append("wrong numerical environment: " + case)
    complete = len(seen) == len(tasks) * manifest["repeats"]
    if not complete:
        errors.append("scheduled runs are incomplete")
    return dict(
        passed=not errors,
        complete=complete,
        runs=len(seen),
        fresh_protocol_executions=fresh,
        cached_protocol_executions=cached,
        invalid_requests_blocked=blocked,
        scientific_protocols=sorted(bundles),
        errors=errors,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.input)
    (args.input / "audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
