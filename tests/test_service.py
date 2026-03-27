from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from semantic_scholar_tool.core import SemanticScholarService  # noqa: E402


class RecordingClient:
    def __init__(self) -> None:
        self.headers: dict[str, str] = {}
        self.calls: list[tuple[str, str, dict[str, object] | None]] = []

    def get_json(
        self,
        url: str,
        params: dict[str, object] | None,
        *,
        max_retries: int,
        initial_backoff_ms: int,
        max_backoff_ms: int,
        jitter_factor: float,
    ) -> dict[str, object]:
        self.calls.append(("GET", url, params))
        return {"data": []}

    def post_json(
        self,
        url: str,
        payload: dict[str, object],
        *,
        params: dict[str, object] | None,
        max_retries: int,
        initial_backoff_ms: int,
        max_backoff_ms: int,
        jitter_factor: float,
    ) -> list[dict[str, object]]:
        self.calls.append(("POST", url, params))
        return []


class ServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = {
            "api": {
                "base_url": "https://api.semanticscholar.org",
                "graph_version": "v1",
                "api_key": "config-key",
                "email": "",
            },
            "rate_limit": {
                "max_retries": 5,
                "initial_backoff_ms": 1000,
                "max_backoff_ms": 30000,
                "jitter_factor": 0.2,
            },
            "paper": {
                "default_search_mode": "relevance",
                "default_fields": "paperId,title,url",
                "bulk_page_size": 100,
                "relevance_limit": 10,
            },
            "author": {
                "default_fields": "authorId,name,url",
            },
            "citation": {
                "default_citation_limit": 50,
            },
            "snippet": {
                "default_fields": "paper.title,snippet.text",
            },
            "output": {
                "default_format": "jsonl",
                "include_citation_context": False,
            },
        }

    def test_no_auth_disables_api_key_usage(self) -> None:
        service = SemanticScholarService(config=self.config, no_auth=True)

        self.assertEqual(service.auth_mode, "unauthenticated")
        self.assertNotIn("x-api-key", service.client.headers)

    def test_api_key_override_enables_authenticated_mode(self) -> None:
        service = SemanticScholarService(
            config=self.config, api_key_override="override-key"
        )

        self.assertEqual(service.auth_mode, "authenticated")
        self.assertEqual(service.client.headers["x-api-key"], "override-key")

    def test_search_papers_uses_default_fields_for_relevance_mode(self) -> None:
        client = RecordingClient()
        service = SemanticScholarService(config=self.config, client=client)

        service.search_papers(
            query="transformers",
            mode="relevance",
            fields=None,
            limit=5,
            year=None,
            token="ignored",
            sort="citationCount:desc",
            offset=10,
        )

        self.assertEqual(
            client.calls[0][1], "https://api.semanticscholar.org/graph/v1/paper/search"
        )
        params = client.calls[0][2]
        self.assertIsNotNone(params)
        assert params is not None
        self.assertEqual(params["fields"], "paperId,title,url")
        self.assertEqual(params["offset"], 10)
        self.assertIsNone(params["token"])
        self.assertIsNone(params["sort"])

    def test_search_papers_bulk_mode_uses_bulk_endpoint_and_token(self) -> None:
        client = RecordingClient()
        service = SemanticScholarService(config=self.config, client=client)

        service.search_papers(
            query="transformers",
            mode="bulk",
            fields="paperId,title,title",
            limit=100,
            year="2024-",
            token="next-page",
            sort="publicationDate:desc",
            offset=10,
        )

        self.assertEqual(
            client.calls[0][1],
            "https://api.semanticscholar.org/graph/v1/paper/search/bulk",
        )
        params = client.calls[0][2]
        self.assertIsNotNone(params)
        assert params is not None
        self.assertEqual(params["fields"], "paperId,title")
        self.assertIsNone(params["offset"])
        self.assertEqual(params["token"], "next-page")
        self.assertEqual(params["sort"], "publicationDate:desc")

    def test_fetch_author_uses_default_author_fields(self) -> None:
        client = RecordingClient()
        service = SemanticScholarService(config=self.config, client=client)

        service.fetch_author(author_id="123", fields=None)

        self.assertEqual(
            client.calls[0][1], "https://api.semanticscholar.org/graph/v1/author/123"
        )
        params = client.calls[0][2]
        self.assertIsNotNone(params)
        assert params is not None
        self.assertEqual(params["fields"], "authorId,name,url")


if __name__ == "__main__":
    unittest.main()
