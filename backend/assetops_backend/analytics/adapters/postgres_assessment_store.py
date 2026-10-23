"""PostgreSQL adapter for durable dispatch assessment (S3-01 phase 2, migration 0007).

Reads: accepted evidence (joined to its ACCEPTED disposition so the knowledge
cutoff applies to the server decision time), Foundation revisions and selected
binding sets, tenant- and Site-scoped and selected at the knowledge cutoff.

Writes, all in this module only: `analytic_run`, `analytic_run_evidence`,
`assessment_revision`, `analytic_run_assessment` (append-only), LR-01
`source_clock_attestation` events (append-only, with their affected-window
requeue in the same transaction), and on the S2
`recompute_job` table only the lease/retry fields (`status`, `lease_until`,
`attempts`, `available_at`, `last_error`) plus scheduling inserts/widening
under the same advisory lock the ledger uses to coalesce.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, OperationalError, ProgrammingError

from assetops_contracts.source_envelope_v4 import V4_EV_MAPPING_PROFILE_ID, V4_EV_MAPPING_PROFILE_VERSION

from assetops_backend.analytics import cold, dispatch_v3, ev
from assetops_backend.analytics.assessment_worker import DISPATCH_ROLES, DOMAIN as DISPATCH_DOMAIN, input_basis
from assetops_backend.analytics.dispatch_read import day_window, derive_status
from assetops_backend.analytics.cold_reads import (
    FUTURE_NOTE,
    HISTORICAL_NOTE,
    NO_PROBE_NOTE,
    NO_SELECTION_NOTE,
    NO_SPOILAGE,
    PENDING_NOTE,
    STALE_NOTE,
    ColdPinnedLineageUnavailable,
    ColdReadUnavailable,
    currentness_state,
    decode_cursor,
    encode_cursor,
)
from assetops_backend.analytics.ev_reads import (
    COUNT_KEYS as _EV_COUNT_KEYS,
    HISTORICAL_NOTE as _EV_HISTORICAL_NOTE,
    NO_SELECTION_NOTE as _EV_NO_SELECTION_NOTE,
    PENDING_NOTE as _EV_PENDING_NOTE,
    EvReadRefused,
    EvPinnedLineageUnavailable,
    EvReadUnavailable,
    check_cursor as _ev_check_cursor,
    completeness as _ev_completeness,
    currentness_state as _ev_currentness_state,
    decode_cursor as _ev_decode_cursor,
    encode_cursor as _ev_encode_cursor,
    energy_complete as _ev_energy_complete,
)
from assetops_backend.analytics.assessment_inputs import (
    BRACKET,
    CONTROL_BATTERY_RESERVE,
    CONTROL_MINIMUM_RUNTIME,
    AcceptedReading,
    ControlValue,
    EvidenceQuery,
    EvidenceQueryResult,
    RoleBinding,
    Window,
    sha256_json,
)
from assetops_backend.analytics.clock_attestation import (
    AttestationChange,
    AttestationRefused,
    ClockAttestation,
    effective_as_of,
    next_event,
    validate_change,
)
from assetops_backend.analytics.assessment_ports import (
    AssessmentStoreUnavailable,
    Configuration,
    JobLease,
    LeaseLost,
    PersistedRun,
    RunHead,
    RunOutput,
    WindowSnapshot,
)
from assetops_backend.evidence.source_provenance import (
    AUTHORED_DEMONSTRATION,
    REGISTERED_SIMULATION,
    classify,
    link_of,
)
from assetops_backend.evidence.public_provenance import (
    LinkRowsReads,
    PublicProvenance,
    cold_consequence_row_selection,
    cold_envelope_selection,
    cold_finding_row_selection,
    dual_blocks,
    ev_envelope_selection,
    ev_finding_row_selection,
    ev_withdrawn_finding_row_selection,
    ev_session_row_selection,
)
from assetops_backend.financials.fuel_cost import iso
from assetops_backend.sites.binding_roles import EV_ROLES_1, ROLE_SET_COLD_1, ROLE_SET_EV_1
from assetops_backend.sites.binding_service import v4_mapping_profile

_EVIDENCE = (
    "SELECT e.id, e.envelope_sha256, e.batch_id, e.gateway_id, e.source_id, e.sequence_epoch, e.sequence, "
    "e.role, e.asset_id, e.source_time, e.interval_start, e.interval_end, e.published_at, e.received_at, "
    "d.decided_at, e.quality, e.normalized_value_text, e.normalized_unit, e.foundation_revision_id, "
    "e.binding_set_revision_id, e.binding_revision_id, e.source_mode "
    "FROM accepted_evidence e JOIN ingestion_disposition d ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal "
    "WHERE e.tenant_id = :t AND e.site_id = :s AND d.decision = 'ACCEPTED' AND d.accepted_evidence_id = e.id "
    "AND d.decided_at <= :k AND COALESCE(e.interval_end, e.source_time) >= :lo "
    "AND COALESCE(e.interval_start, e.source_time) < :hi AND (:any_role OR e.role = ANY(:roles)) "
    "ORDER BY e.source_time, e.id"
)
_ATTESTATION_COLUMNS = ("id, attestation_id, version, event_kind, source_id, sequence_epoch, proof_class, authority, "
                        "label, max_utc_error_ms, valid_from, valid_to, recorded_at")
#: Accepted readings of one stream whose measurement interval touches `[lo, hi)` (any decision time: an
#: attestation change can alter the clock basis of everything already accepted).
_STREAM_READINGS = (
    "SELECT COALESCE(e.interval_start, e.source_time), COALESCE(e.interval_end, e.source_time) "
    "FROM accepted_evidence e JOIN ingestion_disposition d ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal "
    "WHERE e.tenant_id = :t AND e.site_id = :s AND e.source_id = :src AND e.sequence_epoch = :ep "
    "AND d.decision = 'ACCEPTED' AND d.accepted_evidence_id = e.id "
    "AND COALESCE(e.interval_start, e.source_time) < :hi AND COALESCE(e.interval_end, e.source_time) >= :lo "
    "ORDER BY 1, 2")
_REVISION_COLUMNS = ("v.id, v.analytic_id, v.model_version, v.assessment_key, v.revision_no, "
                     "v.analytic_run_id, v.window_start, v.window_end, v.claim_level, v.result, v.evidence_ids, "
                     "v.basis_sha256, v.created_at")
_KNOWN = "recorded_at <= :k AND (superseded_at IS NULL OR superseded_at > :k)"
_OVERLAPS = "valid_from < :hi AND (valid_to IS NULL OR valid_to > :lo)"
_COLD_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
#: W2-06: EV job brackets are five-minute UTC-epoch aligned; one EV assessment window spans at most 31 days.
_EV_BRACKET = timedelta(minutes=5)
_EV_MAX_WINDOW = timedelta(days=31)
#: q3 P4: the declared unit each connector/charger policy property must carry (no conversion is guessed).
_EV_UNITS = {"ev-charger-max-power": "kW", "ev-connector-max-power": "kW", "ev-meter-resolution": "kWh",
             "ev-meter-error-bound": "kWh", "ev-clock-error-bound": "s", "ev-status-cadence": "min",
             "ev-meter-cadence": "min"}
#: Q14: the whole-window denominator counts of the stored EV result.
_EV_COUNTS = ("started", "completed", "observed_abort", "incomplete", "contradictory", "orphan",
              "confirmed_delivery", "fault_aborted")
_ASSESS_LOCK = "SELECT pg_advisory_xact_lock(hashtextextended(CAST(:site AS text) || :suffix, 0))"
_JOB_LOCK = "SELECT pg_advisory_xact_lock(hashtextextended(CAST(:site AS text) || ':' || :d, 0))"


#: W4-02 closure 4 S2: the four mini-depth job domains, and the literal predicate every mini lease/settle keeps.
MINI_JOB_DOMAINS = ("mini_renewable", "mini_service", "mini_fuel", "mini_backup")
_MINI_DOMAIN_SQL = "domain IN ('mini_renewable','mini_service','mini_fuel','mini_backup')"


def _attestation(r) -> ClockAttestation:
    return ClockAttestation(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], timedelta(milliseconds=r[9]),
                            r[10], r[11], r[12])


def _attestations(c: Connection, tenant_id: UUID, site_id: UUID,
                  knowledge_at: datetime) -> tuple[ClockAttestation, ...]:
    """The Site's clock attestations effective at `knowledge_at` (latest version recorded by then, not revoked)."""
    rows = c.execute(text(f"SELECT {_ATTESTATION_COLUMNS} FROM source_clock_attestation WHERE tenant_id = :t "
                          "AND site_id = :s AND recorded_at <= :k"),
                     {"t": tenant_id, "s": site_id, "k": knowledge_at}).all()
    return effective_as_of([_attestation(r) for r in rows], knowledge_at)


def requeue_spans(intervals: list[tuple[datetime, datetime]], bracket: timedelta) -> list[Window]:
    """Job windows for readings' measurement intervals. The worker expands a job by the six-hour bracket to every
    UTC-day window whose bracket intersects it, so the job carries the readings' own intervals (never widened
    here). Intervals closer than two brackets merge: no UTC day fits in such a gap without its bracket reaching
    one of the two readings, so merging adds no window the readings would not already queue."""
    spans: list[list[datetime]] = []
    for lo, hi in sorted(intervals):
        hi = max(hi, lo + timedelta(microseconds=1))  # an instant reading: the ledger's own instant window
        if spans and lo - spans[-1][1] <= 2 * bracket:
            spans[-1][1] = max(spans[-1][1], hi)
        else:
            spans.append([lo, hi])
    return [Window(lo, hi) for lo, hi in spans]


def _property(content: dict[str, Any], component_type: str, key: str) -> dict[str, Any] | None:
    for component in content.get("components") or ():
        if component.get("component_type") != component_type:
            continue
        for item in component.get("properties") or ():
            if item.get("property_key") == key:
                return item
    return None


def _minutes(item: dict[str, Any]) -> str | None:
    factor = {"min": Decimal(1), "minutes": Decimal(1), "h": Decimal(60), "s": Decimal(1) / Decimal(60)}
    try:
        value = Decimal(str(item.get("value"))) * factor[str(item.get("unit"))]
    except (KeyError, InvalidOperation):
        return None
    return format(value.normalize(), "f")


# Unfinished jobs always count; a FAILED job counts only until a later DEFAULT selection of the analytic
# covers its window (the reassessment succeeded; the failure is history, not a permanent mark).
_LIVE_JOBS = ("(status IN ('PENDING', 'LEASED') OR (status = 'FAILED' AND NOT EXISTS (SELECT 1 FROM "
              "analytic_run_selection x WHERE x.tenant_id = recompute_job.tenant_id AND x.site_id = "
              "recompute_job.site_id AND x.analytic_id = :a AND x.selected_at > recompute_job.available_at "
              "AND x.window_start < recompute_job.window_end AND x.window_end > recompute_job.window_start)))")

# W4-02 q7 ruling 2: a mini job is live while PENDING or LEASED, and a FAILED one until a later selection of the same
# tenant, Site, domain (without the `mini_` prefix) and an overlapping hour supersedes it.
_LIVE_MINI_JOBS = ("(status IN ('PENDING', 'LEASED') OR (status = 'FAILED' AND NOT EXISTS (SELECT 1 FROM "
                   "mini_depth_selection x WHERE x.tenant_id = recompute_job.tenant_id AND x.site_id = "
                   "recompute_job.site_id AND 'mini_' || x.domain = recompute_job.domain "
                   "AND x.selected_at > recompute_job.available_at "
                   "AND x.window_start < recompute_job.window_end AND x.window_end > recompute_job.window_start)))")


