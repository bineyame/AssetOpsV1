"""Test helper: enumerate the paths an app actually serves.

FastAPI 0.141 wraps each `include_router` call in an internal router object, so
`app.routes` is not a flat list of routes and a naive
`{r.path for r in app.routes if hasattr(r, "path")}` silently returns an
incomplete set.

That matters here: the structural half of the Simulator Lab gate test asserts
that NO simulator path is registered when the flag is off, and an enumeration
that quietly misses routes would pass no matter what is served. So this
flattener fails loudly when it meets a route it cannot resolve to a path,
rather than degrading into a vacuous assertion.
"""

from __future__ import annotations

from typing import Any, Iterable

from fastapi import FastAPI

_MAX_DEPTH = 10


def served_paths(app: FastAPI) -> set[str]:
    """Return every path registered on `app`, including included routers."""
    paths: set[str] = set()
    _collect(app.router.routes, paths, depth=0)
    return paths


def _collect(routes: Iterable[Any], paths: set[str], depth: int) -> None:
    assert depth < _MAX_DEPTH, "route tree nested deeper than expected"

    for route in routes:
        # FastAPI's lazily-included router wrapper.
        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            _collect(original_router.routes, paths, depth + 1)
            continue

        nested = getattr(route, "routes", None)
        if nested is not None:
            _collect(nested, paths, depth + 1)
            continue

        path = getattr(route, "path", None)
        assert path is not None, (
            f"Could not resolve a served path for {route!r}. The route inventory "
            "helper must be updated, otherwise gate assertions become vacuous."
        )
        paths.add(path)
