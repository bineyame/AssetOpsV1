"""GAP-REASONS (D-E5.46): mini-grid estate coverage turns a selected-but-INDETERMINATE day into a gap with
READINGS_CONFLICT or NOT_ENOUGH_READINGS, read from the selected window's claim and limitation prefixes. Fake
one-transaction snapshots; no database."""

from __future__ import annotations

from datetime import date, timedelta

from assetops_backend.estate import coverage
from test_cov_partial import D0, K, S, T, Snap, day
from test_estate_coverage_local_days import LOCAL, N, grades

CONFLICT = ["AMBIGUOUS_COHORT: two report series overlap for one channel"]
TOO_FEW = ["NO_COHORT: no accepted reading in the window"]


def indeterminate(n: int, limits: list[str], **kw) -> dict:
    d = day(n, **kw)
    d.update(window_claim_level="INDETERMINATE", window_limitations=limits, cohort_status="SELECTED_UNIQUE")
    return d


def cov(days: list[dict], day_grades: dict[date, str] | None = None) -> dict:
    return coverage.site_coverage(Snap(days), T, S, coverage.MINI_GRID, D0, D0 + timedelta(days=N), K,
                                  day_grades=grades() if day_grades is None else day_grades)


def days_with(n: int, replacement: dict) -> list[dict]:
    return [replacement if i == n else day(i) for i in range(N)]


def test_conflicting_readings_day_is_a_partial_gap_with_its_reason() -> None:
    body = cov(days_with(2, indeterminate(2, CONFLICT)))
    assert body["state"] == "PARTIAL"
    assert body["days"]["requested"] == 7 and body["days"]["checked"] == 6
    assert body["days"]["gaps"] == [{"day": LOCAL[2].isoformat(), "state": "UNASSESSED", "reason": "READINGS_CONFLICT"}]
    assert body["days"]["text"] == "6 of 7 days assessed · 1 day not available yet"


def test_generator_series_ambiguous_is_also_conflicting_readings() -> None:
    body = cov(days_with(3, indeterminate(3, ["GENERATOR_SERIES_AMBIGUOUS: x"])))
    assert [g["reason"] for g in body["days"]["gaps"]] == ["READINGS_CONFLICT"]


def test_not_enough_readings_day_is_a_partial_gap_with_its_reason() -> None:
    body = cov(days_with(4, indeterminate(4, TOO_FEW)))
    assert body["state"] == "PARTIAL"
    assert body["days"]["gaps"] == [{"day": LOCAL[4].isoformat(), "state": "UNASSESSED",
                                     "reason": "NOT_ENOUGH_READINGS"}]


def test_no_generator_state_is_not_enough_readings() -> None:
    body = cov(days_with(4, indeterminate(4, ["NO_GENERATOR_STATE: none"])))
    assert [g["reason"] for g in body["days"]["gaps"]] == ["NOT_ENOUGH_READINGS"]


def test_conflict_outranks_not_enough_on_one_day() -> None:
    body = cov(days_with(2, indeterminate(2, TOO_FEW + CONFLICT)))
    assert [g["reason"] for g in body["days"]["gaps"]] == ["READINGS_CONFLICT"]


def test_an_indeterminate_day_without_a_data_prefix_is_not_a_gap() -> None:
    body = cov(days_with(2, indeterminate(2, ["COVERAGE_LOW: some channel is short"])))
    assert body["state"] == "CURRENT" and body["days"]["gaps"] == []


def test_a_determinate_claim_with_the_prefix_is_not_a_gap() -> None:
    d = indeterminate(2, CONFLICT)
    d["window_claim_level"] = "CANDIDATE"
    assert cov(days_with(2, d))["state"] == "CURRENT"


def test_no_readings_grade_outranks_the_data_reason() -> None:
    body = cov(days_with(2, indeterminate(2, CONFLICT)), grades(d2="NO_DATA"))
    assert body["days"]["gaps"] == [{"day": LOCAL[2].isoformat(), "state": "UNASSESSED", "reason": "NO_READINGS"}]


def test_system_work_outranks_the_data_reason() -> None:
    pending = indeterminate(2, CONFLICT, jobs=[{"status": "PENDING"}])
    body = cov(days_with(2, pending))
    assert body["state"] == "PENDING_RECOMPUTE"
    assert all(g["reason"] != "READINGS_CONFLICT" for g in body["days"]["gaps"])


def test_an_unselected_day_stays_not_analysed_not_a_data_reason() -> None:
    body = cov(days_with(2, day(2, selected=False)))
    assert body["days"]["gaps"] == [{"day": LOCAL[2].isoformat(), "state": "UNASSESSED", "reason": "NOT_ANALYSED"}]


def test_two_reasons_on_two_days_each_carry_their_own() -> None:
    days = [indeterminate(1, CONFLICT) if i == 1 else indeterminate(5, TOO_FEW) if i == 5 else day(i)
            for i in range(N)]
    body = cov(days)
    assert [(g["day"], g["reason"]) for g in body["days"]["gaps"]] == [
        (LOCAL[1].isoformat(), "READINGS_CONFLICT"), (LOCAL[5].isoformat(), "NOT_ENOUGH_READINGS")]
    assert body["days"]["checked"] == 5


def test_utc_rule_without_day_grades_is_unchanged() -> None:
    body = coverage.site_coverage(Snap(days_with(2, indeterminate(2, CONFLICT))), T, S, coverage.MINI_GRID, D0,
                                  D0 + timedelta(days=N), K)
    assert body["state"] == "CURRENT" and body["days"]["gaps"] == []
