"""OUT-W W1: `EstateEvidenceService.site_selected_windows` (build sheet OUT-W §2 W1).

A fake store whose `read(work)` runs `work` on a fake snapshot: the method takes the Evidence root's exact selected
windows (same snapshot call and arguments as `estate/coverage.py` `_windowed`), deduplicates them, sorts them and
drops spans that are not forward or exceed 31 days; [] and None stay distinct."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from assetops_backend.estate.evidence_money import EstateEvidenceService
from assetops_backend.estate.scope import EstateRefusal

T = uuid4()
D = datetime(2026, 10, 6, tzinfo=timezone.utc)
READ_AT = datetime(2026, 10, 7, 12, tzinfo=timezone.utc)
CUTOFF = datetime(2026, 10, 7, 6, tzinfo=timezone.utc)


def at(h: int, m: int = 0, day: datetime = D) -> datetime:
    return day + timedelta(hours=h, minutes=m)


class FakeSnap:
    def __init__(self, sites: list[dict], windows: list[dict], cutoff: datetime | None = CUTOFF) -> None:
        self.read_at, self._sites, self._windows, self._cutoff = READ_AT, sites, windows, cutoff
        self.calls: list[tuple] = []

    def imported_sites(self, t, to):
        return list(self._sites)

    def evidence_cutoff(self, t, s, k):
        return self._cutoff

    def selected_windows(self, t, s, domain, from_, to, evidence_cutoff, k):
        self.calls.append((t, s, domain, from_, to, evidence_cutoff, k))
        return [dict(w) for w in self._windows]


class FakeStore:
    def __init__(self, snap: FakeSnap) -> None:
        self.snap = snap

    def read(self, work):
        return work(self.snap)


def site(code: str, site_type: str) -> dict:
    return {"site_id": uuid4(), "site_code": code, "site_name": code, "site_type": site_type, "site_code_key": code}


def win(lo: datetime, hi: datetime, analytic: str = "temperature") -> dict:
    return {"window_start": lo, "window_end": hi, "state": "CURRENT", "analytic_id": analytic}


def svc(snap: FakeSnap) -> EstateEvidenceService:
    return EstateEvidenceService(FakeStore(snap))


def test_cold_windows_deduplicated_and_ascending():
    s = site("COLD-LAB-001", "COLDCHAIN")
    stale = dict(win(at(16), at(17)), state="STALE_SOURCE")
    pending = dict(win(at(18), at(19)), state="PENDING_RECOMPUTE")
    snap = FakeSnap([s], [win(at(14), at(15)), win(at(8), at(9)), win(at(14), at(15), "door"), stale, pending])
    out = svc(snap).site_selected_windows(T, "COLD-LAB-001", D, D + timedelta(days=1))
    # any selected window is the event, whatever its state (review L1)
    assert out == [(at(8), at(9)), (at(14), at(15)), (at(16), at(17)), (at(18), at(19))]
    assert snap.calls == [(T, s["site_id"], "cold_chain", D, D + timedelta(days=1), CUTOFF, READ_AT)]


def test_ev_window_and_exact_arguments():
    s = site("EV-LAB-001", "EV_CHARGING")
    known = datetime(2026, 10, 7, 10, tzinfo=timezone.utc)
    snap = FakeSnap([s], [win(at(8), at(9))])
    out = svc(snap).site_selected_windows(T, "EV-LAB-001", D, D + timedelta(days=1), known)
    assert out == [(at(8), at(9))]
    assert snap.calls == [(T, s["site_id"], "ev_charging", D, D + timedelta(days=1), CUTOFF, known)]


def test_no_evidence_cutoff_is_empty_and_never_selects():
    snap = FakeSnap([site("COLD-LAB-001", "COLDCHAIN")], [win(at(8), at(9))], cutoff=None)
    assert svc(snap).site_selected_windows(T, "COLD-LAB-001", D, D + timedelta(days=1)) == []
    assert snap.calls == []


def test_minigrid_site_is_empty():
    snap = FakeSnap([site("KOBO-001", "MINIGRID")], [win(at(8), at(9))])
    assert svc(snap).site_selected_windows(T, "KOBO-001", D, D + timedelta(days=1)) == []
    assert snap.calls == []


def test_unknown_site_is_none():
    snap = FakeSnap([site("COLD-LAB-001", "COLDCHAIN")], [win(at(8), at(9))])
    assert svc(snap).site_selected_windows(T, "NOPE-001", D, D + timedelta(days=1)) is None


def test_long_and_zero_length_windows_dropped():
    snap = FakeSnap([site("COLD-LAB-001", "COLDCHAIN")],
                    [win(at(0) - timedelta(days=31), at(1)), win(at(9), at(9)), win(at(10), at(9)),
                     win(at(0) - timedelta(days=30), at(0) + timedelta(days=1)), win(at(8), at(9))])
    out = svc(snap).site_selected_windows(T, "COLD-LAB-001", D, D + timedelta(days=1))
    assert out == [(at(0) - timedelta(days=30), at(0) + timedelta(days=1)), (at(8), at(9))]


def test_known_at_after_read_at_refuses():
    snap = FakeSnap([site("COLD-LAB-001", "COLDCHAIN")], [])
    with pytest.raises(EstateRefusal) as e:
        svc(snap).site_selected_windows(T, "COLD-LAB-001", D, D + timedelta(days=1), READ_AT + timedelta(seconds=1))
    assert str(e.value) == "INVALID_KNOWN_AT"


@pytest.mark.parametrize("lo,hi", [(D, D + timedelta(days=32)), (at(1), D + timedelta(days=1))])
def test_window_rule_refuses(lo, hi):
    snap = FakeSnap([site("COLD-LAB-001", "COLDCHAIN")], [])
    with pytest.raises(EstateRefusal) as e:
        svc(snap).site_selected_windows(T, "COLD-LAB-001", lo, hi)
    assert str(e.value) == "INVALID_WINDOW"
