"""PostgreSQL adapter for durable dispatch assessment (S3-01 phase 2, migration 0007).

Reads: accepted evidence (joined to its ACCEPTED disposition so the knowledge
cutoff applies to the server decision time), Foundation revisions and selected
binding sets, tenant- and Site-scoped and selected at the knowledge cutoff.

Writes, all in this module only: `analytic_run`, `analytic_run_evidence`,
`assessment_revision`, `analytic_run_assessment` (append-only), and on the S2
`recompute_job` table only the lease/retry fields (`status`, `lease_until`,
`attempts`, `available_at`, `last_error`) plus scheduling inserts/widening
under the same advisory lock the ledger uses to coalesce.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, OperationalError, ProgrammingError

from assetops_backend.analytics.assessment_inputs import (
    CONTROL_BATTERY_RESERVE,
    CONTROL_MINIMUM_RUNTIME,
    AcceptedReading,
    ControlValue,
    EvidenceQuery,
    EvidenceQueryResult,
    RoleBinding,
    Window,
)
from assetops_backend.analytics.assessment_ports import (
    AssessmentStoreUnavailable,
    Configuration,
    JobLease,
    LeaseLost,
    PersistedRun,
    RunHead,
    RunOutput,
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
_KNOWN = "recorded_at <= :k AND (superseded_at IS NULL OR superseded_at > :k)"
_OVERLAPS = "valid_from < :hi AND (valid_to IS NULL OR valid_to > :lo)"
_ASSESS_LOCK = "SELECT pg_advisory_xact_lock(hashtextextended(CAST(:site AS text) || :suffix, 0))"
_JOB_LOCK = "SELECT pg_advisory_xact_lock(hashtextextended(CAST(:site AS text) || ':' || :d, 0))"


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
                                       config.limits)

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

    def lease_job(self, domain: str, now: datetime, lease: timedelta) -> JobLease | None:
        def work(c: Connection) -> JobLease | None:
            row = c.execute(text(
                "UPDATE recompute_job SET status = 'LEASED', lease_until = :until, attempts = attempts + 1 "
                "WHERE id = (SELECT id FROM recompute_job WHERE domain = :d AND ((status = 'PENDING' AND "
                "available_at <= :now) OR (status = 'LEASED' AND lease_until < :now)) "
                "ORDER BY available_at, created_at LIMIT 1 FOR UPDATE SKIP LOCKED) "
                "RETURNING id, tenant_id, site_id, domain, window_start, window_end, attempts"),
                {"d": domain, "now": now, "until": now + lease}).first()
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
                {"st": "FAILED" if final else "PENDING", "at": now + backoff * lease.attempts, "e": error,
                 "id": lease.job_id})
            return "FAILED" if final else "RETRY"

        try:
            return self._run(work, write=True)
        except LeaseLost:
            return "LEASE_LOST"

    def record_runs(self, outputs: list[RunOutput], now: datetime) -> list[PersistedRun]:
        return self._run(lambda c: [self._persist(c, out, None, now) for out in outputs], write=True)

    def enqueue(self, tenant_id: UUID, site_id: UUID, domain: str, window: Window, now: datetime) -> None:
        def work(c: Connection) -> None:
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

        self._run(work, write=True)

    # --- runs and revisions -------------------------------------------------------

    def _persist(self, c: Connection, out: RunOutput, job_id: UUID | None, now: datetime) -> PersistedRun:
        i = out.inputs
        c.execute(text(_ASSESS_LOCK), {"site": i.site_id, "suffix": ":dispatch-assessment"})
        existing = c.execute(text(
            "SELECT id FROM analytic_run WHERE site_id = :s AND analytic_id = :a AND model_version = :m "
            "AND window_start = :ws AND window_end = :we AND input_sha256 = :h"),
            {"s": i.site_id, "a": i.analytic_id, "m": i.model_version, "ws": i.window.start, "we": i.window.end,
             "h": i.input_sha256}).first()
        if existing is not None:
            linked = c.execute(text("SELECT assessment_revision_id FROM analytic_run_assessment WHERE run_id = :r"),
                               {"r": existing[0]}).scalars().all()
            return PersistedRun(existing[0], False, tuple(linked), ())
        tenant = c.execute(text("SELECT tenant_id FROM site WHERE id = :s"), {"s": i.site_id}).scalar_one()
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
        return PersistedRun(run_id, True, tuple(revision_ids), tuple(new_ids))

    def run_heads(self, tenant_id: UUID, site_id: UUID, analytic_id: str) -> list[RunHead]:
        def work(c: Connection) -> list[RunHead]:
            rows = c.execute(text(
                "SELECT DISTINCT ON (window_start, window_end) window_start, window_end, model_version, "
                "configuration_sha256 FROM analytic_run WHERE tenant_id = :t AND site_id = :s AND analytic_id = :a "
                "AND selection = 'DEFAULT' ORDER BY window_start, window_end, completed_at DESC, id"),
                {"t": tenant_id, "s": site_id, "a": analytic_id}).all()
            return [RunHead(Window(r[0], r[1]), r[2], r[3]) for r in rows]

        return self._run(work)
