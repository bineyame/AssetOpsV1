"""CH-5c Q8 (CH5c-R5 R5-1(d)): the pre-build of the stored routes after the tick's Site loop.

Each request of `config/chain/prebuilt-routes-v1.json` (page 1 only, Q11) is sent through the application's own
route code (an in-process ASGI client over `create_app`), so a pre-built body is exactly a request's body: the
same admission, watermark, compose and before/after store rule. A request whose watermark has not moved is a
store hit and composes nothing (about 50 ms), so the pre-build runs every tick (CH5c-R7 C5): it builds
when a watermark or `F` moved, or when a live row expired (`valid_until`). It holds no Site lease. After
the requests it prunes the store to the latest 3 rows per (route, request_key, code_version). The tick reports its
seconds against the EX-3 "at most 50% of the tick limit" rule.

The tick's environment must equal the server's (the cursor keys and manifests are in `code_version`), or the
pre-built rows are never hit. CH5c-R6: the result carries the 16-hex `code_version` prefix, and a process without
every serve key (`watermark.SERVE_KEYS`) stores nothing and reports `SKIPPED_NO_SERVE_ENV`.
"""
from __future__ import annotations

import os
import time
from collections import Counter
from typing import Any

from assetops_backend.chain.composition import build_response_store, code_version, prebuilt_requests
from assetops_backend.chain.response_store import HEADER, mode
from assetops_backend.chain.watermark import SERVE_KEYS

SCOPE_IDS = "/api/estate/portfolio/scope-ids"


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
        from fastapi.testclient import TestClient

        from assetops_backend.main import create_app

        client = TestClient(create_app())
    states: Counter[str] = Counter()
    failed: dict[str, int] = {}
    try:
        for path in paths():
            response = client.get(path)
            if response.status_code != 200:
                failed[path] = response.status_code
            else:
                states[response.headers.get(HEADER, "none")] += 1
        pruned = store.prune()
    finally:
        store.dispose()
    return {"code": "OK" if not failed else "FAILED", "requests": len(paths()), "states": dict(states),
            "non_200": failed, "pruned": pruned, "code_version": version, "prebuild_ms": int((time.perf_counter() - started) * 1000)}
