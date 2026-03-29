from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Any, Protocol
from urllib.parse import quote

from .config import load_config
from .http import HttpClient


class SemanticScholarHttpClient(Protocol):
    headers: dict[str, str]

    def get_json(
        self,
        url: str,
        params: dict[str, Any] | None,
        *,
        max_retries: int,
        initial_backoff_ms: int,
        max_backoff_ms: int,
        jitter_factor: float,
    ) -> Any: ...

    def post_json(
        self,
        url: str,
        payload: dict[str, Any],
        *,
        params: dict[str, Any] | None,
        max_retries: int,
        initial_backoff_ms: int,
        max_backoff_ms: int,
        jitter_factor: float,
    ) -> Any: ...


PAPER_FIELD_CATALOG = [
    "paperId",
    "corpusId",
    "externalIds",
    "url",
    "title",
    "abstract",
    "venue",
    "publicationVenue",
    "year",
    "referenceCount",
    "citationCount",
    "influentialCitationCount",
    "isOpenAccess",
    "openAccessPdf",
    "fieldsOfStudy",
    "s2FieldsOfStudy",
    "publicationTypes",
    "publicationDate",
    "journal",
    "citationStyles",
    "authors",
    "citations",
    "references",
    "embedding",
    "tldr",
    "textAvailability",
]

AUTHOR_FIELD_CATALOG = [
    "authorId",
    "externalIds",
    "url",
    "name",
    "affiliations",
    "homepage",
    "paperCount",
    "citationCount",
    "hIndex",
    "papers",
]

DATASET_COMMAND_CATALOG = [
    "releases",
    "release",
    "latest",
    "dataset",
    "files",
    "readme",
    "diffs",
]


def _now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _split_fields(value: str | None, default: str) -> str:
    if not value:
        return default
    fields = [field.strip() for field in value.split(",") if field.strip()]
    return ",".join(dict.fromkeys(fields))


def _append_fields(base_fields: str, extra_fields: list[str]) -> str:
    merged = [field for field in base_fields.split(",") if field]
    merged.extend(extra_fields)
    return ",".join(dict.fromkeys(merged))


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_paper(
    record: dict[str, Any], *, auth_mode: str, fields_requested: str
) -> dict[str, Any]:
    external_ids = record.get("externalIds") or {}
    open_access_pdf = record.get("openAccessPdf") or {}
    status = open_access_pdf.get("status")
    paper = {
        "backend": "semanticscholar",
        "id": {
            "s2Id": record.get("paperId"),
            "corpusId": str(record["corpusId"])
            if record.get("corpusId") is not None
            else None,
            "doi": external_ids.get("DOI"),
            "pmid": external_ids.get("PubMed"),
            "pmcId": external_ids.get("PubMedCentral"),
            "arxiv": external_ids.get("ArXiv"),
            "acl": external_ids.get("ACL"),
            "mag": external_ids.get("MAG"),
        },
        "title": record.get("title"),
        "authors": [
            {"authorId": author.get("authorId"), "name": author.get("name")}
            for author in record.get("authors") or []
        ],
        "publishedDate": record.get("publicationDate"),
        "year": record.get("year"),
        "abstract": record.get("abstract"),
        "url": record.get("url"),
        "venue": record.get("venue"),
        "citationCount": record.get("citationCount"),
        "referenceCount": record.get("referenceCount"),
        "influentialCitationCount": record.get("influentialCitationCount"),
        "isOpenAccess": record.get("isOpenAccess"),
        "fieldsOfStudy": record.get("fieldsOfStudy") or [],
        "publicationTypes": record.get("publicationTypes") or [],
        "journal": record.get("journal"),
        "tldr": record.get("tldr"),
        "textAvailability": record.get("textAvailability"),
        "rights": {
            "license": record.get("license") or open_access_pdf.get("license"),
            "s2DataLicense": None,
        },
        "openAccessPdf": {
            "url": open_access_pdf.get("url"),
            "status": status,
            "license": open_access_pdf.get("license"),
            "isLocked": True if status == "LOCKED" else False if status else None,
        },
        "provenance": {
            "retrievedAt": _now(),
            "apiVersion": "graph/v1",
            "authMode": auth_mode,
            "fieldsRequested": [
                field for field in fields_requested.split(",") if field
            ],
        },
    }
    if "matchScore" in record:
        paper["matchScore"] = record.get("matchScore")
    return paper


