"""WARM-1 (BL-71 part 2): the pre-build's HTTP client against a running serve (`chain/prebuild.py` HTTP mode).

`get(path)` returns the two fields the pre-build reads, the status and the headers (case-insensitive `get`); a
non-2xx status is returned, never raised, so the INFRA-1 retry rule can read a 503.
"""
from __future__ import annotations

import urllib.error
import urllib.request
from typing import Any

HTTP_TIMEOUT_SECONDS = 900


class _Headers(dict):
    """Response headers with a case-insensitive `get` (HTTP header names are case-insensitive)."""

    def get(self, key: str, default: Any = None) -> Any:  # type: ignore[override]
        return super().get(key.lower(), default)


class HttpResponse:
    def __init__(self, status_code: int, headers: Any) -> None:
        self.status_code = int(status_code)
        self.headers = _Headers((str(k).lower(), v) for k, v in (headers or []))


class HttpClient:
    def __init__(self, base_url: str, timeout: float = HTTP_TIMEOUT_SECONDS, opener: Any = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._open = opener or urllib.request.urlopen

    def get(self, path: str) -> HttpResponse:
        try:
            with self._open(self.base_url + path, timeout=self.timeout) as response:
                response.read()
                return HttpResponse(response.status, response.headers.items())
        except urllib.error.HTTPError as error:
            return HttpResponse(error.code, error.headers.items() if error.headers else [])
