"""`graded_verdict@1`: the inputs `objectives.judge` / `judge_month` take (§A3.1), from the measure's day grades.
It makes no comparison of its own; the CH-6a2 evaluator calls the unchanged judges."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from assetops_backend.chain.grading import GRADES
from assetops_backend.chain.strategies.base import MEASURED, ContributionContext, Effect

_ORDER = {g: i for i, g in enumerate(GRADES)}


def grade_counts(rows: Iterable[Any]) -> dict[str, int]:
    """Per grade, the number of local days whose weakest subject row has it (`GRADES` order, worst last)."""
    worst: dict[Any, str] = {}
    for r in rows:
        g = worst.get(r.local_day)
        if g is None or _ORDER.get(r.grade, len(_ORDER)) > _ORDER.get(g, len(_ORDER)):
            worst[r.local_day] = r.grade
    out = {g: 0 for g in GRADES}
    for g in worst.values():
        out[g] = out.get(g, 0) + 1
    return out


class GradedVerdict:
    key, version = "graded_verdict", 1

    def effect(self, ctx: ContributionContext) -> Effect:
        return Effect(ctx.record.direction, basis=MEASURED, days=grade_counts(ctx.day_rows),
                      inputs={"measure": ctx.record.driver})
