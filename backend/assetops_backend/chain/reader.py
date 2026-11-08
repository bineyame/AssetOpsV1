"""SnapshotReader (CH-1a §4.4): the one answer to "how many days, of which grade".

``GradeCounts`` is the single graded-day count CH-5a and CH-6 render. Every
count comes from stored grades (``grading.classify_day`` at build time); this
module adds no second day-count rule.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from collections import namedtuple
from typing import Any, Collection, Mapping, Sequence
from uuid import UUID

from .grading import COMPLETE, LOW, NO_DATA, NOT_EXPECTED, PARTIAL, PENDING
from .ports import SnapshotRow, SnapshotStore


@dataclass(frozen=True)
class GradeCounts:
    requested: int
    expected: int
    complete: int
    partial: int
    low: int
    no_data: int
    not_expected: int
    pending: int
    enough_data_days: int

    def to_json(self) -> dict[str, int]:
        return asdict(self)


_DayRow = namedtuple("_DayRow", "local_day measure subject_ref grade")

# Day-level grade from its rows: the weakest row decides (every listed measure,
# every subject). Order from weakest to strongest; NOT_EXPECTED only when no row
# of the day is expected.
_WEAKEST_FIRST = (PENDING, NO_DATA, LOW, PARTIAL, COMPLETE)


def _day_grade(grades: Sequence[str]) -> str:
    expected = [g for g in grades if g != NOT_EXPECTED]
    if not expected:
        return NOT_EXPECTED
    for g in _WEAKEST_FIRST:
        if g in expected:
            return g
    return NO_DATA


#: K10 v2 (R3t): ASSET measures whose subjects are a site-setup declaration; only these can be declared absent.
DECLARED_SUBJECT_MEASURES = frozenset({"productive_kwh"})


def declared_none_day(revisions: Sequence[tuple[datetime, datetime | None, bool]],
                      lo: datetime, hi: datetime) -> bool:
    """R3t3: (valid_from, valid_to, has_productive) of the revisions known at k. True only when the revisions
    overlapping [lo, hi) (valid_from < hi and (valid_to is None or valid_to > lo)) are at least one, none has a
    productive load, and together they cover [lo, hi) with no gap: sorted by valid_from, cursor = lo; a revision
    with valid_from > cursor is a gap -> False; cursor = max(cursor, valid_to or +inf); finally cursor >= hi."""
    over = sorted((r for r in revisions if r[0] < hi and (r[1] is None or r[1] > lo)), key=lambda r: r[0])
    if not over or any(r[2] for r in over):
        return False
    cursor: datetime | None = lo      # None stands for +infinity (an open-ended revision)
    for vf, vt, _ in over:
        if cursor is not None and vf > cursor:
            return False
        cursor = None if vt is None or cursor is None else max(cursor, vt)
    return cursor is None or cursor >= hi


def applicable_measures(per_measure: Mapping[str, Sequence[str]], measures: Sequence[str],
                        none_declared: Collection[str] = ()) -> tuple[str, ...]:
    """R3t: `measures` without each m in `none_declared` ∩ DECLARED_SUBJECT_MEASURES that has no row this day,
    provided the day has a row of some other measure. A declared-absent measure is out of the day's grades; it is
    never COMPLETE and never a gap."""
    if not none_declared:
        return tuple(measures)
    drop = {m for m in none_declared
            if m in DECLARED_SUBJECT_MEASURES and not per_measure.get(m)
            and any(g for x, g in per_measure.items() if x != m)}
    return tuple(m for m in measures if m not in drop)


def _counts(rows: Sequence[SnapshotRow], from_day: date, to_day: date, measures: Sequence[str],
            none_declared: Mapping[date, Collection[str]] | None = None) -> GradeCounts:
    by_day: dict[date, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by_day[r.local_day][r.measure].append(r.grade)
    declared = none_declared or {}
    tally = {COMPLETE: 0, PARTIAL: 0, LOW: 0, NO_DATA: 0, NOT_EXPECTED: 0, PENDING: 0}
    enough = 0
    requested = (to_day - from_day).days + 1
    day = from_day
    while day <= to_day:
        per_measure = by_day.get(day, {})
        not_expected_day = any(NOT_EXPECTED in g for g in per_measure.values())
        grades: list[str] = []
        for m in applicable_measures(per_measure, measures, declared.get(day, ())):
            # A requested measure with no stored row for the day has no data, unless the day is not expected
            # (CH-1a L2: the operating calendar is per Site, so a NOT_EXPECTED row covers the whole day).
            grades.extend(per_measure.get(m) or [NOT_EXPECTED if not_expected_day else NO_DATA])
        g = _day_grade(grades)
        tally[g] += 1
        if all(x == COMPLETE for x in grades):
            enough += 1
        day += timedelta(days=1)
    return GradeCounts(
        requested=requested,
        expected=requested - tally[NOT_EXPECTED],
        complete=tally[COMPLETE],
        partial=tally[PARTIAL],
        low=tally[LOW],
        no_data=tally[NO_DATA],
        not_expected=tally[NOT_EXPECTED],
        pending=tally[PENDING],
        enough_data_days=enough,
    )


def day_grade(grades: Sequence[str]) -> str:
    """CH-6a2: the one day rule (`_day_grade`) under a public name; no rule change."""
    return _day_grade(grades)


def counts(rows: Sequence[Any], from_day: date, to_day: date, measures: Sequence[str],
           none_declared: Mapping[date, Collection[str]] | None = None) -> GradeCounts:
    """CH-6a2 (pre-flight "day grade rule"): `_counts` under a public name for the OutcomeEvaluator; no rule change.
    K10 v2 (R3t): `none_declared` passes through to the one rule."""
    return _counts(rows, from_day, to_day, measures, none_declared)


def grade_counts_of(facts: Any, measures: Sequence[str]) -> GradeCounts:
    """CH-5a2b (review L2): the `GradeCounts` of one `ChainRequest.day` result (`chain.read.DayFacts`: day -> measure
    -> subject -> grade) over its requested days, by the one `_counts` rule (with the facts' R3t declared-absent
    days, so the board and the counts cannot diverge)."""
    rows = [_DayRow(d, m, s, g) for d, per in facts.grades.items() for m, subj in per.items() for s, g in subj.items()]
    return _counts(rows, facts.days[0], facts.days[-1], measures, getattr(facts, "none_declared", {}))


class SnapshotReader:
    def __init__(self, store: SnapshotStore) -> None:
        self._store = store

    def latest(
        self,
        tenant_id: UUID,
        site_id: UUID,
        from_day: date,
        to_day: date,
        measures: Sequence[str] | None = None,
        known_at: datetime | None = None,
    ) -> list[SnapshotRow]:
        return self._store.read_latest(tenant_id, [site_id], from_day, to_day, measures, known_at)

    def latest_many(self, tenant_id: UUID, site_ids: Sequence[UUID], from_day: date, to_day: date,
                    measures: Sequence[str] | None = None, known_at: datetime | None = None) -> list[SnapshotRow]:
        """CH6b1-R Q3: `latest` for several Sites in ONE statement (the store's own `site_id = ANY(...)`)."""
        return self._store.read_latest(tenant_id, list(site_ids), from_day, to_day, measures, known_at)

    def grade_counts(
        self,
        tenant_id: UUID,
        site_id: UUID,
        from_day: date,
        to_day: date,
        measures: Sequence[str],
        known_at: datetime | None = None,
    ) -> GradeCounts:
        rows = self.latest(tenant_id, site_id, from_day, to_day, measures, known_at)
        return _counts(rows, from_day, to_day, measures)

    def grade_counts_many(
        self,
        tenant_id: UUID,
        site_ids: Sequence[UUID],
        from_day: date,
        to_day: date,
        measures_by_site: Mapping[UUID, Sequence[str]],
        known_at: datetime | None = None,
    ) -> dict[UUID, GradeCounts]:
        wanted = sorted({m for s in site_ids for m in measures_by_site.get(s, ())})
        rows = self._store.read_latest(tenant_id, list(site_ids), from_day, to_day, wanted, known_at)
        per_site: dict[UUID, list[SnapshotRow]] = defaultdict(list)
        for r in rows:
            per_site[r.site_id].append(r)
        out: dict[UUID, GradeCounts] = {}
        for s in site_ids:
            ms = list(measures_by_site.get(s, ()))
            out[s] = _counts([r for r in per_site.get(s, []) if r.measure in ms], from_day, to_day, ms)
        return out