def normalize_author(
    record: dict[str, Any], *, auth_mode: str, fields_requested: str
) -> dict[str, Any]:
    papers = []
    for paper in record.get("papers") or []:
        if isinstance(paper, dict):
            papers.append(
                normalize_paper(
                    paper, auth_mode=auth_mode, fields_requested="paperId,title,year"
                )
            )
    return {
        "backend": "semanticscholar",
        "id": {"authorId": record.get("authorId")},
        "externalIds": record.get("externalIds") or {},
        "name": record.get("name"),
        "url": record.get("url"),
        "homepage": record.get("homepage"),
        "affiliations": [
            {"institution": aff, "position": None}
            for aff in record.get("affiliations") or []
        ],
        "paperCount": _to_int(record.get("paperCount")),
        "citationCount": _to_int(record.get("citationCount")),
        "hIndex": _to_int(record.get("hIndex")),
        "papers": papers,
        "provenance": {
            "retrievedAt": _now(),
            "apiVersion": "graph/v1",
            "authMode": auth_mode,
            "fieldsRequested": [
                field for field in fields_requested.split(",") if field
            ],
        },
    }


def normalize_edge(
    edge: dict[str, Any], *, auth_mode: str, fields_requested: str, edge_kind: str
) -> dict[str, Any]:
    key = "citingPaper" if edge_kind == "citations" else "citedPaper"
    return {
        "contexts": edge.get("contexts") or [],
        "intents": edge.get("intents") or [],
        "contextsWithIntent": edge.get("contextsWithIntent") or [],
        "isInfluential": edge.get("isInfluential"),
        "paper": normalize_paper(
            edge.get(key) or {}, auth_mode=auth_mode, fields_requested=fields_requested
        ),
    }


def normalize_autocomplete_match(match: dict[str, Any]) -> dict[str, Any]:
    return {
        "backend": "semanticscholar",
        "id": match.get("id"),
        "title": match.get("title"),
        "authorsYear": match.get("authorsYear"),
    }


def normalize_snippet_hit(
    hit: dict[str, Any], *, auth_mode: str, fields_requested: str
) -> dict[str, Any]:
    paper = hit.get("paper") or {}
    return {
        "backend": "semanticscholar",
        "score": hit.get("score"),
        "snippet": hit.get("snippet") or {},
        "paper": {
            "corpusId": str(paper["corpusId"])
            if paper.get("corpusId") is not None
            else None,
            "title": paper.get("title"),
            "authors": [
                {"authorId": author.get("authorId"), "name": author.get("name")}
                for author in paper.get("authors") or []
            ],
            "openAccessInfo": paper.get("openAccessInfo") or {},
        },
        "provenance": {
            "retrievedAt": _now(),
            "apiVersion": "graph/v1",
            "authMode": auth_mode,
            "fieldsRequested": [
                field for field in fields_requested.split(",") if field
            ],
        },
    }


def normalize_release_metadata(record: dict[str, Any]) -> dict[str, Any]:
    datasets = []
    for dataset in record.get("datasets") or []:
        datasets.append(
            {
                "name": dataset.get("name"),
                "description": dataset.get("description"),
                "README": dataset.get("README"),
            }
        )
    return {
        "backend": "semanticscholar",
        "api": "datasets/v1",
        "releaseId": record.get("release_id"),
        "README": record.get("README"),
        "datasets": datasets,
        "provenance": {"retrievedAt": _now()},
    }


def normalize_dataset_metadata(
    record: dict[str, Any], *, release_id: str
) -> dict[str, Any]:
    return {
        "backend": "semanticscholar",
        "api": "datasets/v1",
        "releaseId": release_id,
        "name": record.get("name"),
        "description": record.get("description"),
        "README": record.get("README"),
        "files": record.get("files") or [],
        "provenance": {"retrievedAt": _now()},
    }


def normalize_dataset_diff_list(record: dict[str, Any]) -> dict[str, Any]:
    diffs = []
    for diff in record.get("diffs") or []:
        diffs.append(
            {
                "fromRelease": diff.get("from_release"),
                "toRelease": diff.get("to_release"),
                "updateFiles": diff.get("update_files") or [],
                "deleteFiles": diff.get("delete_files") or [],
            }
        )
    return {
        "backend": "semanticscholar",
        "api": "datasets/v1",
        "dataset": record.get("dataset"),
        "startRelease": record.get("start_release"),
        "endRelease": record.get("end_release"),
        "diffs": diffs,
        "provenance": {"retrievedAt": _now()},
    }


