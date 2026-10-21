"""W4-02 unit 1: the sole writer of the three migration-0029 mini-depth tables.

`D-2026-10-20-w4-02-buildspec` (base "New model and computation"; closure 1 Q14/Q26; closure 2 "Enqueue, selection
and registration"; closure 4 N6). One call appends, in one transaction:

- an immutable `mini_depth_revision` for one Site, domain, model version, window and input digest, with its exact
  accepted evidence links in `mini_depth_revision_evidence`; or, for an identical digest whose stored cutoff is at
  or before the new cutoff, a reuse of that prior revision (Q14);
- one `mini_depth_selection` event pointing at that revision, with the recompute job it settles.

The writer locks the job row and refuses a job whose tenant, Site, `mini_<domain>` and exact window differ from the
selected revision; a null job is allowed only for an explicitly recorded backfill selection. `created_at` and
`selected_at` are the database `clock_timestamp()` of the write transaction (a constructor-only test clock hook
exists for tests). The store never updates or deletes a row: 0029's append-only triggers refuse both.
"""

from __future__ import annotations

import json
import re
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Iterator, Mapping, Sequence, TypeVar
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError, ProgrammingError

#: The four page domains; each persists one Site-local clock hour per revision (closure 1 Q4).
DOMAINS: tuple[str, ...] = ("renewable", "service", "fuel", "backup")
#: The `recompute_job.domain` value each page domain's work is queued under (closure 1 Q3).
JOB_DOMAIN: dict[str, str] = {d: f"mini_{d}" for d in DOMAINS}
#: Analytic model versions, separate from Dispatch and W1 consequences.
MODEL_VERSIONS: dict[str, str] = {d: f"mini-{d}/1" for d in DOMAINS}

_SHA = re.compile(r"^sha256:[0-9a-f]{64}$")
T = TypeVar("T")


class MiniDepthStoreUnavailable(RuntimeError):
    """The mini-depth database could not be reached or queried."""


class MiniDepthWriteRefused(ValueError):
    """The requested revision or selection breaks a write rule; nothing was written."""


@dataclass(frozen=True)
class MiniRevision:
    """One assessment to persist: everything the immutable revision row and its evidence links hold."""

    tenant_id: UUID
    site_id: UUID
    domain: str
    model_version: str
    window_start: datetime
    window_end: datetime
    knowledge_cutoff: datetime
    input_sha256: str
    foundation_revision_ids: Sequence[UUID]
    binding_set_revision_ids: Sequence[UUID]
    result: Mapping[str, Any]
    evidence_ids: Sequence[UUID]


@dataclass(frozen=True)
class AppendedSelection:
    seq: int
    revision_id: UUID
    reused: bool
    selected_at: datetime


@dataclass(frozen=True)
class SelectionRecord:
    """One persisted selection joined to its revision (replay record; q3 ruling 12)."""

    seq: int
    domain: str
    window_start: datetime
    window_end: datetime
    revision_id: UUID
    job_id: UUID | None
    model_version: str
    knowledge_cutoff: datetime
    input_sha256: str
    foundation_revision_ids: tuple[UUID, ...]
    binding_set_revision_ids: tuple[UUID, ...]
    source_freshness: str | None
    evidence_ids: tuple[UUID, ...]


def _sorted_ids(values: Sequence[UUID], what: str) -> list[str]:
    ids = [str(UUID(str(v))).lower() for v in values]
    if len(ids) != len(set(ids)):
        raise MiniDepthWriteRefused(f"{what} must be distinct")
    return sorted(ids)


