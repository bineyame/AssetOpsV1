"""CH-1b: the snapshot rebuild drain (build sheet CH-1b §3; design §4.3 `snapshot_dirty`, §6 S1).

``drain`` pops this Site's dirty (local day, measure) rows in (day, measure) order, rebuilds each through the one
``SnapshotBuilder`` (the builder always runs; its input fingerprint alone decides whether a revision is appended,
CH-1a review M1), then compare-and-deletes the row: the DELETE matches the ``marked_at`` it read, so a re-mark
made while the build ran keeps the row queued for the next drain.

A deadline or the item cap stops the drain with the rest still queued; that is reported as ``deferred``, never as a
failure (CH-2 L6).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Callable, Protocol, Sequence
from uuid import UUID

from .measures import MEASURES
from .ports import SiteRef


@dataclass(frozen=True)
class DirtyRow:
    local_day: date
    measure: str
    marked_at: datetime


class DirtyQueue(Protocol):
    def pop(self, tenant_id: UUID, site_id: UUID, limit: int) -> list[DirtyRow]:
        """Up to `limit` dirty rows of this Site, ordered by (local_day, measure)."""

    def queued(self, tenant_id: UUID, site_id: UUID) -> int: ...

    def done(self, tenant_id: UUID, site_id: UUID, row: DirtyRow) -> bool:
        """Delete the row only when its ``marked_at`` is still the one read; False when it was re-marked."""


class Builder(Protocol):
    def build(self, tenant_id: Any, site: SiteRef, local_day: date, measure: str,
              known_at: datetime | None = None) -> Sequence[Any]: ...


@dataclass
class DrainReport:
    processed: int = 0
    written: int = 0
    unchanged: int = 0
    re_marked: int = 0
    deferred: int = 0
    stopped: str | None = None  # "deadline" | "items" | None
    by_measure: dict[str, int] = field(default_factory=dict)

    def as_json(self) -> dict[str, Any]:
        return {"processed": self.processed, "written": self.written, "unchanged": self.unchanged,
                "re_marked": self.re_marked, "deferred": self.deferred, "stopped": self.stopped,
                "by_measure": dict(sorted(self.by_measure.items()))}


def drain(queue: DirtyQueue, builder: Builder, tenant_id: UUID, site: SiteRef, limit: int,
          deadline: Callable[[], bool] | None = None) -> DrainReport:
    report = DrainReport()
    rows = queue.pop(tenant_id, site.site_id, limit)
    for row in rows:
        if deadline is not None and deadline():
            report.stopped = "deadline"
            break
        if row.measure in MEASURES:
            out = builder.build(tenant_id, site, row.local_day, row.measure)
            wrote = sum(1 for w in out if getattr(w, "written", False))
            report.written += wrote
            report.unchanged += len(out) - wrote
            if wrote:
                report.by_measure[row.measure] = report.by_measure.get(row.measure, 0) + wrote
        if not queue.done(tenant_id, site.site_id, row):
            report.re_marked += 1
        report.processed += 1
    report.deferred = queue.queued(tenant_id, site.site_id)
    if report.stopped is None and report.deferred and len(rows) >= limit:
        report.stopped = "items"
    return report


class Deadline:
    """True once `now()` passes `at` less the slowest item seen so far, so the next item would not end in time."""

    def __init__(self, at: float, now: Callable[[], float]) -> None:
        self.at, self.now = at, now
        self._last = now()
        self._slowest = 0.0

    def __call__(self) -> bool:
        t = self.now()
        self._slowest = max(self._slowest, t - self._last)
        self._last = t
        return t + self._slowest >= self.at


__all__ = ["Deadline", "DirtyQueue", "DirtyRow", "DrainReport", "drain"]
