"""`graded_verdict@1`: the inputs `objectives.judge` / `judge_month` take (§A3.1), from the measure's day grades.
It makes no comparison of its own; the CH-6a2 evaluator calls the unchanged judges."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from assetops_backend.chain.grading import GRADES
from assetops_backend.chain.reader import day_grade
from assetops_backend.chain.strategies.base import MEASURED, ContributionContext, Effect


def day_grades(rows: Iterable[Any]) -> dict[Any, str]:
    """Per local day, the day grade of its rows by the one day rule (`reader.day_grade`, CH-6a1 L1): the weakest
    expected row decides; NOT_EXPECTED only when no row of the day is expected."""
    by_day: dict[Any, list[str]] = defaultdict(list)
    for r in rows:
        by_day[r.local_day].append(r.grade)
    return {d: day_grade(gs) for d, gs in by_day.items()}


def grade_counts(rows: Iterable[Any]) -> dict[str, int]:
    """Per grade, the number of local days with that day grade (`day_grades`)."""
    out = {g: 0 for g in GRADES}
    for g in day_grades(rows).values():
        out[g] = out.get(g, 0) + 1
    return out


class GradedVerdict:
    key, version = "graded_verdict", 1

    def effect(self, ctx: ContributionContext) -> Effect:
        return Effect(ctx.record.direction, basis=MEASURED, days=grade_counts(ctx.day_rows),
                      inputs={"measure": ctx.record.driver})
