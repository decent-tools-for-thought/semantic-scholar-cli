from __future__ import annotations

import json
import random
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class HttpClient:
    def __init__(self, headers: dict[str, str] | None = None, timeout: float = 30.0) -> None:
        self.headers = headers or {}
        self.timeout = timeout

    def get_json(
        self,
        url: str,
        params: dict[str, Any] | None,
        *,
        max_retries: int,
        initial_backoff_ms: int,
        max_backoff_ms: int,
        jitter_factor: float,
    ) -> Any:
        return self._request_json(
            "GET",
            url,
            params=params,
            payload=None,
            max_retries=max_retries,
            initial_backoff_ms=initial_backoff_ms,
            max_backoff_ms=max_backoff_ms,
            jitter_factor=jitter_factor,
        )

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
    ) -> Any:
        return self._request_json(
            "POST",
            url,
            params=params,
            payload=payload,
            max_retries=max_retries,
            initial_backoff_ms=initial_backoff_ms,
            max_backoff_ms=max_backoff_ms,
            jitter_factor=jitter_factor,
        )

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None,
        payload: dict[str, Any] | None,
        max_retries: int,
        initial_backoff_ms: int,
        max_backoff_ms: int,
        jitter_factor: float,
    ) -> Any:
        query = urlencode({k: v for k, v in (params or {}).items() if v is not None}, doseq=True)
        request_url = f"{url}?{query}" if query else url
        request_headers = dict(self.headers)
        request_data = None
        if payload is not None:
            request_headers["Content-Type"] = "application/json"
            request_data = json.dumps(payload).encode("utf-8")
        backoff_ms = initial_backoff_ms
        for attempt in range(max_retries):
            request = Request(request_url, data=request_data, headers=request_headers, method=method)
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                if exc.code not in {408, 409, 425, 429, 500, 502, 503, 504} or attempt == max_retries - 1:
                    detail = self._error_detail(exc)
                    raise RuntimeError(f"Request failed with HTTP {exc.code}: {request_url}{detail}") from exc
            except URLError as exc:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Request failed: {request_url}") from exc
            jitter = backoff_ms * jitter_factor * random.random()
            time.sleep((backoff_ms + jitter) / 1000.0)
            backoff_ms = min(backoff_ms * 2, max_backoff_ms)

    @staticmethod
    def _error_detail(exc: HTTPError) -> str:
        try:
            body = exc.read().decode("utf-8").strip()
        except Exception:
            body = ""
        if not body:
            return ""
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            return f": {body}"
        if isinstance(parsed, dict) and parsed.get("error"):
            return f": {parsed['error']}"
        return f": {json.dumps(parsed, ensure_ascii=True)}"
