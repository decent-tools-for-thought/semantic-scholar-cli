# Semantic Scholar Tool - Semantic Scholar CLI

A command-line tool for the Semantic Scholar Graph API, Recommendations API, and Datasets API.

## Quick Start

### Installation
```bash
uv tool install semantic-scholar-tool
```

Tagged GitHub releases publish Python distribution artifacts built from the tagged commit.

### Development
```bash
uv sync --extra dev
uv run semantic-scholar --help
uv run ruff format --check .
uv run ruff check .
uv run mypy
```

### Basic Usage

#### Search papers by keyword
```bash
# Relevance search
semantic-scholar paper search "attention mechanisms in transformers" \
  --mode relevance \
  --year 2023- \
  --limit 10 \
  --format jsonl

# Bulk search
semantic-scholar paper search "deep learning in bioinformatics" \
  --mode bulk \
  --year 2020- \
  --fields paperId,title,abstract,authors,citationCount,year \
  --limit 100 \
  --format jsonl
```

#### Fetch a paper and expand graph edges
```bash
semantic-scholar paper fetch --s2-id 2b6d0147698235457a4f7d6a12f8 \
  --include-citations \
  --include-references \
  --citation-limit 20 \
  --format json
```

#### Author search and profile
```bash
semantic-scholar author search "Yann LeCun" \
  --min-citations 10000 \
  --limit 10

semantic-scholar author fetch 1741101 \
  --include-papers \
  --paper-limit 50
```

#### Traverse citations or references
```bash
semantic-scholar references 2b6d0147698235457a4f7d6a12f8 \
  --citations \
  --min-citation-count 100 \
  --depth 1
```

#### Get recommendations
```bash
semantic-scholar recommendations 2b6d0147698235457a4f7d6a12f8 \
  --limit 20

semantic-scholar recommendations \
  --positive-paper-id 204e3073870fae3d05bcbc2f6a8e263d9b72e776 \
  --positive-paper-id 2b6d0147698235457a4f7d6a12f8 \
  --negative-paper-id 5c5751d45e298cea054f32b392c12c61027d2fe7
```

#### Use the datasets API
```bash
semantic-scholar datasets releases --format text
semantic-scholar datasets latest --format json
semantic-scholar datasets dataset papers --release latest --format json
semantic-scholar datasets diffs papers --from 2024-01-02 --to latest --format json
```

## API Coverage

1. Graph API: paper search, paper fetch, batch fetch, paper match, autocomplete, citation/reference traversal, author search/fetch, author papers, author batch, snippet search
2. Recommendations API: recommendations from a single paper or positive/negative example sets
3. Datasets API: release listing, release metadata, dataset file manifests, dataset README access, incremental diffs

## Key Commands

### Paper Discovery
- `semantic-scholar paper search <query>` - Search papers in relevance or bulk mode
- `semantic-scholar paper fetch <id>` - Fetch one paper by S2 ID or external identifier
- `semantic-scholar paper batch <id...>` - Fetch multiple papers in one request
- `semantic-scholar paper match <query>` - Match papers by query string
- `semantic-scholar paper autocomplete <query>` - Autocomplete paper titles
- `semantic-scholar paper authors <paper_id>` - List authors for a paper
- `semantic-scholar paper fields` - Show built-in field catalogs and command catalogs

### Citation Graph
- `semantic-scholar references <paper_id>` - Traverse references or citations with depth control
- `semantic-scholar recommendations <paper_id>` - Get related papers for one seed paper

### Author Discovery
- `semantic-scholar author search <name>` - Search authors
- `semantic-scholar author fetch <author_id>` - Fetch an author profile
- `semantic-scholar author batch <id...>` - Fetch multiple authors
- `semantic-scholar author papers <author_id>` - List an author's papers

### Snippet Search
- `semantic-scholar snippets <query>` - Search snippet-level matches

### Dataset Access
- `semantic-scholar datasets releases` - List all available releases
- `semantic-scholar datasets release <release_id>` - Show one release manifest
- `semantic-scholar datasets latest` - Show the latest release manifest
- `semantic-scholar datasets dataset <dataset_name> --release <release_id|latest>` - Show dataset metadata and pre-signed file URLs
- `semantic-scholar datasets files <dataset_name> --release <release_id|latest>` - Print dataset file URLs for scripting
- `semantic-scholar datasets readme <dataset_name> --release <release_id|latest>` - Print dataset documentation/license text
- `semantic-scholar datasets diffs <dataset_name> --from <release> --to <release|latest>` - Show incremental diff manifests