def resolve_paper_identifier(
    positional: str | None,
    *,
    s2_id: str | None = None,
    doi: str | None = None,
    corpus_id: str | None = None,
    pmid: str | None = None,
    pmc_id: str | None = None,
    arxiv: str | None = None,
    mag: str | None = None,
    acl: str | None = None,
    url: str | None = None,
) -> str:
    values = [positional, s2_id, doi, corpus_id, pmid, pmc_id, arxiv, mag, acl, url]
    if sum(bool(value) for value in values) != 1:
        raise ValueError("Provide exactly one paper identifier")
    if positional:
        return positional
    if s2_id:
        return s2_id
    if doi:
        return f"DOI:{doi.removeprefix('doi:')}"
    if corpus_id:
        return f"CorpusId:{corpus_id}"
    if pmid:
        return f"PMID:{pmid}"
    if pmc_id:
        return f"PMCID:{pmc_id}"
    if arxiv:
        return f"ARXIV:{arxiv.removeprefix('arXiv:').removeprefix('ARXIV:')}"
    if mag:
        return f"MAG:{mag}"
    if acl:
        return f"ACL:{acl}"
    return f"URL:{url}"


class SemanticScholarService:
    def __init__(
        self,
        config: dict | None = None,
        client: SemanticScholarHttpClient | None = None,
        no_auth: bool = False,
        api_key_override: str | None = None,
    ) -> None:
        self.config = config or load_config()
        api_key = (
            ""
            if no_auth
            else (
                api_key_override
                if api_key_override is not None
                else self.config["api"].get("api_key", "")
            )
        )
        headers = {"User-Agent": "semantic-scholar-cli/0.1.0"}
        if api_key:
            headers["x-api-key"] = api_key
            self.auth_mode = "authenticated"
        else:
            self.auth_mode = "unauthenticated"
        self.client = client or HttpClient(headers=headers)
        self.base_url = self.config["api"]["base_url"].rstrip("/")

    def _request(self, path: str, params: dict[str, Any] | None = None) -> Any:
        rate = self.config["rate_limit"]
        return self.client.get_json(
            f"{self.base_url}{path}",
            params,
            max_retries=rate["max_retries"],
            initial_backoff_ms=rate["initial_backoff_ms"],
            max_backoff_ms=rate["max_backoff_ms"],
            jitter_factor=rate["jitter_factor"],
        )

    def _post(
        self, path: str, payload: dict[str, Any], params: dict[str, Any] | None = None
    ) -> Any:
        rate = self.config["rate_limit"]
        return self.client.post_json(
            f"{self.base_url}{path}",
            payload,
            params=params,
            max_retries=rate["max_retries"],
            initial_backoff_ms=rate["initial_backoff_ms"],
            max_backoff_ms=rate["max_backoff_ms"],
            jitter_factor=rate["jitter_factor"],
        )

    def search_papers(
        self,
        *,
        query: str,
        mode: str,
        fields: str | None,
        limit: int | None,
        year: str | None,
        token: str | None,
        sort: str | None,
        offset: int | None = None,
        publication_date_or_year: str | None = None,
        publication_types: str | None = None,
        open_access_pdf: bool | None = None,
        min_citation_count: int | None = None,
        venue: str | None = None,
        fields_of_study: str | None = None,
    ) -> dict[str, Any]:
        field_list = _split_fields(fields, self.config["paper"]["default_fields"])
        endpoint = (
            "/graph/v1/paper/search"
            if mode == "relevance"
            else "/graph/v1/paper/search/bulk"
        )
        params = {
            "query": query,
            "fields": field_list,
            "limit": limit,
            "offset": offset if mode == "relevance" else None,
            "year": year,
            "publicationDateOrYear": publication_date_or_year,
            "publicationTypes": publication_types,
            "openAccessPdf": str(open_access_pdf).lower()
            if open_access_pdf is not None
            else None,
            "minCitationCount": min_citation_count,
            "venue": venue,
            "fieldsOfStudy": fields_of_study,
            "token": token if mode == "bulk" else None,
            "sort": sort if mode == "bulk" else None,
        }
        payload = self._request(endpoint, params)
        data = payload.get("data") or []
        return {
            "items": [
                normalize_paper(
                    item, auth_mode=self.auth_mode, fields_requested=field_list
                )
                for item in data
            ],
            "meta": {
                "offset": payload.get("offset"),
                "next": payload.get("next")
                or payload.get("nextToken")
                or payload.get("token"),
                "mode": mode,
            },
        }

    def match_paper(
        self, *, query: str, fields: str | None, limit: int | None, year: str | None
    ) -> dict[str, Any]:
        field_list = _split_fields(fields, self.config["paper"]["default_fields"])
        payload = self._request(
            "/graph/v1/paper/search/match",
            {"query": query, "fields": field_list, "limit": limit, "year": year},
        )
        data = payload.get("data") or []
        return {
            "items": [
                normalize_paper(
                    item, auth_mode=self.auth_mode, fields_requested=field_list
                )
                for item in data
            ],
            "meta": {},
        }

    def autocomplete_papers(self, *, query: str) -> dict[str, Any]:
        payload = self._request("/graph/v1/paper/autocomplete", {"query": query})
        matches = payload.get("matches") or []
        return {
            "items": [normalize_autocomplete_match(match) for match in matches],
            "meta": {},
        }

    def fetch_paper(
        self,
        *,
        paper_id: str,
        fields: str | None,
        include_citations: bool = False,
        include_references: bool = False,
        include_authors: bool = False,
        edge_limit: int | None = None,
        edge_offset: int | None = None,
        citation_context: bool = False,
    ) -> dict[str, Any]:
        field_list = _split_fields(fields, self.config["paper"]["default_fields"])
        payload = self._request(
            f"/graph/v1/paper/{quote(paper_id, safe=':')}", {"fields": field_list}
        )
        result = normalize_paper(
            payload, auth_mode=self.auth_mode, fields_requested=field_list
        )
        edge_fields = _append_fields(
            field_list, ["paperId", "title", "authors", "year", "url"]
        )
        if include_citations:
            result["citations"] = self.paper_edges(
                paper_id=paper_id,
                edge_type="citations",
                fields=edge_fields,
                limit=edge_limit,
                offset=edge_offset,
                publication_date_or_year=None,
                citation_context=citation_context,
            )
        if include_references:
            result["references"] = self.paper_edges(
                paper_id=paper_id,
                edge_type="references",
                fields=edge_fields,
                limit=edge_limit,
                offset=edge_offset,
                publication_date_or_year=None,
                citation_context=citation_context,
            )
        if include_authors:
            result["paperAuthors"] = self.paper_authors(
                paper_id=paper_id,
                fields=self.config["author"]["default_fields"],
                limit=edge_limit,
                offset=edge_offset,
            )
        return result

    def fetch_papers_batch(
        self, *, paper_ids: list[str], fields: str | None
    ) -> list[dict[str, Any]]:
        field_list = _split_fields(fields, self.config["paper"]["default_fields"])
        payload = self._post(
            "/graph/v1/paper/batch", {"ids": paper_ids}, params={"fields": field_list}
        )
        return [
            normalize_paper(item, auth_mode=self.auth_mode, fields_requested=field_list)
            for item in payload or []
        ]

    def paper_edges(
        self,
        *,
        paper_id: str,
        edge_type: str,
        fields: str | None,
        limit: int | None,
        offset: int | None,
        publication_date_or_year: str | None,
        citation_context: bool,
    ) -> dict[str, Any]:
        if edge_type not in {"citations", "references"}:
            raise ValueError("edge_type must be 'citations' or 'references'")
        field_list = _split_fields(fields, self.config["paper"]["default_fields"])
        edge_fields = _append_fields(field_list, ["paperId", "title"])
        params = {"fields": edge_fields, "limit": limit, "offset": offset}
        if edge_type == "citations":
            params["publicationDateOrYear"] = publication_date_or_year
        payload = self._request(
            f"/graph/v1/paper/{quote(paper_id, safe=':')}/{edge_type}", params
        )
        items = [
            normalize_edge(
                item,
                auth_mode=self.auth_mode,
                fields_requested=edge_fields,
                edge_kind=edge_type,
            )
            for item in payload.get("data") or []
        ]
        if not citation_context:
            for item in items:
                item.pop("contexts", None)
                item.pop("contextsWithIntent", None)
        return {
            "items": items,
            "meta": {"offset": payload.get("offset"), "next": payload.get("next")},
        }

    def traverse_paper_edges(
        self,
        *,
        paper_id: str,
        edge_type: str,
        depth: int,
        depth_limit: int | None,
        fields: str | None,
        per_page_limit: int | None,
        min_citation_count: int | None,
        citation_context: bool,
    ) -> dict[str, Any]:
        if depth < 1:
            raise ValueError("depth must be at least 1")
        queue: deque[tuple[str, int]] = deque([(paper_id, 0)])
        visited = {paper_id}
        nodes: list[dict[str, Any]] = []
        links: list[dict[str, Any]] = []
        total_fetched = 0
        while queue:
            current_id, current_depth = queue.popleft()
            if current_depth >= depth:
                continue
            batch = self.paper_edges(
                paper_id=current_id,
                edge_type=edge_type,
                fields=fields,
                limit=per_page_limit,
                offset=0,
                publication_date_or_year=None,
                citation_context=citation_context,
            )
            for item in batch["items"]:
                paper = item["paper"]
                citation_count = paper.get("citationCount")
                if (
                    min_citation_count is not None
                    and citation_count is not None
                    and citation_count < min_citation_count
                ):
                    continue
                nodes.append(item)
                total_fetched += 1
                target_id = paper.get("id", {}).get("s2Id")
                links.append(
                    {
                        "source": current_id,
                        "target": target_id,
                        "depth": current_depth + 1,
                        "type": edge_type,
                    }
                )
                if target_id and target_id not in visited and current_depth + 1 < depth:
                    visited.add(target_id)
                    queue.append((target_id, current_depth + 1))
                if depth_limit is not None and total_fetched >= depth_limit:
                    return {
                        "root": paper_id,
                        "edgeType": edge_type,
                        "depth": depth,
                        "items": nodes,
                        "links": links,
                        "meta": {"truncated": True, "depthLimit": depth_limit},
                    }
        return {
            "root": paper_id,
            "edgeType": edge_type,
            "depth": depth,
            "items": nodes,
            "links": links,
            "meta": {"truncated": False, "depthLimit": depth_limit},
        }

    def paper_authors(
        self,
        *,
        paper_id: str,
        fields: str | None,
        limit: int | None,
        offset: int | None,
    ) -> dict[str, Any]:
        field_list = _split_fields(fields, self.config["author"]["default_fields"])
        payload = self._request(
            f"/graph/v1/paper/{quote(paper_id, safe=':')}/authors",
            {"fields": field_list, "limit": limit, "offset": offset},
        )
        return {
            "items": [
                normalize_author(
                    item, auth_mode=self.auth_mode, fields_requested=field_list
                )
                for item in payload.get("data") or []
            ],
            "meta": {"offset": payload.get("offset"), "next": payload.get("next")},
        }

    def search_authors(
        self,
        *,
        query: str,
        fields: str | None,
        limit: int | None,
        offset: int | None = None,
        min_citations: int | None = None,
        min_h_index: int | None = None,
    ) -> dict[str, Any]:
        field_list = _split_fields(fields, self.config["author"]["default_fields"])
        payload = self._request(
            "/graph/v1/author/search",
            {"query": query, "fields": field_list, "limit": limit, "offset": offset},
        )
        items = [
            normalize_author(
                item, auth_mode=self.auth_mode, fields_requested=field_list
            )
            for item in payload.get("data") or []
        ]
        if min_citations is not None:
            items = [
                item
                for item in items
                if (item.get("citationCount") or 0) >= min_citations
            ]
        if min_h_index is not None:
            items = [item for item in items if (item.get("hIndex") or 0) >= min_h_index]
        return {
            "items": items,
            "meta": {"offset": payload.get("offset"), "next": payload.get("next")},
        }

    def fetch_author(
        self,
        *,
        author_id: str,
        fields: str | None,
        include_papers: bool = False,
        paper_limit: int | None = None,
        paper_offset: int | None = None,
        papers_fields: str | None = None,
        publication_date_or_year: str | None = None,
    ) -> dict[str, Any]:
        field_list = _split_fields(fields, self.config["author"]["default_fields"])
        payload = self._request(
            f"/graph/v1/author/{quote(author_id, safe='')}", {"fields": field_list}
        )
        result = normalize_author(
            payload, auth_mode=self.auth_mode, fields_requested=field_list
        )
        if include_papers:
            result["papers"] = self.author_papers(
                author_id=author_id,
                fields=papers_fields,
                limit=paper_limit,
                offset=paper_offset,
                publication_date_or_year=publication_date_or_year,
            )
        return result

    def author_papers(
        self,
        *,
        author_id: str,
        fields: str | None,
        limit: int | None,
        offset: int | None,
        publication_date_or_year: str | None,
    ) -> dict[str, Any]:
        field_list = _split_fields(fields, self.config["paper"]["default_fields"])
        payload = self._request(
            f"/graph/v1/author/{quote(author_id, safe='')}/papers",
            {
                "fields": field_list,
                "limit": limit,
                "offset": offset,
                "publicationDateOrYear": publication_date_or_year,
            },
        )
        return {
            "items": [
                normalize_paper(
                    item, auth_mode=self.auth_mode, fields_requested=field_list
                )
                for item in payload.get("data") or []
            ],
            "meta": {"offset": payload.get("offset"), "next": payload.get("next")},
        }

    def fetch_authors_batch(
        self, *, author_ids: list[str], fields: str | None
    ) -> list[dict[str, Any]]:
        field_list = _split_fields(fields, self.config["author"]["default_fields"])
        payload = self._post(
            "/graph/v1/author/batch", {"ids": author_ids}, params={"fields": field_list}
        )
        return [
            normalize_author(
                item, auth_mode=self.auth_mode, fields_requested=field_list
            )
            for item in payload or []
        ]

    def recommendations_for_paper(
        self,
        *,
        paper_id: str,
        fields: str | None,
        limit: int | None,
        pool_from: str | None,
    ) -> dict[str, Any]:
        field_list = _split_fields(fields, self.config["paper"]["default_fields"])
        payload = self._request(
            f"/recommendations/v1/papers/forpaper/{quote(paper_id, safe=':')}",
            {"fields": field_list, "limit": limit, "from": pool_from},
        )
        items = payload.get("recommendedPapers") or []
        return {
            "items": [
                normalize_paper(
                    item, auth_mode=self.auth_mode, fields_requested=field_list
                )
                for item in items
            ],
            "meta": {"sourcePaper": paper_id},
        }

    def recommendations_from_examples(
        self,
        *,
        positive_paper_ids: list[str],
        negative_paper_ids: list[str],
        fields: str | None,
        limit: int | None,
    ) -> dict[str, Any]:
        field_list = _split_fields(fields, self.config["paper"]["default_fields"])
        payload = self._post(
            "/recommendations/v1/papers/",
            {
                "positivePaperIds": positive_paper_ids,
                "negativePaperIds": negative_paper_ids,
            },
            params={"fields": field_list, "limit": limit},
        )
        items = payload.get("recommendedPapers") or []
        return {
            "items": [
                normalize_paper(
                    item, auth_mode=self.auth_mode, fields_requested=field_list
                )
                for item in items
            ],
            "meta": {
                "positivePaperIds": positive_paper_ids,
                "negativePaperIds": negative_paper_ids,
            },
        }

    def snippet_search(
        self,
        *,
        query: str,
        fields: str | None,
        limit: int | None,
        paper_ids: str | None,
        authors: str | None,
        min_citation_count: int | None,
        inserted_before: str | None,
        publication_date_or_year: str | None,
        year: str | None,
        venue: str | None,
        fields_of_study: str | None,
    ) -> dict[str, Any]:
        field_list = _split_fields(fields, self.config["snippet"]["default_fields"])
        payload = self._request(
            "/graph/v1/snippet/search",
            {
                "query": query,
                "fields": field_list,
                "limit": limit,
                "paperIds": paper_ids,
                "authors": authors,
                "minCitationCount": min_citation_count,
                "insertedBefore": inserted_before,
                "publicationDateOrYear": publication_date_or_year,
                "year": year,
                "venue": venue,
                "fieldsOfStudy": fields_of_study,
            },
        )
        return {
            "items": [
                normalize_snippet_hit(
                    item, auth_mode=self.auth_mode, fields_requested=field_list
                )
                for item in payload.get("data") or []
            ],
            "meta": {"retrievalVersion": payload.get("retrievalVersion")},
        }

    def dataset_releases(self) -> dict[str, Any]:
        payload = self._request("/datasets/v1/release/")
        return {
            "backend": "semanticscholar",
            "api": "datasets/v1",
            "items": [{"releaseId": release_id} for release_id in payload or []],
            "provenance": {"retrievedAt": _now()},
        }

    def dataset_release(self, *, release_id: str) -> dict[str, Any]:
        payload = self._request(f"/datasets/v1/release/{quote(release_id, safe='')}")
        return normalize_release_metadata(payload)

    def dataset_metadata(self, *, release_id: str, dataset_name: str) -> dict[str, Any]:
        payload = self._request(
            f"/datasets/v1/release/{quote(release_id, safe='')}/dataset/{quote(dataset_name, safe='')}"
        )
        return normalize_dataset_metadata(payload, release_id=release_id)

    def dataset_diffs(
        self, *, start_release_id: str, end_release_id: str, dataset_name: str
    ) -> dict[str, Any]:
        payload = self._request(
            f"/datasets/v1/diffs/{quote(start_release_id, safe='')}/to/{quote(end_release_id, safe='')}/{quote(dataset_name, safe='')}"
        )
        return normalize_dataset_diff_list(payload)


