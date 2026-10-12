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
from assetops_backend.analytics.finding_episode import plan, window_basis


@dataclass(frozen=True)
class MatchOutcome:
    planned: int
    finding_ids: tuple[str, ...]
    revision_ids: tuple[str, ...]
    window_statuses: dict[str, str]


class FindingMatcher:
    def __init__(self, assessments: Any, findings: Any, *, model: ModuleType | Any = dispatch_v3,
                 now: Callable[[], datetime] = lambda: datetime.now(timezone.utc), fence_moved: type = Exception,
                 attempts: int = 3) -> None:
        self.read = DispatchReadService(assessments, model=model)
        self.findings, self.model, self.now = findings, model, now
        self.fence_moved, self.attempts = fence_moved, attempts

    def match(self, tenant_id: UUID, site_id: UUID) -> MatchOutcome:
        for attempt in range(self.attempts):
            analytic = self.model.ANALYTIC_ID
            fence = self.findings.fence(tenant_id, site_id, analytic)
            reads = [self.read.window(tenant_id, site_id, day)
                     for day in self.findings.assessed_days(tenant_id, site_id, analytic)]
            writes = plan([window_basis(r) for r in reads], self.findings.episodes(tenant_id, site_id),
                          self.model.MODEL_VERSION)
            statuses = {r["window"]["start"].date().isoformat(): r["status"] for r in reads}
            try:
                applied = self.findings.apply(tenant_id, site_id, analytic, writes, fence, self.now())
            except self.fence_moved:
                if attempt + 1 == self.attempts:
                    raise
                continue
            return MatchOutcome(len(writes), applied.finding_ids, applied.revision_ids, statuses)
        raise AssertionError("unreachable")
