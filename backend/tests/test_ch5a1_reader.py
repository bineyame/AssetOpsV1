"""CH-5a1 L0: the pure ChainReader rules (build sheet Part A §A9 item 1)."""

from __future__ import annotations

from collections import namedtuple
from datetime import date, datetime, timedelta, timezone

import pytest

from assetops_backend.chain import read as cr
from assetops_backend.chain.grading import COMPLETE, LOW, NO_DATA, NOT_EXPECTED, PARTIAL, PENDING

Row = namedtuple("Row", "local_day measure grade subject_ref", defaults=("SITE",))
D = date(2026, 10, 31)
K = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
E = datetime(2026, 10, 31, 16, tzinfo=timezone.utc)
M = ("a", "b")


@pytest.mark.parametrize("domain,req,ev,k,want", [
    ("mini_grid", None, E, K, None),          # mini: as known now
    ("mini_grid", K, E, K, K),                # mini: the request's cutoff
    ("cold_chain", None, E, None, E),         # cold: evidence cutoff, no bound
    ("cold_chain", K, E, K, E),               # cold: min(evidence, k)
    ("ev_charging", E, K, E, E),              # EV: k earlier than the evidence cutoff
    ("ev_charging", K, None, K, K),           # EV: evidence cutoff unknown -> the request's
    ("cold_chain", None, None, None, None),
])
def test_site_cutoff_truth_table(domain, req, ev, k, want):
    assert cr.site_cutoff(domain, req, ev, k) == want


@pytest.mark.parametrize("grades,want", [
    ({"a": COMPLETE, "b": COMPLETE}, cr.FULL),
    ({"a": COMPLETE, "b": PARTIAL}, cr.LIMITED),
    ({"a": COMPLETE, "b": LOW}, cr.LIMITED),
    ({"a": PARTIAL, "b": NO_DATA}, cr.LIMITED),
    ({"a": LOW, "b": NO_DATA}, cr.NONE),
    ({"a": LOW}, cr.NONE),                       # missing b = NO_DATA (Q9)
    ({"a": COMPLETE, "b": PENDING}, cr.UNKNOWN),
    ({"a": NOT_EXPECTED, "b": NOT_EXPECTED}, cr.UNKNOWN),
    ({"a": NOT_EXPECTED}, cr.UNKNOWN),           # a NOT_EXPECTED row covers the day (no expected row)
    ({}, cr.NONE),                               # nothing stored: NO_DATA on every measure
])
def test_readiness_of_truth_table(grades, want):
    rows = [Row(D, m, g) for m, g in grades.items()]
    assert cr.readiness_of(rows, (D,), M) == want


def test_readiness_pools_rows_over_the_day_set():
    rows = [Row(D, "a", COMPLETE), Row(D, "b", COMPLETE), Row(D + timedelta(1), "a", LOW),
            Row(D + timedelta(1), "b", LOW)]
    assert cr.readiness_of(rows, (D,), M) == cr.FULL
    assert cr.readiness_of(rows, (D, D + timedelta(1)), M) == cr.LIMITED
    assert cr.readiness_of([], (D,), ()) == cr.UNKNOWN   # a Site type with no measures


def test_day_settled():
    assert cr.day_settled([Row(D, "a", COMPLETE), Row(D, "b", NO_DATA)], D, M)
    assert not cr.day_settled([Row(D, "a", COMPLETE)], D, M)                       # b has no snapshot
    assert not cr.day_settled([Row(D, "a", COMPLETE), Row(D, "b", PENDING)], D, M)
    assert cr.day_settled([Row(D, "a", NOT_EXPECTED)], D, M)
    assert not cr.day_settled([], D, ())


def test_gap_days_are_pending_or_no_data_with_missing_rows_as_no_data():
    d1, d2, d3, d4 = (D + timedelta(i) for i in range(4))
    rows = [Row(d1, "a", COMPLETE), Row(d1, "b", COMPLETE), Row(d2, "a", PENDING), Row(d2, "b", COMPLETE),
            Row(d3, "a", COMPLETE), Row(d4, "a", NOT_EXPECTED)]
    assert cr.day_gaps(rows, (d1, d2, d3, d4, D - timedelta(1)), M) == (d2, d3, D - timedelta(1))


def test_board_day_is_the_site_local_day():
    lo, hi = cr.board_day(D, "Africa/Addis_Ababa")
    assert (lo, hi) == (datetime(2026, 10, 30, 21, tzinfo=timezone.utc),
                        datetime(2026, 10, 31, 21, tzinfo=timezone.utc))
    assert cr.board_day(D, None) == cr.board_day(D, "Etc/UTC") == (
        datetime(2026, 10, 31, tzinfo=timezone.utc), datetime(2026, 11, 1, tzinfo=timezone.utc))


def test_window_day_is_the_board_routes_day_rule():
    """CH5a2-R R7 (replaces `summary_day`): rule 2 picks the UTC calendar date; rule 3 reads `to` in its midnight
    frame; rule 1 a Site-local day pair. Each rule has its own test in `test_out_b4_read.py`."""
    midnight = datetime(2026, 11, 1, tzinfo=timezone.utc)
    assert cr.window_day(midnight - timedelta(days=1), midnight, "Etc/UTC") == D
    assert cr.window_day(midnight - timedelta(days=1), midnight, "Africa/Addis_Ababa") == D
    local_midnight = datetime(2026, 10, 31, 21, tzinfo=timezone.utc)                  # 1 Nov 00:00 Addis
    assert cr.window_day(None, local_midnight, "Africa/Addis_Ababa") == D
    assert cr.window_day(*cr.board_day(D, "Africa/Addis_Ababa"), "Africa/Addis_Ababa") == D


def test_local_days_of_a_window():
    lo, hi = datetime(2026, 10, 31, tzinfo=timezone.utc), datetime(2026, 11, 1, tzinfo=timezone.utc)
    assert cr.local_days(lo, hi, "Africa/Addis_Ababa") == (D, date(2026, 11, 1))
    assert cr.local_days(lo, hi, "Etc/UTC") == (D,)


def test_assessment_state_maps_unassessed():
    assert cr.assessment_state("UNASSESSED") == cr.UNKNOWN
    assert cr.assessment_state("CURRENT") == "CURRENT"
    assert cr.assessment_state(None) is None
