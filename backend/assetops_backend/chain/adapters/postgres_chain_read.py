"""CH-5a1 (build sheet Part A §A3): the ChainReader SQL, SELECT only (registered in `$pgReaders`).

Tables read: `site_day_snapshot` (through the snapshot store), `finding_thread_occurrence`, `finding_thread`,
`finding`, `finding_revision`, `finding_merge`, `action_policy_change`, `event_outbox`, `event_consumption`, and
(CH-5a2a `site_threads`) `finding_thread_event`, `mini_opportunity`, `chain_action`, `action_event`, `domain_action`, and (K10 v2 R3t
`declared_none_days`) `site`, `foundation_revision`.
Every value handed out is frozen (`FindingHead` dataclasses, tuples, a `MappingProxyType`), CH5a-R R1.
"""

from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta, timezone
from types import MappingProxyType
from typing import Any, Mapping, Sequence
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from assetops_backend.chain.read import FindingHead
from assetops_backend.chain.reader import declared_none_day, site_never_declared
from assetops_backend.mini_depth.read import productive_loads
from assetops_backend.evidence.public_provenance import (LinkRowsReads, PublicProvenance, estate_projection,
                                                         finding_row_selection)

#: §A3 Finding heads (CH5a1-R Q6, the finding index's head rule): the latest revision at `k`, merged-away Findings
#: excluded, the index's domain and analytic only, occurrences visible at `k`, the episode intersecting `[lo, hi)`.
#: CH5a1-R2 R-1: `k` here is always the request's transaction-time `known_at` (`ChainRequest.k`, None = live), the
#: only bound `source_known_at` / `created_at` are compared with; a story-time evidence cutoff never reaches it.
_FINDING_HEADS = text("""
SELECT CAST(o.thread_id AS text) AS thread_id, o.occurrence_no, CAST(f.id AS text) AS finding_id,
       CAST(r.id AS text) AS revision_id, r.revision_no, r.lifecycle, r.transition, r.episode_start, r.episode_end,
       f.mechanism, t.subject_ref
  FROM finding_thread_occurrence o
  JOIN finding_thread t ON t.id = o.thread_id
  JOIN finding f ON f.tenant_id = o.tenant_id AND f.site_id = o.site_id AND f.id = o.finding_id
  JOIN LATERAL (SELECT * FROM finding_revision x WHERE x.tenant_id = f.tenant_id AND x.site_id = f.site_id
                AND x.finding_id = f.id AND (CAST(:k AS timestamptz) IS NULL OR x.created_at <= CAST(:k AS timestamptz))
                ORDER BY x.revision_no DESC LIMIT 1) r ON true
 WHERE o.tenant_id = :t AND o.site_id = :s AND o.finding_id IS NOT NULL
   AND f.domain = :domain AND f.analytic_id = :analytic
   AND NOT EXISTS (SELECT 1 FROM finding_merge m
                    WHERE m.superseded_finding_id = f.id
                      AND (CAST(:k AS timestamptz) IS NULL OR m.created_at <= CAST(:k AS timestamptz)))
   AND (CAST(:k AS timestamptz) IS NULL OR coalesce(o.source_known_at, o.joined_at) <= CAST(:k AS timestamptz))
   AND r.episode_start < :hi AND (r.episode_end IS NULL OR r.episode_end > :lo)
 ORDER BY r.episode_start DESC, f.id
""")

#: R8 (CH5a1-R Q1, C1): an unconsumed finding/opportunity event of the Site at story time `k` (pre-flight P8).
_UNSETTLED = text("""
SELECT EXISTS (SELECT 1 FROM event_outbox o
  WHERE o.site_id = :s AND o.type IN ('finding.revised','opportunity.revised') AND o.tenant_id = :t
    AND (CAST(:k AS timestamptz) IS NULL OR o.occurred_at <= CAST(:k AS timestamptz))
    AND NOT EXISTS (SELECT 1 FROM event_consumption x WHERE x.consumer = 'threads' AND x.event_id = o.event_id)
  LIMIT 1)
""")

