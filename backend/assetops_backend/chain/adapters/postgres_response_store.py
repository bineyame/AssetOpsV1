"""CH-5c (CH5c-R6 guard fix): the PostgreSQL side of the stored route responses (`chain/response_store.py`).

The sole runtime writer of `chain_response` (migration 0047). It runs exactly two write statements: the
insert-only store of a composed body (`ON CONFLICT (route, request_key, watermark, code_version) DO NOTHING`) and
the prune, which keeps the latest `keep` rows per (route, request_key, code_version) (CH5c-R6: a version never
evicts another version's rows; dead versions are cleared by the W5 reset and the prepare). It also reads the
watermark (`chain_input_change`, see `chain/watermark.py`), the tenant's Sites and the stored row.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, Sequence
from uuid import UUID

from sqlalchemy import create_engine, text

_SITES = "SELECT id, site_code, timezone FROM site WHERE tenant_id = :t ORDER BY id"
_LOOKUP = ("SELECT body, etag FROM chain_response WHERE route = :r AND request_key = :k AND watermark = :w "
           "AND code_version = :v "
           "AND (valid_until IS NULL OR valid_until > greatest(clock_timestamp(), CAST(:now AS timestamptz)))")
#: INFRA-1 (D-E5.47): the newest stored row for (route, request_key, code_version), whatever its watermark and even
#: past `valid_until`: what a degraded compose serves instead of storing its body.
_LATEST_GOOD = ("SELECT body FROM chain_response WHERE route = :r AND request_key = :k AND code_version = :v "
                "ORDER BY built_at DESC LIMIT 1")
#: CH5c-R7 C2: a live row is a miss once either clock passes `valid_until` (the DB clock, and the app clock
#: `read_scope.clock()` the compose compares with): the earlier expiry, the safe direction.
_INSERT = ("INSERT INTO chain_response (tenant_id, route, request_key, watermark, code_version, etag, body, build_ms, "
           "valid_until) VALUES (:t, :r, :k, :w, :v, :e, :b, :ms, :u) "
           "ON CONFLICT (route, request_key, watermark, code_version) "
           "DO UPDATE SET etag = EXCLUDED.etag, body = EXCLUDED.body, build_ms = EXCLUDED.build_ms, "
           "valid_until = EXCLUDED.valid_until, built_at = EXCLUDED.built_at "
           "WHERE chain_response.valid_until IS NOT NULL "
           "AND chain_response.valid_until <= greatest(clock_timestamp(), CAST(:now AS timestamptz))")
#: CH-5c2: an expired live row (same route, key, W and version) is replaced by the re-warmed body (C5: the pre-build
#: re-warms it within a tick); a row still valid, or historical, is kept and the insert reports nothing (L1).
_PRUNE = ("DELETE FROM chain_response x USING (SELECT ctid, row_number() OVER (PARTITION BY route, request_key, "
          "code_version ORDER BY built_at DESC) AS n FROM chain_response) old WHERE x.ctid = old.ctid AND old.n > :keep")
_WATERMARK = ("SELECT count(*) FROM chain_input_change WHERE (tenant_id = :t OR tenant_id IS NULL) "
              "AND (site_id = ANY(:s) OR site_id IS NULL)")
_TENANT_WATERMARK = "SELECT count(*) FROM chain_input_change WHERE (tenant_id = :t OR tenant_id IS NULL)"


def read_watermark(c: Any, tenant_id: UUID, site_ids: Iterable[UUID] | None) -> str:
    """The watermark on connection `c`, as the first statement of its transaction (CH5c-R5 R5-1(a)). `site_ids`
    None is every Site of the tenant (the estate routes): the tenant's rows and the tenant-wide NULL rows."""
    if site_ids is None:
        return f"cic:{c.execute(text(_TENANT_WATERMARK), {'t': tenant_id}).scalar_one()}"
    sites = sorted({UUID(str(s)) for s in site_ids}, key=str)
    count = c.execute(text(_WATERMARK), {"t": tenant_id, "s": sites}).scalar_one()
    return f"cic:{count}"


class _Snapshot:
    """One short REPEATABLE READ transaction's reads (the port `ResponseStore` speaks)."""

    def __init__(self, c: Any) -> None:
        self._c = c

    def watermark(self, tenant_id: UUID, site_ids: Iterable[UUID] | None) -> str:
        return read_watermark(self._c, tenant_id, site_ids)

    def sites(self, tenant_id: UUID) -> list[tuple[str, str, str]]:
        return [(str(r.id), r.site_code, r.timezone) for r in self._c.execute(text(_SITES), {"t": tenant_id}).all()]

    def lookup(self, route: str, key: str, watermark: str, version: str, now: Any) -> tuple[bytes, str] | None:
        row = self._c.execute(text(_LOOKUP), {"r": route, "k": key, "w": watermark, "v": version,
                                              "now": now}).first()
        return None if row is None else (bytes(row.body), row.etag)


class PostgresResponseRows:
    def __init__(self, database_url: str | None = None, *, engine: Any = None) -> None:
        self._url, self._engine = database_url, engine

    def _e(self) -> Any:
        if self._engine is None:
            self._engine = create_engine(self._url, pool_pre_ping=True, pool_size=2, max_overflow=2)
        return self._engine

    def dispose(self) -> None:
        if self._engine is not None and self._url is not None:
            self._engine.dispose()

    def read(self, work: Callable[[_Snapshot], Any]) -> Any:
        with self._e().connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
            return work(_Snapshot(c))

    def latest_good(self, route: str, key: str, version: str) -> bytes | None:
        """INFRA-1: the newest stored body for (route, request_key, code_version), or None."""
        with self._e().connect() as c:
            row = c.execute(text(_LATEST_GOOD), {"r": route, "k": key, "v": version}).first()
        return None if row is None else bytes(row.body)

    def connections(self) -> int:
        """INFRA-1: the server's `pg_stat_activity` count (the prebuild logs it before it starts)."""
        with self._e().connect() as c:
            return int(c.execute(text("SELECT count(*) FROM pg_stat_activity")).scalar_one())

    def insert(self, tenant_id: UUID, watermark: str, version: str, build_ms: int, valid_until: Any,
               rows: Sequence[tuple[str, str, str, bytes]], now: Any = None) -> set[str]:
        """Store (route, request_key, etag, body) rows under one watermark, in one transaction; the routes whose
        row was inserted (L1: `ON CONFLICT DO NOTHING` reports rowcount 0 for a row already there)."""
        inserted: set[str] = set()
        with self._e().begin() as c:
            for route, key, tag, body in rows:
                if c.execute(text(_INSERT), {"t": tenant_id, "r": route, "k": key, "w": watermark, "v": version,
                                             "e": tag, "b": body, "ms": build_ms, "u": valid_until,
                                             "now": now}).rowcount:
                    inserted.add(route)
        return inserted

    def prune(self, keep: int) -> int:
        with self._e().begin() as c:
            return c.execute(text(_PRUNE), {"keep": keep}).rowcount
