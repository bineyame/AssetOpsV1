"""W5-02a K1a: the sole runtime writer of `domain_action`, `domain_action_intent` and `domain_action_case_link`.

INSERT-only (0033 triggers refuse UPDATE/DELETE on all three): this module never updates, deletes, upserts,
truncates or runs DDL. Each command runs in one SERIALIZABLE transaction with ONE DB instant `command_now`
(`SELECT clock_timestamp()`, kept across a serialization retry) that bounds every selection read and is bound
explicitly to the inserted `recorded_at`. Idempotency is a transaction-scoped advisory lock keyed by
`(tenant, site, command, idempotency_key)`, then select-prior, compare hash, insert (ruling A2; no ON CONFLICT).

The cross-table Action code trigger's named failure (`action_cross_domain_code_conflict`, ruling A4) and the two
intent-chain uniques are typed 409 `DOMAIN_INTENT_CONFLICT` at this transaction boundary; any other integrity
failure propagates. The selected cold Finding pin is an injected caller-connection read (`pin_of`), composed
in `work/composition.py` from the W4 linked-selection reader; no analytics adapter is imported here.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError, ProgrammingError

from assetops_backend.work.domain_action import CODE_CONFLICT_CONSTRAINT, refuse
from assetops_backend.work.model import WorkStoreUnavailable

SERIALIZATION_ATTEMPTS = 3
_CONFLICT_CONSTRAINTS = (CODE_CONFLICT_CONSTRAINT, "domain_action_intent_root", "domain_action_intent_one_successor")

#: (connection, tenant, site, site_code, finding_revision pin row, cutoff) -> the selected pin or None.
PinOf = Callable[[Connection, UUID, UUID, str, dict[str, Any], datetime], "dict[str, Any] | None"]

_ACTION_COLS = ("CAST(id AS text) AS id, action_no, action_code, domain, CAST(origin_finding_id AS text) AS "
                "origin_finding_id, CAST(origin_finding_revision_id AS text) AS origin_finding_revision_id, title, "
                "owner_label, due_at, raised_at, recorded_at, actor_kind, actor_id, attestation, idempotency_key, "
                "payload_sha256")
_INTENT_COLS = ("CAST(id AS text) AS id, CAST(action_id AS text) AS action_id, CAST(supersedes_id AS text) AS "
                "supersedes_id, declared_at, recorded_at, criteria, basis, idempotency_key, payload_sha256")
_LINK_COLS = ("CAST(id AS text) AS id, CAST(action_id AS text) AS action_id, CAST(case_id AS text) AS case_id, "
              "CAST(case_revision_id AS text) AS case_revision_id, CAST(case_event_id AS text) AS case_event_id, "
              "recorded_at, idempotency_key, payload_sha256")


def _one(result) -> dict[str, Any] | None:
    row = result.first()
    return None if row is None else dict(row._mapping)


class _DomainTx:
    """One command's scoped transaction: reads and INSERTs on the caller's connection, bounded by `command_now`."""

    def __init__(self, c: Connection, tenant_id: UUID, site_id: UUID, site_code: str, command_now: datetime,
                 pin_of: PinOf | None) -> None:
        self._c, self._t, self._s, self._code, self._now, self._pin_of = c, tenant_id, site_id, site_code, command_now, pin_of

    def _p(self, **extra: Any) -> dict[str, Any]:
        return {"t": self._t, "s": self._s, "now": self._now, **extra}

    def db_now(self) -> datetime:
        return self._now

    def lock(self, command: str, key: str) -> None:
        self._c.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:k, 0))"),
                        {"k": f"{self._t}:{self._s}:{command}:{key}"})

    # ---- root ----------------------------------------------------------------------------------------------

    def action_by_key(self, key: str) -> dict[str, Any] | None:
        return _one(self._c.execute(text(f"SELECT {_ACTION_COLS} FROM domain_action WHERE tenant_id = :t "
                                         "AND site_id = :s AND idempotency_key = :k"), self._p(k=key)))

    def action(self, action_id: str) -> dict[str, Any] | None:
        return _one(self._c.execute(text(f"SELECT {_ACTION_COLS} FROM domain_action WHERE tenant_id = :t "
                                         "AND site_id = :s AND id = :i AND recorded_at <= :now"), self._p(i=action_id)))

    def finding_revision(self, finding_id: str, revision_id: str) -> dict[str, Any] | None:
        """The exact scoped revision of that Finding, created by `command_now`, with its selection pin columns."""
        return _one(self._c.execute(text(
            "SELECT CAST(fr.id AS text) AS id, CAST(fr.finding_id AS text) AS finding_id, fr.domain, fr.analytic_id, "
            "fr.analytic_run_id, fr.assessment_revision_id, fr.episode_start, fr.episode_end, fr.created_at "
            "FROM finding_revision fr WHERE fr.tenant_id = :t AND fr.site_id = :s AND fr.id = :r "
            "AND fr.finding_id = :f AND fr.created_at <= :now"), self._p(f=finding_id, r=revision_id)))

    def selected_pin(self, revision: dict[str, Any]) -> dict[str, Any] | None:
        if self._pin_of is None:
            raise WorkStoreUnavailable("The domain Action store has no selected Finding reader.")
        return self._pin_of(self._c, self._t, self._s, self._code, revision, self._now)

    def cited_evidence(self, revision_id: str) -> set[str]:
        """The revision's cited accepted evidence received by `command_now`, scoped to this tenant/Site."""
        rows = self._c.execute(text(
            "SELECT CAST(e.evidence_id AS text) FROM finding_revision_evidence e JOIN accepted_evidence a "
            "ON a.tenant_id = e.tenant_id AND a.site_id = e.site_id AND a.id = e.evidence_id "
            "WHERE e.tenant_id = :t AND e.site_id = :s AND e.finding_revision_id = :r AND a.received_at <= :now"),
            self._p(r=revision_id))
        return set(rows.scalars())

    def next_action_no(self) -> int:
        return int(self._c.execute(text("SELECT nextval('action_code_seq')")).scalar_one())

    def insert_action(self, row: dict[str, Any]) -> None:
        self._c.execute(text(
            "INSERT INTO domain_action (id, tenant_id, site_id, action_no, action_code, domain, origin_finding_id, "
            "origin_finding_revision_id, title, owner_label, due_at, raised_at, recorded_at, actor_kind, actor_id, "
            "attestation, idempotency_key, payload_sha256) VALUES (:id, :t, :s, :action_no, :action_code, :domain, "
            ":origin_finding_id, :origin_finding_revision_id, :title, :owner_label, :due_at, :raised_at, :now, "
            ":actor_kind, :actor_id, :attestation, :idempotency_key, :payload_sha256)"), self._p(**row))

    # ---- intent --------------------------------------------------------------------------------------------

    def intent_by_key(self, action_id: str, key: str) -> dict[str, Any] | None:
        return _one(self._c.execute(text(f"SELECT {_INTENT_COLS} FROM domain_action_intent WHERE tenant_id = :t "
                                         "AND site_id = :s AND action_id = :a AND idempotency_key = :k"),
                                    self._p(a=action_id, k=key)))

    def intent_ids(self, action_id: str) -> tuple[list[str], set[str]]:
        """All intent IDs of the Action and the IDs already superseded (the head has no successor)."""
        rows = self._c.execute(text(
            "SELECT CAST(id AS text), CAST(supersedes_id AS text) FROM domain_action_intent WHERE tenant_id = :t "
            "AND site_id = :s AND action_id = :a"), self._p(a=action_id)).all()
        return [r[0] for r in rows], {r[1] for r in rows if r[1] is not None}

    def insert_intent(self, row: dict[str, Any]) -> None:
        self._c.execute(text(
            "INSERT INTO domain_action_intent (id, tenant_id, site_id, action_id, supersedes_id, declared_at, "
            "recorded_at, criteria, basis, actor_kind, actor_id, attestation, idempotency_key, payload_sha256) "
            "VALUES (:id, :t, :s, :action_id, :supersedes_id, :declared_at, :now, CAST(:criteria AS jsonb), "
            "CAST(:basis AS jsonb), :actor_kind, :actor_id, :attestation, :idempotency_key, :payload_sha256)"),
            self._p(**{**row, "criteria": json.dumps(row["criteria"]), "basis": json.dumps(row["basis"])}))

    # ---- W4 case selection and the explicit link ------------------------------------------------------------

    def case(self, case_id: str) -> dict[str, Any] | None:
        return _one(self._c.execute(text(
            "SELECT CAST(id AS text) AS id, kind FROM work_case WHERE tenant_id = :t AND site_id = :s AND id = :i "
            "AND created_at <= :now"), self._p(i=case_id)))

    def case_heads(self, case_id: str) -> tuple[set[str], set[str], str | None, str | None]:
        """The case's revision and event IDs recorded by `command_now`, and its head revision and latest event."""
        revs = self._c.execute(text(
            "SELECT CAST(id AS text) FROM work_case_revision WHERE tenant_id = :t AND site_id = :s AND case_id = :i "
            "AND recorded_at <= :now ORDER BY revision_no"), self._p(i=case_id)).scalars().all()
        events = self._c.execute(text(
            "SELECT CAST(id AS text) FROM work_event WHERE tenant_id = :t AND site_id = :s AND case_id = :i "
            "AND recorded_at <= :now ORDER BY recorded_at, id"), self._p(i=case_id)).scalars().all()
        return set(revs), set(events), (revs[-1] if revs else None), (events[-1] if events else None)

    def case_link_by_key(self, action_id: str, key: str) -> dict[str, Any] | None:
        return _one(self._c.execute(text(f"SELECT {_LINK_COLS} FROM domain_action_case_link WHERE tenant_id = :t "
                                         "AND site_id = :s AND action_id = :a AND idempotency_key = :k"),
                                    self._p(a=action_id, k=key)))

    def case_link_exists(self, action_id: str, case_id: str, revision_id: str, event_id: str) -> bool:
        return self._c.execute(text(
            "SELECT 1 FROM domain_action_case_link WHERE tenant_id = :t AND site_id = :s AND action_id = :a "
            "AND case_id = :c AND case_revision_id = :r AND case_event_id = :e"),
            self._p(a=action_id, c=case_id, r=revision_id, e=event_id)).first() is not None

    def selected_case_link(self, action_id: str, case_id: str, upto: datetime) -> dict[str, Any] | None:
        """The newest explicit link of this case to this Action recorded by `upto`."""
        return _one(self._c.execute(text(
            f"SELECT {_LINK_COLS} FROM domain_action_case_link WHERE tenant_id = :t AND site_id = :s "
            "AND action_id = :a AND case_id = :c AND recorded_at <= :u ORDER BY recorded_at DESC, id DESC LIMIT 1"),
            self._p(a=action_id, c=case_id, u=upto)))

    def record_in_case(self, case_id: str, record_id: str) -> bool:
        """A performed W4 record (`maintenance_record`) on that request, recorded by `command_now`."""
        return self._c.execute(text(
            "SELECT 1 FROM maintenance_record WHERE tenant_id = :t AND site_id = :s AND case_id = :c AND id = :r "
            "AND recorded_at <= :now"), self._p(c=case_id, r=record_id)).first() is not None

    def insert_case_link(self, row: dict[str, Any]) -> None:
        self._c.execute(text(
            "INSERT INTO domain_action_case_link (id, tenant_id, site_id, action_id, case_id, case_revision_id, "
            "case_event_id, recorded_at, actor_kind, actor_id, attestation, idempotency_key, payload_sha256) "
            "VALUES (:id, :t, :s, :action_id, :case_id, :case_revision_id, :case_event_id, :now, :actor_kind, "
            ":actor_id, :attestation, :idempotency_key, :payload_sha256)"), self._p(**row))


