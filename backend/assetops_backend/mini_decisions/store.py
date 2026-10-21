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
    "idempotency_key, payload_sha256, created_at) VALUES (:id, :tenant_id, :site_id, :finding_id, "
    ":finding_revision_id, :alternative_key, :version_no, :supersedes_revision_id, :rank, :explanation, "
    ":evidence_summary, :missing_evidence_reason, :disposition, :reason, :actor_kind, :actor_id, "
    ":authorization_basis, :attestation, :idempotency_key, :payload_sha256, "
    "COALESCE(CAST(:created_at AS timestamptz), clock_timestamp()))"
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
    def _check_job(c: Connection, tenant_id: UUID, site_id: UUID, job_id: UUID | None, *, backfill: bool,
                   study_window: tuple[Any, Any] | None = None) -> None:
        """S3 plus u3 unit-4 dry-read: the job names this tenant, Site and domain and, when the caller passes the
        study's Site-local midnight bounds, exactly that five-day window."""
        if job_id is None:
            if not backfill:
                raise MiniDecisionWriteRefused("A null opportunity job is allowed only for a named backfill")
            return
        job = c.execute(text("SELECT tenant_id, site_id, domain, window_start, window_end FROM recompute_job "
                             "WHERE id = :j FOR SHARE"), {"j": job_id}).one_or_none()
        if job is None or (job.tenant_id, job.site_id, job.domain) != (tenant_id, site_id, OPPORTUNITY_JOB_DOMAIN):
            raise MiniDecisionWriteRefused(
                f"Recompute job {job_id} does not match this tenant, Site and {OPPORTUNITY_JOB_DOMAIN} domain")
        if study_window is not None and (job.window_start, job.window_end) != tuple(study_window):
            raise MiniDecisionWriteRefused(f"Recompute job {job_id} does not cover exactly this five-day study")

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
        values = dict(row)
        values.setdefault("created_at", None)  # unit 3: the command instant (DB time, or the test-only override)
        c.execute(text(_INSERT_ALTERNATIVE_REVISION), values)

    def insert_alternative_evidence(self, c: Connection, row: Mapping[str, Any]) -> None:
        c.execute(text(_INSERT_ALTERNATIVE_EVIDENCE), dict(row))

    def insert_opportunity(self, c: Connection, row: Mapping[str, Any]) -> int:
        return self._one(c, _INSERT_OPPORTUNITY, row)

    def insert_opportunity_revision(self, c: Connection, row: Mapping[str, Any], *, backfill: bool = False,
                                    study_window: tuple[Any, Any] | None = None) -> None:
        self._check_job(c, row["tenant_id"], row["site_id"], row.get("source_job_id"), backfill=backfill,
                        study_window=study_window)
        values = dict(row)
        values.setdefault("source_job_id", None)
        values["selected_hours"] = _json(values["selected_hours"])
        values["result"] = _json(values["result"])
        c.execute(text(_INSERT_OPPORTUNITY_REVISION), values)

    def insert_opportunity_evidence(self, c: Connection, row: Mapping[str, Any]) -> None:
        c.execute(text(_INSERT_OPPORTUNITY_EVIDENCE), dict(row))

    def insert_opportunity_selection(self, c: Connection, row: Mapping[str, Any], *, backfill: bool = False,
                                     study_window: tuple[Any, Any] | None = None) -> int:
        self._check_job(c, row["tenant_id"], row["site_id"], row.get("job_id"), backfill=backfill,
                        study_window=study_window)
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

    # --- alternative reads (unit 3) ---------------------------------------------------------------------------

    @staticmethod
    def finding_root(c: Connection, tenant_id: UUID, site_id: UUID, finding_id: str, *,
                     lock: bool = False) -> Mapping[str, Any] | None:
        """The W1 Finding root of this tenant/Site. A command row-locks it (`FOR NO KEY UPDATE`: it serializes
        alternative commands on one Finding without blocking W1's own revision inserts, which take KEY SHARE)."""
        sql = "SELECT id, domain, created_at FROM finding WHERE tenant_id = :t AND site_id = :s AND id = :id"
        if lock:
            sql += " FOR NO KEY UPDATE"
        return c.execute(text(sql), {"t": tenant_id, "s": site_id, "id": finding_id}).mappings().one_or_none()

    @staticmethod
    def finding_revisions(c: Connection, tenant_id: UUID, site_id: UUID, finding_id: Any) -> list[Mapping[str, Any]]:
        return list(c.execute(text(
            "SELECT id, revision_no, analytic_id, episode_start, episode_end, created_at FROM finding_revision "
            "WHERE tenant_id = :t AND site_id = :s AND finding_id = :f ORDER BY revision_no"),
            {"t": tenant_id, "s": site_id, "f": finding_id}).mappings())

    @staticmethod
    def alternative_revisions(c: Connection, tenant_id: UUID, site_id: UUID,
                              finding_id: Any) -> list[Mapping[str, Any]]:
        """Every alternative revision of one Finding with its exact sorted cited accepted IDs, by key then version."""
        return list(c.execute(text(
            "SELECT r.id, r.finding_revision_id, r.alternative_key, r.version_no, r.supersedes_revision_id, "
            "r.explanation, r.evidence_summary, r.missing_evidence_reason, r.disposition, r.reason, "
            "r.idempotency_key, r.payload_sha256, r.created_at, COALESCE((SELECT array_agg(e.evidence_id::text "
            "ORDER BY e.evidence_id::text) FROM mini_alternative_evidence e WHERE e.tenant_id = r.tenant_id "
            "AND e.site_id = r.site_id AND e.alternative_revision_id = r.id), '{}') AS cited "
            "FROM mini_alternative_revision r WHERE r.tenant_id = :t AND r.site_id = :s AND r.finding_id = :f "
            "ORDER BY r.alternative_key, r.version_no"), {"t": tenant_id, "s": site_id, "f": finding_id}).mappings())

    @staticmethod
    def accepted_intervals(c: Connection, tenant_id: UUID, site_id: UUID, evidence_ids: list[str],
                           now: Any) -> dict[str, tuple[Any, Any]]:
        """The named accepted rows of this tenant/Site received by `now`, keyed by lowercase ID, each with its
        accepted interval; point evidence is `[source_time, source_time + 1us)` as 0029 normalizes it (N2)."""
        if not evidence_ids:
            return {}
        rows = c.execute(text(
            "SELECT id::text, COALESCE(interval_start, source_time), "
            "COALESCE(interval_end, source_time + interval '1 microsecond') FROM accepted_evidence "
            "WHERE tenant_id = :t AND site_id = :s AND id = ANY(CAST(:ids AS uuid[])) AND received_at <= :now"),
            {"t": tenant_id, "s": site_id, "ids": evidence_ids, "now": now}).all()
        return {str(r[0]).lower(): (r[1], r[2]) for r in rows}

    # --- opportunity scan reads (unit 4: closure 2 Q4, closure 4 S5/S6) ------------------------------------------

    @staticmethod
    def renewable_scan_heads(c: Connection, retention_start: Any, tenant_id: UUID | None = None,
                             site_id: UUID | None = None) -> list[Any]:
        """Closure 2 Q4's head query: the latest committed renewable selection `(selected_at DESC, seq DESC)` of
        each Site/noon whose UTC instant is `>= retention_start`, with the Site's time zone; optionally one Site."""
        scope = "" if site_id is None else " AND s.tenant_id = :t AND s.site_id = :s"
        return c.execute(text(
            "SELECT DISTINCT ON (s.tenant_id, s.site_id, s.window_start) s.tenant_id, s.site_id, s.window_start, "
            "s.window_end, s.seq, s.revision_id, s.selected_at, st.timezone "
            "FROM mini_depth_selection AS s JOIN site AS st ON st.tenant_id = s.tenant_id AND st.id = s.site_id "
            "WHERE s.domain = 'renewable' AND s.window_start >= :retention_start" + scope +
            " ORDER BY s.tenant_id, s.site_id, s.window_start, s.selected_at DESC, s.seq DESC"),
            {"retention_start": retention_start, "t": tenant_id, "s": site_id}).all()

    @staticmethod
    def renewable_noon_heads(c: Connection, tenant_id: UUID, site_id: UUID, starts: list[Any]) -> list[Any]:
        """Each named noon's latest renewable head: `(window_start, seq, selected_at, revision id, input digest,
        decision, sorted accepted IDs, selection window_end, revision window_start and window_end, revision result)`;
        a noon with no selection is absent."""
        return c.execute(text(
            "SELECT DISTINCT ON (s.window_start) s.window_start, s.seq, s.selected_at, r.id::text, r.input_sha256, "
            "r.result->'hour'->>'decision', COALESCE((SELECT array_agg(v.evidence_id::text "
            "ORDER BY v.evidence_id::text) FROM mini_depth_revision_evidence v WHERE v.tenant_id = r.tenant_id "
            "AND v.site_id = r.site_id AND v.revision_id = r.id), '{}'), s.window_end, r.window_start, "
            "r.window_end, r.result "
            "FROM mini_depth_selection s JOIN mini_depth_revision r ON r.tenant_id = s.tenant_id "
            "AND r.site_id = s.site_id AND r.id = s.revision_id "
            "WHERE s.tenant_id = :t AND s.site_id = :s AND s.domain = 'renewable' AND r.domain = 'renewable' "
            "AND s.window_start = ANY(CAST(:starts AS timestamptz[])) "
            "ORDER BY s.window_start, s.selected_at DESC, s.seq DESC"),
            {"t": tenant_id, "s": site_id, "starts": starts}).all()

    @staticmethod
    def latest_opportunity_sha(c: Connection, tenant_id: UUID, site_id: UUID, first_day: Any,
                               last_day: Any) -> str | None:
        """The `input_sha256` of the study's latest projected revision (greatest selection `(selected_at, seq)`)."""
        return c.execute(text(
            "SELECT r.input_sha256 FROM mini_opportunity o JOIN mini_opportunity_selection x "
            "ON x.tenant_id = o.tenant_id AND x.site_id = o.site_id AND x.opportunity_id = o.id "
            "JOIN mini_opportunity_revision r ON r.tenant_id = x.tenant_id AND r.site_id = x.site_id "
            "AND r.id = x.revision_id WHERE o.tenant_id = :t AND o.site_id = :s AND o.first_day = :f "
            "AND o.last_day = :l AND o.model_version = :v ORDER BY x.selected_at DESC, x.seq DESC LIMIT 1"),
            {"t": tenant_id, "s": site_id, "f": first_day, "l": last_day, "v": OPPORTUNITY_MODEL_VERSION}).scalar()

    @staticmethod
    def lock_study(c: Connection, tenant_id: UUID, site_id: UUID, first_day: Any, last_day: Any) -> None:
        """Closure 2 Q4's study-key advisory lock, so two projections of one study serialize."""
        c.execute(text(
            "SELECT pg_advisory_xact_lock(hashtextextended(CAST(:t AS text) || ':' || CAST(:s AS text) || "
            "':mini_opportunity:' || CAST(:f AS text) || ':' || CAST(:l AS text), 0))"),
            {"t": tenant_id, "s": site_id, "f": first_day, "l": last_day})

    @staticmethod
    def site_timezone(c: Connection, tenant_id: UUID, site_id: UUID) -> Any:
        """The Site's row `(timezone,)`, or None for an unknown Site."""
        return c.execute(text("SELECT timezone FROM site WHERE tenant_id = :t AND id = :s"),
                         {"t": tenant_id, "s": site_id}).one_or_none()

    @staticmethod
    def opportunity_root(c: Connection, tenant_id: UUID, site_id: UUID, first_day: Any, last_day: Any) -> Any:
        """The study's `mini-opportunity/1` root ID, or None."""
        return c.execute(text(
            "SELECT id FROM mini_opportunity WHERE tenant_id = :t AND site_id = :s AND first_day = :f "
            "AND last_day = :l AND model_version = :v"),
            {"t": tenant_id, "s": site_id, "f": first_day, "l": last_day, "v": OPPORTUNITY_MODEL_VERSION}).scalar()

    @staticmethod
    def opportunity_state(c: Connection, tenant_id: UUID, site_id: UUID, opportunity_id: Any,
                          input_sha256: str) -> tuple[Any, Any, int]:
        """`(revision ID with this input digest or None, head revision ID or None, greatest revision_no or 0)`."""
        params = {"t": tenant_id, "s": site_id, "o": opportunity_id, "h": input_sha256}
        same = c.execute(text(
            "SELECT id FROM mini_opportunity_revision WHERE tenant_id = :t AND site_id = :s "
            "AND opportunity_id = :o AND input_sha256 = :h"), params).scalar()
        head = c.execute(text(
            "SELECT revision_id FROM mini_opportunity_selection WHERE tenant_id = :t AND site_id = :s "
            "AND opportunity_id = :o ORDER BY selected_at DESC, seq DESC LIMIT 1"), params).scalar()
        top = c.execute(text(
            "SELECT COALESCE(max(revision_no), 0) FROM mini_opportunity_revision WHERE tenant_id = :t "
            "AND site_id = :s AND opportunity_id = :o"), params).scalar_one()
        return same, head, int(top)

    # --- opportunity reads and the scenario association (unit 5, u5) -------------------------------------------

    @staticmethod
    def opportunity_roots(c: Connection, tenant_id: UUID, site_id: UUID, *, known: Any, lo_day: Any = None,
                          hi_day: Any = None, opportunity_id: str | None = None) -> list[Mapping[str, Any]]:
        """`mini-opportunity/1` roots visible at `known`: either the one named root, or every study whose
        `[first_day, last_day + 1 day)` intersects the Site-local day range `[lo_day, hi_day)` (u5 ruling 6)."""
        where = "o.id = CAST(:o AS uuid)" if opportunity_id is not None else "o.first_day < :hi AND o.last_day >= :lo"
        return list(c.execute(text(
            "SELECT o.id, o.public_no, o.first_day, o.last_day, o.model_version, o.created_at FROM mini_opportunity o "
            f"WHERE o.tenant_id = :t AND o.site_id = :s AND o.model_version = :v AND o.created_at <= :k AND {where}"),
            {"t": tenant_id, "s": site_id, "v": OPPORTUNITY_MODEL_VERSION, "k": known, "lo": lo_day, "hi": hi_day,
             "o": opportunity_id}).mappings())

    @staticmethod
    def opportunity_selections(c: Connection, tenant_id: UUID, site_id: UUID, opportunity_ids: list[Any],
                               known: Any) -> list[Mapping[str, Any]]:
        """Every selection of the named roots with `selected_at <= known` and its revision `created_at <= known`,
        ordered `(selected_at DESC, seq DESC)` (closure 1 Q12-Q16). The caller applies the pinned W4-02 cutoff."""
        if not opportunity_ids:
            return []
        return list(c.execute(text(
            "SELECT x.seq, x.opportunity_id, x.revision_id, x.job_id, x.selected_at, r.revision_no, r.input_sha256, "
            "r.created_at, r.selected_hours, r.result FROM mini_opportunity_selection x "
            "JOIN mini_opportunity_revision r ON r.tenant_id = x.tenant_id AND r.site_id = x.site_id "
            "AND r.id = x.revision_id WHERE x.tenant_id = :t AND x.site_id = :s "
            "AND x.opportunity_id = ANY(CAST(:ids AS uuid[])) AND x.selected_at <= :k AND r.created_at <= :k "
            "ORDER BY x.selected_at DESC, x.seq DESC"),
            {"t": tenant_id, "s": site_id, "ids": [str(i) for i in opportunity_ids], "k": known}).mappings())

    @staticmethod
    def failed_opportunity_job_at(c: Connection, tenant_id: UUID, site_id: UUID, lo: Any, hi: Any) -> Any:
        """uF 6: the latest failure instant (`available_at` of a terminal FAILED job) of this exact study window."""
        return c.execute(text(
            "SELECT max(available_at) FROM recompute_job WHERE tenant_id = :t AND site_id = :s AND domain = :d "
            "AND window_start = :lo AND window_end = :hi AND status = 'FAILED'"),
            {"t": tenant_id, "s": site_id, "d": OPPORTUNITY_JOB_DOMAIN, "lo": lo, "hi": hi}).scalar()

    @staticmethod
    def live_opportunity_jobs_at(c: Connection, tenant_id: UUID, site_id: UUID, lo: Any, hi: Any,
                                 known: Any) -> list[Any]:
        """u5 ruling 2, narrowed by uF 6: `(id, status)` of this Site's `mini_opportunity` jobs overlapping UTC
        `[lo, hi)` that are PENDING or LEASED and created by `known` (a future `available_at` limits leasing, not
        whether the job is a pending source), or FAILED with its failure instant `available_at <= known`."""
        return c.execute(text(
            "SELECT id::text, status FROM recompute_job WHERE tenant_id = :t AND site_id = :s AND domain = :d "
            "AND window_start < :hi AND window_end > :lo AND ((status IN ('PENDING', 'LEASED') "
            "AND created_at <= :k) OR (status = 'FAILED' AND available_at <= :k)) ORDER BY id"),
            {"t": tenant_id, "s": site_id, "d": OPPORTUNITY_JOB_DOMAIN, "lo": lo, "hi": hi, "k": known}).all()

    @staticmethod
    def opportunity_scenario_links(c: Connection, tenant_id: UUID, site_id: UUID, opportunity_ids: list[Any],
                                   known: Any) -> list[Mapping[str, Any]]:
        """The visible associations of the named roots, ordered `(created_at DESC, id DESC)` (u5 ruling 4)."""
        if not opportunity_ids:
            return []
        return list(c.execute(text(
            "SELECT id, opportunity_id, scenario_id, created_at FROM mini_opportunity_scenario_link "
            "WHERE tenant_id = :t AND site_id = :s AND opportunity_id = ANY(CAST(:ids AS uuid[])) "
            "AND created_at <= :k ORDER BY created_at DESC, id DESC"),
            {"t": tenant_id, "s": site_id, "ids": [str(i) for i in opportunity_ids], "k": known}).mappings())

    @staticmethod
    def opportunity_work_kinds(c: Connection, tenant_id: UUID, site_id: UUID, opportunity_ids: list[Any],
                               known: Any) -> list[Any]:
        """`(opportunity_id, case kind)` of each visible explicit work association (u5 ruling 7)."""
        if not opportunity_ids:
            return []
        return c.execute(text(
            "SELECT l.opportunity_id, w.kind FROM mini_decision_work_link l JOIN work_case w "
            "ON w.tenant_id = l.tenant_id AND w.site_id = l.site_id AND w.id = l.case_id "
            "WHERE l.tenant_id = :t AND l.site_id = :s AND l.opportunity_id = ANY(CAST(:ids AS uuid[])) "
            "AND l.created_at <= :k"),
            {"t": tenant_id, "s": site_id, "ids": [str(i) for i in opportunity_ids], "k": known}).all()

    @staticmethod
    def scenario_head_at(c: Connection, tenant_id: UUID, site_id: UUID, scenario_id: Any,
                         known: Any) -> Mapping[str, Any] | None:
        """The scenario's head revision at `known`: greatest `(recorded_at, revision_no, id)` (closure 1 Q12-Q16)."""
        return c.execute(text(
            "SELECT r.id, r.kind, r.assumptions, r.pinned_selection_hours, r.calculation FROM mini_scenario m "
            "JOIN mini_scenario_revision r ON r.tenant_id = m.tenant_id AND r.site_id = m.site_id "
            "AND r.scenario_id = m.id WHERE m.tenant_id = :t AND m.site_id = :s AND m.id = :id "
            "AND m.created_at <= :k AND r.recorded_at <= :k "
            "ORDER BY r.recorded_at DESC, r.revision_no DESC, r.id DESC LIMIT 1"),
            {"t": tenant_id, "s": site_id, "id": scenario_id, "k": known}).mappings().one_or_none()

    @staticmethod
    def lock_opportunity(c: Connection, tenant_id: UUID, site_id: UUID, opportunity_id: str) -> Any:
        """The opportunity root ID, row-locked for an association command (closure 1: a POST locks its root)."""
        return c.execute(text(
            "SELECT id FROM mini_opportunity WHERE tenant_id = :t AND site_id = :s AND id = :id FOR UPDATE"),
            {"t": tenant_id, "s": site_id, "id": opportunity_id}).scalar()

    @staticmethod
    def scenario_exists(c: Connection, tenant_id: UUID, site_id: UUID, scenario_id: str) -> bool:
        return c.execute(text("SELECT 1 FROM mini_scenario WHERE tenant_id = :t AND site_id = :s AND id = :id"),
                         {"t": tenant_id, "s": site_id, "id": scenario_id}).scalar() is not None

    @staticmethod
    def opportunity_link_by_key(c: Connection, tenant_id: UUID, site_id: UUID,
                                key: str) -> Mapping[str, Any] | None:
        return c.execute(text(
            "SELECT id, opportunity_id, scenario_id, payload_sha256, created_at FROM mini_opportunity_scenario_link "
            "WHERE tenant_id = :t AND site_id = :s AND idempotency_key = :k"),
            {"t": tenant_id, "s": site_id, "k": key}).mappings().one_or_none()

    # --- work associations and the Site Work context overlay (unit 8, u5) ---------------------------------------

    @staticmethod
    def lock_work_case(c: Connection, tenant_id: UUID, site_id: UUID, case_id: str) -> Any:
        """The W4-01 case ID at this tenant/Site, share-locked for a W4-03 association (W4-01 rows are never
        changed); None for an unknown or foreign case."""
        return c.execute(text(
            "SELECT id FROM work_case WHERE tenant_id = :t AND site_id = :s AND id = :id FOR SHARE"),
            {"t": tenant_id, "s": site_id, "id": case_id}).scalar()

    @staticmethod
    def opportunity_exists(c: Connection, tenant_id: UUID, site_id: UUID, opportunity_id: str) -> bool:
        return c.execute(text("SELECT 1 FROM mini_opportunity WHERE tenant_id = :t AND site_id = :s AND id = :id"),
                         {"t": tenant_id, "s": site_id, "id": opportunity_id}).scalar() is not None

    @staticmethod
    def work_link_by_key(c: Connection, tenant_id: UUID, site_id: UUID, key: str) -> Mapping[str, Any] | None:
        return c.execute(text(
            "SELECT id, case_id, scenario_id, opportunity_id, payload_sha256, created_at FROM mini_decision_work_link "
            "WHERE tenant_id = :t AND site_id = :s AND idempotency_key = :k"),
            {"t": tenant_id, "s": site_id, "k": key}).mappings().one_or_none()

    @staticmethod
    def work_link_pair(c: Connection, tenant_id: UUID, site_id: UUID, case_id: str, scenario_id: str | None,
                       opportunity_id: str | None) -> Any:
        """The existing association of this case with this decision, if any (`UNIQUE(case_id, scenario_id)` and
        `UNIQUE(case_id, opportunity_id)`)."""
        return c.execute(text(
            "SELECT id FROM mini_decision_work_link WHERE tenant_id = :t AND site_id = :s AND case_id = :c "
            "AND (scenario_id = CAST(:sc AS uuid) OR opportunity_id = CAST(:o AS uuid))"),
            {"t": tenant_id, "s": site_id, "c": case_id, "sc": scenario_id, "o": opportunity_id}).scalar()

    @staticmethod
    def visible_cases(c: Connection, tenant_id: UUID, site_id: UUID, case_ids: list[str], known: Any) -> set[str]:
        """The requested W4-01 case IDs that exist at this tenant/Site with `created_at <= known` (W4-01 detail
        visibility)."""
        rows = c.execute(text(
            "SELECT id::text FROM work_case WHERE tenant_id = :t AND site_id = :s "
            "AND id = ANY(CAST(:ids AS uuid[])) AND created_at <= :k"),
            {"t": tenant_id, "s": site_id, "ids": case_ids, "k": known}).scalars()
        return set(rows)

    @staticmethod
    def work_contexts(c: Connection, tenant_id: UUID, site_id: UUID, case_ids: list[str],
                      known: Any) -> list[Mapping[str, Any]]:
        """Every visible association of the named cases at `known`, ordered `(created_at, id)` ascending, with the
        opportunity public number and the scenario public number and head-revision name at `known` (null when no
        revision is visible)."""
        return list(c.execute(text(
            "SELECT l.id, l.case_id::text AS case_id, l.created_at, l.opportunity_id, l.scenario_id, "
            "o.public_no AS opportunity_no, m.public_no AS scenario_no, "
            "(SELECT r.name FROM mini_scenario_revision r WHERE r.tenant_id = m.tenant_id AND r.site_id = m.site_id "
            " AND r.scenario_id = m.id AND m.created_at <= :k AND r.recorded_at <= :k "
            " ORDER BY r.recorded_at DESC, r.revision_no DESC, r.id DESC LIMIT 1) AS scenario_name "
            "FROM mini_decision_work_link l "
            "LEFT JOIN mini_opportunity o ON o.tenant_id = l.tenant_id AND o.site_id = l.site_id "
            " AND o.id = l.opportunity_id "
            "LEFT JOIN mini_scenario m ON m.tenant_id = l.tenant_id AND m.site_id = l.site_id AND m.id = l.scenario_id "
            "WHERE l.tenant_id = :t AND l.site_id = :s AND l.case_id = ANY(CAST(:ids AS uuid[])) "
            "AND l.created_at <= :k ORDER BY l.created_at, l.id"),
            {"t": tenant_id, "s": site_id, "ids": case_ids, "k": known}).mappings())

    @staticmethod
    def sites_by_code(c: Connection, site_code: str) -> list[Any]:
        """`reconcile --site <code>`: `(tenant_id, site_id, timezone)` of the Sites with that public code."""
        return c.execute(text("SELECT tenant_id, id, timezone FROM site WHERE site_code_key = lower(:c)"),
                         {"c": site_code}).all()

    def run(self, work: Callable[[Connection], T]) -> T:
        """Run `work` in one write transaction (convenience for callers holding no connection)."""
        with self.transaction() as c:
            return work(c)
