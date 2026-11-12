"""HON-1 (architect sequence 2026-11-11 rev 3, "HON-1 complete-readings honesty"): a day the analysis could not use
for a data fact (D-E5.46 READINGS_CONFLICT / NOT_ENOUGH_READINGS) is not a "complete readings" day, even when every
reading arrived (chain grade COMPLETE). One rule (`chain.claims.without_data_gap_days`) behind every count: the
Portfolio coverage line and its lead, the count cards' basis, the cards' "Why?" days, and the Site Overview day line.
No database: the CH-6b1 fixture summary (`test_ch6b_estate_chain`) with the injected data-gap provider."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import test_ch6b_estate_chain as EC  # noqa: E402
import test_s5_overview_read as S5  # noqa: E402

from assetops_backend.chain import claims  # noqa: E402
from assetops_backend.chain.reader import GradeCounts  # noqa: E402

CONFLICT_DAY = date(2026, 10, 30)   # a Kobo window day every reading of which arrived (graded COMPLETE)
REASONS = ("READINGS_CONFLICT", "NOT_ENOUGH_READINGS")


def _counts(**kw) -> GradeCounts:
    base = dict(requested=7, expected=7, complete=7, partial=0, low=0, no_data=0, not_expected=0, pending=0,
                enough_data_days=7)
    return GradeCounts(**{**base, **kw})


def _summary(monkeypatch, gaps):
    seen = []
    monkeypatch.setattr(claims, "data_gap_provider",
                        lambda t, codes, lo, hi, k: seen.append(tuple(codes)) or gaps)
    _, body, _, _ = EC._summary(EC.ManyPort())
    return body, seen


# ---------------------------------------------------------------- the one rule

@pytest.mark.parametrize("reason", REASONS)
def test_a_complete_graded_data_gap_day_is_not_a_complete_readings_day(reason) -> None:
    grades = {date(2026, 10, 25 + i): "COMPLETE" for i in range(7)}
    out = claims.without_data_gap_days(_counts(), grades, {CONFLICT_DAY: reason})
    assert (out.complete, out.expected, out.partial, out.no_data) == (6, 7, 0, 0)


def test_a_gap_day_already_counted_as_not_complete_is_not_taken_twice() -> None:
    grades = {CONFLICT_DAY: "PARTIAL"}
    counts = _counts(complete=6, partial=1)
    assert claims.without_data_gap_days(counts, grades, {CONFLICT_DAY: "READINGS_CONFLICT"}) is counts
    assert claims.without_data_gap_days(counts, grades, {}) is counts
    assert claims.without_data_gap_days(None, grades, {CONFLICT_DAY: "READINGS_CONFLICT"}) is None


# ---------------------------------------------------------------- the Portfolio line, lead and cards

@pytest.mark.parametrize("reason", REASONS)
def test_portfolio_coverage_counts_the_data_gap_day_out(monkeypatch, reason) -> None:
    body, seen = _summary(monkeypatch, {"KOBO-001": {CONFLICT_DAY: reason}})
    assert seen and "KOBO-001" in seen[0] and "COLD-LAB-001" not in seen[0]   # mini-grid Sites only
    line = body["coverage_line"]
    by = {s["site_code"]: s for s in line["sites"]}
    # was "complete readings on 6 of 7 days" (the conflict day read complete); the gap clause names the day
    assert by["KOBO-001"]["text"] == "Kobo: complete readings on 5 of 7 days · 1 with no readings received"
    assert by["KOBO-001"]["complete"] is False and line["state"] == "INCOMPLETE"
    assert line["days_text"].startswith("Kobo: Complete readings on 5 of 7 days · 1 with no readings received")
    # PF-C2: Grow's income days are the line's day set, so its "Why?" days read the line's count, never "6 of 7"
    assert body["cards"]["GROW_REVENUE"]["days_line"].startswith("Kobo: Complete readings on 5 of 7 days ·")


@pytest.mark.parametrize("reason", REASONS)
def test_the_count_claims_read_the_same_days(monkeypatch, reason) -> None:
    monkeypatch.setattr(claims, "data_gap_provider", lambda *a: {"KOBO-001": {CONFLICT_DAY: reason}})
    svc = EC._summary(EC.ManyPort())[0]
    with EC.read_scope.scope("test:hon1"):
        req = svc.s.chain_reader.request(EC.BC.TENANT, None)
        counted = claims.estate_count_claims(req, [EC.KOBO, EC.COLD, EC.EV], EC.LO, EC.HI, [],
                                             (EC.read.PortUnavailable, AttributeError))
    assert counted.days["KOBO-001"].complete == 5
    for claim in counted.claims.values():
        assert claim.days["complete"] == 5 + 7 + 1 and claim.days["expected"] == 7 + 7 + 1
    # the fixture's thread read fails (values NOT_KNOWN); the opportunity count (0) reads the days basis
    assert counted.claims[claims.OPPORTUNITIES].basis == "CHECKED_DAYS"
    assert counted.arrived["KOBO-001"].complete == 6 and "COLD-LAB-001" not in counted.arrived


def test_the_rule_applies_to_mini_grid_sites_only(monkeypatch) -> None:
    body, _ = _summary(monkeypatch, {"COLD-LAB-001": {CONFLICT_DAY: "READINGS_CONFLICT"}})
    by = {s["site_code"]: s for s in body["coverage_line"]["sites"]}
    # GAP-REASONS wires the data-gap reasons for mini-grid days only; a cold Site's count is unchanged
    assert by["COLD-LAB-001"]["complete"] is True and "complete readings on 7 of 7 days" in by["COLD-LAB-001"]["text"]


def test_an_all_good_week_is_unchanged(monkeypatch) -> None:
    base = EC._summary(EC.ManyPort())[1]
    body, seen = _summary(monkeypatch, {})
    assert seen and body["coverage_line"] == base["coverage_line"] and body["cards"] == base["cards"]
    by = {s["site_code"]: s for s in body["coverage_line"]["sites"]}
    assert by["KOBO-001"]["text"] == "Kobo: complete readings on 6 of 7 days · 1 with no readings received"


def test_an_unreadable_provider_is_noted_and_changes_nothing(monkeypatch) -> None:
    base = EC._summary(EC.ManyPort())[1]

    def boom(*a):
        raise RuntimeError("estate read down")

    monkeypatch.setattr(claims, "data_gap_provider", boom)
    body = EC._summary(EC.ManyPort())[1]
    assert body["coverage_line"] == base["coverage_line"]


# ---------------------------------------------------------------- the Site Overview day line

class _GapWorld(S5.World):
    def __init__(self, reason_limits, cohort=None, **kw) -> None:
        super().__init__(**kw)
        self.reason_limits, self.cohort = reason_limits, cohort

    def detail(self, t, s, day):
        body = super().detail(t, s, day)
        body["window_assessment"] = {"id": "wa-1", "claim_level": "INDETERMINATE", "result": {}}
        body["selection"] = {**body["selection"], "cohort_status": self.cohort}
        body["limitations"] = list(self.reason_limits)
        return body


@pytest.mark.parametrize("limits,cohort,reason", [
    (["AMBIGUOUS_COHORT: two cohorts overlap"], None, "READINGS_CONFLICT"),
    ([], "EMPTY", "NOT_ENOUGH_READINGS"),
])
def test_the_site_overview_names_the_days_data_gap(limits, cohort, reason) -> None:
    body = S5.run(_GapWorld(limits, cohort))
    assert body["freshness"]["data_gap_reason"] == reason


def test_an_analysed_day_has_no_data_gap_reason() -> None:
    assert S5.run(S5.World())["freshness"]["data_gap_reason"] is None
