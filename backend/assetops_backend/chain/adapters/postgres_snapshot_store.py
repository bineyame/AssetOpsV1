"""PostgreSQL day-snapshot store (CH-1a, migration 0043).

The sole writer of ``site_day_snapshot`` (architecture guard rule 8): one
INSERT, never an UPDATE, DELETE, upsert or DDL (the 0043 trigger refuses UPDATE
and DELETE). ``read_latest`` answers the latest revision per (Site, day,
subject, measure) for any number of Sites in ONE statement (``DISTINCT ON``
over ``site_day_snapshot_read``); with ``known_at`` it answers what was
computed at or before that instant.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from assetops_backend.chain.ports import SnapshotKey, SnapshotRow

_COLUMNS = (
    "tenant_id, site_id, local_day, subject_kind, subject_ref, measure, evidence_class, revision, expected, "
    "required_seconds, covered_seconds, coverage_pct, grade, value, money, policy_version, calendar_version, "
    "catalogue_version, input_fp"
)

_INSERT = text(
    f"INSERT INTO site_day_snapshot ({_COLUMNS}) VALUES (:tenant_id, :site_id, :local_day, :subject_kind, "
    ":subject_ref, :measure, :evidence_class, :revision, :expected, :required_seconds, :covered_seconds, "
    ":coverage_pct, :grade, CAST(:value AS jsonb), CAST(:money AS jsonb), :policy_version, :calendar_version, "
    ":catalogue_version, :input_fp)"
)

_LATEST = text(
    "SELECT revision, input_fp FROM site_day_snapshot WHERE tenant_id = :t AND site_id = :s AND measure = :m "
    "AND local_day = :d AND subject_kind = :k AND subject_ref = :r ORDER BY revision DESC LIMIT 1"
)

_READ_LATEST = (
    f"SELECT DISTINCT ON (site_id, measure, local_day, subject_kind, subject_ref) {_COLUMNS}, computed_at "
    "FROM site_day_snapshot WHERE tenant_id = :t AND site_id = ANY(CAST(:sites AS uuid[])) "
    "AND local_day BETWEEN :lo AND :hi{measures}{known} "
    "ORDER BY site_id, measure, local_day, subject_kind, subject_ref, revision DESC"
)


def _row(r: Any) -> SnapshotRow:
    m = r._mapping
    return SnapshotRow(
        tenant_id=m["tenant_id"], site_id=m["site_id"], local_day=m["local_day"],
        subject_kind=m["subject_kind"], subject_ref=m["subject_ref"], measure=m["measure"],
        evidence_class=m["evidence_class"], revision=m["revision"], expected=m["expected"],
        required_seconds=m["required_seconds"], covered_seconds=m["covered_seconds"],
        coverage_pct=f"{m['coverage_pct']:.2f}", grade=m["grade"], value=m["value"], money=m["money"],
        policy_version=m["policy_version"], calendar_version=m["calendar_version"],
        catalogue_version=m["catalogue_version"], input_fp=m["input_fp"], computed_at=m["computed_at"],
    )


class PostgresSnapshotStore:
    def __init__(self, database_url: str | None = None, *, engine: Engine | None = None) -> None:
        if engine is None and not database_url:
            raise RuntimeError("DATABASE_URL is not set, so the snapshot store cannot be reached.")
        self._engine = engine or create_engine(database_url, pool_pre_ping=True)
        self._owns_engine = engine is None

    def dispose(self) -> None:
        if self._owns_engine:
            self._engine.dispose()

    def latest(self, key: SnapshotKey) -> tuple[int, str] | None:
        with self._engine.connect() as c:
            r = c.execute(_LATEST, {"t": key.tenant_id, "s": key.site_id, "m": key.measure,
                                    "d": key.local_day, "k": key.subject_kind, "r": key.subject_ref}).first()
        return None if r is None else (int(r.revision), str(r.input_fp))

    def append(self, row: SnapshotRow) -> None:
        params = {
            "tenant_id": row.tenant_id, "site_id": row.site_id, "local_day": row.local_day,
            "subject_kind": row.subject_kind, "subject_ref": row.subject_ref, "measure": row.measure,
            "evidence_class": row.evidence_class, "revision": row.revision, "expected": row.expected,
            "required_seconds": row.required_seconds, "covered_seconds": row.covered_seconds,
            "coverage_pct": row.coverage_pct, "grade": row.grade,
            "value": None if row.value is None else json.dumps(row.value, sort_keys=True),
            "money": None if row.money is None else json.dumps(row.money, sort_keys=True),
            "policy_version": row.policy_version, "calendar_version": row.calendar_version,
            "catalogue_version": row.catalogue_version, "input_fp": row.input_fp,
        }
        with self._engine.begin() as c:
            c.execute(_INSERT, params)

    def read_latest(
        self,
        tenant_id: UUID,
        site_ids: Sequence[UUID],
        from_day: date,
        to_day: date,
        measures: Sequence[str] | None,
        known_at: datetime | None,
    ) -> list[SnapshotRow]:
        params: dict[str, Any] = {"t": tenant_id, "sites": [str(s) for s in site_ids],
                                  "lo": from_day, "hi": to_day}
        measures_sql = ""
        if measures is not None:
            measures_sql = " AND measure = ANY(CAST(:measures AS text[]))"
            params["measures"] = list(measures)
        known_sql = ""
        if known_at is not None:
            known_sql = " AND computed_at <= :k"
            params["k"] = known_at
        sql = text(_READ_LATEST.format(measures=measures_sql, known=known_sql))
        with self._engine.connect() as c:
            return [_row(r) for r in c.execute(sql, params)]
