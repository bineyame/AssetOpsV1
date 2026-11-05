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

The store is ON unless `ASSETOPS_RESPONSE_STORE=off` (CH-5c2); off, every request composes (the uncached probe);
`compose` composes every request inside the compose scope and stores nothing (the W6 guard). It never changes body bytes, so it is not a `COMPOSER_ENV` setting.

CH5c-R6: the SQL lives below the port in `chain/adapters/postgres_response_store.py` (the sole writer of
`chain_response`); `chain.composition.build_response_store` wires it with `code_version`.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from datetime import time as dtime
from typing import Any, Callable, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response

from assetops_backend import perf, read_scope

LOG = logging.getLogger("assetops.chain.response_store")
HEADER = "X-AssetOps-Stored"  # hit | stored | race | unstored (a store failure) | composed; never body bytes

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
    """`rows` is the `chain_response` port (`read(work)` runs `work(snapshot)` in one short REPEATABLE READ
    transaction, the snapshot offering `watermark`, `sites` and `lookup`; `insert` returns the routes it inserted;
    `prune`, `dispose`); `version()` is the process's `code_version`; `files(site_codes)` is the F2 file-state term
    (CH5c-R7 H1), appended to the DB watermark. `compose_only` (`ASSETOPS_RESPONSE_STORE=compose`, the W6 probe)
    composes every request under the compose scope and touches no store row."""

    def __init__(self, rows: Any, version: Callable[[], str], *, keep: int = 3,
                 files: Callable[[Sequence[str]], str] | None = None, compose_only: bool = False) -> None:
        self._rows, self._version, self.keep = rows, version, keep
        self._files, self.compose_only = files, compose_only

    def dispose(self) -> None:
        self._rows.dispose()

    def _state(self, c: Any, req: StoredRoute) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
        """(W, admitted Site ids, their time zones) on snapshot `c`: the DB watermark as the first statement, then
        the Sites, then `F` over the request's Sites (every tenant Site for an estate route, CH5c2-R1 Q6)."""
        w = c.watermark(req.tenant_id, req.watermark_sites)  # (a) the first statement
        rows = c.sites(req.tenant_id)
        if req.sites is not None:
            sites = tuple(str(s) for s in req.sites)
        else:
            sites = tuple(r[0] for r in rows if req.admit is None or req.admit(r[1]))
        chosen = set(sites)
        zones = tuple(sorted({r[2] for r in rows if r[0] in chosen}))
        if self._files is not None:
            codes = [r[1] for r in rows if req.sites is None or r[0] in chosen]
            w = f"{w}|f:{self._files(codes)}"
        return w, sites, zones

    def watermark(self, req: StoredRoute) -> str:
        return self._rows.read(lambda c: self._state(c, req)[0])

    def _composed(self, req: StoredRoute, compose: Callable[[], Mapping[str, Any]]) -> tuple[dict[str, Any], Any]:
        with read_scope.fresh(req.route) as sc, read_scope.composing(req.route):
            return dict(compose()), sc

    def serve(self, req: StoredRoute, compose: Callable[[], Mapping[str, Any]]) -> Response:
        """Serve `req.route`. `compose()` returns {route: body} for `req.route` and any sibling sub-route composed
        by the same call (the Portfolio and its scope-ids), each stored under its own key and the same W."""
        if self.compose_only:
            bodies, _ = self._composed(req, compose)
            return _response(render(bodies[req.route]), None, "composed")
        version = self._version()
        now = read_scope.clock()

        def lookup(c: Any) -> tuple[str, tuple[str, ...], tuple[str, ...], Any]:
            w, sites, zones = self._state(c, req)
            key = request_key(req.route, req.tenant_id, sites, req.request)
            return w, sites, zones, c.lookup(req.route, key, w, version, now)

        try:
            with perf.timed("store.lookup"):
                w, sites, zones, row = self._rows.read(lookup)
        except Exception as error:  # noqa: BLE001 - the store never fails a request: compose, do not store
            _warn("stored_route_lookup_failed", req, error)
            bodies, _ = self._composed(req, compose)
            return _response(render(bodies[req.route]), None, "unstored")
        if row is not None:
            return _response(row[0], row[1], "hit")
        started = time.perf_counter()
        bodies, sc = self._composed(req, compose)  # (b) the compose memo starts after (a)
        build_ms = int((time.perf_counter() - started) * 1000)
        rendered = {route: render(body) for route, body in bodies.items()}
        until = valid_until(sc.boundaries, now, zones, live=req.request.get("known_at") is None)
        try:
            keys = {route: request_key(route, req.tenant_id, sites, req.request) for route in rendered}
            tags = {route: etag(route, keys[route], w, version) for route in rendered}
            with perf.timed("store.recheck"):
                after = self.watermark(req)  # (c) a new short transaction
            if after != w:
                LOG.info(json.dumps({"event": "stored_route_race", "route": req.route, "before": w, "after": after}))
                return _response(rendered[req.route], None, "race")  # L1: a body never stored carries no ETag
            with perf.timed("store.insert"):
                inserted = self._rows.insert(req.tenant_id, w, version, build_ms, until,
                                             [(route, keys[route], tags[route], body)
                                              for route, body in rendered.items()])
        except Exception as error:  # noqa: BLE001 - M1/Q10: a store failure after compose never fails the request
            _warn("stored_route_store_failed", req, error)
            return _response(rendered[req.route], None, "unstored")
        if req.route not in inserted:  # L1: `ON CONFLICT` kept another row; this body's tag is not stored
            return _response(rendered[req.route], None, "race")
        return _response(rendered[req.route], tags[req.route], "stored")

    def prune(self) -> int:
        """Q8 (CH5c-R6): keep the latest `keep` rows per (route, request_key, code_version); a version never evicts
        another version's rows. The pre-build calls it, never a GET."""
        return self._rows.prune(self.keep)


