"""1a (spec `specs/1a-optimize-card-scope/spec.md`, D-1A.1): the Portfolio Optimize card's figure is one lead
Finding's stored cost, chosen on the window's last day. Commit 1 pins today's behaviour (P1 to P4) before any change.
Pure: no database."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

import pytest

from assetops_backend.chain import vocabulary as v
from assetops_backend.chain.read import FindingHead, board_day, lead_finding, window_day
from assetops_backend.i18n import message, render
from assetops_backend.site_outcomes.read import (WINDOW_BASIS_DAY, BoardServices, SiteOutcomeBoardService, SiteRef,
                                                 _optimize_card)

UTC = timezone.utc
NAIROBI = "Africa/Nairobi"
LO, HI = datetime(2026, 10, 1, tzinfo=UTC), datetime(2026, 10, 31, tzinfo=UTC)
# The `KOBO` SiteRef literal of `test_out_w2_summary_window.py` (fixed ids here: the pins read no id).
T = UUID("00000000-0000-4000-8000-0000000001a0")
KOBO = SiteRef(T, UUID("00000000-0000-4000-8000-0000000001a1"), "KOBO-001", "Kobo", "MINIGRID", NAIROBI)


def _claim(amount: str | None, label: str = "possible_extra_fuel_cost", days=None, cur: str = "USD") -> dict:
    """As `test_ch5d1_optimize_card.py`: a cost claim as `money_claim` builds it (a stored consequence: no days)."""
    return v.money_claim(label, None if amount is None else {"amount": Decimal(amount), "currency": cur}, days).to_json()


def _site(code: str, name: str, claim: dict | None, nodes: bool = True) -> dict:
    """As `test_ch5d1_optimize_card.py`: one summary Site with only its `OPTIMIZE_COST` row."""
    row = {"category": "OPTIMIZE_COST", "state": "NEEDS_ATTENTION", "state_label": "Needs attention",
           "nodes": {"kpi": None, "potential": None, "earnings": claim} if nodes else None}
    return {"site_code": code, "site_name": name, "rows": [row], "earnings": None}


def _head(fid: str, start: datetime, end: datetime | None) -> FindingHead:
    return FindingHead(finding_id=fid, revision_id=f"{fid}-r1", revision_no=1, lifecycle="OPEN", transition=None,
                       episode_start=start, episode_end=end, mechanism="GENERATOR_AVOIDABLE", subject_ref="gen-1",
                       thread_id=None, occurrence_no=None)


# --- commit 1: the pins ----------------------------------------------------------------------------------------


def test_p1_the_board_day_of_a_multi_day_window_is_its_last_day() -> None:
    """Pins `chain/read.py` `window_day` rule 3: `to` is a UTC midnight, so the day is the UTC date of `to - 1 µs`."""
    assert window_day(LO, HI, NAIROBI) == date(2026, 10, 30)
    assert window_day(LO, HI, None) == date(2026, 10, 30)


def test_p2_a_mini_grid_site_is_judged_on_that_day_in_the_summary() -> None:
    """Pins `site_outcomes/read.py` `summary_window`: mini reads `window_day` on the DAY basis, no lo/hi."""
    service = SiteOutcomeBoardService(BoardServices(estate=None))
    assert service.summary_window(KOBO, LO, HI, None) == (WINDOW_BASIS_DAY, date(2026, 10, 30), None, None)
    assert WINDOW_BASIS_DAY == "DAY"


def test_p3_the_money_comes_from_the_one_lead_finding_touching_the_board_day() -> None:
    """Pins `chain/read.py` `lead_finding`: of the heads whose episode touches `[start, end)`, the greatest episode
    start; a head that ended before the day is never chosen."""
    a = _head("a", datetime(2026, 10, 2, tzinfo=UTC), datetime(2026, 10, 10, tzinfo=UTC))
    b = _head("b", datetime(2026, 10, 30, 6, tzinfo=UTC), None)
    start, end = board_day(date(2026, 10, 30), NAIROBI)
    assert lead_finding((a, b), start, end, source_open=True) == (b.finding_id, b.revision_id, True)
    assert lead_finding((a,), start, end, source_open=True) is None


def test_p4_the_card_carries_no_day_or_scope_today() -> None:
    """Pins `site_outcomes/read.py` `_optimize_card`: the seven keys, and no days line for a stored consequence.
    Commit 2 (1a, spec §2) adds the eighth key, `scope_text`, None without a scope (the pin's call passes none)."""
    card = _optimize_card([_site("K", "Kobo", _claim("3.31"))])
    assert set(card) == {"value", "missing", "detail", "basis_text", "days_line", "tone", "claim", "scope_text"}
    assert card["days_line"] is None and card["scope_text"] is None


# --- commit 2: the day and scope stated (spec §3.5) --------------------------------------------------------------

S1 = "Cost of Kobo's lead issue on 30 October 2026, the last of the 30 days shown, not their total"
S2 = "Cost of Kobo's lead issue on 30 October 2026"
S3 = "Cost of GreenHarvest's latest issue in the 7 days shown, not their total"
S4 = "Cost at each Site of its lead issue on 30 October 2026, the last of the 30 days shown, not their total"
S5 = "Cost at each Site of its lead issue in the days it shows, not their total"
OCT30, OCT29, OCT31 = date(2026, 10, 30), date(2026, 10, 29), date(2026, 10, 31)
BASIS_MONEY = "Modelled from the stored record and the declared price · not a saving"


def _range_claim(low: str, high: str) -> dict:
    return v.money_claim("possible_extra_fuel_cost", {"low": Decimal(low), "high": Decimal(high), "currency": "USD"},
                         None).to_json()


def _scope(day: dict, days: dict):
    from assetops_backend.site_outcomes.read import CostScope
    return CostScope(day, days)


def _card(sites: list[dict], scope) -> dict:
    return _optimize_card(sites, scope=scope)


TWO = [_site("K", "Kobo", _claim("3.31")), _site("D", "Depot", _claim("1.20"))]

#: (name, sites, scope, expected scope text) for S1 to S5c, and S7's range claim on 31 Oct.
SCOPED = [
    ("S1", [_site("K", "Kobo", _claim("3.31"))], ({"K": OCT30}, {"K": 30}), S1),
    ("S2", [_site("K", "Kobo", _claim("3.31"))], ({"K": OCT30}, {"K": 1}), S2),
    ("S3", [_site("G", "GreenHarvest", _claim("3.31"))], ({"G": None}, {"G": 7}), S3),
    ("S4", TWO, ({"K": OCT30, "D": OCT30}, {"K": 30, "D": 30}), S4),
    ("S5 days", TWO, ({"K": OCT30, "D": OCT30}, {"K": 30, "D": 31}), S5),
    ("S5 day", TWO, ({"K": OCT29, "D": OCT30}, {"K": 30, "D": 30}), S5),
    ("S5b", TWO, ({"K": None, "D": None}, {"K": 7, "D": 7}), S5),
    ("S5c", TWO, ({"K": OCT30, "D": None}, {"K": 30, "D": 30}), S5),
    ("S7 range", [_site("K", "Kobo", _range_claim("3.31", "3.97"))], ({"K": OCT31}, {"K": 7}),
     "Cost of Kobo's lead issue on 31 October 2026, the last of the 7 days shown, not their total"),
]


def test_s1_one_priced_site_over_30_days_names_the_day_and_scope_and_keeps_its_figure() -> None:
    claim = _claim("3.31")
    card = _card([_site("K", "Kobo", claim)], _scope({"K": OCT30}, {"K": 30}))
    assert card["scope_text"] == S1
    # byte-equal to `test_ch5d1_optimize_card.py`'s expected values
    assert card["value"] == {"text": "3.31 USD", "small": "possible extra fuel cost"}
    assert card["value"]["text"].encode() == claim["text"].encode()
    assert card["detail"] == "At Kobo · not added across sites" and card["basis_text"] == BASIS_MONEY
    assert card["claim"] == claim
    assert list(card)[-1] == "scope_text"


def test_s2_one_day_window_reads_the_day_alone() -> None:
    assert _card([_site("K", "Kobo", _claim("3.31"))], _scope({"K": OCT30}, {"K": 1}))["scope_text"] == S2


def test_s3_a_period_site_reads_its_latest_issue_in_the_days_shown() -> None:
    card = _card([_site("G", "GreenHarvest", _claim("3.31"))], _scope({"G": None}, {"G": 7}))
    assert card["scope_text"] == S3


def test_s4_two_priced_sites_same_day_read_each_site_and_never_sum() -> None:
    card = _card(TWO, _scope({"K": OCT30, "D": OCT30}, {"K": 30, "D": 30}))
    assert card["scope_text"] == S4
    assert card["detail"] == "Kobo: 3.31 USD possible extra fuel cost · Depot: 1.20 USD possible extra fuel cost"
    assert card["claim"] is None and card["value"] == {"text": "Costs at 2 sites", "small": None}


def test_s5_two_priced_sites_whose_days_differ_read_each_differ() -> None:
    assert _card(TWO, _scope({"K": OCT30, "D": OCT30}, {"K": 30, "D": 31}))["scope_text"] == S5
    assert _card(TWO, _scope({"K": OCT29, "D": OCT30}, {"K": 30, "D": 30}))["scope_text"] == S5


def test_s5b_two_period_sites_read_each_differ() -> None:
    """D-1A.10 (R3): PERIOD Sites have no single day; 'in the days it shows' is true on both bases."""
    assert _card(TWO, _scope({"K": None, "D": None}, {"K": 7, "D": 7}))["scope_text"] == S5


def test_s5c_a_day_site_and_a_period_site_read_each_differ() -> None:
    assert _card(TWO, _scope({"K": OCT30, "D": None}, {"K": 30, "D": 30}))["scope_text"] == S5


def test_s6_no_priced_site_or_no_scope_reads_no_scope_line() -> None:
    none = [_site("K", "Kobo", _claim(None)), _site("D", "Depot", None)]
    assert _card(none, _scope({"K": OCT30, "D": OCT30}, {"K": 30, "D": 30}))["scope_text"] is None
    assert _card([_site("K", "Kobo", _claim("3.31"))], None)["scope_text"] is None
    assert _optimize_card([_site("K", "Kobo", _claim("3.31"))])["scope_text"] is None


def _amounts(claim: dict) -> list[str]:
    value = claim.get("value") or {}
    return [value[k] for k in ("amount", "low", "high") if value.get(k) is not None]


def test_s7_the_scope_line_holds_no_amount() -> None:
    """D-1A.2, D-1A.10 (R1): one figure; the scope text holds neither the claim's text nor any of its amounts as a
    whole decimal token (`(?<![\\d.])<amount>(?![\\d.])`)."""
    import re
    for name, sites, (day, days), want in SCOPED:
        card = _card(sites, _scope(day, days))
        text = card["scope_text"]
        assert text == want, name
        for site in sites:
            claim = site["rows"][0]["nodes"]["earnings"]
            assert claim["text"] not in text, (name, claim["text"])
            for amount in _amounts(claim):
                assert re.search(rf"(?<![\d.]){re.escape(amount)}(?![\d.])", text) is None, (name, amount)


# --- S8, S9: the summary wiring and COH-17 O1 ------------------------------------------------------------------

KISIWA = SiteRef(T, UUID("00000000-0000-4000-8000-0000000001a2"), "KISIWA-001", "Kisiwa", "MINIGRID", NAIROBI)


def _fake_board(monkeypatch, priced: dict[str, str]) -> list[dict]:
    """The recording fake board of `test_out_w2_summary_window.py`, whose `OPTIMIZE_COST` row's `_window` nodes carry
    a priced cost claim for each Site code in `priced`; the real `_summary_row` keeps those nodes."""
    from datetime import timedelta

    from assetops_backend.outcomes.catalogue import CATEGORIES
    from assetops_backend.site_outcomes.read import wire
    calls: list[dict] = []

    def board(self, site, *, day=None, lo=None, hi=None, known_at=None, pin=None, node_days=None, windows=None):
        calls.append({"site": site.site_code, "day": day, "lo": lo, "hi": hi, "node_days": node_days})
        a = lo or datetime(day.year, day.month, day.day, tzinfo=UTC)
        b = hi or a + timedelta(days=1)
        rows = [{"category": c, "state": "NEEDS_ATTENTION" if c == "OPTIMIZE_COST" else "UNKNOWN",
                 "state_label": "x", "tone": "neutral", "lead_outcome": None, "headline": None,
                 "headline_money": None} for c in CATEGORIES]
        nodes = {"OPTIMIZE_COST": {"kpi": None, "potential": None, "earnings": _claim(priced[site.site_code])}
                 } if site.site_code in priced else {}
        return {"window": {"from": wire(a), "to": wire(b), "known_at": None}, "read_state": "AVAILABLE",
                "rows": rows, "warnings": [], "_short_values": {}, "_window": {"nodes": nodes, "earnings": {}}}

    monkeypatch.setattr(SiteOutcomeBoardService, "board", board)
    return calls


def _summary(sites, lo, hi) -> dict:
    return SiteOutcomeBoardService(BoardServices(estate=None)).summary(sites, lo, hi, None)


def test_s8_the_summary_states_the_day_and_scope_from_its_window(monkeypatch) -> None:
    _fake_board(monkeypatch, {"KOBO-001": "3.31"})
    month = _summary([KOBO], LO, datetime(2026, 10, 31, tzinfo=UTC))
    assert month["cards"]["OPTIMIZE_COST"]["scope_text"] == S1
    day = _summary([KOBO], datetime(2026, 10, 30, tzinfo=UTC), datetime(2026, 10, 31, tzinfo=UTC))
    assert day["cards"]["OPTIMIZE_COST"]["scope_text"] == S2


def test_s9_coh17_o1_passes_on_the_scoped_summaries(monkeypatch) -> None:
    """D-1A.4, D-1A.10 (R4): COH-17 O1 with its real signature, unchanged, on S8's two summaries and two priced
    Sites."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "checks"))
    from chain_coherence import coh17_optimize

    _fake_board(monkeypatch, {"KOBO-001": "3.31", "KISIWA-001": "1.20"})
    summaries = [_summary([KOBO], LO, HI),
                 _summary([KOBO], datetime(2026, 10, 30, tzinfo=UTC), HI),
                 _summary([KOBO, KISIWA], LO, HI)]
    assert summaries[2]["cards"]["OPTIMIZE_COST"]["scope_text"] == S4
    for s in summaries:
        assert s["cards"]["OPTIMIZE_COST"]["scope_text"] is not None
        tally = {"compared": 0}
        assert coh17_optimize("1a", s, [], tally) == []
        assert tally["compared"] == 1


# --- the statement's cases render their English through the shipped catalogue -----------------------------------
# `test_sc1_statements.py` T9 renders only the common and worked cases; the catalogue guard proves coverage, not the
# words. So each `portfolio_card.cost_scope` case is rendered here, and the variant chosen is the case's (D-1A.9).

from statement_cases import portfolio_card as card_cases  # noqa: E402


@pytest.mark.parametrize("case", card_cases.CASES, ids=lambda c: c.variant)
def test_cost_scope_cases_render_their_english_through_their_variant(case) -> None:
    from assetops_backend.i18n.render import _render
    assert render(message(case.key, **case.facts)) == case.english
    trace: list = []
    _render(message(case.key, **case.facts), None, False, trace)
    assert trace[0] == (case.key, case.variant)


def test_cost_scope_cases_cover_the_six_variants() -> None:
    assert [c.variant for c in card_cases.CASES] == ["one_day", "one_range", "one_latest", "each_one_day",
                                                     "each_range", "each_differ"]
