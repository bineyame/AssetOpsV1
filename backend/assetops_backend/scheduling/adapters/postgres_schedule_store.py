"""The eighth PostgreSQL writer: schedule claims, heads, cursor and enrolment (S4-02d phase 1).

Ratified in `D-2026-10-14-s402d-schedule-storage-and-install-gate`. This module is the sole runtime writer of
`schedule_tick_head`, `schedule_site_head`, `schedule_cursor` and `schedule_enrolment` (migration 0013), and it
writes no other table. Guard rule 8 (`tools/checks/configuration-persistence.ps1`) admits its inserts into those
four tables and its updates of named schedule-state columns only, so every update statement here keeps its whole
assignment list and its condition on one source line, and no upsert is used: a row is created with
`ON CONFLICT DO NOTHING`, then changed by a guarded statement.

Claims are expiring ownership in the head rows: a claim is taken when the row has no token or its lease has
passed, and every later write of that claim names its token, so a holder whose lease expired and was taken over
writes nothing. All instants (claims, leases, heartbeat, retry due) are DB time, `clock_timestamp()`.

Every connection carries `statement_timeout` and `lock_timeout`, so a stalled database cannot hang the tick.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, OperationalError, ProgrammingError


class ScheduleStoreUnavailable(RuntimeError):
    """The schedule state could not be read or written (no URL, connection failure or a server timeout)."""


_CLAIM_COLUMNS = "claim_token, claim_owner, claimed_at, lease_until"
_SITE_HEAD = ("tenant_id, site_id, " + _CLAIM_COLUMNS + ", stage, stage_started_at, selected_count, "
              "last_selected_at, last_completed_at, s3_processed, s3_deferred, mini_processed, mini_deferred, "
              "mini_failed, opportunity_processed, opportunity_deferred, opportunity_failed, consequence_processed, "
              "consequence_deferred, s4_outcome, s4_outcome_at, matched_fence, matched_version, matched_at, "
              "fence_moved_streak, last_failure_stage, last_failure_code, last_failure_detail, last_failed_at, "
              "consecutive_failures, retry_due_at, claim_skips, last_skipped_at, created_at")
_TICK_HEAD = ("environment, " + _CLAIM_COLUMNS + ", last_started_at, last_succeeded_at, last_failed_at, "
              "last_failure_code, last_failure_detail, heartbeat_at, retry_due_at, consecutive_failures, "
              "claim_skips, last_skipped_at, last_sites_selected, last_sites_processed, last_sites_deferred, "
              "last_excluded_with_work, last_reconcile_ms, created_at")


class PostgresScheduleStore:
    def __init__(self, database_url: str | None, *, statement_timeout_ms: int = 30_000,
                 lock_timeout_ms: int = 5_000) -> None:
        self._database_url = database_url
        self._options = f"-c statement_timeout={int(statement_timeout_ms)} -c lock_timeout={int(lock_timeout_ms)}"
        self._engine: Engine | None = None

    def _connect(self) -> Engine:
        if not self._database_url:
            raise ScheduleStoreUnavailable("DATABASE_URL is not set, so the schedule store cannot be reached.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True,
                                         connect_args={"options": self._options})
        return self._engine

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def _run(self, work):
        try:
            with self._connect().begin() as c:
                return work(c)
        except (OperationalError, ProgrammingError) as error:
            raise ScheduleStoreUnavailable(f"The schedule store failed: {error.orig}") from error
        except DBAPIError as error:
            if error.connection_invalidated:
                raise ScheduleStoreUnavailable(str(error.orig)) from error
            raise

    @staticmethod
    def _row(row) -> dict[str, Any] | None:
        return None if row is None else dict(row._mapping)

    # ---- reads ---------------------------------------------------------------------------------------------

    def db_now(self) -> datetime:
        return self._run(lambda c: c.execute(text("SELECT clock_timestamp()")).scalar_one())

    def site_inventory(self) -> list[dict[str, Any]]:
        """Every imported Site of every tenant by stable IDs, with its lifecycle, whether it has registered
        evidence (at least one `accepted_evidence` row; a registered gateway or source alone is not evidence,
        S4-02d N4) and its explicit enrolment. The active-Site predicate is applied by the tick."""
        return self._run(lambda c: [dict(r._mapping) for r in c.execute(text(
            "SELECT s.tenant_id, s.id AS site_id, s.site_code, s.lifecycle, "
            "EXISTS (SELECT 1 FROM accepted_evidence e WHERE e.tenant_id = s.tenant_id AND e.site_id = s.id) "
            "AS has_evidence, coalesce(n.enrolled, false) AS enrolled FROM site s "
            "LEFT JOIN schedule_enrolment n ON n.tenant_id = s.tenant_id AND n.site_id = s.id "
            "WHERE EXISTS (SELECT 1 FROM site_import i WHERE i.tenant_id = s.tenant_id AND i.site_id = s.id) "
            "ORDER BY s.tenant_id, s.id"))])

    def tick_head(self, environment: str) -> dict[str, Any] | None:
        return self._run(lambda c: self._row(c.execute(text(
            "SELECT " + _TICK_HEAD + " FROM schedule_tick_head WHERE environment = :e"),
            {"e": environment}).first()))

    def site_head(self, tenant_id: UUID, site_id: UUID) -> dict[str, Any] | None:
        return self._run(lambda c: self._row(c.execute(text(
            "SELECT " + _SITE_HEAD + " FROM schedule_site_head WHERE tenant_id = :t AND site_id = :s"),
            {"t": tenant_id, "s": site_id}).first()))

    def site_heads(self) -> list[dict[str, Any]]:
        return self._run(lambda c: [dict(r._mapping) for r in c.execute(text(
            "SELECT " + _SITE_HEAD + " FROM schedule_site_head ORDER BY tenant_id, site_id"))])

    def cursor(self, environment: str) -> tuple[UUID, UUID] | None:
        row = self._run(lambda c: c.execute(text(
            "SELECT after_tenant_id, after_site_id FROM schedule_cursor WHERE environment = :e"),
            {"e": environment}).first())
        return None if row is None or row[0] is None else (row[0], row[1])

    # ---- enrolment -----------------------------------------------------------------------------------------

    def enrol(self, tenant_id: UUID, site_id: UUID, enrolled: bool, changed_by: str) -> dict[str, Any]:
        """Explicit enrolment of one Site of its own tenant (the FK refuses a Site of another tenant)."""
        def work(c: Connection) -> dict[str, Any]:
            p = {"t": tenant_id, "s": site_id, "n": bool(enrolled), "b": changed_by}
            c.execute(text(
                "INSERT INTO schedule_enrolment (tenant_id, site_id, enrolled, changed_by, changed_at, created_at) "
                "VALUES (:t, :s, :n, :b, clock_timestamp(), clock_timestamp()) ON CONFLICT DO NOTHING"), p)
            return dict(c.execute(text(
                "UPDATE schedule_enrolment SET enrolled = :n, changed_by = :b, changed_at = clock_timestamp() WHERE tenant_id = :t AND site_id = :s "  # noqa: E501
                "RETURNING tenant_id, site_id, enrolled, changed_by, changed_at"), p).one()._mapping)
        return self._run(work)

    # ---- environment tick ----------------------------------------------------------------------------------

    def claim_tick(self, environment: str, token: UUID, owner: str, lease_seconds: float) -> dict[str, Any]:
        """Take the environment tick claim if free or expired. Returns `claimed` and the head as it now stands;
        a refused claim counts a skip (which never advances the heartbeat)."""
        def work(c: Connection) -> dict[str, Any]:
            p = {"e": environment, "k": token, "o": owner, "l": float(lease_seconds)}
            c.execute(text("INSERT INTO schedule_tick_head (environment, created_at) "
                           "VALUES (:e, clock_timestamp()) ON CONFLICT DO NOTHING"), p)
            row = c.execute(text(
                "UPDATE schedule_tick_head SET claim_token = :k, claim_owner = :o, claimed_at = clock_timestamp(), lease_until = clock_timestamp() + :l * interval '1 second', last_started_at = clock_timestamp() WHERE environment = :e "  # noqa: E501
                "AND (claim_token IS NULL OR lease_until < clock_timestamp()) RETURNING " + _TICK_HEAD), p).first()
            if row is None:
                row = c.execute(text(
                    "UPDATE schedule_tick_head SET claim_skips = claim_skips + 1, last_skipped_at = clock_timestamp() WHERE environment = :e "  # noqa: E501
                    "RETURNING " + _TICK_HEAD), p).one()
                return {"claimed": False, "db_now": c.execute(text("SELECT clock_timestamp()")).scalar_one(),
                        **dict(row._mapping)}
            return {"claimed": True, "db_now": c.execute(text("SELECT clock_timestamp()")).scalar_one(),
                    **dict(row._mapping)}
        return self._run(work)

    def release_tick(self, environment: str, token: UUID) -> bool:
        """Give the claim back without recording success or failure (a tick still inside its retry back-off)."""
        return self._run(lambda c: c.execute(text(
            "UPDATE schedule_tick_head SET claim_token = NULL, claim_owner = NULL, claimed_at = NULL, lease_until = NULL WHERE environment = :e "  # noqa: E501
            "AND claim_token = :k RETURNING environment"), {"e": environment, "k": token}).first() is not None)

    def finish_tick(self, environment: str, token: UUID, *, sites_selected: int, sites_processed: int,
                    sites_deferred: int, excluded_with_work: int, reconcile_ms: int | None) -> bool:
        """A completed tick: release the claim and advance success and heartbeat. False if the claim was lost."""
        p = {"e": environment, "k": token, "sel": sites_selected, "pro": sites_processed, "def": sites_deferred,
             "exc": excluded_with_work, "rms": reconcile_ms}
        return self._run(lambda c: c.execute(text(
            "UPDATE schedule_tick_head SET claim_token = NULL, claim_owner = NULL, claimed_at = NULL, lease_until = NULL, last_succeeded_at = clock_timestamp(), heartbeat_at = clock_timestamp(), consecutive_failures = 0, retry_due_at = NULL, claim_skips = 0, last_sites_selected = :sel, last_sites_processed = :pro, last_sites_deferred = :def, last_excluded_with_work = :exc, last_reconcile_ms = :rms WHERE environment = :e "  # noqa: E501
            "AND claim_token = :k RETURNING environment"), p).first() is not None)

    def fail_tick(self, environment: str, token: UUID, code: str, detail: str, backoff_seconds: float) -> bool:
        """A failed or timed-out tick: release the claim, record the failure and its retry time; no heartbeat."""
        p = {"e": environment, "k": token, "c": code, "d": detail[:2000], "b": float(backoff_seconds)}
        return self._run(lambda c: c.execute(text(
            "UPDATE schedule_tick_head SET claim_token = NULL, claim_owner = NULL, claimed_at = NULL, lease_until = NULL, last_failed_at = clock_timestamp(), last_failure_code = :c, last_failure_detail = :d, consecutive_failures = consecutive_failures + 1, retry_due_at = clock_timestamp() + :b * interval '1 second' WHERE environment = :e "  # noqa: E501
            "AND claim_token = :k RETURNING environment"), p).first() is not None)

    def set_cursor(self, environment: str, tenant_id: UUID, site_id: UUID) -> None:
        def work(c: Connection) -> None:
            p = {"e": environment, "t": tenant_id, "s": site_id}
            c.execute(text("INSERT INTO schedule_cursor (environment, updated_at) "
                           "VALUES (:e, clock_timestamp()) ON CONFLICT DO NOTHING"), p)
            c.execute(text(
                "UPDATE schedule_cursor SET after_tenant_id = :t, after_site_id = :s, updated_at = clock_timestamp() WHERE environment = :e"),  # noqa: E501
                p)
        self._run(work)

    # ---- Site stage claim ----------------------------------------------------------------------------------

    def claim_site(self, tenant_id: UUID, site_id: UUID, token: UUID, owner: str,
                   lease_seconds: float) -> dict[str, Any]:
        """Take one Site's stage claim if free or expired (S3, S4 and the consequence drain of a Site never
        overlap across hosts). Returns `claimed` and the head; a refused claim counts a Site skip."""
        def work(c: Connection) -> dict[str, Any]:
            p = {"t": tenant_id, "s": site_id, "k": token, "o": owner, "l": float(lease_seconds)}
            c.execute(text("INSERT INTO schedule_site_head (tenant_id, site_id, created_at) "
                           "VALUES (:t, :s, clock_timestamp()) ON CONFLICT DO NOTHING"), p)
            row = c.execute(text(
                "UPDATE schedule_site_head SET claim_token = :k, claim_owner = :o, claimed_at = clock_timestamp(), lease_until = clock_timestamp() + :l * interval '1 second', selected_count = selected_count + 1, last_selected_at = clock_timestamp() WHERE tenant_id = :t AND site_id = :s "  # noqa: E501
                "AND (claim_token IS NULL OR lease_until < clock_timestamp()) RETURNING " + _SITE_HEAD), p).first()
            if row is None:
                row = c.execute(text(
                    "UPDATE schedule_site_head SET claim_skips = claim_skips + 1, last_skipped_at = clock_timestamp() WHERE tenant_id = :t AND site_id = :s "  # noqa: E501
                    "RETURNING " + _SITE_HEAD), p).one()
                return {"claimed": False, **dict(row._mapping)}
            return {"claimed": True, **dict(row._mapping)}
        return self._run(work)

    def set_stage(self, tenant_id: UUID, site_id: UUID, token: UUID, stage: str) -> bool:
        return self._run(lambda c: c.execute(text(
            "UPDATE schedule_site_head SET stage = :st, stage_started_at = clock_timestamp() WHERE tenant_id = :t AND site_id = :s "  # noqa: E501
            "AND claim_token = :k RETURNING site_id"),
            {"t": tenant_id, "s": site_id, "k": token, "st": stage}).first() is not None)

    def record_s3(self, tenant_id: UUID, site_id: UUID, token: UUID, processed: int, deferred: int) -> bool:
        return self._run(lambda c: c.execute(text(
            "UPDATE schedule_site_head SET s3_processed = :p, s3_deferred = :d WHERE tenant_id = :t AND site_id = :s "  # noqa: E501
            "AND claim_token = :k RETURNING site_id"),
            {"t": tenant_id, "s": site_id, "k": token, "p": processed, "d": deferred}).first() is not None)

    def record_mini(self, tenant_id: UUID, site_id: UUID, token: UUID, processed: int, deferred: int,
                    failed: int) -> bool:
        """W4-02 q7 ruling 1: the three counts of an `OK` MINI stage, written together under the Site claim."""
        counts = {"p": int(processed), "d": int(deferred), "f": int(failed)}
        if min(counts.values()) < 0:
            raise ValueError("The MINI stage counts are nonnegative.")
        return self._run(lambda c: c.execute(text(
            "UPDATE schedule_site_head SET mini_processed = :p, mini_deferred = :d, mini_failed = :f WHERE tenant_id = :t AND site_id = :s "  # noqa: E501
            "AND claim_token = :k RETURNING site_id"),
            {"t": tenant_id, "s": site_id, "k": token, **counts}).first() is not None)

    def record_opportunity(self, tenant_id: UUID, site_id: UUID, token: UUID, processed: int, deferred: int,
                           failed: int) -> bool:
        """W4-03 u3 unit-4 dry-read: the three counts of an `OK` OPPORTUNITY stage, written together under the
        Site claim (a lost token writes nothing)."""
        counts = {"p": int(processed), "d": int(deferred), "f": int(failed)}
        if min(counts.values()) < 0:
            raise ValueError("The OPPORTUNITY stage counts are nonnegative.")
        return self._run(lambda c: c.execute(text(
            "UPDATE schedule_site_head SET opportunity_processed = :p, opportunity_deferred = :d, opportunity_failed = :f WHERE tenant_id = :t AND site_id = :s "  # noqa: E501
            "AND claim_token = :k RETURNING site_id"),
            {"t": tenant_id, "s": site_id, "k": token, **counts}).first() is not None)

    def record_consequence(self, tenant_id: UUID, site_id: UUID, token: UUID, processed: int,
                           deferred: int) -> bool:
        return self._run(lambda c: c.execute(text(
            "UPDATE schedule_site_head SET consequence_processed = :p, consequence_deferred = :d WHERE tenant_id = :t AND site_id = :s "  # noqa: E501
            "AND claim_token = :k RETURNING site_id"),
            {"t": tenant_id, "s": site_id, "k": token, "p": processed, "d": deferred}).first() is not None)

    def record_s4(self, tenant_id: UUID, site_id: UUID, token: UUID, outcome: str,
                  fence: dict[str, Any] | None = None, version: str | None = None) -> bool:
        """`MATCHED` stores the completed pass's fence and matcher version (the next tick skips S4 while both are
        unchanged); `FENCE_MOVED` grows the streak an alarm reads and `SKIPPED_UNCHANGED_FENCE` clears it; any other
        outcome records only itself."""
        p = {"t": tenant_id, "s": site_id, "k": token, "o": outcome,
             "f": None if fence is None else json.dumps(fence, sort_keys=True), "v": version}
        if outcome == "MATCHED":
            sql = ("UPDATE schedule_site_head SET s4_outcome = :o, s4_outcome_at = clock_timestamp(), matched_fence = CAST(:f AS jsonb), matched_version = :v, matched_at = clock_timestamp(), fence_moved_streak = 0 WHERE tenant_id = :t AND site_id = :s "  # noqa: E501
                   "AND claim_token = :k RETURNING site_id")
        elif outcome == "FENCE_MOVED":
            sql = ("UPDATE schedule_site_head SET s4_outcome = :o, s4_outcome_at = clock_timestamp(), fence_moved_streak = fence_moved_streak + 1 WHERE tenant_id = :t AND site_id = :s "  # noqa: E501
                   "AND claim_token = :k RETURNING site_id")
        elif outcome == "SKIPPED_UNCHANGED_FENCE":
            # Phase 2: the stored fence is current again, so no move is pending; the streak alarm clears.
            sql = ("UPDATE schedule_site_head SET s4_outcome = :o, s4_outcome_at = clock_timestamp(), fence_moved_streak = 0 WHERE tenant_id = :t AND site_id = :s "  # noqa: E501
                   "AND claim_token = :k RETURNING site_id")
        else:
            sql = ("UPDATE schedule_site_head SET s4_outcome = :o, s4_outcome_at = clock_timestamp() WHERE tenant_id = :t AND site_id = :s "  # noqa: E501
                   "AND claim_token = :k RETURNING site_id")
        return self._run(lambda c: c.execute(text(sql), p).first() is not None)

    def release_site(self, tenant_id: UUID, site_id: UUID, token: UUID, *, failure: tuple[str, str, str] | None,
                     backoff_seconds: float = 0) -> bool:
        """End this Site's stage sequence. Without a failure it records completion and clears retry; with
        `(stage, code, detail)` it records the failure and the schedule-level retry time (S3 jobs and consequence
        work keep their own retry; nothing here re-enqueues them)."""
        p = {"t": tenant_id, "s": site_id, "k": token}
        if failure is None:
            sql = ("UPDATE schedule_site_head SET claim_token = NULL, claim_owner = NULL, claimed_at = NULL, lease_until = NULL, stage = 'IDLE', stage_started_at = NULL, last_completed_at = clock_timestamp(), consecutive_failures = 0, retry_due_at = NULL, claim_skips = 0 WHERE tenant_id = :t AND site_id = :s "  # noqa: E501
                   "AND claim_token = :k RETURNING site_id")
        else:
            p.update({"fs": failure[0], "fc": failure[1], "fd": failure[2][:2000], "b": float(backoff_seconds)})
            sql = ("UPDATE schedule_site_head SET claim_token = NULL, claim_owner = NULL, claimed_at = NULL, lease_until = NULL, stage = 'IDLE', stage_started_at = NULL, last_failure_stage = :fs, last_failure_code = :fc, last_failure_detail = :fd, last_failed_at = clock_timestamp(), consecutive_failures = consecutive_failures + 1, retry_due_at = clock_timestamp() + :b * interval '1 second', claim_skips = 0 WHERE tenant_id = :t AND site_id = :s "  # noqa: E501
                   "AND claim_token = :k RETURNING site_id")
        return self._run(lambda c: c.execute(text(sql), p).first() is not None)
