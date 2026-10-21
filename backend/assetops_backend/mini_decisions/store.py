"""W4-03 unit 1: the sole writer of the ten migration-0030 mini-decision tables (insert skeletons).

`.agent/W4-03-build-spec.md` closure 1 ("Rule-8 registers exactly `mini_decisions/store.py`"), closure 4 S3/S4.
Every write is one INSERT into one 0030 table on the caller's transaction; 0030's `<table>_immutable` triggers
refuse UPDATE and DELETE, and this module never issues either, never upserts and never writes another table. The
later units compose these inserts into their commands and add their own rules (scenario, alternative, projection,
link). This unit carries the two relationship checks SQL cannot state for rows it can already be handed:

- an alternative revision's `finding_revision_id` must belong to its `finding_id` (S4: two scoped FKs plus a service
  pair check, no invented composite FK);
- an opportunity revision's `source_job_id` and a selection's `job_id` must name a `mini_opportunity` recompute job
  of the same tenant and Site (S3; null only for a named backfill), and a selection's revision must belong to its
  opportunity.

`created_at`/`recorded_at`/`selected_at` are the database `clock_timestamp()` defaults.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Mapping, TypeVar
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError, ProgrammingError

#: The one W4-03 job domain (closure 1); never leased by Dispatch or W4-02's four-domain worker.
OPPORTUNITY_JOB_DOMAIN = "mini_opportunity"
#: The exact opportunity producer model version (closure 1).
OPPORTUNITY_MODEL_VERSION = "mini-opportunity/1"

T = TypeVar("T")


class MiniDecisionStoreUnavailable(RuntimeError):
    """The mini-decision database could not be reached or queried."""


class MiniDecisionWriteRefused(ValueError):
    """The requested row breaks a write rule; nothing was written."""


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


_INSERT_SCENARIO = (
    "INSERT INTO mini_scenario (id, tenant_id, site_id, create_key, create_payload_sha256, create_actor_id) "
    "VALUES (:id, :tenant_id, :site_id, :create_key, :create_payload_sha256, :create_actor_id) "
    "RETURNING public_no"
)
_INSERT_SCENARIO_REVISION = (
    "INSERT INTO mini_scenario_revision (id, tenant_id, site_id, scenario_id, revision_no, "
    "supersedes_revision_id, name, kind, narrative, assumptions, pinned_mini_revision_ids, pinned_selection_hours, "
    "calculation, correction_reason, actor_kind, actor_id, authorization_basis, attestation, idempotency_key, "
    "payload_sha256) VALUES (:id, :tenant_id, :site_id, :scenario_id, :revision_no, :supersedes_revision_id, "
    ":name, :kind, :narrative, CAST(:assumptions AS jsonb), CAST(:pinned_mini_revision_ids AS jsonb), "
    "CAST(:pinned_selection_hours AS jsonb), CAST(:calculation AS jsonb), :correction_reason, :actor_kind, "
    ":actor_id, :authorization_basis, :attestation, :idempotency_key, :payload_sha256)"
)
_INSERT_ALTERNATIVE_REVISION = (
    "INSERT INTO mini_alternative_revision (id, tenant_id, site_id, finding_id, finding_revision_id, "
    "alternative_key, version_no, supersedes_revision_id, rank, explanation, evidence_summary, "
    "missing_evidence_reason, disposition, reason, actor_kind, actor_id, authorization_basis, attestation, "
    "idempotency_key, payload_sha256) VALUES (:id, :tenant_id, :site_id, :finding_id, :finding_revision_id, "
    ":alternative_key, :version_no, :supersedes_revision_id, :rank, :explanation, :evidence_summary, "
    ":missing_evidence_reason, :disposition, :reason, :actor_kind, :actor_id, :authorization_basis, "
    ":attestation, :idempotency_key, :payload_sha256)"
)
_INSERT_ALTERNATIVE_EVIDENCE = (
    "INSERT INTO mini_alternative_evidence (tenant_id, site_id, alternative_revision_id, evidence_id) "
    "VALUES (:tenant_id, :site_id, :alternative_revision_id, :evidence_id)"
)
_INSERT_OPPORTUNITY = (
    "INSERT INTO mini_opportunity (id, tenant_id, site_id, first_day, last_day, model_version) "
    "VALUES (:id, :tenant_id, :site_id, :first_day, :last_day, :model_version) RETURNING public_no"
)
_INSERT_OPPORTUNITY_REVISION = (
    "INSERT INTO mini_opportunity_revision (id, tenant_id, site_id, opportunity_id, revision_no, selected_hours, "
    "result, input_sha256, producer_id, source_job_id, model_version) VALUES (:id, :tenant_id, :site_id, "
    ":opportunity_id, :revision_no, CAST(:selected_hours AS jsonb), CAST(:result AS jsonb), :input_sha256, "
    ":producer_id, :source_job_id, :model_version)"
)
_INSERT_OPPORTUNITY_EVIDENCE = (
    "INSERT INTO mini_opportunity_evidence (tenant_id, site_id, opportunity_revision_id, evidence_id) "
    "VALUES (:tenant_id, :site_id, :opportunity_revision_id, :evidence_id)"
)
_INSERT_OPPORTUNITY_SELECTION = (
    "INSERT INTO mini_opportunity_selection (tenant_id, site_id, opportunity_id, revision_id, job_id) "
    "VALUES (:tenant_id, :site_id, :opportunity_id, :revision_id, :job_id) RETURNING seq"
)
_INSERT_WORK_LINK = (
    "INSERT INTO mini_decision_work_link (id, tenant_id, site_id, case_id, scenario_id, opportunity_id, "
    "actor_kind, actor_id, authorization_basis, attestation, idempotency_key, payload_sha256) VALUES (:id, "
    ":tenant_id, :site_id, :case_id, :scenario_id, :opportunity_id, :actor_kind, :actor_id, "
    ":authorization_basis, :attestation, :idempotency_key, :payload_sha256)"
)
_INSERT_OPPORTUNITY_SCENARIO_LINK = (
    "INSERT INTO mini_opportunity_scenario_link (id, tenant_id, site_id, opportunity_id, scenario_id, "
    "actor_kind, actor_id, authorization_basis, attestation, idempotency_key, payload_sha256) VALUES (:id, "
    ":tenant_id, :site_id, :opportunity_id, :scenario_id, :actor_kind, :actor_id, :authorization_basis, "
    ":attestation, :idempotency_key, :payload_sha256)"
)


class PostgresMiniDecisionStore:
    """Appends 0030 rows on the caller's transaction (`transaction()` opens one when the caller has none)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @classmethod
    def from_url(cls, database_url: str) -> "PostgresMiniDecisionStore":
        return cls(create_engine(database_url, pool_pre_ping=True))

    def dispose(self) -> None:
        self._engine.dispose()

    @contextmanager
    def transaction(self) -> Iterator[Connection]:
        """One write transaction; a refused or failed insert rolls the whole block back."""
        try:
            with self._engine.begin() as c:
                yield c
        except MiniDecisionWriteRefused:
            raise
        except IntegrityError as error:
            raise MiniDecisionWriteRefused(f"The mini-decision write was refused: {error.orig}") from error
        except (OperationalError, ProgrammingError, DBAPIError) as error:
            raise MiniDecisionStoreUnavailable(f"The mini-decision store failed: {error.orig}") from error

    @staticmethod
    def _one(c: Connection, sql: str, row: Mapping[str, Any]) -> Any:
        return c.execute(text(sql), dict(row)).scalar()

    # --- service relationship checks -------------------------------------------------------------------------

    @staticmethod
    def _check_job(c: Connection, tenant_id: UUID, site_id: UUID, job_id: UUID | None, *, backfill: bool) -> None:
        if job_id is None:
            if not backfill:
                raise MiniDecisionWriteRefused("A null opportunity job is allowed only for a named backfill")
            return
        job = c.execute(text("SELECT tenant_id, site_id, domain FROM recompute_job WHERE id = :j FOR SHARE"),
                        {"j": job_id}).one_or_none()
        if job is None or (job.tenant_id, job.site_id, job.domain) != (tenant_id, site_id, OPPORTUNITY_JOB_DOMAIN):
            raise MiniDecisionWriteRefused(
                f"Recompute job {job_id} does not match this tenant, Site and {OPPORTUNITY_JOB_DOMAIN} domain")

    # --- inserts ----------------------------------------------------------------------------------------------

    def insert_scenario(self, c: Connection, row: Mapping[str, Any]) -> int:
        return self._one(c, _INSERT_SCENARIO, row)

    def insert_scenario_revision(self, c: Connection, row: Mapping[str, Any]) -> None:
        values = dict(row)
        for key in ("assumptions", "pinned_mini_revision_ids", "pinned_selection_hours", "calculation"):
            values[key] = _json(values.get(key, []))
        c.execute(text(_INSERT_SCENARIO_REVISION), values)

    def insert_alternative_revision(self, c: Connection, row: Mapping[str, Any]) -> None:
        owner = c.execute(text("SELECT finding_id FROM finding_revision WHERE tenant_id = :t AND site_id = :s "
                               "AND id = :r"),
                          {"t": row["tenant_id"], "s": row["site_id"], "r": row["finding_revision_id"]}).scalar()
        if owner != row["finding_id"]:
            raise MiniDecisionWriteRefused(
                f"Finding revision {row['finding_revision_id']} does not belong to Finding {row['finding_id']}")
        c.execute(text(_INSERT_ALTERNATIVE_REVISION), dict(row))

    def insert_alternative_evidence(self, c: Connection, row: Mapping[str, Any]) -> None:
        c.execute(text(_INSERT_ALTERNATIVE_EVIDENCE), dict(row))

    def insert_opportunity(self, c: Connection, row: Mapping[str, Any]) -> int:
        return self._one(c, _INSERT_OPPORTUNITY, row)

    def insert_opportunity_revision(self, c: Connection, row: Mapping[str, Any], *, backfill: bool = False) -> None:
        self._check_job(c, row["tenant_id"], row["site_id"], row.get("source_job_id"), backfill=backfill)
        values = dict(row)
        values.setdefault("source_job_id", None)
        values["selected_hours"] = _json(values["selected_hours"])
        values["result"] = _json(values["result"])
        c.execute(text(_INSERT_OPPORTUNITY_REVISION), values)

    def insert_opportunity_evidence(self, c: Connection, row: Mapping[str, Any]) -> None:
        c.execute(text(_INSERT_OPPORTUNITY_EVIDENCE), dict(row))

    def insert_opportunity_selection(self, c: Connection, row: Mapping[str, Any], *, backfill: bool = False) -> int:
        self._check_job(c, row["tenant_id"], row["site_id"], row.get("job_id"), backfill=backfill)
        owner = c.execute(text("SELECT opportunity_id FROM mini_opportunity_revision WHERE tenant_id = :t "
                               "AND site_id = :s AND id = :r"),
                          {"t": row["tenant_id"], "s": row["site_id"], "r": row["revision_id"]}).scalar()
        if owner != row["opportunity_id"]:
            raise MiniDecisionWriteRefused(
                f"Opportunity revision {row['revision_id']} does not belong to opportunity {row['opportunity_id']}")
        values = dict(row)
        values.setdefault("job_id", None)
        return self._one(c, _INSERT_OPPORTUNITY_SELECTION, values)

    def insert_work_link(self, c: Connection, row: Mapping[str, Any]) -> None:
        values = dict(row)
        values.setdefault("scenario_id", None)
        values.setdefault("opportunity_id", None)
        c.execute(text(_INSERT_WORK_LINK), values)

    def insert_opportunity_scenario_link(self, c: Connection, row: Mapping[str, Any]) -> None:
        c.execute(text(_INSERT_OPPORTUNITY_SCENARIO_LINK), dict(row))

    @contextmanager
    def snapshot(self) -> Iterator[Connection]:
        """One read-only REPEATABLE READ snapshot (closure 1 Q12-Q16); the caller captures DB time first."""
        try:
            with self._engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
                with c.begin():
                    c.execute(text("SET TRANSACTION READ ONLY"))
                    yield c
        except (OperationalError, ProgrammingError, DBAPIError) as error:
            raise MiniDecisionStoreUnavailable(f"The mini-decision read failed: {error.__class__.__name__}") from error

    @staticmethod
    def db_now(c: Connection) -> Any:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one()

    # --- scenario reads (unit 2b) -----------------------------------------------------------------------------

    @staticmethod
    def scenario_by_create_key(c: Connection, tenant_id: UUID, site_id: UUID, key: str) -> Mapping[str, Any] | None:
        return c.execute(text(
            "SELECT id, public_no, create_payload_sha256 FROM mini_scenario WHERE tenant_id = :t AND site_id = :s "
            "AND create_key = :k"), {"t": tenant_id, "s": site_id, "k": key}).mappings().one_or_none()

    @staticmethod
    def lock_scenario(c: Connection, tenant_id: UUID, site_id: UUID, scenario_id: str) -> Mapping[str, Any] | None:
        """The scenario root, row-locked for a correction (closure 1: every POST locks its root/head)."""
        return c.execute(text(
            "SELECT id, public_no FROM mini_scenario WHERE tenant_id = :t AND site_id = :s AND id = :id FOR UPDATE"),
            {"t": tenant_id, "s": site_id, "id": scenario_id}).mappings().one_or_none()

    @staticmethod
    def scenario_revisions(c: Connection, tenant_id: UUID, site_id: UUID, scenario_id: Any) -> list[Mapping[str, Any]]:
        return list(c.execute(text(
            "SELECT id, revision_no, supersedes_revision_id, idempotency_key, payload_sha256, recorded_at "
            "FROM mini_scenario_revision WHERE tenant_id = :t AND site_id = :s AND scenario_id = :id "
            "ORDER BY revision_no"), {"t": tenant_id, "s": site_id, "id": scenario_id}).mappings())

    @staticmethod
    def scenario_heads(c: Connection, tenant_id: UUID, site_id: UUID, lo: Any, hi: Any,
                       known: Any) -> list[Mapping[str, Any]]:
        """Every root created in UTC `[lo, hi)` and visible at `known`, with its head revision at that cutoff:
        greatest `(recorded_at, revision_no, id)` (closure 1 Q12-Q16; a correction never moves root membership)."""
        return list(c.execute(text(
            "SELECT DISTINCT ON (m.id) m.id, m.public_no, m.created_at, r.id AS revision_id, r.revision_no, r.name, "
            "r.kind, r.narrative, r.assumptions, r.pinned_mini_revision_ids, r.pinned_selection_hours, "
            "r.calculation, r.actor_id, r.recorded_at FROM mini_scenario m JOIN mini_scenario_revision r "
            "ON r.tenant_id = m.tenant_id AND r.site_id = m.site_id AND r.scenario_id = m.id "
            "WHERE m.tenant_id = :t AND m.site_id = :s AND m.created_at >= :lo AND m.created_at < :hi "
            "AND m.created_at <= :k AND r.recorded_at <= :k "
            "ORDER BY m.id, r.recorded_at DESC, r.revision_no DESC, r.id DESC"),
            {"t": tenant_id, "s": site_id, "lo": lo, "hi": hi, "k": known}).mappings())

    def run(self, work: Callable[[Connection], T]) -> T:
        """Run `work` in one write transaction (convenience for callers holding no connection)."""
        with self.transaction() as c:
            return work(c)
