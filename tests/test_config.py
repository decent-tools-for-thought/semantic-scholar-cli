from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from semantic_scholar_tool import config as ss_config  # noqa: E402


class ConfigTests(unittest.TestCase):
    def test_save_and_load_config_preserve_types_and_escape_strings(self) -> None:
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_path = config_dir / "config.toml"
            with (
                mock.patch.object(ss_config, "CONFIG_DIR", config_dir),
                mock.patch.object(ss_config, "CONFIG_PATH", config_path),
            ):
                updated = ss_config.load_config()
                updated["api"]["email"] = 'ada"@example.test'
                updated["rate_limit"]["max_retries"] = 9
                updated["output"]["include_citation_context"] = True
                ss_config.save_config(updated)

                reloaded = ss_config.load_config()

        self.assertEqual(reloaded["api"]["email"], 'ada"@example.test')
        self.assertEqual(reloaded["rate_limit"]["max_retries"], 9)
        self.assertTrue(reloaded["output"]["include_citation_context"])

    def test_reset_config_rewrites_defaults(self) -> None:
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_path = config_dir / "config.toml"
            with (
                mock.patch.object(ss_config, "CONFIG_DIR", config_dir),
                mock.patch.object(ss_config, "CONFIG_PATH", config_path),
            ):
                mutated = ss_config.load_config()
                mutated["paper"]["default_fields"] = "paperId"
                ss_config.save_config(mutated)

                reset = ss_config.reset_config()

        self.assertEqual(reset, ss_config.DEFAULT_CONFIG)


if __name__ == "__main__":
    unittest.main()
