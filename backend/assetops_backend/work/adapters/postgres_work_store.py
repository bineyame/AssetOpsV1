"""W4-01 commit 2: the sole runtime writer of the eleven migration-0027 work tables (rule 8, `$workWriter`).

INSERT-only: every work row is append-only (0027 triggers refuse UPDATE/DELETE), so this module never updates,
deletes, upserts, truncates or runs DDL. Each command runs in one SERIALIZABLE transaction on one connection
(`transaction`) with ONE DB-selected instant `command_now` (`SELECT clock_timestamp()`, fixed across a serialization
retry). It bounds `occurred_at`, gates cited accepted evidence (`received_at <= :command_now`) and is bound explicitly
to every `created_at`/`recorded_at` this command INSERTs (q2 ruling 4). `test_db_clock_override` is a
constructor-only, test-only virtual DB instant; no HTTP field, environment variable or composition sets it. Every
read is scoped by tenant and Site. A serialization failure re-runs the whole command (bounded); exhaustion or a lost store is
`WorkStoreUnavailable`. A unique violation from a concurrent duplicate submission or successor is a refusal, so
nothing partial commits.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError, ProgrammingError

from assetops_backend.work.model import WorkRefused, WorkStoreUnavailable

SERIALIZATION_ATTEMPTS = 3
_SUCCESSOR_CONSTRAINTS = ("work_revision_one_successor", "work_revision_number", "maintenance_plan_one_successor",
                          "operational_record_one_successor")

_CASE_COLS = ("id, kind, public_no, public_code, asset_id, occurred_at, created_at, actor_kind, actor_id, "
              "authorization_basis, attestation, create_key, create_payload_sha256")
_REVISION_COLS = ("id, case_id, revision_no, supersedes_revision_id, title, narrative, actor_kind, actor_id, "
                  "attestation, authorization_basis, occurred_at, idempotency_key, payload_sha256, reason, recorded_at")
_EVENT_COLS = ("id, case_id, kind, payload, occurred_at, recorded_at, actor_kind, actor_id, authorization_basis, "
               "attestation, idempotency_key, payload_sha256")
_RECORD_COLS = ("id, case_id, supersedes_record_id, activity, outcome_note, occurred_at, recorded_at, actor_id, "
                "actor_kind, authorization_basis, attestation, idempotency_key, payload_sha256")
_LINEAGE = {"maintenance_plan": "canonical_plan_id", "operational_record": "canonical_record_id"}


def _rows(result) -> list[dict[str, Any]]:
    return [dict(r._mapping) for r in result]


def _one(result) -> dict[str, Any] | None:
    row = result.first()
    return None if row is None else dict(row._mapping)


class _Tx:
    """One command's scoped transaction: reads and INSERTs on the caller's connection."""

    def __init__(self, c: Connection, tenant_id: UUID, site_id: UUID,
                 link_rows: Callable[[Connection, UUID, UUID, list[str]], list[Any]] | None,
                 command_now: datetime) -> None:
        self._c, self._t, self._s, self._link_rows = c, tenant_id, site_id, link_rows
        self._now = command_now

    def _p(self, **extra: Any) -> dict[str, Any]:
        return {"t": self._t, "s": self._s, "command_now": self._now, **extra}

    # ---- reads ---------------------------------------------------------------------------------------------

    def db_now(self) -> datetime:
        """The command's single DB instant (q2 ruling 4); never re-read within a command."""
        return self._now

    def next_public_no(self) -> int:
        return int(self._c.execute(text("SELECT nextval('work_public_no_seq')")).scalar_one())

    def case_by_create_key(self, key: str) -> dict[str, Any] | None:
        return _one(self._c.execute(text(f"SELECT {_CASE_COLS} FROM work_case WHERE tenant_id = :t AND site_id = :s "
                                         "AND create_key = :k"), self._p(k=key)))

    def case(self, case_id: str) -> dict[str, Any] | None:
        return _one(self._c.execute(text(f"SELECT {_CASE_COLS} FROM work_case WHERE tenant_id = :t AND site_id = :s "
                                         "AND id = :i"), self._p(i=case_id)))

    def lock_case(self, case_id: str) -> dict[str, Any] | None:
        """The case root row under a row lock: corrections and events on one case are serialized (linear chain)."""
        return _one(self._c.execute(text(f"SELECT {_CASE_COLS} FROM work_case WHERE tenant_id = :t AND site_id = :s "
                                         "AND id = :i FOR UPDATE"), self._p(i=case_id)))

    def revisions(self, case_id: str) -> list[dict[str, Any]]:
        return _rows(self._c.execute(text(f"SELECT {_REVISION_COLS} FROM work_case_revision WHERE tenant_id = :t "
                                          "AND site_id = :s AND case_id = :i ORDER BY revision_no"),
                                     self._p(i=case_id)))

    def events(self, case_id: str) -> list[dict[str, Any]]:
        return _rows(self._c.execute(text(f"SELECT {_EVENT_COLS} FROM work_event WHERE tenant_id = :t "
                                          "AND site_id = :s AND case_id = :i ORDER BY recorded_at, id"),
                                     self._p(i=case_id)))

    def revision_links(self, revision_id: str) -> dict[str, Any]:
        p = self._p(r=revision_id)
        finding = self._c.execute(text(
            "SELECT CAST(finding_id AS text) AS finding_id, CAST(finding_revision_id AS text) AS finding_revision_id "
            "FROM work_case_finding_link WHERE tenant_id = :t AND site_id = :s AND case_revision_id = :r "
            "ORDER BY finding_id, finding_revision_id"), p)
        action = self._c.execute(text(
            "SELECT CAST(action_id AS text) AS action_id, CAST(action_event_id AS text) AS action_event_id "
            "FROM work_case_action_link WHERE tenant_id = :t AND site_id = :s AND case_revision_id = :r "
            "ORDER BY action_id, action_event_id"), p)
        evidence = self._c.execute(text(
            "SELECT CAST(evidence_id AS text) FROM work_case_evidence WHERE tenant_id = :t AND site_id = :s "
            "AND case_revision_id = :r ORDER BY evidence_id"), p)
        return {"finding_links": _rows(finding), "action_links": _rows(action), "evidence_ids": list(evidence.scalars())}

    def latest_record(self, case_id: str, upto: datetime) -> dict[str, Any] | None:
        return _one(self._c.execute(text(
            f"SELECT {_RECORD_COLS} FROM maintenance_record WHERE tenant_id = :t AND site_id = :s AND case_id = :i "
            "AND recorded_at <= :u ORDER BY recorded_at DESC, id DESC LIMIT 1"), self._p(i=case_id, u=upto)))

    def lineage_evidence(self, finding_revision_ids: list[str], action_ids: list[str]) -> list[str]:
        """Q11: pinned Finding revisions' cited evidence, each pinned Action's basis evidence and its origin
        Finding revision's cited evidence, all scoped to this tenant/Site."""
        p = self._p(r=list(finding_revision_ids), a=list(action_ids))
        return list(self._c.execute(text(
            "SELECT CAST(evidence_id AS text) FROM finding_revision_evidence WHERE tenant_id = :t AND site_id = :s "
            "AND finding_revision_id = ANY(CAST(:r AS uuid[])) "
            "UNION SELECT CAST(evidence_id AS text) FROM action_basis_evidence WHERE tenant_id = :t "
            "AND site_id = :s AND action_id = ANY(CAST(:a AS uuid[])) "
            "UNION SELECT CAST(e.evidence_id AS text) FROM action a JOIN finding_revision_evidence e "
            "ON e.tenant_id = a.tenant_id AND e.site_id = a.site_id AND e.finding_revision_id = a.origin_finding_revision_id "
            "WHERE a.tenant_id = :t AND a.site_id = :s AND a.id = ANY(CAST(:a AS uuid[]))"), p).scalars())

    def link_rows(self, evidence_ids: list[str]) -> list[Any]:
        if self._link_rows is None:
            raise WorkStoreUnavailable("The work store has no provenance link-row reader.")
        return list(self._link_rows(self._c, self._t, self._s, evidence_ids))

    def asset_in_scope(self, asset_id: str) -> bool:
        return self._c.execute(text("SELECT 1 FROM asset WHERE tenant_id = :t AND site_id = :s AND id = :a"),
                               self._p(a=asset_id)).first() is not None

    def incident_in_scope(self, incident_id: str) -> bool:
        return self._c.execute(text("SELECT 1 FROM incident WHERE tenant_id = :t AND site_id = :s AND id = :i"),
                               self._p(i=incident_id)).first() is not None

    def finding_pairs_in_scope(self, pairs: list[tuple[str, str]]) -> set[tuple[str, str]]:
        rows = self._c.execute(text(
            "SELECT CAST(finding_id AS text), CAST(id AS text) FROM finding_revision WHERE tenant_id = :t "
            "AND site_id = :s AND id = ANY(CAST(:r AS uuid[]))"), self._p(r=[r for _, r in pairs]))
        return {(f, r) for f, r in rows} & set(pairs)

    def action_pairs_in_scope(self, pairs: list[tuple[str, str]]) -> set[tuple[str, str]]:
        """Exact (Action, event) pairs whose event belongs to that Action, both in this tenant/Site."""
        rows = self._c.execute(text(
            "SELECT CAST(e.action_id AS text), CAST(e.id AS text) FROM action_event e JOIN action a "
            "ON a.tenant_id = e.tenant_id AND a.site_id = e.site_id AND a.id = e.action_id "
            "WHERE e.tenant_id = :t AND e.site_id = :s AND e.id = ANY(CAST(:e AS uuid[]))"),
            self._p(e=[e for _, e in pairs]))
        return {(a, e) for a, e in rows} & set(pairs)

    def accepted_evidence_by_command_now(self, evidence_ids: list[str]) -> set[str]:
        """Q2 ruling 4: the scoped cited rows with `received_at <= :command_now`."""
        rows = self._c.execute(text(
            "SELECT id FROM accepted_evidence WHERE tenant_id = :t AND site_id = :s "
            "AND id = ANY(CAST(:e AS uuid[])) AND received_at <= :command_now"), self._p(e=list(evidence_ids)))
        return {str(v) for v in rows.scalars().all()}

    def record_in_case(self, case_id: str, record_id: str) -> bool:
        return self._c.execute(text("SELECT 1 FROM maintenance_record WHERE tenant_id = :t AND site_id = :s "
                                    "AND case_id = :c AND id = :r"), self._p(c=case_id, r=record_id)).first() is not None

    def record_by_key(self, case_id: str, key: str) -> dict[str, Any] | None:
        return _one(self._c.execute(text(f"SELECT {_RECORD_COLS} FROM maintenance_record WHERE tenant_id = :t "
                                         "AND site_id = :s AND case_id = :c AND idempotency_key = :k"),
                                    self._p(c=case_id, k=key)))

    def lineage_by_key(self, table: str, key: str) -> dict[str, Any] | None:
        assert table in _LINEAGE
        return _one(self._c.execute(text(f"SELECT * FROM {table} WHERE tenant_id = :t AND site_id = :s "
                                         "AND idempotency_key = :k"), self._p(k=key)))

    def lineage_row(self, table: str, row_id: str) -> dict[str, Any] | None:
        assert table in _LINEAGE
        return _one(self._c.execute(text(f"SELECT * FROM {table} WHERE tenant_id = :t AND site_id = :s AND id = :i"),
                                    self._p(i=row_id)))

    def lock_root(self, table: str, root_id: str) -> dict[str, Any] | None:
        """The canonical root under a row lock, or None if the ID is not a root of this tenant/Site."""
        assert table in _LINEAGE
        return _one(self._c.execute(text(f"SELECT * FROM {table} WHERE tenant_id = :t AND site_id = :s AND id = :i "
                                         f"AND {_LINEAGE[table]} = id FOR UPDATE"), self._p(i=root_id)))

    def lineage_head(self, table: str, root_id: str) -> dict[str, Any]:
        assert table in _LINEAGE
        return _one(self._c.execute(text(f"SELECT * FROM {table} WHERE tenant_id = :t AND site_id = :s "
                                         f"AND {_LINEAGE[table]} = :i ORDER BY recorded_at DESC, id DESC LIMIT 1"),
                                    self._p(i=root_id)))

    # ---- INSERTs (one statement per table) -----------------------------------------------------------------

    def insert_case(self, r: dict[str, Any]) -> None:
        self._c.execute(text(
            "INSERT INTO work_case (id, tenant_id, site_id, kind, public_no, public_code, asset_id, occurred_at, "
            "actor_kind, actor_id, authorization_basis, attestation, create_key, create_payload_sha256, created_at) "
            "VALUES (:id, :t, :s, :kind, :public_no, :public_code, :asset_id, :occurred_at, :actor_kind, :actor_id, "
            ":authorization_basis, :attestation, :create_key, :create_payload_sha256, :command_now)"), self._p(**r))

    def insert_incident(self, case_id: str, key: str) -> None:
        self._c.execute(text("INSERT INTO incident (tenant_id, site_id, id, incident_key) VALUES (:t, :s, :i, :k)"),
                        self._p(i=case_id, k=key))

    def insert_request(self, case_id: str, key: str, incident_id: str | None) -> None:
        self._c.execute(text(
            "INSERT INTO maintenance_work_request (tenant_id, site_id, id, request_key, incident_id) "
            "VALUES (:t, :s, :i, :k, :n)"), self._p(i=case_id, k=key, n=incident_id))

    def insert_revision(self, r: dict[str, Any]) -> None:
        self._c.execute(text(
            "INSERT INTO work_case_revision (id, tenant_id, site_id, case_id, revision_no, supersedes_revision_id, "
            "title, narrative, actor_kind, actor_id, attestation, authorization_basis, occurred_at, idempotency_key, "
            "payload_sha256, reason, recorded_at) VALUES (:id, :t, :s, :case_id, :revision_no, "
            ":supersedes_revision_id, :title, :narrative, :actor_kind, :actor_id, :attestation, :authorization_basis, "
            ":occurred_at, :idempotency_key, :payload_sha256, :reason, :command_now)"), self._p(**r))

    def insert_finding_link(self, revision_id: str, finding_id: str, finding_revision_id: str) -> None:
        self._c.execute(text(
            "INSERT INTO work_case_finding_link (tenant_id, site_id, case_revision_id, finding_id, finding_revision_id) "
            "VALUES (:t, :s, :r, :f, :fr)"), self._p(r=revision_id, f=finding_id, fr=finding_revision_id))

    def insert_action_link(self, revision_id: str, action_id: str, action_event_id: str) -> None:
        self._c.execute(text(
            "INSERT INTO work_case_action_link (tenant_id, site_id, case_revision_id, action_id, action_event_id) "
            "VALUES (:t, :s, :r, :a, :e)"), self._p(r=revision_id, a=action_id, e=action_event_id))

    def insert_case_evidence(self, revision_id: str, evidence_id: str) -> None:
        self._c.execute(text(
            "INSERT INTO work_case_evidence (tenant_id, site_id, case_revision_id, evidence_id) "
            "VALUES (:t, :s, :r, :e)"), self._p(r=revision_id, e=evidence_id))

    def insert_event(self, r: dict[str, Any]) -> None:
        self._c.execute(text(
            "INSERT INTO work_event (id, tenant_id, site_id, case_id, kind, payload, occurred_at, actor_kind, "
            "actor_id, authorization_basis, attestation, idempotency_key, payload_sha256, recorded_at) VALUES (:id, "
            ":t, :s, :case_id, :kind, CAST(:payload AS jsonb), :occurred_at, :actor_kind, :actor_id, "
            ":authorization_basis, :attestation, :idempotency_key, :payload_sha256, :command_now)"), self._p(**{**r, "payload": json.dumps(r["payload"])}))

    def insert_record(self, r: dict[str, Any]) -> None:
        self._c.execute(text(
            "INSERT INTO maintenance_record (id, tenant_id, site_id, case_id, activity, outcome_note, occurred_at, "
            "actor_id, actor_kind, authorization_basis, attestation, idempotency_key, payload_sha256, recorded_at) "
            "VALUES (:id, :t, :s, :case_id, :activity, :outcome_note, :occurred_at, :actor_id, :actor_kind, "
            ":authorization_basis, :attestation, :idempotency_key, :payload_sha256, :command_now)"), self._p(**r))

    def insert_plan(self, r: dict[str, Any]) -> None:
        self._c.execute(text(
            "INSERT INTO maintenance_plan (id, tenant_id, site_id, asset_id, public_no, public_code, "
            "canonical_plan_id, title, trigger_kind, next_due_at, next_due_hours, state, supersedes_plan_id, "
            "actor_id, actor_kind, authorization_basis, occurred_at, correction_reason, attestation, idempotency_key, "
            "payload_sha256, recorded_at) VALUES (:id, :t, :s, :asset_id, :public_no, :public_code, "
            ":canonical_plan_id, :title, :trigger_kind, :next_due_at, :next_due_hours, :state, :supersedes_plan_id, "
            ":actor_id, :actor_kind, :authorization_basis, :occurred_at, :correction_reason, :attestation, "
            ":idempotency_key, :payload_sha256, :command_now)"), self._p(**r))

    def insert_operational_record(self, r: dict[str, Any]) -> None:
        self._c.execute(text(
            "INSERT INTO operational_record (id, tenant_id, site_id, public_no, public_code, canonical_record_id, "
            "kind, body, period_end, unit, quantity, source_document_sha256, correction_reason, state, "
            "supersedes_record_id, case_id, occurred_at, actor_id, actor_kind, authorization_basis, attestation, "
            "idempotency_key, payload_sha256, recorded_at) VALUES (:id, :t, :s, :public_no, :public_code, "
            ":canonical_record_id, :kind, :body, :period_end, :unit, :quantity, :source_document_sha256, "
            ":correction_reason, :state, :supersedes_record_id, :case_id, :occurred_at, :actor_id, :actor_kind, "
            ":authorization_basis, :attestation, :idempotency_key, :payload_sha256, :command_now)"), self._p(**r))