#: §A3 `has_change` (C6): replaces the board's `action` detail read, `bool(detail.change)`.
_HAS_CHANGE = text("""
SELECT CAST(a.id AS text) AS action_id,
       EXISTS (SELECT 1 FROM action_policy_change c WHERE c.tenant_id = :t AND c.action_id = a.id) AS has_change
  FROM unnest(CAST(:ids AS uuid[])) AS a(id)
""")


#: CH-5a2a §B1 (`/chain` routes): one Site's threads, their occurrences visible at the request's `k` (transaction
#: time, CH5a1-R2 R-1), every event of those threads (visibility at the state cutoff is applied in pure code,
#: `lifecycle.visible`) and their linked Actions with the ACCEPTED time `lookup.LOOKUP` reads.
_SITE_OCCURRENCES = text("""
SELECT CAST(o.thread_id AS text) AS thread_id, t.mechanism, t.subject_ref, o.occurrence_no,
       CAST(o.finding_id AS text) AS finding_id, CAST(o.opportunity_id AS text) AS opportunity_id,
       m.public_no AS opportunity_no, o.episode_start, o.episode_end
  FROM finding_thread_occurrence o
  JOIN finding_thread t ON t.id = o.thread_id
  LEFT JOIN mini_opportunity m ON m.tenant_id = o.tenant_id AND m.id = o.opportunity_id
 WHERE o.tenant_id = :t AND o.site_id = :s
   AND (CAST(:k AS timestamptz) IS NULL OR coalesce(o.source_known_at, o.joined_at) <= CAST(:k AS timestamptz))
 ORDER BY o.thread_id, o.occurrence_no
""")
_SITE_EVENTS = text("""
SELECT CAST(e.thread_id AS text) AS thread_id, e.seq, e.state, e.cause_kind, e.cause_id, e.effective_day,
       e.recorded_at, e.cause_known_at
  FROM finding_thread_event e WHERE e.tenant_id = :t AND e.site_id = :s ORDER BY e.thread_id, e.seq
""")
_SITE_ACTIONS = text("""
SELECT CAST(a.id AS text) AS action_id, a.action_code, a.kind, CAST(a.thread_id AS text) AS thread_id,
       CAST(a.origin_finding_id AS text) AS origin_finding_id,
       CAST(a.origin_opportunity_id AS text) AS origin_opportunity_id,
       CASE WHEN a.kind = 'MINI_TRIAL' THEN (SELECT min(x.recorded_at) FROM action_event x
              WHERE x.tenant_id = a.tenant_id AND x.action_id = a.id AND x.kind = 'ACCEPTED')
            ELSE (SELECT d.recorded_at FROM domain_action d WHERE d.tenant_id = a.tenant_id AND d.id = a.id)
       END AS accepted_at,
       CASE WHEN a.kind = 'DOMAIN_INTENT' THEN (SELECT d.domain FROM domain_action d WHERE d.tenant_id = a.tenant_id AND d.id = a.id) END AS action_domain,
       v.outcome, v.recorded_at AS outcome_recorded_at, v.source_class
  FROM chain_action a
  -- WD-1m-R2: `source_class` is the example-data class stored with the verdict when it was judged (NULL = none found,
  -- or a verdict stored before WD-1m). One jsonb field; the board read never scans evidence.
  LEFT JOIN LATERAL (SELECT o.outcome, o.recorded_at, o.details->'source'->>'source_class' AS source_class
                       FROM verification_outcome o
                      WHERE a.kind = 'DOMAIN_INTENT' AND o.tenant_id = a.tenant_id AND o.domain_action_id = a.id
                      ORDER BY o.recorded_at, o.id LIMIT 1) v ON true
 WHERE a.tenant_id = :t AND a.site_id = :s AND a.thread_id IS NOT NULL
 ORDER BY a.action_code, a.id
""")

#: CH-5a2b (§B14 Q7): the Site's evidence watermark, `EstateSnapshot.evidence_cutoff`'s statement (None k = now).
_EVIDENCE_CUTOFF = text("""
SELECT max(decided_at) FROM ingestion_disposition
 WHERE tenant_id = :t AND site_id = :s AND (CAST(:k AS timestamptz) IS NULL OR decided_at <= CAST(:k AS timestamptz))
""")