class PostgresDomainIntentStore:
    def __init__(self, database_url: str | None, *, pin_of: PinOf | None = None, statement_timeout_ms: int = 30_000,
                 lock_timeout_ms: int = 5_000, test_db_clock_override: Callable[[], datetime] | None = None) -> None:
        self._database_url = database_url
        self._pin_of = pin_of
        # Test-only virtual DB instant; production composition never passes it.
        self.test_db_clock_override = test_db_clock_override
        self._options = f"-c statement_timeout={int(statement_timeout_ms)} -c lock_timeout={int(lock_timeout_ms)}"
        self._engine: Engine | None = None

    def _connect(self) -> Engine:
        if not self._database_url:
            raise WorkStoreUnavailable("DATABASE_URL is not set, so the domain Action store cannot be reached.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True,
                                         connect_args={"options": self._options})
        return self._engine

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def transaction(self, tenant_id: UUID, site_id: UUID, site_code: str, work: Callable[[_DomainTx], Any]) -> Any:
        command_now: datetime | None = None
        for attempt in range(SERIALIZATION_ATTEMPTS):
            try:
                with self._connect().begin() as c:
                    c.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
                    if command_now is None:
                        command_now = (self.test_db_clock_override() if self.test_db_clock_override is not None
                                       else c.execute(text("SELECT clock_timestamp()")).scalar_one().astimezone(timezone.utc))
                        assert command_now.tzinfo is not None and command_now.utcoffset() == timedelta(0)
                    return work(_DomainTx(c, tenant_id, site_id, site_code, command_now, self._pin_of))
            except IntegrityError as error:
                if getattr(error.orig, "sqlstate", None) == "40001" and attempt + 1 < SERIALIZATION_ATTEMPTS:
                    continue
                constraint = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
                if constraint in _CONFLICT_CONSTRAINTS:
                    raise refuse("DOMAIN_INTENT_CONFLICT") from error
                raise
            except (OperationalError, ProgrammingError) as error:
                if getattr(error.orig, "sqlstate", None) == "40001" and attempt + 1 < SERIALIZATION_ATTEMPTS:
                    continue
                raise WorkStoreUnavailable(f"The domain Action store failed: {error.orig}") from error
            except DBAPIError as error:
                if getattr(error.orig, "sqlstate", None) == "40001" and attempt + 1 < SERIALIZATION_ATTEMPTS:
                    continue
                if error.connection_invalidated:
                    raise WorkStoreUnavailable(str(error.orig)) from error
                raise
        raise WorkStoreUnavailable("The domain Action store could not serialize this command.")
