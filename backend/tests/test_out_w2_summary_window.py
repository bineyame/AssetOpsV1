"""OUT-W W2, rewritten by CH6b1-R Q2 (R14): the estate summary judges every cold or EV Site on the requested window
(PERIOD) and every mini Site on `window_day` (DAY). The OUT-W latest-event choice is gone: the judged window is the
requested one. CH6b1-R3 (updated): the cold/EV rows read their selected windows over the requested window in ONE
batch (the only estate read) and keep the contained ones; the board window never moves to an event; and the Overview
link is the plain Site link. Fake estate and a recording fake board, no database; `known_at` is
passed through, never invented."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from assetops_backend.chain.read import window_days
from assetops_backend.outcomes.catalogue import CATEGORIES
from assetops_backend.site_outcomes import read
from assetops_backend.site_outcomes.read import BoardServices, SiteOutcomeBoardService, SiteRef, wire

UTC = timezone.utc
T = uuid4()
KOBO = SiteRef(T, uuid4(), "KOBO-001", "Kobo", "MINIGRID", "Africa/Nairobi")
COLD = SiteRef(T, uuid4(), "COLD-LAB-001", "GreenHarvest", "COLDCHAIN", None)
EVS = SiteRef(T, uuid4(), "EV-LAB-001", "Depot", "EV_CHARGING", None)
D = datetime(2026, 10, 6, tzinfo=UTC)
LO, HI = D, D + timedelta(days=1)


def at(h: int, m: int = 0) -> datetime:
    return D + timedelta(hours=h, minutes=m)


class Estate:
    """An estate whose selected windows hold an event inside the period: the summary reads it (one batch, cold/EV
    Sites only) but never judges on it instead of the period."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def site_selected_windows(self, *a):
        return [{"window_start": at(14), "window_end": at(15), "selected_at": at(16), "seq": 1, "selection_id": "s"}]

    def site_selected_windows_many(self, tenant_id, codes, lo, hi, known_at=None, *, snap=None):
        self.calls.append((tuple(codes), lo, hi, known_at))
        return {c: self.site_selected_windows(tenant_id, c, lo, hi, known_at) for c in codes}


@pytest.fixture
def boards(monkeypatch):
    """A fake board recording `day`/`lo`/`hi`/`known_at`/`node_days`, echoing them as the board's own window."""
    calls: list[dict] = []

    def board(self, site, *, day=None, lo=None, hi=None, known_at=None, pin=None, node_days=None, windows=None):
        calls.append({"site": site.site_code, "day": day, "lo": lo, "hi": hi, "known_at": known_at,
                      "node_days": node_days, "windows": windows})
        if site.site_code == "FAIL-1":
            raise read.PortUnavailable("boom")
        a = lo or datetime(day.year, day.month, day.day, tzinfo=UTC)
        b = hi or a + timedelta(days=1)
        rows = [{"category": c, "state": "NEEDS_ATTENTION" if c == "OPTIMIZE_COST" else "UNKNOWN",
                 "lead_outcome": None, "label": c} for c in CATEGORIES]
        warning = {"kind": "REPEATED", "site_code": site.site_code, "lo": wire(a),
                   "categories": {"items": [{"category": "OPTIMIZE_COST"}]}}
        return {"window": {"from": wire(a), "to": wire(b), "known_at": wire(known_at or at(23))},
                "read_state": "AVAILABLE", "rows": rows, "warnings": [warning], "_short_values": {},
                "_window": {"nodes": {}, "earnings": {}}}

    monkeypatch.setattr(SiteOutcomeBoardService, "board", board)
    monkeypatch.setattr(read, "_summary_row", lambda r, sv, nodes=None: {
        "category": r["category"], "state": r["state"], "state_label": r["state"]})
    return calls


def summary(estate, sites, known_at=None, lo=LO, hi=HI):
    return SiteOutcomeBoardService(BoardServices(estate=estate)).summary(sites, lo, hi, known_at)


def test_no_window_choice_helpers_remain():
    for name in ("latest_window", "_event_window", "_prefetch", "_PREFETCH", "WINDOW_BASIS_EVENT"):
        assert not hasattr(read, name) and not hasattr(SiteOutcomeBoardService, name), name


