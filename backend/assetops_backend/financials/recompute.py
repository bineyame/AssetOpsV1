"""Durable `fuel-cost-1` consequence recompute (S4-02b phase 2a; S4-02c phase 2 scoped drain and runner).

Packet `tasks/S4-02b-fuel-consequence.md` "Migration, recompute and reads" and
`tasks/S4-02c-evidence-consequence-work.md` items 3-4: dirty work rows are written only by the migration 0011/0012
triggers (in the assumption publication, FindingRevision or evidence acceptance transaction). This worker drains
them:

    pending_work -> (due?) -> targets -> load_input -> quantify -> select_window_price -> append -> record_attempt

- `FINDING_REVISION_APPENDED` recomputes that exact FindingRevision (a new FindingRevision gets its own
  consequence chain, even when a later revision has since superseded it).
- `ASSUMPTION_PUBLISHED` recomputes the latest revision of every Finding whose episode overlaps the
  publication's affected valid range `[affected_from, affected_to)`.
- `EVIDENCE_ACCEPTED` treats the queued FindingRevision as a locator and rechecks it inside this tenant/Site
  (`evidence_target`). A locator this Site cannot read (forged or foreign) or a reading without an ACCEPTED
  disposition is a typed FAILED attempt with no fallback. The work is a typed successful no-op (no consequence
  append) only when the queued revision is no longer the Finding's highest same-Site `revision_no` (the new
  revision's own 0011 work derives it), the stored role is not generator power, the asset is not the Finding's
  generator, or the reading does not strictly overlap the merged positive-width Candidate spans: the cases
  `quantify` would not examine (re-review N1). Reading quality never makes a no-op. Otherwise the same revision
  is derived from its own persisted inputs, where a late reading outside the cited runs' inputs gives
  `QUANTITY_UNAVAILABLE/POWER_NOT_IN_ASSESSMENT_INPUTS`; it is never substituted into the old input set.
- Any other cause records a typed `CAUSE_NOT_SUPPORTED` FAILED attempt and stays pending; it never falls through
  to an assumption-range recompute.

Each target is derived from the exact persisted inputs and the price timeline known now, and appended
idempotently: an unchanged basis replays the stored ID (review M1 keeps an unrelated publication from
re-revising), a changed one appends revision n+1. A failure records a typed FAILED attempt and leaves the work
pending, so the read shows STALE/PENDING rather than an old amount as current. A crash between `append` and
`record_attempt` is safe: the retry replays the same consequence ID.

`run` is the scheduled one-shot (item 4): under the Site claim it selects the work due at the injected `now`
(never attempted, or past its retry time derived from the last FAILED attempt's `finished_at` and `attempt_no`:
1, 2, 4, 8, 16 minutes, then 16, no terminal cap), orders it by the instant it became eligible so failing rows
never starve newer work (phase 1 review L2), processes at most `limit` items once each and reports the counts.

This module does no I/O of its own; stores are injected (composition builds them).
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Protocol
from uuid import UUID

from assetops_backend.financials import fuel_cost as fc

ERROR_STORE_UNAVAILABLE = "STORE_UNAVAILABLE"
ERROR_FINDING_REVISION_NOT_FOUND = "FINDING_REVISION_NOT_FOUND"
ERROR_RECOMPUTE_FAILED = "RECOMPUTE_FAILED"
ERROR_CAUSE_NOT_SUPPORTED = "CAUSE_NOT_SUPPORTED"
ERROR_EVIDENCE_LOCATOR_NOT_IN_SITE = "EVIDENCE_LOCATOR_NOT_IN_SITE"
ERROR_EVIDENCE_NOT_ACCEPTED = "EVIDENCE_NOT_ACCEPTED"
ERROR_WORK_SCOPE_MISMATCH = "WORK_SCOPE_MISMATCH"

CAUSE_FINDING_REVISION = "FINDING_REVISION_APPENDED"
CAUSE_ASSUMPTION = "ASSUMPTION_PUBLISHED"
CAUSE_EVIDENCE = "EVIDENCE_ACCEPTED"

# Typed no-op reasons (migration 0012 `financial_consequence_attempt_no_op_reason`).
NO_OP_SUPERSEDED = "FINDING_REVISION_SUPERSEDED"
NO_OP_ROLE = "EVIDENCE_ROLE_NOT_RELEVANT"
NO_OP_ASSET = "EVIDENCE_ASSET_NOT_RELEVANT"
NO_OP_OUTSIDE_CANDIDATE_TIME = "EVIDENCE_OUTSIDE_CANDIDATE_TIME"

# Retry delay after the n-th FAILED attempt (item 4): 1, 2, 4, 8, 16 minutes, then 16 minutes, no terminal cap.
RETRY_MINUTES = (1, 2, 4, 8, 16)


def retry_due_at(last_failed_finished_at: datetime, failed_attempt_no: int) -> datetime:
    """When work whose last FAILED attempt is number `failed_attempt_no`, finished at `last_failed_finished_at`,
    is due again."""
    step = RETRY_MINUTES[min(max(failed_attempt_no, 1), len(RETRY_MINUTES)) - 1]
    return last_failed_finished_at + timedelta(minutes=step)


def eligible_since(work: dict[str, Any]) -> datetime:
    """The instant pending work became eligible: its enqueue time before any attempt, else its retry time."""
    if work.get("last_attempt_no") is None:
        return work["enqueued_at"]
    return retry_due_at(work["last_finished_at"], work["last_attempt_no"])


def _instant(value: Any) -> datetime:
    return value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def evidence_no_op(target: dict[str, Any]) -> str | None:
    """The typed no-op reason for one in-Site evidence locator, or None when the revision must be derived.

    Only the cases `fuel_cost.quantify` cannot examine (re-review N1): a superseded revision, a stored role other
    than generator power, another asset, or no strict overlap with the merged positive-width Candidate spans
    (which covers a reading outside the episode and a null interval too). Never reading quality."""
    ev, rev = target["evidence"], target["revision"]
    if rev["revision_no"] != rev["latest_revision_no"]:
        return NO_OP_SUPERSEDED
    if ev["role"] != fc.POWER_ROLE:
        return NO_OP_ROLE
    if ev["asset_id"] is None or str(ev["asset_id"]) != str(rev["generator_asset_id"]):
        return NO_OP_ASSET
    a, b = ev["interval_start"], ev["interval_end"]
    if a is None or b is None or not a < b:
        return NO_OP_OUTSIDE_CANDIDATE_TIME
    spans = [(_instant(x["start"]), _instant(x["end"])) for x in ((rev["claim"] or {}).get("candidate_spans") or ())]
    components = fc.merge((x, y) for x, y in spans if x < y)
    if not any(a < y and x < b for x, y in components):
        return NO_OP_OUTSIDE_CANDIDATE_TIME
    return None


class CauseNotSupported(LookupError):
    """A work cause this worker does not dispatch (S4-02c review L3): recorded as a typed FAILED attempt, never
    treated as an assumption-range recompute. `EVIDENCE_ACCEPTED` stays here until its scoped drain exists."""


class ConsequenceStore(Protocol):
    def load_input(self, tenant_id: UUID, site_id: UUID, finding_id: UUID,
                   finding_revision_id: UUID) -> fc.FindingInput | None: ...

    def append(self, c_: fc.Consequence) -> Any: ...

    def pending_work(self, tenant_id: UUID, site_id: UUID) -> list[dict[str, Any]]: ...

    def record_attempt(self, tenant_id: UUID, site_id: UUID, work_id: UUID, **kw: Any) -> int: ...

    def latest_revisions_overlapping(self, tenant_id: UUID, site_id: UUID, lo: Any,
                                     hi: Any) -> list[tuple[UUID, UUID]]: ...

    def evidence_target(self, tenant_id: UUID, site_id: UUID, accepted_evidence_id: UUID, finding_id: UUID,
                        finding_revision_id: UUID) -> dict[str, Any]: ...

    def claim_site(self, tenant_id: UUID, site_id: UUID) -> AbstractContextManager[bool]: ...


class PriceStore(Protocol):
    def snapshot(self, tenant_id: UUID, site_id: UUID, key: str, recorded_at: Any, after_revision_no: int,
                 limit: int) -> dict[str, Any]: ...


class FindingRevisionMissing(LookupError):
    pass


class EvidenceLocatorRefused(LookupError):
    """An `EVIDENCE_ACCEPTED` locator this Site cannot read, or a reading with no ACCEPTED disposition."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code


