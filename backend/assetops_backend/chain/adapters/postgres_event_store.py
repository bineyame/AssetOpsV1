"""CH-1b: the PostgreSQL event store (build sheet CH-1b §3 and §7; ruling CH1b-R Q2).

- `event_consumption`: INSERT only (one row per consumer and event).
- `snapshot_dirty`: the mutable rebuild queue. The consumer upserts with `ON CONFLICT DO UPDATE SET marked_at`
  (a re-mark during a build is not lost), and the drain compare-and-deletes on the `marked_at` it read.
- `event_outbox`: written by the 0044 triggers. This module's one INSERT records the backfill's `backfill.site`
  provenance event (ruling CH1b-R Q2), with `ON CONFLICT DO NOTHING`.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from assetops_backend.chain.drain import DirtyRow
from assetops_backend.chain.events import Event, Mark
from assetops_backend.chain.ports import SiteRef

_UNCONSUMED = (
    "SELECT o.event_id, o.type, o.schema_version, o.occurred_at, o.recorded_at, o.source, o.tenant_id, o.site_id, "
    "o.subject, o.payload FROM event_outbox o WHERE o.tenant_id = :t AND o.site_id = :s AND o.type = ANY(:types) "
    "AND NOT EXISTS (SELECT 1 FROM event_consumption x WHERE x.consumer = :c AND x.event_id = o.event_id) "
    "ORDER BY o.recorded_at, o.event_id LIMIT :n")

_PENDING = (
    "SELECT count(*) FROM event_outbox o WHERE o.tenant_id = :t AND o.site_id = :s AND o.type = ANY(:types) "
    "AND NOT EXISTS (SELECT 1 FROM event_consumption x WHERE x.consumer = :c AND x.event_id = o.event_id)")

_SITE = "SELECT id, site_code, site_type, timezone FROM site WHERE tenant_id = :t AND id = :s"

_MARK = (
    "INSERT INTO snapshot_dirty (tenant_id, site_id, local_day, measure, first_event_id) "
    "VALUES (:t, :s, :d, :m, :e) "
    "ON CONFLICT (tenant_id, site_id, local_day, measure) DO UPDATE SET marked_at = clock_timestamp()")

_CONSUMED = "INSERT INTO event_consumption (consumer, event_id) VALUES (:c, :e)"

#: Rows per multi-row VALUES statement of a page write: 5 binds a mark row, so 1,000 rows stay far below the
#: driver's bind limit; a page with more coalesced marks writes several statements inside its one transaction.
_PAGE_ROWS = 1000
_BIND = re.compile(r":([a-z_]+)")


def _values(sql: str, rows: list[dict]) -> tuple[str, dict]:
    """The declared one-row statement widened to a multi-row VALUES list (ruling CH1b-R2 note 3): its one VALUES
    tuple is repeated once per row with each bind suffixed by the row index. Nothing else in the text changes, so
    the statement stays the guarded insert-only shape with the same ON CONFLICT arbiter."""
    head, sep, rest = sql.partition(" VALUES ")
    close = rest.index(")") + 1
    row, tail = rest[:close], rest[close:]
    tuples = ", ".join(_BIND.sub(lambda m: f":{m.group(1)}_{i}", row) for i in range(len(rows)))
    params = {f"{k}_{i}": v for i, r in enumerate(rows) for k, v in r.items()}
    return head + sep + tuples + tail, params


_POP = ("SELECT local_day, measure, marked_at FROM snapshot_dirty WHERE tenant_id = :t AND site_id = :s "
        "ORDER BY local_day, measure LIMIT :n")

_DONE = ("DELETE FROM snapshot_dirty WHERE tenant_id = :t AND site_id = :s AND local_day = :d AND measure = :m "
         "AND marked_at = :at")

_BACKFILL = (
    "INSERT INTO event_outbox (type, schema_version, occurred_at, source, tenant_id, site_id, subject, "
    "idempotency_key) VALUES ('backfill.site', 1, :occurred, 'chain_backfill', :t, :s, CAST(:subject AS jsonb), :k) "
    "ON CONFLICT (source, idempotency_key) DO NOTHING")


class EventStoreUnavailable(RuntimeError):
    pass


class PostgresEventStore:
    def __init__(self, database_url: str | None = None, *, engine: Engine | None = None) -> None:
        if engine is None and not database_url:
            raise EventStoreUnavailable("DATABASE_URL is not set, so the event store cannot be used.")
        self._engine = engine or create_engine(database_url, pool_pre_ping=True)
        self._owns = engine is None

    def dispose(self) -> None:
        if self._owns:
            self._engine.dispose()

    # --- EventPort -------------------------------------------------------------------------------------------

    def unconsumed(self, consumer: str, tenant_id: UUID, site_id: UUID, types: Sequence[str],
                   limit: int) -> list[Event]:
        with self._engine.connect() as c:
            rows = c.execute(text(_UNCONSUMED), {"t": tenant_id, "s": site_id, "types": list(types),
                                                 "c": consumer, "n": int(limit)}).all()
        out = []
        for r in rows:
            subject = r[8] if isinstance(r[8], dict) else json.loads(r[8])
            payload = r[9] if isinstance(r[9], dict) else json.loads(r[9] or "{}")
            out.append(Event(r[0], r[1], int(r[2]), r[3], r[4], r[5], r[6], r[7], subject, payload))
        return out

    def pending(self, consumer: str, tenant_id: UUID, site_id: UUID, types: Sequence[str]) -> int:
        """This Site's events of `types` not yet consumed by `consumer` (the tick reports them as deferred)."""
        with self._engine.connect() as c:
            return int(c.execute(text(_PENDING), {"t": tenant_id, "s": site_id, "types": list(types),
                                                  "c": consumer}).scalar_one())

    def site(self, tenant_id: UUID, site_id: UUID) -> SiteRef | None:
        """The Site the tick stages consume for (type and timezone resolve its events)."""
        with self._engine.connect() as c:
            r = c.execute(text(_SITE), {"t": tenant_id, "s": site_id}).first()
        return None if r is None else SiteRef(tenant_id, r[0], r[1], r[2], r[3])

    def mark_and_consume(self, consumer: str, event: Event, marks: Sequence[tuple[date, str]]) -> None:
        with self._engine.begin() as c:
            for day, measure in marks:
                c.execute(text(_MARK), {"t": event.tenant_id, "s": event.site_id, "d": day, "m": measure,
                                        "e": event.event_id})
            c.execute(text(_CONSUMED), {"c": consumer, "e": event.event_id})

    def mark_and_consume_page(self, consumer: str, events: Sequence[Event], marks: Sequence[Mark]) -> None:
        """One transaction per page: the coalesced marks (multi-row upserts), then every consumption row."""
        mark_rows = [{"t": m.tenant_id, "s": m.site_id, "d": m.local_day, "m": m.measure, "e": m.first_event_id}
                     for m in marks]
        if len({(r["t"], r["s"], r["d"], r["m"]) for r in mark_rows}) != len(mark_rows):
            raise ValueError("page marks must be coalesced before the upsert (one row per tenant, Site, day, measure)")
        consumed = [{"c": consumer, "e": ev.event_id} for ev in events]
        with self._engine.begin() as c:
            for sql, rows in ((_MARK, mark_rows), (_CONSUMED, consumed)):
                for i in range(0, len(rows), _PAGE_ROWS):
                    statement, params = _values(sql, rows[i:i + _PAGE_ROWS])
                    c.execute(text(statement), params)

    def site_today(self, tenant_id: UUID, site_id: UUID, tz: str) -> date:
        with self._engine.connect() as c:
            return c.execute(text("SELECT (clock_timestamp() AT TIME ZONE :z)::date"), {"z": tz}).scalar_one()

    # --- DirtyQueue ------------------------------------------------------------------------------------------

    def pop(self, tenant_id: UUID, site_id: UUID, limit: int) -> list[DirtyRow]:
        with self._engine.connect() as c:
            rows = c.execute(text(_POP), {"t": tenant_id, "s": site_id, "n": int(limit)}).all()
        return [DirtyRow(r[0], r[1], r[2]) for r in rows]

    def queued(self, tenant_id: UUID, site_id: UUID) -> int:
        with self._engine.connect() as c:
            return int(c.execute(text("SELECT count(*) FROM snapshot_dirty WHERE tenant_id = :t AND site_id = :s"),
                                 {"t": tenant_id, "s": site_id}).scalar_one())

    def done(self, tenant_id: UUID, site_id: UUID, row: DirtyRow) -> bool:
        with self._engine.begin() as c:
            deleted = c.execute(text(_DONE), {"t": tenant_id, "s": site_id, "d": row.local_day, "m": row.measure,
                                              "at": row.marked_at}).rowcount
        return deleted == 1

    # --- the backfill's provenance event (ruling CH1b-R Q2) -------------------------------------------------

    def record_backfill(self, tenant_id: UUID, site_id: UUID, occurred_at: datetime, subject: dict[str, Any],
                        idempotency_key: str) -> None:
        with self._engine.begin() as c:
            c.execute(text(_BACKFILL), {"t": tenant_id, "s": site_id, "occurred": occurred_at,
                                        "subject": json.dumps(subject, sort_keys=True, default=str),
                                        "k": idempotency_key})


__all__ = ["EventStoreUnavailable", "PostgresEventStore"]
