# semantic-scholar-cli

[![Release](https://img.shields.io/github/v/release/decent-tools-for-thought/semantic-scholar-cli?sort=semver)](https://github.com/decent-tools-for-thought/semantic-scholar-cli/releases)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-0BSD-green)

Command-line client for the Semantic Scholar Graph, Recommendations, and Datasets APIs.

> [!IMPORTANT]
> This codebase is largely AI-generated. It is useful to me, I hope it might be useful to others, and issues and contributions are welcome.

## Why This Exists

- Search papers, authors, and citation graphs from the terminal.
- Pull recommendations and dataset manifests without custom scripts.
- Keep common academic discovery workflows consistent and automatable.

## Install

```bash
uv tool install .
semantic-scholar --help
```

For local development:

```bash
uv sync --extra dev
uv run semantic-scholar --help
```

## Quick Start

Search papers:

```bash
semantic-scholar paper search "attention mechanisms in transformers" \
  --mode relevance \
  --limit 10
```

Fetch a paper and expand edges:

```bash
semantic-scholar paper fetch --s2-id 2b6d0147698235457a4f7d6a12f8 \
  --include-citations \
  --include-references
```

Use the datasets API:

```bash
semantic-scholar datasets latest --format json
semantic-scholar datasets dataset papers --release latest --format json
```

## Authentication

Smoke usage works without stored credentials:

```bash
semantic-scholar paper search "graph neural networks" --no-auth --limit 1 --format text
```

For regular usage:

```bash
semantic-scholar config set api-key "<your-api-key>"
semantic-scholar config show
```

## Development

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
```

## Credits

This client depends on the Semantic Scholar APIs and dataset services. Credit goes to Semantic Scholar and the Allen Institute for AI for the upstream academic graph, recommendations, and dataset infrastructure.