class NoOp(Exception):
    """A work item whose target needs no consequence append (typed `no_op_reason`)."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


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
    no_op_reason: str | None = None


@dataclass
class RunReport:
    """One scoped `run`: whether it held the Site claim, its outcomes and the counts the CLI reports (item 4)."""
    tenant_id: UUID
    site_id: UUID
    claimed: bool
    now: datetime
    outcomes: list[WorkOutcome] = field(default_factory=list)
    deferred: int = 0
    backlog: int = 0

    def counts(self) -> dict[str, int]:
        o = self.outcomes
        return {"selected": len(o), "appended": sum(len(x.appended) for x in o),
                "replayed": sum(len(x.replayed) for x in o),
                "no_op": sum(1 for x in o if x.succeeded and x.no_op_reason is not None),
                "failed": sum(1 for x in o if not x.succeeded), "deferred": self.deferred, "backlog": self.backlog}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ConsequenceRecomputeWorker:
    def __init__(self, store: ConsequenceStore, prices: PriceStore,
                 unavailable: tuple[type[BaseException], ...] = (),
                 clock: Callable[[], datetime] = _utc_now) -> None:
        self._store = store
        self._prices = prices
        self._unavailable = unavailable
        self._clock = clock

    def targets(self, tenant_id: UUID, site_id: UUID, work: dict[str, Any]) -> list[tuple[UUID, UUID]]:
        cause = work["cause"]
        if cause == CAUSE_FINDING_REVISION:
            return [(work["finding_id"], work["finding_revision_id"])]
        if cause == CAUSE_ASSUMPTION:
            return self._store.latest_revisions_overlapping(tenant_id, site_id, work["affected_from"],
                                                            work["affected_to"])
        if cause == CAUSE_EVIDENCE:
            target = self._store.evidence_target(tenant_id, site_id, work["accepted_evidence_id"],
                                                 work["finding_id"], work["finding_revision_id"])
            if target["evidence"] is None or target["revision"] is None:
                raise EvidenceLocatorRefused(
                    ERROR_EVIDENCE_LOCATOR_NOT_IN_SITE,
                    f"Accepted evidence {work['accepted_evidence_id']} or FindingRevision "
                    f"{work['finding_revision_id']} of Finding {work['finding_id']} is not this Site's.")
            if not target["evidence"]["accepted"]:
                raise EvidenceLocatorRefused(
                    ERROR_EVIDENCE_NOT_ACCEPTED,
                    f"Evidence {work['accepted_evidence_id']} has no ACCEPTED disposition binding it.")
            reason = evidence_no_op(target)
            if reason is not None:
                raise NoOp(reason)
            return [(work["finding_id"], work["finding_revision_id"])]
        raise CauseNotSupported(f"Consequence work cause {cause!r} is not dispatched by this worker.")

    def process(self, tenant_id: UUID, site_id: UUID, work: dict[str, Any]) -> WorkOutcome:
        out = WorkOutcome(work["id"], work["cause"], False, 0)
        if any(work.get(k) is not None and str(work[k]) != str(v)
               for k, v in (("tenant_id", tenant_id), ("site_id", site_id))):
            # Another Site's work row: refused without fallback. Its attempt cannot be recorded in this scope.
            out.error_code = ERROR_WORK_SCOPE_MISMATCH
            out.error_detail = f"Work {work['id']} is not this tenant/Site's work."
            return out
        try:
            for finding_id, revision_id in self.targets(tenant_id, site_id, work):
                appended = self._store.append(derive(self._store, self._prices, tenant_id, site_id, finding_id,
                                                     revision_id))
                out.consequence_revision_ids.append(appended.consequence_revision_id)
                (out.replayed if appended.replayed else out.appended).append(appended.consequence_revision_id)
        except NoOp as no_op:
            out.no_op_reason = no_op.reason
        except CauseNotSupported as error:
            out.error_code, out.error_detail = ERROR_CAUSE_NOT_SUPPORTED, str(error)
        except EvidenceLocatorRefused as error:
            out.error_code, out.error_detail = error.code, str(error)
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
                consequence_revision_ids=tuple(out.consequence_revision_ids), skip_if_succeeded=True,
                **({"no_op_reason": out.no_op_reason} if out.no_op_reason is not None else {}))
        else:
            out.attempt_no = self._store.record_attempt(
                tenant_id, site_id, work["id"], succeeded=False, error_code=out.error_code,
                error_detail=out.error_detail[:2000] if out.error_detail else None)
        return out

    def run_pending(self, tenant_id: UUID, site_id: UUID, limit: int | None = None) -> list[WorkOutcome]:
        """Drain this Site's pending work oldest first, without the retry schedule or the Site claim (a test and
        walkthrough helper); failed items stay pending. The scheduled path is `run`."""
        pending = self._store.pending_work(tenant_id, site_id)
        return [self.process(tenant_id, site_id, w) for w in pending[:limit]]

    def run(self, tenant_id: UUID, site_id: UUID, limit: int, now: datetime | None = None) -> RunReport:
        """One scoped, bounded run (item 4). Holds the Site claim through selection and processing; when another
        runner holds it, reports the Site skipped and touches nothing. Never-attempted work is always due; failed
        work is due once `now` reaches its retry time. Due work is ordered by the instant it became eligible, then
        enqueue order; at most `limit` items are processed, each once."""
        if limit < 1:
            raise ValueError("A run processes at least one work item.")
        now = self._clock() if now is None else now
        report = RunReport(tenant_id, site_id, False, now)
        with self._store.claim_site(tenant_id, site_id) as claimed:
            if not claimed:
                return report
            report.claimed = True
            pending = self._store.pending_work(tenant_id, site_id)
            due = sorted((w for w in pending if w.get("last_attempt_no") is None or eligible_since(w) <= now),
                         key=lambda w: (eligible_since(w), w["enqueued_at"], str(w["id"])))
            report.deferred = len(pending) - len(due)
            report.outcomes = [self.process(tenant_id, site_id, w) for w in due[:limit]]
            report.backlog = len(pending) - sum(1 for o in report.outcomes if o.succeeded)
        return report
