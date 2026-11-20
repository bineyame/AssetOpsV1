"""3A1 (spec §4.1, §5; R4, R6, R7, R11, R13, P2, P7): the Postgres commercial record store.

This adapter is the sole runtime writer of the four 0063 tables (registered in
`tools/checks/configuration-persistence.ps1`). It runs exactly one plain `INSERT INTO <table> (...) VALUES (...)`
per table, binding plain parameters, and no UPDATE, DELETE or TRUNCATE; the 0063 triggers refuse every change.

`write_intake` is one READ COMMITTED transaction (R4). It first takes the tenant's commercial advisory lock, then
re-reads the existing records under it, so a concurrent intake that committed while this one waited is seen, and the
decision is made on that state (P2). A dry run takes the lock, decides, and rolls back.

The engine is built with `hide_parameters=True`, and an integrity error leaves as a bare `StoreRefused` carrying only
the constraint's name: the driver's message and DETAIL print the failing row and never survive, not as text, cause
or context (D-2A.11's class, R13).
"""
from __future__ import annotations

from datetime import datetime
from typing import Callable, Mapping
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError

from assetops_backend.commercial.model import (ExistingRecord, IntakeRow, IntakeSummary, Plan, RejectionRow,
                                               RevisionRow, StoreRefused)

_LOCK = text("SELECT pg_advisory_xact_lock(hashtextextended('commercial:' || CAST(:tenant_id AS text), 0))")

_INSERT#: 3A4 (spec §2): an intake's revisions, byte-wise by (source_system, source_record_id); then the superseded ones.
_INTAKE_REVISIONS = text(
    "SELECT " + _REVISION_COLUMNS + " FROM commercial_record_revision v JOIN commercial_record r ON r.id = v.record_id "
    "WHERE v.tenant_id = :t AND v.intake_id = :i "
    "ORDER BY r.source_system COLLATE \"C\", r.source_record_id COLLATE \"C\"")
_REVISIONS_BY_ID = text(
    "SELECT " + _REVISION_COLUMNS + " FROM commercial_record_revision v JOIN commercial_record r ON r.id = v.record_id "
    "WHERE v.tenant_id = :t AND v.id = ANY(:ids)")
_SITE_ZONES = text("SELECT id, timezone FROM site WHERE tenant_id = :t")
_INTAKE = text(
    "INSERT INTO commercial_intake (id, tenant_id, source_type, source_system, provenance, produced_at, batch_sha256, "
    "state, refusal_code, refusal_path, record_count, new_count, revised_count, unchanged_count, refused_count, "
    "entered_by, entered_at) VALUES (:id, :tenant_id, :source_type, :source_system, :provenance, :produced_at, "
    ":batch_sha256, :state, :refusal_code, :refusal_path, :record_count, :new_count, :revised_count, "
    ":unchanged_count, :refused_count, :entered_by, :entered_at)")
_INSERT_RECORD = text(
    "INSERT INTO commercial_record (id, tenant_id, site_id, kind, source_system, source_record_id, first_recorded_at) "
    "VALUES (:id, :tenant_id, :site_id, :kind, :source_system, :source_record_id, :first_recorded_at)")
_INSERT_REVISION = text(
    "INSERT INTO commercial_record_revision (id, tenant_id, record_id, site_id, kind, revision_no, source_version, "
    "intake_id, record_sha256, canonical, provenance, recognition_period, occurred_at, settled_at, effective_from, "
    "effective_to, amount, currency, quantity, unit, status, supersedes_revision_id, recorded_at) VALUES (:id, "
    ":tenant_id, :record_id, :site_id, :kind, :revision_no, :source_version, :intake_id, :record_sha256, :canonical, "
    ":provenance, :recognition_period, :occurred_at, :settled_at, :effective_from, :effective_to, :amount, "
    ":currency, :quantity, :unit, :status, :supersedes_revision_id, :recorded_at)")
_INSERT_REJECTION = text(
    "INSERT INTO commercial_rejection (id, tenant_id, intake_id, record_index, source_record_id, code, path, "
    "recorded_at) VALUES (:id, :tenant_id, :intake_id, :record_index, :source_record_id, :code, :path, :recorded_at)")

_TENANT = text("SELECT slug FROM tenant WHERE id = :t")
_SITES = text("SELECT site_code_key, id FROM site WHERE tenant_id = :t AND site_code_key = ANY(:keys)")
_EXISTING = text(
    "SELECT r.id AS record_id, r.kind, r.site_id, r.source_record_id, v.id AS revision_id, v.revision_no, "
    "v.source_version, v.record_sha256, v.provenance FROM commercial_record r "
    "JOIN commercial_record_revision v ON v.record_id = r.id "
    "WHERE r.tenant_id = :t AND r.source_system = :s AND r.source_record_id = ANY(:ids) "
    "ORDER BY r.id, v.revision_no")

