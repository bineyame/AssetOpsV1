"""PostgreSQL declared-objective store (OUT-D U3, migration 0038).

The sole writer of `outcome_objective_revision` (architecture guard rule 8): one INSERT, never an UPDATE, DELETE,
upsert or DDL (the 0038 trigger refuses UPDATE and DELETE). A declaration runs in one transaction: it takes the
(tenant, site, outcome) advisory lock and locks the current head row (`FOR UPDATE`), answers an exact retry of its
idempotency key with the stored row (a different payload under the same key is refused), checks the expected prior
against the head, then inserts revision head+1 superseding the head at `clock_timestamp()`.

`current(..., known_at)` reads the latest revision per outcome recorded at or before `known_at` (now when None),
which is what keeps an earlier reading reproducible after a later declaration.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import OperationalError, ProgrammingError

from assetops_backend.financials.assumptions import SystemPrincipal
from assetops_backend.objectives.model import (
    CHANNELS, Declaration, ObjectiveRefused, measure_of, payload_sha256, validate)


class ObjectiveStoreUnavailable(RuntimeError):
    pass


COLUMNS = ("id, tenant_id, site_id, outcome_key, revision_no, supersedes_revision_id, measure_key, measure_kind, "
           "comparison, target, unit, currency, window_rule, source, source_note, actor_kind, actor_id, "
           "authorization_basis, source_channel, idempotency_key, payload_sha256, recorded_at")


def _row(r) -> dict[str, Any]:
    return dict(r._mapping)


class PostgresObjectiveStore:
    def __init__(self, database_url: str | None) -> None:
        self._database_url = database_url
        self._engine: Engine | None = None

    def _connect(self) -> Engine:
        if not self._database_url:
            raise ObjectiveStoreUnavailable("DATABASE_URL is not set, so the objective store cannot be reached.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True)
        return self._engine

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def _run(self, work):
        try:
            with self._connect().connect() as c:
                with c.begin():
                    return work(c)
        except (OperationalError, ProgrammingError) as error:
            raise ObjectiveStoreUnavailable(f"The objective store failed: {error.orig}") from error

    # ---- scope -------------------------------------------------------------------------------------------

    def tenant_id(self, tenant_slug: str) -> UUID | None:
        return self._run(lambda c: c.execute(text("SELECT id FROM tenant WHERE slug = :slug"),
                                             {"slug": tenant_slug}).scalar())

    def site_id(self, tenant_id: UUID, site_code: str) -> UUID | None:
        return self._run(lambda c: c.execute(text(
            "SELECT id FROM site WHERE tenant_id = :t AND site_code_key = lower(:code)"),
            {"t": tenant_id, "code": site_code}).scalar())

    # ---- declaration -------------------------------------------------------------------------------------

    def declare(self, tenant_id: UUID, decl: Declaration, principal: SystemPrincipal,
                channel: str) -> tuple[dict[str, Any], bool]:
        """(stored row, inserted). Refusals: 404 SITE_NOT_FOUND, 409 IDEMPOTENCY_KEY_REUSED /
        OBJECTIVE_PRIOR_MISMATCH, 422 OBJECTIVE_INVALID, 403 SYSTEM_PRINCIPAL_REQUIRED."""
        validate(decl)
        measure = measure_of(decl)
        if principal.actor_kind != "SYSTEM":
            raise ObjectiveRefused(403, "SYSTEM_PRINCIPAL_REQUIRED", "Only the server-side SYSTEM declarer declares.")
        if channel not in CHANNELS:
            raise ObjectiveRefused(422, "OBJECTIVE_INVALID", f"Channel {channel!r} is not a SYSTEM channel.")
        digest = payload_sha256(decl)

        def work(c: Connection) -> tuple[dict[str, Any], bool]:
            site = c.execute(text("SELECT id FROM site WHERE tenant_id = :t AND site_code_key = lower(:code)"),
                             {"t": tenant_id, "code": decl.site_code}).scalar()
            if site is None:
                raise ObjectiveRefused(404, "SITE_NOT_FOUND", f"No imported Site {decl.site_code!r}.")
            scope = {"t": tenant_id, "s": site, "o": decl.outcome_key}
            c.execute(text("SELECT pg_advisory_xact_lock(hashtextextended("
                           "'outcome_objective:' || :t || ':' || :s || ':' || :o, 0))"),
                      {"t": str(tenant_id), "s": str(site), "o": decl.outcome_key})
            same = c.execute(text(f"SELECT {COLUMNS} FROM outcome_objective_revision "
                                  "WHERE tenant_id = :t AND site_id = :s AND idempotency_key = :k"),
                             {"t": tenant_id, "s": site, "k": decl.idempotency_key}).first()
            if same is not None:
                if same.payload_sha256 != digest:
                    raise ObjectiveRefused(409, "IDEMPOTENCY_KEY_REUSED",
                                           f"Idempotency key {decl.idempotency_key!r} already declared revision "
                                           f"{same.id} with a different payload; nothing was written.")
                return _row(same), False
            head = c.execute(text(
                "SELECT id, revision_no FROM outcome_objective_revision WHERE tenant_id = :t AND site_id = :s "
                "AND outcome_key = :o ORDER BY revision_no DESC LIMIT 1 FOR UPDATE"), scope).first()
            head_id = None if head is None else head.id
            if decl.expected_prior != head_id:
                raise ObjectiveRefused(409, "OBJECTIVE_PRIOR_MISMATCH",
                                       f"The expected prior revision {decl.expected_prior} is not the current "
                                       f"revision {head_id} of {decl.outcome_key}; nothing was written.")
            stored = c.execute(text(
                f"INSERT INTO outcome_objective_revision ({COLUMNS}) VALUES (:id, :t, :s, :o, :no, :sup, :m, :kind, "
                ":cmp, :target, :unit, :cur, :win, :src, :note, :actor_kind, :actor_id, :basis, :channel, :k, :sha, "
                f"clock_timestamp()) RETURNING {COLUMNS}"),
                {**scope, "id": uuid4(), "no": 1 if head is None else head.revision_no + 1, "sup": head_id,
                 "m": measure.key, "kind": measure.kind, "cmp": measure.comparison, "target": decl.target,
                 "unit": measure.unit, "cur": decl.currency, "win": measure.window_rule, "src": decl.source,
                 "note": decl.source_note, "actor_kind": principal.actor_kind, "actor_id": principal.actor_id,
                 "basis": principal.authorization_basis, "channel": channel, "k": decl.idempotency_key,
                 "sha": digest}).one()
            return _row(stored), True

        return self._run(work)

    def revision_id(self, tenant_id: UUID, site_id: UUID, idempotency_key: str) -> UUID | None:
        return self._run(lambda c: c.execute(text(
            "SELECT id FROM outcome_objective_revision WHERE tenant_id = :t AND site_id = :s "
            "AND idempotency_key = :k"), {"t": tenant_id, "s": site_id, "k": idempotency_key}).scalar())

    # ---- read --------------------------------------------------------------------------------------------

    def current(self, tenant_id: UUID, site_id: UUID, known_at: datetime | None) -> list[dict[str, Any]]:
        """The latest revision per outcome recorded at or before `known_at` (now when None)."""
        return self._run(lambda c: [_row(r) for r in c.execute(text(
            f"SELECT DISTINCT ON (outcome_key) {COLUMNS} FROM outcome_objective_revision "
            "WHERE tenant_id = :t AND site_id = :s AND recorded_at <= coalesce(CAST(:k AS timestamptz), now()) "
            "ORDER BY outcome_key, revision_no DESC"), {"t": tenant_id, "s": site_id, "k": known_at})])