#: PB-7 `readings_began`: the measurement start of the Site's earliest ACCEPTED reading decided by the cutoff.
_READINGS_BEGAN = text("""
SELECT min(COALESCE(e.interval_start, e.source_time))
  FROM accepted_evidence e JOIN ingestion_disposition d ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal
 WHERE e.tenant_id = :t AND e.site_id = :s AND d.decision = 'ACCEPTED' AND d.accepted_evidence_id = e.id
   AND (CAST(:k AS timestamptz) IS NULL OR d.decided_at <= CAST(:k AS timestamptz))
""")

#: CH-5a2b R1 (§B14 Q1/Q2) `placement_facts`: per selected Finding revision, its cited evidence ids (the lineage
#: `finding_revision_evidence`, as `coverage.py` reads it) and its Finding's `recurs_after` id and title (the latest
#: revision's title at `k`, the index head title).
_PLACEMENT = text("""
SELECT CAST(r.id AS text) AS revision_id,
       coalesce((SELECT array_agg(CAST(e.evidence_id AS text) ORDER BY e.evidence_id) FROM finding_revision_evidence e
                  WHERE e.tenant_id = r.tenant_id AND e.site_id = r.site_id AND e.finding_revision_id = r.id),
                CAST('{}' AS text[])) AS cited,
       CAST(f.recurs_after_finding_id AS text) AS recurs_after_finding_id,
       (SELECT x.title FROM finding_revision x
         WHERE x.tenant_id = f.tenant_id AND x.site_id = f.site_id AND x.finding_id = f.recurs_after_finding_id
           AND (CAST(:k AS timestamptz) IS NULL OR x.created_at <= CAST(:k AS timestamptz))
         ORDER BY x.revision_no DESC LIMIT 1) AS recurs_after_title
  FROM finding_revision r JOIN finding f ON f.id = r.finding_id AND f.tenant_id = r.tenant_id
 WHERE r.tenant_id = :t AND r.site_id = :s AND r.id = ANY(CAST(:ids AS uuid[]))
""")

#: CH-5a2b R1 (§B14 Q5) `action_rows`: the verification plans and outcomes (with the stored source class, R2) of the
#: Site's Actions recorded by `k`, the estate `verification` read's statements over the whole Site.
#: CH-9b2 (CH9b2-R Q10): W1 Action rows only (`action_id IS NOT NULL`); a domain Action's plan or outcome is not read here;
#: domain verdicts are read on `_SITE_ACTIONS` (MB-1-R Q1).
_ACTION_PLANS = text("""
SELECT CAST(action_id AS text) AS action_id, CAST(id AS text) AS id, recorded_at, later_start, later_end
  FROM verification_plan WHERE tenant_id = :t AND site_id = :s AND action_id IS NOT NULL
   AND (CAST(:k AS timestamptz) IS NULL OR recorded_at <= CAST(:k AS timestamptz)) ORDER BY recorded_at, id
""")
_ACTION_OUTCOMES = text("""
SELECT CAST(action_id AS text) AS action_id, CAST(id AS text) AS id, recorded_at,
       details->'source'->>'source_class' AS source_class
  FROM verification_outcome WHERE tenant_id = :t AND site_id = :s AND action_id IS NOT NULL
   AND (CAST(:k AS timestamptz) IS NULL OR recorded_at <= CAST(:k AS timestamptz)) ORDER BY recorded_at, id
""")

#: CH-5b2 (CH5b2-R Q4) `trace_facts`: per Finding of the Site, its head revision at `k` (the `_FINDING_HEADS` head
#: rule without the window), that revision's `analytic_run_id` and its cited-evidence count; one statement.
_TRACE_FACTS = text("""
SELECT CAST(f.id AS text) AS finding_id, CAST(r.id AS text) AS revision_id, r.revision_no,
       CAST(r.analytic_run_id AS text) AS analytic_run_id,
       (SELECT count(*) FROM finding_revision_evidence e
         WHERE e.tenant_id = r.tenant_id AND e.site_id = r.site_id AND e.finding_revision_id = r.id) AS cited
  FROM finding f
  JOIN LATERAL (SELECT * FROM finding_revision x WHERE x.tenant_id = f.tenant_id AND x.site_id = f.site_id
                AND x.finding_id = f.id AND (CAST(:k AS timestamptz) IS NULL OR x.created_at <= CAST(:k AS timestamptz))
                ORDER BY x.revision_no DESC LIMIT 1) r ON true
 WHERE f.tenant_id = :t AND f.site_id = :s AND f.id = ANY(CAST(:ids AS uuid[]))
 ORDER BY f.id
""")
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_END = datetime(9999, 1, 1, tzinfo=timezone.utc)

