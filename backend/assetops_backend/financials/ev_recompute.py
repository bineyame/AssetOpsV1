"""W2-07 commit 2: the EV gross tariff consequence worker, written against store protocols (no SQL driver).

Mirrors W2-04 `cold_recompute.py`. `process_one` works one trigger-created `ev_consequence_work` item inside the
store's locked repeatable-read unit. q3 R8: an overlapping PENDING/LEASED/FAILED `ev_charging` job is a retryable
refusal: the unit rolls back and one FAILED attempt with literal `PENDING_RECOMPUTE` is appended in a fresh
transaction; no consequence revision or link is written and the work stays selectable. Otherwise the unit reads
the exact selected `ev-session/1` basis, derives `ev-gross-tariff/1` (`financials/ev_money.py`), appends or replays
the one Site/window consequence and its priced links, and appends the SUCCEEDED attempt in that transaction. No
exact selection or no qualifying session succeeds with no consequence (never a fictional zero). Any failure is
recorded as a typed FAILED attempt. `run` takes the Site claim and processes due work under
`financials/recompute.py:retry_due_at`, bounded, each item once.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Protocol
from uuid import UUID

from assetops_backend.financials import ev_money as em
from assetops_backend.financials.recompute import retry_due_at

ERROR_PENDING = em.ERROR_PENDING
ERROR_STORE_UNAVAILABLE = "STORE_UNAVAILABLE"
ERROR_RECOMPUTE_FAILED = "EV_RECOMPUTE_FAILED"
ERROR_WORK_SCOPE_MISMATCH = "WORK_SCOPE_MISMATCH"


class EvUnitPort(Protocol):
    def work(self) -> dict[str, Any] | None: ...

    def pending(self, work: dict[str, Any]) -> bool: ...

    def basis(self, work: dict[str, Any]) -> em.EvMoneyBasis | None: ...

    def append(self, consequence: em.EvConsequence) -> tuple[UUID, bool]: ...

    def succeed(self) -> int: ...


class EvConsequenceStorePort(Protocol):
    def ev_unit(self, tenant_id: UUID, site_id: UUID, work_id: UUID) -> AbstractContextManager[EvUnitPort]: ...

    def ev_record_failure(self, tenant_id: UUID, site_id: UUID, work_id: UUID, error_code: str) -> int: ...

    def ev_pending_work(self, tenant_id: UUID, site_id: UUID) -> list[dict[str, Any]]: ...

    def ev_claim_site(self, tenant_id: UUID, site_id: UUID) -> AbstractContextManager[bool]: ...


@dataclass
class EvOutcome:
    work_id: UUID
    succeeded: bool
    attempt_no: int
    consequence_revision_id: UUID | None = None
    replayed: bool = False
    already_succeeded: bool = False
    error_code: str | None = None
    error_detail: str | None = None


@dataclass
class EvRunReport:
    tenant_id: UUID
    site_id: UUID
    claimed: bool
    now: datetime
    outcomes: list[EvOutcome] = field(default_factory=list)
    deferred: int = 0
    backlog: int = 0


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def eligible_since(work: dict[str, Any]) -> datetime:
    """Never-attempted work is eligible from its creation time; failed work from its retry time."""
    if work.get("last_attempt_no") is None:
        return work["created_at"]
    return retry_due_at(work["last_finished_at"], work["last_attempt_no"])


class _Refused(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code


class EvConsequenceWorker:
    def __init__(self, store: EvConsequenceStorePort, unavailable: tuple[type[BaseException], ...] = (),
                 clock: Callable[[], datetime] = _utc_now) -> None:
        self._store = store
        self._unavailable = unavailable
        self._clock = clock

    def process_one(self, tenant_id: UUID, site_id: UUID, work_id: UUID) -> EvOutcome:
        out = EvOutcome(work_id, False, 0)
        try:
            with self._store.ev_unit(tenant_id, site_id, work_id) as unit:
                work = unit.work()
                if work is None:
                    raise _Refused(ERROR_WORK_SCOPE_MISMATCH, f"Work {work_id} is not this tenant/Site's EV work.")
                if work["succeeded"]:
                    out.succeeded = out.already_succeeded = True
                    return out
                if unit.pending(work):
                    raise _Refused(ERROR_PENDING, "An overlapping EV assessment job is not settled.")
                basis = unit.basis(work)
                consequence = None if basis is None else em.derive(basis)
                if consequence is not None:
                    out.consequence_revision_id, out.replayed = unit.append(consequence)
                out.attempt_no = unit.succeed()
                out.succeeded = True
                return out
        except _Refused as error:
            out.error_code, out.error_detail = error.code, str(error)
        except self._unavailable as error:
            out.error_code, out.error_detail = ERROR_STORE_UNAVAILABLE, str(error)
        except Exception as error:  # noqa: BLE001 - any failure is recorded as typed pending work, never lost
            out.error_code, out.error_detail = ERROR_RECOMPUTE_FAILED, f"{type(error).__name__}: {error}"
        # The unit rolled back: nothing partial is stored. Record the typed failure in a fresh transaction.
        out.consequence_revision_id, out.replayed = None, False
        if out.error_code != ERROR_WORK_SCOPE_MISMATCH:
            try:
                out.attempt_no = self._store.ev_record_failure(tenant_id, site_id, work_id, out.error_code)
            except self._unavailable as error:
                out.error_detail = f"{out.error_detail}; the failed attempt was not recorded: {error}"
            if out.attempt_no == 0 and out.error_code is not None:
                # Another worker finished this item while this one waited: nothing recorded.
                out.already_succeeded = all(str(w["id"]) != str(work_id)
                                            for w in self._store.ev_pending_work(tenant_id, site_id))
                out.succeeded = out.already_succeeded
        return out

    def run(self, tenant_id: UUID, site_id: UUID, limit: int, now: datetime | None = None) -> EvRunReport:
        """One scoped, bounded run under the Site claim. Never-attempted work is due; failed work is due once `now`
        reaches `retry_due_at` of its last attempt. Due items are ordered by eligibility, then `(created_at, id)`;
        at most `limit` are processed, each once."""
        if limit < 1:
            raise ValueError("A run processes at least one work item.")
        now = self._clock() if now is None else now
        report = EvRunReport(tenant_id, site_id, False, now)
        with self._store.ev_claim_site(tenant_id, site_id) as claimed:
            if not claimed:
                return report
            report.claimed = True
            pending = self._store.ev_pending_work(tenant_id, site_id)
            due = sorted((w for w in pending if w.get("last_attempt_no") is None or eligible_since(w) <= now),
                         key=lambda w: (eligible_since(w), w["created_at"], str(w["id"])))
            report.deferred = len(pending) - len(due)
            report.outcomes = [self.process_one(tenant_id, site_id, w["id"]) for w in due[:limit]]
            report.backlog = len(pending) - sum(1 for o in report.outcomes if o.succeeded)
        return report

    def run_pending(self, tenant_id: UUID, site_id: UUID) -> list[EvOutcome]:
        """Drain this Site's pending EV work once, oldest first, without the retry schedule (tests/walkthrough)."""
        return [self.process_one(tenant_id, site_id, w["id"])
                for w in self._store.ev_pending_work(tenant_id, site_id)]