_REVISION_COLUMNS = (
    "v.id, v.tenant_id, v.record_id, v.site_id, v.kind, v.revision_no, v.source_version, v.intake_id, "
    "v.record_sha256, v.canonical, v.provenance, v.recognition_period, v.occurred_at, v.settled_at, v.effective_from, "
    "v.effective_to, v.amount, v.currency, v.quantity, v.unit, v.status, v.supersedes_revision_id, v.recorded_at, "
    "r.source_system, r.source_record_id")
#: R7: the latest revision per record over all of its revisions first; only then the filters. P7: a NULL filter is
#: no filter. 3A4 (D-3A4.7): the `known_at` cutoff sits inside the `DISTINCT ON` subquery, before "latest". The text sort keys are compared byte-wise (`COLLATE "C"`), as the in-memory store compares them.
_LATEST = text(
    "SELECT * FROM (SELECT DISTINCT ON (v.record_id) " + _REVISION_COLUMNS + " "
    "FROM commercial_record_revision v JOIN commercial_record r ON r.id = v.record_id "
    "WHERE v.tenant_id = :t "
    "AND (CAST(:known AS timestamptz) IS NULL OR v.recorded_at <= CAST(:known AS timestamptz)) "
    "ORDER BY v.record_id, v.revision_no DESC) latest "
    "WHERE (CAST(:site AS uuid) IS NULL OR latest.site_id = CAST(:site AS uuid)) "
    "AND (CAST(:kind AS text) IS NULL OR latest.kind = CAST(:kind AS text)) "
    "AND (CAST(:period AS text) IS NULL OR latest.recognition_period = CAST(:period AS text)) "
    "ORDER BY latest.site_id NULLS FIRST, latest.kind COLLATE \"C\", latest.recognition_period COLLATE \"C\", "
    "latest.source_system COLLATE \"C\", latest.source_record_id COLLATE \"C\"")
_HISTORY = text(
    "SELECT " + _REVISION_COLUMNS + " FROM commercial_record_revision v JOIN commercial_record r ON r.id = v.record_id "
    "WHERE v.tenant_id = :t AND v.record_id = :r ORDER BY v.revision_no")
_INTAKE = text(
    "SELECT id, tenant_id, source_type, source_system, provenance, produced_at, batch_sha256, state, refusal_code, "
    "refusal_path, record_count, new_count, revised_count, unchanged_count, refused_count, entered_by, entered_at "
    "FROM commercial_intake WHERE tenant_id = :t AND id = :i")
_REJECTIONS = text(
    "SELECT id, tenant_id, intake_id, record_index, source_record_id, code, path, recorded_at "
    "FROM commercial_rejection WHERE tenant_id = :t AND intake_id = :i ORDER BY record_index")
_WRITTEN = text("SELECT id FROM commercial_record_revision WHERE tenant_id = :t AND intake_id = :i "
                "ORDER BY CAST(id AS text)")


def _values(row) -> dict:
    return dict(vars(row))


def _revision(row) -> RevisionRow:
    return RevisionRow(**dict(row._mapping))