class PostgresWorkStore:
    def __init__(self, database_url: str | None, *,
                 link_rows: Callable[[Connection, UUID, UUID, list[str]], list[Any]] | None = None,
                 statement_timeout_ms: int = 30_000, lock_timeout_ms: int = 5_000,
                 test_db_clock_override: Callable[[], datetime] | None = None) -> None:
        self._database_url = database_url
        self._link_rows = link_rows
        # Test-only virtual DB instant (q2 ruling 4); production composition never passes it.
        self.test_db_clock_override = test_db_clock_override
        self._options = f"-c statement_timeout={int(statement_timeout_ms)} -c lock_timeout={int(lock_timeout_ms)}"
        self._engine: Engine | None = None

    def _connect(self) -> Engine:
        if not self._database_url:
            raise WorkStoreUnavailable("DATABASE_URL is not set, so the work store cannot be reached.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True,
                                         connect_args={"options": self._options})
        return self._engine

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def transaction(self, tenant_id: UUID, site_id: UUID, work: Callable[[_Tx], Any]) -> Any:
        command_now: datetime | None = None  # one instant per command, kept across a serialization retry
        for attempt in range(SERIALIZATION_ATTEMPTS):
            try:
                with self._connect().begin() as c:
                    c.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
                    if command_now is None:
                        command_now = (self.test_db_clock_override() if self.test_db_clock_override is not None
                                       else c.execute(text("SELECT clock_timestamp()")).scalar_one().astimezone(timezone.utc))
                        assert command_now.tzinfo is not None and command_now.utcoffset() == timedelta(0)
                    return work(_Tx(c, tenant_id, site_id, self._link_rows, command_now))
            except IntegrityError as error:
                if getattr(error.orig, "sqlstate", None) == "40001":
                    continue
                constraint = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
                if constraint in _SUCCESSOR_CONSTRAINTS:
                    raise WorkRefused("WORK_CORRECTION_CONFLICT") from error
                if constraint is not None and (constraint.endswith("_once") or constraint.endswith("_key_once")):
                    raise WorkRefused("WORK_EVENT_DUPLICATE_KEY") from error
                raise
            except (OperationalError, ProgrammingError) as error:
                if getattr(error.orig, "sqlstate", None) == "40001" and attempt + 1 < SERIALIZATION_ATTEMPTS:
                    continue
                raise WorkStoreUnavailable(f"The work store failed: {error.orig}") from error
            except DBAPIError as error:
                if getattr(error.orig, "sqlstate", None) == "40001" and attempt + 1 < SERIALIZATION_ATTEMPTS:
                    continue
                if error.connection_invalidated:
                    raise WorkStoreUnavailable(str(error.orig)) from error
                raise
        raise WorkStoreUnavailable("The work store could not serialize this command.")