class PostgresMiniDepthStore:
    """Appends mini-depth revisions and selections. Reads live in the later read unit."""

    def __init__(self, engine: Engine, *, test_clock_override: Callable[[], datetime] | None = None) -> None:
        self._engine = engine
        self._clock = test_clock_override

    def _run(self, work: Callable[[Connection], T], connection: Connection | None) -> T:
        try:
            if connection is not None:
                return work(connection)
            with self._engine.begin() as own:
                return work(own)
        except MiniDepthWriteRefused:
            raise
        except IntegrityError as error:
            raise MiniDepthWriteRefused(f"The mini-depth write was refused: {error.orig}") from error
        except (OperationalError, ProgrammingError, DBAPIError) as error:
            raise MiniDepthStoreUnavailable(f"The mini-depth store failed: {error.orig}") from error

    def _now(self, c: Connection) -> datetime:
        if self._clock is not None:
            return self._clock()
        return c.execute(text("SELECT clock_timestamp()")).scalar_one()

    @classmethod
    def from_url(cls, database_url: str, **options: Any) -> "PostgresMiniDepthStore":
        return cls(create_engine(database_url, pool_pre_ping=True), **options)

    def dispose(self) -> None:
        self._engine.dispose()

    @contextmanager
    def snapshot(self) -> Iterator[Connection]:
        """Unit 4 worker: one REPEATABLE READ write transaction (inputs, revision, selection and the job's DONE);
        it commits when the block ends and rolls back on any error."""
        with self._engine.connect().execution_options(isolation_level="REPEATABLE READ") as c:
            with c.begin():
                yield c

    def clock(self, c: Connection) -> datetime:
        """The write transaction's database `clock_timestamp()` (or the test clock): a backfill's cutoff."""
        return self._now(c)

    def site_scope(self, site_code: str) -> tuple[UUID, UUID, str | None]:
        """`reconcile --site <code>`: the one Site with that public code as (tenant_id, site_id, timezone)."""
        def work(c: Connection) -> tuple[UUID, UUID, str | None]:
            rows = c.execute(text("SELECT tenant_id, id, timezone FROM site WHERE site_code_key = lower(:c)"),
                             {"c": site_code}).all()
            if len(rows) != 1:
                raise MiniDepthWriteRefused(f"Site code {site_code!r} names {len(rows)} Sites, not exactly one")
            return rows[0][0], rows[0][1], rows[0][2]

        return self._run(work, None)

    def site_selections(self, tenant_id: UUID, site_id: UUID) -> tuple["SelectionRecord", ...]:
        """Unit 4 step 5 (q3 ruling 12): every selection of one Site in `seq` order, joined to its revision and that
        revision's exact accepted-ID set, for the replay record. Read only."""
        def work(c: Connection) -> tuple[SelectionRecord, ...]:
            rows = c.execute(text(
                "SELECT s.seq, s.domain, s.window_start, s.window_end, s.revision_id, s.job_id, r.model_version, "
                "r.knowledge_cutoff, r.input_sha256, r.foundation_revision_ids, r.binding_set_revision_ids, "
                "r.result -> 'basis' ->> 'source_freshness', "
                "COALESCE((SELECT array_agg(v.evidence_id ORDER BY v.evidence_id) FROM mini_depth_revision_evidence v "
                "WHERE v.tenant_id = r.tenant_id AND v.site_id = r.site_id AND v.revision_id = r.id), '{}') "
                "FROM mini_depth_selection s JOIN mini_depth_revision r "
                "ON r.tenant_id = s.tenant_id AND r.site_id = s.site_id AND r.id = s.revision_id "
                "WHERE s.tenant_id = :t AND s.site_id = :s ORDER BY s.seq"), {"t": tenant_id, "s": site_id}).all()
            return tuple(SelectionRecord(
                seq=r[0], domain=r[1], window_start=r[2], window_end=r[3], revision_id=r[4], job_id=r[5],
                model_version=r[6], knowledge_cutoff=r[7], input_sha256=r[8],
                foundation_revision_ids=tuple(UUID(i) for i in r[9]),
                binding_set_revision_ids=tuple(UUID(i) for i in r[10]), source_freshness=r[11],
                evidence_ids=tuple(r[12])) for r in rows)

        return self._run(work, None)

    def append_selection(
        self, revision: MiniRevision, *, job_id: UUID | None, backfill: bool = False,
        connection: Connection | None = None,
    ) -> AppendedSelection:
        """Append (or reuse) the revision and one selection of it, in one transaction.

        With a caller-owned `connection` (the later worker's lease transaction) it neither begins nor commits."""
        if revision.domain not in DOMAINS:
            raise MiniDepthWriteRefused(f"Unknown mini-depth domain {revision.domain!r}")
        if not revision.window_start < revision.window_end:
            raise MiniDepthWriteRefused("The window must be half-open with window_start < window_end")
        if not _SHA.match(revision.input_sha256):
            raise MiniDepthWriteRefused("input_sha256 must be 'sha256:' followed by 64 lowercase hex digits")
        if job_id is None and not backfill:
            raise MiniDepthWriteRefused("A selection without a recompute job must be an explicitly recorded backfill")
        foundation_ids = _sorted_ids(revision.foundation_revision_ids, "Foundation revision IDs")
        binding_ids = _sorted_ids(revision.binding_set_revision_ids, "binding set revision IDs")
        evidence_ids = _sorted_ids(revision.evidence_ids, "evidence IDs")
        scope = {"t": revision.tenant_id, "s": revision.site_id, "d": revision.domain,
                 "lo": revision.window_start, "hi": revision.window_end}

        def work(c: Connection) -> AppendedSelection:
            if job_id is not None:
                job = c.execute(text(
                    "SELECT tenant_id, site_id, domain, window_start, window_end FROM recompute_job "
                    "WHERE id = :j FOR UPDATE"), {"j": job_id}).first()
                if job is None or (job.tenant_id, job.site_id, job.domain, job.window_start, job.window_end) != (
                        revision.tenant_id, revision.site_id, JOB_DOMAIN[revision.domain], revision.window_start,
                        revision.window_end):
                    raise MiniDepthWriteRefused(
                        "The recompute job does not match the selected revision's tenant, Site, domain and window")
            now = self._now(c)
            prior = c.execute(text(
                "SELECT id, knowledge_cutoff FROM mini_depth_revision WHERE tenant_id = :t AND site_id = :s "
                "AND domain = :d AND model_version = :m AND window_start = :lo AND window_end = :hi "
                "AND input_sha256 = :h FOR SHARE"),
                {**scope, "m": revision.model_version, "h": revision.input_sha256}).first()
            if prior is not None:
                if prior.knowledge_cutoff > revision.knowledge_cutoff:
                    raise MiniDepthWriteRefused(
                        "An identical input digest is stored with a later knowledge cutoff; it cannot be reused")
                cited = sorted(str(r[0]).lower() for r in c.execute(text(
                    "SELECT evidence_id FROM mini_depth_revision_evidence WHERE tenant_id = :t AND site_id = :s "
                    "AND revision_id = :r"), {**scope, "r": prior.id}).all())
                if cited != evidence_ids:
                    raise MiniDepthWriteRefused("An identical input digest cites a different accepted evidence set")
                revision_id, reused = prior.id, True
            else:
                revision_id, reused = uuid4(), False
                c.execute(text(
                    "INSERT INTO mini_depth_revision (id, tenant_id, site_id, domain, model_version, window_start, "
                    "window_end, knowledge_cutoff, input_sha256, foundation_revision_ids, binding_set_revision_ids, "
                    "result, created_at) VALUES (:id, :t, :s, :d, :m, :lo, :hi, :k, :h, CAST(:f AS jsonb), "
                    "CAST(:b AS jsonb), CAST(:r AS jsonb), :now)"),
                    {**scope, "id": revision_id, "m": revision.model_version, "k": revision.knowledge_cutoff,
                     "h": revision.input_sha256, "f": json.dumps(foundation_ids), "b": json.dumps(binding_ids),
                     "r": json.dumps(revision.result, sort_keys=True, separators=(",", ":")), "now": now})
                for evidence_id in evidence_ids:
                    c.execute(text(
                        "INSERT INTO mini_depth_revision_evidence (tenant_id, site_id, revision_id, evidence_id) "
                        "VALUES (:t, :s, :r, :e)"), {**scope, "r": revision_id, "e": evidence_id})
            seq = c.execute(text(
                "INSERT INTO mini_depth_selection (tenant_id, site_id, domain, window_start, window_end, "
                "revision_id, selected_at, job_id) VALUES (:t, :s, :d, :lo, :hi, :r, :now, :j) RETURNING seq"),
                {**scope, "r": revision_id, "now": now, "j": job_id}).scalar_one()
            return AppendedSelection(seq=int(seq), revision_id=revision_id, reused=reused, selected_at=now)

        return self._run(work, connection)


