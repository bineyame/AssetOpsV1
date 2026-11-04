"""CH-5a1 (build sheet Part A §A3): the ChainReader SQL, SELECT only (registered in `$pgReaders`).

Tables read: `site_day_snapshot` (through the snapshot store), `finding_thread_occurrence`, `finding_thread`,
`finding`, `finding_revision`, `finding_merge`, `action_policy_change`, `event_outbox`, `event_consumption`.
Every value handed out is frozen (`FindingHead` dataclasses, tuples, a `MappingProxyType`), CH5a-R R1.
"""

from __future__ import annotations

from datetime import date, datetime
from types import MappingProxyType
from typing import Any, Mapping, Sequence
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from assetops_backend.chain.read import FindingHead

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


class PostgresChainRead:
    """The `ChainReadPort` (`chain/read.py`). `snapshots` reuses the snapshot store's latest-row read."""

    def __init__(self, database_url: str | None = None, *, engine: Engine | None = None,
                 snapshots: Any = None) -> None:
        if engine is None and not database_url:
            raise RuntimeError("DATABASE_URL is not set, so the chain read cannot be reached.")
        self._engine = engine or create_engine(database_url, pool_pre_ping=True)
        self._owns_engine = engine is None
        self._snapshots = snapshots

    def dispose(self) -> None:
        if self._owns_engine:
            self._engine.dispose()

    def snapshots(self, tenant_id: UUID, site_id: UUID, lo: date, hi: date, measures: Sequence[str],
                  known_at: datetime | None) -> tuple[Any, ...]:
        return tuple(self._snapshots.latest(tenant_id, site_id, lo, hi, list(measures), known_at))

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