class PostgresAssessmentStore:
    def __init__(self, database_url: str | None, *, link_rows: Callable[..., list] | None = None) -> None:
        self._database_url = database_url
        self._engine: Engine | None = None
        # W2-03: the S4-05 link reader on a caller's connection, injected by the composition root (the cold
        # selection reads its source gate in the same transaction). Absent, cold selection refuses.
        self._link_rows = link_rows
        # W4-03 closure 4 S6: a test-only clock for the opportunity enqueue seam; None in production.
        self.test_clock_override: Callable[[], datetime] | None = None

    def _connect_engine(self) -> Engine:
        if not self._database_url:
            raise AssessmentStoreUnavailable("DATABASE_URL is not set, so the assessment store cannot be reached.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True)
        return self._engine

    def _run(self, work, *, write: bool = False):
        engine = self._connect_engine()
        try:
            if write:
                with engine.begin() as connection:
                    return work(connection)
            with engine.connect() as connection:
                return work(connection)
        except (OperationalError, ProgrammingError) as error:
            raise AssessmentStoreUnavailable(f"The assessment store failed: {error.orig}") from error
        except DBAPIError as error:
            if error.connection_invalidated:
                raise AssessmentStoreUnavailable(str(error.orig)) from error
            raise

    # --- reads: the typed seam ------------------------------------------------

    def query_evidence(self, query: EvidenceQuery) -> EvidenceQueryResult:
        rng = query.read_range

        def work(c: Connection) -> EvidenceQueryResult:
            rows = c.execute(text(_EVIDENCE), {
                "t": query.tenant_id, "s": query.site_id, "k": query.knowledge_at, "lo": rng.start, "hi": rng.end,
                "any_role": not query.roles, "roles": list(query.roles),
            }).all()
            readings = tuple(AcceptedReading(
                evidence_id=r[0], envelope_sha256=r[1], batch_id=r[2], gateway_id=r[3], source_id=r[4],
                sequence_epoch=r[5], sequence=r[6], role=r[7], asset_id=r[8], source_time=r[9],
                interval_start=r[10], interval_end=r[11], published_at=r[12], received_at=r[13], accepted_at=r[14],
                quality=r[15], value=r[16], unit=r[17], foundation_revision_id=r[18],
                binding_set_revision_id=r[19], binding_revision_id=r[20], source_mode=r[21]) for r in rows)
            config = self._configuration(c, query.tenant_id, query.site_id, rng, query.knowledge_at)
            return EvidenceQueryResult(query, readings, config.bindings, config.controls, config.role_sets,
                                       config.limits,
                                       _attestations(c, query.tenant_id, query.site_id, query.knowledge_at))

        return self._run(work)

    def configuration(self, tenant_id: UUID, site_id: UUID, read_range: Window,
                      knowledge_at: datetime) -> Configuration:
        return self._run(lambda c: self._configuration(c, tenant_id, site_id, read_range, knowledge_at))

    def _configuration(self, c: Connection, tenant_id: UUID, site_id: UUID, rng: Window,
                       k: datetime) -> Configuration:
        params = {"t": tenant_id, "s": site_id, "k": k, "lo": rng.start, "hi": rng.end}
        limits: list[str] = []
        foundations = c.execute(text(
            f"SELECT id, version, valid_from, valid_to, content FROM foundation_revision "
            f"WHERE tenant_id = :t AND site_id = :s AND {_KNOWN} AND {_OVERLAPS} ORDER BY valid_from"), params).all()
        controls: list[ControlValue] = []
        for rev_id, version, valid_from, valid_to, content in foundations:
            content = content if isinstance(content, dict) else json.loads(content)
            reserve = _property(content, "BATTERY", "reserve-state-of-charge")
            if reserve is not None and reserve.get("value") is not None:
                controls.append(ControlValue(CONTROL_BATTERY_RESERVE, format(Decimal(str(reserve["value"])), "f"),
                                             str(reserve.get("unit") or "%"), valid_from, valid_to, rev_id,
                                             f"{reserve.get('source')} v{reserve.get('source_version')}"))
            else:
                limits.append(f"Foundation v{version} has no battery reserve control")
            runtime = _property(content, "GENERATOR", "minimum-runtime")
            if runtime is not None:
                minutes = _minutes(runtime)
                if minutes is None:
                    limits.append(f"Foundation v{version} minimum-runtime unit {runtime.get('unit')!r} not mapped")
                else:
                    controls.append(ControlValue(CONTROL_MINIMUM_RUNTIME, minutes, "min", valid_from, valid_to,
                                                 rev_id, f"{runtime.get('source')} v{runtime.get('source_version')}"))
        ordered = sorted(foundations, key=lambda r: r[2])
        for a, b in zip(ordered, ordered[1:]):
            if a[3] is None or a[3] > b[2]:
                limits.append(f"Foundation v{a[1]} and v{b[1]} overlap at the cutoff")
        sets = c.execute(text(
            f"SELECT id, role_set, valid_from, valid_to FROM signal_binding_set_revision "
            f"WHERE tenant_id = :t AND site_id = :s AND {_KNOWN} AND {_OVERLAPS}"), params).all()
        bindings: list[RoleBinding] = []
        for set_id, role_set, set_from, set_to in sets:
            for b in c.execute(text(
                    "SELECT id, role, asset_id, valid_from, valid_to FROM signal_binding_revision "
                    "WHERE tenant_id = :t AND site_id = :s AND binding_set_revision_id = :b"),
                    {**params, "b": set_id}).all():
                start = max(set_from, b[3])
                ends = [x for x in (set_to, b[4]) if x is not None]
                bindings.append(RoleBinding(b[1], b[2], start, min(ends) if ends else None, set_id, b[0], role_set))
        return Configuration(tuple(bindings), tuple(controls), tuple(sorted({s[1] for s in sets})), tuple(limits))

    # --- jobs -------------------------------------------------------------------

    def lease_job(self, domain: str, now: datetime, lease: timedelta, *,
                  max_attempts: int = 3, tenant_id: UUID | None = None,
                  site_id: UUID | None = None) -> JobLease | None:
        """Lease the oldest due job of `domain`; with `tenant_id` and `site_id`, only that Site's jobs (S4-02d:
        the schedule leases per Site, which the global FIFO cannot make fair). Both the expire-to-FAILED step and
        the lease are scoped the same way."""
        if domain in MINI_JOB_DOMAINS:
            raise ValueError("Mini-depth jobs are leased only by lease_mini_job (W4-02 closure 4 S2).")
        if domain == "mini_opportunity":
            raise ValueError("Opportunity jobs are leased only by lease_opportunity_job (W4-03 closure 4 S2).")
        if (tenant_id is None) != (site_id is None):
            raise ValueError("A Site-scoped lease names both the tenant and the Site.")
        scope = "" if site_id is None else " AND tenant_id = :t AND site_id = :s"
        scoped = {} if site_id is None else {"t": tenant_id, "s": site_id}

        def work(c: Connection) -> JobLease | None:
            # A lease that expired on its last allowed attempt (the worker crashed or always outlives
            # its lease) is FAILED with a reason instead of being re-leased forever (phase-2 F6).
            c.execute(text(
                "UPDATE recompute_job SET status = 'FAILED', lease_until = NULL, last_error = "
                "'lease expired on attempt ' || attempts || ' of ' || CAST(:max AS integer) || "
                "' without completing' WHERE domain = :d AND status = 'LEASED' AND lease_until < :now "
                "AND attempts >= :max" + scope), {"d": domain, "now": now, "max": max_attempts, **scoped})
            row = c.execute(text(
                "UPDATE recompute_job SET status = 'LEASED', lease_until = :until, attempts = attempts + 1 "
                "WHERE id = (SELECT id FROM recompute_job WHERE domain = :d AND ((status = 'PENDING' AND "
                "available_at <= :now) OR (status = 'LEASED' AND lease_until < :now))" + scope +
                " ORDER BY available_at, created_at LIMIT 1 FOR UPDATE SKIP LOCKED) "
                "RETURNING id, tenant_id, site_id, domain, window_start, window_end, attempts"),
                {"d": domain, "now": now, "until": now + lease, **scoped}).first()
            if row is None:
                return None
            return JobLease(row[0], row[1], row[2], row[3], Window(row[4], row[5]), row[6], now)

        return self._run(work, write=True)

    # --- mini-depth jobs (W4-02 closure 4 S2) ------------------------------------------------------------------
    # The mini worker issues no recompute_job SQL: it leases, settles and fails through these methods. Every
    # statement keeps the literal four-domain predicate, and settle/fail also the job's id, tenant and Site, so a
    # Dispatch, cold or EV job can never be leased, settled or failed here.

    def lease_mini_job(self, lease: timedelta, *, max_attempts: int = 3, tenant_id: UUID | None = None,
                       site_id: UUID | None = None, now: datetime | None = None) -> JobLease | None:
        """Lease the oldest due mini-depth job of any of the four domains, optionally of one Site. The instant is
        the database `clock_timestamp()` unless a test passes `now`; it is the returned lease's knowledge cutoff."""
        if (tenant_id is None) != (site_id is None):
            raise ValueError("A Site-scoped lease names both the tenant and the Site.")
        scope = "" if site_id is None else " AND tenant_id = :t AND site_id = :s"
        scoped = {} if site_id is None else {"t": tenant_id, "s": site_id}

        def work(c: Connection) -> JobLease | None:
            at = now if now is not None else c.execute(text("SELECT clock_timestamp()")).scalar_one()
            c.execute(text(
                "UPDATE recompute_job SET status = 'FAILED', lease_until = NULL, last_error = "
                "'lease expired on attempt ' || attempts || ' of ' || CAST(:max AS integer) || "
                "' without completing' WHERE " + _MINI_DOMAIN_SQL + " AND status = 'LEASED' AND lease_until < :now "
                "AND attempts >= :max" + scope), {"now": at, "max": max_attempts, **scoped})
            row = c.execute(text(
                "UPDATE recompute_job SET status = 'LEASED', lease_until = :until, attempts = attempts + 1 "
                "WHERE " + _MINI_DOMAIN_SQL + " AND id = (SELECT id FROM recompute_job WHERE " + _MINI_DOMAIN_SQL +
                " AND ((status = 'PENDING' AND available_at <= :now) OR (status = 'LEASED' AND lease_until < :now))"
                + scope + " ORDER BY available_at, created_at LIMIT 1 FOR UPDATE SKIP LOCKED) "
                "RETURNING id, tenant_id, site_id, domain, window_start, window_end, attempts"),
                {"now": at, "until": at + lease, **scoped}).first()
            if row is None:
                return None
            return JobLease(row[0], row[1], row[2], row[3], Window(row[4], row[5]), row[6], at)

        return self._run(work, write=True)

    @staticmethod
    def _mini_still_mine(c: Connection, lease: JobLease) -> None:
        row = c.execute(text(
            "SELECT status, attempts FROM recompute_job WHERE id = :id AND tenant_id = :t AND site_id = :s AND "
            + _MINI_DOMAIN_SQL + " FOR UPDATE"), {"id": lease.job_id, "t": lease.tenant_id, "s": lease.site_id}).first()
        if row is None or row[0] != "LEASED" or row[1] != lease.attempts:
            raise LeaseLost(f"mini job {lease.job_id} is {row[0] if row else 'missing'} (attempt "
                            f"{row[1] if row else '-'}), not our attempt {lease.attempts}")

    def settle_mini_job(self, connection: Connection, lease: JobLease) -> None:
        """Mark a still-held mini job DONE on the worker's own connection, so the revision, its selection and DONE
        commit together; it neither begins nor commits. Raises `LeaseLost` (the caller rolls back) otherwise."""
        self._mini_still_mine(connection, lease)
        connection.execute(text(
            "UPDATE recompute_job SET status = 'DONE', lease_until = NULL, last_error = NULL "
            "WHERE id = :id AND tenant_id = :t AND site_id = :s AND " + _MINI_DOMAIN_SQL + " AND status = 'LEASED' "
            "AND attempts = :a"), {"id": lease.job_id, "t": lease.tenant_id, "s": lease.site_id, "a": lease.attempts})

    def fail_mini_job(self, lease: JobLease, error: str, *, max_attempts: int, backoff: timedelta,
                      now: datetime | None = None) -> str:
        """In its own transaction (the worker's was rolled back): back to PENDING after `backoff x attempts`, or
        FAILED on the last allowed attempt. Returns RETRY, FAILED or LEASE_LOST."""
        def work(c: Connection) -> str:
            self._mini_still_mine(c, lease)
            at = now if now is not None else c.execute(text("SELECT clock_timestamp()")).scalar_one()
            final = lease.attempts >= max_attempts
            c.execute(text(
                "UPDATE recompute_job SET status = :st, lease_until = NULL, available_at = :at, last_error = :e "
                "WHERE id = :id AND tenant_id = :t AND site_id = :s AND " + _MINI_DOMAIN_SQL +
                " AND status = 'LEASED' AND attempts = :a"),
                {"st": "FAILED" if final else "PENDING", "at": at if final else at + backoff * lease.attempts,
                 "e": error, "id": lease.job_id, "t": lease.tenant_id, "s": lease.site_id, "a": lease.attempts})
            return "FAILED" if final else "RETRY"

        try:
            return self._run(work, write=True)
        except LeaseLost:
            return "LEASE_LOST"

    # --- opportunity jobs (W4-03 closure 4 S2, closure 2 Q4) ---------------------------------------------------
    # The opportunity worker issues no recompute_job SQL: it enqueues, leases, settles and fails through these
    # methods. Every statement keeps the literal `domain = 'mini_opportunity'`, so no other domain's job is touched.

    def enqueue_opportunity_job(self, tenant_id: UUID, site_id: UUID, first_day: date, last_day: date,
                                window: Window) -> tuple[str, UUID]:
        """Queue one five-day study in one transaction (closure 2 Q4): take the study-key advisory lock, lock a
        matching PENDING job and advance its `available_at` with `greatest(available_at, :at)`, or insert a new
        PENDING job with `cause_evidence_id = NULL`. LEASED/DONE/FAILED jobs are never made PENDING. `:at` is one
        DB `clock_timestamp()` unless a test sets `test_clock_override`. Returns `(COALESCED|INSERTED, job id)`."""
        if not (first_day <= last_day and window.start < window.end):
            raise ValueError("An opportunity study needs first_day <= last_day and a nonempty window.")
        key = {"tenant_id": tenant_id, "site_id": site_id, "first_day": first_day, "last_day": last_day}

        def work(c: Connection) -> tuple[str, UUID]:
            override = self.test_clock_override
            at = override() if override is not None else c.execute(text("SELECT clock_timestamp()")).scalar_one()
            c.execute(text(
                "SELECT pg_advisory_xact_lock(hashtextextended(CAST(:tenant_id AS text) || ':' || "
                "CAST(:site_id AS text) || ':mini_opportunity:' || CAST(:first_day AS text) || ':' || "
                "CAST(:last_day AS text), 0))"), key)
            pending = c.execute(text(
                "SELECT id FROM recompute_job WHERE tenant_id = :t AND site_id = :s AND domain = 'mini_opportunity' "
                "AND window_start = :lo AND window_end = :hi AND status = 'PENDING' ORDER BY id LIMIT 1 FOR UPDATE"),
                {"t": tenant_id, "s": site_id, "lo": window.start, "hi": window.end}).scalar()
            if pending is not None:
                c.execute(text(
                    "UPDATE recompute_job SET available_at = greatest(available_at, :at) WHERE id = :pending_id "
                    "AND domain = 'mini_opportunity' AND status = 'PENDING'"), {"at": at, "pending_id": pending})
                return "COALESCED", pending
            job_id = uuid4()
            c.execute(text(
                "INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, "
                "cause_evidence_id, status, available_at, created_at) VALUES (:id, :t, :s, 'mini_opportunity', "
                ":lo, :hi, NULL, 'PENDING', :at, :at)"),
                {"id": job_id, "t": tenant_id, "s": site_id, "lo": window.start, "hi": window.end, "at": at})
            return "INSERTED", job_id

        return self._run(work, write=True)

    def lease_opportunity_job(self, lease: timedelta, *, max_attempts: int = 3, tenant_id: UUID | None = None,
                              site_id: UUID | None = None, now: datetime | None = None) -> JobLease | None:
        """Lease the oldest due `mini_opportunity` job, optionally of one Site, by the `lease_mini_job` rules (an
        expired last attempt goes FAILED first). The instant is DB time unless a test passes `now`."""
        if (tenant_id is None) != (site_id is None):
            raise ValueError("A Site-scoped lease names both the tenant and the Site.")
        scope = "" if site_id is None else " AND tenant_id = :t AND site_id = :s"
        scoped = {} if site_id is None else {"t": tenant_id, "s": site_id}

        def work(c: Connection) -> JobLease | None:
            at = now if now is not None else c.execute(text("SELECT clock_timestamp()")).scalar_one()
            c.execute(text(
                "UPDATE recompute_job SET status = 'FAILED', lease_until = NULL, last_error = "
                "'lease expired on attempt ' || attempts || ' of ' || CAST(:max AS integer) || "
                "' without completing' WHERE domain = 'mini_opportunity' AND status = 'LEASED' "
                "AND lease_until < :now AND attempts >= :max" + scope), {"now": at, "max": max_attempts, **scoped})
            row = c.execute(text(
                "UPDATE recompute_job SET status = 'LEASED', lease_until = :until, attempts = attempts + 1 "
                "WHERE domain = 'mini_opportunity' AND id = (SELECT id FROM recompute_job WHERE "
                "domain = 'mini_opportunity' AND ((status = 'PENDING' AND available_at <= :now) OR "
                "(status = 'LEASED' AND lease_until < :now))" + scope + " ORDER BY available_at, created_at "
                "LIMIT 1 FOR UPDATE SKIP LOCKED) "
                "RETURNING id, tenant_id, site_id, domain, window_start, window_end, attempts"),
                {"now": at, "until": at + lease, **scoped}).first()
            if row is None:
                return None
            return JobLease(row[0], row[1], row[2], row[3], Window(row[4], row[5]), row[6], at)

        return self._run(work, write=True)

    @staticmethod
    def _opportunity_still_mine(c: Connection, lease: JobLease) -> None:
        row = c.execute(text(
            "SELECT status, attempts FROM recompute_job WHERE id = :id AND tenant_id = :t AND site_id = :s AND "
            "domain = 'mini_opportunity' FOR UPDATE"),
            {"id": lease.job_id, "t": lease.tenant_id, "s": lease.site_id}).first()
        if row is None or row[0] != "LEASED" or row[1] != lease.attempts:
            raise LeaseLost(f"opportunity job {lease.job_id} is {row[0] if row else 'missing'} (attempt "
                            f"{row[1] if row else '-'}), not our attempt {lease.attempts}")

    def settle_opportunity_job(self, connection: Connection, lease: JobLease) -> None:
        """Mark a still-held opportunity job DONE on the worker's own connection, so the projection and DONE commit
        together; it neither begins nor commits. Raises `LeaseLost` (the caller rolls back) otherwise."""
        self._opportunity_still_mine(connection, lease)
        connection.execute(text(
            "UPDATE recompute_job SET status = 'DONE', lease_until = NULL, last_error = NULL "
            "WHERE id = :id AND tenant_id = :t AND site_id = :s AND domain = 'mini_opportunity' "
            "AND status = 'LEASED' AND attempts = :a"),
            {"id": lease.job_id, "t": lease.tenant_id, "s": lease.site_id, "a": lease.attempts})

    def fail_opportunity_job(self, lease: JobLease, error: str, *, max_attempts: int, backoff: timedelta,
                             now: datetime | None = None) -> str:
        """In its own transaction: back to PENDING after `backoff x attempts`, or FAILED on the last allowed
        attempt. Returns RETRY, FAILED or LEASE_LOST."""
        def work(c: Connection) -> str:
            self._opportunity_still_mine(c, lease)
            at = now if now is not None else c.execute(text("SELECT clock_timestamp()")).scalar_one()
            final = lease.attempts >= max_attempts
            c.execute(text(
                "UPDATE recompute_job SET status = :st, lease_until = NULL, available_at = :at, last_error = :e "
                "WHERE id = :id AND tenant_id = :t AND site_id = :s AND domain = 'mini_opportunity' "
                "AND status = 'LEASED' AND attempts = :a"),
                {"st": "FAILED" if final else "PENDING", "at": at if final else at + backoff * lease.attempts,
                 "e": error, "id": lease.job_id, "t": lease.tenant_id, "s": lease.site_id, "a": lease.attempts})
            return "FAILED" if final else "RETRY"

        try:
            return self._run(work, write=True)
        except LeaseLost:
            return "LEASE_LOST"

    def live_opportunity_jobs(self, tenant_id: UUID | None = None,
                              site_id: UUID | None = None) -> list[dict[str, Any]]:
        """PENDING or LEASED `mini_opportunity` jobs of every Site, or of one Site; FAILED stays diagnostic (u3
        unit-4 dry-read)."""
        if (tenant_id is None) != (site_id is None):
            raise ValueError("A Site-scoped read names both the tenant and the Site.")
        scope = "" if site_id is None else " AND tenant_id = :t AND site_id = :s"
        return self._run(lambda c: [dict(r._mapping) for r in c.execute(text(
            "SELECT id, tenant_id, site_id, domain, status, window_start, window_end, attempts, available_at, "
            "lease_until, last_error, created_at FROM recompute_job WHERE domain = 'mini_opportunity' "
            "AND status IN ('PENDING', 'LEASED')" + scope + " ORDER BY tenant_id, site_id, available_at, created_at"),
            {"t": tenant_id, "s": site_id})])

    def _still_mine(self, c: Connection, lease: JobLease) -> None:
        row = c.execute(text("SELECT status, attempts FROM recompute_job WHERE id = :id FOR UPDATE"),
                        {"id": lease.job_id}).first()
        if row is None or row[0] != "LEASED" or row[1] != lease.attempts:
            raise LeaseLost(f"job {lease.job_id} is {row[0] if row else 'missing'} (attempt "
                            f"{row[1] if row else '-'}), not our attempt {lease.attempts}")

    def complete_job(self, lease: JobLease, outputs: list[RunOutput], now: datetime) -> list[PersistedRun]:
        def work(c: Connection) -> list[PersistedRun]:
            self._still_mine(c, lease)
            runs = [self._persist(c, out, lease.job_id, now) for out in outputs]
            c.execute(text("UPDATE recompute_job SET status = 'DONE', lease_until = NULL, last_error = NULL "
                           "WHERE id = :id"), {"id": lease.job_id})
            return runs

        return self._run(work, write=True)

    def fail_job(self, lease: JobLease, error: str, now: datetime, *, max_attempts: int,
                 backoff: timedelta) -> str:
        def work(c: Connection) -> str:
            self._still_mine(c, lease)
            final = lease.attempts >= max_attempts
            c.execute(text(
                "UPDATE recompute_job SET status = :st, lease_until = NULL, available_at = :at, last_error = :e "
                "WHERE id = :id"),
                # A FAILED job keeps its failure instant in available_at (never reused): a later DEFAULT
                # selection covering its window supersedes it (_LIVE_JOBS).
                {"st": "FAILED" if final else "PENDING", "at": now if final else now + backoff * lease.attempts,
                 "e": error,
                 "id": lease.job_id})
            return "FAILED" if final else "RETRY"

        try:
            return self._run(work, write=True)
        except LeaseLost:
            return "LEASE_LOST"

    def record_runs(self, outputs: list[RunOutput], now: datetime) -> list[PersistedRun]:
        return self._run(lambda c: [self._persist(c, out, None, now) for out in outputs], write=True)

    def enqueue(self, tenant_id: UUID, site_id: UUID, domain: str, window: Window, now: datetime) -> None:
        self._run(lambda c: self._enqueue(c, tenant_id, site_id, domain, window, now), write=True)

    @staticmethod
    def _enqueue(c: Connection, tenant_id: UUID, site_id: UUID, domain: str, window: Window,
                 now: datetime) -> None:
        c.execute(text(_JOB_LOCK), {"site": site_id, "d": domain})
        job = c.execute(text(
            "SELECT id, window_start, window_end FROM recompute_job WHERE site_id = :site AND domain = :d "
            "AND status = 'PENDING' AND window_start <= :end AND window_end >= :start "
            "ORDER BY window_start LIMIT 1 FOR UPDATE"),
            {"site": site_id, "d": domain, "start": window.start, "end": window.end}).first()
        if job is None:
            c.execute(text(
                "INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, "
                "cause_evidence_id, status, available_at, created_at) "
                "VALUES (:id, :t, :site, :d, :start, :end, NULL, 'PENDING', :now, :now)"),
                {"id": uuid4(), "t": tenant_id, "site": site_id, "d": domain, "start": window.start,
                 "end": window.end, "now": now})
            return
        c.execute(text("UPDATE recompute_job SET window_start = :start, window_end = :end WHERE id = :id"),
                  {"start": min(window.start, job[1]), "end": max(window.end, job[2]), "id": job[0]})

    # --- clock attestations (LR-01) ------------------------------------------------

    def site_scope(self, tenant_slug: str, site_code: str) -> tuple[str, UUID, UUID] | None:
        """(site_code, tenant_id, site_id) of an imported Site inside the named tenant, else None."""
        return self._run(lambda c: (lambda row: None if row is None else (row[0], row[1], row[2]))(c.execute(text(
            "SELECT s.site_code, s.tenant_id, s.id FROM site s JOIN tenant t ON t.id = s.tenant_id "
            "WHERE t.slug = :slug AND s.site_code_key = lower(:code)"), {"slug": tenant_slug, "code": site_code}
        ).first()))

    def clock_attestation_events(self, tenant_id: UUID, site_id: UUID) -> list[ClockAttestation]:
        return self._run(lambda c: [_attestation(r) for r in c.execute(text(
            f"SELECT {_ATTESTATION_COLUMNS} FROM source_clock_attestation WHERE tenant_id = :t AND site_id = :s "
            "ORDER BY recorded_at, attestation_id, version"), {"t": tenant_id, "s": site_id}).all()])

    def record_clock_attestation(self, tenant_id: UUID, site_id: UUID, change: AttestationChange, principal,
                                 now: datetime, *, domain: str = "dispatch",
                                 bracket: timedelta = BRACKET) -> dict[str, Any]:
        """Append one attestation event for the SYSTEM attester and, in the same transaction, requeue every
        accepted reading of the stream whose measurement interval touches the old or the new validity (creation,
        replacement, expiry and revocation alike). A retry with the same idempotency key and request answers the
        stored event and queues nothing; the same key with another request is a conflict."""
        validate_change(change, principal)
        request_sha = sha256_json({k: (None if v is None else str(v)) for k, v in asdict(change).items()})

        def work(c: Connection) -> dict[str, Any]:
            c.execute(text(_ASSESS_LOCK), {"site": site_id, "suffix": ":clock-attestation"})
            held = c.execute(text(
                f"SELECT {_ATTESTATION_COLUMNS}, request_sha256 FROM source_clock_attestation WHERE tenant_id = :t "
                "AND site_id = :s AND idempotency_key = :key"),
                {"t": tenant_id, "s": site_id, "key": change.idempotency_key}).first()
            if held is not None:
                if held[13] != request_sha:
                    raise AttestationRefused(409, "IDEMPOTENCY_CONFLICT", "This idempotency key already recorded "
                                             "another attestation request.")
                return {"event": _attestation(held), "created": False, "requeued": []}
            site = c.execute(text("SELECT proposed_source_mode FROM site WHERE tenant_id = :t AND id = :s"),
                             {"t": tenant_id, "s": site_id}).first()
            if site is None:
                raise AttestationRefused(404, "SITE_NOT_FOUND", "No such Site in this tenant.")
            if site[0] != "SIMULATED":
                raise AttestationRefused(403, "SIMULATED_PROOF_FOR_LIVE_SITE", "A simulated attestation cannot "
                                         "prove a real source's clock; this Site is not simulated.")
            if c.execute(text("SELECT 1 FROM source WHERE id = :src AND tenant_id = :t AND site_id = :s"),
                         {"src": change.source_id, "t": tenant_id, "s": site_id}).first() is None:
                raise AttestationRefused(404, "SOURCE_NOT_IN_SITE", "The source is not registered on this Site.")
            prior = None
            if change.attestation_id is not None:
                row = c.execute(text(
                    f"SELECT {_ATTESTATION_COLUMNS} FROM source_clock_attestation WHERE attestation_id = :a "
                    "AND tenant_id = :t AND site_id = :s ORDER BY version DESC LIMIT 1"),
                    {"a": change.attestation_id, "t": tenant_id, "s": site_id}).first()
                prior = None if row is None else _attestation(row)
            event = next_event(change, prior, event_id=uuid4(), attestation_id=uuid4(), recorded_at=now)
            c.execute(text(
                "INSERT INTO source_clock_attestation (id, attestation_id, version, tenant_id, site_id, source_id, "
                "sequence_epoch, event_kind, proof_class, authority, label, max_utc_error_ms, valid_from, valid_to, "
                "reason, recorded_at, recorded_by, authorization_basis, channel, idempotency_key, request_sha256) "
                "VALUES (:id, :a, :v, :t, :s, :src, :ep, :kind, :proof, :auth, :label, :err, :vf, :vt, :reason, "
                ":now, :by, :basis, :channel, :key, :sha)"),
                {"id": event.event_id, "a": event.attestation_id, "v": event.version, "t": tenant_id, "s": site_id,
                 "src": event.source_id, "ep": event.sequence_epoch, "kind": event.event_kind,
                 "proof": event.proof_class, "auth": event.authority, "label": event.label,
                 "err": int(event.max_utc_error / timedelta(milliseconds=1)), "vf": event.valid_from,
                 "vt": event.valid_to, "reason": change.reason, "now": now, "by": principal.actor_id,
                 "basis": principal.authorization_basis, "channel": change.channel, "key": change.idempotency_key,
                 "sha": request_sha})
            intervals: set[tuple[datetime, datetime]] = set()
            for lo, hi in {(a.valid_from, a.valid_to) for a in (prior, event) if a is not None}:
                intervals.update((r[0], r[1]) for r in c.execute(text(_STREAM_READINGS), {
                    "t": tenant_id, "s": site_id, "src": event.source_id, "ep": event.sequence_epoch,
                    "lo": lo, "hi": hi}).all())
            spans = requeue_spans(sorted(intervals), bracket)
            for span in spans:
                self._enqueue(c, tenant_id, site_id, domain, span, now)
            return {"event": event, "created": True, "requeued": spans}

        return self._run(work, write=True)

    # --- runs and revisions -------------------------------------------------------

    def _persist(self, c: Connection, out: RunOutput, job_id: UUID | None, now: datetime) -> PersistedRun:
        i = out.inputs
        c.execute(text(_ASSESS_LOCK), {"site": i.site_id, "suffix": ":dispatch-assessment"})
        existing = c.execute(text(
            "SELECT id FROM analytic_run WHERE site_id = :s AND analytic_id = :a AND model_version = :m "
            "AND window_start = :ws AND window_end = :we AND input_sha256 = :h"),
            {"s": i.site_id, "a": i.analytic_id, "m": i.model_version, "ws": i.window.start, "we": i.window.end,
             "h": i.input_sha256}).first()
        tenant = c.execute(text("SELECT tenant_id FROM site WHERE id = :s"), {"s": i.site_id}).scalar_one()
        if existing is not None:
            linked = c.execute(text("SELECT assessment_revision_id FROM analytic_run_assessment WHERE run_id = :r"),
                               {"r": existing[0]}).scalars().all()
            self._select(c, out, tenant, existing[0], job_id, now)
            return PersistedRun(existing[0], False, tuple(linked), ())
        run_id = uuid4()
        c.execute(text(
            "INSERT INTO analytic_run (id, tenant_id, site_id, analytic_id, model_version, window_start, window_end, "
            "knowledge_cutoff, input_sha256, cohort_status, cohort_sha256, cohort, configuration_sha256, "
            "foundation_revision_ids, binding_set_revision_ids, role_coverage, watermarks, selection, job_id, "
            "status, started_at, completed_at) VALUES (:id, :t, :s, :a, :m, :ws, :we, :k, :h, :cs, :ch, "
            "CAST(:cohort AS jsonb), :cfg, CAST(:fr AS jsonb), CAST(:br AS jsonb), CAST(:cov AS jsonb), "
            "CAST(:wm AS jsonb), :sel, :job, 'COMPLETED', :started, :now)"),
            {"id": run_id, "t": tenant, "s": i.site_id, "a": i.analytic_id, "m": i.model_version,
             "ws": i.window.start, "we": i.window.end, "k": i.knowledge_at, "h": i.input_sha256,
             "cs": i.cohort.status, "ch": i.cohort.identity(), "cohort": json.dumps(i.cohort.payload()),
             "cfg": out.configuration_sha256, "fr": json.dumps(list(i.foundation_revision_ids)),
             "br": json.dumps(list(i.binding_set_revision_ids)), "cov": json.dumps(i.role_coverage),
             "wm": json.dumps(out.watermarks), "sel": out.selection, "job": job_id, "started": out.started_at,
             "now": now})
        if i.readings:
            c.execute(text("INSERT INTO analytic_run_evidence (run_id, evidence_id, tenant_id, site_id) "
                           "VALUES (:r, :e, :t, :s)"),
                      [{"r": run_id, "e": r.evidence_id, "t": tenant, "s": i.site_id} for r in i.readings])
        revision_ids, new_ids = [], []
        a = out.assessment
        items = [("WINDOW", a.assessment_key, a.claim_level, a.result, (), a.basis_sha256)]
        items += [("INTERVAL", x.assessment_key, x.claim_level, x.result, x.evidence_ids, x.basis_sha256)
                  for x in a.intervals]
        for scope, key, claim, result, evidence, basis in items:
            latest = c.execute(text(
                "SELECT id, revision_no, basis_sha256 FROM assessment_revision WHERE site_id = :s "
                "AND analytic_id = :a AND assessment_key = :key ORDER BY revision_no DESC LIMIT 1"),
                {"s": i.site_id, "a": i.analytic_id, "key": key}).first()
            if latest is not None and latest[2] == basis:
                rev_id = latest[0]
            else:
                rev_id = uuid4()
                c.execute(text(
                    "INSERT INTO assessment_revision (id, tenant_id, site_id, analytic_id, model_version, "
                    "assessment_key, revision_no, analytic_run_id, window_start, window_end, claim_level, result, "
                    "evidence_ids, basis_sha256, created_at) VALUES (:id, :t, :s, :a, :m, :key, :no, :run, :ws, "
                    ":we, :claim, CAST(:result AS jsonb), CAST(:ev AS jsonb), :basis, :now)"),
                    {"id": rev_id, "t": tenant, "s": i.site_id, "a": i.analytic_id, "m": i.model_version, "key": key,
                     "no": 1 if latest is None else latest[1] + 1, "run": run_id, "ws": i.window.start,
                     "we": i.window.end, "claim": claim, "result": json.dumps(result),
                     "ev": json.dumps(list(evidence)), "basis": basis, "now": now})
                new_ids.append(rev_id)
            c.execute(text("INSERT INTO analytic_run_assessment (run_id, assessment_revision_id, tenant_id, site_id, "
                           "scope) VALUES (:r, :rev, :t, :s, :scope)"),
                      {"r": run_id, "rev": rev_id, "t": tenant, "s": i.site_id, "scope": scope})
            revision_ids.append(rev_id)
        self._select(c, out, tenant, run_id, job_id, now)
        return PersistedRun(run_id, True, tuple(revision_ids), tuple(new_ids))

    @staticmethod
    def _select(c: Connection, out: RunOutput, tenant: UUID, run_id: UUID, job_id: UUID | None,
                now: datetime) -> None:
        """Log a DEFAULT selection (created or reused run) in commit order (migration 0008)."""
        if out.selection != "DEFAULT":
            return
        i = out.inputs
        c.execute(text(
            "INSERT INTO analytic_run_selection (tenant_id, site_id, analytic_id, window_start, window_end, run_id, "
            "job_id, selected_at) VALUES (:t, :s, :a, :ws, :we, :r, :job, :now)"),
            {"t": tenant, "s": i.site_id, "a": i.analytic_id, "ws": i.window.start, "we": i.window.end,
             "r": run_id, "job": job_id, "now": now})

    def run_heads(self, tenant_id: UUID, site_id: UUID, analytic_id: str) -> list[RunHead]:
        def work(c: Connection) -> list[RunHead]:
            # The head is the last selection in commit order, not the newest run (a reverted input
            # reuses an older run; migration 0008).
            rows = c.execute(text(
                "SELECT DISTINCT ON (x.window_start, x.window_end) x.window_start, x.window_end, r.model_version, "
                "r.configuration_sha256 FROM analytic_run_selection x JOIN analytic_run r ON r.id = x.run_id "
                "WHERE x.tenant_id = :t AND x.site_id = :s AND x.analytic_id = :a "
                "ORDER BY x.window_start, x.window_end, x.seq DESC"),
                {"t": tenant_id, "s": site_id, "a": analytic_id}).all()
            return [RunHead(Window(r[0], r[1]), r[2], r[3]) for r in rows]

        return self._run(work)

    def assessed_sites(self, analytic_id: str) -> list[tuple[UUID, UUID]]:
        return self._run(lambda c: [(r[0], r[1]) for r in c.execute(text(
            "SELECT DISTINCT tenant_id, site_id FROM analytic_run_selection WHERE analytic_id = :a "
            "ORDER BY tenant_id, site_id"), {"a": analytic_id}).all()])

    def live_jobs(self, analytic_id: str, domain: str, tenant_id: UUID | None = None,
                  site_id: UUID | None = None) -> list[dict[str, Any]]:
        """Live jobs (unfinished, or FAILED and not yet superseded by a later DEFAULT selection over their window;
        `_LIVE_JOBS`) of every Site, or of one Site, with status, window, attempts, lease and last error (S4-02d
        Site inventory and backlog)."""
        scope = "" if site_id is None else " AND tenant_id = :t AND site_id = :s"
        return self._run(lambda c: [dict(r._mapping) for r in c.execute(text(
            "SELECT id, tenant_id, site_id, status, window_start, window_end, attempts, available_at, lease_until, "
            "last_error, created_at FROM recompute_job WHERE domain = :d AND " + _LIVE_JOBS + scope +
            " ORDER BY tenant_id, site_id, available_at, created_at"),
            {"a": analytic_id, "d": domain, "t": tenant_id, "s": site_id})])

    def live_mini_jobs(self, tenant_id: UUID | None = None, site_id: UUID | None = None) -> list[dict[str, Any]]:
        """Live four-domain mini jobs (`_LIVE_MINI_JOBS`) of every Site, or of one Site: the `live_jobs` fields
        and order, plus the job's domain (W4-02 q7 ruling 2). `live_jobs` stays Dispatch-only."""
        scope = "" if site_id is None else " AND tenant_id = :t AND site_id = :s"
        return self._run(lambda c: [dict(r._mapping) for r in c.execute(text(
            "SELECT id, tenant_id, site_id, domain, status, window_start, window_end, attempts, available_at, "
            "lease_until, last_error, created_at FROM recompute_job WHERE " + _MINI_DOMAIN_SQL + " AND "
            + _LIVE_MINI_JOBS + scope + " ORDER BY tenant_id, site_id, available_at, created_at"),
            {"t": tenant_id, "s": site_id})])

    def job(self, tenant_id: UUID, site_id: UUID, job_id: UUID, analytic_id: str) -> dict[str, Any] | None:
        """One job of this tenant/Site (never another Site's), with whether it is still live (`_LIVE_JOBS`)."""
        row = self._run(lambda c: c.execute(text(
            "SELECT id, tenant_id, site_id, domain, status, window_start, window_end, attempts, available_at, "
            "last_error, " + _LIVE_JOBS + " AS live FROM recompute_job WHERE tenant_id = :t AND site_id = :s "
            "AND id = :j"), {"a": analytic_id, "t": tenant_id, "s": site_id, "j": job_id}).first())
        return None if row is None else dict(row._mapping)

    # --- phase-3 reads: selected window, pinned run, revision drill-down -----------

    def _snapshot(self, work):
        """One REPEATABLE READ transaction: every part of a read sees one committed state."""
        engine = self._connect_engine()
        try:
            with engine.connect().execution_options(isolation_level="REPEATABLE READ") as connection:
                with connection.begin():
                    return work(connection)
        except (OperationalError, ProgrammingError) as error:
            raise AssessmentStoreUnavailable(f"The assessment store failed: {error.orig}") from error

    def window_snapshot(self, query: EvidenceQuery, analytic_id: str,
                        basis: Callable[[EvidenceQueryResult], tuple[str | None, str]]) -> WindowSnapshot:
        """The current accepted basis, the last DEFAULT selection, its revisions and every overlapping
        unfinished or failed job of one window, read in one snapshot (Architect Q7)."""
        return self._snapshot(lambda c: self._window(c, query, analytic_id, basis))

    def claim_limit_snapshot(self, query: EvidenceQuery, analytic_id: str,
                             basis: Callable[[EvidenceQueryResult], tuple[str | None, str]],
                             revision_id: UUID | None) -> tuple[WindowSnapshot, dict[str, Any] | None]:
        """S3-02a: the window snapshot and one exact revision's detail in the same REPEATABLE READ snapshot,
        so currentness and the pinned revision can never come from two committed states."""
        def work(c: Connection) -> tuple[WindowSnapshot, dict[str, Any] | None]:
            snap = self._window(c, query, analytic_id, basis)
            detail = None if revision_id is None else self._revision_detail(
                c, query.tenant_id, query.site_id, revision_id)
            return snap, detail

        return self._snapshot(work)

    def _window(self, c: Connection, query: EvidenceQuery, analytic_id: str,
                basis: Callable[[EvidenceQueryResult], tuple[str | None, str]], *,
                cutoff: datetime | None = None, all_jobs: bool = False) -> WindowSnapshot:
        """`cutoff` (W3-01 q5) keeps only the selection, assessment key heads and jobs recorded at or before it;
        `all_jobs` returns every overlapping job whatever its status, for the caller to reconstruct at the cutoff."""
        w = query.window
        rng = query.read_range
        rows = c.execute(text(_EVIDENCE), {
            "t": query.tenant_id, "s": query.site_id, "k": query.knowledge_at, "lo": rng.start, "hi": rng.end,
            "any_role": not query.roles, "roles": list(query.roles)}).all()
        readings = tuple(_reading(r) for r in rows)
        config = self._configuration(c, query.tenant_id, query.site_id, rng, query.knowledge_at)
        input_sha, config_sha = basis(EvidenceQueryResult(
            query, readings, config.bindings, config.controls, config.role_sets, config.limits,
            _attestations(c, query.tenant_id, query.site_id, query.knowledge_at)))
        p = {"t": query.tenant_id, "s": query.site_id, "a": analytic_id, "ws": w.start, "we": w.end,
             "d": query.domain, "lo": rng.start, "hi": rng.end, "k": cutoff}

        def by(column: str) -> str:
            return "" if cutoff is None else f" AND {column} <= :k"
        head = c.execute(text(
            "SELECT seq, selected_at, job_id, run_id FROM analytic_run_selection WHERE tenant_id = :t "
            f"AND site_id = :s AND analytic_id = :a AND window_start = :ws AND window_end = :we{by('selected_at')} "
            "ORDER BY seq DESC LIMIT 1"), p).first()
        jobs = c.execute(text(
            "SELECT id, status, window_start, window_end, attempts, last_error, created_at, available_at "
            "FROM recompute_job WHERE tenant_id = :t AND site_id = :s AND domain = :d "
            f"AND {'TRUE' if all_jobs else _LIVE_JOBS} AND window_start < :hi AND window_end >= :lo{by('created_at')} "
            "ORDER BY created_at, id"), p).all()
        run = None if head is None else self._run_detail(c, query.tenant_id, query.site_id, head[3])
        keys = c.execute(text(
            "SELECT DISTINCT ON (assessment_key) assessment_key, id, revision_no, claim_level, created_at "
            "FROM assessment_revision WHERE tenant_id = :t AND site_id = :s AND analytic_id = :a "
            f"AND window_start = :ws AND window_end = :we{by('created_at')} "
            "ORDER BY assessment_key, revision_no DESC"), p).all()
        read_at = c.execute(text("SELECT clock_timestamp()")).scalar_one()
        return WindowSnapshot(
            reading_count=len(readings), current_input_sha256=input_sha, current_configuration_sha256=config_sha,
            head=None if head is None else {"seq": head[0], "selected_at": head[1], "job_id": head[2]},
            run=run,
            jobs=[dict(zip(("id", "status", "window_start", "window_end", "attempts", "last_error",
                            "created_at", "available_at"), j)) for j in jobs],
            key_heads=[dict(zip(("assessment_key", "id", "revision_no", "claim_level", "created_at"), k))
                       for k in keys],
            read_at=read_at)

    # --- W3-01 Run 5 (q5): S3 dispatch day selection on a caller-owned connection, at a cutoff -----------

    def select_dispatch_days_on(self, c: Connection, tenant_id: UUID, site_id: UUID, from_: datetime,
                                to: datetime, known_at: datetime) -> list[dict[str, Any]]:
        """One S3 dispatch result for each UTC day intersecting `[from_, to)`, as of `known_at`, on `c` (no
        transaction of its own). Each day reuses the S3 selector (`_window`) with `EvidenceQuery(knowledge_at=
        known_at)`: the accepted basis is decided by then, the selection, assessment key heads and jobs are
        recorded by then, and the selected run and its revisions must be recorded by then. A day with no
        selection by then is returned with `selection=None` and its at-cutoff status. A day the stored records
        cannot reconstruct at the cutoff is returned `available=False` with its reasons and no selection, never
        a current day labelled historical. Job status is a mutable column with no transition time: below the
        transaction time a job counts as outstanding at the cutoff (reported PENDING) when it is PENDING or LEASED
        now, or DONE with its first selection after the cutoff; as finished when a selection is recorded by then;
        and a DONE job with no selection, or a FAILED job, makes the day unavailable. At or after
        the transaction time the jobs are read exactly as the S3 read does."""
        if from_ >= to:
            return []
        live = known_at >= self._transaction_time(c)

        def basis(result: EvidenceQueryResult) -> tuple[str | None, str]:
            inputs, config_sha = input_basis(result, dispatch_v3)
            return (None if inputs.cohort.status == "EMPTY" else inputs.input_sha256), config_sha

        days: list[dict[str, Any]] = []
        day = from_.astimezone(timezone.utc).date()
        while (window := day_window(day)).start < to:
            if window.end > from_:
                days.append(self._dispatch_day_on(c, tenant_id, site_id, day, window, known_at, live, basis))
            day += timedelta(days=1)
        return days

    @staticmethod
    def _transaction_time(c: Connection) -> datetime:
        """The caller's transaction time: at or after it, a job's present status is its status at the cutoff."""
        return c.execute(text("SELECT now()")).scalar_one()

    def _dispatch_day_on(self, c: Connection, tenant_id: UUID, site_id: UUID, day: date, window: Window,
                         known_at: datetime, live: bool,
                         basis: Callable[[EvidenceQueryResult], tuple[str | None, str]]) -> dict[str, Any]:
        query = EvidenceQuery(tenant_id, site_id, DISPATCH_DOMAIN, window, known_at, roles=DISPATCH_ROLES)
        snap = self._window(c, query, dispatch_v3.ANALYTIC_ID, basis, cutoff=known_at, all_jobs=not live)
        unavailable: list[str] = []
        if not live:
            outstanding = []
            for job in snap.jobs:
                if job["status"] in ("PENDING", "LEASED"):
                    # open now, created by the cutoff, and job states never return from terminal: open then too;
                    # the lease state at the cutoff is not recorded, so it is reported as PENDING
                    outstanding.append({**job, "status": "PENDING"})
                    continue
                selected = None
                if job["status"] == "DONE":
                    selected = c.execute(text(
                        "SELECT min(selected_at) FROM analytic_run_selection WHERE tenant_id = :t "
                        "AND site_id = :s AND job_id = :j"),
                        {"t": tenant_id, "s": site_id, "j": job["id"]}).scalar_one()
                if selected is None:
                    unavailable.append(f"JOB_STATE_AT_CUTOFF_UNKNOWN: job {job['id']} is {job['status']} now and "
                                       "no stored completion selection establishes its state at the cutoff")
                elif selected > known_at:
                    outstanding.append({**job, "status": "PENDING"})  # completed only after the cutoff
            snap = replace(snap, jobs=outstanding)
        run = snap.run
        if run is not None:
            if run["completed_at"] is None or run["completed_at"] > known_at:
                unavailable.append(f"SELECTED_RUN_AFTER_CUTOFF: run {run['id']} was recorded after the cutoff")
            if any(r["created_at"] > known_at for r in run["revisions"]):
                unavailable.append(f"SELECTED_REVISION_AFTER_CUTOFF: run {run['id']} cites a revision recorded "
                                   "after the cutoff")
        base = {"day": day, "window_start": window.start, "window_end": window.end, "known_at": known_at,
                "available": not unavailable, "unavailable_reasons": unavailable}
        if unavailable:
            return {**base, "status": None, "status_reasons": [], "selection": None, "run_id": None,
                    "assessment_revision_ids": [], "window_assessment_revision_id": None,
                    "accepted_reading_count": None, "input_sha256": None, "configuration_sha256": None,
                    "accepted_watermarks": None, "jobs": []}
        projection = derive_status(snap, dispatch_v3.MODEL_VERSION)
        revisions = [] if run is None else run["revisions"]
        window_rev = next((r for r in revisions if r.get("scope") == "WINDOW"), None)
        return {**base, "status": projection.status, "status_reasons": list(projection.reasons),
                "selection": None if run is None else {
                    "seq": snap.head["seq"], "selected_at": snap.head["selected_at"],
                    "selected_by_job": snap.head["job_id"], "run_id": run["id"],
                    "model_version": run["model_version"], "cohort": run["cohort"]},
                "run_id": None if run is None else run["id"],
                "assessment_revision_ids": sorted(str(r["id"]) for r in revisions),
                "window_assessment_revision_id": None if window_rev is None else window_rev["id"],
                "accepted_reading_count": snap.reading_count, "input_sha256": snap.current_input_sha256,
                "configuration_sha256": snap.current_configuration_sha256,
                "accepted_watermarks": None if run is None else run["watermarks"], "jobs": snap.jobs}

    def run_detail(self, tenant_id: UUID, site_id: UUID, run_id: UUID) -> dict[str, Any] | None:
        return self._snapshot(lambda c: self._run_detail(c, tenant_id, site_id, run_id))

    def _run_detail(self, c: Connection, tenant_id: UUID, site_id: UUID, run_id: UUID) -> dict[str, Any] | None:
        p = {"t": tenant_id, "s": site_id, "r": run_id}
        row = c.execute(text(
            "SELECT id, analytic_id, model_version, window_start, window_end, knowledge_cutoff, input_sha256, "
            "cohort_status, cohort_sha256, cohort, configuration_sha256, foundation_revision_ids, "
            "binding_set_revision_ids, role_coverage, watermarks, selection, job_id, started_at, completed_at "
            "FROM analytic_run WHERE tenant_id = :t AND site_id = :s AND id = :r"), p).first()
        if row is None:
            return None
        run = dict(zip(("id", "analytic_id", "model_version", "window_start", "window_end", "knowledge_cutoff",
                        "input_sha256", "cohort_status", "cohort_sha256", "cohort", "configuration_sha256",
                        "foundation_revision_ids", "binding_set_revision_ids", "role_coverage", "watermarks",
                        "selection", "job_id", "started_at", "completed_at"), row))
        run["revisions"] = [_revision_row(r) for r in c.execute(text(
            f"SELECT {_REVISION_COLUMNS}, l.scope FROM analytic_run_assessment l JOIN assessment_revision v "
            "ON v.id = l.assessment_revision_id WHERE l.tenant_id = :t AND l.site_id = :s AND l.run_id = :r "
            "ORDER BY l.scope DESC, v.assessment_key"), p).all()]
        run["evidence"] = _evidence(c, tenant_id, site_id, c.execute(text(
            "SELECT evidence_id FROM analytic_run_evidence WHERE tenant_id = :t AND site_id = :s AND run_id = :r"),
            p).scalars().all())
        return run

    def revision_detail(self, tenant_id: UUID, site_id: UUID, revision_id: UUID) -> dict[str, Any] | None:
        return self._snapshot(lambda c: self._revision_detail(c, tenant_id, site_id, revision_id))

    def _revision_detail(self, c: Connection, tenant_id: UUID, site_id: UUID,
                         revision_id: UUID) -> dict[str, Any] | None:
        p = {"t": tenant_id, "s": site_id, "r": revision_id}
        row = c.execute(text(
            f"SELECT {_REVISION_COLUMNS}, NULL FROM assessment_revision v WHERE v.tenant_id = :t "
            "AND v.site_id = :s AND v.id = :r"), p).first()
        if row is None:
            return None
        revision = _revision_row(row)
        revision["history"] = [_revision_row(r) for r in c.execute(text(
            f"SELECT {_REVISION_COLUMNS}, NULL FROM assessment_revision v WHERE v.tenant_id = :t "
            "AND v.site_id = :s AND v.analytic_id = :a AND v.assessment_key = :k ORDER BY v.revision_no"),
            {**p, "a": revision["analytic_id"], "k": revision["assessment_key"]}).all()]
        revision["selected_by_runs"] = [str(x) for x in c.execute(text(
            "SELECT run_id FROM analytic_run_assessment WHERE tenant_id = :t AND site_id = :s "
            "AND assessment_revision_id = :r ORDER BY run_id"), p).scalars().all()]
        revision["run"] = self._run_detail(c, tenant_id, site_id, revision["analytic_run_id"])
        revision["evidence"] = _evidence(c, tenant_id, site_id, revision["evidence_ids"])
        return revision

    def claim_limit_snapshot_on(self, c: Connection, tenant_id: UUID, site_id: UUID, day: date,
                                revision_id: UUID | None,
                                known_at: datetime) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """W3-02 0b: one UTC day's dispatch selection at `known_at` (`select_dispatch_days_on`) and one exact
        revision's detail (`_revision_detail`), both on the caller's connection `c`, with no transaction of its
        own. The detail is not cut off here: the claim-limit read validates its records against `known_at`."""
        window = day_window(day)
        selected = {**self.select_dispatch_days_on(c, tenant_id, site_id, window.start, window.end, known_at)[0],
                    "transaction_time": self._transaction_time(c)}
        detail = None if revision_id is None else self._revision_detail(c, tenant_id, site_id, revision_id)
        return selected, detail

    def lineage_breaks(self, tenant_id: UUID, site_id: UUID, analytic_id: str,
                       model_version: str) -> dict[str, int]:
        """Counts of lineage breaks for the Performance cutover gate; every break count must be zero.
        A window whose last DEFAULT selection used another model version is one (not yet reassessed)."""
        def work(c: Connection) -> dict[str, int]:
            p = {"t": tenant_id, "s": site_id, "a": analytic_id, "m": model_version}

            def count(sql: str) -> int:
                return int(c.execute(text(sql), p).scalar_one())

            return {
                "selected_runs": count(
                    "SELECT count(DISTINCT run_id) FROM analytic_run_selection WHERE tenant_id = :t "
                    "AND site_id = :s AND analytic_id = :a"),
                "selected_heads_other_model": count(
                    "SELECT count(*) FROM (SELECT DISTINCT ON (x.window_start, x.window_end) r.model_version "
                    "FROM analytic_run_selection x JOIN analytic_run r ON r.id = x.run_id WHERE x.tenant_id = :t "
                    "AND x.site_id = :s AND x.analytic_id = :a ORDER BY x.window_start, x.window_end, x.seq DESC"
                    ") h WHERE h.model_version <> :m"),
                "run_evidence_not_accepted": count(
                    "SELECT count(*) FROM analytic_run_evidence x JOIN analytic_run r ON r.id = x.run_id "
                    "WHERE r.tenant_id = :t AND r.site_id = :s AND r.analytic_id = :a AND NOT EXISTS ("
                    "SELECT 1 FROM ingestion_disposition d WHERE d.accepted_evidence_id = x.evidence_id "
                    "AND d.decision = 'ACCEPTED')"),
                "revision_evidence_outside_run": count(
                    "SELECT count(*) FROM assessment_revision v CROSS JOIN LATERAL "
                    "jsonb_array_elements_text(v.evidence_ids) AS ev(id) WHERE v.tenant_id = :t AND v.site_id = :s "
                    "AND v.analytic_id = :a AND NOT EXISTS (SELECT 1 FROM analytic_run_evidence x WHERE "
                    "x.run_id = v.analytic_run_id AND x.evidence_id = CAST(ev.id AS uuid))"),
                "runs_without_window_revision": count(
                    "SELECT count(*) FROM analytic_run r WHERE r.tenant_id = :t AND r.site_id = :s "
                    "AND r.analytic_id = :a AND NOT EXISTS (SELECT 1 FROM analytic_run_assessment l "
                    "WHERE l.run_id = r.id AND l.scope = 'WINDOW')"),
                "foundation_revisions_missing": count(
                    "SELECT count(*) FROM analytic_run r CROSS JOIN LATERAL "
                    "jsonb_array_elements_text(r.foundation_revision_ids) AS f(id) WHERE r.tenant_id = :t "
                    "AND r.site_id = :s AND r.analytic_id = :a AND NOT EXISTS (SELECT 1 FROM foundation_revision "
                    "x WHERE x.tenant_id = :t AND x.site_id = :s AND x.id = CAST(f.id AS uuid))"),
            }

        return self._snapshot(work)

    def accepted_evidence(self, tenant_id: UUID, site_id: UUID, message_ids: list[str]) -> dict[str, str]:
        """Accepted Evidence ID of each cited message ID that is accepted centrally in this Site."""
        if not message_ids:
            return {}
        return self._snapshot(lambda c: {r[0]: str(r[1]) for r in c.execute(text(
            "SELECT e.message_id, e.id FROM accepted_evidence e JOIN ingestion_disposition d "
            "ON d.accepted_evidence_id = e.id AND d.decision = 'ACCEPTED' WHERE e.tenant_id = :t AND e.site_id = :s "
            "AND e.message_id = ANY(:m)"), {"t": tenant_id, "s": site_id, "m": list(message_ids)}).all()})

    def selected_intervals(self, tenant_id: UUID, site_id: UUID, analytic_id: str, domain: str,
                           bracket: timedelta) -> list[dict[str, Any]]:
        """INTERVAL revisions of each window's last DEFAULT selection, with that run's window limitations
        and every unfinished or failed recompute job overlapping the window's read range (the read's
        freshness rule: a matching prior result stays stale while a job is outstanding)."""
        def work(c: Connection) -> list[dict[str, Any]]:
            heads = c.execute(text(
                "SELECT DISTINCT ON (window_start, window_end) run_id, window_start, window_end "
                "FROM analytic_run_selection WHERE tenant_id = :t AND site_id = :s AND analytic_id = :a "
                "ORDER BY window_start, window_end, seq DESC"), {"t": tenant_id, "s": site_id, "a": analytic_id})
            out = []
            for run_id, ws, we in heads.all():
                jobs = [{"id": str(j[0]), "status": j[1]} for j in c.execute(text(
                    "SELECT id, status FROM recompute_job WHERE tenant_id = :t AND site_id = :s AND domain = :d "
                    f"AND {_LIVE_JOBS} AND window_start < :hi AND window_end >= :lo "
                    "ORDER BY created_at, id"), {"t": tenant_id, "s": site_id, "d": domain, "a": analytic_id, "lo": ws - bracket,
                                                 "hi": we + bracket}).all()]
                revisions = [_revision_row(r) for r in c.execute(text(
                    f"SELECT {_REVISION_COLUMNS}, l.scope FROM analytic_run_assessment l JOIN assessment_revision v "
                    "ON v.id = l.assessment_revision_id WHERE l.run_id = :r"), {"r": run_id}).all()]
                limits = [x for r in revisions if r["scope"] == "WINDOW"
                          for x in (r["result"] or {}).get("limitations", [])]
                out += [{**r, "window_limitations": limits, "window_jobs": jobs}
                        for r in revisions if r["scope"] == "INTERVAL"]
            return out

        return self._snapshot(work)

    # --- cold_chain (W2-03): selection and the assessment/episode projection --------------------------------
    # `.agent/W2-03-build-spec.md` commit 3. Every cold method takes the caller's connection: the cold worker owns
    # one transaction for assessment, episodes, Findings and job completion. This module alone inserts the
    # analytic and episode rows; the Finding store alone inserts Finding rows.

    @staticmethod
    def ev_enqueue_configuration(c: Connection, tenant_id: UUID, site_id: UUID, valid_from: datetime,
                                 valid_to: datetime | None, cause: str, now: datetime) -> None:
        """W2-06 Q12: on the publishing connection, after an effective EV Foundation, binding/mapping or S4-05
        source-gate change, dirty every already selected `ev-session/1` window intersecting `[valid_from,
        valid_to)` (open-ended when `valid_to` is None), each separately; with none, seed `valid_from`'s five-minute
        bracket. The coalescing is migration 0025's `ev_enqueue_window`, shared with the accepted-evidence trigger;
        `cause_evidence_id` stays NULL (`recompute_job` has no column for the textual `cause`). It commits or rolls
        back with the caller's publication."""
        c.execute(text("SELECT ev_enqueue_configuration(:t, :s, :f, :to, :now)"),
                  {"t": tenant_id, "s": site_id, "f": valid_from, "to": valid_to, "now": now})

    def transaction(self):
        """One write transaction on the store's engine, for the cold worker to share across both stores."""
        return self._connect_engine().begin()

    @staticmethod
    def cold_watermark(c: Connection, tenant_id: UUID, site_id: UUID) -> datetime | None:
        """The latest committed disposition instant of the Site: the default cold `known_at`."""
        return c.execute(text("SELECT max(decided_at) FROM ingestion_disposition WHERE tenant_id = :t "
                              "AND site_id = :s"), {"t": tenant_id, "s": site_id}).scalar()

    def cold_still_mine(self, c: Connection, lease: JobLease) -> None:
        self._still_mine(c, lease)

    @staticmethod
    def cold_complete(c: Connection, lease: JobLease) -> None:
        c.execute(text("UPDATE recompute_job SET status = 'DONE', lease_until = NULL, last_error = NULL "
                       "WHERE id = :id"), {"id": lease.job_id})

    @staticmethod
    def cold_windows(c: Connection, lease: JobLease) -> list[Window]:
        """The work window of a cold job: the five-minute-aligned bracket of its accepted source times, merged with
        every selected cold window within the rules' ten-minute bridge of it, so one contiguous accepted series
        (including a late reading inside it) is assessed as one window."""
        lo, hi = lease.window.start, lease.window.end
        start = lo - ((lo - _COLD_EPOCH) % cold.SLOT)
        rest = (hi - _COLD_EPOCH) % cold.SLOT
        end = hi if rest == timedelta(0) else hi + (cold.SLOT - rest)
        selected = c.execute(text(
            "SELECT DISTINCT window_start, window_end FROM analytic_run_selection WHERE tenant_id = :t "
            "AND site_id = :s AND analytic_id IN (:a, :b) AND window_start <= :hi AND window_end >= :lo"),
            {"t": lease.tenant_id, "s": lease.site_id, "a": cold.EXCURSION_ANALYTIC,
             "b": cold.START_RESPONSE_ANALYTIC, "lo": start - cold.MAX_BRIDGE, "hi": end + cold.MAX_BRIDGE}).all()
        for a, b in selected:
            start, end = min(start, a), max(end, b)
        return [Window(start, end)]

    def cold_inputs(self, c: Connection, tenant_id: UUID, site_id: UUID,
                    window: cold.ColdWindow) -> cold.ColdInputs:
        """Accepted records in `[from,to)` known at `known_at`, the one effective Foundation and `cold-roles-1`
        binding set covering the window (policy, calibration, probe/room/generator), clock attestation and the
        exact S4-05 source gate. Anything missing, duplicated or overlapping refuses (fail closed)."""
        lo, hi, k = window.from_at, window.to_at, window.known_at
        p = {"t": tenant_id, "s": site_id, "k": k, "lo": lo, "hi": hi}
        foundations = c.execute(text(
            f"SELECT id, version, valid_from, valid_to, content FROM foundation_revision WHERE tenant_id = :t "
            f"AND site_id = :s AND {_KNOWN} AND {_OVERLAPS}"), p).all()
        if len(foundations) != 1:
            raise cold.ColdConfigurationRefused(
                f"{len(foundations)} effective Foundation revisions overlap the window; exactly one is required")
        f_id, f_version, f_from, f_to, content = foundations[0]
        if f_from > lo or (f_to is not None and f_to < hi):
            raise cold.ColdConfigurationRefused(f"Foundation v{f_version} does not cover the whole window")
        content = content if isinstance(content, dict) else json.loads(content)
        assets = {r[0]: r[1] for r in c.execute(text(
            "SELECT asset_code, id FROM asset WHERE tenant_id = :t AND site_id = :s"), p).all()}
        components = list(content.get("components") or ())

        def one(component_type: str) -> dict[str, Any]:
            found = [x for x in components if x.get("component_type") == component_type]
            if len(found) != 1:
                raise cold.ColdConfigurationRefused(f"{len(found)} {component_type} components; exactly one needed")
            return found[0]

        def number(component: dict[str, Any], key: str) -> Decimal:
            items = [i for i in component.get("properties") or () if i.get("property_key") == key]
            if len(items) != 1 or items[0].get("value") is None:
                raise cold.ColdConfigurationRefused(f"{component.get('component_id')} has no single {key}")
            try:
                return Decimal(str(items[0]["value"]))
            except InvalidOperation as error:
                raise cold.ColdConfigurationRefused(f"{key} is not a number") from error

        def asset_of(component: dict[str, Any]) -> UUID:
            code = component.get("component_id")
            if code not in assets:
                raise cold.ColdConfigurationRefused(f"component {code} has no Site asset")
            return assets[code]

        room, generator = one("COLD_ROOM"), one("GENERATOR")
        sets = c.execute(text(
            f"SELECT id, valid_from, valid_to FROM signal_binding_set_revision WHERE tenant_id = :t "
            f"AND site_id = :s AND role_set = :rs AND {_KNOWN} AND {_OVERLAPS}"), {**p, "rs": ROLE_SET_COLD_1}).all()
        if len(sets) != 1:
            raise cold.ColdConfigurationRefused(
                f"{len(sets)} effective {ROLE_SET_COLD_1} binding sets overlap the window; exactly one is required")
        set_id, set_from, set_to = sets[0]
        if set_from > lo or (set_to is not None and set_to < hi):
            raise cold.ColdConfigurationRefused(f"the {ROLE_SET_COLD_1} binding set does not cover the whole window")
        bindings = c.execute(text(
            "SELECT id, role, asset_id, valid_from, valid_to FROM signal_binding_revision WHERE tenant_id = :t "
            "AND site_id = :s AND binding_set_revision_id = :b ORDER BY id"), {**p, "b": set_id}).all()

        def bound(role: str) -> list[UUID]:
            return sorted({b[2] for b in bindings if b[1] == role}, key=str)

        probes = bound(cold.PROBE_ROLE)
        if len(probes) != 1:
            raise cold.ColdConfigurationRefused(
                f"{len(probes)} assets bound to {cold.PROBE_ROLE}; exactly one needed")
        probe_asset = probes[0]
        probe_components = [x for x in components if x.get("component_type") == "TEMPERATURE_PROBE"
                            and assets.get(x.get("component_id")) == probe_asset]
        if len(probe_components) != 1:
            raise cold.ColdConfigurationRefused("the bound chamber probe is not one Foundation temperature probe")
        number(probe_components[0], "cold-probe-error")  # Q10: calibration resolved here, or refused
        generator_asset = asset_of(generator)
        if bound(cold.START_ROLE) != [generator_asset]:
            raise cold.ColdConfigurationRefused(f"{cold.START_ROLE} is not bound to the Foundation generator")
        policy = cold.ColdPolicy(asset_of(room), probe_asset, number(room, "cold-policy-low"),
                                 number(room, "cold-policy-high"), number(room, "cold-return-hysteresis"),
                                 number(room, "cold-min-excursion"))
        start_policy = cold.ColdStartPolicy(generator_asset, number(generator, "cold-start-timeout"),
                                            bool(bound(cold.TRANSFER_ROLE)), probe_asset)
        effective = {b[0]: b for b in bindings}
        attestations = _attestations(c, tenant_id, site_id, k)
        rows = c.execute(text(
            "SELECT e.id, e.envelope_sha256, e.family, e.record_kind, e.role, e.asset_id, e.source_time, "
            "e.received_at, d.decided_at, e.quality, e.normalized_value_text, e.normalized_unit, e.event_id, "
            "e.correlation_id, e.outcome, e.source_id, e.sequence_epoch, e.binding_revision_id "
            "FROM accepted_evidence e JOIN ingestion_batch b ON b.tenant_id = e.tenant_id "
            "AND b.site_id = e.site_id AND b.id = e.batch_id JOIN ingestion_disposition d "
            "ON d.batch_id = e.batch_id AND d.accepted_evidence_id = e.id AND d.decision = 'ACCEPTED' "
            "WHERE e.tenant_id = :t AND e.site_id = :s AND e.source_time >= :lo AND e.source_time < :hi "
            "AND e.received_at <= :k AND d.decided_at <= :k ORDER BY e.source_time, e.received_at, e.id"), p).all()
        evidence = []
        for r in rows:
            b = effective.get(r[17])
            in_force = (b is not None and b[1] == r[4] and b[2] == r[5] and b[3] <= r[6]
                        and (b[4] is None or r[6] < b[4]))
            attested = any(str(a.source_id) == str(r[15]) and a.sequence_epoch == r[16] and a.covers(r[6], r[6])
                           for a in attestations)
            evidence.append(cold.ColdEvidence(
                evidence_id=r[0], envelope_sha256=r[1], family=r[2], record_kind=r[3],
                role=r[4] if in_force else None, asset_id=r[5], source_time=r[6], received_at=r[7],
                decided_at=r[8], quality=r[9], value=_cold_value(r[10]), unit=r[11],
                event_id=r[12], correlation_id=r[13], outcome=r[14], source_id=str(r[15]),
                clock_attested=attested))
        ids = [str(e.evidence_id) for e in evidence]
        if self._link_rows is None:
            raise cold.ColdConfigurationRefused("no S4-05 link reader is configured for the cold source gate")
        classified = classify(ids, {row.requested_id: link_of(row)
                                    for row in (self._link_rows(c, tenant_id, site_id, ids) if ids else [])})
        gate = cold.SourceGate(classified["state"], tuple(sorted({e.source_id for e in evidence})),
                               classified["state"] in (REGISTERED_SIMULATION, AUTHORED_DEMONSTRATION))
        return cold.ColdInputs(tenant_id, site_id, window, tuple(evidence), policy, start_policy, gate,
                               (f_id,), tuple(sorted(effective, key=str)))

    def cold_persist(self, c: Connection, inputs: cold.ColdInputs, assessment: cold.ColdAssessment, *,
                     job_id: UUID | None, selection: str, now: datetime, started: datetime) -> dict[str, Any]:
        """Run, run evidence, the window's assessment revision (appended when the basis changed, reused when it
        is identical) and, for a DEFAULT run, its selection. Returns the run/revision IDs and whether it is new."""
        t, s, w = inputs.tenant_id, inputs.site_id, inputs.window
        analytic = assessment.analytic_id
        c.execute(text(_ASSESS_LOCK), {"site": s, "suffix": ":cold-assessment"})
        basis = inputs.basis(analytic)
        key = f"{analytic}:{cold.iso(w.from_at)}:{cold.iso(w.to_at)}"

        def select(run_id: UUID) -> None:
            if selection == "DEFAULT":
                c.execute(text(
                    "INSERT INTO analytic_run_selection (tenant_id, site_id, analytic_id, window_start, window_end, "
                    "run_id, job_id, selected_at) VALUES (:t, :s, :a, :ws, :we, :r, :job, :now)"),
                    {"t": t, "s": s, "a": analytic, "ws": w.from_at, "we": w.to_at, "r": run_id, "job": job_id,
                     "now": now})

        latest = c.execute(text(
            "SELECT id, revision_no, basis_sha256 FROM assessment_revision WHERE site_id = :s AND analytic_id = :a "
            "AND assessment_key = :key ORDER BY revision_no DESC LIMIT 1"),
            {"s": s, "a": analytic, "key": key}).first()
        held = c.execute(text(
            "SELECT r.id, x.assessment_revision_id FROM analytic_run r JOIN analytic_run_assessment x "
            "ON x.run_id = r.id WHERE r.site_id = :s AND r.analytic_id = :a AND r.model_version = :m "
            "AND r.window_start = :ws AND r.window_end = :we AND r.input_sha256 = :b"),
            {"s": s, "a": analytic, "m": cold.MODEL_VERSION, "ws": w.from_at, "we": w.to_at, "b": basis}).first()
        if held is not None:
            select(held[0])
            return {"run_id": held[0], "revision_id": held[1], "created": False, "basis": basis,
                    "previous_revision_id": None, "coverage": assessment.coverage}
        run_id, revision_id = uuid4(), uuid4()
        policy = inputs.policy if analytic == cold.EXCURSION_ANALYTIC else inputs.start_policy
        document = cold.assessment_document(assessment, policy=policy, gate=inputs.gate)
        evidence_ids = sorted(str(e.evidence_id) for e in inputs.evidence)
        c.execute(text(
            "INSERT INTO analytic_run (id, tenant_id, site_id, analytic_id, model_version, window_start, "
            "window_end, knowledge_cutoff, input_sha256, cohort_status, cohort_sha256, cohort, "
            "configuration_sha256, foundation_revision_ids, binding_set_revision_ids, role_coverage, watermarks, "
            "selection, job_id, status, started_at, completed_at) VALUES (:id, :t, :s, :a, :m, :ws, :we, :k, :b, "
            "'NOT_APPLICABLE', :b, CAST(:cohort AS jsonb), :cfg, CAST(:fids AS jsonb), CAST(:bids AS jsonb), "
            "'{}'::jsonb, CAST(:marks AS jsonb), :sel, :job, 'COMPLETED', :started, :now)"),
            {"id": run_id, "t": t, "s": s, "a": analytic, "m": cold.MODEL_VERSION, "ws": w.from_at,
             "we": w.to_at, "k": w.known_at, "b": basis,
             "cohort": json.dumps({"source_gate": document["source_gate"]}),
             "cfg": sha256_json(document["policy"]),
             "fids": json.dumps([str(x) for x in inputs.foundation_revision_ids]),
             "bids": json.dumps([str(x) for x in inputs.binding_revision_ids]),
             "marks": json.dumps({"known_at": cold.iso(w.known_at)}), "sel": selection, "job": job_id,
             "started": started, "now": now})
        if evidence_ids:
            c.execute(text("INSERT INTO analytic_run_evidence (run_id, evidence_id, tenant_id, site_id) "
                           "VALUES (:r, :e, :t, :s)"),
                      [{"r": run_id, "e": e, "t": t, "s": s} for e in evidence_ids])
        if latest is not None and latest[2] == basis:
            revision_id = latest[0]
        else:
            c.execute(text(
                "INSERT INTO assessment_revision (id, tenant_id, site_id, analytic_id, model_version, "
                "assessment_key, revision_no, analytic_run_id, window_start, window_end, claim_level, result, "
                "evidence_ids, basis_sha256, created_at) VALUES (:id, :t, :s, :a, :m, :key, :n, :run, :ws, :we, "
                ":claim, CAST(:result AS jsonb), CAST(:ids AS jsonb), :b, :now)"),
                {"id": revision_id, "t": t, "s": s, "a": analytic, "m": cold.MODEL_VERSION, "key": key,
                 "n": 1 if latest is None else latest[1] + 1, "run": run_id, "ws": w.from_at, "we": w.to_at,
                 "claim": assessment.claim_level, "result": json.dumps(document), "ids": json.dumps(evidence_ids),
                 "b": basis, "now": now})
        c.execute(text("INSERT INTO analytic_run_assessment (run_id, assessment_revision_id, tenant_id, site_id, "
                       "scope) VALUES (:r, :a, :t, :s, 'WINDOW')"),
                  {"r": run_id, "a": revision_id, "t": t, "s": s})
        select(run_id)
        return {"run_id": run_id, "revision_id": revision_id, "created": True, "basis": basis,
                "previous_revision_id": None if latest is None else latest[0], "coverage": assessment.coverage}

    def cold_episodes(self, c: Connection, inputs: cold.ColdInputs, assessment: cold.ColdAssessment,
                      persisted: dict[str, Any], now: datetime) -> list[dict[str, Any]]:
        """Episodes of one new assessment revision: an excursion per confirmed crossing, a chain per start
        correlation, each keyed by its stable anchor. A changed basis appends a revision; an episode the previous
        revision supported but this one does not gets a `NO_LONGER_SUPPORTED` revision (no evidence links), and
        a new anchor of the same kind and subject records `split_from_episode_id`. Returns what the Finding store
        needs."""
        t, s = inputs.tenant_id, inputs.site_id
        kind = "EXCURSION" if assessment.analytic_id == cold.EXCURSION_ANALYTIC else "START_RESPONSE"
        items = assessment.excursions if kind == "EXCURSION" else assessment.chains
        subject = inputs.policy.room_asset_id if kind == "EXCURSION" else inputs.start_policy.generator_asset_id
        supported_before: list[UUID] = []
        if persisted["previous_revision_id"] is not None:
            # A supported revision always links evidence; a NO_LONGER_SUPPORTED one links none.
            supported_before = [r[0] for r in c.execute(text(
                "SELECT r.episode_id FROM cold_episode_revision r JOIN cold_episode e ON e.id = r.episode_id "
                "WHERE r.tenant_id = :t AND r.site_id = :s AND r.assessment_revision_id = :a AND e.kind = :k "
                "AND EXISTS (SELECT 1 FROM cold_episode_evidence x WHERE x.episode_revision_id = r.id) "
                "ORDER BY e.anchor_time, r.episode_id"),
                {"a": persisted["previous_revision_id"], "t": t, "s": s, "k": kind}).all()]
        keyed = {cold.episode_key_sha256(t, s, kind, subject, x.anchor_evidence_id): x for x in items}
        found = {r[1]: r[0] for r in c.execute(text(
            "SELECT id, episode_key_sha256 FROM cold_episode WHERE tenant_id = :t AND site_id = :s "
            "AND episode_key_sha256 = ANY(:keys)"), {"t": t, "s": s, "keys": list(keyed)}).all()} if keyed else {}
        invalidated = [e for e in supported_before if e not in found.values()]
        out = [self._cold_revision(c, t, s, e, persisted, None, kind, subject, now) for e in invalidated]
        for key, item in keyed.items():
            episode_id, split = found.get(key), None
            if episode_id is None:
                episode_id = uuid4()
                split = invalidated[0] if invalidated else None
                c.execute(text(
                    "INSERT INTO cold_episode (id, tenant_id, site_id, kind, asset_id, anchor_time, "
                    "episode_key_sha256, split_from_episode_id, finding_id, created_at) VALUES (:i, :t, :s, :k, :a, "
                    ":at, :key, :sp, NULL, :now)"),
                    {"i": episode_id, "t": t, "s": s, "k": kind, "a": subject, "at": item.anchor_time, "key": key,
                     "sp": split, "now": now})
            row = self._cold_revision(c, t, s, episode_id, persisted, item, kind, subject, now)
            out.append({**row, "split_from_episode_id": split})
        return out

    @staticmethod
    def _cold_revision(c: Connection, t: UUID, s: UUID, episode_id: UUID, persisted: dict[str, Any], item,
                       kind: str, subject: UUID, now: datetime) -> dict[str, Any]:
        """Append one episode revision (or reuse the identical-basis one) with its exact evidence links."""
        latest = c.execute(text(
            "SELECT id, revision_no, basis_sha256 FROM cold_episode_revision WHERE episode_id = :e "
            "ORDER BY revision_no DESC LIMIT 1"), {"e": episode_id}).first()
        before = set() if latest is None else {(str(r[0]), r[1]) for r in c.execute(text(
            "SELECT evidence_id, use FROM cold_episode_evidence WHERE episode_revision_id = :r"),
            {"r": latest[0]}).all()}
        first: dict[tuple[str, str], str | None] = {}
        for link in () if item is None else item.links:
            first.setdefault((str(link.evidence_id), link.use), link.reason)
        links = sorted((e, u, why) for (e, u), why in first.items())
        result = {"episode_id": episode_id, "kind": kind, "subject_asset_id": subject, "item": item,
                  "state": "NO_LONGER_SUPPORTED" if item is None else "SUPPORTED",
                  "evidence_changed": before != {(e, u) for e, u, _ in links}, "split_from_episode_id": None,
                  "support_ids": sorted({e for e, u, _ in links if u == "SUPPORT"})}
        if latest is not None and latest[2] == persisted["basis"]:
            return {**result, "revision_id": latest[0], "revision_no": latest[1], "created": False}
        rid, n = uuid4(), 1 if latest is None else latest[1] + 1
        x = item if (kind == "EXCURSION" and item is not None) else None
        coverage = persisted["coverage"] if kind == "EXCURSION" else Decimal(0)
        c.execute(text(
            "INSERT INTO cold_episode_revision (id, tenant_id, site_id, episode_id, revision_no, "
            "assessment_revision_id, basis_sha256, claim_level, lower_start, upper_start, lower_end, upper_end, "
            "duration_low, duration_high, degree_minutes_low, degree_minutes_high, peak_observed, coverage, "
            "missing_steps, created_at) VALUES (:i, :t, :s, :e, :n, :a, :b, :claim, :ls, :us, :le, :ue, :dl, :dh, "
            ":ml, :mh, :peak, :cov, CAST(:missing AS jsonb), :now)"),
            {"i": rid, "t": t, "s": s, "e": episode_id, "n": n, "a": persisted["revision_id"],
             "b": persisted["basis"], "claim": "UNKNOWN" if item is None else item.claim_level,
             "ls": x and x.start_earliest, "us": x and x.start_latest, "le": x and x.end_earliest,
             "ue": x and x.end_latest, "dl": x and x.duration_low, "dh": x and x.duration_high,
             "ml": x and x.degree_minutes_low, "mh": x and x.degree_minutes_high, "peak": x and x.peak_observed,
             "cov": format(Decimal(coverage).quantize(Decimal("0.0001")), "f"),
             "missing": json.dumps(list(item.missing_steps) if (item is not None and kind == "START_RESPONSE")
                                   else []), "now": now})
        if links:
            c.execute(text("INSERT INTO cold_episode_evidence (episode_revision_id, tenant_id, site_id, "
                           "evidence_id, use, reason) VALUES (:r, :t, :s, :e, :u, :why)"),
                      [{"r": rid, "t": t, "s": s, "e": e, "u": u, "why": why} for e, u, why in links])
        return {**result, "revision_id": rid, "revision_no": n, "created": True}


    # --- ev_charging (W2-06 commit 3): ev-session/1 on the EV worker's connection --------------------------------
    # `.agent/W2-06-build-spec.md` commit 3, Q10-Q14 and q3 P1-P4. Every EV method takes the caller's connection:
    # the EV worker owns one transaction for selection, run, assessment, sessions, Findings and job completion. This
    # module alone inserts the analytic and EV session rows; the Finding store alone inserts Finding rows.

    @staticmethod
    def ev_watermark(c: Connection, tenant_id: UUID, site_id: UUID) -> datetime | None:
        """The latest committed disposition instant of the Site: the default EV `known_at`."""
        return PostgresAssessmentStore.cold_watermark(c, tenant_id, site_id)

    def ev_still_mine(self, c: Connection, lease: JobLease) -> None:
        self._still_mine(c, lease)

    @staticmethod
    def ev_complete(c: Connection, lease: JobLease) -> None:
        PostgresAssessmentStore.cold_complete(c, lease)

    @staticmethod
    def ev_windows(c: Connection, lease: JobLease) -> list[Window]:
        """The assessment windows of an EV job (r8 H1): every exact selected `ev-session/1` window intersecting the
        full leased job bounds is re-assessed at its exact bounds (never widened, merged or replaced by a covering
        window); the job interval minus those selections is aligned outward to five-minute UTC brackets, the
        selected intervals are subtracted again, and each nonempty remainder piece is its own window. Output is
        deduplicated by exact bounds; the worker assesses and selects all of them before completing the job."""
        lo, hi = lease.window.start, lease.window.end

        def align(a: datetime, b: datetime) -> tuple[datetime, datetime]:
            start = a - ((a - _COLD_EPOCH) % _EV_BRACKET)
            rest = (b - _COLD_EPOCH) % _EV_BRACKET
            return start, (b if rest == timedelta(0) else b + (_EV_BRACKET - rest))

        def subtract(pieces: list[tuple[datetime, datetime]],
                     cuts: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
            for a, b in cuts:
                out: list[tuple[datetime, datetime]] = []
                for x, y in pieces:
                    if b <= x or a >= y:
                        out.append((x, y))
                        continue
                    if x < a:
                        out.append((x, a))
                    if b < y:
                        out.append((b, y))
                pieces = out
            return pieces

        hull_lo, hull_hi = align(lo, hi)
        # Selected windows near the job: those intersecting the job are re-headed; those intersecting only the
        # aligned brackets are subtracted from the remainder so no new window overlaps an existing selection.
        near = [(a, b) for a, b in c.execute(text(
            "SELECT DISTINCT window_start, window_end FROM analytic_run_selection WHERE tenant_id = :t "
            "AND site_id = :s AND analytic_id = :a AND window_start < :hi AND window_end > :lo ORDER BY 1, 2"),
            {"t": lease.tenant_id, "s": lease.site_id, "a": ev.SESSION_ANALYTIC, "lo": hull_lo, "hi": hull_hi}).all()]
        selected = [(a, b) for a, b in near if a < hi and b > lo]
        remainder: list[tuple[datetime, datetime]] = []
        for x, y in subtract([(lo, hi)], selected):
            remainder.extend(subtract([align(x, y)], near))
        out: list[Window] = []
        seen: set[tuple[datetime, datetime]] = set()
        for a, b in sorted(selected + remainder):
            if a < b and (a, b) not in seen:
                seen.add((a, b))
                out.append(Window(a, b))
        return out

    def ev_inputs(self, c: Connection, tenant_id: UUID, site_id: UUID, window: Window,
                  known_at: datetime) -> ev.EvInputs:
        """Accepted records whose measurement touches `[from,to)` known at `known_at`, the one effective Foundation
        and `ev-roles-1` binding set covering the window (connectors with their single parent charger and exact
        properties, q3 P4; every member binding, q3 P2), the registered public mapping profile (Q8), clock
        attestation per row (q3 P1) and the exact S4-05 source class. Anything missing, duplicated or overlapping
        refuses (fail closed)."""
        lo, hi, k = window.start, window.end, known_at
        if hi - lo > _EV_MAX_WINDOW:
            raise ev.EvConfigurationRefused("an EV assessment window spans at most 31 days")
        w = ev.EvWindow(lo, hi, k)
        p = {"t": tenant_id, "s": site_id, "k": k, "lo": lo, "hi": hi}
        profile = v4_mapping_profile(ROLE_SET_EV_1)
        if profile != (V4_EV_MAPPING_PROFILE_ID, V4_EV_MAPPING_PROFILE_VERSION):
            raise ev.EvConfigurationRefused(f"the {ROLE_SET_EV_1} mapping table is not the registered public profile")
        foundations = c.execute(text(
            f"SELECT id, version, valid_from, valid_to, content FROM foundation_revision WHERE tenant_id = :t "
            f"AND site_id = :s AND {_KNOWN} AND {_OVERLAPS}"), p).all()
        if len(foundations) != 1:
            raise ev.EvConfigurationRefused(
                f"{len(foundations)} effective Foundation revisions overlap the window; exactly one is required")
        f_id, f_version, f_from, f_to, content = foundations[0]
        if f_from > lo or (f_to is not None and f_to < hi):
            raise ev.EvConfigurationRefused(f"Foundation v{f_version} does not cover the whole window")
        content = content if isinstance(content, dict) else json.loads(content)
        assets = {r[0]: r[1] for r in c.execute(text(
            "SELECT asset_code, id FROM asset WHERE tenant_id = :t AND site_id = :s"), p).all()}
        components = {x.get("component_id"): x for x in content.get("components") or ()}
        topology = content.get("topology") or {}
        node_component = {n.get("node_id"): n.get("component_id") for n in topology.get("nodes") or ()}
        parents: dict[str, list[str]] = {}
        for edge in topology.get("connections") or ():
            if edge.get("medium") == "SIGNAL":
                parents.setdefault(node_component.get(edge.get("to_node")), []).append(
                    node_component.get(edge.get("from_node")))

        def asset_of(component: dict[str, Any]) -> UUID:
            code = component.get("component_id")
            if code not in assets:
                raise ev.EvConfigurationRefused(f"component {code} has no Site asset")
            return assets[code]

        def number(component: dict[str, Any], key: str) -> Decimal:
            items = [i for i in component.get("properties") or () if i.get("property_key") == key]
            if len(items) != 1 or items[0].get("value") is None:
                raise ev.EvConfigurationRefused(f"{component.get('component_id')} has no single {key}")
            item, unit = items[0], _EV_UNITS[key]
            if item.get("unit") != unit:
                raise ev.EvConfigurationRefused(f"{key} is declared in {item.get('unit')}, not {unit}")
            try:
                return Decimal(str(item["value"]))
            except InvalidOperation as error:
                raise ev.EvConfigurationRefused(f"{key} is not a number") from error

        connectors = []
        for cid, component in sorted(components.items(), key=lambda kv: str(kv[0])):
            if component.get("component_type") != "EV_CONNECTOR":
                continue
            chargers = [x for x in parents.get(cid, [])
                        if (components.get(x) or {}).get("component_type") == "EV_CHARGER"]
            if len(chargers) != 1 or len(parents.get(cid, [])) != 1:
                raise ev.EvConfigurationRefused(f"connector {cid} does not have exactly one parent charger")
            charger = components[chargers[0]]
            connectors.append(ev.EvConnector(
                asset_id=asset_of(component), charger_asset_id=asset_of(charger), connector_id=cid,
                max_power_kw=number(component, "ev-connector-max-power"),
                meter_resolution_kwh=number(component, "ev-meter-resolution"),
                meter_error_bound_kwh=number(component, "ev-meter-error-bound"),
                clock_error_bound_s=number(component, "ev-clock-error-bound"),
                status_cadence_min=number(component, "ev-status-cadence"),
                meter_cadence_min=number(component, "ev-meter-cadence"),
                charger_max_power_kw=number(charger, "ev-charger-max-power")))
        if not connectors:
            raise ev.EvConfigurationRefused("the Foundation declares no EV connector")
        sets = c.execute(text(
            f"SELECT id, valid_from, valid_to FROM signal_binding_set_revision WHERE tenant_id = :t "
            f"AND site_id = :s AND role_set = :rs AND {_KNOWN} AND {_OVERLAPS}"), {**p, "rs": ROLE_SET_EV_1}).all()
        if len(sets) != 1:
            raise ev.EvConfigurationRefused(
                f"{len(sets)} effective {ROLE_SET_EV_1} binding sets overlap the window; exactly one is required")
        set_id, set_from, set_to = sets[0]
        if set_from > lo or (set_to is not None and set_to < hi):
            raise ev.EvConfigurationRefused(f"the {ROLE_SET_EV_1} binding set does not cover the whole window")
        members = tuple(ev.EvBindingMember(
            binding_revision_id=r[0], binding_set_revision_id=r[1], role=r[2], asset_id=r[3], source_id=r[4],
            device_id=r[5], signal_id=r[6], valid_from=r[7], valid_to=r[8]) for r in c.execute(text(
                "SELECT id, binding_set_revision_id, role, asset_id, source_id, device_id, signal_id, valid_from, "
                "valid_to FROM signal_binding_revision WHERE tenant_id = :t AND site_id = :s "
                "AND binding_set_revision_id = :b ORDER BY id"), {**p, "b": set_id}).all())
        attestations = _attestations(c, tenant_id, site_id, k)
        rows = _ev_rows(c, p)
        ids = [str(r[0]) for r in rows]
        if self._link_rows is None:
            raise ev.EvConfigurationRefused("no S4-05 link reader is configured for the EV source gate")
        links = {row.requested_id: link_of(row)
                 for row in (self._link_rows(c, tenant_id, site_id, ids) if ids else [])}
        # r8/r9 M1: the whole accepted set is classified first; only a coherent positive class projects. A MIXED or
        # UNKNOWN non-empty set refuses before `assess`/`ev_persist` (the job stays FAILED/retryable) with the S4-05
        # reasons and exact IDs as the diagnostic detail. An empty set yields no records (the worker skips it).
        whole = classify(ids, links)
        if ids and whole["state"] not in ev.ASSESSABLE_CLASSES:
            raise ev.EvConfigurationRefused(
                f"{ev.SOURCE_UNASSESSABLE} class={whole['state']} reasons="
                + json.dumps([{"code": x["code"], "accepted_evidence_ids": x["accepted_evidence_ids"]}
                              for x in whole["reasons"]], separators=(",", ":")))
        records = []
        for r in rows:
            lo_r = r[3] if r[3] is not None else r[2]
            hi_r = r[4] if r[4] is not None else r[2]
            attested = any(str(a.source_id) == str(r[17]) and a.sequence_epoch == r[18] and a.covers(lo_r, hi_r)
                           for a in attestations)
            records.append(ev.EvRecord(
                report_key=None, report_sha256=None, batch_external_id=None, ordinal=None,
                accepted_evidence_id=r[0], envelope_sha256=r[1], source_time=r[2], interval_start=r[3],
                interval_end=r[4], connector_id=r[5], session_id=r[6], family=r[7], record_kind=r[8],
                measurement=r[9], quality=r[10], value=r[11], unit=r[12], event_id=r[13], outcome=r[14],
                asset_id=r[15], binding_revision_id=r[16], source_id=None if r[17] is None else str(r[17]),
                sequence_epoch=r[18], clock_attested=attested,
                # r8 M1: the per-record gate is the S4-05 link status and exact binding (`ev._source_reason`).
                source_class=_ev_link_class(links.get(str(r[0]))), binding_set_revision_id=r[19], role=r[20],
                device_id=r[21], signal_id=r[22]))
        return ev.EvInputs(
            tenant_id=tenant_id, site_id=site_id, window=w, records=tuple(records), connectors=tuple(connectors),
            foundation_revision_id=f_id, binding_revision_id=set_id,
            mapping_profile_id=f"{profile[0]}/{profile[1]}", source_class=whole["state"],
            binding_members=members)

    def ev_persist(self, c: Connection, inputs: ev.EvInputs, assessed: ev.EvAssessment, *, job_id: UUID | None,
                   selection: str, now: datetime, started: datetime | None = None) -> dict[str, Any]:
        """Q14: the run, run evidence, the window's assessment revision and, for a DEFAULT run, its selection. The
        identical idempotency key `(Site, ev-session/1, window, input_sha256, model 1)` returns the existing IDs
        and appends nothing (a DEFAULT selection only if another run heads that window). A new run plans each
        session's revision (an identical session basis reuses its revision) so the immutable result can list
        them."""
        t, s, w = inputs.tenant_id, inputs.site_id, inputs.window
        c.execute(text(_ASSESS_LOCK), {"site": s, "suffix": ":ev-assessment"})
        basis = ev.run_input_sha256(inputs, assessed)
        key = assessed.assessment_key
        scope = {"t": t, "s": s, "a": ev.SESSION_ANALYTIC, "ws": w.from_at, "we": w.to_at}

        def select(run_id: UUID) -> None:
            if selection != "DEFAULT":
                return
            head = c.execute(text(
                "SELECT run_id FROM analytic_run_selection WHERE tenant_id = :t AND site_id = :s AND analytic_id = :a "
                "AND window_start = :ws AND window_end = :we ORDER BY selected_at DESC LIMIT 1"), scope).first()
            if head is None or head[0] != run_id:
                c.execute(text(
                    "INSERT INTO analytic_run_selection (tenant_id, site_id, analytic_id, window_start, window_end, "
                    "run_id, job_id, selected_at) VALUES (:t, :s, :a, :ws, :we, :r, :job, :now)"),
                    {**scope, "r": run_id, "job": job_id, "now": now})

        held = c.execute(text(
            "SELECT r.id, x.assessment_revision_id FROM analytic_run r JOIN analytic_run_assessment x "
            "ON x.run_id = r.id WHERE r.tenant_id = :t AND r.site_id = :s AND r.analytic_id = :a "
            "AND r.model_version = :m AND r.window_start = :ws AND r.window_end = :we AND r.input_sha256 = :b"),
            {**scope, "m": ev.MODEL_VERSION, "b": basis}).first()
        if held is not None:
            select(held[0])
            return {"run_id": held[0], "revision_id": held[1], "created": False, "basis": basis,
                    "assessment_key": key, "previous_revision_id": None, "plan": []}
        configuration = ev.configuration_sha256(inputs)
        run_id, revision_id = uuid4(), uuid4()
        ids = sorted({r.id for r in inputs.records})
        decided = c.execute(text(
            "SELECT max(decided_at) FROM ingestion_disposition WHERE tenant_id = :t AND site_id = :s "
            "AND decision = 'ACCEPTED' AND accepted_evidence_id = ANY(CAST(:ids AS uuid[]))"),
            {"t": t, "s": s, "ids": ids}).scalar() if ids else None
        required = sorted(r.role for r in EV_ROLES_1 if r.required)
        present = {m.role for m in inputs.binding_members}
        missing = [r for r in required if r not in present]
        c.execute(text(
            "INSERT INTO analytic_run (id, tenant_id, site_id, analytic_id, model_version, window_start, "
            "window_end, knowledge_cutoff, input_sha256, cohort_status, cohort_sha256, cohort, "
            "configuration_sha256, foundation_revision_ids, binding_set_revision_ids, role_coverage, watermarks, "
            "selection, job_id, status, started_at, completed_at) VALUES (:id, :t, :s, :a, :m, :ws, :we, :k, :b, "
            "'NOT_APPLICABLE', :cohort_sha, '[]'::jsonb, :cfg, CAST(:fids AS jsonb), CAST(:bids AS jsonb), "
            "CAST(:roles AS jsonb), CAST(:marks AS jsonb), :sel, :job, 'COMPLETED', :started, :now)"),
            {**scope, "id": run_id, "m": ev.MODEL_VERSION, "k": w.known_at, "b": basis,
             "cohort_sha": ev.cohort_sha256(), "cfg": configuration,
             "fids": json.dumps([str(inputs.foundation_revision_id).lower()]),
             "bids": json.dumps([str(inputs.binding_revision_id).lower()]),
             "roles": json.dumps({"required_roles": required, "missing_roles": missing, "covered": not missing}),
             "marks": json.dumps({"accepted_decided_at": None if decided is None else iso(decided),
                                  "known_at": iso(w.known_at), "source_class": inputs.source_class}),
             "sel": selection, "job": job_id, "started": started or now, "now": now})
        if ids:
            c.execute(text("INSERT INTO analytic_run_evidence (run_id, evidence_id, tenant_id, site_id) "
                           "VALUES (:r, :e, :t, :s)"),
                      [{"r": run_id, "e": e, "t": t, "s": s} for e in ids])
        plan = [self._ev_plan(c, t, s, session) for session in assessed.sessions]
        latest = c.execute(text(
            "SELECT id, revision_no FROM assessment_revision WHERE tenant_id = :t AND site_id = :s "
            "AND analytic_id = :a AND assessment_key = :key ORDER BY revision_no DESC LIMIT 1"),
            {**scope, "key": key}).first()
        as_of = iso(now)
        document = {
            "schema": "ev-session-assessment/1",
            "status": {"state": assessed.status_state, "claim_level": assessed.claim_level, "as_of": as_of,
                       "limitation": assessed.limitation},
            "denominator": {**{k: assessed.denominator[k] for k in _EV_COUNTS}, "as_of": as_of,
                            "limitation": assessed.limitation},
            "session_revision_ids": sorted(str(x["revision_id"]).lower() for x in plan),
            "excluded_records": [dict(x) for x in assessed.excluded_records],
            "source_provenance": {"class": inputs.source_class, "as_of": as_of, "limitation": None},
            "limitations": [],
        }
        c.execute(text(
            "INSERT INTO assessment_revision (id, tenant_id, site_id, analytic_id, model_version, "
            "assessment_key, revision_no, analytic_run_id, window_start, window_end, claim_level, result, "
            "evidence_ids, basis_sha256, created_at) VALUES (:id, :t, :s, :a, :m, :key, :n, :run, :ws, :we, "
            ":claim, CAST(:result AS jsonb), CAST(:ids AS jsonb), :b, :now)"),
            {**scope, "id": revision_id, "m": ev.MODEL_VERSION, "key": key,
             "n": 1 if latest is None else latest[1] + 1, "run": run_id, "claim": assessed.claim_level,
             "result": json.dumps(document), "ids": json.dumps(ids), "b": basis, "now": now})
        c.execute(text("INSERT INTO analytic_run_assessment (run_id, assessment_revision_id, tenant_id, site_id, "
                       "scope) VALUES (:r, :a, :t, :s, 'WINDOW')"),
                  {"r": run_id, "a": revision_id, "t": t, "s": s})
        select(run_id)
        return {"run_id": run_id, "revision_id": revision_id, "created": True, "basis": basis,
                "assessment_key": key, "previous_revision_id": None if latest is None else latest[0], "plan": plan}

    @staticmethod
    def _ev_plan(c: Connection, t: UUID, s: UUID, session: ev.EvSession) -> dict[str, Any]:
        """The stable session ID (existing, or new for its first START) and the revision of `session`: the stored
        revision with this exact session basis, else a new one numbered after the latest."""
        found = c.execute(text(
            "SELECT id FROM ev_session WHERE tenant_id = :t AND site_id = :s AND charger_asset_id = :ch "
            "AND connector_asset_id = :co AND external_session_id = :x"),
            {"t": t, "s": s, "ch": session.charger_asset_id, "co": session.connector_asset_id,
             "x": session.external_session_id}).first()
        if found is None:
            return {"session": session, "session_id": uuid4(), "new_session": True, "revision_id": uuid4(),
                    "revision_no": 1, "created": True}
        same = c.execute(text(
            "SELECT id, revision_no FROM ev_session_revision WHERE tenant_id = :t AND site_id = :s "
            "AND session_id = :e AND basis_sha256 = :b"),
            {"t": t, "s": s, "e": found[0], "b": session.basis_sha256}).first()
        if same is not None:
            return {"session": session, "session_id": found[0], "new_session": False, "revision_id": same[0],
                    "revision_no": same[1], "created": False}
        n = c.execute(text("SELECT coalesce(max(revision_no), 0) + 1 FROM ev_session_revision WHERE tenant_id = :t "
                           "AND site_id = :s AND session_id = :e"), {"t": t, "s": s, "e": found[0]}).scalar_one()
        return {"session": session, "session_id": found[0], "new_session": False, "revision_id": uuid4(),
                "revision_no": n, "created": True}

    @staticmethod
    def ev_sessions(c: Connection, inputs: ev.EvInputs, assessed: ev.EvAssessment, persisted: dict[str, Any],
                    now: datetime) -> list[dict[str, Any]]:
        """The planned session heads and revisions of one new assessment revision, each new revision with its
        exact evidence links (one use/reason per accepted ID) and representable meter intervals. Returns the plan
        rows (session, IDs, `created`) for the Finding store."""
        t, s = inputs.tenant_id, inputs.site_id
        for row in persisted["plan"]:
            session: ev.EvSession = row["session"]
            if row["new_session"]:
                c.execute(text(
                    "INSERT INTO ev_session (id, tenant_id, site_id, charger_asset_id, connector_asset_id, "
                    "external_session_id, first_start_evidence_id, anchor_time, created_at) VALUES (:i, :t, :s, "
                    ":ch, :co, :x, :first, :at, :now)"),
                    {"i": row["session_id"], "t": t, "s": s, "ch": session.charger_asset_id,
                     "co": session.connector_asset_id, "x": session.external_session_id,
                     "first": session.first_start_evidence_id, "at": session.anchor_time, "now": now})
            if not row["created"]:
                continue
            c.execute(text(
                "INSERT INTO ev_session_revision (id, tenant_id, site_id, session_id, revision_no, "
                "assessment_revision_id, analytic_run_id, basis_sha256, state, start_at, end_at, start_earliest, "
                "start_latest, end_earliest, end_latest, supported_kwh, unknown_meter_seconds, fault_evidence_id, "
                "reason_codes, created_at) VALUES (:i, :t, :s, :e, :n, :a, :run, :b, :state, :start, :end, :se, "
                ":sl, :ee, :el, :kwh, :unknown, :fault, CAST(:reasons AS jsonb), :now)"),
                {"i": row["revision_id"], "t": t, "s": s, "e": row["session_id"], "n": row["revision_no"],
                 "a": persisted["revision_id"], "run": persisted["run_id"], "b": session.basis_sha256,
                 "state": session.state, "start": session.start_at, "end": session.end_at,
                 "se": session.start_bounds[0], "sl": session.start_bounds[1], "ee": session.end_bounds[0],
                 "el": session.end_bounds[1],
                 "kwh": None if session.supported_kwh is None else format(session.supported_kwh, "f"),
                 "unknown": session.unknown_meter_seconds, "fault": session.fault_evidence_id,
                 "reasons": json.dumps(list(session.reason_codes)), "now": now})
            if session.links:
                c.execute(text(
                    "INSERT INTO ev_session_evidence (tenant_id, site_id, revision_id, evidence_id, use, reason) "
                    "VALUES (:t, :s, :r, :e, :u, :why)"),
                    [{"t": t, "s": s, "r": row["revision_id"], "e": link.evidence_id, "u": link.use,
                      "why": link.reason} for link in session.links])
            if session.intervals:
                c.execute(text(
                    "INSERT INTO ev_meter_interval (id, tenant_id, site_id, revision_id, connector_asset_id, "
                    "evidence_id, start_at, end_at, kwh, error_bound_kwh, use, reason) VALUES (:i, :t, :s, :r, :co, "
                    ":e, :lo, :hi, :kwh, :err, :u, :why)"),
                    [{"i": uuid4(), "t": t, "s": s, "r": row["revision_id"], "co": i.connector_asset_id,
                      "e": i.evidence_id, "lo": i.start_at, "hi": i.end_at, "kwh": format(i.kwh, "f"),
                      "err": format(i.error_bound_kwh, "f"), "u": i.use, "why": i.reason} for i in session.intervals])
        return [{k: row[k] for k in ("session", "session_id", "revision_id", "revision_no", "created")}
                for row in persisted["plan"]]


def _cold_value(raw: str | None) -> Decimal | str | None:
    """A numeric normalized value as Decimal; a state value (e.g. `UNPOWERED`) stays its text."""
    if raw is None:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        return raw


_REVISION_NAMES = ("id", "analytic_id", "model_version", "assessment_key", "revision_no", "analytic_run_id",
                   "window_start", "window_end", "claim_level", "result", "evidence_ids", "basis_sha256",
                   "created_at", "scope")
_EVIDENCE_NAMES = ("evidence_id", "envelope_sha256", "message_id", "batch_id", "external_batch_id", "gateway_id",
                   "source_id", "sequence_epoch", "sequence", "device_id", "signal_id", "role", "asset_id",
                   "source_time", "interval_start", "interval_end", "published_at", "received_at", "accepted_at",
                   "quality", "unavailable_reason", "value", "unit", "source_mode", "foundation_revision_id",
                   "binding_set_revision_id", "binding_revision_id", "disposition")


def _reading(r) -> AcceptedReading:
    return AcceptedReading(
        evidence_id=r[0], envelope_sha256=r[1], batch_id=r[2], gateway_id=r[3], source_id=r[4],
        sequence_epoch=r[5], sequence=r[6], role=r[7], asset_id=r[8], source_time=r[9],
        interval_start=r[10], interval_end=r[11], published_at=r[12], received_at=r[13], accepted_at=r[14],
        quality=r[15], value=r[16], unit=r[17], foundation_revision_id=r[18],
        binding_set_revision_id=r[19], binding_revision_id=r[20], source_mode=r[21])


def _revision_row(r) -> dict[str, Any]:
    return dict(zip(_REVISION_NAMES, r))


def _evidence(c: Connection, tenant_id: UUID, site_id: UUID, ids) -> list[dict[str, Any]]:
    """Exact accepted Evidence by stored ID (never re-selected by time or `knowledge_at`)."""
    if not ids:
        return []
    rows = c.execute(text(
        "SELECT e.id, e.envelope_sha256, e.message_id, e.batch_id, b.external_batch_id, e.gateway_id, "
        "e.source_id, e.sequence_epoch, e.sequence, e.device_id, e.signal_id, e.role, e.asset_id, "
        "e.source_time, e.interval_start, e.interval_end, e.published_at, e.received_at, d.decided_at, "
        "e.quality, e.unavailable_reason, e.normalized_value_text, e.normalized_unit, e.source_mode, "
        "e.foundation_revision_id, e.binding_set_revision_id, e.binding_revision_id, d.decision "
        "FROM accepted_evidence e JOIN ingestion_batch b ON b.id = e.batch_id "
        "JOIN ingestion_disposition d ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal "
        "WHERE e.tenant_id = :t AND e.site_id = :s AND e.id = ANY(:ids) ORDER BY e.source_time, e.id"),
        {"t": tenant_id, "s": site_id, "ids": [UUID(str(i)) for i in ids]}).all()
    return [dict(zip(_EVIDENCE_NAMES, r)) for r in rows]


# --- W2-03 commit 4: the selected cold read (read-only; rules in `analytics/cold_reads.py`) ----------------


@dataclass(frozen=True)
class ColdSelected:
    analytic_id: str
    revision_id: UUID
    revision_no: int
    basis: str
    result: dict[str, Any]
    evidence_ids: list[str]
    window_start: datetime
    window_end: datetime
    knowledge_cutoff: datetime


def _cold_plain(value: Any) -> Any:
    return cold.plain(value)


def _cold_decimal(raw: str | None) -> str | None:
    """A stored normalized value as a canonical decimal string, or null when it is not a number."""
    try:
        return None if raw is None else _cold_plain(Decimal(raw))
    except InvalidOperation:
        return None


def _bound_link_rows(c: Connection, link_rows: Callable[..., list], unavailable: type) -> Callable[..., list]:
    """W3-01: `link_rows` on the snapshot connection. A store failure reaches the caller's 503 mapper and a
    programming error propagates (c2 r1 L1); neither is converted into a selected-lineage conflict."""
    def read(t: UUID, s: UUID, ids: list[str]) -> list:
        return list(link_rows(c, t, s, ids))
    return read


class SelectionPinRefused(LookupError):
    """W3-01 Run 6: a pinned cold/EV selection whose exact seq is not a consistent selection at the cutoff (the
    caller's 409 for an internally inconsistent selection); never resolved to another head."""

    def __init__(self, analytic_id: str, seq: int, window_start: datetime, window_end: datetime,
                 cutoff: datetime) -> None:
        super().__init__(f"{analytic_id} seq {seq} [{window_start.isoformat()}, {window_end.isoformat()}) is not a "
                         f"consistent selection at {cutoff.isoformat()}")
        self.analytic_id, self.seq, self.window_start, self.window_end, self.cutoff = (
            analytic_id, seq, window_start, window_end, cutoff)


def selected_windows_on(c: Connection, t: UUID, s: UUID, analytics: tuple[str, ...], from_: datetime,
                        to: datetime, cutoff: datetime,
                        evidence_cutoff: datetime | None = None) -> list[dict[str, Any]]:
    """W3-01 Run 6 Blocker 1: every exact `(analytic_id, window_start, window_end)` of this tenant/Site whose
    selection intersects `[from_, to)` (`window_start < to AND window_end > from_`), with the greatest selection
    seq among rows selected by `cutoff` whose same-tenant/Site run has `knowledge_cutoff` and `completed_at` by it
    and whose assessment revision was created by it. A later reselection is invisible at an earlier cutoff.
    W3-01 Run 7 (q7-1): `cutoff` is the requested cutoff (selection, completion and revision-creation bounds);
    `evidence_cutoff` (default `cutoff`) bounds only the run's `knowledge_cutoff`.
    Ordered by `(window_start, window_end, analytic_id, seq)`. Read on the caller's `c` only."""
    rows = c.execute(text(
        "SELECT DISTINCT ON (sel.analytic_id, sel.window_start, sel.window_end) sel.analytic_id, sel.window_start, "
        "sel.window_end, sel.seq FROM analytic_run_selection sel JOIN analytic_run r ON r.id = sel.run_id "
        "AND r.tenant_id = sel.tenant_id AND r.site_id = sel.site_id WHERE sel.tenant_id = :t AND sel.site_id = :s "
        "AND sel.analytic_id = ANY(:as) AND sel.window_start < :to AND sel.window_end > :from "
        "AND sel.selected_at <= :k AND r.knowledge_cutoff <= :e AND r.completed_at <= :k AND EXISTS (SELECT 1 "
        "FROM analytic_run_assessment x JOIN assessment_revision ar ON ar.id = x.assessment_revision_id "
        "WHERE x.run_id = r.id AND ar.created_at <= :k) "
        "ORDER BY sel.analytic_id, sel.window_start, sel.window_end, sel.seq DESC"),
        {"t": t, "s": s, "as": list(analytics), "from": from_, "to": to, "k": cutoff,
         "e": cutoff if evidence_cutoff is None else evidence_cutoff}).all()
    out = [{"analytic_id": r[0], "window_start": r[1], "window_end": r[2], "seq": int(r[3])} for r in rows]
    return sorted(out, key=lambda k: (k["window_start"], k["window_end"], k["analytic_id"], k["seq"]))


class ColdReadService:
    def __init__(self, database_url: str | None = None, *, engine=None,
                 clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
                 link_rows: Callable[..., list] | None = None) -> None:
        self._url, self._engine, self.clock = database_url, engine, clock
        # W3-01 (Run 3 q3): the S4-05 link-row reader on the snapshot connection, for the public provenance sets.
        self._link_rows = link_rows

    def _public(self, c: Connection) -> PublicProvenance:
        """W3-01: the public DTO resolver bound to this snapshot connection (set reads only). A missing link
        reader is the read's unavailable error, never a fabricated UNKNOWN block."""
        if self._link_rows is None:
            raise ColdReadUnavailable("The cold source provenance reader is not wired.")
        return PublicProvenance(LinkRowsReads(_bound_link_rows(c, self._link_rows, ColdReadUnavailable)))

    def _connect(self):
        if self._engine is None:
            self._engine = create_engine(self._url, pool_pre_ping=True)
        return self._engine.connect().execution_options(isolation_level="REPEATABLE READ")

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()

    def _read(self, work: Callable[[Connection], Any]) -> Any:
        try:
            with self._connect() as c, c.begin():
                return work(c)
        except (OperationalError, DBAPIError) as error:
            raise ColdReadUnavailable(f"The cold assessment store is unavailable: {error.__class__.__name__}") \
                from error

    # --- the shared snapshot ---------------------------------------------------------------------------------

    def _snapshot(self, c: Connection, t: UUID, s: UUID, code: str, lo: datetime | None, hi: datetime | None,
                  known_at: datetime | None, *, selection_cutoff: datetime | None = None,
                  selection_seqs: dict[str, int] | None = None) -> dict[str, Any]:
        """The cold read snapshot on the caller's `c` (never a connection or transaction of its own).

        Default (no `selection_cutoff`): the W2 Site selection, unchanged. Pinned mode (W3-01 Run 6 Blocker 1,
        W4-01 Run 3 ruling 6): `lo`/`hi` are one exact stored selected window and `selection_seqs` maps each
        analytic to select to its exact `analytic_run_selection.seq`; that row must also be selected, its run
        completed and its assessment revision created by `selection_cutoff`, or `SelectionPinRefused` is raised
        (never a fallback to another head). The snapshot then also carries `selection_seqs`."""
        if selection_seqs is not None and selection_cutoff is None:
            raise ValueError("selection_seqs requires selection_cutoff: a pin without a cutoff is never read unpinned.")
        pinned = selection_cutoff is not None
        if pinned and (lo is None or hi is None or not selection_seqs):
            raise ValueError("A pinned cold selection needs its exact stored window and selected seqs.")
        if pinned:
            unknown = sorted(set(selection_seqs) - {cold.EXCURSION_ANALYTIC, cold.START_RESPONSE_ANALYTIC})
            if unknown:
                raise ValueError(f"selection_seqs names unknown cold analytic keys: {unknown}")
        p = {"t": t, "s": s}
        watermark = c.execute(text("SELECT max(decided_at) FROM ingestion_disposition WHERE tenant_id = :t "
                                   "AND site_id = :s"), p).scalar()
        known = known_at or watermark
        if pinned and known is None:
            raise SelectionPinRefused(sorted(selection_seqs)[0], selection_seqs[sorted(selection_seqs)[0]], lo, hi,
                                      selection_cutoff)
        if lo is None and known is not None:  # no explicit window: the latest selected cold window at the cutoff
            row = c.execute(text(
                "SELECT sel.window_start, sel.window_end FROM analytic_run_selection sel JOIN analytic_run r "
                "ON r.id = sel.run_id WHERE sel.tenant_id = :t AND sel.site_id = :s AND sel.analytic_id IN (:a, :b) "
                "AND r.knowledge_cutoff <= :k ORDER BY sel.seq DESC LIMIT 1"),
                {**p, "a": cold.EXCURSION_ANALYTIC, "b": cold.START_RESPONSE_ANALYTIC, "k": known}).first()
            if row is not None:
                lo, hi = row[0], row[1]
        selected: dict[str, ColdSelected] = {}
        if lo is not None and known is not None:
            for analytic in (cold.EXCURSION_ANALYTIC, cold.START_RESPONSE_ANALYTIC):
                if pinned:
                    if analytic not in selection_seqs:
                        continue
                    r = c.execute(text(
                        "SELECT ar.id, ar.revision_no, ar.basis_sha256, ar.result, ar.evidence_ids, sel.window_start, "
                        "sel.window_end, r.knowledge_cutoff FROM analytic_run_selection sel JOIN analytic_run r "
                        "ON r.id = sel.run_id AND r.tenant_id = sel.tenant_id AND r.site_id = sel.site_id "
                        "JOIN analytic_run_assessment x ON x.run_id = r.id JOIN assessment_revision "
                        "ar ON ar.id = x.assessment_revision_id WHERE sel.tenant_id = :t AND sel.site_id = :s "
                        "AND sel.analytic_id = :a AND sel.window_start = :lo AND sel.window_end = :hi "
                        "AND sel.seq = :seq AND sel.selected_at <= :sk AND r.completed_at <= :sk "
                        "AND ar.created_at <= :sk AND r.knowledge_cutoff <= :k LIMIT 1"),
                        {**p, "a": analytic, "lo": lo, "hi": hi, "k": known, "seq": selection_seqs[analytic],
                         "sk": selection_cutoff}).first()
                    if r is None:
                        raise SelectionPinRefused(analytic, selection_seqs[analytic], lo, hi, selection_cutoff)
                else:
                    r = c.execute(text(
                        "SELECT ar.id, ar.revision_no, ar.basis_sha256, ar.result, ar.evidence_ids, sel.window_start, "
                        "sel.window_end, r.knowledge_cutoff FROM analytic_run_selection sel JOIN analytic_run r "
                        "ON r.id = sel.run_id JOIN analytic_run_assessment x ON x.run_id = r.id JOIN assessment_revision "
                        "ar ON ar.id = x.assessment_revision_id WHERE sel.tenant_id = :t AND sel.site_id = :s "
                        "AND sel.analytic_id = :a AND sel.window_start <= :lo AND sel.window_end >= :hi "
                        "AND r.knowledge_cutoff <= :k ORDER BY sel.seq DESC LIMIT 1"),
                        {**p, "a": analytic, "lo": lo, "hi": hi, "k": known}).first()
                if r is not None:
                    result = r[3] if isinstance(r[3], dict) else json.loads(r[3])
                    ids = r[4] if isinstance(r[4], list) else json.loads(r[4])
                    selected[analytic] = ColdSelected(analytic, r[0], r[1], r[2], result, list(ids), r[5], r[6], r[7])
        # W3-01 r1 M3.2: an explicit historical cutoff precedes pending-job selection (job status has no as-of
        # ledger); a current read ignores a job created after the requested `known_at`.
        historical = known_at is not None and watermark is not None and known_at < watermark
        pending_since = None
        if lo is not None and not historical and known is not None:
            pending_since = c.execute(text(
                "SELECT min(created_at) FROM recompute_job WHERE tenant_id = :t AND site_id = :s "
                "AND domain = :d AND status IN ('PENDING', 'LEASED', 'FAILED') AND window_start < :hi "
                "AND window_end > :lo AND (CAST(:k AS timestamptz) IS NULL OR created_at <= :k)"),
                {**p, "d": cold.DOMAIN, "lo": lo - cold.MAX_BRIDGE, "hi": hi + cold.MAX_BRIDGE, "k": known_at}).scalar()
        exc = selected.get(cold.EXCURSION_ANALYTIC)
        support = [UUID(x["evidence_id"]) for x in (exc.result.get("links") or [])
                   if x["use"] == "SUPPORT"] if exc else []
        evidence = self._evidence(c, t, s, support + [UUID(x["evidence_id"]) for x in self._other_links(selected)])
        probes = sorted((evidence[e] for e in support if e in evidence), key=lambda e: (e["source_time"], e["id"]))
        latest_probe = probes[-1]["source_time"] if probes else None
        any_selected = exc or selected.get(cold.START_RESPONSE_ANALYTIC)
        window_to = any_selected.window_end if any_selected else None
        state = currentness_state(pending=pending_since is not None, historical=historical,
                                  selected=bool(selected), latest_probe_at=latest_probe, window_to=window_to,
                                  now=self.clock())
        limitations = []
        if not selected:
            limitations.append(NO_SELECTION_NOTE)
        elif state == "PENDING_RECOMPUTE":
            limitations.append(PENDING_NOTE)
        elif state == "HISTORICAL":
            limitations.append(HISTORICAL_NOTE)
        elif state == "STALE_SOURCE":
            limitations.append(STALE_NOTE)
        elif state == "UNKNOWN":
            limitations.append(FUTURE_NOTE if window_to is not None and window_to > self.clock() else NO_PROBE_NOTE)
        snap = {"code": code, "t": t, "s": s, "lo": lo, "hi": hi, "known": known, "watermark": watermark,
                "selected": selected, "pending_since": pending_since, "evidence": evidence, "probes": probes,
                "latest_probe": latest_probe, "state": state, "limitations": limitations}
        if pinned:
            snap["selection_seqs"] = {a: int(selection_seqs[a]) for a in selected}
            snap["selection_cutoff"] = selection_cutoff
        return snap

    def estate_snapshots_on(self, c: Connection, t: UUID, s: UUID, code: str, from_: datetime, to: datetime,
                            known_at: datetime | None, selection_cutoff: datetime) -> list[dict[str, Any]]:
        """W3-01 Run 6 Blocker 1: one pinned `_snapshot` per exact stored cold window whose as-of selection
        intersects `[from_, to)`; both cold analytics of one exact window share one snapshot. Ordered by
        `(window_start, window_end)`; empty when nothing qualifies (the caller's UNKNOWN, never a zero)."""
        if known_at is None:  # Run 7 q7-1: no provable evidence basis is UNKNOWN, never a current zero
            return []
        keys = selected_windows_on(c, t, s, (cold.EXCURSION_ANALYTIC, cold.START_RESPONSE_ANALYTIC), from_, to,
                                   selection_cutoff, evidence_cutoff=known_at)
        windows: dict[tuple[datetime, datetime], dict[str, int]] = {}
        for k in keys:
            windows.setdefault((k["window_start"], k["window_end"]), {})[k["analytic_id"]] = k["seq"]
        return [self._snapshot(c, t, s, code, lo, hi, known_at, selection_cutoff=selection_cutoff,
                               selection_seqs=seqs) for (lo, hi), seqs in windows.items()]

    @staticmethod
    def _other_links(selected: dict[str, ColdSelected]) -> list[dict[str, Any]]:
        out = []
        for sel in selected.values():
            out += [x for x in sel.result.get("links") or () if x["use"] != "SUPPORT"
                    or sel.analytic_id == cold.START_RESPONSE_ANALYTIC]
        return out

    @staticmethod
    def _evidence(c: Connection, t: UUID, s: UUID, ids: list[UUID]) -> dict[UUID, dict[str, Any]]:
        if not ids:
            return {}
        rows = c.execute(text(
            "SELECT id, source_time, normalized_value_text, quality, outcome, message_id, record_kind, role "
            "FROM accepted_evidence WHERE tenant_id = :t AND site_id = :s AND id = ANY(:ids)"),
            {"t": t, "s": s, "ids": sorted(set(ids), key=str)}).all()
        return {r[0]: {"id": r[0], "source_time": r[1], "value": r[2], "quality": r[3], "outcome": r[4],
                       "message_id": r[5], "record_kind": r[6], "role": r[7]} for r in rows}

    @staticmethod
    def selected_basis(snap: dict[str, Any], analytics: tuple[str, ...]) -> str | None:
        """The private stored selection basis of the route's analytics tuple (the cursor fence; W3-01 Run 1 ruling
        3): one `ColdSelected.basis`, or the existing two-analytic `sha256_json` combination; None if unselected."""
        chosen = [snap["selected"][a] for a in analytics if a in snap["selected"]]
        return (chosen[0].basis if len(chosen) == 1 else sha256_json([x.basis for x in chosen])) if chosen else None

    @staticmethod
    def _pending_ids(c: Connection, snap: dict[str, Any]) -> list[str]:
        """W3-01 Run 2 ruling 2: the complete accepted cold input set of the requested window at the cutoff."""
        return [str(x) for x in c.execute(text(
            "SELECT DISTINCT e.id FROM accepted_evidence e JOIN ingestion_batch b ON b.tenant_id = e.tenant_id "
            "AND b.site_id = e.site_id AND b.id = e.batch_id JOIN ingestion_disposition d ON d.batch_id = e.batch_id "
            "AND d.accepted_evidence_id = e.id AND d.decision = 'ACCEPTED' WHERE e.tenant_id = :t AND e.site_id = :s "
            "AND e.source_time >= :lo AND e.source_time < :hi AND e.received_at <= :k AND d.decided_at <= :k "
            "ORDER BY e.id"),
            {"t": snap["t"], "s": snap["s"], "lo": snap["lo"], "hi": snap["hi"], "k": snap["known"]}).scalars().all()]

    def _provenance_blocks(self, c: Connection, snap: dict[str, Any], analytics: tuple[str, ...]) -> dict[str, Any]:
        """W3-01 Run 1 ruling 5 / Run 2-3: the three sibling blocks. Selected: the chosen revisions' full cited
        union; pending (only when an overlapping cold job exists): the full accepted window set, no digest."""
        chosen = [snap["selected"][a] for a in analytics if a in snap["selected"]]
        public = self._public(c)
        t, s = snap["t"], snap["s"]
        selected = public.cited_set(t, s, sorted({e for x in chosen for e in x.evidence_ids}),
                                    cold_envelope_selection(x.revision_id for x in chosen)) if chosen else None
        pending = public.cited_set(t, s, self._pending_ids(c, snap), []) \
            if snap["pending_since"] is not None else None
        return dual_blocks(selected, pending)

    def _envelope(self, c: Connection, snap: dict[str, Any], analytics: tuple[str, ...]) -> dict[str, Any]:
        chosen = [snap["selected"][a] for a in analytics if a in snap["selected"]]
        return {
            "site_id": str(snap["s"]),
            "window": {"from": _cold_plain(snap["lo"]), "to": _cold_plain(snap["hi"]), "known_at": _cold_plain(snap["known"])},
            "currentness": {"state": snap["state"],
                            "watermark": {"decided_at": _cold_plain(snap["watermark"]),
                                          "assessment_revision_ids": [str(x.revision_id) for x in chosen]},
                            "latest_relevant_evidence_at": _cold_plain(snap["latest_probe"]),
                            "pending_since": _cold_plain(snap["pending_since"])},
            **self._provenance_blocks(c, snap, analytics),
            "limitations": list(snap["limitations"]),
        }

    def _as_of(self, snap: dict[str, Any], analytic: str) -> str | None:
        sel = snap["selected"].get(analytic)
        return None if sel is None else _cold_plain(sel.knowledge_cutoff)

    def _episodes(self, c: Connection, snap: dict[str, Any], sel: ColdSelected | None, kind: str,
                  subject: str | None) -> dict[str, tuple[str, str]]:
        """anchor evidence ID -> (episode_id, episode_revision_id) of the selected assessment revision."""
        if sel is None or subject is None:
            return {}
        rows = c.execute(text(
            "SELECT e.id, e.episode_key_sha256, r.id FROM cold_episode e JOIN cold_episode_revision r "
            "ON r.episode_id = e.id WHERE e.tenant_id = :t AND e.site_id = :s AND e.kind = :k "
            "AND r.assessment_revision_id = :a"),
            {"t": snap["t"], "s": snap["s"], "k": kind, "a": sel.revision_id}).all()
        by_key = {r[1]: (str(r[0]), str(r[2])) for r in rows}
        items = sel.result.get("excursions" if kind == "EXCURSION" else "chains") or []
        out = {}
        for item in items:
            key = cold.episode_key_sha256(snap["t"], snap["s"], kind, UUID(subject), UUID(item["anchor_evidence_id"]))
            if key in by_key:
                out[item["anchor_evidence_id"]] = by_key[key]
        return out

    # --- temperature -----------------------------------------------------------------------------------------

    def temperature(self, tenant_id: UUID, site_id: UUID, code: str, lo: datetime | None, hi: datetime | None,
                    known_at: datetime | None) -> dict[str, Any]:
        return self._read(lambda c: self._temperature(c, tenant_id, site_id, code, lo, hi, known_at))

    def _temperature(self, c, t, s, code, lo, hi, known_at) -> dict[str, Any]:
        snap = self._snapshot(c, t, s, code, lo, hi, known_at)
        body = self._envelope(c, snap, (cold.EXCURSION_ANALYTIC,))
        sel = snap["selected"].get(cold.EXCURSION_ANALYTIC)
        as_of = self._as_of(snap, cold.EXCURSION_ANALYTIC)
        if sel is None:
            return {**body, "policy": None, "points": [], "gaps": [], "excursions": [], "excluded": [],
                    "coverage": {"known_points": None, "expected_points": None, "ratio": None}}
        r, pol = sel.result, sel.result.get("policy") or {}
        in_window = [p for p in snap["probes"] if snap["lo"] <= p["source_time"] < snap["hi"]]
        episodes = self._episodes(c, snap, sel, "EXCURSION", pol.get("room_asset_id"))
        body["limitations"] += list(r.get("limitations") or ()) + [NO_SPOILAGE]
        return {
            **body,
            "state": r.get("state"), "claim_level": r.get("claim_level"),
            "policy": {"low_deg_c": pol.get("policy_low"), "high_deg_c": pol.get("policy_high"),
                       "return_hysteresis_deg_c": pol.get("return_hysteresis"),
                       "min_excursion_min": pol.get("min_excursion_minutes"),
                       "probe_asset_id": pol.get("probe_asset_id"), "room_asset_id": pol.get("room_asset_id"),
                       "as_of": as_of, "limitation": None},
            "points": [{"at": _cold_plain(p["source_time"]), "value": _cold_decimal(p["value"]), "quality": p["quality"], "evidence_id": str(p["id"]),
                "as_of": _cold_plain(p["source_time"]), "limitation": None} for p in in_window],
            "coverage": {"known_points": r.get("known_points"), "expected_points": r.get("expected_points"),
                         "ratio": r.get("coverage")},
            "gaps": [{**{k: g.get(k) for k in ("start", "end", "reason", "expected_points", "received_points")},
                      "as_of": as_of, "limitation": None} for g in r.get("gaps") or ()],
            "excursions": [{
                "episode_id": episodes.get(x["anchor_evidence_id"], (None, None))[0],
                "revision_id": episodes.get(x["anchor_evidence_id"], (None, None))[1],
                "direction": x["direction"], "anchor_time": x["anchor_time"], "open": x["open"],
                "start_bounds": {"earliest": x["start_earliest"], "latest": x["start_latest"]},
                "end_bounds": {"earliest": x["end_earliest"], "latest": x["end_latest"]},
                "duration_bounds": {"low": x["duration_low"], "high": x["duration_high"]},
                "degree_minute_bounds": {"low": x["degree_minutes_low"], "high": x["degree_minutes_high"]},
                "peak_observed": x["peak_observed"], "claim_level": x["claim_level"],
                "exposure_finding": x["exposure_finding"], "as_of": as_of, "limitation": x.get("limitation"),
            } for x in r.get("excursions") or ()],
            "excluded": [{"evidence_id": x["evidence_id"], "use": x["use"], "reason": x["reason"],
                          "as_of": _cold_plain(snap["evidence"].get(UUID(x["evidence_id"]), {}).get("source_time")),
                          "limitation": None}
                         for x in r.get("links") or () if x["use"] != "SUPPORT"],
        }

    # --- backup chain ----------------------------------------------------------------------------------------

    def backup_chain(self, tenant_id: UUID, site_id: UUID, code: str, lo: datetime | None, hi: datetime | None,
                     known_at: datetime | None) -> dict[str, Any]:
        return self._read(lambda c: self._backup(c, tenant_id, site_id, code, lo, hi, known_at))

    def _backup(self, c, t, s, code, lo, hi, known_at) -> dict[str, Any]:
        snap = self._snapshot(c, t, s, code, lo, hi, known_at)
        body = self._envelope(c, snap, (cold.START_RESPONSE_ANALYTIC,))
        sel = snap["selected"].get(cold.START_RESPONSE_ANALYTIC)
        if sel is None:
            return {**body, "state": None, "claim_level": None, "chains": [], "contradictions": []}
        r, as_of = sel.result, self._as_of(snap, cold.START_RESPONSE_ANALYTIC)
        episodes = self._episodes(c, snap, sel, "START_RESPONSE", (r.get("policy") or {}).get("generator_asset_id"))
        order = {name: n for n, name in enumerate(cold.STEPS)}
        chains, contradictions = [], []
        for ch in r.get("chains") or ():
            steps = []
            for st in sorted(ch["steps"], key=lambda x: order.get(x["step"], 99)):
                first = st["evidence_ids"][0] if st.get("evidence_ids") else None
                e = snap["evidence"].get(UUID(first)) if first else None
                outcome = None if e is None else (e["outcome"] or e["value"])
                steps.append({"kind": st["step"], "at": st["at"], "outcome": outcome, "evidence_id": first,
                              "evidence_ids": list(st.get("evidence_ids") or ()), "state": st["state"],
                              "as_of": st["at"], "limitation": None if st["state"] == "OBSERVED" else (
                                  "No accepted record shows this step." if st["state"] == "MISSING"
                                  else "Accepted records disagree for this step.")})
            episode = episodes.get(ch["anchor_evidence_id"], (None, None))
            chains.append({"correlation_id": ch["correlation_id"], "episode_id": episode[0],
                           "revision_id": episode[1], "result": ch["result"], "steps": steps,
                           "missing_steps": list(ch["missing_steps"]), "claim_level": ch["claim_level"],
                           "start_timeout_min": ch["start_timeout_min"], "as_of": as_of,
                           "limitation": ch.get("limitation")})
            conflicting = [x["evidence_id"] for x in ch["links"] if x.get("reason") == "CONTRADICTORY"]
            if conflicting:
                contradictions.append({"correlation_id": ch["correlation_id"], "evidence_ids": sorted(conflicting),
                                       "reason": "CONTRADICTORY", "as_of": as_of,
                                       "limitation": "Conflicting accepted outcomes; no failure is claimed."})
        body["limitations"] += list(r.get("limitations") or ())
        excluded = [{"evidence_id": x["evidence_id"], "use": x["use"], "reason": x["reason"],
                     "as_of": _cold_plain(snap["evidence"].get(UUID(x["evidence_id"]), {}).get("source_time")),
                     "limitation": None} for x in r.get("links") or () if x["use"] != "SUPPORT"]
        return {**body, "state": r.get("state"), "claim_level": r.get("claim_level"), "chains": chains,
                "contradictions": contradictions, "excluded": excluded}

    # --- Findings --------------------------------------------------------------------------------------------

    _REVISION = (
        "SELECT r.id, r.revision_no, r.transition, r.lifecycle, r.claim_level, r.title, r.claim, r.limitations, "
        "r.assessment_revision_id, r.basis_sha256, r.created_at, er.lower_start, er.upper_start, er.lower_end, "
        "er.upper_end, er.id, er.assessment_revision_id FROM finding_revision r JOIN analytic_run ar "
        "ON ar.id = r.analytic_run_id LEFT JOIN cold_episode_revision er ON er.tenant_id = r.tenant_id "
        "AND er.site_id = r.site_id AND er.id = CAST(r.claim->>'episode_revision_id' AS uuid) "
        "WHERE r.finding_id = :f AND r.domain = 'cold_chain' AND ar.knowledge_cutoff <= :k ")

    def _finding_ids(self, c, snap, after: tuple[datetime, UUID] | None, limit: int | None,
                     finding_id: UUID | None = None) -> list:
        sql = ("SELECT f.id, f.anchor_start, f.subject_asset_id, f.split_from_finding_id FROM finding f "
               "WHERE f.tenant_id = :t AND f.site_id = :s AND f.domain = 'cold_chain' AND f.anchor_start >= :lo "
               "AND f.anchor_start < :hi AND EXISTS (SELECT 1 FROM finding_revision r JOIN analytic_run ar "
               "ON ar.id = r.analytic_run_id WHERE r.finding_id = f.id AND ar.knowledge_cutoff <= :k) ")
        p = {"t": snap["t"], "s": snap["s"], "lo": snap["lo"], "hi": snap["hi"], "k": snap["known"]}
        if finding_id is not None:
            sql += "AND f.id = :f "
            p["f"] = finding_id
        if after is not None:
            sql += "AND (f.anchor_start, f.id) > (:at, :aid) "
            p.update(at=after[0], aid=after[1])
        sql += "ORDER BY f.anchor_start, f.id"
        if limit is not None:
            sql += " LIMIT :n"
            p["n"] = limit + 1
        return c.execute(text(sql), p).all()

    def _revisions(self, c, snap, finding_id: UUID, latest_only: bool) -> list:
        sql = self._REVISION + "ORDER BY r.revision_no DESC" + (" LIMIT 1" if latest_only else "")
        return c.execute(text(sql), {"f": finding_id, "k": snap["known"]}).all()

    @staticmethod
    def _revision_evidence(c, revision_id: UUID) -> list[str]:
        return [str(x) for x in c.execute(text(
            "SELECT evidence_id FROM finding_revision_evidence WHERE finding_revision_id = :r ORDER BY evidence_id"),
            {"r": revision_id}).scalars().all()]

    def _links(self, snap, finding_id, revision_id, assessment_revision_id, evidence_ids) -> dict[str, Any]:
        q = f"?from={_cold_plain(snap['lo'])}&to={_cold_plain(snap['hi'])}&known_at={_cold_plain(snap['known'])}"
        messages = {str(k): v["message_id"] for k, v in snap.get("finding_evidence", {}).items()}
        return {
            "finding": f"/api/sites/{snap['code']}/cold/findings/{finding_id}{q}",
            "evidence": [{"evidence_id": e, "href": f"/api/sites/{snap['code']}/evidence/records/{messages[e]}{q}"
                          if e in messages else None} for e in evidence_ids],
            "analysis": {"assessment_revision_id": str(assessment_revision_id),
                         "href": f"/api/sites/{snap['code']}/assessments/{assessment_revision_id}{q}"},
        }

    def _item(self, c, snap, row, rev) -> dict[str, Any]:
        claim = rev[6] if isinstance(rev[6], dict) else json.loads(rev[6])
        limits = rev[7] if isinstance(rev[7], list) else json.loads(rev[7])
        evidence_ids = self._revision_evidence(c, rev[0])
        snap.setdefault("finding_evidence", {}).update(self._evidence(c, snap["t"], snap["s"],
                                                                      [UUID(e) for e in evidence_ids]))
        # W3-01 Run 3 q3: the row's own DTO over its exact `finding_revision_evidence`, selecting the pinned
        # `cold_episode_revision` of its claim; a missing or mismatched pinned revision refuses the read.
        if rev[15] is None or rev[16] != rev[8]:
            raise ColdPinnedLineageUnavailable("A cold Finding revision's pinned episode revision cannot be read.")
        source = self._public(c).cited_set(snap["t"], snap["s"], evidence_ids,
                                           cold_finding_row_selection(rev[0], rev[15], rev[8]))
        return {
            "finding_id": str(row[0]), "kind": claim.get("kind"), "subject_asset_id": _cold_plain(row[2]),
            "revision_id": str(rev[0]), "lifecycle": rev[3], "claim_level": rev[4], "title": rev[5],
            "state": claim.get("state"), "claim": claim,
            "episode_bounds": {"start": {"earliest": _cold_plain(rev[11]), "latest": _cold_plain(rev[12])},
                               "end": {"earliest": _cold_plain(rev[13]), "latest": _cold_plain(rev[14])}},
            "limitations": list(limits), "assessment_revision_id": str(rev[8]), "evidence_ids": evidence_ids,
            "split_from_finding_id": _cold_plain(row[3]),
            "links": self._links(snap, row[0], rev[0], rev[8], evidence_ids),
            "as_of": _cold_plain(rev[10]), "limitation": limits[0] if limits else None,
            "source_provenance": source,
        }

    def findings(self, tenant_id: UUID, site_id: UUID, code: str, lo: datetime | None, hi: datetime | None,
                 known_at: datetime | None, cursor: str | None, limit: int) -> dict[str, Any]:
        def work(c):
            snap = self._snapshot(c, tenant_id, site_id, code, lo, hi, known_at)
            body = self._envelope(c, snap, (cold.EXCURSION_ANALYTIC, cold.START_RESPONSE_ANALYTIC))
            basis = self.selected_basis(snap, (cold.EXCURSION_ANALYTIC, cold.START_RESPONSE_ANALYTIC)) or "none"
            after = None if cursor is None else decode_cursor(cursor, basis)
            if not snap["selected"]:
                return {**body, "items": [], "next_cursor": None}
            rows = self._finding_ids(c, snap, after, limit)
            page, more = rows[:limit], len(rows) > limit
            items = [self._item(c, snap, row, self._revisions(c, snap, row[0], True)[0]) for row in page]
            nxt = encode_cursor(page[-1][1], page[-1][0], basis) if more else None
            return {**body, "items": items, "next_cursor": nxt}
        return self._read(work)

    def finding(self, tenant_id: UUID, site_id: UUID, code: str, finding_id: UUID, lo: datetime | None,
                hi: datetime | None, known_at: datetime | None) -> dict[str, Any] | None:
        def work(c):
            snap = self._snapshot(c, tenant_id, site_id, code, lo, hi, known_at)
            body = self._envelope(c, snap, (cold.EXCURSION_ANALYTIC, cold.START_RESPONSE_ANALYTIC))
            if snap["lo"] is None:
                return None
            rows = self._finding_ids(c, snap, None, None, finding_id)
            if not rows:
                return None
            revisions = self._revisions(c, snap, finding_id, False)
            item = self._item(c, snap, rows[0], revisions[0])
            claim = item["claim"]
            history = [{"revision_id": str(r[0]), "revision_no": r[1], "transition": r[2], "lifecycle": r[3],
                        "claim_level": r[4], "basis_sha256": r[9], "created_at": _cold_plain(r[10]),
                        "evidence_ids": self._revision_evidence(c, r[0]), "as_of": _cold_plain(r[10]),
                        "limitation": None} for r in revisions]
            # W3-01 Run 3 q2: the envelope is spread, then only its top-level `source_provenance` is the row DTO
            # (from `item`); the siblings stay the window blocks and the stored basis keeps its own field.
            return {**body, **item, "basis_sha256": revisions[0][9], "episode_id": claim.get("episode_id"),
                    "episode_revision_id": claim.get("episode_revision_id"), "revisions": history}
        return self._read(work)


    # --- W2-04 commit 3: caller-connection reads for `analytics/cold_site_reads.py` ---------------------------
    # `.agent/W2-04-build-spec.md` "Five API reads" and "How does the API keep one snapshot?": the Site read
    # composes every part on the one REPEATABLE READ connection `within` opens. All SELECT-only.

    def within(self, work: Callable[[Connection], Any]) -> Any:
        """Run `work(c)` in one REPEATABLE READ transaction; a store failure is `ColdReadUnavailable` (503)."""
        return self._read(work)

    def selection_on(self, c: Connection, t: UUID, s: UUID, code: str, lo: datetime | None, hi: datetime | None,
                     known_at: datetime | None) -> dict[str, Any]:
        return self._snapshot(c, t, s, code, lo, hi, known_at)

    def envelope_on(self, c: Connection, snap: dict[str, Any], analytics: tuple[str, ...]) -> dict[str, Any]:
        return self._envelope(c, snap, analytics)

    def consequence_provenance_on(self, c: Connection, snap: dict[str, Any], head: dict[str, Any]) -> dict[str, Any]:
        """W3-01 Run 3 q3: one cold consequence row's DTO: its stored evidence IDs union its pinned FindingRevision's
        exact citations, selecting `{consequence, Finding, episode, assessment}` revisions. The pinned Finding
        must be this Site's, of that assessment and episode; otherwise the read is refused (unavailable)."""
        t, s = snap["t"], snap["s"]
        pinned = c.execute(text(
            "SELECT r.id FROM finding_revision r JOIN cold_episode_revision er ON er.tenant_id = r.tenant_id "
            "AND er.site_id = r.site_id AND er.id = CAST(r.claim->>'episode_revision_id' AS uuid) "
            "WHERE r.tenant_id = :t AND r.site_id = :s AND r.id = :f AND r.assessment_revision_id = :a "
            "AND er.id = :e AND er.assessment_revision_id = :a"),
            {"t": t, "s": s, "f": UUID(str(head["finding_revision_id"])),
             "a": UUID(str(head["assessment_revision_id"])), "e": UUID(str(head["episode_revision_id"]))}).first()
        if pinned is None:
            raise ColdPinnedLineageUnavailable("A cold consequence's pinned Finding revision cannot be read.")
        cited = {str(x) for x in head["evidence_ids"] or ()} | set(self._revision_evidence(c, pinned[0]))
        return self._public(c).cited_set(t, s, sorted(cited), cold_consequence_row_selection(
            head["id"], head["finding_revision_id"], head["episode_revision_id"], head["assessment_revision_id"]))

    def temperature_on(self, c: Connection, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        return self._temperature(c, t, s, code, lo, hi, known_at)

    def backup_on(self, c: Connection, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        return self._backup(c, t, s, code, lo, hi, known_at)

    def current_findings_on(self, c: Connection, snap: dict[str, Any]) -> list[dict[str, Any]]:
        """Every cold Finding of the selected window, each at its latest revision known at the cutoff."""
        if snap["lo"] is None or snap["known"] is None or not snap["selected"]:
            return []
        return [self._item(c, snap, row, self._revisions(c, snap, row[0], True)[0])
                for row in self._finding_ids(c, snap, None, None)]

    @staticmethod
    def basis_revisions_on(c: Connection, t: UUID, s: UUID, assessment_revision_id: UUID) -> dict[str, Any]:
        """The selected assessment revision's `created_at`, its run's Foundation revisions (`id, valid_from,
        valid_to`) and its run's bound channels (`source_id, role, gateway_id`; a cold run stores its exact
        `signal_binding_revision` IDs in `binding_set_revision_ids`), by exact stored IDs."""
        row = c.execute(text(
            "SELECT ar.created_at, r.foundation_revision_ids, r.binding_set_revision_ids FROM assessment_revision ar "
            "JOIN analytic_run_assessment x ON x.assessment_revision_id = ar.id JOIN analytic_run r ON r.id = x.run_id "
            "WHERE ar.tenant_id = :t AND ar.site_id = :s AND ar.id = :a ORDER BY r.knowledge_cutoff DESC LIMIT 1"),
            {"t": t, "s": s, "a": assessment_revision_id}).first()
        if row is None:
            return {"created_at": None, "foundations": [], "bindings": []}
        foundation_ids = row[1] if isinstance(row[1], list) else json.loads(row[1])
        binding_set_ids = row[2] if isinstance(row[2], list) else json.loads(row[2])
        foundations = c.execute(text(
            "SELECT id, valid_from, valid_to FROM foundation_revision WHERE tenant_id = :t AND site_id = :s "
            "AND id = ANY(:ids) ORDER BY valid_from, id"),
            {"t": t, "s": s, "ids": [UUID(str(i)) for i in foundation_ids]}).all()
        bindings = c.execute(text(
            "SELECT DISTINCT source_id, role, gateway_id FROM signal_binding_revision WHERE tenant_id = :t "
            "AND site_id = :s AND id = ANY(:ids) ORDER BY role, source_id"),
            {"t": t, "s": s, "ids": [UUID(str(i)) for i in binding_set_ids]}).all()
        return {"created_at": row[0], "foundations": [tuple(f) for f in foundations],
                "bindings": [tuple(b) for b in bindings]}

    #: W5-01 C1 Health: the Foundation component types a Health row reads (`.agent/W5-01-build-spec.md` Q7).
    HEALTH_COMPONENT_TYPES = ("GENERATOR", "COMPRESSOR", "TEMPERATURE_PROBE")

    def foundation_on(self, c: Connection, snap: dict[str, Any]) -> dict[str, Any] | None:
        """W5-01 C1 Q7: the selected Foundation revision and its Health components on the caller connection.
        With a selection, the one distinct Foundation revision of every selected analytic's run; without one, the
        one revision known at the cutoff that overlaps the window (the `cold_inputs` predicate). Anything else is
        None. Components are `GENERATOR`/`COMPRESSOR`/`TEMPERATURE_PROBE` entries that have a same-code,
        same-type Site asset row, sorted `(component_type, asset_code)`. SELECT-only."""
        t, s = snap["t"], snap["s"]
        if snap["selected"]:
            ids = {str(f[0]).lower() for sel in snap["selected"].values()
                   for f in self.basis_revisions_on(c, t, s, sel.revision_id)["foundations"]}
            if len(ids) != 1:
                return None
            found = c.execute(text("SELECT id, content FROM foundation_revision WHERE tenant_id = :t "
                                   "AND site_id = :s AND id = :f"), {"t": t, "s": s, "f": UUID(ids.pop())}).all()
        else:
            if snap["known"] is None or snap["lo"] is None or snap["hi"] is None:
                return None
            found = c.execute(text(
                f"SELECT id, content FROM foundation_revision WHERE tenant_id = :t AND site_id = :s "
                f"AND {_KNOWN} AND {_OVERLAPS}"),
                {"t": t, "s": s, "k": snap["known"], "lo": snap["lo"], "hi": snap["hi"]}).all()
        if len(found) != 1:
            return None
        revision_id, content = found[0]
        content = content if isinstance(content, dict) else json.loads(content)
        assets = {(r[1], r[2]): str(r[0]).lower() for r in c.execute(text(
            "SELECT id, asset_code, asset_type FROM asset WHERE tenant_id = :t AND site_id = :s"),
            {"t": t, "s": s}).all()}
        components = []
        for comp in content.get("components") or ():
            kind, code = comp.get("component_type"), comp.get("component_id")
            if kind in self.HEALTH_COMPONENT_TYPES and (code, kind) in assets:
                components.append({"component_type": kind, "asset_id": assets[(code, kind)], "asset_code": code,
                                   "display_name": comp.get("display_name") or None})
        # Q13: the one returned probe at the `to_node` of a SIGNAL edge from a COLD_ROOM component, else None.
        topology = content.get("topology") or {}
        node_comp = {n.get("node_id"): n.get("component_id") for n in topology.get("nodes") or ()}
        kinds = {x.get("component_id"): x.get("component_type") for x in content.get("components") or ()}
        probes = {x["asset_code"]: x["asset_id"] for x in components if x["component_type"] == "TEMPERATURE_PROBE"}
        chamber = {node_comp.get(e.get("to_node")) for e in topology.get("connections") or ()
                   if e.get("medium") == "SIGNAL" and kinds.get(node_comp.get(e.get("from_node"))) == "COLD_ROOM"
                   and node_comp.get(e.get("to_node")) in probes}
        return {"revision_id": str(revision_id).lower(),
                "components": sorted(components, key=lambda x: (x["component_type"], x["asset_code"])),
                "chamber_probe_asset_id": probes[next(iter(chamber))] if len(chamber) == 1 else None}

    @staticmethod
    def accepted_on(c: Connection, t: UUID, s: UUID, ids: list[str], after: tuple[datetime, UUID] | None = None,
                    limit: int | None = None) -> list[dict[str, Any]]:
        """Exact accepted public records by stored ID, ordered `(source_time, id)`, paged after the tuple."""
        if not ids:
            return []
        sql = ("SELECT id, record_kind, source_time, received_at, published_at, quality, role, source_id, "
               "envelope_sha256, normalized_value_text, normalized_unit, outcome FROM accepted_evidence "
               "WHERE tenant_id = :t AND site_id = :s AND id = ANY(:ids) ")
        p: dict[str, Any] = {"t": t, "s": s, "ids": sorted({UUID(str(i)) for i in ids}, key=str)}
        if after is not None:
            sql += "AND (source_time, id) > (:at, :aid) "
            p.update(at=after[0], aid=after[1])
        sql += "ORDER BY source_time, id"
        if limit is not None:
            sql += " LIMIT :n"
            p["n"] = limit + 1
        names = ("id", "record_kind", "source_time", "received_at", "published_at", "quality", "role", "source_id",
                 "envelope_sha256", "normalized_value_text", "normalized_unit", "outcome")
        return [dict(zip(names, r)) for r in c.execute(text(sql), p).all()]

    @staticmethod
    def accepted_count_on(c: Connection, t: UUID, s: UUID, ids: list[str]) -> int:
        """How many of the stored IDs are accepted public records: the full selected count behind the paged list."""
        if not ids:
            return 0
        return int(c.execute(text(
            "SELECT count(*) FROM accepted_evidence WHERE tenant_id = :t AND site_id = :s AND id = ANY(:ids)"),
            {"t": t, "s": s, "ids": sorted({UUID(str(i)) for i in ids}, key=str)}).scalar_one())

    @staticmethod
    def source_facts_on(c: Connection, t: UUID, s: UUID, lo: datetime, hi: datetime,
                        known: datetime) -> dict[tuple[UUID, str], tuple[int, datetime, int]]:
        """(source_id, role) -> (accepted count, latest `source_time`, GOOD-quality count) of the accepted records
        in `[lo, hi)` whose disposition was committed at or before the cutoff (Run-5 copy-source closure)."""
        rows = c.execute(text(
            "SELECT e.source_id, e.role, count(*), max(e.source_time), "
            "count(*) FILTER (WHERE e.quality = 'GOOD') FROM accepted_evidence e "
            "JOIN ingestion_disposition d ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal "
            "WHERE e.tenant_id = :t AND e.site_id = :s AND e.source_time >= :lo AND e.source_time < :hi "
            "AND d.decided_at <= :k GROUP BY e.source_id, e.role"),
            {"t": t, "s": s, "lo": lo, "hi": hi, "k": known}).all()
        return {(r[0], r[1]): (int(r[2]), r[3], int(r[4])) for r in rows}

    @staticmethod
    def source_contacts_on(c: Connection, t: UUID, s: UUID, gateway_ids: list[UUID],
                           cutoff: datetime) -> dict[UUID, dict[str, Any]]:
        """Commit-3 Architect ruling (source contact): per registered gateway, its latest diagnostic received at or
        before `cutoff` (`min(known_at, to)`), in the S2 order (received_at, then sequence), with the gateway's
        declared diagnostic cadence. A gateway with no such diagnostic is absent from the result."""
        if not gateway_ids:
            return {}
        rows = c.execute(text(
            "SELECT DISTINCT ON (d.gateway_id) d.gateway_id, d.id, d.received_at, d.last_device_contact_by_source, "
            "d.clock_offset_ms, g.diagnostic_cadence_seconds FROM gateway_diagnostic d JOIN gateway g "
            "ON g.tenant_id = d.tenant_id AND g.site_id = d.site_id AND g.id = d.gateway_id "
            "WHERE d.tenant_id = :t AND d.site_id = :s AND d.gateway_id = ANY(:g) AND d.received_at <= :k "
            "ORDER BY d.gateway_id, d.received_at DESC, d.diagnostic_sequence DESC"),
            {"t": t, "s": s, "g": sorted(set(gateway_ids), key=str), "k": cutoff}).all()
        out = {}
        for r in rows:
            contacts = r[3] if isinstance(r[3], dict) else json.loads(r[3])
            out[r[0]] = {"diagnostic_id": r[1], "received_at": r[2], "contacts": contacts,
                         "clock_offset_ms": r[4], "cadence_seconds": r[5]}
        return out


# --- W2-06 commit 4: the selected EV session and Finding read (read-only; rules in `analytics/ev_reads.py`) -----
# One REPEATABLE READ, READ ONLY transaction per request: the committed disposition watermark, the resolved cutoff,
# the selected `ev-session/1` assessment of the exact window, its stored Q14 result and session revisions, their
# links, the Finding revisions of that assessment and the overlapping PENDING/LEASED/FAILED `ev_charging` jobs.


_ev_plain = ev.plain


def _ev_rows(c: Connection, p: dict[str, Any]) -> list:
    """The accepted rows of one EV window at the cutoff `p['k']` (`ev_inputs`, and the r9 M1-a read classification
    of exactly the same accepted set): every accepted row touching `[lo,hi)`, plus the r8 H1 late same-session
    terminals/faults of a START inside it."""
    lo, hi = p["lo"], p["hi"]
    rows = c.execute(text(
        "SELECT e.id, e.envelope_sha256, e.source_time, e.interval_start, e.interval_end, e.connector_id, "
        "e.session_id, e.family, e.record_kind, e.measurement, e.quality, e.normalized_value_text, "
        "e.normalized_unit, e.event_id, e.outcome, e.asset_id, e.binding_revision_id, e.source_id, "
        "e.sequence_epoch, e.binding_set_revision_id, e.role, e.device_id, e.signal_id "
        "FROM accepted_evidence e JOIN ingestion_disposition d ON d.batch_id = e.batch_id "
        "AND d.accepted_evidence_id = e.id AND d.decision = 'ACCEPTED' "
        "WHERE e.tenant_id = :t AND e.site_id = :s AND COALESCE(e.interval_start, e.source_time) < :hi "
        "AND (CASE WHEN e.interval_end IS NULL THEN e.source_time >= :lo ELSE e.interval_end > :lo END) "
        "AND e.received_at <= :k AND d.decided_at <= :k ORDER BY e.source_time, e.id"), p).all()
    # r8 H1: the full scoped session extent anchored by a START inside the window. A same-session terminal
    # (or fault) outside the window is correlation input for that START; sessions STARTing outside the window
    # stay context and never enter its denominator (ev.assess counts only STARTs and orphans inside it).
    anchored = sorted({(r[15], r[6]) for r in rows if r[7] == "EVENT" and r[8] == ev.START
                       and r[6] is not None and lo <= r[2] < hi and r[15] is not None})
    if anchored:
        held = {r[0] for r in rows}
        late = c.execute(text(
            "SELECT e.id, e.envelope_sha256, e.source_time, e.interval_start, e.interval_end, e.connector_id, "
            "e.session_id, e.family, e.record_kind, e.measurement, e.quality, e.normalized_value_text, "
            "e.normalized_unit, e.event_id, e.outcome, e.asset_id, e.binding_revision_id, e.source_id, "
            "e.sequence_epoch, e.binding_set_revision_id, e.role, e.device_id, e.signal_id "
            "FROM accepted_evidence e JOIN ingestion_disposition d ON d.batch_id = e.batch_id "
            "AND d.accepted_evidence_id = e.id AND d.decision = 'ACCEPTED' "
            "WHERE e.tenant_id = :t AND e.site_id = :s AND e.family = 'EVENT' "
            "AND e.record_kind IN ('EV_SESSION_END', 'EV_SESSION_ABORT', 'EV_CONNECTOR_FAULT') "
            "AND e.source_time >= :hi AND e.received_at <= :k AND d.decided_at <= :k "
            "AND (e.asset_id, e.session_id) IN (SELECT * FROM unnest(CAST(:assets AS uuid[]), "
            "CAST(:sessions AS text[]))) ORDER BY e.source_time, e.id"),
            {**p, "assets": [str(x[0]) for x in anchored], "sessions": [x[1] for x in anchored]}).all()
        rows = list(rows) + [r for r in late if r[0] not in held]
    return list(rows)


def _ev_link_class(link: Any) -> str | None:
    """r8 M1: a record's own S4-05 class: its BOUND publication class, else None (never a set state)."""
    return link.source_class if link is not None and link.status == "BOUND" else None


def _ev_json(value: Any) -> Any:
    return json.loads(value) if isinstance(value, str) else value


class EvReadService:
    def __init__(self, database_url: str | None = None, *, engine=None,
                 clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
                 link_rows: Callable[..., list] | None = None) -> None:
        self._url, self._engine, self.clock = database_url, engine, clock
        # r9 M1-a: the S4-05 scoped link reader on the read connection (`evidence.composition`).
        self._link_rows = link_rows

    def _connect(self):
        if self._engine is None:
            self._engine = create_engine(self._url, pool_pre_ping=True)
        return self._engine.connect().execution_options(isolation_level="REPEATABLE READ")

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()

    def _read(self, work: Callable[[Connection], Any]) -> Any:
        try:
            with self._connect() as c, c.begin():
                c.execute(text("SET TRANSACTION READ ONLY"))
                return work(c)
        except (OperationalError, DBAPIError) as error:
            raise EvReadUnavailable(f"The EV assessment store is unavailable: {error.__class__.__name__}") from error

    # --- the one snapshot --------------------------------------------------------------------------------------

    def _snapshot(self, c: Connection, t: UUID, s: UUID, code: str, lo: datetime | None, hi: datetime | None,
                  known_at: datetime | None, *, selection_cutoff: datetime | None = None,
                  selection_seqs: dict[str, int] | None = None) -> dict[str, Any]:
        """The EV read snapshot on the caller's `c` (never a connection or transaction of its own). Default: the W2
        Site selection, unchanged. Pinned mode (W3-01 Run 6 Blocker 1, W4-01 Run 3 ruling 6): `lo`/`hi` are one
        exact stored selected window and `selection_seqs` maps the session analytic to its exact selected seq; the
        row must be selected, its run completed and its revision created by `selection_cutoff`, or
        `SelectionPinRefused`. The snapshot then also carries `selection_seqs`."""
        if selection_seqs is not None and selection_cutoff is None:
            raise ValueError("selection_seqs requires selection_cutoff: a pin without a cutoff is never read unpinned.")
        pinned = selection_cutoff is not None
        if pinned and (lo is None or hi is None or ev.SESSION_ANALYTIC not in (selection_seqs or {})):
            raise ValueError("A pinned EV selection needs its exact stored window and the session analytic's seq.")
        p = {"t": t, "s": s, "a": ev.SESSION_ANALYTIC}
        watermark = c.execute(text("SELECT max(decided_at) FROM ingestion_disposition WHERE tenant_id = :t "
                                   "AND site_id = :s"), p).scalar()
        if known_at is not None and watermark is not None and known_at > watermark:
            raise EvReadRefused(422, "EV_TIME_INVALID",
                                "'known_at' is later than the latest committed evidence cutoff.")
        known = known_at or watermark
        if pinned and known is None:
            raise SelectionPinRefused(ev.SESSION_ANALYTIC, selection_seqs[ev.SESSION_ANALYTIC], lo, hi,
                                      selection_cutoff)
        if lo is None and known is not None:  # the paired default: the latest selected EV window at the cutoff
            row = c.execute(text(
                "SELECT sel.window_start, sel.window_end FROM analytic_run_selection sel JOIN analytic_run r "
                "ON r.id = sel.run_id WHERE sel.tenant_id = :t AND sel.site_id = :s AND sel.analytic_id = :a "
                "AND r.knowledge_cutoff <= :k ORDER BY sel.seq DESC LIMIT 1"), {**p, "k": known}).first()
            if row is not None:
                lo, hi = row[0], row[1]
        selected = None
        if pinned and known is not None:
            selected = c.execute(text(
                "SELECT ar.id, ar.revision_no, ar.basis_sha256, ar.result, ar.evidence_ids, ar.created_at, "
                "ar.claim_level, r.id, r.knowledge_cutoff, r.foundation_revision_ids FROM analytic_run_selection sel "
                "JOIN analytic_run r ON r.id = sel.run_id AND r.tenant_id = sel.tenant_id AND r.site_id = sel.site_id "
                "JOIN analytic_run_assessment x ON x.run_id = r.id "
                "JOIN assessment_revision ar ON ar.id = x.assessment_revision_id WHERE sel.tenant_id = :t "
                "AND sel.site_id = :s AND sel.analytic_id = :a AND sel.window_start = :lo AND sel.window_end = :hi "
                "AND sel.seq = :seq AND sel.selected_at <= :sk AND r.completed_at <= :sk AND ar.created_at <= :sk "
                "AND r.knowledge_cutoff <= :k LIMIT 1"),
                {**p, "lo": lo, "hi": hi, "k": known, "seq": selection_seqs[ev.SESSION_ANALYTIC],
                 "sk": selection_cutoff}).first()
            if selected is None:
                raise SelectionPinRefused(ev.SESSION_ANALYTIC, selection_seqs[ev.SESSION_ANALYTIC], lo, hi,
                                          selection_cutoff)
        elif lo is not None and known is not None:
            selected = c.execute(text(
                "SELECT ar.id, ar.revision_no, ar.basis_sha256, ar.result, ar.evidence_ids, ar.created_at, "
                "ar.claim_level, r.id, r.knowledge_cutoff, r.foundation_revision_ids FROM analytic_run_selection sel "
                "JOIN analytic_run r ON r.id = sel.run_id JOIN analytic_run_assessment x ON x.run_id = r.id "
                "JOIN assessment_revision ar ON ar.id = x.assessment_revision_id WHERE sel.tenant_id = :t "
                "AND sel.site_id = :s AND sel.analytic_id = :a AND sel.window_start = :lo AND sel.window_end = :hi "
                "AND r.knowledge_cutoff <= :k ORDER BY sel.seq DESC LIMIT 1"),
                {**p, "lo": lo, "hi": hi, "k": known}).first()
        # W3-01 Run 3 q1: the overlapping job is read whenever the window exists, with or without a selected head;
        # it gates only the public pending block when nothing is selected (currentness is unchanged).
        historical = known_at is not None and watermark is not None and known_at < watermark
        job = False
        if lo is not None and not historical and known is not None:
            job = c.execute(text(
                "SELECT EXISTS (SELECT 1 FROM recompute_job WHERE tenant_id = :t AND site_id = :s "
                "AND domain = 'ev_charging' AND status IN ('PENDING', 'LEASED', 'FAILED') AND window_start < :hi "
                "AND window_end > :lo AND (CAST(:k AS timestamptz) IS NULL OR created_at <= :k))"), {**p, "lo": lo, "hi": hi, "k": known_at}).scalar_one()
        pending = selected is not None and job
        state = _ev_currentness_state(selected=selected is not None, pending=pending, historical=historical)
        note = {"UNKNOWN": _EV_NO_SELECTION_NOTE, "PENDING_RECOMPUTE": _EV_PENDING_NOTE,
                "HISTORICAL": _EV_HISTORICAL_NOTE}.get(state)
        # r9 M1-a: with no exact head, or a pending one, classify exactly the window's accepted EV set at the
        # cutoff with the worker's S4-05 classifier; a MIXED/UNKNOWN non-empty set is the unassessable source.
        unassessable = None
        if lo is not None and known is not None and (selected is None or pending):
            unassessable = self._unassessable(c, t, s, lo, hi, known)
        if unassessable is not None and selected is None:
            note = ev.SOURCE_UNASSESSABLE
        snap: dict[str, Any] = {"code": code, "t": t, "s": s, "lo": lo, "hi": hi, "known": known,
                                "watermark": watermark, "state": state, "note": note, "selected": None,
                                "unassessable": unassessable, "job": job}
        if selected is not None:
            result = _ev_json(selected[3])
            snap["selected"] = {
                "revision_id": selected[0], "revision_no": selected[1], "basis": selected[2], "result": result,
                "evidence_ids": sorted(str(x).lower() for x in _ev_json(selected[4])), "created_at": selected[5],
                "claim_level": selected[6], "run_id": selected[7], "cutoff": selected[8],
                "foundation_ids": list(_ev_json(selected[9]) or ())}
        if pinned:
            snap["selection_seqs"] = {ev.SESSION_ANALYTIC: int(selection_seqs[ev.SESSION_ANALYTIC])}
            snap["selection_cutoff"] = selection_cutoff
        return snap

    def estate_snapshots_on(self, c: Connection, t: UUID, s: UUID, code: str, from_: datetime, to: datetime,
                            known_at: datetime | None, selection_cutoff: datetime) -> list[dict[str, Any]]:
        """W3-01 Run 6 Blocker 1: one pinned `_snapshot` per exact stored EV session window whose as-of selection
        intersects `[from_, to)`, ordered by `(window_start, window_end)`; empty when nothing qualifies.
        `known_at` is the caller's clamped Site cutoff (at or before the Site's evidence watermark)."""
        if known_at is None:  # Run 7 q7-1: no provable evidence basis is UNKNOWN, never a current zero
            return []
        keys = selected_windows_on(c, t, s, (ev.SESSION_ANALYTIC,), from_, to, selection_cutoff,
                                   evidence_cutoff=known_at)
        return [self._snapshot(c, t, s, code, k["window_start"], k["window_end"], known_at,
                               selection_cutoff=selection_cutoff, selection_seqs={k["analytic_id"]: k["seq"]})
                for k in keys]

    def _unassessable(self, c: Connection, t: UUID, s: UUID, lo: datetime, hi: datetime,
                      known: datetime) -> dict[str, Any] | None:
        """The S4-05 classification of the window's accepted EV set when it is non-empty and neither positive
        class (else None). A failed scoped link query is 503 `EV_READ_UNAVAILABLE`, never a guessed UNKNOWN."""
        rows = _ev_rows(c, {"t": t, "s": s, "k": known, "lo": lo, "hi": hi})
        ids = sorted({str(r[0]).lower() for r in rows})
        if not ids:
            return None
        if self._link_rows is None:
            raise EvReadUnavailable("The EV source provenance reader is unavailable.")
        try:
            links = {row.requested_id: link_of(row) for row in self._link_rows(c, t, s, ids)}
        except (OperationalError, DBAPIError):
            raise
        except Exception as error:  # noqa: BLE001 - any failed link read is unavailable, never a guess
            raise EvReadUnavailable(f"The EV source provenance read failed: {error.__class__.__name__}") from error
        whole = classify(ids, links)
        if whole["state"] in ev.ASSESSABLE_CLASSES:
            return None
        return {"classification": whole["state"], "evidence_ids": ids,
                "source_ids": sorted({str(r[17]).lower() for r in rows if r[17] is not None}),
                "reasons": [{"code": r["code"], "accepted_evidence_ids": list(r["accepted_evidence_ids"])}
                            for r in whole["reasons"]]}

    def _query(self, snap: dict[str, Any]) -> str:
        return f"?from={_ev_plain(snap['lo'])}&to={_ev_plain(snap['hi'])}&known_at={_ev_plain(snap['known'])}"

    def _public(self, c: Connection) -> PublicProvenance:
        """W3-01: the public DTO resolver bound to this read connection (set reads only)."""
        if self._link_rows is None:
            raise EvReadUnavailable("The EV source provenance reader is unavailable.")
        return PublicProvenance(LinkRowsReads(_bound_link_rows(c, self._link_rows, EvReadUnavailable)))

    def _provenance_blocks(self, c: Connection, snap: dict[str, Any]) -> dict[str, Any]:
        """W3-01 Run 1 rulings 4-5, Run 2-3 q1: the selected head's `ev_selected` block (the stored result is not
        mutated) and, with an overlapping job, the pending block over every `_ev_rows` ID of the window."""
        sel, t, s = snap["selected"], snap["t"], snap["s"]
        public = self._public(c)
        selected = None if sel is None else public.ev_selected(
            t, s, sel["evidence_ids"],
            ev_envelope_selection(sel["revision_id"], sel["result"].get("session_revision_ids") or ()),
            (sel["result"].get("source_provenance") or {}).get("class"))
        pending = None
        if snap.get("job"):
            ids = sorted({str(r[0]).lower() for r in _ev_rows(
                c, {"t": t, "s": s, "lo": snap["lo"], "hi": snap["hi"], "k": snap["known"]})})
            pending = public.cited_set(t, s, ids, [])
        return dual_blocks(selected, pending)

    def money_row_provenance_on(self, c: Connection, snap: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
        """W3-01 Run 4 q4 ruling 1: one stored EV consequence row's own DTO. Selects `{row id, its stored
        assessment, every linked session revision}` and cites only its `ev_consequence_evidence` set. The stored
        assessment and each linked session revision (naming that assessment) must exist in this tenant/Site; a
        non-null Finding pin is outside the reviewed W2-07 row contract. Either fails closed as unavailable."""
        t, s = snap["t"], snap["s"]
        if row.get("finding_revision_id") is not None:
            raise EvPinnedLineageUnavailable("An EV consequence revision has an unreviewed Finding pin.")
        ar = row["assessment_revision_id"]
        if c.execute(text("SELECT 1 FROM assessment_revision WHERE tenant_id = :t AND site_id = :s AND id = :ar"),
                     {"t": t, "s": s, "ar": ar}).first() is None:
            raise EvPinnedLineageUnavailable("An EV consequence revision's stored assessment cannot be read.")
        sessions = sorted({str(x).lower() for x in row["session_revision_ids"]})
        if sessions:
            found = c.execute(text(
                "SELECT count(*) FROM ev_session_revision WHERE tenant_id = :t AND site_id = :s "
                "AND assessment_revision_id = :ar AND id = ANY(CAST(:ids AS uuid[]))"),
                {"t": t, "s": s, "ar": ar, "ids": sessions}).scalar_one()
            if found != len(sessions):
                raise EvPinnedLineageUnavailable("An EV consequence revision's linked session revision cannot be read.")
        selected = sorted({str(row["id"]).lower(), str(ar).lower(), *sessions})
        return self._public(c).cited_set(t, s, sorted({str(x).lower() for x in row["evidence_ids"]}), selected)

    def _envelope(self, c: Connection, snap: dict[str, Any]) -> dict[str, Any]:
        sel = snap["selected"]
        blocks = self._provenance_blocks(c, snap)
        bad = snap.get("unassessable")
        if bad is not None and sel is None:  # r9 M1-a: no exact head; `_unassessable` supplies only the limitation
            return {
                "site_id": str(snap["s"]).lower(),
                "window": {"from": _ev_plain(snap["lo"]), "to": _ev_plain(snap["hi"]),
                           "known_at": _ev_plain(snap["known"])},
                "currentness": {"state": snap["state"], "as_of": None, "limitation": snap["note"]},
                **blocks,
                "limitations": [ev.SOURCE_UNASSESSABLE],
            }
        return {
            "site_id": str(snap["s"]).lower(),
            "window": {"from": _ev_plain(snap["lo"]), "to": _ev_plain(snap["hi"]), "known_at": _ev_plain(snap["known"])},
            "currentness": {"state": snap["state"], "as_of": None if sel is None else _ev_plain(sel["created_at"]),
                            "limitation": snap["note"]},
            **blocks,
            "limitations": ([] if sel is None else list(sel["result"].get("limitations") or ()))
            + ([snap["note"]] if snap["note"] else []) + ([ev.SOURCE_UNASSESSABLE] if bad is not None else []),
        }

    @staticmethod
    def _status(snap: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        sel = snap["selected"]
        if sel is None:
            note = ev.SOURCE_UNASSESSABLE if snap.get("unassessable") is not None else _EV_NO_SELECTION_NOTE
            return ({"state": "UNKNOWN", "claim_level": "UNKNOWN", "as_of": None, "limitation": note},
                    {**{k: None for k in _EV_COUNT_KEYS}, "as_of": None, "limitation": note})
        status, counts = sel["result"]["status"], sel["result"]["denominator"]
        return ({k: status.get(k) for k in ("state", "claim_level", "as_of", "limitation")},
                {**{k: counts.get(k) for k in _EV_COUNT_KEYS}, "as_of": counts.get("as_of"),
                 "limitation": counts.get("limitation")})

    # --- sessions ----------------------------------------------------------------------------------------------

    def _sessions(self, c: Connection, snap: dict[str, Any], session_id: UUID | None = None) -> list[dict[str, Any]]:
        sel = snap["selected"]
        if sel is None:
            return []
        ids = list(sel["result"].get("session_revision_ids") or ())
        if not ids:
            return []
        sql = ("SELECT e.id, e.external_session_id, e.charger_asset_id, e.connector_asset_id, v.id, v.revision_no, "
               "v.basis_sha256, v.state, v.start_at, v.end_at, v.start_earliest, v.start_latest, v.end_earliest, "
               "v.end_latest, v.supported_kwh, v.unknown_meter_seconds, v.fault_evidence_id, v.reason_codes, "
               "a.asset_code FROM ev_session_revision v JOIN ev_session e ON e.tenant_id = v.tenant_id "
               "AND e.site_id = v.site_id AND e.id = v.session_id JOIN asset a ON a.tenant_id = e.tenant_id "
               "AND a.site_id = e.site_id AND a.id = e.connector_asset_id WHERE v.tenant_id = :t AND v.site_id = :s "
               "AND v.id = ANY(CAST(:ids AS uuid[])) ")
        p: dict[str, Any] = {"t": snap["t"], "s": snap["s"], "ids": ids}
        if session_id is not None:
            sql += "AND e.id = :e "
            p["e"] = session_id
        rows = c.execute(text(sql + "ORDER BY v.start_at, e.id"), p).all()
        findings = {claim_session: fid for fid, claim_session in c.execute(text(
            "SELECT f.id, fr.claim->>'session_id' FROM finding_revision fr JOIN finding f ON f.tenant_id = "
            "fr.tenant_id AND f.site_id = fr.site_id AND f.id = fr.finding_id WHERE fr.tenant_id = :t "
            "AND fr.site_id = :s AND f.domain = 'ev_charging' AND fr.assessment_revision_id = :ar "
            "AND fr.lifecycle = 'SUPPORTED'"), {"t": snap["t"], "s": snap["s"], "ar": sel["revision_id"]}).all()}
        names = self._display_names(c, snap)
        q = self._query(snap)
        # r8 M2: completeness from the exact selected revisions' uses, in the same read snapshot.
        revision_ids = [r[4] for r in rows]
        # W3-01 Run 3 q3: each session revision cites every `ev_session_evidence` and `ev_meter_interval` row of
        # that revision (no use, reason or page filter).
        cited: dict[Any, set[str]] = {x: set() for x in revision_ids}
        if revision_ids:
            for rid, evidence_id in c.execute(text(
                    "SELECT revision_id, evidence_id FROM ev_session_evidence WHERE tenant_id = :t AND site_id = :s "
                    "AND revision_id = ANY(CAST(:ids AS uuid[])) UNION SELECT revision_id, evidence_id "
                    "FROM ev_meter_interval WHERE tenant_id = :t AND site_id = :s "
                    "AND revision_id = ANY(CAST(:ids AS uuid[])) AND evidence_id IS NOT NULL"),
                    {"t": snap["t"], "s": snap["s"], "ids": [str(x) for x in revision_ids]}).all():
                cited[rid].add(str(evidence_id).lower())
        public = self._public(c)
        uses: dict[Any, list] = {x: [] for x in revision_ids}
        meters: dict[Any, list] = {x: [] for x in revision_ids}
        if revision_ids:
            for rid, kind, use, why in c.execute(text(
                    "SELECT x.revision_id, CASE WHEN e.family = 'EVENT' THEN e.record_kind END, x.use, x.reason "
                    "FROM ev_session_evidence x JOIN accepted_evidence e ON e.tenant_id = x.tenant_id "
                    "AND e.site_id = x.site_id AND e.id = x.evidence_id WHERE x.tenant_id = :t AND x.site_id = :s "
                    "AND x.revision_id = ANY(CAST(:ids AS uuid[]))"),
                    {"t": snap["t"], "s": snap["s"], "ids": [str(x) for x in revision_ids]}).all():
                uses[rid].append((kind, use, why))
            for rid, use, why in c.execute(text(
                    "SELECT revision_id, use, reason FROM ev_meter_interval WHERE tenant_id = :t AND site_id = :s "
                    "AND revision_id = ANY(CAST(:ids AS uuid[]))"),
                    {"t": snap["t"], "s": snap["s"], "ids": [str(x) for x in revision_ids]}).all():
                meters[rid].append((use, why))
        items = []
        for r in rows:
            reasons = list(_ev_json(r[17]) or ())
            fid = findings.get(str(r[0]).lower())
            items.append({
                "session_id": _ev_plain(r[0]), "external_session_id": r[1], "charger_asset_id": _ev_plain(r[2]),
                "connector_asset_id": _ev_plain(r[3]), "connector_display_name": names.get(r[18]),
                "revision_id": _ev_plain(r[4]), "revision_no": r[5], "basis_sha256": r[6], "state": r[7],
                "start_at": _ev_plain(r[8]), "end_at": _ev_plain(r[9]),
                "start_bounds": {"earliest": _ev_plain(r[10]), "latest": _ev_plain(r[11])},
                "end_bounds": {"earliest": _ev_plain(r[12]), "latest": _ev_plain(r[13])},
                "supported_kwh": _ev_plain(r[14]), "energy_complete": _ev_energy_complete(r[7], r[14], r[15]),
                "unknown_meter_seconds": r[15], "reason_codes": reasons, "fault_evidence_id": _ev_plain(r[16]),
                "finding_id": _ev_plain(fid), "completeness": _ev_completeness(r[7], r[15], uses[r[4]], meters[r[4]]),
                "as_of": _ev_plain(sel["created_at"]),
                "source_provenance": public.cited_set(snap["t"], snap["s"], sorted(cited[r[4]]),
                                                      ev_session_row_selection(sel["revision_id"], r[4])),
                "links": {"self": f"/api/sites/{snap['code']}/ev/sessions/{_ev_plain(r[0])}{q}", "evidence": None,
                          "analysis": None,
                          "finding": None if fid is None else f"/api/sites/{snap['code']}/ev/findings/{_ev_plain(fid)}{q}",
                          "financials": None},
                "_sort": (r[8], r[0])})
        return items

    def _display_names(self, c: Connection, snap: dict[str, Any]) -> dict[str, str]:
        """asset_code -> the selected Foundation revision's component `display_name` (the scoped connector label)."""
        ids = snap["selected"]["foundation_ids"]
        if len(ids) != 1:
            return {}
        content = c.execute(text("SELECT content FROM foundation_revision WHERE tenant_id = :t AND site_id = :s "
                                 "AND id = :f"), {"t": snap["t"], "s": snap["s"], "f": UUID(str(ids[0]))}).scalar()
        content = _ev_json(content) or {}
        return {x.get("component_id"): x.get("display_name") for x in content.get("components") or ()
                if isinstance(x.get("display_name"), str)}

    def _open(self, c: Connection, t: UUID, s: UUID, code: str, lo, hi, known_at) -> tuple[dict, dict]:
        snap = self._snapshot(c, t, s, code, lo, hi, known_at)
        body = self._envelope(c, snap)
        return snap, body

    @staticmethod
    def _page(items: list[dict[str, Any]], snap: dict[str, Any], basis: str | None, cursor: str | None,
              limit: int) -> tuple[list[dict[str, Any]], str | None]:
        """`basis` is the private stored selection basis (W3-01 Run 1 ruling 3), never a public DTO digest."""
        if cursor is not None:
            doc, last_time, last_id = _ev_decode_cursor(cursor)
            if snap["lo"] is None or snap["known"] is None:
                raise EvReadRefused(409, "EV_CURSOR_BASIS_CHANGED",
                                    "No selected EV window matches this cursor; reload the first page.")
            _ev_check_cursor(doc, snap["lo"], snap["hi"], snap["known"], basis)
            items = [x for x in items if (x["_sort"][0], str(x["_sort"][1])) > (last_time, str(last_id))]
        page, more = items[:limit], len(items) > limit
        nxt = None
        if more:
            at, last = page[-1]["_sort"]
            nxt = _ev_encode_cursor(snap["lo"], snap["hi"], snap["known"], basis, at, last)
        return [{k: v for k, v in x.items() if k != "_sort"} for x in page], nxt

    # --- W2-07 commit 3: the same snapshot on a caller connection (spec "Five selected reads", q4) ---------------

    def within(self, work: Callable[[Connection], Any]) -> Any:
        """One read-only repeatable-read transaction for a composed W2-07 Site read."""
        return self._read(work)

    def open_on(self, c: Connection, t: UUID, s: UUID, code: str, lo, hi, known_at) -> tuple[dict, dict]:
        """The W2-06 snapshot and public envelope, unchanged."""
        return self._open(c, t, s, code, lo, hi, known_at)

    def status_on(self, snap: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        return self._status(snap)

    def sessions_on(self, c: Connection, snap: dict[str, Any]) -> list[dict[str, Any]]:
        return [{k: v for k, v in x.items() if k != "_sort"} for x in self._sessions(c, snap)]

    def findings_on(self, c: Connection, snap: dict[str, Any]) -> list[dict[str, Any]]:
        """The selected SUPPORTED EV Finding heads with the r9 M3 read-time START/ABORT IDs."""
        out = []
        for row in self._findings(c, snap):
            item = {k: v for k, v in row.items() if not k.startswith("_")}
            item["claim"] = {**row["_claim"], **self._support_ids(c, snap, row)}
            out.append(item)
        return out

    def page_on(self, items: list[dict[str, Any]], snap: dict[str, Any], body: dict[str, Any], route: str,
                cursor: str | None, limit: int) -> tuple[list[dict[str, Any]], str | None]:
        """W2-06 paging with the route inside the canonical cursor (`route|basis`), so a cursor is never reused
        across routes; items carry `_sort=(time, id)`."""
        return self._page(items, snap, f"{route}|{self._basis(snap) or ''}", cursor, limit)

    @staticmethod
    def _basis(snap: dict[str, Any]) -> str | None:
        """The selected head's private stored basis (the cursor fence), None with no head."""
        return None if snap["selected"] is None else snap["selected"]["basis"]

    def foundation_on(self, c: Connection, snap: dict[str, Any]) -> dict[str, Any] | None:
        """The selected assessment's Foundation revision, else the one effective at the cutoff: `{content,
        valid_from}`. None when no Foundation exists. Delegates to `foundation_revision_on` (W5-03a pre-flight)
        so the two reads can never disagree."""
        row = self.foundation_revision_on(c, snap)
        return None if row is None else {"content": row["content"], "valid_from": row["valid_from"]}

    def foundation_revision_on(self, c: Connection, snap: dict[str, Any]) -> dict[str, Any] | None:
        """W5-03a pre-flight: the `foundation_on` revision with its identity and validity, `{id, content,
        valid_from, valid_to}` (`id` lowercase, `valid_to` None when open ended), by the same predicate: the selected
        head's single `foundation_ids` entry, else the revision effective at the cutoff. None when none resolves."""
        p: dict[str, Any] = {"t": snap["t"], "s": snap["s"]}
        sel = snap["selected"]
        if sel is not None and len(sel["foundation_ids"]) == 1:
            row = c.execute(text("SELECT id, content, valid_from, valid_to FROM foundation_revision "
                                 "WHERE tenant_id = :t AND site_id = :s AND id = :f"),
                            {**p, "f": UUID(str(sel["foundation_ids"][0]))}).first()
        else:
            at = snap["known"] or snap["hi"]
            row = None if at is None else c.execute(text(
                "SELECT id, content, valid_from, valid_to FROM foundation_revision WHERE tenant_id = :t "
                "AND site_id = :s AND superseded_at IS NULL AND valid_from <= :k AND (valid_to IS NULL OR valid_to > :k) "
                "ORDER BY valid_from DESC, version DESC LIMIT 1"), {**p, "k": at}).first()
        return None if row is None else {"id": _ev_plain(row[0]), "content": _ev_json(row[1]) or {},
                                         "valid_from": row[2], "valid_to": row[3]}

    def assets_on(self, c: Connection, snap: dict[str, Any]) -> dict[str, str]:
        """asset_code -> lowercase asset UUID for the Site (the Foundation component IDs' scoped assets)."""
        return {code: _ev_plain(i) for i, code in c.execute(text(
            "SELECT id, asset_code FROM asset WHERE tenant_id = :t AND site_id = :s"),
            {"t": snap["t"], "s": snap["s"]}).all()}

    def accepted_on(self, c: Connection, snap: dict[str, Any]) -> list[dict[str, Any]]:
        """The window's accepted public records at the cutoff (`_ev_rows`, the same set W2-06 assessed), each with
        its selected W2-06 use/reason: a selected session revision's `ev_session_evidence`/meter use, else the
        selected full-window `excluded_records` reason; no synthetic gap row and no invented link."""
        if snap["lo"] is None or snap["known"] is None:
            return []
        rows = _ev_rows(c, {"t": snap["t"], "s": snap["s"], "k": snap["known"], "lo": snap["lo"], "hi": snap["hi"]})
        if not rows:
            return []
        p = {"t": snap["t"], "s": snap["s"], "ids": [str(r[0]) for r in rows]}
        extra = {r[0]: (r[1], r[2]) for r in c.execute(text(
            "SELECT id, published_at, received_at FROM accepted_evidence WHERE tenant_id = :t AND site_id = :s "
            "AND id = ANY(CAST(:ids AS uuid[]))"), p).all()}
        uses: dict[str, tuple[str, str | None, str | None]] = {}
        sel = snap["selected"]
        if sel is not None:
            revisions = [str(x) for x in sel["result"].get("session_revision_ids") or ()]
            if revisions:
                q = {**p, "revs": revisions}
                for eid, use, why, session in c.execute(text(
                        "SELECT x.evidence_id, x.use, x.reason, v.session_id FROM ev_session_evidence x "
                        "JOIN ev_session_revision v ON v.tenant_id = x.tenant_id AND v.site_id = x.site_id "
                        "AND v.id = x.revision_id WHERE x.tenant_id = :t AND x.site_id = :s "
                        "AND x.revision_id = ANY(CAST(:revs AS uuid[])) ORDER BY x.evidence_id, x.use"), q).all():
                    uses.setdefault(_ev_plain(eid), (use, why, _ev_plain(session)))
                for eid, use, why, session in c.execute(text(
                        "SELECT m.evidence_id, m.use, m.reason, v.session_id FROM ev_meter_interval m "
                        "JOIN ev_session_revision v ON v.tenant_id = m.tenant_id AND v.site_id = m.site_id "
                        "AND v.id = m.revision_id WHERE m.tenant_id = :t AND m.site_id = :s "
                        "AND m.revision_id = ANY(CAST(:revs AS uuid[])) ORDER BY m.evidence_id, m.use"), q).all():
                    uses.setdefault(_ev_plain(eid), (use, why, _ev_plain(session)))
            for x in sel["result"].get("excluded_records") or ():
                uses.setdefault(str(x.get("evidence_id")).lower(), ("EXCLUDED", x.get("reason"), None))
        out = []
        for r in sorted(rows, key=lambda r: (r[2], str(r[0]))):
            eid = _ev_plain(r[0])
            use, why, session = uses.get(eid, (None, None, None))
            sent, received = extra.get(r[0], (None, None))
            out.append({
                "evidence_id": eid, "record_kind": r[8] if r[8] is not None else r[9], "family": r[7],
                "measurement": r[9], "role": r[20], "value": r[11], "unit": r[12], "source_time": r[2],
                "interval_start": r[3], "interval_end": r[4], "sent_at": sent, "received_at": received,
                "quality": r[10], "asset_id": _ev_plain(r[15]), "source_id": _ev_plain(r[17]),
                "connector_id": r[5], "session_id": session, "use": use, "reason": why,
                "_sort": (r[2], r[0])})
        return out

    def source_bindings_on(self, c: Connection, snap: dict[str, Any]) -> list[tuple[str, str, UUID, str]]:
        """q5 R2: `(asset_id, source_id, gateway_id, role)` of the selected run's bound channels (its stored
        `binding_set_revision_ids`, matched as binding or binding-set revision IDs), else the bindings effective at
        the cutoff over the window; only bindings on a registered gateway, on the caller connection."""
        if snap["lo"] is None or snap["known"] is None:
            return []
        p: dict[str, Any] = {"t": snap["t"], "s": snap["s"], "k": snap["known"], "lo": snap["lo"], "hi": snap["hi"]}
        ids: list[UUID] = []
        if snap["selected"] is not None:
            raw = c.execute(text("SELECT binding_set_revision_ids FROM analytic_run WHERE id = :r"),
                            {"r": snap["selected"]["run_id"]}).scalar()
            ids = [UUID(str(x)) for x in _ev_json(raw) or ()]
        if ids:
            where, p["ids"] = "(b.id = ANY(:ids) OR b.binding_set_revision_id = ANY(:ids))", ids
        else:
            where = ("b.recorded_at <= :k AND (b.superseded_at IS NULL OR b.superseded_at > :k) "
                     "AND b.valid_from < :hi AND (b.valid_to IS NULL OR b.valid_to > :lo)")
        rows = c.execute(text(
            "SELECT DISTINCT b.asset_id, b.source_id, b.gateway_id, b.role FROM signal_binding_revision b "
            "JOIN gateway g ON g.tenant_id = b.tenant_id AND g.site_id = b.site_id AND g.id = b.gateway_id "
            f"WHERE b.tenant_id = :t AND b.site_id = :s AND b.asset_id IS NOT NULL AND {where} "
            "ORDER BY b.asset_id, b.source_id, b.gateway_id, b.role"), p).all()
        return [(_ev_plain(r[0]), _ev_plain(r[1]), r[2], r[3]) for r in rows]

    def source_contacts_on(self, c: Connection, t: UUID, s: UUID, gateway_ids: list[UUID],
                           cutoff: datetime) -> dict[UUID, dict[str, Any]]:
        """q5 R2: the commit-3 per-gateway latest eligible diagnostic at `cutoff` (`ColdReadService`'s query)."""
        return ColdReadService.source_contacts_on(c, t, s, gateway_ids, cutoff)

    def sessions(self, tenant_id: UUID, site_id: UUID, code: str, lo: datetime | None, hi: datetime | None,
                 known_at: datetime | None, cursor: str | None, limit: int) -> dict[str, Any]:
        def work(c):
            snap, body = self._open(c, tenant_id, site_id, code, lo, hi, known_at)
            status, denominator = self._status(snap)
            items, nxt = self._page(self._sessions(c, snap), snap, self._basis(snap), cursor, limit)
            # r9 M1-c: the selected assessment's full-window wrong-binding records, independent of paging.
            excluded = [] if snap["selected"] is None else list(snap["selected"]["result"].get("excluded_records")
                                                                or ())
            return {**body, "status": status, "denominator": denominator, "excluded_records": excluded,
                    "items": items, "next_cursor": nxt}
        return self._read(work)

    def session(self, tenant_id: UUID, site_id: UUID, code: str, session_id: UUID, lo: datetime | None,
                hi: datetime | None, known_at: datetime | None) -> dict[str, Any] | None:
        def work(c):
            snap, body = self._open(c, tenant_id, site_id, code, lo, hi, known_at)
            found = self._sessions(c, snap, session_id)
            if not found:
                return None
            item = {k: v for k, v in found[0].items() if k != "_sort"}
            p = {"t": tenant_id, "s": site_id, "r": UUID(item["revision_id"])}
            evidence = [{"evidence_id": _ev_plain(r[0]), "content_sha256": r[1], "use": r[2], "reason": r[3],
                         "source_time": _ev_plain(r[4]), "received_at": _ev_plain(r[5])} for r in c.execute(text(
                "SELECT x.evidence_id, e.envelope_sha256, x.use, x.reason, e.source_time, e.received_at "
                "FROM ev_session_evidence x JOIN accepted_evidence e ON e.tenant_id = x.tenant_id "
                "AND e.site_id = x.site_id AND e.id = x.evidence_id WHERE x.tenant_id = :t AND x.site_id = :s "
                "AND x.revision_id = :r ORDER BY e.source_time, x.evidence_id"), p).all()]
            intervals = [{"evidence_id": _ev_plain(r[0]), "start_at": _ev_plain(r[1]), "end_at": _ev_plain(r[2]),
                          "kwh": _ev_plain(r[3]), "error_bound_kwh": _ev_plain(r[4]), "use": r[5], "reason": r[6]}
                         for r in c.execute(text(
                             "SELECT evidence_id, start_at, end_at, kwh, error_bound_kwh, use, reason "
                             "FROM ev_meter_interval WHERE tenant_id = :t AND site_id = :s AND revision_id = :r "
                             "ORDER BY start_at, evidence_id"), p).all()]
            history = [{"revision_id": _ev_plain(r[0]), "revision_no": r[1], "basis_sha256": r[2], "state": r[3],
                        "created_at": _ev_plain(r[4])} for r in c.execute(text(
                "SELECT v.id, v.revision_no, v.basis_sha256, v.state, v.created_at FROM ev_session_revision v "
                "JOIN analytic_run r ON r.tenant_id = v.tenant_id AND r.site_id = v.site_id AND r.id = "
                "v.analytic_run_id WHERE v.tenant_id = :t AND v.site_id = :s AND v.session_id = :e "
                "AND r.knowledge_cutoff <= :k ORDER BY v.revision_no"),
                {"t": tenant_id, "s": site_id, "e": session_id, "k": snap["known"]}).all()]
            status, denominator = self._status(snap)
            return {**body, "status": status, "denominator": denominator, **item, "evidence": evidence,
                    "meter_intervals": intervals, "history": history}
        return self._read(work)

    # --- Findings ----------------------------------------------------------------------------------------------

    def _findings(self, c: Connection, snap: dict[str, Any], finding_id: UUID | None = None) -> list[dict[str, Any]]:
        """The Finding revisions of the selected assessment revision: SUPPORTED ones for the list; for one ID, its
        revision at that assessment whatever its lifecycle (a withdrawal is then read as history)."""
        sel = snap["selected"]
        if sel is None:
            return []
        sql = ("SELECT f.id, fr.id, fr.revision_no, fr.basis_sha256, fr.claim, fr.title, fr.claim_level, "
               "fr.lifecycle, fr.created_at, f.anchor_start, fr.limitations, fr.transition FROM finding_revision fr JOIN finding f "
               "ON f.tenant_id = fr.tenant_id AND f.site_id = fr.site_id AND f.id = fr.finding_id "
               "WHERE fr.tenant_id = :t AND fr.site_id = :s AND f.domain = 'ev_charging' "
               "AND fr.assessment_revision_id = :ar ")
        p: dict[str, Any] = {"t": snap["t"], "s": snap["s"], "ar": sel["revision_id"]}
        if finding_id is None:
            sql += "AND fr.lifecycle = 'SUPPORTED' "
        else:
            sql += "AND f.id = :f "
            p["f"] = finding_id
        q = self._query(snap)
        found = c.execute(text(sql + "ORDER BY f.anchor_start, f.id"), p).all()
        # W3-01 Run 3 q3: the selected session revision pinned by each claim's `session_id`, among the selected
        # assessment's `session_revision_ids`; a missing or ambiguous one is a failed row selection (refused).
        revisions = list(sel["result"].get("session_revision_ids") or ())
        by_session: dict[str, list[Any]] = {}
        if found and revisions:
            for vid, session in c.execute(text(
                    "SELECT id, session_id FROM ev_session_revision WHERE tenant_id = :t AND site_id = :s "
                    "AND id = ANY(CAST(:ids AS uuid[]))"),
                    {"t": snap["t"], "s": snap["s"], "ids": [str(x) for x in revisions]}).all():
                by_session.setdefault(str(session).lower(), []).append(vid)
        public = self._public(c) if found else None
        items = []
        for r in found:
            claim = _ev_json(r[4]) or {}
            pinned = by_session.get(str(claim.get("session_id")).lower(), []) if claim.get("session_id") is not None else []
            # W3-01 r1 M3.1: only a withdrawal (lifecycle and transition NO_LONGER_SUPPORTED) whose stored session has
            # zero matches in the selected assessment's full session set reads on the two-ID selection.
            withdrawn_dropped = (len(pinned) == 0 and claim.get("session_id") is not None
                                 and r[7] == "NO_LONGER_SUPPORTED" and r[11] == "NO_LONGER_SUPPORTED")
            if len(pinned) != 1 and not withdrawn_dropped:
                raise EvPinnedLineageUnavailable("An EV Finding revision's pinned session revision cannot be read.")
            cited = [str(x).lower() for x in c.execute(text(
                "SELECT evidence_id FROM finding_revision_evidence WHERE tenant_id = :t AND site_id = :s "
                "AND finding_revision_id = :r"), {"t": snap["t"], "s": snap["s"], "r": r[1]}).scalars().all()]
            items.append({
                "finding_id": _ev_plain(r[0]), "revision_id": _ev_plain(r[1]), "revision_no": r[2], "basis_sha256": r[3],
                "session_id": claim.get("session_id"), "title": r[5], "claim_level": r[6], "lifecycle": r[7],
                "as_of": _ev_plain(r[8]),
                "source_provenance": public.cited_set(
                    snap["t"], snap["s"], sorted(cited),
                    ev_withdrawn_finding_row_selection(sel["revision_id"], r[1]) if withdrawn_dropped
                    else ev_finding_row_selection(sel["revision_id"], pinned[0], r[1])),
                "links": {"self": f"/api/sites/{snap['code']}/ev/findings/{_ev_plain(r[0])}{q}", "evidence": None,
                          "analysis": None, "finding": None, "financials": None},
                "_claim": claim, "_limitations": list(_ev_json(r[10]) or ()), "_sort": (r[9], r[0])})
        return items

    @staticmethod
    def _support_ids(c: Connection, snap: dict[str, Any], row: dict[str, Any]) -> dict[str, str | None]:
        """r9 M3 (read-time only): the Finding revision's exact cited IDs joined to the selected session revision's
        `SUPPORT`/null-reason uses and to the literal accepted `EV_SESSION_START` / `EV_SESSION_ABORT` kind;
        exactly one ID of a kind, else null for that kind."""
        session = row["_claim"].get("session_id")
        revisions = list(snap["selected"]["result"].get("session_revision_ids") or ())
        found: dict[str, set[str]] = {ev.START: set(), ev.ABORT: set()}
        if session is not None and revisions:
            for kind, evidence_id in c.execute(text(
                    "SELECT e.record_kind, x.evidence_id FROM finding_revision_evidence fe "
                    "JOIN ev_session_evidence x ON x.evidence_id = fe.evidence_id AND x.tenant_id = :t "
                    "AND x.site_id = :s JOIN ev_session_revision v ON v.tenant_id = x.tenant_id "
                    "AND v.site_id = x.site_id AND v.id = x.revision_id JOIN accepted_evidence e "
                    "ON e.tenant_id = x.tenant_id AND e.site_id = x.site_id AND e.id = x.evidence_id "
                    "WHERE fe.finding_revision_id = :r AND v.id = ANY(CAST(:revs AS uuid[])) "
                    "AND CAST(v.session_id AS text) = :session AND x.use = 'SUPPORT' AND x.reason IS NULL "
                    "AND e.family = 'EVENT' AND e.record_kind IN (:start, :abort)"),
                    {"t": snap["t"], "s": snap["s"], "r": UUID(row["revision_id"]), "revs": revisions,
                     "session": str(session).lower(), "start": ev.START, "abort": ev.ABORT}).all():
                found[kind].add(_ev_plain(evidence_id))

        def one(kind: str) -> str | None:
            return next(iter(found[kind])) if len(found[kind]) == 1 else None

        return {"start_evidence_id": one(ev.START), "abort_evidence_id": one(ev.ABORT)}

    def findings(self, tenant_id: UUID, site_id: UUID, code: str, lo: datetime | None, hi: datetime | None,
                 known_at: datetime | None, cursor: str | None, limit: int) -> dict[str, Any]:
        def work(c):
            snap, body = self._open(c, tenant_id, site_id, code, lo, hi, known_at)
            rows = [{k: v for k, v in x.items() if k not in ("_claim", "_limitations")}
                    for x in self._findings(c, snap)]
            items, nxt = self._page(rows, snap, self._basis(snap), cursor, limit)
            return {**body, "items": items, "next_cursor": nxt}
        return self._read(work)

    def finding(self, tenant_id: UUID, site_id: UUID, code: str, finding_id: UUID, lo: datetime | None,
                hi: datetime | None, known_at: datetime | None) -> dict[str, Any] | None:
        def work(c):
            snap, body = self._open(c, tenant_id, site_id, code, lo, hi, known_at)
            found = self._findings(c, snap, finding_id)
            if not found:
                return None
            row = found[0]
            evidence = [{"evidence_id": _ev_plain(r[0]), "content_sha256": r[1], "source_time": _ev_plain(r[2]),
                         "received_at": _ev_plain(r[3])} for r in c.execute(text(
                "SELECT x.evidence_id, e.envelope_sha256, e.source_time, e.received_at FROM "
                "finding_revision_evidence x JOIN accepted_evidence e ON e.id = x.evidence_id "
                "AND e.tenant_id = :t AND e.site_id = :s WHERE x.finding_revision_id = :r "
                "ORDER BY e.source_time, x.evidence_id"),
                {"t": tenant_id, "s": site_id, "r": UUID(row["revision_id"])}).all()]
            history = [{"revision_id": _ev_plain(r[0]), "revision_no": r[1], "transition": r[2], "lifecycle": r[3],
                        "created_at": _ev_plain(r[4])} for r in c.execute(text(
                "SELECT fr.id, fr.revision_no, fr.transition, fr.lifecycle, fr.created_at FROM finding_revision fr "
                "JOIN analytic_run r ON r.tenant_id = fr.tenant_id AND r.site_id = fr.site_id "
                "AND r.id = fr.analytic_run_id WHERE fr.tenant_id = :t AND fr.site_id = :s AND fr.finding_id = :f "
                "AND r.knowledge_cutoff <= :k ORDER BY fr.revision_no"),
                {"t": tenant_id, "s": site_id, "f": finding_id, "k": snap["known"]}).all()]
            item = {k: v for k, v in row.items() if not k.startswith("_")}
            claim = {**row["_claim"], **self._support_ids(c, snap, row)}
            return {**body, **item, "claim": claim, "evidence": evidence, "history": history,
                    "limitations": row["_limitations"]}
        return self._read(work)
