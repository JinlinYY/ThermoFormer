import hashlib
import io
import json
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
        for root_name in ("analysis", "src", "scripts", "tests", "configs", "experiments"):
            for path in (PROJECT_ROOT / root_name).rglob("*"):
                relative = path.relative_to(PROJECT_ROOT).as_posix()
                self.assertTrue(relative.isascii(), relative)

    def test_active_python_comments_are_english(self) -> None:
        for root_name in ("analysis", "src", "scripts", "tests"):
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
        paper_map = (PROJECT_ROOT / "docs" / "paper_code_map.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Machine-learning and thermodynamic-model comparison", paper_map)
        self.assertIn("Autonomous separation design", paper_map)
        self.assertIn("not evaluated", paper_map.lower())

    def test_active_experiments_match_manuscript_results_sections(self) -> None:
        active = {
            path.name
            for path in (PROJECT_ROOT / "experiments").iterdir()
            if path.is_dir() and any(path.rglob("*"))
        }
        self.assertEqual(
            active,
            {
                "ablations",
                "comparisons",
                "interpretability",
                "predictive_performance",
                "separation_design",
            },
        )
        representation_variants = {
            path.name
            for path in (
                PROJECT_ROOT / "experiments" / "ablations" / "molecular_representation"
            ).iterdir()
            if path.is_dir()
        }
        self.assertEqual(
            representation_variants,
            {
                "unimol_v2_only",
                "rdkit_only",
                "functional_groups_only",
                "rdkit_unimol",
                "full_three_view",
            },
        )
        interaction_variants = {
            path.name
            for path in (
                PROJECT_ROOT / "experiments" / "ablations" / "interaction_architecture"
            ).iterdir()
            if path.is_dir()
        }
        self.assertEqual(
            interaction_variants,
            {
                "vanilla_transformer",
                "chemical_interaction_bias",
                "context_pair_without_attention_bias",
            },
        )

    def test_manuscript_figures_have_single_active_sources(self) -> None:
        dataset_figures = PROJECT_ROOT / "analysis" / "dataset_distribution" / "figures"
        self.assertEqual(
            {path.name for path in dataset_figures.glob("Figure_dataset_overview*.png")},
            {"Figure_dataset_overview_v3.png"},
        )
        figure_1 = dataset_figures / "Figure_dataset_overview_v3.png"
        figure_1_source = json.loads(
            (dataset_figures / "Figure_dataset_overview_v3.source.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            hashlib.sha256(figure_1.read_bytes()).hexdigest(),
            figure_1_source["artifact_sha256"],
        )
        self.assertTrue(figure_1_source["rgb_pixels_match_manuscript"])
        figure_2_root = PROJECT_ROOT / "analysis" / "manuscript_figures"
        figure_2 = figure_2_root / "Figure_2_interpretability.png"
        source = json.loads(
            (figure_2_root / "Figure_2_interpretability.source.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            hashlib.sha256(figure_2.read_bytes()).hexdigest(),
            source["artifact_sha256"],
        )
        self.assertEqual(source["dimensions_pixels"], [3157, 2878])

    def test_active_implementation_uses_manuscript_subpackages(self) -> None:
        expected = {
            "data",
            "evaluation",
            "features",
            "interpretability",
            "models",
            "protocols",
            "reporting",
            "thermodynamics",
            "training",
        }
        package_root = PROJECT_ROOT / "src" / "thermoformer"
        actual = {path.name for path in package_root.iterdir() if path.is_dir()}
        self.assertTrue(expected.issubset(actual))
        for name in expected:
            self.assertTrue((package_root / name / "__init__.py").is_file(), name)

    def test_manuscript_configs_resolve(self) -> None:
        from src.thermoformer.configuration import load_experiment_config

        config_root = PROJECT_ROOT / "configs"
        paths = [
            config_root / "model" / "c1_three_view_vanilla.yaml",
            config_root / "training" / "supervised.yaml",
            config_root / "training" / "fugacity_finetuning.yaml",
            config_root / "protocols" / "overall_binary_ternary.yaml",
        ]
        configs = [load_experiment_config(path) for path in paths]
        self.assertTrue(all(config.encoder.representation == "multiview" for config in configs))
        self.assertFalse(configs[-1].encoder.chemical_attention_bias)
        self.assertEqual(configs[-1].training.epochs_physics, 10)
        self.assertEqual(configs[-1].protocol.registered_splits, ("overall_binary_ternary",))
        self.assertEqual(configs[-1].protocol.seeds, (0, 1, 2, 3, 4))


if __name__ == "__main__":
    unittest.main()
