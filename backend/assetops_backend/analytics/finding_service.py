"""S4-01 Finding matching over the selected dispatch read (`finding-episode-1`).

Reads every assessed window of a Site through `DispatchReadService.window`, so
"CURRENT" here is exactly the read's derived status, then plans with the pure
`finding_episode.plan` and persists through the Finding store under the fence
taken before the read. A fence that moved means a selection or job changed
mid-pass: the pass is retried from a fresh read, never half-applied.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import ModuleType
from typing import Any, Callable
from uuid import UUID

from assetops_backend.analytics import dispatch_v3
from assetops_backend.analytics.dispatch_read import DispatchReadService
from assetops_backend.analytics.finding_episode import WindowBasis, plan, window_basis


@dataclass(frozen=True)
class MatchOutcome:
    planned: int
    finding_ids: tuple[str, ...]
    revision_ids: tuple[str, ...]
    window_statuses: dict[str, str]
    #: The matcher fence the successful pass applied under (S4-02d: the schedule records it, advanced by the
    #: revisions this pass appended, as the Site's last completed fence).
    fence: Any = None


class FindingMatcher:
    def __init__(self, assessments: Any, findings: Any, *, model: ModuleType | Any = dispatch_v3,
                 now: Callable[[], datetime] = lambda: datetime.now(timezone.utc), fence_moved: type = Exception,
                 attempts: int = 3) -> None:
        self.read = DispatchReadService(assessments, model=model)
        self.findings, self.model, self.now = findings, model, now
        self.fence_moved, self.attempts = fence_moved, attempts

    def bases(self, tenant_id: UUID, site_id: UUID) -> tuple[list[dict[str, Any]], list[WindowBasis]]:
        """Every assessed window read, with the selected run's exact accepted input evidence for CURRENT windows
        (typed generator reports for the Q17 stop proof; read once per run)."""
        reads = [self.read.window(tenant_id, site_id, day)
                 for day in self.findings.assessed_days(tenant_id, site_id, self.model.ANALYTIC_ID)]
        runs: dict[str, list[dict[str, Any]] | None] = {}
        bases = []
        for r in reads:
            run_id = (r.get("selection") or {}).get("run_id")
            evidence = None
            if r["status"] == "CURRENT" and run_id is not None:
                if str(run_id) not in runs:
                    detail = self.read.run(tenant_id, site_id, UUID(str(run_id)))
                    runs[str(run_id)] = None if detail is None else detail["evidence"]
                evidence = runs[str(run_id)]
            bases.append(window_basis(r, evidence))
        return reads, bases

    def match(self, tenant_id: UUID, site_id: UUID) -> MatchOutcome:
        for attempt in range(self.attempts):
            analytic = self.model.ANALYTIC_ID
            fence = self.findings.fence(tenant_id, site_id, analytic)
            reads, bases = self.bases(tenant_id, site_id)
            writes = plan(bases, self.findings.episodes(tenant_id, site_id), self.model.MODEL_VERSION)
            statuses = {r["window"]["start"].date().isoformat(): r["status"] for r in reads}
            try:
                applied = self.findings.apply(tenant_id, site_id, analytic, writes, fence, self.now())
            except self.fence_moved:
                if attempt + 1 == self.attempts:
                    raise
                continue
            return MatchOutcome(len(writes), applied.finding_ids, applied.revision_ids, statuses, fence)
        raise AssertionError("unreachable")