#: CH5c-R7 C2: the clock margin under every boundary (app/DB skew on one host).
MARGIN = timedelta(seconds=1)
#: CH5c-R7 C2: a registration is live when its `at` is no earlier than the request instant less this slack (a live
#: read instant is captured during the compose; a historical `k` is a fixed earlier instant). A historical `k`
#: within the slack of now counts as live: earlier expiry, the safe direction.
LIVE_SLACK = timedelta(seconds=1)


def valid_until(boundaries: Iterable[tuple[datetime, datetime]], now: datetime, zones: Iterable[str], *,
                live: bool) -> datetime | None:
    """CH5c-R7 C2: min(every live registered boundary later than its own `at`, the earliest next local midnight
    over the request's Sites) - 1 s. A historical request with no live registration never expires (None)."""
    marks = [b for b, at in boundaries if b > at and at >= now - LIVE_SLACK]
    if not live and not marks:
        return None
    for zone in tuple(zones) or ("UTC",):
        z = ZoneInfo(zone)
        local = now.astimezone(z)
        marks.append(datetime.combine(local.date() + timedelta(days=1), dtime(0), tzinfo=z))
    return min(marks) - MARGIN


def _warn(event: str, req: StoredRoute, error: Exception) -> None:
    LOG.warning(json.dumps({"event": event, "route": req.route, "error": f"{type(error).__name__}: {error}"[:500]}))


def _response(body: bytes, tag: str | None, state: str) -> Response:
    headers = {HEADER: state}
    if tag is not None:
        headers["ETag"] = f'"{tag}"'
    return Response(content=body, media_type="application/json", headers=headers)


def finish(out: Response, response: Response) -> Response:
    """Carry the injected response's headers (`Server-Timing`, set by `perf.route` on exit) onto a returned
    `Response`, which FastAPI does not merge itself."""
    for name, value in response.headers.items():
        if name.lower() not in ("content-length", "content-type"):
            out.headers[name] = value
    return out


def mode() -> str:
    """CH-5c2 (CH5c-R7): `on` by default; `off` (`off`/`0`/`false`/`no`) composes every request outside the store;
    `compose` composes every request inside the compose scope and stores nothing (the W6 probe, the F4 guard)."""
    value = os.environ.get("ASSETOPS_RESPONSE_STORE", "on").strip().lower()
    if value in ("off", "0", "false", "no"):
        return "off"
    return "compose" if value == "compose" else "on"


def enabled() -> bool:
    """CH-5c2: on unless `ASSETOPS_RESPONSE_STORE` opts out."""
    return mode() != "off"
