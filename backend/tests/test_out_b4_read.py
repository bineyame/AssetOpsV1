"""OUT-B4: `SiteOutcomeBoardService` over fake services (no database): the port binding forwards the Site, tenant,
cutoff and pin; an unconfigured service is that port's refusal (PARTIAL, never a refused board); the estate summary
is serial, keeps the caller's Site order, gives an UNAVAILABLE Site four UNKNOWN rows, and sets `short_value` only
on a mini Grow row led by MG-1 in OPPORTUNITY (B-Q27)."""
from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

from assetops_backend.outcomes.catalogue import CATEGORIES
from assetops_backend.site_outcomes import read
from assetops_backend.site_outcomes.read import BoardServices, SiteOutcomeBoardService, SiteRef, mini_summary_day

UTC = timezone.utc
T, S = uuid4(), uuid4()
KOBO = SiteRef(T, S, "KOBO-001", "Kobo", "MINIGRID", "Africa/Nairobi")
COLD = SiteRef(T, uuid4(), "COLD-LAB-001", "GreenHarvest", "COLDCHAIN", None)
ODD = SiteRef(T, uuid4(), "ODD-1", "Odd", "UNKNOWN_TYPE", None)


def test_mini_summary_day_is_the_utc_day_of_to() -> None:
    assert mini_summary_day(datetime(2026, 10, 8, tzinfo=UTC)) == date(2026, 10, 7)
    assert mini_summary_day(datetime(2026, 10, 8, 5, tzinfo=UTC)) == date(2026, 10, 8)


def test_unconfigured_services_make_a_partial_board_not_a_refusal() -> None:
    body = SiteOutcomeBoardService(BoardServices()).board(KOBO, day=date(2026, 10, 6))
    assert body["read_state"] == "PARTIAL" and [r["category"] for r in body["rows"]] == list(CATEGORIES)
    assert body["window"] == {"from": "2026-10-06T00:00:00Z", "to": "2026-10-07T00:00:00Z", "known_at": None}
    assert body["links"]["self"] == ("/api/sites/KOBO-001/outcome-board?from=2026-10-06T00%3A00%3A00Z"
                                     "&to=2026-10-07T00%3A00%3A00Z")
    assert all(r["state"] in ("UNKNOWN", "NOT_MEASURED") for r in body["rows"])


def test_ports_forward_site_tenant_cutoff_and_pin() -> None:
    seen: dict[str, tuple] = {}
    known = datetime(2026, 10, 9, 12, tzinfo=UTC)
    pin = (uuid4(), uuid4())

    class Overview:
        def read(self, code, t, s, day, **kw):
            seen["overview"] = (code, t, s, day, kw["pinned"], kw["source_open"], kw["source_reason"])
            return {"window": {}}

    class Depth:
        def read(self, **kw):
            seen.setdefault("depth", kw)
            return {"site": {"timezone": "Africa/Nairobi"}, "cards": {}}

    class Estate:
        def site_readiness(self, *a):
            seen["readiness"] = a
            return "LIMITED"

        def site_work_rows(self, *a):
            seen["estate"] = a
            return {"site_cov": {}, "findings": [], "actions": []}

    svc = SiteOutcomeBoardService(BoardServices(
        overview=Overview(), overview_source=lambda c, t, s: (True, "open"), mini_depth=Depth(), estate=Estate()))
    body = svc.board(KOBO, day=date(2026, 10, 6), known_at=known, pin=pin)
    assert seen["overview"] == ("KOBO-001", T, S, date(2026, 10, 6), pin, True, "open")
    assert seen["depth"]["known_at"] == known and seen["depth"]["site_id"] == S
    assert seen["readiness"] == (T, "KOBO-001", datetime(2026, 10, 6, tzinfo=UTC), datetime(2026, 10, 7, tzinfo=UTC),
                                 known)
    assert seen["estate"][1:3] == ("KOBO-001", datetime(2026, 9, 6, tzinfo=UTC)) and seen["estate"][4] == known
    assert body["window"]["known_at"] == "2026-10-09T12:00:00Z"
    assert "finding_id=" in body["links"]["self"] and "known_at=" in body["links"]["self"]


def test_summary_order_unavailable_site_and_short_value(monkeypatch) -> None:
    calls: list[str] = []
    real = SiteOutcomeBoardService.board

    def board(self, site, **kw):
        calls.append(site.site_code)
        body = real(self, site, **kw)
        if site is KOBO:  # a Grow row led by MG-1 in OPPORTUNITY, as the composer would give it
            grow = body["rows"][0]
            grow.update(state="OPPORTUNITY", lead_outcome={"key": "MG-1", "label": "Productive use"})
            body["_short_values"] = {"GROW_REVENUE": "18–24.3 kW unused"}
        return body

    monkeypatch.setattr(SiteOutcomeBoardService, "board", board)
    lo, hi = datetime(2026, 10, 1, tzinfo=UTC), datetime(2026, 10, 8, tzinfo=UTC)
    out = SiteOutcomeBoardService(BoardServices()).summary([KOBO, COLD, ODD], lo, hi)
    assert calls == ["KOBO-001", "COLD-LAB-001", "ODD-1"]
    assert [s["site_code"] for s in out["sites"]] == calls
    kobo, cold, odd = out["sites"]
    assert kobo["rows"][0]["short_value"] == "18–24.3 kW unused"
    assert all(r["short_value"] is None for r in kobo["rows"][1:])
    assert cold["read_state"] == "PARTIAL" and cold["overview_href"] == "/sites/COLD-LAB-001"
    assert odd["read_state"] == read.UNAVAILABLE and [r["state"] for r in odd["rows"]] == ["UNKNOWN"] * 4
    assert [c["category"] for c in out["categories"]] == list(CATEGORIES)
    assert out["window"] == {"from": "2026-10-01T00:00:00Z", "to": "2026-10-08T00:00:00Z"}
