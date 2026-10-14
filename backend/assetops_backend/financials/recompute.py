"""Durable `fuel-cost-1` consequence recompute (S4-02b phase 2a).

Packet `tasks/S4-02b-fuel-consequence.md` "Migration, recompute and reads": dirty work rows are written by
migration 0011's triggers in the assumption-publication or FindingRevision transaction (and once for every
FindingRevision that predates 0011). This worker drains them:

    pending_work -> load_input -> quantify -> select_window_price -> consequence -> append -> record_attempt

- `FINDING_REVISION_APPENDED` recomputes that exact FindingRevision (a new FindingRevision gets its own
  consequence chain, even when a later revision has since superseded it).
- `ASSUMPTION_PUBLISHED` recomputes the latest revision of every Finding whose episode overlaps the
  publication's affected valid range `[affected_from, affected_to)`.

Each target is derived from the exact persisted inputs and the price timeline known now, and appended
idempotently: an unchanged basis replays the stored ID (review M1 keeps an unrelated publication from
re-revising), a changed one appends revision n+1. A failure records a typed FAILED attempt and leaves the work
pending, so the read shows STALE/PENDING rather than an old amount as current; the next run retries. A crash
between `append` and `record_attempt` is safe: the retry replays the same consequence ID.

This module does no I/O of its own; stores are injected (composition builds them).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import UUID

from assetops_backend.financials import fuel_cost as fc

ERROR_STORE_UNAVAILABLE = "STORE_UNAVAILABLE"
ERROR_FINDING_REVISION_NOT_FOUND = "FINDING_REVISION_NOT_FOUND"
ERROR_RECOMPUTE_FAILED = "RECOMPUTE_FAILED"


class ConsequenceStore(Protocol):
    def load_input(self, tenant_id: UUID, site_id: UUID, finding_id: UUID,
                   finding_revision_id: UUID) -> fc.FindingInput | None: ...

    def append(self, c_: fc.Consequence) -> Any: ...

    def pending_work(self, tenant_id: UUID, site_id: UUID) -> list[dict[str, Any]]: ...

    def record_attempt(self, tenant_id: UUID, site_id: UUID, work_id: UUID, **kw: Any) -> int: ...

    def latest_revisions_overlapping(self, tenant_id: UUID, site_id: UUID, lo: Any,
                                     hi: Any) -> list[tuple[UUID, UUID]]: ...


class PriceStore(Protocol):
    def snapshot(self, tenant_id: UUID, site_id: UUID, key: str, recorded_at: Any, after_revision_no: int,
                 limit: int) -> dict[str, Any]: ...


class FindingRevisionMissing(LookupError):
    pass


def window_price(prices: PriceStore, tenant_id: UUID, site_id: UUID, f: fc.FindingInput) -> fc.PriceSelection:
    """The whole-window price selection from the current price timeline (recorded cutoff: now)."""
    snap = prices.snapshot(tenant_id, site_id, fc.PRICE_KEY, None, 0, 1)
    return fc.select_window_price(snap["timeline"], snap["cited"], f.window_start, f.window_end)


def derive(store: ConsequenceStore, prices: PriceStore, tenant_id: UUID, site_id: UUID, finding_id: UUID,
           finding_revision_id: UUID) -> fc.Consequence:
    """The consequence the exact persisted inputs and today's price timeline give, not yet stored."""
    f = store.load_input(tenant_id, site_id, finding_id, finding_revision_id)
    if f is None:
        raise FindingRevisionMissing(f"FindingRevision {finding_revision_id} is not this Site's Finding's.")
    q = fc.quantify(f)
    price = fc.NOT_EVALUATED if q.state != "AVAILABLE" else window_price(prices, tenant_id, site_id, f)
    return fc.consequence(f, q, price)


@dataclass
class WorkOutcome:
    work_id: UUID
    cause: str
    succeeded: bool
    attempt_no: int
    consequence_revision_ids: list[UUID] = field(default_factory=list)
    appended: list[UUID] = field(default_factory=list)
    replayed: list[UUID] = field(default_factory=list)
    error_code: str | None = None
    error_detail: str | None = None


class ConsequenceRecomputeWorker:
    def __init__(self, store: ConsequenceStore, prices: PriceStore,
                 unavailable: tuple[type[BaseException], ...] = ()) -> None:
        self._store = store
        self._prices = prices
        self._unavailable = unavailable

    def targets(self, tenant_id: UUID, site_id: UUID, work: dict[str, Any]) -> list[tuple[UUID, UUID]]:
        if work["cause"] == "FINDING_REVISION_APPENDED":
            return [(work["finding_id"], work["finding_revision_id"])]
        return self._store.latest_revisions_overlapping(tenant_id, site_id, work["affected_from"],
                                                        work["affected_to"])

    def process(self, tenant_id: UUID, site_id: UUID, work: dict[str, Any]) -> WorkOutcome:
        out = WorkOutcome(work["id"], work["cause"], False, 0)
        try:
            for finding_id, revision_id in self.targets(tenant_id, site_id, work):
                appended = self._store.append(derive(self._store, self._prices, tenant_id, site_id, finding_id,
                                                     revision_id))
                out.consequence_revision_ids.append(appended.consequence_revision_id)
                (out.replayed if appended.replayed else out.appended).append(appended.consequence_revision_id)
        except FindingRevisionMissing as error:
            out.error_code, out.error_detail = ERROR_FINDING_REVISION_NOT_FOUND, str(error)
        except self._unavailable as error:
            out.error_code, out.error_detail = ERROR_STORE_UNAVAILABLE, str(error)
        except Exception as error:  # noqa: BLE001 - any failure is recorded as typed pending work, never lost
            out.error_code, out.error_detail = ERROR_RECOMPUTE_FAILED, f"{type(error).__name__}: {error}"
        if out.error_code is None:
            out.succeeded = True
            out.attempt_no = self._store.record_attempt(
                tenant_id, site_id, work["id"], succeeded=True,
                consequence_revision_ids=tuple(out.consequence_revision_ids), skip_if_succeeded=True)
        else:
            out.attempt_no = self._store.record_attempt(
                tenant_id, site_id, work["id"], succeeded=False, error_code=out.error_code,
                error_detail=out.error_detail[:2000] if out.error_detail else None)
        return out

    def run_pending(self, tenant_id: UUID, site_id: UUID, limit: int | None = None) -> list[WorkOutcome]:
        """Drain this Site's pending work oldest first; failed items stay pending for the next run."""
        pending = self._store.pending_work(tenant_id, site_id)
        return [self.process(tenant_id, site_id, w) for w in pending[:limit]]
