"""Portable paths for reproducible experiment artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEXT_ARTIFACT_SUFFIXES = {".csv", ".json", ".md", ".txt"}


def artifact_sha256(path: Path) -> str:
    """Hash text after LF normalization and binary artifacts byte-for-byte."""

    payload = path.read_bytes()
    if path.suffix.lower() in TEXT_ARTIFACT_SUFFIXES:
        text = payload.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        payload = text.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def portable_artifact_path(path: Path, root: Path = PROJECT_ROOT) -> str:
    """Use repository-relative POSIX paths when an artifact lives in the project."""

    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def resolve_artifact_path(value: str, root: Path = PROJECT_ROOT) -> Path:
    """Resolve the portable schema while retaining old absolute-manifest support."""

    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()
