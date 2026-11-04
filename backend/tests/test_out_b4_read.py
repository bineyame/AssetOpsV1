"""OUT-B4: `SiteOutcomeBoardService` over fake services (no database): the port binding forwards the Site, tenant,
cutoff and pin; an unconfigured service is that port's refusal (PARTIAL, never a refused board); the estate summary
is serial, keeps the caller's Site order, gives an UNAVAILABLE Site four UNKNOWN rows, and sets `short_value` only
on a mini Grow row led by MG-1 in OPPORTUNITY (B-Q27)."""
from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

from assetops_backend.outcomes.catalogue import CATEGORIES
from assetops_backend.site_outcomes import read
from assetops_backend.chain.read import window_day
from assetops_backend.site_outcomes.read import BoardServices, SiteOutcomeBoardService, SiteRef

UTC = timezone.utc
T, S = uuid4(), uuid4()
KOBO = SiteRef(T, S, "KOBO-001", "Kobo", "MINIGRID", "Africa/Nairobi")
COLD = SiteRef(T, uuid4(), "COLD-LAB-001", "GreenHarvest", "COLDCHAIN", None)
ODD = SiteRef(T, uuid4(), "ODD-1", "Odd", "UNKNOWN_TYPE", None)


ADDIS = "Africa/Addis_Ababa"  # UTC+3: 30 Oct 21:00Z is local midnight 31 Oct


def test_window_day_rule_1_one_site_local_day_is_that_local_date() -> None:
    """CH5a2-R R7 rule 1: a pair that is exactly one Site-local day selects that local date."""
    assert window_day(datetime(2026, 10, 30, 21, tzinfo=UTC), datetime(2026, 10, 31, 21, tzinfo=UTC), ADDIS)         == date(2026, 10, 31)
    assert window_day(datetime(2026, 10, 31, tzinfo=UTC), datetime(2026, 11, 1, tzinfo=UTC), "Etc/UTC")         == date(2026, 10, 31)


def test_window_day_rule_2_utc_midnight_one_day_pair_is_the_picked_date() -> None:
    """Rule 2: a UTC-midnight one-day pair is the calendar date the user picked, east of UTC too (the CH-5a1
    `summary_day` gave Addis 1 Nov here: the defect the owner approved fixing)."""
    lo, hi = datetime(2026, 10, 31, tzinfo=UTC), datetime(2026, 11, 1, tzinfo=UTC)
    assert window_day(lo, hi, ADDIS) == date(2026, 10, 31)
    assert window_day(lo, hi, "America/New_York") == date(2026, 10, 31)
    assert window_day(lo, hi, None) == date(2026, 10, 31)


def test_window_day_rule_3_other_windows_read_to_in_its_midnight_frame() -> None:
    """Rule 3: any other window is the date of `to - 1 µs` in the frame where `to` is a midnight: UTC when `to` is a
    UTC midnight, otherwise Site-local. No `to` is None."""
    week = datetime(2026, 10, 25, tzinfo=UTC), datetime(2026, 11, 1, tzinfo=UTC)
    assert window_day(*week, ADDIS) == date(2026, 10, 31)                 # UTC frame (local would be 1 Nov)
    local_week = datetime(2026, 10, 24, 21, tzinfo=UTC), datetime(2026, 10, 31, 21, tzinfo=UTC)
    assert window_day(*local_week, ADDIS) == date(2026, 10, 31)           # Site-local frame
    assert window_day(None, datetime(2026, 10, 8, 5, tzinfo=UTC), ADDIS) == date(2026, 10, 8)
    assert window_day(None, datetime(2026, 10, 8, tzinfo=UTC), ADDIS) == date(2026, 10, 7)
    assert window_day(datetime(2026, 10, 1, tzinfo=UTC), None, ADDIS) is None


def test_31_oct_summary_card_is_the_31_oct_kobo_board(monkeypatch) -> None:
    """R7: the summary card of the picked day 31 Oct reads the same Kobo board the board route gives for that pair
    (the Site page the card links into), so the card and the Site page cannot disagree."""
    from assetops_backend.outcome_api import _mini_day_params
    from assetops_backend.site_overview.route import selected_day

    kobo = SiteRef(T, S, "KOBO-001", "Kobo", "MINIGRID", ADDIS)
    days: list = []
    real = SiteOutcomeBoardService.board

    def board(self, site, **kw):
        days.append(kw.get("day"))
        return real(self, site, **kw)

    monkeypatch.setattr(SiteOutcomeBoardService, "board", board)
    pair = {"from": "2026-10-31T00:00:00Z", "to": "2026-11-01T00:00:00Z"}
    route_day = selected_day(_mini_day_params(pair, ADDIS))
    out = SiteOutcomeBoardService(BoardServices()).summary(
        [kobo], datetime(2026, 10, 31, tzinfo=UTC), datetime(2026, 11, 1, tzinfo=UTC))
    assert route_day == date(2026, 10, 31) and days == [route_day]
    route_board = real(SiteOutcomeBoardService(BoardServices()), kobo, day=route_day)
    card = out["sites"][0]["window"]
    assert {k: card[k] for k in ("from", "to")} == {k: route_board["window"][k] for k in ("from", "to")} == {
        "from": "2026-10-30T21:00:00Z", "to": "2026-10-31T21:00:00Z"}


