"""Portable paths for reproducible experiment artifacts."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
