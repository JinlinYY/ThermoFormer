"""Condition-bound execution memory. Never a source of numerical parameters."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path

from schemas.domain import TaskManifest
from schemas.evidence import EvidenceState


def task_fingerprint(task: TaskManifest) -> str:
    snapshot = task.model_dump(mode="json", exclude={"task_id", "original_question", "requested_outputs", "assumptions"})
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()


class ExperienceStore:
    """Store immutable observations; recall only within the same conversation and exact conditions."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(os.getenv("THERMO_EXPERIENCE_DB", "data/agent_experience.sqlite3"))

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=5)
        connection.execute("CREATE TABLE IF NOT EXISTS experiences (id TEXT PRIMARY KEY, session TEXT, fingerprint TEXT, payload TEXT)")
        return connection

    def save(self, session: str, state: EvidenceState) -> str:
        payload = state.model_dump_json()
        identifier = hashlib.sha256((session + payload).encode()).hexdigest()
        with self._connect() as connection:
            connection.execute("INSERT OR IGNORE INTO experiences VALUES (?, ?, ?, ?)",
                               (identifier, session, state.task_fingerprint, payload))
        return identifier

    def recall(self, session: str, fingerprint: str) -> list[tuple[str, EvidenceState]]:
        if not self.path.exists():
            return []
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, payload FROM experiences WHERE session=? AND fingerprint=? ORDER BY rowid DESC LIMIT 3",
                (session, fingerprint),
            ).fetchall()
        return [(str(identifier), EvidenceState.model_validate_json(payload)) for identifier, payload in rows]

    def export(self, destination: Path) -> int:
        if not self.path.exists():
            destination.write_text("", encoding="utf-8")
            return 0
        with self._connect() as connection:
            rows = connection.execute("SELECT payload FROM experiences ORDER BY rowid").fetchall()
        destination.write_text("\n".join(str(row[0]) for row in rows) + "\n", encoding="utf-8")
        return len(rows)
