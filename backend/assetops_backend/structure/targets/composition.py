"""5a unit 3 (spec `specs/5a-targets/spec.md` §4): the target read, wired. No route and nothing stored (D-5A.9).

The actual side is whatever `structure.composition.build_structure_read` wires on `main`; the budget lines come from
`commercial.composition.build_commercial_reads` (handshake P2: two stores, each disposed). A failure in the second
builder disposes the first.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from assetops_backend.structure.targets.lines import BudgetLineReader
from assetops_backend.structure.targets.read import TargetRead


@dataclass(frozen=True)
class TargetReadService:
    read: TargetRead
    dispose: Callable[[], None]


def build_target_read(database_url: str) -> TargetReadService:
    from assetops_backend.commercial.composition import build_commercial_reads
    from assetops_backend.structure.composition import build_structure_read

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

    return TargetReadService(TargetRead(BudgetLineReader(reads.months, reads.store), actual.read), dispose)


__all__ = ["TargetReadService", "build_target_read"]