# --- Reads for `inputs.py` (unit 4 step 2) ----------------------------------------------------------------------

_KNOWN = "recorded_at <= :k AND (superseded_at IS NULL OR superseded_at > :k)"
_OVERLAPS = "valid_from < :hi AND (valid_to IS NULL OR valid_to > :lo)"
_COLUMNS = ("e.id, e.role, e.asset_id, e.source_time, e.interval_start, e.interval_end, e.quality, "
            "e.normalized_value_text, e.normalized_unit, e.record_kind, e.outcome, e.correlation_id, e.source_id, "
            "e.binding_revision_id, e.foundation_revision_id, d.decided_at")
#: W4-02 unit 4 (closure 1 Q13, q5 ruling 5): the accepted, cutoff-visible rows of the gate roles touching `[lo, hi)`.
_ACCEPTED = (
    f"SELECT {_COLUMNS} FROM accepted_evidence e JOIN ingestion_disposition d "
    "ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal "
    "WHERE e.tenant_id = :t AND e.site_id = :s AND d.decision = 'ACCEPTED' AND d.accepted_evidence_id = e.id "
    "AND e.received_at <= :k AND d.decided_at <= :k AND e.role = ANY(:roles) "
    "AND COALESCE(e.interval_end, e.source_time) >= :lo AND COALESCE(e.interval_start, e.source_time) < :hi "
    "ORDER BY e.source_time, e.id")