class PostgresCommercialStore:
    def __init__(self, url: str) -> None:
        self._engine = create_engine(url, pool_pre_ping=True, hide_parameters=True)

    def dispose(self) -> None:
        self._engine.dispose()

    # --- reads --------------------------------------------------------------------------------------------------

    def tenant_slug(self, tenant_id: UUID) -> str | None:
        with self._engine.connect() as c:
            return c.execute(_TENANT, {"t": tenant_id}).scalar()

    def site_ids(self, tenant_id: UUID, codes: set[str]) -> dict[str, UUID]:
        if not codes:
            return {}
        with self._engine.connect() as c:
            found = dict(c.execute(_SITES, {"t": tenant_id, "keys": sorted({code.lower() for code in codes})}).all())
        return {code: found[code.lower()] for code in codes if code.lower() in found}

    @staticmethod
    def _existing(c: Connection, tenant_id: UUID, source_system: str | None,
                  ids: set[str]) -> dict[str, ExistingRecord]:
        if not ids or source_system is None:
            return {}
        rows = c.execute(_EXISTING, {"t": tenant_id, "s": source_system, "ids": sorted(ids)}).all()
        grouped: dict[str, list] = {}
        for row in rows:
            grouped.setdefault(row.source_record_id, []).append(row)
        out: dict[str, ExistingRecord] = {}
        for key, revs in grouped.items():
            last = revs[-1]
            out[key] = ExistingRecord(
                record_id=last.record_id, kind=last.kind, site_id=last.site_id,
                versions={r.source_version: r.record_sha256 for r in revs},
                latest_revision_id=last.revision_id, latest_revision_no=last.revision_no,
                provenances={r.source_version: r.provenance for r in revs})
        return out

    def existing(self, tenant_id: UUID, source_system: str, ids: set[str]) -> dict[str, ExistingRecord]:
        with self._engine.connect() as c:
            return self._existing(c, tenant_id, source_system, ids)

    def latest_revisions(self, tenant_id: UUID, *, site_id: UUID | None = None, kind: str | None = None,
                         recognition_period: str | None = None,
                         known_at: datetime | None = None) -> tuple[RevisionRow, ...]:
        with self._engine.connect() as c:
            rows = c.execute(_LATEST, {"t": tenant_id, "site": site_id, "kind": kind, "period": recognition_period,
                                       "known": known_at})
            return tuple(_revision(r) for r in rows)

    def record_history(self, tenant_id: UUID, record_id: UUID) -> tuple[RevisionRow, ...]:
        with self._engine.connect() as c:
            return tuple(_revision(r) for r in c.execute(_HISTORY, {"t": tenant_id, "r": record_id}))

    def intake(self, tenant_id: UUID, intake_id: UUID) -> IntakeSummary | None:
        with self._engine.connect() as c:
            found = c.execute(_INTAKE, {"t": tenant_id, "i": intake_id}).first()
            if found is None:
                return None
            rejections = tuple(RejectionRow(**dict(r._mapping))
                               for r in c.execute(_REJECTIONS, {"t": tenant_id, "i": intake_id}))
            written = tuple(c.execute(_WRITTEN, {"t": tenant_id, "i": intake_id}).scalars())
        return IntakeSummary(IntakeRow(**dict(found._mapping)), rejections, written)

    # --- 3A4 reads (spec §2) --------------------------------------------------------------------------------------

    def intake_revisions(self, tenant_id: UUID,
                         intake_id: UUID) -> tuple[tuple[RevisionRow, RevisionRow | None], ...]:
        with self._engine.connect() as c:
            written = [_revision(r) for r in c.execute(_INTAKE_REVISIONS, {"t": tenant_id, "i": intake_id})]
            ids = sorted({r.supersedes_revision_id for r in written if r.supersedes_revision_id is not None}, key=str)
            superseded = ({} if not ids else
                          {row.id: row for row in (_revision(r) for r in
                                                   c.execute(_REVISIONS_BY_ID, {"t": tenant_id, "ids": ids}))})
        return tuple((r, superseded[r.supersedes_revision_id] if r.supersedes_revision_id is not None else None)
                     for r in written)

    def site_zones(self, tenant_id: UUID) -> Mapping[UUID, str]:
        with self._engine.connect() as c:
            return dict(c.execute(_SITE_ZONES, {"t": tenant_id}).all())

    # --- the one write ------------------------------------------------------------------------------------------

    def write_intake(self, tenant_id: UUID, source_system: str | None, ids: set[str],
                     decide: Callable[[Mapping[str, ExistingRecord]], Plan], *, dry_run: bool) -> Plan:
        refused: str | None = None
        failed = False
        with self._engine.connect() as connection:
            c = connection.execution_options(isolation_level="READ COMMITTED")
            tx = c.begin()
            try:
                c.execute(_LOCK, {"tenant_id": str(tenant_id)})
                plan = decide(self._existing(c, tenant_id, source_system, ids))
                if dry_run:
                    tx.rollback()
                    return plan
                c.execute(_INSERT_INTAKE, _values(plan.intake))
                for record in plan.records:
                    c.execute(_INSERT_RECORD, _values(record))
                for revision in plan.revisions:
                    values = _values(revision)
                    del values["source_system"], values["source_record_id"]
                    c.execute(_INSERT_REVISION, values)
                for rejection in plan.rejections:
                    c.execute(_INSERT_REJECTION, _values(rejection))
                tx.commit()
                return plan
            except IntegrityError as error:
                refused = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
                failed = True
            finally:
                if tx.is_active:
                    tx.rollback()
        if failed:  # raised outside the handler, so the driver's error is neither cause nor context
            raise StoreRefused(refused)
        raise AssertionError("unreachable")  # pragma: no cover
