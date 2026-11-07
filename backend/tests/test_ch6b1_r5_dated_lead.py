"""CH6b1-R5: the cold/EV lead names the event's Site-local date and time when the requested window is longer."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from assetops_backend.site_outcomes import cold, read
from assetops_backend.site_outcomes.board import SiteFacts
from assetops_backend.site_outcomes.mini import MiniComposition

ZONE = "Africa/Addis_Ababa"   # UTC+3
LEAD = "Chamber above 4°C for 65 min"
# the event 13:00-14:05 UTC is 16:00-17:05 on 26 Oct in Site time
EV_LO, EV_HI = datetime(2026, 10, 26, 13, 0, tzinfo=timezone.utc), datetime(2026, 10, 26, 14, 5, tzinfo=timezone.utc)


def _compose(monkeypatch, lo, hi):
    def fake(ports, *, site_code, lo, hi, site_timezone, actions_to=None):
        facts = SiteFacts(domain="COLD", site_code=site_code, headline={cold.PROTECT: LEAD})
        return MiniComposition(facts, "AVAILABLE", (), (), {"from": lo, "to": hi}, site_timezone)
    monkeypatch.setattr(read.cold, "compose", fake)
    svc = read.SiteOutcomeBoardService(read.BoardServices())
    monkeypatch.setattr(svc, "cold_ports", lambda site, known_at: None)
    monkeypatch.setattr(read.SiteOutcomeBoardService, "cold_ev_cutoff",
                        staticmethod(lambda site, ports, lo, hi, known_at, use: (lo, hi, None, use(ports, lo, hi))))
    monkeypatch.setattr(svc, "event_window", lambda *a, **k: (EV_LO, EV_HI))
    site = read.SiteRef(uuid4(), uuid4(), "C", "Cold", "COLD_STORAGE", ZONE)
    monkeypatch.setattr(read.SiteRef, "domain", property(lambda self: read.COLD))
    comp, _ = svc.compose(site, lo=lo, hi=hi)
    return comp.facts.headline[cold.PROTECT]


def test_a_week_window_dates_the_lead(monkeypatch):
    lo, hi = datetime(2026, 10, 25, 21, 0, tzinfo=timezone.utc), datetime(2026, 11, 1, 21, 0, tzinfo=timezone.utc)
    assert _compose(monkeypatch, lo, hi) == LEAD + " · 26 Oct 16:00–17:05"


def test_an_event_length_window_leaves_the_lead(monkeypatch):
    assert _compose(monkeypatch, EV_LO, EV_HI) == LEAD
