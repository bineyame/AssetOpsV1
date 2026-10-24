"""Post-W6 W3-estate backend hrefs (rulings Cross-card 7, Q2, Q4, Q9, Q10): pure, DB-free URL contracts.

`site_home_href` (EV `/sites/{code}/ev`), the EV unproven-window fallbacks, the cold/EV windowed Finding route and
its null cases, and the Portfolio objectives matrix destinations per domain.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from assetops_backend.estate.evidence_money import (
    CURRENT_VIEW, finding_window_href, site_home_href, window_links)
from assetops_backend.estate.financials import _money_links
from assetops_backend.estate.index import _finding_links, _WindowRecorder
from assetops_backend.estate.portfolio import objective_destinations

D0 = datetime(2026, 10, 13, tzinfo=timezone.utc)
CUT = datetime(2026, 10, 20, 6, tzinfo=timezone.utc)
K = datetime(2026, 10, 20, 12, tzinfo=timezone.utc)
FID, FRID = "11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222"
QUERY = ("from=2026-10-13T00%3A00%3A00.000000Z&to=2026-10-14T00%3A00%3A00.000000Z"
         "&known_at=2026-10-20T06%3A00%3A00.000000Z")


def pin(lo=D0, hi=D0 + timedelta(days=1), known=CUT, watermark=CUT):
    return {"lo": lo, "hi": hi, "known": known, "watermark": watermark}


def test_site_home_href_per_domain_and_site_type() -> None:
    assert site_home_href("EV-1", "ev_charging") == site_home_href("EV-1", "EV_CHARGING") == "/sites/EV-1/ev"
    assert site_home_href("COLD 1", "cold_chain") == site_home_href("COLD 1", "COLDCHAIN") == "/sites/COLD%201"
    assert site_home_href("KOBO-001", "mini_grid") == site_home_href("KOBO-001", "MINIGRID") == "/sites/KOBO-001"
    assert site_home_href("X/1", "NOT_APPLICABLE") == "/sites/X%2F1"


def test_window_links_fallbacks_use_the_site_home() -> None:
    for snap in (None, pin(known=CUT + timedelta(hours=1))):
        assert window_links("EV-1", "ev_charging", snap, CUT, K) == {
            "site": "/sites/EV-1/ev", "site_readiness": "/sites/EV-1/ev", "site_readiness_label": CURRENT_VIEW}
    assert window_links("C1", "cold_chain", None, CUT, K)["site_readiness"] == "/sites/C1"
    proven = window_links("EV-1", "ev_charging", pin(), CUT, K)
    assert proven == {"site": "/sites/EV-1/ev", "site_readiness": f"/sites/EV-1/ev/evidence?{QUERY}",
                      "site_readiness_label": None}
    assert window_links("C1", "cold_chain", pin(), CUT, K)["site_readiness"] == f"/sites/C1/evidence?{QUERY}"


def test_money_links_never_bare_site_for_ev() -> None:
    assert _money_links("EV-1", "ev_charging", None, CUT, K) == {
        "site": "/sites/EV-1/ev", "bridge": "/sites/EV-1/ev", "evidence": "/sites/EV-1/ev",
        "current_view_label": CURRENT_VIEW}
    assert _money_links("EV-1", "ev_charging", pin(), CUT, K) == {
        "site": "/sites/EV-1/ev", "bridge": f"/sites/EV-1/ev/financials?{QUERY}",
        "evidence": f"/sites/EV-1/ev/evidence?{QUERY}", "current_view_label": None}
    assert _money_links("C1", "cold_chain", None, CUT, K)["bridge"] == "/sites/C1"
    assert _money_links("K1", "mini_grid", None, None, K)["site"] == "/sites/K1"


def test_finding_window_href_proved_or_null() -> None:
    hi = D0 + timedelta(days=1)
    assert finding_window_href("C 1", FID, D0, hi, CUT, CUT, K) == f"/sites/C%201/findings/{FID}?{QUERY}"
    assert finding_window_href("C1", FID, D0, D0 + timedelta(days=31), CUT, CUT, K) is not None
    assert finding_window_href("C1", FID, D0, D0 + timedelta(days=31, seconds=1), CUT, CUT, K) is None  # >31 days
    assert finding_window_href("C1", FID, hi, D0, CUT, CUT, K) is None  # reversed
    assert finding_window_href("C1", FID, None, hi, CUT, CUT, K) is None  # window missing
    assert finding_window_href("C1", FID, D0, hi, None, None, K) is None  # cutoff missing
    assert finding_window_href("C1", FID, D0, hi, CUT, CUT - timedelta(hours=1), K) is None  # not the Site cutoff
    assert finding_window_href("C1", FID, D0, hi, CUT, CUT, CUT - timedelta(hours=1)) is None  # after estate cutoff
    assert finding_window_href("C1", FID, D0, hi, CUT, CUT, K, CUT - timedelta(hours=1)) is None  # after watermark


class _Snap:
    def __init__(self, windows, cutoff=CUT):
        self.windows, self.cutoff, self.basis_historical = windows, cutoff, False

    def evidence_cutoff(self, *args):
        return self.cutoff

    def selected_windows(self, *args):
        return self.windows


def _recorded(windows, cutoff=CUT) -> _WindowRecorder:
    rec = _WindowRecorder(_Snap(windows, cutoff))
    rec.evidence_cutoff("t", "s", K)
    rec.selected_windows("t", "s", "cold_chain", D0, D0, CUT, K)
    assert rec.basis_historical is False  # every other attribute delegates
    return rec


def window(lo, days=1, fids=(FID,)):
    return {"window_start": lo, "window_end": lo + timedelta(days=days),
            "findings": [{"finding_id": f} for f in fids]}


def test_finding_links_per_domain() -> None:
    mini = _finding_links("KOBO 001", "mini_grid", FID, FRID, None, K)
    assert mini == {"finding": f"/sites/KOBO%20001/findings/{FID}?revision_id={FRID}", "site": "/sites/KOBO%20001"}
    held = _recorded([window(D0 - timedelta(days=1), fids=()), window(D0)])
    assert _finding_links("C1", "cold_chain", FID, FRID, held, K) == {
        "finding": f"/sites/C1/findings/{FID}?{QUERY}", "site": "/sites/C1"}
    assert _finding_links("EV-1", "ev_charging", FID, FRID, held, K) == {
        "finding": f"/sites/EV-1/findings/{FID}?{QUERY}", "site": "/sites/EV-1/ev"}
    # Null: no recorded window, a Finding no selected window holds, two windows holding it, an unproved cutoff,
    # or a holding window longer than 31 days. Episode bounds are never used.
    assert _finding_links("EV-1", "ev_charging", FID, FRID, None, K)["finding"] is None
    assert _finding_links("C1", "cold_chain", FID, FRID, _recorded([window(D0, fids=())]), K)["finding"] is None
    two = _recorded([window(D0), window(D0 + timedelta(days=1))])
    assert _finding_links("C1", "cold_chain", FID, FRID, two, K)["finding"] is None
    assert _finding_links("C1", "cold_chain", FID, FRID, _recorded([window(D0)], cutoff=None), K)["finding"] is None
    assert _finding_links("C1", "cold_chain", FID, FRID, _recorded([window(D0, days=32)]), K)["finding"] is None


def _evidence_row(readiness, label, start=None, end=None):
    return {"window_start": start, "window_end": end,
            "links": {"site": "x", "site_readiness": readiness, "site_readiness_label": label}}


def test_objective_destinations_per_domain() -> None:
    assert objective_destinations("KOBO 001", "mini_grid", []) == {
        "SERVICE_PRODUCT": "/sites/KOBO%20001/performance/service",
        "BACKUP": "/sites/KOBO%20001/performance/backup", "ASSET_CONDITION": "/sites/KOBO%20001/health",
        "COST_CONTROL": "/sites/KOBO%20001/financials", "EVIDENCE": "/sites/KOBO%20001/evidence"}
    unproved = [_evidence_row("/sites/C1", CURRENT_VIEW)]
    assert objective_destinations("C1", "cold_chain", unproved) == {
        "SERVICE_PRODUCT": "/sites/C1/performance/temperature", "BACKUP": "/sites/C1/performance/backup",
        "ASSET_CONDITION": "/sites/C1/health", "COST_CONTROL": "/sites/C1", "EVIDENCE": "/sites/C1"}
    older = "from=2026-10-12T00%3A00%3A00.000000Z&to=2026-10-13T00%3A00%3A00.000000Z&known_at=x"
    cold_rows = [_evidence_row(f"/sites/C1/evidence?{older}", None, "2026-10-12", "2026-10-13"),
                 _evidence_row(f"/sites/C1/evidence?{QUERY}", None, "2026-10-13", "2026-10-14"), *unproved]
    cold = objective_destinations("C1", "cold_chain", cold_rows)
    assert (cold["COST_CONTROL"], cold["EVIDENCE"]) == (f"/sites/C1/financials?{QUERY}", f"/sites/C1/evidence?{QUERY}")
    assert objective_destinations("EV-1", "ev_charging", [_evidence_row("/sites/EV-1/ev", CURRENT_VIEW)]) == {
        "SERVICE_PRODUCT": "/sites/EV-1/performance/sessions", "BACKUP": None, "ASSET_CONDITION": "/sites/EV-1/health",
        "COST_CONTROL": "/sites/EV-1/ev", "EVIDENCE": "/sites/EV-1/ev"}
    ev = objective_destinations("EV-1", "ev_charging",
                                [_evidence_row(f"/sites/EV-1/ev/evidence?{QUERY}", None, "2026-10-13", "2026-10-14")])
    assert ev["BACKUP"] is None
    assert (ev["COST_CONTROL"], ev["EVIDENCE"]) == (f"/sites/EV-1/ev/financials?{QUERY}",
                                                    f"/sites/EV-1/ev/evidence?{QUERY}")
    assert set(objective_destinations("U1", "NOT_APPLICABLE", []).values()) == {None}
