from __future__ import annotations

import argparse
import json
import sys

from .config import load_config, reset_config, save_config
from .core import (
    AUTHOR_FIELD_CATALOG,
    DATASET_COMMAND_CATALOG,
    PAPER_FIELD_CATALOG,
    SemanticScholarService,
    render_output,
    resolve_paper_identifier,
)


def _add_auth_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--api-key")
    parser.add_argument("--no-auth", action="store_true")


def _add_format_arg(parser: argparse.ArgumentParser, *choices: str) -> None:
    parser.add_argument("--format", choices=list(choices))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sem")
    subparsers = parser.add_subparsers(dest="command", required=True)

    paper = subparsers.add_parser("paper")
    paper_sub = paper.add_subparsers(dest="paper_command", required=True)

    paper_search = paper_sub.add_parser("search")
    paper_search.add_argument("query")
    paper_search.add_argument("--mode", choices=["relevance", "bulk"])
    paper_search.add_argument("--relevance", action="store_true")
    paper_search.add_argument("--bulk", action="store_true")
    paper_search.add_argument("--fields")
    paper_search.add_argument("--limit", type=int)
    paper_search.add_argument("--offset", type=int)
    paper_search.add_argument("--year")
    paper_search.add_argument("--publication-date-or-year")
    paper_search.add_argument("--publication-types")
    paper_search.add_argument("--open-access-pdf", action="store_true")
    paper_search.add_argument("--min-citation-count", type=int)
    paper_search.add_argument("--venue")
    paper_search.add_argument("--fields-of-study")
    paper_search.add_argument("--token")
    paper_search.add_argument("--sort")
    _add_auth_args(paper_search)
    _add_format_arg(paper_search, "jsonl", "json", "text")

    paper_fetch = paper_sub.add_parser("fetch")
    paper_fetch.add_argument("paper_id", nargs="?")
    paper_fetch.add_argument("--s2-id")
    paper_fetch.add_argument("--doi")
    paper_fetch.add_argument("--corpus-id")
    paper_fetch.add_argument("--pmid")
    paper_fetch.add_argument("--pmc-id")
    paper_fetch.add_argument("--arxiv")
    paper_fetch.add_argument("--mag")
    paper_fetch.add_argument("--acl")
    paper_fetch.add_argument("--url")
    paper_fetch.add_argument("--fields")
    paper_fetch.add_argument("--include-citations", action="store_true")
    paper_fetch.add_argument("--include-references", action="store_true")
    paper_fetch.add_argument("--include-authors", action="store_true")
    paper_fetch.add_argument("--citation-limit", type=int)
    paper_fetch.add_argument("--offset", type=int)
    paper_fetch.add_argument("--citation-context", action=argparse.BooleanOptionalAction)
    _add_auth_args(paper_fetch)
    _add_format_arg(paper_fetch, "json", "text")

    paper_batch = paper_sub.add_parser("batch")
    paper_batch.add_argument("paper_ids", nargs="+")
    paper_batch.add_argument("--fields")
    _add_auth_args(paper_batch)
    _add_format_arg(paper_batch, "jsonl", "json", "text")

    paper_match = paper_sub.add_parser("match")
    paper_match.add_argument("query")
    paper_match.add_argument("--fields")
    paper_match.add_argument("--limit", type=int)
    paper_match.add_argument("--year")
    _add_auth_args(paper_match)
    _add_format_arg(paper_match, "jsonl", "json", "text")

    paper_autocomplete = paper_sub.add_parser("autocomplete")
    paper_autocomplete.add_argument("query")
    _add_auth_args(paper_autocomplete)
    _add_format_arg(paper_autocomplete, "jsonl", "json", "text")

    paper_authors = paper_sub.add_parser("authors")
    paper_authors.add_argument("paper_id")
    paper_authors.add_argument("--fields")
    paper_authors.add_argument("--limit", type=int)
    paper_authors.add_argument("--offset", type=int)
    _add_auth_args(paper_authors)
    _add_format_arg(paper_authors, "jsonl", "json", "text")

    paper_fields = paper_sub.add_parser("fields")
    _add_format_arg(paper_fields, "json", "text")

    author = subparsers.add_parser("author")
    author_sub = author.add_subparsers(dest="author_command", required=True)

    author_search = author_sub.add_parser("search")
    author_search.add_argument("query")
    author_search.add_argument("--fields")
    author_search.add_argument("--limit", type=int)
    author_search.add_argument("--offset", type=int)
    author_search.add_argument("--min-citations", type=int)
    author_search.add_argument("--min-h-index", type=int)
    _add_auth_args(author_search)
    _add_format_arg(author_search, "jsonl", "json", "text")

    author_fetch = author_sub.add_parser("fetch")
    author_fetch.add_argument("author_id")
    author_fetch.add_argument("--fields")
    author_fetch.add_argument("--include-papers", action="store_true")
    author_fetch.add_argument("--paper-limit", type=int)
    author_fetch.add_argument("--offset", type=int)
    author_fetch.add_argument("--papers-fields")
    author_fetch.add_argument("--publication-date-or-year")
    _add_auth_args(author_fetch)
    _add_format_arg(author_fetch, "json", "text")

    author_batch = author_sub.add_parser("batch")
    author_batch.add_argument("author_ids", nargs="+")
    author_batch.add_argument("--fields")
    _add_auth_args(author_batch)
    _add_format_arg(author_batch, "jsonl", "json", "text")

    author_papers = author_sub.add_parser("papers")
    author_papers.add_argument("author_id")
    author_papers.add_argument("--fields")
    author_papers.add_argument("--limit", type=int)
    author_papers.add_argument("--offset", type=int)
    author_papers.add_argument("--publication-date-or-year")
    _add_auth_args(author_papers)
    _add_format_arg(author_papers, "jsonl", "json", "text")

    recommendations = subparsers.add_parser("recommendations")
    recommendations.add_argument("paper_id", nargs="?")
    recommendations.add_argument("--positive-paper-id", action="append", default=[])
    recommendations.add_argument("--negative-paper-id", action="append", default=[])
    recommendations.add_argument("--fields")
    recommendations.add_argument("--limit", type=int)
    recommendations.add_argument("--from", dest="pool_from", choices=["recent", "all-cs"])
    _add_auth_args(recommendations)
    _add_format_arg(recommendations, "jsonl", "json", "text")

    references = subparsers.add_parser("references")
    references.add_argument("paper_id")
    mode_group = references.add_mutually_exclusive_group()
    mode_group.add_argument("--citations", action="store_true")
    mode_group.add_argument("--references", action="store_true")
    references.add_argument("--depth", type=int, default=1)
    references.add_argument("--depth-limit", type=int)
    references.add_argument("--fields")
    references.add_argument("--limit", type=int)
    references.add_argument("--min-citation-count", type=int)
    references.add_argument("--citation-context", action=argparse.BooleanOptionalAction)
    _add_auth_args(references)
    _add_format_arg(references, "json", "text", "jsonl")

    snippets = subparsers.add_parser("snippets")
    snippets.add_argument("query")
    snippets.add_argument("--fields")
    snippets.add_argument("--limit", type=int)
    snippets.add_argument("--paper-ids")
    snippets.add_argument("--authors")
    snippets.add_argument("--min-citation-count", type=int)
    snippets.add_argument("--inserted-before")
    snippets.add_argument("--publication-date-or-year")
    snippets.add_argument("--year")
    snippets.add_argument("--venue")
    snippets.add_argument("--fields-of-study")
    _add_auth_args(snippets)
    _add_format_arg(snippets, "jsonl", "json", "text")

    datasets = subparsers.add_parser("datasets")
    datasets_sub = datasets.add_subparsers(dest="datasets_command", required=True)

    datasets_releases = datasets_sub.add_parser("releases")
    _add_auth_args(datasets_releases)
    _add_format_arg(datasets_releases, "jsonl", "json", "text")

    datasets_release = datasets_sub.add_parser("release")
    datasets_release.add_argument("release_id")
    _add_auth_args(datasets_release)
    _add_format_arg(datasets_release, "json", "text")

    datasets_latest = datasets_sub.add_parser("latest")
    _add_auth_args(datasets_latest)
    _add_format_arg(datasets_latest, "json", "text")

    datasets_dataset = datasets_sub.add_parser("dataset")
    datasets_dataset.add_argument("dataset_name")
    datasets_dataset.add_argument("--release", dest="release_id", default="latest")
    _add_auth_args(datasets_dataset)
    _add_format_arg(datasets_dataset, "json", "text")

    datasets_files = datasets_sub.add_parser("files")
    datasets_files.add_argument("dataset_name")
    datasets_files.add_argument("--release", dest="release_id", default="latest")
    _add_auth_args(datasets_files)
    _add_format_arg(datasets_files, "jsonl", "json", "text")

    datasets_readme = datasets_sub.add_parser("readme")
    datasets_readme.add_argument("dataset_name")
    datasets_readme.add_argument("--release", dest="release_id", default="latest")
    _add_auth_args(datasets_readme)
    _add_format_arg(datasets_readme, "json", "text")

    datasets_diffs = datasets_sub.add_parser("diffs")
    datasets_diffs.add_argument("dataset_name")
    datasets_diffs.add_argument("--from", dest="start_release_id", required=True)
    datasets_diffs.add_argument("--to", dest="end_release_id", required=True)
    _add_auth_args(datasets_diffs)
    _add_format_arg(datasets_diffs, "json", "text")

    config = subparsers.add_parser("config")
    config_sub = config.add_subparsers(dest="config_command", required=True)
    config_sub.add_parser("show")
    config_sub.add_parser("reset")
    config_sub.add_parser("request-key")
    config_set = config_sub.add_parser("set")
    config_set.add_argument(
        "field",
        choices=["api-key", "email", "default-fields", "search-mode", "default-format", "include-citation-context"],
    )
    config_set.add_argument("value")

    return parser


