<div align="center">

# semantic-scholar-cli

[![Release](https://img.shields.io/github/v/release/decent-tools-for-thought/semantic-scholar-cli?sort=semver&color=facc15)](https://github.com/decent-tools-for-thought/semantic-scholar-cli/releases)
![Python](https://img.shields.io/badge/python-3.11%2B-eab308)
![License](https://img.shields.io/badge/license-0BSD-ca8a04)

Command-line client for Semantic Scholar paper, author, recommendation, snippet, citation-graph, and dataset APIs.

</div>

> [!IMPORTANT]
> This codebase is entirely AI-generated. It is useful to me, I hope it might be useful to others, and issues and contributions are welcome.

## Map
- [Install](#install)
- [Functionality](#functionality)
- [Authentication](#authentication)
- [Quick Start](#quick-start)
- [Credits](#credits)

## Install
$$\color{#EAB308}Install \space \color{#CA8A04}Tool$$

```bash
uv tool install .          # install the CLI
semantic-scholar --help    # inspect the command surface
```

## Functionality
$$\color{#EAB308}Paper \space \color{#CA8A04}Workflows$$
- `semantic-scholar paper search <query>`: search papers with relevance or bulk mode, field selection, year filters, publication-date filters, publication-type filters, venue filters, field-of-study filters, citation-count filters, token pagination, sorting, and `jsonl`/`json`/`text` output.
- `semantic-scholar paper fetch`: fetch one paper by Semantic Scholar ID, DOI, Corpus ID, PMID, PMC ID, arXiv ID, MAG ID, ACL ID, URL, or positional identifier.
- `semantic-scholar paper fetch`: optionally expand citations, references, and authors, with limits, offsets, and citation-context control.
- `semantic-scholar paper batch`: fetch multiple papers in one request.
- `semantic-scholar paper match`: run paper matching against a query.
- `semantic-scholar paper autocomplete`: fetch autocomplete suggestions.
- `semantic-scholar paper authors`: list authors for one paper.
- `semantic-scholar paper fields`: print the built-in paper field catalog.

$$\color{#EAB308}Author \space \color{#CA8A04}Workflows$$
- `semantic-scholar author search <query>`: search authors with field selection, paging, minimum citation count, and minimum h-index filters.
- `semantic-scholar author fetch <author-id>`: fetch one author and optionally include papers.
- `semantic-scholar author fetch`: supports paper limits, offsets, paper field selection, and publication-date filtering for included papers.
- `semantic-scholar author batch`: fetch multiple authors in one request.
- `semantic-scholar author papers <author-id>`: list papers for one author with paging and date filtering.

$$\color{#EAB308}Graph \space \color{#CA8A04}Expansion$$
- `semantic-scholar recommendations`: fetch recommendations from one paper ID or from positive and negative seed paper sets.
- `semantic-scholar references <paper-id>`: traverse citations or references with depth controls, limits, citation-count filters, and optional citation context.
- `semantic-scholar snippets <query>`: search snippet results with paper ID filters, author filters, venue filters, date filters, field-of-study filters, and citation-count filters.

$$\color{#EAB308}Dataset \space \color{#CA8A04}Access$$
- `semantic-scholar datasets releases`: list dataset releases.
- `semantic-scholar datasets release <release-id>`: fetch one release.
- `semantic-scholar datasets latest`: fetch the latest release metadata.
- `semantic-scholar datasets dataset <name>`: fetch metadata for one dataset in a specific release.
- `semantic-scholar datasets files <name>`: list files for one dataset and release.
- `semantic-scholar datasets readme <name>`: fetch the dataset readme payload.
- `semantic-scholar datasets diffs <name> --from ... --to ...`: compare two dataset releases.

$$\color{#EAB308}Saved \space \color{#CA8A04}Defaults$$
- `semantic-scholar config show`: print the saved config.
- `semantic-scholar config reset`: restore defaults.
- `semantic-scholar config request-key`: print API-key request guidance.
- `semantic-scholar config set api-key`, `email`, `default-fields`, `search-mode`, `default-format`, and `include-citation-context`: tune saved defaults.

## Authentication
$$\color{#EAB308}Access \space \color{#CA8A04}Setup$$

Smoke usage works without stored credentials:

```bash
semantic-scholar paper search "graph neural networks" --no-auth --limit 1 --format text    # smoke-test without saved auth
```

For regular usage:

```bash
semantic-scholar config set api-key "<your-api-key>"    # save the API key
semantic-scholar config show                            # inspect saved defaults
```

## Quick Start
$$\color{#EAB308}Try \space \color{#CA8A04}Search$$

```bash
semantic-scholar paper search "attention mechanisms in transformers" \    # search papers
  --mode relevance \
  --limit 10

semantic-scholar paper fetch --s2-id 2b6d0147698235457a4f7d6a12f8 \    # fetch one paper and expand edges
  --include-citations \
  --include-references

semantic-scholar datasets latest --format json                     # inspect the latest dataset release
semantic-scholar datasets dataset papers --release latest --format json    # fetch one dataset manifest
```

## Credits

This client is built for the Semantic Scholar APIs and is not affiliated with Semantic Scholar or the Allen Institute for AI.

Credit goes to Semantic Scholar and AI2 for the upstream academic graph, recommendation services, datasets, and API documentation this tool depends on.
