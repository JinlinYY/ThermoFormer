import io
from pathlib import Path
import re
import tokenize
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HAN = re.compile(r"[\u3400-\u9fff]")


class RepositoryLayoutTests(unittest.TestCase):
    def test_release_dataset_contains_only_two_workbooks(self) -> None:
        files = sorted(
            path.relative_to(PROJECT_ROOT / "dataset").as_posix()
            for path in (PROJECT_ROOT / "dataset").rglob("*")
            if path.is_file()
        )
        self.assertEqual(
            files,
            ["binary_vle_english.xlsx", "ternary_vle_english.xlsx"],
        )

    def test_active_source_paths_are_ascii(self) -> None:
        for root_name in ("src", "scripts", "tests", "configs", "experiments"):
            for path in (PROJECT_ROOT / root_name).rglob("*"):
                relative = path.relative_to(PROJECT_ROOT).as_posix()
                self.assertTrue(relative.isascii(), relative)

    def test_active_python_comments_are_english(self) -> None:
        for root_name in ("src", "scripts", "tests"):
            for path in (PROJECT_ROOT / root_name).rglob("*.py"):
                source = path.read_text(encoding="utf-8-sig")
                tokens = tokenize.generate_tokens(io.StringIO(source).readline)
                for token in tokens:
                    if token.type == tokenize.COMMENT:
                        self.assertIsNone(
                            HAN.search(token.string),
                            f"Non-English comment in {path.relative_to(PROJECT_ROOT)}:{token.start[0]}",
                        )

    def test_legacy_code_is_isolated_from_active_imports(self) -> None:
        self.assertTrue((PROJECT_ROOT / "archive" / "legacy_code" / "README.md").is_file())
        for root_name in ("src", "scripts"):
            for path in (PROJECT_ROOT / root_name).rglob("*.py"):
                source = path.read_text(encoding="utf-8-sig")
                self.assertNotIn("archive.legacy_code", source)
                self.assertNotIn("archive/legacy_code", source)

    def test_paper_navigation_declares_incomplete_studies(self) -> None:
        paper_map = (PROJECT_ROOT / "experiments" / "paper" / "README.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Machine-learning comparison", paper_map)
        self.assertIn("Autonomous separation design", paper_map)
        self.assertIn("Not evaluated", paper_map)


if __name__ == "__main__":
    unittest.main()
