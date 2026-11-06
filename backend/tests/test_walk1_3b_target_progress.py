"""WALK1-3b (build sheet WALK1 Addendum 2, §A2.1-§A2.5): performance, KPI progress and potential on the Grow row.

Pure: `judge_month` (each rule, the c = 2/3 and avg = need boundaries, the configurable minimum), the `outcome_state`
precedence (an opportunity never outranks a declared objective; no-objective rows unchanged), the Kobo compose on the
story day (MET, On track, contributor order, the Opportunity chip), the TOO_EARLY text with its minimum, the EV pin,
declaration validation and its idempotency hash, and the vocabulary of every new string.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

import test_out_b2_mini as b2
import test_out_b3_cold_ev as b3
from assetops_backend.objectives.model import Declaration, ObjectiveRefused, payload_sha256, validate
from assetops_backend.outcomes import objectives as obj
from assetops_backend.outcomes.catalogue import OUTCOME_BY_KEY
from assetops_backend.outcomes.objectives import (
    BEHIND_PACE, DEFAULT_MIN_CHECKED_DAYS, MET, MISSED, NOT_JUDGED, ON_PACE, TOO_EARLY, ObjectiveFact, Reading,
    judge_month)
from assetops_backend.outcomes.status import SIGNAL_OPPORTUNITY, Signal, outcome_state
from assetops_backend.site_outcomes import mini, objective_facts
from assetops_backend.site_outcomes.board import assemble, objectives_wire
from test_out_b2_vocabulary import _patterns

GROW = mini.GROW
MG1, MG2 = OUTCOME_BY_KEY["MG-1"], OUTCOME_BY_KEY["MG-2"]
MILL = {"asset_code": "load-mill", "asset_id": "a-mill", "name": "Grain mill"}
PRICE = {"selection": {"state": "PRICED", "price": {"value": "0.2500", "currency": "USD"}}}
NOTE = "Declared for the demonstration"


def fact(target: str = "300", min_days: int = DEFAULT_MIN_CHECKED_DAYS) -> ObjectiveFact:
    return ObjectiveFact("MG-1", "productive_use_kwh", obj.AT_LEAST, Decimal(target), False, "t", "DECLARED", "r1",
                         None, min_days)


def month(value: str | None, c: int, e: int, m: int = 31) -> Reading:
    return Reading(None if value is None else Decimal(value), e == m and c == m, None, c, e, m)


# --------------------------------------------------------------- judge_month (§A2.2, §A2.5)

def test_judge_month_truth_table() -> None:
    f = fact()  # 300 kWh in a 31-day month: need = 300 / 31 kWh a day
    assert judge_month(f, None) == NOT_JUDGED
    assert judge_month(f, month(None, 0, 10)) == NOT_JUDGED
    assert judge_month(f, month("0", 0, 10)) == NOT_JUDGED            # no checked day
    # 1. reaching the target is MET whatever the missing days (even on one checked day)
    assert judge_month(f, month("300", 1, 5)) == MET
    assert judge_month(f, month("673.2", 4, 29)) == MET
    # 2. a complete month with every day checked below target is MISSED
    assert judge_month(f, month("299", 31, 31)) == MISSED
    # 5. a complete month with gaps below target is behind pace, never MISSED
    assert judge_month(f, month("200", 30, 31)) == BEHIND_PACE
    # 3. boundary c = 2 / 3 under the default minimum of 3
    assert judge_month(f, month("100", 2, 10)) == TOO_EARLY
    assert judge_month(f, month("100", 3, 10)) == ON_PACE
    # 4/5. boundary avg = need: 3 days at exactly 300/31 a day is on pace; a hair less is behind
    exact = Decimal(300) * 3 / 31
    assert judge_month(f, Reading(exact, False, None, 3, 10, 31)) == ON_PACE
    assert judge_month(f, Reading(exact - Decimal("0.0001"), False, None, 3, 10, 31)) == BEHIND_PACE


def test_judge_month_configurable_minimum() -> None:
    assert judge_month(fact(min_days=1), month("20", 1, 2)) == ON_PACE     # one checked day can judge pace
    assert judge_month(fact(min_days=1), month("5", 1, 2)) == BEHIND_PACE
    assert judge_month(fact(min_days=5), month("100", 4, 10)) == TOO_EARLY  # four days are too early
    assert judge_month(fact(min_days=5), month("100", 5, 10)) == ON_PACE


def test_default_minimum_from_rows() -> None:
    row = {"outcome_key": "MG-1", "measure_key": "productive_use_kwh", "target": "300", "currency": None,
           "source": "DECLARED", "id": "o1", "source_note": NOTE}
    [absent] = objective_facts.from_rows([row], mini.num)
    [null] = objective_facts.from_rows([dict(row, min_checked_days=None)], mini.num)
    [five] = objective_facts.from_rows([dict(row, min_checked_days=5)], mini.num)
    assert absent.min_checked_days == null.min_checked_days == 3 == DEFAULT_MIN_CHECKED_DAYS
    assert five.min_checked_days == 5
    assert [m.key for m in obj.MEASURES.values() if m.monthly] == ["productive_use_kwh"]


# --------------------------------------------------------------- outcome_state precedence (§A2.1)

def st(outcome, signals=(), **kw):
    return outcome_state(outcome, settled=True, signals=list(signals), readiness=None, **kw)


def test_opportunity_no_longer_outranks_a_declared_objective() -> None:
    opp = [Signal(SIGNAL_OPPORTUNITY, "MG-1", True, True)]
    assert st(MG1, opp, objective=MET) == ("ON_TRACK", "OBJECTIVE_MET")
    assert st(MG1, opp, objective=ON_PACE) == ("ON_TRACK", "OBJECTIVE_ON_PACE")
    assert st(MG1, opp, objective=BEHIND_PACE) == ("WATCH", "OBJECTIVE_BEHIND_PACE")
    assert st(MG1, opp, objective=TOO_EARLY) == ("UNKNOWN", "OBJECTIVE_TOO_EARLY")
    assert st(MG1, opp, objective=NOT_JUDGED) == ("UNKNOWN", "OBJECTIVE_NOT_JUDGED")
    assert st(MG1, opp, objective=MISSED) == ("NEEDS_ATTENTION", "OBJECTIVE_MISSED")
    # rows without an objective keep today's order: Opportunity, then No objective
    assert st(MG1, opp) == ("OPPORTUNITY", "OPPORTUNITY_OPEN")
    assert st(MG1) == ("NO_OBJECTIVE", "NO_OBJECTIVE_DECLARED")
    assert st(MG1, opp, objectives_ok=False) == ("OPPORTUNITY", "OPPORTUNITY_OPEN")
    # findings keep their precedence above the objective
    applied = [Signal("FINDING", "MG-2", True, True, applied=True)]
    assert st(MG2, applied, objective=MET)[0] == "WATCH"


# --------------------------------------------------------------- Kobo compose (§A2.2, §A2.3)

LO = datetime(b2.DAY.year, b2.DAY.month, b2.DAY.day, tzinfo=timezone.utc)
NO_HEADROOM = dict(b2.DEPTH, renewable={"headroom_kw": {"low": None, "high": None}, "eligible_days": None,
                                        "assessed_days": None})


def mill_day(day: datetime, kw: str = "21.0375") -> list[dict[str, Any]]:
    """03:00-11:00 UTC in five-minute intervals (8 h x 21.0375 kW = 168.3 kWh)."""
    return [{"asset_id": "a-mill", "start": day + timedelta(hours=3, minutes=5 * n),
             "end": day + timedelta(hours=3, minutes=5 * n + 5), "value_kw": kw, "quality": "GOOD"} for n in range(96)]


def mg1_row(min_days: int | None = None) -> list[dict[str, Any]]:
    row = {"outcome_key": "MG-1", "measure_key": "productive_use_kwh", "target": "300", "currency": None,
           "source": "DECLARED", "id": "o1", "source_note": NOTE}
    return [dict(row, min_checked_days=min_days)] if min_days is not None else [row]


def run(days: list[int], *, fake: b2.Fake | None = None, objectives: Any = None):
    """Mill readings on the given October dates; the fake returns those readings that touch the asked window."""
    readings = [r for d in days for r in mill_day(datetime(2026, 10, d, tzinfo=timezone.utc))]
    seen: list[tuple[datetime, datetime]] = []

    def productive_readings(ids, lo, hi):
        seen.append((lo, hi))
        return [r for r in readings if r["start"] < hi and r["end"] > lo]

    ports = replace((fake or b2.Fake(cards=NO_HEADROOM)).ports(), productive_users=lambda at: [MILL],
                    productive_readings=productive_readings, productive_price=lambda at: PRICE,
                    objectives=lambda: mg1_row() if objectives is None else objectives)
    comp = mini.compose(ports, site_code=b2.C, day=b2.DAY, site_timezone=b2.ZONE)
    return comp, {r["category"]: r for r in assemble(comp.facts)}[GROW], seen


def test_kobo_month_to_date_met_is_on_track_without_an_opportunity_chip() -> None:
    # Board day 20 Oct (Nairobi, UTC+3); four checked mill days of 168.3 kWh in October before it and on it.
    comp, row, seen = run([2, 9, 16, 20])
    assert row["state"] == "ON_TRACK" and row["state_label"] == "On track"
    assert {o["key"]: o["reason"] for o in row["outcomes"]}["MG-1"] == "OBJECTIVE_MET"
    assert row["potential"] is None                     # no spare-solar headroom read
    assert row["headline"] == "estimated productive-use sales"  # (a) performance stays the headline
    assert [c["key"] for c in row["contributors"]] == [
        "productive_sales", "declared_objective:MG-1", "productive_use", "productive_price", "cash_collected",
        "site_earnings"]
    line = next(c for c in row["contributors"] if c["key"] == "declared_objective:MG-1")
    assert line["text"] == ("Productive electricity sales: at least 300 kWh sold for productive use a month · "
                            "673.2 kWh so far this month, on 4 of 20 days checked")
    assert line["confidence"] == {"label": "Met", "tone": "green"}
    # the month window: Nairobi local 1 Oct 00:00 (30 Sep 21:00 UTC) through the end of the local board day
    assert (datetime(2026, 9, 30, 21, tzinfo=timezone.utc), datetime(2026, 10, 20, 21, tzinfo=timezone.utc)) in seen
    wire = next(o for o in objectives_wire(comp.facts) if o["outcome_key"] == "MG-1")
    assert wire["verdict"] == MET


def test_spare_solar_is_the_opportunity_chip_beside_the_kpi_state() -> None:
    comp, row, _ = run([2, 9, 16, 20], fake=b2.Fake())  # the fixture's spare-solar signal is open
    assert row["state"] == "ON_TRACK"
    assert row["potential"] == {"label": "Opportunity", "text": "Productive-use headroom"}
    assert any(i["kind"] == "OPPORTUNITY" for i in row["issues"])
    _, no_objective, _ = run([20], fake=b2.Fake(), objectives=[])
    assert no_objective["state"] == "OPPORTUNITY" and no_objective["potential"] is None


def test_pace_texts_and_states() -> None:
    _, row, _ = run([9, 16, 20], fake=b2.Fake(cards=NO_HEADROOM),
                    objectives=[dict(mg1_row()[0], target="6000")])  # 504.9 kWh over 3 days vs 6000/31 a day
    line = next(c for c in row["contributors"] if c["key"] == "declared_objective:MG-1")
    assert line["text"].endswith("504.9 kWh so far this month, on 3 of 20 days checked · averages 168.3 kWh a day; "
                                 "the target needs 193.5 kWh a day")
    assert line["confidence"] == {"label": "Behind pace", "tone": "amber"} and row["state"] == "WATCH"
    _, row, _ = run([9, 16, 20], objectives=[dict(mg1_row()[0], target="3000")])
    line = next(c for c in row["contributors"] if c["key"] == "declared_objective:MG-1")
    assert line["confidence"] == {"label": "On pace", "tone": "green"} and row["state"] == "ON_TRACK"


def test_too_early_text_names_the_minimum() -> None:
    _, row, _ = run([20])
    line = next(c for c in row["contributors"] if c["key"] == "declared_objective:MG-1")
    assert line["text"].endswith("168.3 kWh so far this month, on 1 checked day; too early to judge "
                                 "(needs 3 checked days)")
    assert line["confidence"] == {"label": "Too early to judge", "tone": "gray"} and row["state"] == "UNKNOWN"
    # a declared minimum of 5: four checked days of 50 kWh are still too early
    _, row, _ = run([2, 9, 16, 20], objectives=[dict(mg1_row(5)[0], target="3000")])
    line = next(c for c in row["contributors"] if c["key"] == "declared_objective:MG-1")
    assert line["text"].endswith("673.2 kWh so far this month, on 4 checked days; too early to judge "
                                 "(needs 5 checked days)")


def test_conflicting_day_is_not_checked() -> None:
    overlap = [{"asset_id": "a-mill", "start": LO + timedelta(hours=3), "end": LO + timedelta(hours=4),
                "value_kw": "10", "quality": "GOOD"}] * 2
    readings = mill_day(datetime(2026, 10, 9, tzinfo=timezone.utc)) + overlap
    ports = replace(b2.Fake(cards=NO_HEADROOM).ports(), productive_users=lambda at: [MILL],
                    productive_readings=lambda ids, lo, hi: [r for r in readings if r["start"] < hi and r["end"] > lo],
                    productive_price=lambda at: PRICE, objectives=lambda: mg1_row())
    comp = mini.compose(ports, site_code=b2.C, day=b2.DAY, site_timezone=b2.ZONE)
    mg1 = comp.facts.readings["MG-1"]
    assert (mg1.value, mg1.checked_days) == (Decimal("168.3"), 1)  # the board day's conflict adds nothing


def test_ev_grow_rows_are_unchanged() -> None:
    """EV declares no Grow objective (no EV Grow measure exists), so the generic precedence leaves its row alone."""
    assert not [m for m in obj.MEASURES.values() if m.outcome in ("EV-3", "EV-6")]
    _, rows = b3.run_ev()
    assert rows[GROW]["potential"] is None and rows[GROW]["state"] != "OPPORTUNITY"


# --------------------------------------------------------------- declaration (§A2.5)

def decl(measure: str = "productive_use_kwh", outcome: str = "MG-1", target: str = "300", **kw: Any) -> Declaration:
    return Declaration("KOBO-001", outcome, measure, Decimal(target), None, "DECLARED", NOTE, None,
                       "walk1-3b-kobo-mg-1", **kw)


@pytest.mark.parametrize("value", [0, 29, 2.5, "3", True])
def test_min_checked_days_refused(value: Any) -> None:
    with pytest.raises(ObjectiveRefused) as refused:
        validate(decl(min_checked_days=value))
    assert (refused.value.status, refused.value.code) == (422, "OBJECTIVE_INVALID")


def test_min_checked_days_refused_for_a_non_monthly_measure() -> None:
    with pytest.raises(ObjectiveRefused) as refused:
        validate(decl("avoidable_generator_minutes", "MG-2", "0", min_checked_days=3))
    assert (refused.value.status, refused.value.code) == (422, "OBJECTIVE_INVALID")


@pytest.mark.parametrize("value", [1, 28, None])
def test_min_checked_days_accepted(value: Any) -> None:
    validate(decl(min_checked_days=value))


def test_existing_declaration_keeps_its_hash() -> None:
    d = decl()
    before = {"site_code": "kobo-001", "outcome_key": "MG-1", "measure_key": "productive_use_kwh", "target": "300",
              "currency": None, "source": "DECLARED", "source_note": NOTE, "expected_prior": None}
    expected = hashlib.sha256(json.dumps(before, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    assert payload_sha256(d) == expected
    assert payload_sha256(decl(min_checked_days=3)) != expected  # present: part of the payload


# --------------------------------------------------------------- vocabulary

def test_new_strings_are_in_copy_and_plain() -> None:
    patterns = _patterns()
    new = [mini.MG1_SO_FAR, mini.MG1_PACE, mini.MG1_TOO_EARLY, mini.MG1_MISSED,
           *(c["label"] for c in obj.VERDICT_CHIP.values()), "Opportunity"]
    hits = [(t, name) for t in new for name, p in patterns if p.search(t)]
    assert hits == [], hits
    for template in (mini.MG1_SO_FAR, mini.MG1_PACE, mini.MG1_TOO_EARLY, mini.MG1_MISSED):
        assert any(template.split("{")[0] in c for c in mini.COPY), template
    for days in ([20], [2, 9, 16, 20]):
        _, row, _ = run(days, fake=b2.Fake())
        texts = [row["headline"] or "", row["subline"] or "", row["potential"]["label"] if row["potential"] else "",
                 *(c["text"] for c in row["contributors"]), *(c["confidence"]["label"] for c in row["contributors"]
                                                              if c["confidence"])]
        assert [(t, n) for t in texts for n, p in patterns if p.search(t)] == []
