"""K10 v2 (build sheet DIESEL-1 §9t.3 items 4-5, ruling DIESEL-1-R3t): the mini board on a declared-absent day.

The zero is stated (Grow line, headline, MG-1 earnings node, gap note), never priced, never summed, never "checked";
a day the chain read did not prove declared absent keeps today's wording. Fakes from `test_out_b2_mini`."""
from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

import test_out_b2_mini as b2
from link_parity import checked

from assetops_backend.chain import vocabulary as v
from assetops_backend.chain.read import DayFacts
from assetops_backend.site_outcomes import mini
from assetops_backend.site_outcomes.board import assemble

GROW = mini.GROW
KWH = "productive_kwh"
DECL = {b2.DAY: frozenset({KWH})}
NO_SPARE = {"study": None}   # no opportunity item: no spare-solar headline


def objective(outcome, measure, target):
    return {"id": uuid5(NAMESPACE_URL, f"{outcome}/k10"), "outcome_key": outcome, "measure_key": measure,
            "target": Decimal(target), "currency": None, "source": "DECLARED", "source_note": "demo"}


def run(fake, objectives=None):
    ports = fake.ports()
    if objectives is not None:
        ports = replace(ports, objectives=lambda: objectives)
    comp = mini.compose(ports, site_code=b2.C, day=b2.DAY, site_timezone=b2.ZONE)
    return comp, {r["category"]: r for r in checked(assemble(comp.facts))}


def sales(row):
    return b2.contributor(row, "productive_sales")


def earnings(row):
    return ((row.get("nodes") or {}).get("earnings") or {})


def test_literals_are_r3t_exactly():
    assert mini.SALES_NONE_DECLARED == ("0 kWh · no productive-use equipment declared for this site · "
                                        "not a metered reading")
    assert mini.GROW_NONE_HEADLINE == "No productive-use equipment declared · 0 kWh"
    assert mini.GAPS_NONE_DECLARED == ("Productive use not assessed: no productive-use equipment declared for this "
                                       "site (0 kWh)")
    assert v.NODE_TEXT["money.none_declared"] == "No productive-use sales · no productive-use equipment declared"


def test_declared_absent_day_states_the_zero_on_line_headline_and_earnings():
    comp, rows = run(b2.Fake(day={"none_declared": DECL}, **NO_SPARE))
    grow = rows[GROW]
    line = sales(grow)
    assert line["text"] == mini.SALES_NONE_DECLARED
    assert line.get("confidence") is None and line.get("href") is None   # no chip, no link
    assert grow["headline"] == mini.GROW_NONE_HEADLINE
    assert grow.get("subline") is None
    assert comp.facts.headline_money.get(GROW) is None                   # no headline money
    assert comp.node_inputs.none_declared == frozenset({KWH})
    e = earnings(grow)
    assert e["text"] == "No productive-use sales · no productive-use equipment declared"
    assert e.get("value") is None                                         # never priced, so never summed


def test_spare_solar_headline_still_leads():
    _, rows = run(b2.Fake(day={"none_declared": DECL}))
    assert rows[GROW]["headline"] == "18–24.3 kW of daytime solar unused"
    assert sales(rows[GROW])["text"] == mini.SALES_NONE_DECLARED


def test_no_users_without_declaration_keeps_todays_wording():
    comp, rows = run(b2.Fake(**NO_SPARE))
    assert sales(rows[GROW])["text"] == mini.SALES_NO_USERS
    assert rows[GROW]["subline"] == mini.GROW_SUBLINE
    assert rows[GROW]["headline"] != mini.GROW_NONE_HEADLINE
    assert comp.node_inputs.none_declared == frozenset()
    assert earnings(rows[GROW]).get("text") != v.NODE_TEXT["money.none_declared"]
    # a declaration for another day (e.g. the window's earlier days only) does not reach the board day
    _, rows = run(b2.Fake(day={"none_declared": {date(2026, 10, 19): frozenset({KWH})}}, **NO_SPARE))
    assert sales(rows[GROW])["text"] == mini.SALES_NO_USERS


