from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from semantic_scholar_tool.core import (  # noqa: E402
    normalize_dataset_diff_list,
    normalize_dataset_metadata,
    normalize_release_metadata,
    normalize_author,
    normalize_edge,
    normalize_paper,
    render_output,
    resolve_paper_identifier,
)


class SemanticCoreTests(unittest.TestCase):
    def test_resolve_paper_identifier_prefixes_external_ids(self) -> None:
        self.assertEqual(resolve_paper_identifier(None, doi="doi:10.1/x"), "DOI:10.1/x")
        self.assertEqual(resolve_paper_identifier(None, pmid="123"), "PMID:123")
        self.assertEqual(
            resolve_paper_identifier(None, arxiv="arXiv:1234.5678"), "ARXIV:1234.5678"
        )
        self.assertEqual(
            resolve_paper_identifier(None, url="https://example.test/paper"),
            "URL:https://example.test/paper",
        )

    def test_normalize_paper_maps_external_ids(self) -> None:
        record = {
            "paperId": "abc",
            "corpusId": 7,
            "title": "Paper",
            "authors": [{"authorId": "1", "name": "Ada"}],
            "externalIds": {
                "DOI": "10.1/x",
                "PubMed": "123",
                "PubMedCentral": "PMC7",
                "ArXiv": "1234.5678",
            },
            "url": "https://example.test/paper",
        }
        normalized = normalize_paper(
            record, auth_mode="unauthenticated", fields_requested="paperId,title"
        )
        self.assertEqual(normalized["id"]["doi"], "10.1/x")
        self.assertEqual(normalized["id"]["pmcId"], "PMC7")
        self.assertEqual(normalized["id"]["arxiv"], "1234.5678")
        self.assertEqual(normalized["authors"][0]["name"], "Ada")

    def test_normalize_author_coerces_numeric_metrics(self) -> None:
        record = {
            "authorId": "42",
            "name": "Ada Lovelace",
            "citationCount": "12",
            "hIndex": "4",
            "paperCount": "2",
        }
        normalized = normalize_author(
            record, auth_mode="authenticated", fields_requested="authorId,name"
        )
        self.assertEqual(normalized["citationCount"], 12)
        self.assertEqual(normalized["hIndex"], 4)
        self.assertEqual(normalized["paperCount"], 2)

    def test_normalize_edge_wraps_citing_or_cited_paper(self) -> None:
        edge = {
            "contexts": ["cited in introduction"],
            "intents": ["background"],
            "isInfluential": True,
            "citingPaper": {
                "paperId": "abc",
                "title": "Paper",
                "url": "https://example.test/paper",
            },
        }
        normalized = normalize_edge(
            edge,
            auth_mode="unauthenticated",
            fields_requested="paperId,title",
            edge_kind="citations",
        )
        self.assertTrue(normalized["isInfluential"])
        self.assertEqual(normalized["paper"]["id"]["s2Id"], "abc")

    def test_render_output_accepts_items_dict_for_jsonl(self) -> None:
        payload = {"items": [{"title": "Paper A", "url": "https://example.test/a"}]}
        output = render_output(payload, "jsonl")
        self.assertIn('"title": "Paper A"', output)

    def test_normalize_release_metadata_maps_dataset_summaries(self) -> None:
        record = {
            "release_id": "2024-01-01",
            "README": "release readme",
            "datasets": [
                {
                    "name": "papers",
                    "description": "Core paper metadata",
                    "README": "dataset readme",
                }
            ],
        }
        normalized = normalize_release_metadata(record)
        self.assertEqual(normalized["releaseId"], "2024-01-01")
        self.assertEqual(normalized["datasets"][0]["name"], "papers")

    def test_normalize_dataset_metadata_preserves_files(self) -> None:
        record = {
            "name": "abstracts",
            "description": "Paper abstracts",
            "README": "dataset docs",
            "files": ["https://example.test/file1.gz"],
        }
        normalized = normalize_dataset_metadata(record, release_id="latest")
        self.assertEqual(normalized["releaseId"], "latest")
        self.assertEqual(normalized["files"][0], "https://example.test/file1.gz")

    def test_normalize_dataset_diff_list_maps_diff_files(self) -> None:
        record = {
            "dataset": "papers",
            "start_release": "2024-01-01",
            "end_release": "2024-01-08",
            "diffs": [
                {
                    "from_release": "2024-01-01",
                    "to_release": "2024-01-08",
                    "update_files": ["https://example.test/update.gz"],
                    "delete_files": ["https://example.test/delete.gz"],
                }
            ],
        }
        normalized = normalize_dataset_diff_list(record)
        self.assertEqual(normalized["dataset"], "papers")
        self.assertEqual(
            normalized["diffs"][0]["updateFiles"][0], "https://example.test/update.gz"
        )

    def test_render_output_formats_dataset_releases_in_text(self) -> None:
        payload = {"items": [{"releaseId": "2024-01-01"}, {"releaseId": "2024-01-08"}]}
        output = render_output(payload, "text")
        self.assertIn("2024-01-01", output)


if __name__ == "__main__":
    unittest.main()
