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
from dataclasses import asdict
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Callable
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, OperationalError, ProgrammingError

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
_ASSESS_LOCK = "SELECT pg_advisory_xact_lock(hashtextextended(CAST(:site AS text) || :suffix, 0))"
_JOB_LOCK = "SELECT pg_advisory_xact_lock(hashtextextended(CAST(:site AS text) || ':' || :d, 0))"


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


class PostgresAssessmentStore:
    def __init__(self, database_url: str | None) -> None:
        self._database_url = database_url
        self._engine: Engine | None = None

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
        w = query.window

        def work(c: Connection) -> WindowSnapshot:
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
                 "d": query.domain, "lo": rng.start, "hi": rng.end}
            head = c.execute(text(
                "SELECT seq, selected_at, job_id, run_id FROM analytic_run_selection WHERE tenant_id = :t "
                "AND site_id = :s AND analytic_id = :a AND window_start = :ws AND window_end = :we "
                "ORDER BY seq DESC LIMIT 1"), p).first()
            jobs = c.execute(text(
                "SELECT id, status, window_start, window_end, attempts, last_error, created_at, available_at "
                "FROM recompute_job WHERE tenant_id = :t AND site_id = :s AND domain = :d "
                f"AND {_LIVE_JOBS} AND window_start < :hi AND window_end >= :lo "
                "ORDER BY created_at, id"), p).all()
            run = None if head is None else self._run_detail(c, query.tenant_id, query.site_id, head[3])
            keys = c.execute(text(
                "SELECT DISTINCT ON (assessment_key) assessment_key, id, revision_no, claim_level, created_at "
                "FROM assessment_revision WHERE tenant_id = :t AND site_id = :s AND analytic_id = :a "
                "AND window_start = :ws AND window_end = :we ORDER BY assessment_key, revision_no DESC"), p).all()
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

        return self._snapshot(work)

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
        def work(c: Connection) -> dict[str, Any] | None:
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

        return self._snapshot(work)

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
