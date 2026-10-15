"""Validate every published S8 panel against its final interaction records, offline."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import median
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.benchmarks.paper_agent.agent_publication_figure import collect  # noqa: E402
from scripts.benchmarks.paper_agent.audit_reliability import audit  # noqa: E402


def verify(directory: Path) -> dict[str, Any]:
    """Check complete source records and the paper's stated counts and costs."""
    source = directory / "results/reliability-20260926-v3"
    intervention = directory / "results/evidence_interventions"
    checked = audit(source)
    if not checked["passed"]:
        raise ValueError(checked["errors"])
    data = collect(source, intervention)
    checks = {
        "equivalent_requests": sum(row["passed"] for row in data["equivalence"]) == 45,
        "schema_blocks": sum(row["schema_blocked"] for row in data["gates"]) == 18,
        "contract_blocks": sum(row["contract_blocked"] for row in data["gates"]) == 27,
        "recovery": all(
            row["resolved"] == row["reused"] == row["reported"] == row["n"]
            for row in data["recovery"]
        )
        and sum(row["n"] for row in data["recovery"]) == 27,
        "evidence_decisions": sum(row["passed"] for row in data["actions"]) == 36,
    }
    medians = {
        kind: median(row["tokens"] for row in data["costs"] if row["experiment"] == kind)
        for kind in {row["experiment"] for row in data["costs"]}
    }
    checks["token_medians"] = sorted(medians.values()) == [508, 2750]
    if not all(checks.values()):
        raise ValueError({key: value for key, value in checks.items() if not value})
    return {"passed": True, "checks": checks, "token_medians": medians, "reliability": checked}


if __name__ == "__main__":
    print(
        json.dumps(
            verify(ROOT / "experiments/supporting_information/s8_agent_reliability"), indent=2
        )
    )
