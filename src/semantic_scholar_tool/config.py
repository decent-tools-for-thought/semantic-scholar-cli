from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import tomllib

def _xdg_config_home() -> Path:
    configured = os.environ.get("XDG_CONFIG_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".config"


CONFIG_DIR = _xdg_config_home() / "semantic-scholar-tool"
CONFIG_PATH = CONFIG_DIR / "config.toml"

DEFAULT_CONFIG = {
    "api": {
        "base_url": "https://api.semanticscholar.org",
        "graph_version": "v1",
        "api_key": "",
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
        "default_fields": "paperId,title,authors,year,abstract,citationCount,url",
        "bulk_page_size": 100,
        "relevance_limit": 10,
    },
    "author": {
        "default_fields": "authorId,name,affiliations,paperCount,citationCount,hIndex,url",
    },
    "citation": {
        "default_citation_limit": 50,
    },
    "snippet": {
        "default_fields": "paper.title,paper.corpusId,paper.authors,snippet.text,snippet.section",
    },
    "output": {
        "default_format": "jsonl",
        "include_citation_context": False,
    },
}


def _merge(base: dict, override: dict) -> dict:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return deepcopy(DEFAULT_CONFIG)
    with CONFIG_PATH.open("rb") as handle:
        loaded = tomllib.load(handle)
    return _merge(DEFAULT_CONFIG, loaded)


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    for section, values in config.items():
        lines.append(f"[{section}]")
        for key, value in values.items():
            if isinstance(value, bool):
                encoded = "true" if value else "false"
            elif isinstance(value, int):
                encoded = str(value)
            else:
                escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
                encoded = f'"{escaped}"'
            lines.append(f"{key} = {encoded}")
        lines.append("")
    CONFIG_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def reset_config() -> dict:
    config = deepcopy(DEFAULT_CONFIG)
    save_config(config)
    return config