def render_output(data: dict[str, Any] | list[dict[str, Any]], fmt: str) -> str:
    import json

    if fmt == "json":
        return json.dumps(data, indent=2, ensure_ascii=True)
    if fmt == "jsonl":
        if (
            isinstance(data, dict)
            and "items" in data
            and isinstance(data["items"], list)
        ):
            items = data["items"]
        elif isinstance(data, list):
            items = data
        else:
            raise ValueError(
                "jsonl output requires a list or a dict with an 'items' list"
            )
        return "\n".join(json.dumps(item, ensure_ascii=True) for item in items)
    if fmt == "text":
        if (
            isinstance(data, dict)
            and "items" in data
            and isinstance(data["items"], list)
        ):
            items = data["items"]
            return "\n".join(_render_text_line(item) for item in items)
        if isinstance(data, list):
            return "\n".join(_render_text_line(item) for item in data)
        return _render_text_block(data)
    raise ValueError(f"Unsupported format: {fmt}")


def _render_text_line(item: dict[str, Any]) -> str:
    if "paper" in item and isinstance(item["paper"], dict):
        target = item["paper"]
        return f"{target.get('title') or target.get('name') or ''}\t{target.get('url') or ''}"
    if "releaseId" in item:
        return str(item.get("releaseId") or "")
    return f"{item.get('title') or item.get('name') or item.get('id') or ''}\t{item.get('url') or ''}"


