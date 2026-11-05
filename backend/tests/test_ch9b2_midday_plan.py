"""CH-9b2 L0 (build sheet CH-9b R2, CH9b2-R Q2-Q7): the pure `midday-productive-shift-1` day choice and registry."""

from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from assetops_backend.actions import verification_families as vf
from assetops_backend.actions.ports import ActionRefused

EFF = date(2026, 10, 20)


def row(day: date, grade: str, subject: str = "asset:mill", value: float = 1.0, measure: str = vf.MEASURE):
    return SimpleNamespace(local_day=day, grade=grade, subject_ref=subject, measure=measure, value={"kwh": value},
                           revision=1, input_fp="fp")


def days_before(*offsets: int) -> list[date]:
    return [EFF - timedelta(days=o) for o in offsets]


def grades_of(rows, days):
    return vf.day_grades(rows, days)


def test_baseline_is_the_last_three_complete_days_before_the_effective_day() -> None:
    cand = vf.baseline_candidates(EFF)
    assert cand[0] == EFF - timedelta(days=1) and cand[-1] == EFF - timedelta(days=14) and EFF not in cand
    rows = [row(d, "COMPLETE") for d in days_before(1, 2, 3, 4)] + [row(EFF, "COMPLETE")]
    sel = vf.baseline_selection(grades_of(rows, cand), EFF)
    assert sel["state"] == "COMPLETE" and sel["found"] == 3
    assert sel["days"] == [d.isoformat() for d in days_before(3, 2, 1)]


def test_gaps_and_low_days_are_skipped_by_grade() -> None:
    cand = vf.baseline_candidates(EFF)
    rows = [row(EFF - timedelta(days=1), "LOW"), row(EFF - timedelta(days=2), "PARTIAL"),
            row(EFF - timedelta(days=4), "COMPLETE"), row(EFF - timedelta(days=6), "PENDING"),
            row(EFF - timedelta(days=7), "COMPLETE"), row(EFF - timedelta(days=9), "COMPLETE"),
            row(EFF - timedelta(days=10), "COMPLETE")]
    sel = vf.baseline_selection(grades_of(rows, cand), EFF)
    assert sel["days"] == [d.isoformat() for d in days_before(9, 7, 4)]
    assert sel["grades"][(EFF - timedelta(days=3)).isoformat()] == "NO_DATA"  # the gap: no row at all
    assert sel["grades"][(EFF - timedelta(days=1)).isoformat()] == "LOW"


def test_one_weak_subject_row_makes_the_day_not_count() -> None:
    cand = vf.baseline_candidates(EFF)
    rows = [row(d, "COMPLETE") for d in days_before(1, 2, 3, 4)] + [row(EFF - timedelta(days=2), "LOW", "asset:pump")]
    sel = vf.baseline_selection(grades_of(rows, cand), EFF)
    assert sel["days"] == [d.isoformat() for d in days_before(4, 3, 1)]


def test_fewer_than_three_complete_days_freezes_short_with_the_not_judged_text() -> None:
    cand = vf.baseline_candidates(EFF)
    rows = [row(d, "COMPLETE") for d in days_before(2, 13)] + [row(EFF - timedelta(days=15), "COMPLETE")]
    sel = vf.baseline_selection(grades_of(rows, cand), EFF)
    assert sel["state"] == "SHORT" and sel["found"] == 2  # day 15 is outside the 14-day look-back
    assert vf.short_text(sel) == "Not judged yet: only 2 of 3 fully checked days before the change"
    full = vf.baseline_selection(grades_of([row(d, "COMPLETE") for d in days_before(1, 2, 3)], cand), EFF)
    assert vf.short_text(full) is None


def test_later_window_looks_at_most_fourteen_days_ahead_and_excludes_the_effective_day() -> None:
    later = vf.later_candidates(EFF)
    assert later[0] == EFF + timedelta(days=1) and later[-1] == EFF + timedelta(days=14) and len(later) == 14
    rows = [row(EFF, "COMPLETE"), row(EFF + timedelta(days=3), "COMPLETE"), row(EFF + timedelta(days=12), "COMPLETE"),
            row(EFF + timedelta(days=15), "COMPLETE"), row(EFF + timedelta(days=16), "COMPLETE")]
    picked = vf.choose_days(vf.day_grades(rows, later), later)
    assert picked == [EFF + timedelta(days=3), EFF + timedelta(days=12)]  # only two inside the look-ahead


def test_choice_is_by_grade_only_never_by_value() -> None:
    cand = vf.baseline_candidates(EFF)
    low_values = [row(d, "COMPLETE", value=0.1) for d in days_before(1, 2, 3, 4, 5)]
    high_values = [row(d, "COMPLETE", value=99.0) for d in days_before(1, 2, 3, 4, 5)]
    assert vf.baseline_selection(grades_of(low_values, cand), EFF) == \
        vf.baseline_selection(grades_of(high_values, cand), EFF)


def test_other_measures_do_not_grade_the_day() -> None:
    cand = vf.baseline_candidates(EFF)
    rows = [row(d, "COMPLETE") for d in days_before(1, 2, 3)] + \
        [row(EFF - timedelta(days=1), "LOW", measure="daylight_headroom_kw")]
    assert vf.baseline_selection(grades_of(rows, cand), EFF)["state"] == "COMPLETE"


def test_target_is_the_owner_rule_verbatim_and_no_guardrails() -> None:
    assert vf.TARGET == {"rule": "10*mean(later) >= 11*mean(baseline) productive_kwh[midday]",
                         "over": "COMPLETE days of each window", "ratio": [11, 10], "declared_by": "owner 2026-11-05"}


def test_registry_dispatches_on_the_plan_family() -> None:
    assert vf.family_of({"rule_id": "reserve-trial-1"}).plan_version == "reserve-trial-verification-1"
    assert isinstance(vf.family_of({"rule_id": "midday-productive-shift-1"}), vf.MiddayShift)
    with pytest.raises(ActionRefused):
        vf.family_of({"rule_id": "unknown-1"})
