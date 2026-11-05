"""CH-5c (CH5c-R3 R6, CH5c-R4 W1-W5, CH5c-R5 R5-1): stored route responses.

A stored route is served from `chain_response` when its watermark (`chain/watermark.py`) and code version are
unchanged; otherwise it is composed as before and stored. The before/after rule (R5-1):

- (a) one short REPEATABLE READ transaction reads the watermark W first, then the admitted Site set (the tenant's
  `site` rows filtered by the route's own admission predicate), then the stored row for
  (route, request_key, W, code_version); it is closed before the first compose read.
- (b) the compose runs as today, inside a read scope created after (a) (`read_scope.fresh`); there is no
  cross-request cache.
- (c) on a miss the watermark is re-read in a new short transaction: equal to W, the body is stored under W on the
  write engine in its own transaction (`ON CONFLICT DO NOTHING`; a failure is logged and never fails the request);
  different, the body is served and not stored, and the race is logged.

Every count only rises, and every compose read starts after W's snapshot, so a body stored under W is never older
than W; storing only when W is unchanged after the compose keeps stored bodies quiet-state bodies.

The served bytes are the stored bytes: the body is serialised once exactly as FastAPI's `JSONResponse` renders it,
and the response carries `ETag` = sha256(route, request_key, W, code_version). `request_key` is the canonical JSON of
the route, the tenant, the sorted admitted Site ids and the parsed request, so equivalent requests (a defaulted
lens or limit, a board `date` against its `from`/`to`) share one key.

`ASSETOPS_RESPONSE_STORE=off` turns the store off (every request composes; the W6 guard and the uncached probe use
it). It never changes body bytes, so it is not a `COMPOSER_ENV` setting.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response
from sqlalchemy import create_engine, text

from assetops_backend import perf, read_scope
from assetops_backend.chain.watermark import code_version, read_watermark

LOG = logging.getLogger("assetops.chain.response_store")
HEADER = "X-AssetOps-Stored"  # hit | stored | race | unstored (a store failure); never body bytes

_SITES = "SELECT id, site_code FROM site WHERE tenant_id = :t ORDER BY id"
_LOOKUP = ("SELECT body, etag FROM chain_response WHERE route = :r AND request_key = :k AND watermark = :w "
           "AND code_version = :v")
_INSERT = ("INSERT INTO chain_response (tenant_id, route, request_key, watermark, code_version, etag, body, build_ms) "
           "VALUES (:t, :r, :k, :w, :v, :e, :b, :ms) ON CONFLICT (route, request_key, watermark, code_version) "
           "DO NOTHING")
_PRUNE = ("DELETE FROM chain_response x USING (SELECT ctid, row_number() OVER (PARTITION BY route, request_key "
          "ORDER BY built_at DESC) AS n FROM chain_response) old WHERE x.ctid = old.ctid AND old.n > :keep")


def render(body: Any) -> bytes:
    """The bytes FastAPI's `JSONResponse` would send for `body` (serialised once, served and stored as is)."""
    return json.dumps(jsonable_encoder(body), ensure_ascii=False, allow_nan=False, indent=None,
                      separators=(",", ":")).encode("utf-8")