def _service(args, config):
    return SemanticScholarService(
        config=config,
        no_auth=getattr(args, "no_auth", False),
        api_key_override=getattr(args, "api_key", None),
    )


def _config_set(config: dict, field: str, value: str) -> dict:
    if field == "api-key":
        config["api"]["api_key"] = value
    elif field == "email":
        config["api"]["email"] = value
    elif field == "default-fields":
        config["paper"]["default_fields"] = value
    elif field == "search-mode":
        if value not in {"relevance", "bulk"}:
            raise ValueError("search-mode must be 'relevance' or 'bulk'")
        config["paper"]["default_search_mode"] = value
    elif field == "default-format":
        if value not in {"json", "jsonl", "text"}:
            raise ValueError("default-format must be one of: json, jsonl, text")
        config["output"]["default_format"] = value
    elif field == "include-citation-context":
        if value.lower() not in {"true", "false"}:
            raise ValueError("include-citation-context must be true or false")
        config["output"]["include_citation_context"] = value.lower() == "true"
    else:
        raise ValueError(f"Unsupported config field: {field}")
    save_config(config)
    return config


def _output_format(args, config) -> str:
    return getattr(args, "format", None) or config["output"]["default_format"]


def _paper_identifier_from_args(args) -> str:
    return resolve_paper_identifier(
        getattr(args, "paper_id", None),
        s2_id=getattr(args, "s2_id", None),
        doi=getattr(args, "doi", None),
        corpus_id=getattr(args, "corpus_id", None),
        pmid=getattr(args, "pmid", None),
        pmc_id=getattr(args, "pmc_id", None),
        arxiv=getattr(args, "arxiv", None),
        mag=getattr(args, "mag", None),
        acl=getattr(args, "acl", None),
        url=getattr(args, "url", None),
    )


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    config = load_config()

    try:
        if args.command == "config":
            if args.config_command == "show":
                print(json.dumps(config, indent=2, ensure_ascii=True))
                return 0
            if args.config_command == "reset":
                print(json.dumps(reset_config(), indent=2, ensure_ascii=True))
                return 0
            if args.config_command == "request-key":
                print("Request an API key at https://www.semanticscholar.org/product/api")
                return 0
            print(json.dumps(_config_set(config, args.field, args.value), indent=2, ensure_ascii=True))
            return 0

        if args.command == "paper" and args.paper_command == "fields":
            output_format = _output_format(args, config)
            payload = {
                "paperFields": PAPER_FIELD_CATALOG,
                "authorFields": AUTHOR_FIELD_CATALOG,
                "datasetCommands": DATASET_COMMAND_CATALOG,
            }
            print(render_output(payload, output_format))
            return 0

        output_format = _output_format(args, config)
        service = _service(args, config)

        if args.command == "paper" and args.paper_command == "search":
            mode = args.mode or ("bulk" if args.bulk else "relevance" if args.relevance else config["paper"]["default_search_mode"])
            payload = service.search_papers(
                query=args.query,
                mode=mode,
                fields=args.fields,
                limit=args.limit,
                offset=args.offset,
                year=args.year,
                publication_date_or_year=args.publication_date_or_year,
                publication_types=args.publication_types,
                open_access_pdf=args.open_access_pdf if args.open_access_pdf else None,
                min_citation_count=args.min_citation_count,
                venue=args.venue,
                fields_of_study=args.fields_of_study,
                token=args.token,
                sort=args.sort,
            )
        elif args.command == "paper" and args.paper_command == "fetch":
            payload = service.fetch_paper(
                paper_id=_paper_identifier_from_args(args),
                fields=args.fields,
                include_citations=args.include_citations,
                include_references=args.include_references,
                include_authors=args.include_authors,
                edge_limit=args.citation_limit or config["citation"]["default_citation_limit"],
                edge_offset=args.offset,
                citation_context=(
                    config["output"]["include_citation_context"]
                    if args.citation_context is None
                    else args.citation_context
                ),
            )
        elif args.command == "paper" and args.paper_command == "batch":
            payload = service.fetch_papers_batch(paper_ids=args.paper_ids, fields=args.fields)
        elif args.command == "paper" and args.paper_command == "match":
            payload = service.match_paper(query=args.query, fields=args.fields, limit=args.limit, year=args.year)
        elif args.command == "paper" and args.paper_command == "autocomplete":
            payload = service.autocomplete_papers(query=args.query)
        elif args.command == "paper" and args.paper_command == "authors":
            payload = service.paper_authors(paper_id=args.paper_id, fields=args.fields, limit=args.limit, offset=args.offset)
        elif args.command == "author" and args.author_command == "search":
            payload = service.search_authors(
                query=args.query,
                fields=args.fields,
                limit=args.limit,
                offset=args.offset,
                min_citations=args.min_citations,
                min_h_index=args.min_h_index,
            )
        elif args.command == "author" and args.author_command == "fetch":
            payload = service.fetch_author(
                author_id=args.author_id,
                fields=args.fields,
                include_papers=args.include_papers,
                paper_limit=args.paper_limit,
                paper_offset=args.offset,
                papers_fields=args.papers_fields,
                publication_date_or_year=args.publication_date_or_year,
            )
        elif args.command == "author" and args.author_command == "batch":
            payload = service.fetch_authors_batch(author_ids=args.author_ids, fields=args.fields)
        elif args.command == "author" and args.author_command == "papers":
            payload = service.author_papers(
                author_id=args.author_id,
                fields=args.fields,
                limit=args.limit,
                offset=args.offset,
                publication_date_or_year=args.publication_date_or_year,
            )
        elif args.command == "recommendations":
            if args.paper_id:
                payload = service.recommendations_for_paper(
                    paper_id=args.paper_id,
                    fields=args.fields,
                    limit=args.limit,
                    pool_from=args.pool_from,
                )
            elif args.positive_paper_id:
                payload = service.recommendations_from_examples(
                    positive_paper_ids=args.positive_paper_id,
                    negative_paper_ids=args.negative_paper_id,
                    fields=args.fields,
                    limit=args.limit,
                )
            else:
                raise ValueError("Provide a paper_id or at least one --positive-paper-id")
        elif args.command == "references":
            edge_type = "citations" if args.citations else "references"
            payload = service.traverse_paper_edges(
                paper_id=args.paper_id,
                edge_type=edge_type,
                depth=args.depth,
                depth_limit=args.depth_limit,
                fields=args.fields,
                per_page_limit=args.limit or config["citation"]["default_citation_limit"],
                min_citation_count=args.min_citation_count,
                citation_context=(
                    config["output"]["include_citation_context"]
                    if args.citation_context is None
                    else args.citation_context
                ),
            )
        elif args.command == "snippets":
            payload = service.snippet_search(
                query=args.query,
                fields=args.fields,
                limit=args.limit,
                paper_ids=args.paper_ids,
                authors=args.authors,
                min_citation_count=args.min_citation_count,
                inserted_before=args.inserted_before,
                publication_date_or_year=args.publication_date_or_year,
                year=args.year,
                venue=args.venue,
                fields_of_study=args.fields_of_study,
            )
        elif args.command == "datasets" and args.datasets_command == "releases":
            payload = service.dataset_releases()
        elif args.command == "datasets" and args.datasets_command in {"release", "latest"}:
            payload = service.dataset_release(release_id=(args.release_id if args.datasets_command == "release" else "latest"))
        elif args.command == "datasets" and args.datasets_command in {"dataset", "files", "readme"}:
            dataset = service.dataset_metadata(release_id=args.release_id, dataset_name=args.dataset_name)
            if args.datasets_command == "files":
                payload = {"items": [{"url": file_url} for file_url in dataset.get("files", [])]}
            elif args.datasets_command == "readme":
                payload = {
                    "backend": "semanticscholar",
                    "api": "datasets/v1",
                    "releaseId": dataset.get("releaseId"),
                    "name": dataset.get("name"),
                    "README": dataset.get("README"),
                }
            else:
                payload = dataset
        elif args.command == "datasets" and args.datasets_command == "diffs":
            payload = service.dataset_diffs(
                start_release_id=args.start_release_id,
                end_release_id=args.end_release_id,
                dataset_name=args.dataset_name,
            )
        else:
            raise ValueError("Unsupported command")

        if output_format == "jsonl":
            printable = payload if isinstance(payload, list) else payload.get("items", payload)
        else:
            printable = payload
        print(render_output(printable, output_format))
        return 0
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
