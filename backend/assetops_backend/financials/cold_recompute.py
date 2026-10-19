"""W2-04 commit 2: the cold consequence worker, written against store protocols (no SQL driver).

`.agent/W2-04-build-spec.md` "Money schema `0023` and rules" (last paragraph) and "Implementer dry-read".
`process_one` works one trigger-created `cold_consequence_work` item inside the store's locked repeatable-read
unit: it reads each exact cold FindingRevision basis the item names, refuses a missing/foreign/unpaired basis
(`COLD_BASIS_MISMATCH`), derives `cold-exposure/1` and writes the consequence revisions, their evidence links and
the SUCCEEDED attempt in that one transaction. An item whose Findings warrant no exposure (a START_RESPONSE, an
unwarranted or withdrawn revision, an episode with no Finding) succeeds with `[]` IDs. Any failure rolls the unit
back and appends a typed FAILED attempt in a fresh transaction; the work stays pending (no status UPDATE).
`run` takes the Site claim and processes due work under `financials/recompute.py:retry_due_at` (1, 2, 4, 8,
16 minutes), bounded, each item once, so one bad item cannot starve the others.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Protocol
from uuid import UUID

from assetops_backend.financials import cold_consequence as cc
from assetops_backend.financials.recompute import retry_due_at

ERROR_BASIS_MISMATCH = cc.ERROR_BASIS_MISMATCH
ERROR_STORE_UNAVAILABLE = "STORE_UNAVAILABLE"
ERROR_RECOMPUTE_FAILED = "COLD_RECOMPUTE_FAILED"
ERROR_WORK_SCOPE_MISMATCH = "WORK_SCOPE_MISMATCH"


class ColdUnitPort(Protocol):
    def work(self) -> dict[str, Any] | None: ...

    def targets(self, work: dict[str, Any]) -> list[UUID]: ...

    def basis(self, finding_revision_id: UUID) -> cc.ColdBasis | None: ...

    def append(self, consequence: cc.ColdConsequence) -> tuple[UUID, bool]: ...

    def succeed(self, revision_ids: list[UUID]) -> int: ...


class ColdConsequenceStorePort(Protocol):
    def cold_unit(self, tenant_id: UUID, site_id: UUID, work_id: UUID) -> AbstractContextManager[ColdUnitPort]: ...

    def cold_record_failure(self, tenant_id: UUID, site_id: UUID, work_id: UUID, error_code: str) -> int: ...

    def cold_pending_work(self, tenant_id: UUID, site_id: UUID) -> list[dict[str, Any]]: ...

    def cold_claim_site(self, tenant_id: UUID, site_id: UUID) -> AbstractContextManager[bool]: ...


@dataclass
class ColdOutcome:
    work_id: UUID
    succeeded: bool
    attempt_no: int
    consequence_revision_ids: list[UUID] = field(default_factory=list)
    appended: list[UUID] = field(default_factory=list)
    replayed: list[UUID] = field(default_factory=list)
    already_succeeded: bool = False
    error_code: str | None = None
    error_detail: str | None = None


@dataclass
class ColdRunReport:
    tenant_id: UUID
    site_id: UUID
    claimed: bool
    now: datetime
    outcomes: list[ColdOutcome] = field(default_factory=list)
    deferred: int = 0
    backlog: int = 0


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def eligible_since(work: dict[str, Any]) -> datetime:
    """Never-attempted work is eligible from its enqueue time; failed work from its retry time."""
    if work.get("last_attempt_no") is None:
        return work["enqueued_at"]
    return retry_due_at(work["last_finished_at"], work["last_attempt_no"])


class _Refused(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code


class ColdConsequenceWorker:
    def __init__(self, store: ColdConsequenceStorePort, unavailable: tuple[type[BaseException], ...] = (),
                 clock: Callable[[], datetime] = _utc_now) -> None:
        self._store = store
        self._unavailable = unavailable
        self._clock = clock

    def process_one(self, tenant_id: UUID, site_id: UUID, work_id: UUID) -> ColdOutcome:
        out = ColdOutcome(work_id, False, 0)
        try:
            with self._store.cold_unit(tenant_id, site_id, work_id) as unit:
                work = unit.work()
                if work is None:
                    raise _Refused(ERROR_WORK_SCOPE_MISMATCH, f"Work {work_id} is not this tenant/Site's cold work.")
                if work["succeeded"]:
                    out.succeeded = out.already_succeeded = True
                    return out
                for finding_revision_id in unit.targets(work):
                    basis = unit.basis(finding_revision_id)
                    if basis is None:
                        raise cc.ColdBasisMismatch(
                            f"FindingRevision {finding_revision_id} is not a cold revision of this Site.")
                    cc.check_basis(basis, work)
                    consequence = cc.derive(basis)
                    if consequence is None:
                        continue
                    revision_id, replayed = unit.append(consequence)
                    out.consequence_revision_ids.append(revision_id)
                    (out.replayed if replayed else out.appended).append(revision_id)
                out.attempt_no = unit.succeed(out.consequence_revision_ids)
                out.succeeded = True
                return out
        except _Refused as error:
            out.error_code, out.error_detail = error.code, str(error)
        except cc.ColdBasisMismatch as error:
            out.error_code, out.error_detail = ERROR_BASIS_MISMATCH, str(error)
        except self._unavailable as error:
            out.error_code, out.error_detail = ERROR_STORE_UNAVAILABLE, str(error)
        except Exception as error:  # noqa: BLE001 - any failure is recorded as typed pending work, never lost
            out.error_code, out.error_detail = ERROR_RECOMPUTE_FAILED, f"{type(error).__name__}: {error}"
        # The unit rolled back: nothing partial is stored. Record the typed failure in a fresh transaction.
        out.consequence_revision_ids, out.appended, out.replayed = [], [], []
        if out.error_code != ERROR_WORK_SCOPE_MISMATCH:
            try:
                out.attempt_no = self._store.cold_record_failure(tenant_id, site_id, work_id, out.error_code)
            except self._unavailable as error:
                out.error_detail = f"{out.error_detail}; the failed attempt was not recorded: {error}"
            if out.attempt_no == 0 and out.error_code is not None:
                # Another worker finished this item while this one waited (see `cold_unit`): nothing recorded.
                out.already_succeeded = bool(self._finished(tenant_id, site_id, work_id))
                out.succeeded = out.already_succeeded
        return out

    def _finished(self, tenant_id: UUID, site_id: UUID, work_id: UUID) -> bool:
        return all(str(w["id"]) != str(work_id) for w in self._store.cold_pending_work(tenant_id, site_id))

    def run(self, tenant_id: UUID, site_id: UUID, limit: int, now: datetime | None = None) -> ColdRunReport:
        """One scoped, bounded run under the Site claim. Never-attempted work is due; failed work is due once `now`
        reaches `retry_due_at` of its last attempt. Due items are ordered by eligibility, then `(enqueued_at, id)`;
        at most `limit` are processed, each once."""
        if limit < 1:
            raise ValueError("A run processes at least one work item.")
        now = self._clock() if now is None else now
        report = ColdRunReport(tenant_id, site_id, False, now)
        with self._store.cold_claim_site(tenant_id, site_id) as claimed:
            if not claimed:
                return report
            report.claimed = True
            pending = self._store.cold_pending_work(tenant_id, site_id)
            due = sorted((w for w in pending if w.get("last_attempt_no") is None or eligible_since(w) <= now),
                         key=lambda w: (eligible_since(w), w["enqueued_at"], str(w["id"])))
            report.deferred = len(pending) - len(due)
            report.outcomes = [self.process_one(tenant_id, site_id, w["id"]) for w in due[:limit]]
            report.backlog = len(pending) - sum(1 for o in report.outcomes if o.succeeded)
        return report

    def run_pending(self, tenant_id: UUID, site_id: UUID) -> list[ColdOutcome]:
        """Drain this Site's pending cold work once, oldest first, without the retry schedule (tests/walkthrough)."""
        return [self.process_one(tenant_id, site_id, w["id"])
                for w in self._store.cold_pending_work(tenant_id, site_id)]