def test_unconfigured_services_make_a_partial_board_not_a_refusal() -> None:
    body = SiteOutcomeBoardService(BoardServices()).board(KOBO, day=date(2026, 10, 6))
    assert body["read_state"] == "PARTIAL" and [r["category"] for r in body["rows"]] == list(CATEGORIES)
    # E4 (R6): the window is the Site-local day (Africa/Nairobi, UTC+3), not the UTC day.
    assert body["window"] == {"from": "2026-10-05T21:00:00Z", "to": "2026-10-06T21:00:00Z", "known_at": None}
    assert body["links"]["self"] == ("/api/sites/KOBO-001/outcome-board?from=2026-10-05T21%3A00%3A00Z"
                                     "&to=2026-10-06T21%3A00%3A00Z")
    assert all(r["state"] in ("UNKNOWN", "NOT_MEASURED") for r in body["rows"])


def test_ports_forward_site_tenant_cutoff_and_pin() -> None:
    seen: dict[str, tuple] = {}
    known = datetime(2026, 10, 9, 12, tzinfo=UTC)
    pin = (uuid4(), uuid4())

    class Request:  # CH-5a1: the ChainReader request; the overview and estate readiness are not read
        def day(self, sid, site_type, days, readiness_days):
            seen["day"] = (sid, site_type, days[0], days[-1], len(days), readiness_days)
            raise RuntimeError("no snapshots in this fake")

        def findings(self, sid, *a):
            seen["findings"] = (sid, *a)
            return ()

        def findings_settled(self, sid):
            seen["settled"] = sid
            return True

    class Reader:
        def request(self, tenant, k):
            seen.setdefault("request", []).append((tenant, k))
            return Request()

    class Depth:
        def read(self, **kw):
            seen.setdefault("depth", kw)
            return {"site": {"timezone": "Africa/Nairobi"}, "cards": {}}

    class Estate:
        def site_readiness(self, *a):  # pragma: no cover - CH-5a1: never read by the board
            raise AssertionError("estate readiness is not a board read")

        def site_work_rows(self, *a):
            seen["estate"] = a
            return {"site_cov": {}, "findings": [], "actions": []}

    svc = SiteOutcomeBoardService(BoardServices(
        overview_source=lambda c, t, s: seen.setdefault("source", (c, t, s)) and (True, "open"), mini_depth=Depth(),
        estate=Estate(), chain_reader=Reader()))
    body = svc.board(KOBO, day=date(2026, 10, 6), known_at=known, pin=pin)
    assert seen["source"] == ("KOBO-001", T, S)
    assert svc.mini_ports(KOBO, known, pin).pin == pin
    assert {r for r in seen["request"]} == {(T, known)}
    assert seen["day"] == (S, "MINIGRID", date(2026, 9, 6), date(2026, 10, 6), 31, (date(2026, 10, 6),))
    assert seen["settled"] == S and "findings" not in seen  # no Finding index gate: the heads read is refused
    assert seen["depth"]["known_at"] == known and seen["depth"]["site_id"] == S
    # The kept estate read stays on the UTC day and the 31 UTC days ending with it (`mini.estate_bounds`).
    assert seen["estate"][1:] == ("KOBO-001", datetime(2026, 10, 6, tzinfo=UTC), datetime(2026, 10, 7, tzinfo=UTC),
                                  datetime(2026, 9, 6, tzinfo=UTC), datetime(2026, 10, 7, tzinfo=UTC), known)
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

def test_summary_short_value_with_declared_objective_and_potential(monkeypatch) -> None:
    """WALK1-3b M1: a declared MG-1 (state not OPPORTUNITY) with an open headroom potential still sends it."""
    real = SiteOutcomeBoardService.board

    def board(self, site, **kw):
        body = real(self, site, **kw)
        body["rows"][0].update(state="ON_TRACK", lead_outcome={"key": "MG-1", "label": "Productive use"},
                               potential={"text": "18-24.3 kW unused"})
        body["_short_values"] = {"GROW_REVENUE": "18-24.3 kW unused"}
        return body

    monkeypatch.setattr(SiteOutcomeBoardService, "board", board)
    lo, hi = datetime(2026, 10, 1, tzinfo=UTC), datetime(2026, 10, 8, tzinfo=UTC)
    kobo = SiteOutcomeBoardService(BoardServices()).summary([KOBO], lo, hi)["sites"][0]
    assert kobo["rows"][0]["short_value"] == "18-24.3 kW unused"



