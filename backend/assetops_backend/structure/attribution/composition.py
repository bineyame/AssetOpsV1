"""5b unit 3 (spec §4.2; handshake R6): the bridge read, wired. No route and nothing stored.

The one module under `structure/attribution/` that may reach `commercial` (wiring). The actual side is
`structure.composition.build_structure_read`; the budget lines come from `commercial.composition.build_commercial_reads`
(one pool each, as 5a's `build_target_read`, whose service does not expose the actual read). A failure in the second
builder disposes the first; `dispose` disposes both.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from assetops_backend.structure.attribution.read import BridgeRead


@dataclass(frozen=True)
class BridgeReadService:
    read: BridgeRead
    dispose: Callable[[], None]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_bridge_read(database_url: str) -> BridgeReadService:
    from assetops_backend.commercial.composition import build_commercial_reads
    from assetops_backend.structure.composition import build_structure_read
    from assetops_backend.structure.targets.lines import BudgetLineReader
    from assetops_backend.structure.targets.read import TargetRead

    actual = build_structure_read(database_url)
    try:
        reads = build_commercial_reads(database_url)
    except BaseException:
        actual.dispose()  # never leak the first service when the second builder raises
        raise

    def dispose() -> None:
        try:
            actual.dispose()
        finally:
            reads.dispose()

    targets = TargetRead(BudgetLineReader(reads.months, reads.store), actual.read)
    return BridgeReadService(BridgeRead(actual.read, targets, _utc_now), dispose)


__all__ = ["BridgeReadService", "build_bridge_read"]