#: q3 ruling 4: every cutoff-visible supply row at the latest supply instant before the hour (competing rows kept).
_PRIOR_SUPPLY = (
    f"SELECT {_COLUMNS} FROM accepted_evidence e JOIN ingestion_disposition d "
    "ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal "
    "WHERE e.tenant_id = :t AND e.site_id = :s AND d.decision = 'ACCEPTED' AND d.accepted_evidence_id = e.id "
    "AND e.received_at <= :k AND d.decided_at <= :k AND e.role = :role AND e.source_time = ("
    "SELECT max(p.source_time) FROM accepted_evidence p JOIN ingestion_disposition q "
    "ON q.batch_id = p.batch_id AND q.ordinal = p.ordinal WHERE p.tenant_id = :t AND p.site_id = :s "
    "AND q.decision = 'ACCEPTED' AND q.accepted_evidence_id = p.id AND p.received_at <= :k "
    "AND q.decided_at <= :k AND p.role = :role AND p.source_time < :lo) ORDER BY e.id")




@dataclass(frozen=True)
class HourRows:
    """Raw cutoff-visible rows of one hour, read on the caller's connection; `inputs.py` adapts them."""

    timezone: str | None
    foundations: Sequence[Any]  # (id, valid_from, valid_to, content) known at the cutoff, overlapping the hour
    binding_sets: Sequence[Any]  # (id, valid_from, valid_to)
    bindings: Sequence[Any]  # (id, role, asset_id, valid_from, valid_to) of the single set, else empty
    assets: Sequence[Any]  # (asset_code, id)
    accepted: Sequence[Any]
    prior_supply: Sequence[Any]
    row_foundations: Mapping[UUID, Any]  # every as-accepted Foundation revision of the selected rows


def read_hour_rows(c: Connection, tenant_id: UUID, site_id: UUID, window_start: datetime, window_end: datetime,
                   knowledge_cutoff: datetime, *, role_set: str, roles: Sequence[str], supply_role: str) -> HourRows:
    """SELECT only. The caller owns the (REPEATABLE READ) transaction; `knowledge_cutoff` is used unchanged."""
    p = {"t": tenant_id, "s": site_id, "k": knowledge_cutoff, "lo": window_start, "hi": window_end}
    tz = c.execute(text("SELECT timezone FROM site WHERE tenant_id = :t AND id = :s"), p).scalar_one_or_none()
    foundations = c.execute(text(
        f"SELECT id, valid_from, valid_to, content FROM foundation_revision WHERE tenant_id = :t AND site_id = :s "
        f"AND {_KNOWN} AND {_OVERLAPS}"), p).all()
    sets = c.execute(text(
        f"SELECT id, valid_from, valid_to FROM signal_binding_set_revision WHERE tenant_id = :t AND site_id = :s "
        f"AND role_set = :rs AND {_KNOWN} AND {_OVERLAPS}"), {**p, "rs": role_set}).all()
    bindings = c.execute(text(
        "SELECT id, role, asset_id, valid_from, valid_to FROM signal_binding_revision WHERE tenant_id = :t "
        "AND site_id = :s AND binding_set_revision_id = :b ORDER BY id"), {**p, "b": sets[0][0]}).all()         if len(sets) == 1 else []
    assets = c.execute(text("SELECT asset_code, id FROM asset WHERE tenant_id = :t AND site_id = :s"), p).all()
    accepted = c.execute(text(_ACCEPTED), {**p, "roles": list(roles)}).all()
    prior = c.execute(text(_PRIOR_SUPPLY), {**p, "role": supply_role}).all()
    ids = sorted({r[14] for r in (*accepted, *prior)}, key=str)
    row_foundations = {r[0]: r for r in c.execute(text(
        "SELECT id, valid_from, valid_to, content FROM foundation_revision WHERE tenant_id = :t AND site_id = :s "
        "AND id = ANY(:ids)"), {**p, "ids": ids}).all()}
    return HourRows(tz, foundations, sets, bindings, assets, accepted, prior, row_foundations)


__all__ = [
    "DOMAINS", "JOB_DOMAIN", "MODEL_VERSIONS", "AppendedSelection", "MiniDepthStoreUnavailable",
    "MiniDepthWriteRefused", "MiniRevision", "PostgresMiniDepthStore", "HourRows", "SelectionRecord", "read_hour_rows",
]