def test_mini_price_cutoff_is_known_at_or_current_never_a_clock() -> None:  # addendum 4 #4
    seen: list = []

    class Assumptions:
        def series(self, t, s, key, *, valid_at, recorded_at):
            seen.append(recorded_at)
            return {}

    svc = SiteOutcomeBoardService(BoardServices(assumptions=Assumptions()))
    known = datetime(2026, 10, 9, 12, tzinfo=UTC)
    svc.mini_ports(KOBO).assumption(datetime(2026, 10, 6, tzinfo=UTC))
    svc.mini_ports(KOBO, known).assumption(datetime(2026, 10, 6, tzinfo=UTC))
    assert seen == [None, known]


def test_window_known_at_echoes_the_cutoff_used() -> None:  # addendum 4 #5
    resolved = "2026-10-08T03:00:00Z"
    calls: list = []

    class ColdSite:
        def overview(self, t, s, c, lo, hi, known_at):
            calls.append(known_at)
            return {"window": {"from": "2026-10-01T00:00:00Z", "to": "2026-10-08T00:00:00Z", "known_at": resolved}}

    svc = SiteOutcomeBoardService(BoardServices(cold_site=ColdSite()))
    assert svc.board(COLD)["window"] == {"from": "2026-10-01T00:00:00Z", "to": "2026-10-08T00:00:00Z",
                                         "known_at": resolved}
    lo, hi = datetime(2026, 10, 1, tzinfo=UTC), datetime(2026, 10, 8, tzinfo=UTC)
    assert svc.board(COLD, lo=lo, hi=hi)["window"]["known_at"] == resolved  # a given window, still resolved
    known = datetime(2026, 10, 7, tzinfo=UTC)
    assert svc.board(COLD, lo=lo, hi=hi, known_at=known)["window"]["known_at"] == "2026-10-07T00:00:00Z"
    assert calls[0] is None and calls[-1] == known  # the resolved cutoff is never forwarded (addendum 4 #3)
    assert set(calls[:-1]) == {None}
    # mini without a cutoff: null, even when the overview body carries one
    mini_body = SiteOutcomeBoardService(BoardServices()).board(KOBO, day=date(2026, 10, 6))
    assert mini_body["window"]["known_at"] is None


def test_walk1_summary_verified_count_and_headline_money(monkeypatch) -> None:
    """WALK1-1 (WN-1, WN-3): the verified count is the boards' own VERIFIED Actions (stripped private key, same
    window as each Site row); `headline_money` passes through; a failed board adds to `verified_sites_unread`."""
    from dataclasses import replace

    from assetops_backend.site_outcomes.board import ActionFact

    def act(n, state):
        return ActionFact(f"a{n}", None, "t", None, None, True, False, state, None)

    real_compose = SiteOutcomeBoardService.compose

    def compose(self, site, **kw):
        comp, window = real_compose(self, site, **kw)
        if site is KOBO:
            facts = replace(comp.facts, actions=(act(1, "VERIFIED"), act(2, "PENDING"), act(3, None)))
            comp = replace(comp, facts=facts)
        return comp, window

    money = {"amount_low": "4.20", "amount_high": "4.20", "currency": "USD"}
    real_board = SiteOutcomeBoardService.board

    def board(self, site, **kw):
        body = real_board(self, site, **kw)
        if site is KOBO:
            body["rows"][0]["headline_money"] = money
        return body

    monkeypatch.setattr(SiteOutcomeBoardService, "compose", compose)
    monkeypatch.setattr(SiteOutcomeBoardService, "board", board)
    lo, hi = datetime(2026, 10, 1, tzinfo=UTC), datetime(2026, 10, 8, tzinfo=UTC)
    svc = SiteOutcomeBoardService(BoardServices())
    assert svc.board(KOBO, day=date(2026, 10, 6))["_verified_results"] == 1
    out = svc.summary([KOBO, COLD, ODD], lo, hi)
    assert out["verified_result_count"] == 1 and out["verified_sites_unread"] == 1  # ODD's board fails
    kobo, cold, odd = out["sites"]
    assert kobo["rows"][0]["headline_money"] == money
    assert all(r["headline_money"] is None for r in [*kobo["rows"][1:], *odd["rows"]])
    assert SiteOutcomeBoardService(BoardServices()).summary([ODD], lo, hi)["verified_result_count"] is None
