"""PostgreSQL stored read-period store (ANY-1 AR-1, migration 0059).

The sole writer of ``site_period_read`` and ``revision_provenance`` (architecture guard rule 8): one INSERT each, never
an UPDATE, DELETE, upsert or DDL (the 0059 triggers refuse UPDATE and DELETE). A provenance block is inserted once per
(assessment revision, builder version); a concurrent second insert loses on the primary key and is reported as not
written, never overwritten.

``read_latest`` answers the latest revision per (Site, kind, period) for any number of Sites, kinds and days in ONE
statement (``DISTINCT ON`` over ``site_period_read_day``); with ``known_at`` it answers what was computed at or
before that instant. ``unconsumed_at`` and ``dirty_marks`` are the PENDING-at-k reads over the append-only
``event_outbox`` / ``event_consumption`` ledgers and the live ``snapshot_dirty`` queue (SELECT only).
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from assetops_backend.chain.events import Event
from assetops_backend.chain.ports import PeriodKey, PeriodRow, ProvenanceBlock

_COLUMNS = ("tenant_id, site_id, kind, period_start, period_end, local_day, revision, builder_version, input_fp, "
            "state, body")

_INSERT = text(
    f"INSERT INTO site_period_read ({_COLUMNS}) VALUES (:tenant_id, :site_id, :kind, :period_start, :period_end, "
    ":local_day, :revision, :builder_version, :input_fp, :state, CAST(:body AS jsonb))"
)

_INSERT_PROVENANCE = text(
    "INSERT INTO revision_provenance (assessment_revision_id, builder_version, tenant_id, block) "
    "VALUES (:r, :v, :t, CAST(:block AS jsonb))"
)

_LATEST = text(
    "SELECT revision, input_fp, builder_version FROM site_period_read WHERE tenant_id = :t AND site_id = :s "
    "AND kind = :k AND period_start = :p ORDER BY revision DESC LIMIT 1"
)

_READ_LATEST = (
    f"SELECT DISTINCT ON (site_id, kind, period_start) {_COLUMNS}, computed_at FROM site_period_read "
    "WHERE tenant_id = :t AND site_id = ANY(CAST(:sites AS uuid[])) AND kind = ANY(CAST(:kinds AS text[])) "
    "AND local_day BETWEEN :lo AND :hi{known} "
    "ORDER BY site_id, kind, period_start, revision DESC"
)

_PROVENANCE = text(
    "SELECT assessment_revision_id, block FROM revision_provenance WHERE tenant_id = :t "
    "AND assessment_revision_id = ANY(CAST(:ids AS uuid[])) AND builder_version = :v"
)

#: PENDING-at-k (architect answer §4 "Late and corrected data"): recorded at or before k and not consumed by the
#: snapshots consumer by k. Live (k null): the transaction's clock.
_UNCONSUMED_AT = (
    "SELECT o.event_id, o.type, o.schema_version, o.occurred_at, o.recorded_at, o.source, o.tenant_id, o.site_id, "
    "o.subject, o.payload FROM event_outbox o WHERE o.tenant_id = :t AND o.site_id = ANY(CAST(:sites AS uuid[])) "
    "AND o.type = ANY(CAST(:types AS text[])) AND o.recorded_at <= {k} "
    "AND NOT EXISTS (SELECT 1 FROM event_consumption x WHERE x.consumer = 'snapshots' "
    "AND x.event_id = o.event_id AND x.processed_at <= {k}) ORDER BY o.recorded_at, o.event_id"
)

_DIRTY = text(
    "SELECT site_id, local_day, measure FROM snapshot_dirty WHERE tenant_id = :t "
    "AND site_id = ANY(CAST(:sites AS uuid[])) AND measure = ANY(CAST(:kinds AS text[])) "
    "AND local_day BETWEEN :lo AND :hi ORDER BY site_id, local_day, measure"
)


def _json(value: Any) -> Any:
    return value if isinstance(value, (dict, list)) or value is None else json.loads(value)


def _row(r: Any) -> PeriodRow:
    m = r._mapping
    return PeriodRow(
        tenant_id=m["tenant_id"], site_id=m["site_id"], kind=m["kind"], period_start=m["period_start"],
        period_end=m["period_end"], local_day=m["local_day"], revision=m["revision"],
        builder_version=m["builder_version"], input_fp=m["input_fp"], state=m["state"], body=_json(m["body"]),
        computed_at=m["computed_at"],
    )


class PostgresPeriodReadStore:
    def __init__(self, database_url: str | None = None, *, engine: Engine | None = None) -> None:
        if engine is None and not database_url:
            raise RuntimeError("DATABASE_URL is not set, so the period read store cannot be reached.")
        self._engine = engine or create_engine(database_url, pool_pre_ping=True)
        self._owns_engine = engine is None

    def dispose(self) -> None:
        if self._owns_engine:
            self._engine.dispose()

    def latest(self, key: PeriodKey) -> tuple[int, str, str] | None:
        with self._engine.connect() as c:
            r = c.execute(_LATEST, {"t": key.tenant_id, "s": key.site_id, "k": key.kind,
                                    "p": key.period_start}).first()
        return None if r is None else (int(r.revision), str(r.input_fp), str(r.builder_version))

    def append(self, row: PeriodRow) -> None:
        params = {
            "tenant_id": row.tenant_id, "site_id": row.site_id, "kind": row.kind,
            "period_start": row.period_start, "period_end": row.period_end, "local_day": row.local_day,
            "revision": row.revision, "builder_version": row.builder_version, "input_fp": row.input_fp,
            "state": row.state, "body": json.dumps(row.body, sort_keys=True),
        }
        with self._engine.begin() as c:
            c.execute(_INSERT, params)

    def read_latest(
        self,
        tenant_id: UUID,
        site_ids: Sequence[UUID],
        kinds: Sequence[str],
        from_day: date,
        to_day: date,
        known_at: datetime | None,
    ) -> list[PeriodRow]:
        params: dict[str, Any] = {"t": tenant_id, "sites": [str(s) for s in site_ids], "kinds": list(kinds),
                                  "lo": from_day, "hi": to_day}
        known_sql = ""
        if known_at is not None:
            known_sql = " AND computed_at <= :k"
            params["k"] = known_at
        with self._engine.connect() as c:
            return [_row(r) for r in c.execute(text(_READ_LATEST.format(known=known_sql)), params)]

    def provenance(self, tenant_id: UUID, revision_ids: Sequence[UUID],
                   builder_version: str) -> dict[UUID, dict[str, Any]]:
        with self._engine.connect() as c:
            rows = c.execute(_PROVENANCE, {"t": tenant_id, "ids": [str(i) for i in revision_ids],
                                           "v": builder_version}).all()
        return {r[0]: _json(r[1]) for r in rows}

    def append_provenance(self, block: ProvenanceBlock) -> bool:
        if self.provenance(block.tenant_id, [block.assessment_revision_id], block.builder_version):
            return False
        try:
            with self._engine.begin() as c:
                c.execute(_INSERT_PROVENANCE, {"r": block.assessment_revision_id, "v": block.builder_version,
                                               "t": block.tenant_id,
                                               "block": json.dumps(block.block, sort_keys=True)})
        except IntegrityError:
            return False  # a concurrent builder stored it first; the stored block is never overwritten
        return True

    def unconsumed_at(self, tenant_id: UUID, site_ids: Sequence[UUID], types: Sequence[str],
                      known_at: datetime | None) -> list[Event]:
        names = sorted({t.partition("@")[0] for t in types})
        params: dict[str, Any] = {"t": tenant_id, "sites": [str(s) for s in site_ids], "types": names}
        k = "clock_timestamp()"
        if known_at is not None:
            k = ":k"
            params["k"] = known_at
        with self._engine.connect() as c:
            rows = c.execute(text(_UNCONSUMED_AT.format(k=k)), params).all()
        wanted = set(types)
        out = []
        for r in rows:
            if f"{r[1]}@{int(r[2])}" not in wanted:
                continue
            out.append(Event(r[0], r[1], int(r[2]), r[3], r[4], r[5], r[6], r[7], _json(r[8]),
                             _json(r[9]) or {}))
        return out

    def dirty_marks(self, tenant_id: UUID, site_ids: Sequence[UUID], kinds: Sequence[str],
                    from_day: date, to_day: date) -> list[tuple[UUID, date, str]]:
        with self._engine.connect() as c:
            rows = c.execute(_DIRTY, {"t": tenant_id, "sites": [str(s) for s in site_ids], "kinds": list(kinds),
                                      "lo": from_day, "hi": to_day}).all()
        return [(r[0], r[1], r[2]) for r in rows]
