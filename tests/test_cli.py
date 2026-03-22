from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from semantic_scholar_tool import cli as ss_cli  # noqa: E402
from semantic_scholar_tool import config as ss_config  # noqa: E402


class FakeService:
    def search_papers(self, **_: object) -> dict[str, object]:
        return {
            "items": [
                {
                    "title": "Paper A",
                    "url": "https://example.test/paper-a",
                }
            ],
            "meta": {},
        }

    def fetch_author(self, **_: object) -> dict[str, object]:
        return {
            "name": "Ada Lovelace",
            "url": "https://example.test/authors/ada",
            "hIndex": 42,
        }

    def dataset_metadata(self, **_: object) -> dict[str, object]:
        return {
            "backend": "semanticscholar",
            "api": "datasets/v1",
            "releaseId": "latest",
            "name": "papers",
            "README": "dataset readme",
            "files": ["https://example.test/file-1.gz"],
        }


class CliTests(unittest.TestCase):
    def test_config_set_show_and_reset_commands(self) -> None:
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_path = config_dir / "config.toml"
            stdout = StringIO()
            with (
                mock.patch.object(ss_config, "CONFIG_DIR", config_dir),
                mock.patch.object(ss_config, "CONFIG_PATH", config_path),
                mock.patch.object(ss_cli, "load_config", ss_config.load_config),
                mock.patch.object(ss_cli, "save_config", ss_config.save_config),
                mock.patch.object(ss_cli, "reset_config", ss_config.reset_config),
                redirect_stdout(stdout),
            ):
                self.assertEqual(
                    ss_cli.main(["config", "set", "include-citation-context", "true"]),
                    0,
                )
                self.assertTrue(
                    ss_config.load_config()["output"]["include_citation_context"]
                )

                stdout.seek(0)
                stdout.truncate(0)
                self.assertEqual(ss_cli.main(["config", "show"]), 0)
                self.assertIn('"include_citation_context": true', stdout.getvalue())

                stdout.seek(0)
                stdout.truncate(0)
                self.assertEqual(ss_cli.main(["config", "reset"]), 0)
                self.assertFalse(
                    ss_config.load_config()["output"]["include_citation_context"]
                )

    def test_paper_search_renders_jsonl_output(self) -> None:
        stdout = StringIO()
        with (
            mock.patch.object(
                ss_cli, "load_config", return_value=ss_config.DEFAULT_CONFIG
            ),
            mock.patch.object(ss_cli, "_service", return_value=FakeService()),
            redirect_stdout(stdout),
        ):
            exit_code = ss_cli.main(
                ["paper", "search", "transformers", "--format", "jsonl"]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            stdout.getvalue().strip(),
            '{"title": "Paper A", "url": "https://example.test/paper-a"}',
        )

    def test_author_fetch_renders_text_output(self) -> None:
        stdout = StringIO()
        with (
            mock.patch.object(
                ss_cli, "load_config", return_value=ss_config.DEFAULT_CONFIG
            ),
            mock.patch.object(ss_cli, "_service", return_value=FakeService()),
            redirect_stdout(stdout),
        ):
            exit_code = ss_cli.main(["author", "fetch", "123", "--format", "text"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Ada Lovelace", stdout.getvalue())
        self.assertIn("hIndex=42", stdout.getvalue())

    def test_datasets_files_renders_jsonl_urls(self) -> None:
        stdout = StringIO()
        with (
            mock.patch.object(
                ss_cli, "load_config", return_value=ss_config.DEFAULT_CONFIG
            ),
            mock.patch.object(ss_cli, "_service", return_value=FakeService()),
            redirect_stdout(stdout),
        ):
            exit_code = ss_cli.main(
                ["datasets", "files", "papers", "--format", "jsonl"]
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            stdout.getvalue().strip(),
            '{"url": "https://example.test/file-1.gz"}',
        )

    def test_datasets_readme_renders_text_block(self) -> None:
        stdout = StringIO()
        with (
            mock.patch.object(
                ss_cli, "load_config", return_value=ss_config.DEFAULT_CONFIG
            ),
            mock.patch.object(ss_cli, "_service", return_value=FakeService()),
            redirect_stdout(stdout),
        ):
            exit_code = ss_cli.main(
                ["datasets", "readme", "papers", "--format", "text"]
            )

        self.assertEqual(exit_code, 0)
        self.assertIn("release=latest", stdout.getvalue())
        self.assertIn("dataset readme", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