#: K10 v2 (R3t §9t.3 item 3): ONE statement - the Site's timezone (the column the builder's Site read gives
#: `SiteRef.timezone`) plus every Foundation revision of the Site known at `k` (as `MiniDepthRead.productive_users`
#: reads it), at any validity (R3t4: the gate needs the whole known history). `k` None = live, in this
#: file's `CAST(:k AS timestamptz) IS NULL OR ...` form (no SQL clock read: CH-5c2 C3 clock guard): live means every
#: recorded revision not superseded, which is `COALESCE(:k, clock_timestamp())` for rows the database already holds.
_DECLARED_NONE = text("""
SELECT s.timezone, r.valid_from, r.valid_to, r.content
  FROM site s
  LEFT JOIN foundation_revision r
    ON r.tenant_id = s.tenant_id AND r.site_id = s.id
   AND (CAST(:k AS timestamptz) IS NULL OR r.recorded_at <= CAST(:k AS timestamptz))
   AND (r.superseded_at IS NULL
        OR (CAST(:k AS timestamptz) IS NOT NULL AND r.superseded_at > CAST(:k AS timestamptz)))
 WHERE s.tenant_id = :t AND s.id = :s
""")


def declared_none_of(tz: str | None, revisions: Sequence[tuple[Any, Any, Any]], days: Sequence[date]) -> frozenset[date]:
    """K10 v2 (R3t safeguard 1, R3t3), pure: the days of `days` that `declared_none_day` accepts, i.e. whole-day
    coverage by revisions with no productive load (`productive_loads`, the builder's subject filter) and no gap.
    No timezone or no revision: not declared absent."""
    if not tz or not days:
        return frozenset()
    zone = ZoneInfo(tz)
    revs = [(vf, vt, bool(productive_loads(c if isinstance(c, Mapping) else json.loads(c))))
            for vf, vt, c in revisions if vf is not None]
    if not site_never_declared(revs):   # R3t4: a Site that ever declared productive equipment declares nothing absent
        return frozenset()
    out = set()
    for d in days:
        lo = datetime.combine(d, time.min, zone).astimezone(timezone.utc)
        hi = datetime.combine(d + timedelta(days=1), time.min, zone).astimezone(timezone.utc)
        if declared_none_day(revs, lo, hi):
            out.add(d)
    return frozenset(out)


