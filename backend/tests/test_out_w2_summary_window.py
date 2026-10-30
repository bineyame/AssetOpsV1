"""OUT-W W2: the estate summary judges each cold or EV Site on its latest assessed event inside the period (build
sheet OUT-W §2 W2, P-C1 option A). Fake estate and a recording fake board, no database: the latest window wins (ties
on the end go to the later start), the Overview link carries it, and no window, an unauthorized Site or a failing
estate fall back to the period with a plain link. Mini is untouched; `known_at` is passed through, never invented."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from assetops_backend.estate.scope import EstateRefusal
from assetops_backend.outcomes.catalogue import CATEGORIES
from assetops_backend.site_outcomes import read
from assetops_backend.site_outcomes.read import BoardServices, SiteOutcomeBoardService, SiteRef, latest_window, wire

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
    def __init__(self, windows=None, error: Exception | None = None) -> None:
        self.windows, self.error, self.calls = windows, error, []

    def site_selected_windows(self, *a):
        self.calls.append(a)
        if self.error is not None:
            raise self.error
        return self.windows


@pytest.fixture
def boards(monkeypatch):
    """A fake board recording `day`/`lo`/`hi`/`known_at`, echoing them as the board's own window."""
    calls: list[dict] = []

    def board(self, site, *, day=None, lo=None, hi=None, known_at=None, pin=None):
        calls.append({"site": site.site_code, "day": day, "lo": lo, "hi": hi, "known_at": known_at})
        if site.site_code == "FAIL-1":
            raise read.PortUnavailable("boom")
        a = lo or datetime(day.year, day.month, day.day, tzinfo=UTC)
        b = hi or a + timedelta(days=1)
        rows = [{"category": c, "state": "NEEDS_ATTENTION" if c == "OPTIMIZE_COST" else "UNKNOWN",
                 "lead_outcome": None, "label": c} for c in CATEGORIES]
        warning = {"kind": "REPEATED", "site_code": site.site_code, "lo": wire(a),
                   "categories": {"items": [{"category": "OPTIMIZE_COST"}]}}
        return {"window": {"from": wire(a), "to": wire(b), "known_at": wire(known_at or at(23))},
                "read_state": "AVAILABLE", "rows": rows, "warnings": [warning], "_short_values": {}}

    monkeypatch.setattr(SiteOutcomeBoardService, "board", board)
    monkeypatch.setattr(read, "_summary_row", lambda r, sv: {"category": r["category"], "state": r["state"]})
    return calls


def summary(estate, sites, known_at=None):
    return SiteOutcomeBoardService(BoardServices(estate=estate)).summary(sites, LO, HI, known_at)


def test_latest_window_helper():
    assert latest_window(None) is None and latest_window([]) is None
    assert latest_window([(at(14), at(15)), (at(8), at(9))]) == (at(14), at(15))
    assert latest_window([(at(13), at(15)), (at(14), at(15)), (at(8), at(9))]) == (at(14), at(15))


def test_cold_site_board_on_latest_event_and_href(boards):
    est = Estate([(at(8), at(9)), (at(14), at(15))])
    out = summary(est, [COLD])
    assert est.calls == [(T, "COLD-LAB-001", LO, HI, None)]
    assert (boards[0]["lo"], boards[0]["hi"], boards[0]["day"]) == (at(14), at(15), None)
    site = out["sites"][0]
    assert site["window_basis"] == "LATEST_EVENT"
    assert site["window"] == {"from": "2026-10-06T14:00:00Z", "to": "2026-10-06T15:00:00Z",
                              "known_at": "2026-10-06T23:00:00Z"}
    assert site["overview_href"] == "/sites/COLD-LAB-001?from=2026-10-06T14%3A00%3A00Z&to=2026-10-06T15%3A00%3A00Z"
    assert out["window"] == {"from": "2026-10-06T00:00:00Z", "to": "2026-10-07T00:00:00Z"}


def test_tie_on_end_takes_later_start(boards):
    summary(Estate([(at(14), at(15)), (at(13), at(15))]), [COLD])
    assert (boards[0]["lo"], boards[0]["hi"]) == (at(14), at(15))


def test_ev_site_href(boards):
    out = summary(Estate([(at(8), at(9))]), [EVS])
    assert out["sites"][0]["overview_href"] == ("/sites/EV-LAB-001/ev?from=2026-10-06T08%3A00%3A00Z"
                                                "&to=2026-10-06T09%3A00%3A00Z")
    assert out["sites"][0]["window_basis"] == "LATEST_EVENT"


@pytest.mark.parametrize("estate", [Estate([]), Estate(None), Estate(error=RuntimeError("store down")),
                                    Estate(error=EstateRefusal("ESTATE_SELECTION_INCONSISTENT")), None],
                         ids=["no-window", "not-authorized", "raises", "read-refusal", "unconfigured"])
def test_no_event_falls_back_to_period(boards, estate):
    out = summary(estate, [COLD, EVS])
    assert [(b["lo"], b["hi"]) for b in boards] == [(LO, HI), (LO, HI)]
    assert [s["window_basis"] for s in out["sites"]] == ["PERIOD", "PERIOD"]
    assert [s["overview_href"] for s in out["sites"]] == ["/sites/COLD-LAB-001", "/sites/EV-LAB-001/ev"]
    assert out["sites"][0]["window"]["from"] == "2026-10-06T00:00:00Z"
    assert all(s["read_state"] == "AVAILABLE" for s in out["sites"])


def test_mini_site_unchanged(boards):
    est = Estate([(at(8), at(9))])
    out = summary(est, [KOBO])
    assert est.calls == []
    assert boards[0]["day"] == D.date() and boards[0]["lo"] is None and boards[0]["hi"] is None
    assert out["sites"][0]["window_basis"] == "DAY" and out["sites"][0]["overview_href"] == "/sites/KOBO-001"


def test_known_at_passed_through_and_on_href(boards):
    k = datetime(2026, 10, 7, 6, 30, tzinfo=UTC)
    est = Estate([(at(14), at(15))])
    out = summary(est, [COLD], known_at=k)
    assert est.calls == [(T, "COLD-LAB-001", LO, HI, k)] and boards[0]["known_at"] == k
    assert out["sites"][0]["overview_href"] == ("/sites/COLD-LAB-001?from=2026-10-06T14%3A00%3A00Z"
                                                "&to=2026-10-06T15%3A00%3A00Z&known_at=2026-10-07T06%3A30%3A00Z")
    out = summary(Estate([(at(14), at(15))]), [COLD])
    assert "known_at" not in out["sites"][0]["overview_href"]


def test_failed_board_has_no_window(boards):
    fail = SiteRef(T, uuid4(), "FAIL-1", "Fail", "COLDCHAIN", None)
    out = summary(Estate([(at(14), at(15))]), [fail])
    site = out["sites"][0]
    assert site["window"] is None and site["window_basis"] is None
    assert site["read_state"] == read.UNAVAILABLE and [r["state"] for r in site["rows"]] == ["UNKNOWN"] * 4
    assert site["overview_href"] == "/sites/FAIL-1"
    assert out["warnings"] == []


def test_warnings_come_from_the_event_window_board(boards):
    out = summary(Estate([(at(14), at(15))]), [COLD])
    assert [(w["kind"], w["lo"]) for w in out["warnings"]] == [("REPEATED", "2026-10-06T14:00:00Z")]
    counts = {c["category"]: c["warning_count"] for c in out["categories"]}
    assert counts["OPTIMIZE_COST"] == 1
    assert {c["category"]: c["sites_needing_attention"] for c in out["categories"]}["OPTIMIZE_COST"] == 1