@pytest.mark.parametrize("site,href", [(COLD, "/sites/COLD-LAB-001"), (EVS, "/sites/EV-LAB-001/ev")])
def test_cold_and_ev_are_judged_on_the_requested_window(boards, site, href):
    est = Estate()
    out = summary(est, [site])
    # an event inside the period is read (one batch, this Site only) and never chosen over the period
    assert est.calls == [((site.site_code,), LO, HI, None)]
    assert len(boards[0]["windows"]) == 1 and boards[0]["windows"][0]["window_start"] == at(14)
    assert (boards[0]["lo"], boards[0]["hi"], boards[0]["day"]) == (LO, HI, None)
    entry = out["sites"][0]
    assert entry["window_basis"] == "PERIOD" and entry["overview_href"] == href
    assert entry["window"] == {"from": "2026-10-06T00:00:00Z", "to": "2026-10-07T00:00:00Z",
                               "known_at": "2026-10-06T23:00:00Z"}
    assert out["window"] == {"from": "2026-10-06T00:00:00Z", "to": "2026-10-07T00:00:00Z"}


def test_a_week_is_one_period_for_cold_and_ev_and_one_day_for_mini(boards):
    lo, hi = LO, LO + timedelta(days=7)
    est = Estate()
    out = summary(est, [KOBO, COLD, EVS], lo=lo, hi=hi)
    assert [s["window_basis"] for s in out["sites"]] == ["DAY", "PERIOD", "PERIOD"]
    assert boards[0]["day"] == date(2026, 10, 12) and boards[0]["lo"] is None
    assert [(b["lo"], b["hi"]) for b in boards[1:]] == [(lo, hi), (lo, hi)]
    assert est.calls == [(("COLD-LAB-001", "EV-LAB-001"), lo, hi, None)]  # one batch, cold/EV only, never mini
    # CH6b1-R Q1: every Site's nodes are asked over its `window_days`, the frame of its `days`
    assert [b["node_days"] for b in boards] == [window_days(lo, hi, s.timezone) for s in (KOBO, COLD, EVS)]


def test_mini_site_unchanged(boards):
    est = Estate()
    out = summary(est, [KOBO])
    assert est.calls == []  # a mini Site reads no estate windows (CH6b1-R3 is cold/EV only)
    # CH5a2-R R7: the UTC-midnight one-day pair [6 Oct 00Z, 7 Oct 00Z) is the picked date 6 Oct (`window_day` rule 2)
    assert boards[0]["day"] == date(2026, 10, 6) and boards[0]["lo"] is None and boards[0]["hi"] is None
    assert out["sites"][0]["window_basis"] == "DAY" and out["sites"][0]["overview_href"] == "/sites/KOBO-001"


def test_known_at_passed_through_never_on_href(boards):
    k = datetime(2026, 10, 7, 6, 30, tzinfo=UTC)
    out = summary(Estate(), [COLD], known_at=k)
    assert boards[0]["known_at"] == k
    assert out["sites"][0]["overview_href"] == "/sites/COLD-LAB-001"


def test_failed_board_has_no_window(boards):
    fail = SiteRef(T, uuid4(), "FAIL-1", "Fail", "COLDCHAIN", None)
    out = summary(Estate(), [fail])
    site = out["sites"][0]
    assert site["window"] is None and site["window_basis"] is None and site["earnings"] is None
    assert site["read_state"] == read.UNAVAILABLE and [r["state"] for r in site["rows"]] == ["UNKNOWN"] * 4
    assert site["overview_href"] == "/sites/FAIL-1"
    assert out["warnings"] == []


def test_warnings_come_from_the_period_board(boards):
    out = summary(Estate(), [COLD])
    assert [(w["kind"], w["lo"]) for w in out["warnings"]] == [("REPEATED", "2026-10-06T00:00:00Z")]
    counts = {c["category"]: c["warning_count"] for c in out["categories"]}
    assert counts["OPTIMIZE_COST"] == 1
    assert {c["category"]: c["sites_needing_attention"] for c in out["categories"]}["OPTIMIZE_COST"] == 1


def test_seed_fallback_is_counted_never_silent(boards, monkeypatch):
    """CH6b1-R Q3: no chain reader means no one-statement read; the fallback is recorded."""
    seen: list[str] = []
    monkeypatch.setattr(read.perf, "record", lambda name, ms: seen.append(name))
    summary(Estate(), [COLD])
    assert seen.count("summary.seed_fallback") == 1