class PostgresChainRead:
    """The `ChainReadPort` (`chain/read.py`). `snapshots` reuses the snapshot store's latest-row read."""

    def __init__(self, database_url: str | None = None, *, engine: Engine | None = None,
                 snapshots: Any = None, link_rows: Any = None, link_rows_many: Any = None,
                 action_window: Any = None) -> None:
        """`link_rows` / `link_rows_many` are the evidence ledger's connection-scoped link-row readers and
        `action_window` the Action store's `site_window_on`, injected by `chain/composition.py` (R1)."""
        if engine is None and not database_url:
            raise RuntimeError("DATABASE_URL is not set, so the chain read cannot be reached.")
        self._engine = engine or create_engine(database_url, pool_pre_ping=True)
        self._owns_engine = engine is None
        self._snapshots = snapshots
        self._link_rows, self._link_rows_many, self._action_window = link_rows, link_rows_many, action_window

    def dispose(self) -> None:
        if self._owns_engine:
            self._engine.dispose()

    def snapshots(self, tenant_id: UUID, site_id: UUID, lo: date, hi: date, measures: Sequence[str],
                  known_at: datetime | None) -> tuple[Any, ...]:
        return tuple(self._snapshots.latest(tenant_id, site_id, lo, hi, list(measures), known_at))

    def snapshots_many(self, tenant_id: UUID, site_ids: Sequence[UUID], lo: date, hi: date,
                       measures: Sequence[str], known_at: datetime | None) -> tuple[Any, ...]:
        """CH6b1-R Q3: every Site's rows in one statement (ordered by Site, measure, day, subject)."""
        return tuple(self._snapshots.latest_many(tenant_id, list(site_ids), lo, hi, list(measures), known_at))

    def declared_none_days(self, tenant_id: UUID, site_id: UUID, measure: str, days: Sequence[date],
                           known_at: datetime | None) -> frozenset[date]:
        """K10 v2 (R3t): the days of `days` on which the site setup declares no productive-use load (the optional
        `ChainReadPort` method). Only `productive_kwh`; one statement; never inferred from a missing row."""
        if measure != "productive_kwh" or not days:
            return frozenset()
        params = {"t": tenant_id, "s": site_id, "k": known_at}
        with self._engine.connect() as c:
            rows = c.execute(_DECLARED_NONE, params).all()
        if not rows:
            return frozenset()
        return declared_none_of(rows[0][0], [(r[1], r[2], r[3]) for r in rows], days)

    def finding_heads(self, tenant_id: UUID, site_id: UUID, domain: str, analytic_id: str, lo: datetime,
                      hi: datetime, known_at: datetime | None) -> tuple[FindingHead, ...]:
        params = {"t": tenant_id, "s": site_id, "domain": domain, "analytic": analytic_id, "lo": lo, "hi": hi,
                  "k": known_at}
        with self._engine.connect() as c:
            rows = c.execute(_FINDING_HEADS, params).mappings().all()
        return tuple(FindingHead(r["finding_id"], r["revision_id"], int(r["revision_no"]), r["lifecycle"],
                                 r["transition"], r["episode_start"], r["episode_end"], r["mechanism"],
                                 r["subject_ref"], r["thread_id"], r["occurrence_no"]) for r in rows)

    def findings_settled(self, tenant_id: UUID, site_id: UUID, known_at: datetime | None) -> bool:
        with self._engine.connect() as c:
            unsettled = c.execute(_UNSETTLED, {"t": tenant_id, "s": site_id, "k": known_at}).scalar()
        return not bool(unsettled)

    def has_change(self, tenant_id: UUID, action_ids: Sequence[str]) -> Mapping[str, bool]:
        if not action_ids:
            return MappingProxyType({})
        with self._engine.connect() as c:
            rows = c.execute(_HAS_CHANGE, {"t": tenant_id, "ids": [str(a) for a in action_ids]}).mappings().all()
        return MappingProxyType({str(r["action_id"]).lower(): bool(r["has_change"]) for r in rows})

    def site_threads(self, tenant_id: UUID, site_id: UUID, known_at: datetime | None) -> Mapping[str, Any]:
        """CH-5a2a: `{"occurrences", "events", "actions"}` of one Site (three statements on one read-only
        connection, one port call)."""
        params = {"t": tenant_id, "s": site_id, "k": known_at}
        with self._engine.connect() as c:
            with c.begin():
                c.execute(text("SET TRANSACTION READ ONLY"))
                out = {name: tuple(dict(r) for r in c.execute(sql, params).mappings().all())
                       for name, sql in (("occurrences", _SITE_OCCURRENCES), ("events", _SITE_EVENTS),
                                         ("actions", _SITE_ACTIONS))}
        return MappingProxyType(out)

    def evidence_cutoff(self, tenant_id: UUID, site_id: UUID, known_at: datetime | None) -> datetime | None:
        with self._engine.connect() as c:
            return c.execute(_EVIDENCE_CUTOFF, {"t": tenant_id, "s": site_id, "k": known_at}).scalar_one()

    def readings_began(self, tenant_id: UUID, site_id: UUID, known_at: datetime | None) -> datetime | None:
        """PB-7: the measurement start of the Site's earliest ACCEPTED reading decided by `known_at`."""
        with self._engine.connect() as c:
            return c.execute(_READINGS_BEGAN, {"t": tenant_id, "s": site_id, "k": known_at}).scalar_one()

    def placement_facts(self, tenant_id: UUID, site_id: UUID, revision_ids: Sequence[str],
                        known_at: datetime | None) -> Mapping[str, Any]:
        """CH-5a2b R1 (§B14 Q1/Q2): per Finding revision `{source_state, recurs_after_finding_id,
        recurs_after_title}`. At most 3 statements on one read-only connection: the cited ids and recurrence facts,
        one batched link-row read, and the per-Site link-row read only for an id the batch did not return. The
        source state is `PublicProvenance.cited_set` over the revision's cited set (imported unchanged)."""
        if not revision_ids:
            return MappingProxyType({})
        site = str(site_id).lower()
        with self._engine.connect() as c:
            with c.begin():
                c.execute(text("SET TRANSACTION READ ONLY"))
                rows = c.execute(_PLACEMENT, {"t": tenant_id, "s": site_id, "k": known_at,
                                              "ids": [str(r) for r in revision_ids]}).mappings().all()
                wanted = sorted({str(e).lower() for r in rows for e in r["cited"] or ()})
                pre = self._link_rows_many(c, tenant_id, [(site_id, wanted)]) if wanted else {}

                def link_rows(t: UUID, s: UUID, ids: list[str]) -> list[Any]:
                    keys = [(site, str(i).lower()) for i in ids]
                    if any(k not in pre for k in keys):
                        return list(self._link_rows(c, t, s, ids))
                    return [row for k in keys for row in pre[k]]

                public = PublicProvenance(LinkRowsReads(link_rows))
                out = {}
                for r in rows:
                    dto = estate_projection(public.cited_set(tenant_id, site_id, list(r["cited"] or ()),
                                                             finding_row_selection(r["revision_id"]), detail=False))
                    out[str(r["revision_id"]).lower()] = MappingProxyType({
                        "source_state": dto.get("state"), "recurs_after_finding_id": r["recurs_after_finding_id"],
                        "recurs_after_title": r["recurs_after_title"]})
        return MappingProxyType(out)

    def trace_facts(self, tenant_id: UUID, site_id: UUID, finding_ids: Sequence[str],
                    known_at: datetime | None) -> Mapping[str, Any]:
        """CH-5b2 (CH5b2-R Q4): per Finding id (lowercase) `{revision_id, revision_no, analytic_run_id, cited}` of
        its head revision at `k`; one SELECT."""
        if not finding_ids:
            return MappingProxyType({})
        with self._engine.connect() as c:
            rows = c.execute(_TRACE_FACTS, {"t": tenant_id, "s": site_id, "k": known_at,
                                            "ids": [str(f) for f in finding_ids]}).mappings().all()
        return MappingProxyType({str(r["finding_id"]).lower(): MappingProxyType({
            "revision_id": r["revision_id"], "revision_no": int(r["revision_no"]),
            "analytic_run_id": r["analytic_run_id"], "cited": int(r["cited"])}) for r in rows})

    def action_rows(self, tenant_id: UUID, site_id: UUID, known_at: datetime | None) -> Mapping[str, Any]:
        """CH-5a2b R1 (§B14 Q5): the Site's mini Actions created by `k` with their events recorded by `k` (the
        Action store's own `site_window_on`, unbounded window), and their verification plans and outcomes by `k`;
        reduced in pure code (`chain.read.reduce_action_rows`). One read-only connection, four statements."""
        params = {"t": tenant_id, "s": site_id, "k": known_at}
        hi = _END if known_at is None else known_at + timedelta(microseconds=1)
        with self._engine.connect() as c:
            with c.begin():
                c.execute(text("SET TRANSACTION READ ONLY"))
                window = self._action_window(c, tenant_id, site_id, _EPOCH, hi, known_at)
                plans = tuple(dict(r) for r in c.execute(_ACTION_PLANS, params).mappings().all())
                outcomes = tuple(dict(r) for r in c.execute(_ACTION_OUTCOMES, params).mappings().all())
        return MappingProxyType({"actions": tuple(window["actions"]), "events": tuple(window["events"]),
                                 "plans": plans, "outcomes": outcomes})