### Configuration
- `semantic-scholar config set api-key <key>`
- `semantic-scholar config set email <address>`
- `semantic-scholar config set default-fields <fields>`
- `semantic-scholar config set search-mode <relevance|bulk>`
- `semantic-scholar config set default-format <json|jsonl|text>`
- `semantic-scholar config set include-citation-context <true|false>`
- `semantic-scholar config show`
- `semantic-scholar config reset`
- `semantic-scholar config request-key`

## Output Formats

### JSONL Search Result
```jsonl
{"backend":"semanticscholar","id":{"s2Id":"2b6d0147698235457a4f7d6a12f8","corpusId":"1234567","doi":"10.1145/1234567.1234568","pmid":null,"pmcId":null,"arxiv":null,"acl":null,"mag":null},"title":"Attention Is All You Need","authors":[{"authorId":"123","name":"Ashish Vaswani"}],"year":2017,"citationCount":45000,"referenceCount":123,"influentialCitationCount":12000,"isOpenAccess":true,"url":"https://www.semanticscholar.org/paper/2b6d0147698235457a4f7d6a12f8","provenance":{"retrievedAt":"2026-03-16T18:30:00Z","apiVersion":"graph/v1","authMode":"authenticated","fieldsRequested":["paperId","title","authors"]}}
```

### Dataset Manifest Example
```json
{
  "backend": "semanticscholar",
  "api": "datasets/v1",
  "releaseId": "latest",
  "name": "papers",
  "description": "Core paper metadata",
  "README": "Subject to terms of use ...",
  "files": ["https://..."],
  "provenance": {"retrievedAt": "2026-03-16T18:30:00Z"}
}
```

## Configuration

Global config path: `$XDG_CONFIG_HOME/semantic-scholar-tool/config.toml` (default `~/.config/semantic-scholar-tool/config.toml`)

```toml
[api]
base_url = "https://api.semanticscholar.org"
graph_version = "v1"
api_key = ""
email = "user@example.com"

[rate_limit]
max_retries = 5
initial_backoff_ms = 1000
max_backoff_ms = 30000
jitter_factor = 0.2

[paper]
default_search_mode = "relevance"
default_fields = "paperId,title,authors,year,abstract,citationCount,url"
bulk_page_size = 100
relevance_limit = 10

[author]
default_fields = "authorId,name,affiliations,paperCount,citationCount,hIndex,url"

[citation]
default_citation_limit = 50

[snippet]
default_fields = "paper.title,paper.corpusId,paper.authors,snippet.text,snippet.section"

[output]
default_format = "jsonl"
include_citation_context = false
```

## Authentication and Rate Limiting

### Unauthenticated
- Shared public access
- Suitable for occasional usage and smoke testing

Smoke test without stored credentials:
```bash
semantic-scholar --help
semantic-scholar paper fields --format text
semantic-scholar paper search "graph neural networks" --no-auth --limit 1 --format text
```

### Authenticated
- API key via `x-api-key`
- More predictable for regular workflows

Store defaults for regular usage:
```bash
semantic-scholar config set api-key "<your-api-key>"
semantic-scholar config set default-format json
semantic-scholar config show
```

### Backoff
- Exponential backoff with jitter is implemented automatically
- The API terms explicitly prohibit rate-limit circumvention

## Datasets Notes

- `semantic-scholar datasets dataset ...` returns pre-signed URLs for full dataset downloads
- `semantic-scholar datasets diffs ...` returns ordered diff manifests with `updateFiles` and `deleteFiles`
- Datasets endpoints are metadata/manifests only; the CLI does not download or unpack the files for you

## Project Structure

```text
semantic-scholar-tool/
├── PROJECT_OUTLINE.md
├── README.md
├── pyproject.toml
├── src/
└── tests/
```

## Documentation

- `PROJECT_OUTLINE.md` - design document
- `https://api.semanticscholar.org/api-docs/graph`
- `https://api.semanticscholar.org/api-docs/recommendations`
- `https://api.semanticscholar.org/api-docs/datasets`

## Status

- Status: Implemented
- Version: 0.1.0
- API Documentation: `https://api.semanticscholar.org`
- API License: `https://www.semanticscholar.org/product/api#api-terms-and-conditions`