def test_declared_users_present_ignore_the_flag():
    users = [{"asset_code": "MILL", "asset_id": "m1", "name": "Grain mill"}]
    fake = b2.Fake(day={"none_declared": DECL}, **NO_SPARE)
    _, rows = run_with_users(fake, users)
    assert sales(rows[GROW])["text"] == mini.SALES_NO_READINGS.format(names="Grain mill")


def run_with_users(fake, users):
    ports = replace(fake.ports(), productive_users=lambda at: users)
    comp = mini.compose(ports, site_code=b2.C, day=b2.DAY, site_timezone=b2.ZONE)
    return comp, {r["category"]: r for r in checked(assemble(comp.facts))}


def facts(gaps=(), grades=None, none_declared=None):
    days = (date(2026, 10, 18), date(2026, 10, 19), b2.DAY)
    return DayFacts(days, grades or {}, True, "FULL", tuple(gaps), none_declared=none_declared or {})


def test_gap_line_three_forms():
    d18 = date(2026, 10, 18)
    # gaps and a declared-absent window day: the current text plus the note
    line = mini.finding_gap_line(facts([d18], none_declared=DECL), 31)
    assert line == {"text": mini.GAPS_NO_READINGS.format(g=1, n=31, verb="has") + " · " + mini.GAPS_NONE_DECLARED,
                    "days": ["2026-10-18"], "withheld": False}
    pend = facts([d18], grades={d18: {"critical_served": {"SITE": "PENDING"}}}, none_declared=DECL)
    assert mini.finding_gap_line(pend, 31)["text"] == (mini.GAPS_NOT_ASSESSED.format(g=1, n=31, verb="is") + " · "
                                                       + mini.GAPS_NONE_DECLARED)
    # no gaps, a declared-absent day: the note alone
    assert mini.finding_gap_line(facts(none_declared=DECL), 31) == {"text": mini.GAPS_NONE_DECLARED, "days": [],
                                                                    "withheld": False}
    # no gaps, no declaration: None (today); gaps, no declaration: today's text
    assert mini.finding_gap_line(facts(), 31) is None
    assert mini.finding_gap_line(facts([d18]), 31)["text"] == mini.GAPS_NO_READINGS.format(g=1, n=31, verb="has")
    # a declaration outside the window's days adds no note
    assert mini.finding_gap_line(facts(none_declared={date(2026, 9, 1): frozenset({KWH})}), 31) is None


def test_gap_line_reaches_the_board():
    comp, _ = run(b2.Fake(day={"none_declared": DECL}, **NO_SPARE))
    assert comp.facts.finding_gaps == {"text": mini.GAPS_NONE_DECLARED, "days": [], "withheld": False}


def test_mg1_with_objective_and_declared_absent_is_never_on_track_or_met():
    objs = [objective("MG-1", "productive_use_kwh", "300")]
    for over in ({}, NO_SPARE):
        _, rows = run(b2.Fake(day={"none_declared": DECL}, **over), objs)
        grow = rows[GROW]
        mg1 = next(o for o in grow["outcomes"] if o["key"] == "MG-1")
        assert mg1["state"] != "ON_TRACK", mg1
        assert grow["state"] != "ON_TRACK"
        kpi = (grow.get("nodes") or {}).get("kpi") or {}
        assert kpi.get("verdict") != "MET", kpi
        for c in grow["contributors"]:
            assert (c.get("confidence") or {}).get("label") != "Met", c
    # without an objective: no objective, or Opportunity when the headroom thread is open; never On track
    _, rows = run(b2.Fake(day={"none_declared": DECL}))
    assert rows[GROW]["state"] != "ON_TRACK"


def test_kobo_shaped_composition_body_equal_to_before():
    plain, _ = run(b2.Fake())
    keyed, _ = run(b2.Fake(day={"none_declared": {}}))
    assert checked(assemble(plain.facts)) == checked(assemble(keyed.facts))
    assert plain.facts == keyed.facts and plain.node_inputs == keyed.node_inputs