def _canonical(value: Any) -> str:
    return json.dumps(jsonable_encoder(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def request_key(route: str, tenant_id: UUID, site_ids: Iterable[Any], request: Mapping[str, Any]) -> str:
    return _canonical({"route": route, "tenant": str(tenant_id), "sites": sorted(str(s) for s in site_ids),
                       "request": dict(request)})


def etag(route: str, key: str, watermark: str, version: str) -> str:
    return hashlib.sha256("\x00".join((route, key, watermark, version)).encode("utf-8")).hexdigest()


def parsed_key(parsed: Any) -> dict[str, Any]:
    """A parsed estate request (`estate.scope.EstateRequest`) as a `request_key` part: every field after defaulting,
    so a `lens`-less or `limit`-less request shares the key of its defaulted twin; `known_at` stays None when absent."""
    return {"kind": parsed.kind, "from": parsed.from_, "to": parsed.to, "known_at": parsed.known_at,
            "lens": parsed.lens, "state": parsed.state_filter, "limit": parsed.limit, "cursor": parsed.cursor}


@dataclass(frozen=True)
class StoredRoute:
    """One stored-route request. `admit(site_code)` is the route's admission predicate (the composer's own);
    `sites` fixes the admitted set instead (the board's one Site). `watermark_sites` None is every tenant Site."""
    route: str
    tenant_id: UUID
    request: Mapping[str, Any]
    admit: Callable[[str], bool] | None = None
    sites: tuple[UUID, ...] | None = None
    watermark_sites: tuple[UUID, ...] | None = None


class ResponseStore:
    def __init__(self, database_url: str | None = None, *, engine: Any = None, keep: int = 3) -> None:
        self._url, self._engine, self.keep = database_url, engine, keep

    def _e(self) -> Any:
        if self._engine is None:
            self._engine = create_engine(self._url, pool_pre_ping=True, pool_size=2, max_overflow=2)
        return self._engine

    def dispose(self) -> None:
        if self._engine is not None and self._url is not None:
            self._engine.dispose()

    def _read(self, work: Callable[[Any], Any]) -> Any:
        with self._e().connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
            return work(c)

    def watermark(self, req: StoredRoute) -> str:
        return self._read(lambda c: read_watermark(c, req.tenant_id, req.watermark_sites))

    def serve(self, req: StoredRoute, compose: Callable[[], Mapping[str, Any]]) -> Response:
        """Serve `req.route`. `compose()` returns {route: body} for `req.route` and any sibling sub-route composed
        by the same call (the Portfolio and its scope-ids), each stored under its own key and the same W."""
        version = code_version()

        def lookup(c: Any) -> tuple[str, tuple[str, ...], Any]:
            w = read_watermark(c, req.tenant_id, req.watermark_sites)  # (a) the first statement
            if req.sites is not None:
                sites = tuple(str(s) for s in req.sites)
            else:
                rows = c.execute(text(_SITES), {"t": req.tenant_id}).all()
                sites = tuple(str(r.id) for r in rows if req.admit is None or req.admit(r.site_code))
            key = request_key(req.route, req.tenant_id, sites, req.request)
            row = c.execute(text(_LOOKUP), {"r": req.route, "k": key, "w": w, "v": version}).first()
            return w, sites, row

        try:
            with perf.timed("store.lookup"):
                w, sites, row = self._read(lookup)
        except Exception as error:  # noqa: BLE001 - the store never fails a request: compose, do not store
            LOG.warning(json.dumps({"event": "stored_route_lookup_failed", "route": req.route,
                                    "error": f"{type(error).__name__}: {error}"[:500]}))
            with read_scope.fresh(req.route):
                body = render(compose()[req.route])
            return Response(content=body, media_type="application/json", headers={HEADER: "unstored"})
        if row is not None:
            return _response(bytes(row.body), row.etag, "hit")
        started = time.perf_counter()
        with read_scope.fresh(req.route):  # (b) the compose memo starts after (a)
            bodies = compose()
        build_ms = int((time.perf_counter() - started) * 1000)
        rendered = {route: render(body) for route, body in bodies.items()}
        keys = {route: request_key(route, req.tenant_id, sites, req.request) for route in rendered}
        tags = {route: etag(route, keys[route], w, version) for route in rendered}
        with perf.timed("store.recheck"):
            after = self.watermark(req)  # (c) a new short transaction
        if after != w:
            LOG.info(json.dumps({"event": "stored_route_race", "route": req.route, "before": w, "after": after}))
            return _response(rendered[req.route], tags[req.route], "race")
        state = "stored"
        try:
            with perf.timed("store.insert"), self._e().begin() as c:
                for route, body in rendered.items():
                    c.execute(text(_INSERT), {"t": req.tenant_id, "r": route, "k": keys[route], "w": w, "v": version,
                                              "e": tags[route], "b": body, "ms": build_ms})
        except Exception as error:  # noqa: BLE001 - Q10: a store failure is logged and never fails the request
            state = "unstored"
            LOG.warning(json.dumps({"event": "stored_route_insert_failed", "route": req.route,
                                    "error": f"{type(error).__name__}: {error}"[:500]}))
        return _response(rendered[req.route], tags[req.route], state)

    def prune(self) -> int:
        """Q8: keep the latest `keep` rows per (route, request_key); the pre-build calls it, never a GET."""
        with self._e().begin() as c:
            return c.execute(text(_PRUNE), {"keep": self.keep}).rowcount


def _response(body: bytes, tag: str, state: str) -> Response:
    return Response(content=body, media_type="application/json", headers={"ETag": f'"{tag}"', HEADER: state})


def finish(out: Response, response: Response) -> Response:
    """Carry the injected response's headers (`Server-Timing`, set by `perf.route` on exit) onto a returned
    `Response`, which FastAPI does not merge itself."""
    for name, value in response.headers.items():
        if name.lower() not in ("content-length", "content-type"):
            out.headers[name] = value
    return out


def enabled() -> bool:
    return os.environ.get("ASSETOPS_RESPONSE_STORE", "on").strip().lower() not in ("off", "0", "false", "no")


def build_response_store(database_url: str | None) -> ResponseStore | None:
    return ResponseStore(database_url) if database_url and enabled() else None
