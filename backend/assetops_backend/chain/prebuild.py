"""CH-5c Q8 (CH5c-R5 R5-1(d)): the pre-build of the stored routes after the tick's Site loop.

Each request of `config/chain/prebuilt-routes-v1.json` (page 1 only, Q11) is sent through the application's own
route code (an in-process ASGI client over `create_app`), so a pre-built body is exactly a request's body: the
same admission, watermark, compose and before/after store rule. A request whose watermark has not moved is a
store hit and composes nothing, so the pre-build only builds when a watermark moved. It holds no Site lease. After
the requests it prunes the store to the latest 3 rows per (route, request_key). The tick reports its seconds
against the EX-3 "at most 50% of the tick limit" rule.

The tick's environment must equal the server's (the cursor keys and manifests are in `code_version`), or the
pre-built rows are never hit.
"""
from __future__ import annotations

import time
from collections import Counter
from typing import Any

from assetops_backend.chain import prebuilt
from assetops_backend.chain.response_store import HEADER, build_response_store

SCOPE_IDS = "/api/estate/portfolio/scope-ids"


def paths() -> list[str]:
    """Every pre-built request path with its query; a Portfolio request also pre-builds its scope ids (Q9)."""
    out = []
    for req in prebuilt.requests():
        out.append(f"{req.path}?{req.query}")
        if req.path == "/api/estate/portfolio":
            out.append(f"{SCOPE_IDS}?{req.query}")
    return out


def run(url: str | None, client: Any = None) -> dict[str, Any]:
    started = time.perf_counter()
    store = build_response_store(url)
    if store is None:
        return {"code": "OK", "skipped": "no database or ASSETOPS_RESPONSE_STORE=off"}
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
            "non_200": failed, "pruned": pruned, "prebuild_ms": int((time.perf_counter() - started) * 1000)}
