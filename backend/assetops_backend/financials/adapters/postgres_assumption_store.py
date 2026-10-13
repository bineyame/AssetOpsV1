"""PostgreSQL financial assumption store (S4-02a phase 1, migration 0010).

The sixth product database writer (architecture guard rule 8). It inserts only
`financial_assumption_revision` and `financial_assumption_assignment`, and its one
UPDATE sets an assignment's set-once `recorded_to` (the trigger refuses anything
else). A publication runs in one transaction: it takes the Site/key series
advisory lock, answers an exact retry with the stored revision ID (a conflicting
retry is refused), checks the expected prior revision, then takes ONE server
instant with `clock_timestamp()` after the lock (not transaction-start `now()`),
which must be later than the series' latest recorded instant. That instant is the
new revision's `recorded_at`, every superseded assignment's `recorded_to` and
every new assignment's `recorded_from`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import OperationalError, ProgrammingError

from assetops_backend.financials.assumptions import (
    UNIT,
    Current,
    Publication,
    PublicationRefused,
    SystemPrincipal,
    plan_assignments,
    request_sha256,
    validate,
)


class AssumptionStoreUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class Published:
    revision_id: UUID
    revision_no: int
    recorded_at: datetime
    change_kind: str
    replayed: bool


REVISION_COLUMNS = ("id, tenant_id, site_id, assumption_key, revision_no, prior_revision_id, currency, unit, value, "
                    "basis, source_reference, valid_from, valid_to, recorded_at, change_kind, correction_reason, "
                    "actor_kind, actor_id, author_id, channel, authorization_basis, provenance, idempotency_key, "
                    "request_sha256")
ASSIGNMENT_COLUMNS = ("id, tenant_id, site_id, assumption_key, revision_id, publication_revision_id, valid_from, "
                      "valid_to, recorded_from, recorded_to")


class PostgresAssumptionStore:
    def __init__(self, database_url: str | None) -> None:
        self._database_url = database_url
        self._engine: Engine | None = None

    def _connect(self) -> Engine:
        if not self._database_url:
            raise AssumptionStoreUnavailable("DATABASE_URL is not set, so the assumption store cannot be reached.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True)
        return self._engine

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def _run(self, work, isolation: str = "READ COMMITTED"):
        try:
            with self._connect().connect().execution_options(isolation_level=isolation) as c:
                with c.begin():
                    return work(c)
        except (OperationalError, ProgrammingError) as error:
            raise AssumptionStoreUnavailable(f"The assumption store failed: {error.orig}") from error

    # ---- scope -------------------------------------------------------------------------------------------

    def site_scope(self, tenant_slug: str, site_code: str) -> tuple[str, UUID, UUID] | None:
        """(site_code, tenant_id, site_id) of an imported Site inside the named tenant, else None."""
        def work(c: Connection):
            row = c.execute(text(
                "SELECT s.site_code, s.tenant_id, s.id FROM site s JOIN tenant t ON t.id = s.tenant_id "
                "WHERE t.slug = :slug AND s.site_code_key = lower(:code)"), {"slug": tenant_slug, "code": site_code}
            ).first()
            return None if row is None else (row[0], row[1], row[2])
        return self._run(work)

    # ---- publication -------------------------------------------------------------------------------------

    def publish(self, tenant_id: UUID, site_id: UUID, p: Publication, principal: SystemPrincipal) -> Published:
        validate(p)
        if principal.actor_kind != "SYSTEM":
            raise PublicationRefused(403, "SYSTEM_PRINCIPAL_REQUIRED",
                                     "Only the server-side SYSTEM publisher can publish in this slice.")
        digest = request_sha256(p, principal, tenant_id, site_id)
        series = {"t": tenant_id, "s": site_id, "k": p.assumption_key}

        def work(c: Connection) -> Published:
            c.execute(text("SELECT pg_advisory_xact_lock(hashtextextended("
                           "'financial_assumption:' || :t || ':' || :s || ':' || :k, 0))"),
                      {"t": str(tenant_id), "s": str(site_id), "k": p.assumption_key})
            same = c.execute(text(
                "SELECT id, revision_no, recorded_at, change_kind, request_sha256 FROM financial_assumption_revision "
                "WHERE tenant_id = :t AND site_id = :s AND assumption_key = :k AND idempotency_key = :i"),
                {**series, "i": p.idempotency_key}).first()
            if same is not None:
                if same[4] != digest:
                    raise PublicationRefused(409, "IDEMPOTENCY_KEY_REUSED",
                                             f"Idempotency key {p.idempotency_key!r} already published revision "
                                             f"{same[0]} with a different request; nothing was written.")
                return Published(same[0], same[1], same[2], same[3], True)
            head = c.execute(text(
                "SELECT id, revision_no FROM financial_assumption_revision "
                "WHERE tenant_id = :t AND site_id = :s AND assumption_key = :k ORDER BY revision_no DESC LIMIT 1"),
                series).first()
            head_id = None if head is None else head[0]
            if head_id != p.expected_prior_revision_id:
                raise PublicationRefused(409, "PRIOR_REVISION_MISMATCH",
                                         f"Expected prior revision {p.expected_prior_revision_id}, but the series "
                                         f"head is {head_id}; re-read and publish against the current head.")
            # One server instant, taken after the lock.
            at = c.execute(text("SELECT clock_timestamp()")).scalar_one()
            latest = c.execute(text(
                "SELECT max(recorded_from) FROM financial_assumption_assignment "
                "WHERE tenant_id = :t AND site_id = :s AND assumption_key = :k"), series).scalar_one()
            if latest is not None and not at > latest:
                raise PublicationRefused(409, "RECORDED_TIME_NOT_LATER",
                                         "The server clock is not later than the series' latest recorded instant.")
            current = [Current(r[0], r[1], r[2], r[3]) for r in c.execute(text(
                "SELECT id, revision_id, valid_from, valid_to FROM financial_assumption_assignment "
                "WHERE tenant_id = :t AND site_id = :s AND assumption_key = :k AND recorded_to IS NULL "
                "ORDER BY valid_from"), series)]
            plan = plan_assignments(p.change_kind, p.valid_from, p.valid_to, at, current)
            revision_id = uuid4()
            revision_no = 1 if head is None else head[1] + 1
            c.execute(text(
                "INSERT INTO financial_assumption_revision (id, tenant_id, site_id, assumption_key, revision_no, "
                "prior_revision_id, currency, unit, value, basis, source_reference, valid_from, valid_to, "
                "recorded_at, change_kind, correction_reason, actor_kind, actor_id, author_id, channel, "
                "authorization_basis, provenance, idempotency_key, request_sha256) VALUES (:id, :t, :s, :k, :no, "
                ":prior, :currency, :unit, :value, :basis, :source, :vf, :vt, :at, :kind, :reason, :actor_kind, "
                ":actor_id, NULL, :channel, :auth, CAST(:provenance AS jsonb), :idem, :digest)"),
                {**series, "id": revision_id, "no": revision_no, "prior": head_id, "currency": p.currency,
                 "unit": UNIT, "value": p.value, "basis": p.basis, "source": p.source_reference,
                 "vf": p.valid_from, "vt": p.valid_to, "at": at, "kind": p.change_kind,
                 "reason": p.correction_reason, "actor_kind": principal.actor_kind, "actor_id": principal.actor_id,
                 "channel": p.channel, "auth": principal.authorization_basis,
                 "provenance": json.dumps(p.provenance, sort_keys=True), "idem": p.idempotency_key,
                 "digest": digest})
            for closing in plan.close:
                closed = c.execute(text(
                    "UPDATE financial_assumption_assignment SET recorded_to = :at WHERE id = :id "
                    "AND recorded_to IS NULL"), {"at": at, "id": closing}).rowcount
                if closed != 1:
                    raise PublicationRefused(409, "SERIES_MOVED", "A current assignment changed under the lock.")
            for new in plan.insert:
                c.execute(text(
                    "INSERT INTO financial_assumption_assignment (id, tenant_id, site_id, assumption_key, "
                    "revision_id, publication_revision_id, valid_from, valid_to, recorded_from, recorded_to) "
                    "VALUES (:id, :t, :s, :k, :rev, :pub, :vf, :vt, :at, NULL)"),
                    {**series, "id": uuid4(), "rev": new.revision_id or revision_id, "pub": revision_id,
                     "vf": new.valid_from, "vt": new.valid_to, "at": at})
            return Published(revision_id, revision_no, at, p.change_kind, False)

        return self._run(work)

    # ---- raw rows (phase 2 builds the read service over these) -----------------------------------------------

    def revisions(self, tenant_id: UUID, site_id: UUID, key: str) -> list[dict[str, Any]]:
        def work(c: Connection):
            return [dict(r._mapping) for r in c.execute(text(
                f"SELECT {REVISION_COLUMNS} FROM financial_assumption_revision WHERE tenant_id = :t AND "
                "site_id = :s AND assumption_key = :k ORDER BY revision_no"), {"t": tenant_id, "s": site_id, "k": key})]
        return self._run(work, "REPEATABLE READ")

    def assignments(self, tenant_id: UUID, site_id: UUID, key: str) -> list[dict[str, Any]]:
        def work(c: Connection):
            return [dict(r._mapping) for r in c.execute(text(
                f"SELECT {ASSIGNMENT_COLUMNS} FROM financial_assumption_assignment WHERE tenant_id = :t AND "
                "site_id = :s AND assumption_key = :k ORDER BY recorded_from, valid_from"),
                {"t": tenant_id, "s": site_id, "k": key})]
        return self._run(work, "REPEATABLE READ")

    # ---- phase 2 reads: exact, at a recorded cutoff, bounded ------------------------------------------------

    def snapshot(self, tenant_id: UUID, site_id: UUID, key: str, recorded_at: datetime | None,
                 after_revision_no: int, limit: int) -> dict[str, Any]:
        """One consistent read of the series as known at `recorded_at` (None: current).

        Assignments at a cutoff `c` satisfy `recorded_from <= c < recorded_to` (half-open, open-ended when
        `recorded_to` is NULL); current assignments have `recorded_to IS NULL`. Revisions are those recorded
        at or before the cutoff, paged by revision number."""
        series = {"t": tenant_id, "s": site_id, "k": key, "c": recorded_at}
        known = "" if recorded_at is None else " AND recorded_at <= :c"
        at = ("recorded_to IS NULL" if recorded_at is None
              else "recorded_from <= :c AND (recorded_to IS NULL OR :c < recorded_to)")

        def work(c: Connection) -> dict[str, Any]:
            where = "tenant_id = :t AND site_id = :s AND assumption_key = :k"
            total = c.execute(text(f"SELECT count(*) FROM financial_assumption_revision WHERE {where}{known}"),
                              series).scalar_one()
            page = [dict(r._mapping) for r in c.execute(text(
                f"SELECT {REVISION_COLUMNS} FROM financial_assumption_revision WHERE {where}{known} "
                "AND revision_no > :after ORDER BY revision_no LIMIT :limit"),
                {**series, "after": after_revision_no, "limit": limit})]
            timeline = [dict(r._mapping) for r in c.execute(text(
                f"SELECT {ASSIGNMENT_COLUMNS} FROM financial_assumption_assignment WHERE {where} AND {at} "
                "ORDER BY valid_from, id"), series)]
            ids = sorted({a["revision_id"] for a in timeline} | {a["publication_revision_id"] for a in timeline},
                         key=str)
            cited = {} if not ids else {r._mapping["id"]: dict(r._mapping) for r in c.execute(text(
                f"SELECT {REVISION_COLUMNS} FROM financial_assumption_revision WHERE {where} "
                "AND id = ANY(:ids)"), {**series, "ids": ids})}
            return {"total": total, "revisions": page, "timeline": timeline, "cited": cited}

        return self._run(work, "REPEATABLE READ")

    def revision_detail(self, tenant_id: UUID, site_id: UUID, revision_id: UUID) -> dict[str, Any] | None:
        """The exact revision of this Site with every assignment row that ever named it; None if unknown here."""
        def work(c: Connection) -> dict[str, Any] | None:
            row = c.execute(text(
                f"SELECT {REVISION_COLUMNS} FROM financial_assumption_revision "
                "WHERE tenant_id = :t AND site_id = :s AND id = :id"),
                {"t": tenant_id, "s": site_id, "id": revision_id}).first()
            if row is None:
                return None
            assignments = [dict(r._mapping) for r in c.execute(text(
                f"SELECT {ASSIGNMENT_COLUMNS} FROM financial_assumption_assignment WHERE tenant_id = :t AND "
                "site_id = :s AND (revision_id = :id OR publication_revision_id = :id) "
                "ORDER BY recorded_from, valid_from, id"), {"t": tenant_id, "s": site_id, "id": revision_id})]
            return {"revision": dict(row._mapping), "assignments": assignments}

        return self._run(work, "REPEATABLE READ")