def _render_text_block(data: dict[str, Any]) -> str:
    if data.get("api") == "datasets/v1":
        return _render_dataset_text_block(data)
    title = data.get("title") or data.get("name") or data.get("id") or ""
    url = data.get("url") or ""
    extra = []
    if data.get("year") is not None:
        extra.append(f"year={data['year']}")
    if data.get("citationCount") is not None:
        extra.append(f"citations={data['citationCount']}")
    if data.get("hIndex") is not None:
        extra.append(f"hIndex={data['hIndex']}")
    lines = [title, url]
    if extra:
        lines.append(" ".join(extra))
    return "\n".join(line for line in lines if line)


def _render_dataset_text_block(data: dict[str, Any]) -> str:
    lines: list[str] = []
    if data.get("releaseId"):
        lines.append(f"release={data['releaseId']}")
    if data.get("name"):
        lines.append(data["name"])
    if data.get("dataset"):
        lines.append(data["dataset"])
    if data.get("description"):
        lines.append(data["description"])
    if data.get("files"):
        lines.extend(data["files"])
    if data.get("diffs"):
        for diff in data["diffs"]:
            lines.append(f"{diff.get('fromRelease')} -> {diff.get('toRelease')}")
            lines.extend(diff.get("updateFiles") or [])
            lines.extend(diff.get("deleteFiles") or [])
    if data.get("README") and not data.get("files") and not data.get("diffs"):
        lines.append(data["README"])
    if data.get("datasets"):
        for dataset in data["datasets"]:
            lines.append(f"{dataset.get('name')}: {dataset.get('description')}")
    return "\n".join(line for line in lines if line)
