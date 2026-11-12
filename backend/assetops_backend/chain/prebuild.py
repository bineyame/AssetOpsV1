"""CH-5c Q8 (CH5c-R5 R5-1(d)): the pre-build of the stored routes after the tick's Site loop.

Each request of the pre-built route list (page 1 only, Q11; E4 D-E4.1: the file named by `ASSETOPS_PREBUILT_ROUTES`
when set, else `config/chain/prebuilt-routes-v1.json`) is sent through the application's own
route code (an in-process ASGI client over `create_app`), so a pre-built body is exactly a request's body: the
same admission, watermark, compose and before/after store rule. A request whose watermark has not moved is a
store hit and composes nothing (about 50 ms), so the pre-build runs every tick (CH5c-R7 C5): it builds
when a watermark or `F` moved, or when a live row expired (`valid_until`). It holds no Site lease. After
the requests it prunes the store to the latest 3 rows per (route, request_key, code_version). The tick reports its
seconds against the EX-3 "at most 50% of the tick limit" rule.

The tick's environment must equal the server's (the cursor keys and manifests are in `code_version`), or the
pre-built rows are never hit. CH5c-R6: the result carries the 16-hex `code_version` prefix, and a process without
every serve key (`watermark.SERVE_KEYS`) stores nothing and reports `SKIPPED_NO_SERVE_ENV`.

WARM-1 (BL-71 part 2, rev 7 §7.1): with `ASSETOPS_PREBUILD_BASE_URL` set, the same requests go over HTTP to that
running serve (`HttpClient`), so the bodies are composed and stored by the serve itself under its own pools.
"""
from __future__ import annotations

import json
import logging
import os
import time
from collections import Counter
from typing import Any

from assetops_backend.chain.composition import build_response_store, code_version, prebuilt_requests
from assetops_backend.chain.response_store import HEADER, mode
from assetops_backend.chain.watermark import SERVE_KEYS

SCOPE_IDS = "/api/estate/portfolio/scope-ids"
LOG = logging.getLogger("assetops.chain.prebuild")


def paths() -> list[str]:
    """Every pre-built request path with its query; a Portfolio request also pre-builds its scope ids (Q9)."""
    out = []
    for req in prebuilt_requests():
        out.append(f"{req.path}?{req.query}")
        if req.path == "/api/estate/portfolio":
            out.append(f"{SCOPE_IDS}?{req.query}")
    return out


def run(url: str | None, client: Any = None) -> dict[str, Any]:
    started = time.perf_counter()
    version = code_version()[:16]
    if mode() != "on":  # the store is off (or compose-only); nothing is stored
        return {"code": "SKIPPED_STORE_OFF", "code_version": version, "requests": 0}
    missing = [k for k in SERVE_KEYS if not os.environ.get(k)]
    if missing:  # CH5c-R6: no server could hit rows built under this process's code_version
        return {"code": "SKIPPED_NO_SERVE_ENV", "missing": missing, "code_version": version, "requests": 0}
    store = build_response_store(url)
    if store is None:
        return {"code": "OK", "skipped": "no database", "code_version": version}
    if client is None:
        client = http_client()  # WARM-1 (BL-71 part 2): the running serve, when one is named
    if client is None:
        from fastapi.testclient import TestClient

        from assetops_backend.main import create_app

        client = TestClient(create_app())
    states: Counter[str] = Counter()
    failed: dict[str, int] = {}
    degraded: dict[str, int] = {}  # INFRA-1: path -> attempts, for every path that was degraded at least once
    still: list[str] = []  # INFRA-1: the paths still degraded after every retry
    connections = _connections(store)
    LOG.info(json.dumps({"event": "prebuild_start", "pg_stat_activity": connections}))
    try:
        for path in paths():
            response = client.get(path)
            attempts = 1
            for wait in RETRY_WAITS:  # INFRA-1 (D-E5.47) rule 5: a 503 or a stale copy is retried after 2, 5, 10 s
                if not _is_degraded(response):
                    break
                _sleep(wait)
                response = client.get(path)
                attempts += 1
            if attempts > 1:
                degraded[path] = attempts
            if _is_degraded(response):
                still.append(path)
            elif response.status_code != 200:
                failed[path] = response.status_code
            else:
                states[response.headers.get(HEADER, "none")] += 1
        pruned = store.prune()
    finally:
        store.dispose()
    code = "DEGRADED" if still else ("FAILED" if failed else "OK")
    return {"code": code, "requests": len(paths()), "states": dict(states), "non_200": failed,
            "degraded": degraded, "still_degraded": still, "pg_stat_activity": connections,
            "pruned": pruned, "code_version": version, "prebuild_ms": int((time.perf_counter() - started) * 1000)}


#: INFRA-1 (D-E5.47) rule 5: the waits before each of the 3 retries of a degraded path.
RETRY_WAITS = (2, 5, 10)
_sleep = time.sleep  # a test moves it


def _is_degraded(response: Any) -> bool:
    """A 503 (`TEMPORARILY_UNAVAILABLE`) or a stale copy served in place of a degraded compose."""
    return response.status_code == 503 or response.headers.get(HEADER) == "stale"


#: WARM-1 (BL-71 part 2): when set (e.g. `http://127.0.0.1:8990`), the pre-build sends its requests to that running
#: serve over HTTP instead of composing them in this process through an in-process ASGI client. The in-process path
#: opened a second set of connection pools beside the serve's (D-E5.47); over HTTP the serve's own pools answer.
BASE_URL_ENV = "ASSETOPS_PREBUILD_BASE_URL"
HTTP_TIMEOUT_SECONDS = 900


class _Headers(dict):
    """Response headers with a case-insensitive `get` (HTTP header names are case-insensitive)."""

    def get(self, key: str, default: Any = None) -> Any:  # type: ignore[override]
        return super().get(key.lower(), default)


class HttpResponse:
    """The two fields the pre-build reads from a response: the status and the headers."""

    def __init__(self, status_code: int, headers: Any) -> None:
        self.status_code = int(status_code)
        self.headers = _Headers((str(k).lower(), v) for k, v in (headers or []))


class HttpClient:
    """`get(path)` against a running serve; a non-2xx status is returned, never raised (the retry rule reads it)."""

    def __init__(self, base_url: str, timeout: float = HTTP_TIMEOUT_SECONDS, opener: Any = None) -> None:
        import urllib.request

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._open = opener or urllib.request.urlopen

    def get(self, path: str) -> HttpResponse:
        import urllib.error

        try:
            with self._open(self.base_url + path, timeout=self.timeout) as response:
                response.read()
                out = HttpResponse(response.status, response.headers.items())
        except urllib.error.HTTPError as error:
            out = HttpResponse(error.code, error.headers.items() if error.headers else [])
        return out


def http_client() -> HttpClient | None:
    """The HTTP client when `ASSETOPS_PREBUILD_BASE_URL` names a serve; None keeps the in-process client."""
    base = os.environ.get(BASE_URL_ENV, "").strip()
    return HttpClient(base) if base else None


def _connections(store: Any) -> int | None:
    """The `pg_stat_activity` count, logged before the prebuild starts (None when it cannot be read)."""
    try:
        return store.connections()
    except Exception as error:  # noqa: BLE001 - a diagnostic; it never stops the prebuild
        LOG.warning(json.dumps({"event": "prebuild_connections_unread", "error": type(error).__name__}))
        return None
