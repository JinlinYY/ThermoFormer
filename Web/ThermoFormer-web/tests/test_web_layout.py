"""Checks for the files that make the web release runnable and reviewable."""

from pathlib import Path


WEB_ROOT = Path(__file__).parents[1]


def test_psmi_style_web_layout_is_complete() -> None:
    for directory in ("backend", "frontend", "scripts", "tests"):
        assert (WEB_ROOT / directory).is_dir()
    for path in (
        WEB_ROOT / "backend" / "main.py",
        WEB_ROOT / "backend" / "requirements.txt",
        WEB_ROOT / "frontend" / "package.json",
        WEB_ROOT / "frontend" / "src" / "app" / "page.tsx",
        WEB_ROOT / "scripts" / "run_backend.ps1",
        WEB_ROOT / "scripts" / "run_frontend.ps1",
    ):
        assert path.is_file(), path


def test_generated_or_secret_artifacts_are_not_copied() -> None:
    for path in (
        WEB_ROOT / "frontend" / "node_modules",
        WEB_ROOT / "frontend" / ".next",
        WEB_ROOT / "backend" / "conversation_memory.db",
        WEB_ROOT / "backend" / ".env",
    ):
        assert not path.exists(), path
