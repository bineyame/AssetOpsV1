"""5c unit 1 (spec sections 2, 3 and 6, tests 1 to 7): the month's deep-dive view, pure, over 3B7a's served snapshot.

Every English literal below is written by hand from spec section 3.5, changed only by the rules the packet lists
(PF2/D-4A.12 records, PF5 "when", PF8 headline object, D-3A7.16 standing details). Worlds are 5b section 5.2's
(3A4 `new_world()`, 4b's money fixture, 5a's steps 1 and 2, 5b's Mto step), built and served by 3B7a in memory.
"""
from __future__ import annotations

import json
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

import pytest

import test_3b7a_structure_snapshot as t3
import test_5b_attribution as t5b
from assetops_backend.deep_dive import tables as T
from assetops_backend.deep_dive import words as W
from assetops_backend.deep_dive import view as V
from assetops_backend.deep_dive.view import AgreedAction, AgreedActions, month_view
from assetops_backend.structure.attribution.bridge import bridge
from assetops_backend.outcomes.catalogue import CATEGORIES
from assetops_backend.structure.expressions import names as expr_names
from assetops_backend.structure.registry import REGISTRIES
from assetops_backend.structure.targets.read import TargetCheck
from assetops_backend.structure_snapshot.model import Freshness, Served
from test_3a4_commercial_months import new_world

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "5c" / "deep_dive_lakeside_2026-10.json"
MG = REGISTRIES["MINI_GRID"]
AS_OF = t3.AS_OF
NAMES = {"KOBO-001": "Kobo", "KISIWA-001": "Kisiwa", "MTO-001": "Mto"}
NOT_MATCHED = SimpleNamespace(
    reconciled=False, reason="THIS_MONTH_NOT_MATCHED",
    text="Not yet reconciled: October 2026 (the organisation) does not match the management accounts within 1%.",
    details=("Fuel cost (Recorded and Emulated): the accounts say $5,100.00 and the records say $4,995.00, $105.00 "
             "less (2.06%), beyond the $51.00 allowed (1%).",))
RECONCILED = SimpleNamespace(
    reconciled=True, reason="RECONCILED",
    text="Reconciled: October 2026 (the organisation) matches the management accounts within 1%.", details=())
OFF = AgreedActions(False, ())

EMS = ("the EMS interval export (generator running and output, solar available power, battery charge)")
CURVE = "the generator's fuel curve (litres per kWh; litres per hour idle)"
SETUP = "a generator and a fuel tank declared in the Site's setup (litres are worked out for each)"
REVENUE_STOP = ("Not split further until the billing export, a feeder meter export, a meter register with change "
                "dates, the customer meter reads for the month, the expected technical loss of each feeder, declared "
                "in the Site's setup, the productive-use tariff and budget lines for energy delivered, tariff and "
                "productive-use price.")
FUEL_STOP = (f"Not split further until {EMS}, {CURVE}, tank dips at the start and end of the month and fuel delivery "
             "notes.")
THREE_FUEL = ("Diesel not shown to be avoidable, Diesel run while solar and battery could carry the load and "
              "Unexplained fuel")
ALL = "Kobo, Kisiwa and Mto"


# --- worlds -----------------------------------------------------------------------------------------------------

def served_world(*, with_mto: bool = True, thika: bool = False, fb=None, late: bool = False):
    w = t5b.load_lakeside(new_world(), with_mto)
    s = t3.setup(w, fb=fb)
    sites = t3.refs(w) if thika else t3.refs(w)[:3]
    s.builder.build(w["tid"], sites, t3.OCT, built_by=t3.BY)
    at = AS_OF
    if late:
        t3.ingest_late(w)
        at = datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc)
    return t3.reader(s, at=at).portfolio(w["tid"], t3.OCT), at, (w, s)


_CACHE: dict = {}


def world(name: str):
    if name not in _CACHE:
        if name == "H":
            from test_4b_money_leaves import fallback
            from test_4d_litre_split import LakesideInputs
            from assetops_backend.structure.litres.source import LitreLeafSource
            _CACHE[name] = served_world(fb=LitreLeafSource(LakesideInputs(), fallback(), lambda: AS_OF))
        else:
            _CACHE[name] = served_world(with_mto=name != "D", thika=name == "G", late=name == "E")
    return _CACHE[name]


def view(name: str = "A", *, standing=NOT_MATCHED, actions=OFF, names=None, served=None, month="2026-10"):
    sv, at, _ = world(name)
    names = names if names is not None else ({**NAMES, "THIKA-001": "Thika"} if name == "G" else NAMES)
    return month_view(operator="Lakeside Power", month=month, served=served if served is not None else sv,
                      standing=standing, actions=actions, names=names, now=at)


def step(v: dict, key: str) -> dict:
    return next(s for g in v["bridge"]["groups"] for s in g["steps"] if s["key"] == key)


def strings(obj) -> list[str]:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [x for v in obj.values() for x in strings(v)]
    if isinstance(obj, list):
        return [x for v in obj for x in strings(v)]
    return []


# --- test 1: tables ---------------------------------------------------------------------------------------------

def _reachable(root: str) -> set[str]:
    out, todo = set(), [root]
    while todo:
        f = todo.pop()
        if f in out:
            continue
        out.add(f)
        todo.extend(expr_names(MG.parsed[f]) if f in MG.parsed else ())
    return out


def test_1_tables() -> None:
    from assetops_backend.structure.attribution.rules import BRIDGE_ROOTS
    from assetops_backend.structure.energy.rules import NOTES as ENERGY_NOTES
    from assetops_backend.structure.litres.rules import NOTES
    reach = set().union(*(_reachable(r) for r in BRIDGE_ROOTS["MINI_GRID"]))
    assert {f for f in reach if not W.factor_label(f)} == set()
    assert [W.heading_label(c) for c in CATEGORIES] == [
        "Grow revenue", "Optimize cost and efficiency", "Protect asset and capital", "Assure performance and returns"]
    cost = expr_names(MG.parsed["cost_to_serve"])
    # Neutral: an OPTION_ONLY leaf (its observed value is the neutral 0) or a product of one (battery_wear).
    neutral = tuple(t for t in cost if MG.row(t).neutral is not None or any(
        MG.row(f).neutral is not None for f in (expr_names(MG.parsed[t]) if t in MG.parsed else ())))
    assert T.STEPS["MINI_GRID"] == ("revenue", *(t for t in cost if t not in neutral))
    assert set(T.STEPS["MINI_GRID"][1:]) | set(neutral) == set(cost)
    assert "revenue" in expr_names(MG.parsed["contribution"])
    # 4d's notes (spec test 1) and 4a's record notes (D-4A.12/.24); 4a's `PREFIX:detail` reasons are not notes.
    assert (set(NOTES) | {n for n in ENERGY_NOTES if ":" not in n}) - set(T.NOTE_KEYS) == set()


# --- test 2: formats --------------------------------------------------------------------------------------------

def test_2_formats() -> None:
    assert W.amount(D("-852"), "USD", "SIGNED") == "−$852.00"
    assert W.amount(D("38"), "USD", "SIGNED") == "+$38.00"
    assert W.amount(D("38"), "USD") == "$38.00"
    assert W.amount(D("0"), "USD", "SIGNED") == "$0.00"
    assert W.amount(D("0"), "KES", "SIGNED") == "KES 0.00"  # plant P15
    assert W.amount(D("-0.00"), "USD") == "$0.00"
    assert W.amount(D("1234567.891"), "USD", "SIGNED") == "+$1,234,567.89"
    assert W.amount(D("1234567.891"), "USD") == "$1,234,567.89"
    assert W.amount(D("-1234567.891"), "KES") == "−KES 1,234,567.89"
    assert W.detail("QUANTITY", D("1180.000"), D("700"), "USD", "L") == "Actual 1,180 L · Target 700 L"
    assert W.tile_target(W.money(D("2295"), "USD"), D("1443") / D("2295")) == "Target $2,295.00 · 63% of target"
    assert W.tile_target(W.money(D("-65"), "USD"), None) == "Target −$65.00"
    assert W.cost_received(D("0.91510")) == "91.5% of cost from figures received"
    assert W.site_names(["KOBO-001"], NAMES) == "Kobo"
    assert W.site_names(["KOBO-001", "MTO-001"], NAMES) == "Kobo and Mto"
    assert W.site_names(["KOBO-001", "KISIWA-001", "MTO-001"], NAMES) == ALL
    assert W.sites(1, 1) == "1 of 1 Site" and W.sites(3, 4) == "3 of 4 Sites"


# --- test 3: World A --------------------------------------------------------------------------------------------

def test_3_world_a_key_by_key_and_whole() -> None:
    v = view("A")
    assert list(v)[:4] == ["schema", "operator", "month", "month_words"]
    assert (v["schema"], v["month_words"], v["nav"], v["state"]) == (
        "deep-dive-month-1", "October 2026", {"previous": "2026-09", "next": None}, "SERVED")
    assert v["as_of_text"] == "Figures as of 20 November 2026, 08:00 UTC."
    assert v["fresh"] == {"current": True, "text": None, "untracked_text": None}
    assert v["headline"] == {"text": "Contribution is $852.00 below target in October; cost and efficiency explain "
                                      "$755.00 of it.", "evidence": ["Estimated"]}
    assert v["status_line"] == ("Figures as of 20 November 2026, 08:00 UTC. Not yet reconciled with the management "
                                "accounts. Kisiwa's budget disagrees with its own lines.")
    t0, t1, t2, t3_ = v["tiles"]
    assert t0 == {"key": "contribution", "label": "Contribution", "value": "$1,443.00",
                  "word": "Estimated, not yet reconciled",
                  "lines": ["Target $2,295.00 · 63% of target", "3 of 3 Sites", "91.5% of cost from figures received"],
                  "bar": {"actual": "1443.00", "target": "2295.00"}}
    assert (t1["label"], t1["value"], t1["word"], t1["lines"]) == (
        "Gap to target", "−$852.00", "Estimated, not yet reconciled",
        ["Grow −$97.00 · Optimize −$755.00", "$852.00 of it not split to its drivers yet"])
    assert (t2["label"], t2["value"], t2["word"], t2["lines"], t2["bar"]) == (
        "Plan spend", "Not available yet", None, ["No plan has been made yet"], None)
    assert (t3_["label"], t3_["value"], t3_["word"], t3_["lines"]) == (
        "Plan value, 12 months", "Not available yet", None,
        ["Each change is valued against doing nothing when decisions are recorded"])
    assert v["notices"] == ["Kisiwa's budget states a contribution of −$60.00; its budget lines add to −$65.00. The "
                            "target used is −$65.00."]
    b = v["bridge"]
    assert b["title"] == "Cost and efficiency explain $755.00 of the $852.00 gap. Open a step for what is behind it."
    assert b["totals"] == {"actual_label": "Contribution, October", "actual": "$1,443.00", "target_label": "Target",
                           "target": "$2,295.00"}
    assert [(g["label"], g["value"]) for g in b["groups"]] == [("Grow revenue", "−$97.00"),
                                                               ("Optimize cost and efficiency", "−$755.00")]
    assert [(s["key"], s["value"], s["share"], s["word"], s["sites"]) for g in b["groups"] for s in g["steps"]] == [
        ("revenue", "−$97.00", "11% of what widens the gap", "Emulated, not yet reconciled", "3 of 3 Sites"),
        ("fuel_cost", "−$755.00", "89% of what widens the gap", "Emulated, not yet reconciled", "3 of 3 Sites"),
        ("om", "$0.00", "No effect", "Estimated, not yet reconciled", "3 of 3 Sites"),
        ("staff", "$0.00", "No effect", "Emulated, not yet reconciled", "3 of 3 Sites")]
    rev = step(v, "revenue")["drawer"]
    assert rev["lines"] == ["Actual $9,688.00 · Target $9,785.00 · Difference −$97.00",
                            "Effect on contribution −$97.00", "3 of 3 Sites"]
    assert rev["sites"] == [{"site": "Kobo", "value": "+$38.00", "text": REVENUE_STOP},
                            {"site": "Kisiwa", "value": "−$55.00", "text": REVENUE_STOP},
                            {"site": "Mto", "value": "−$80.00", "text": REVENUE_STOP}]
    assert rev["drivers"] == [] and rev["out"] == [] and rev["carried"] == []
    fuel = step(v, "fuel_cost")["drawer"]
    assert fuel["lines"] == ["Actual $4,995.00 · Target $4,240.00 · Difference +$755.00",
                             "Effect on contribution −$755.00", "3 of 3 Sites"]
    assert [(r["site"], r["value"], r["text"]) for r in fuel["sites"]] == [
        ("Kobo", "−$600.00", FUEL_STOP), ("Kisiwa", "−$130.00", FUEL_STOP), ("Mto", "−$25.00", FUEL_STOP)]
    om = step(v, "om")["drawer"]
    assert om["lines"] == ["Actual $1,800.00 · Target $1,800.00 · Difference $0.00", "Effect on contribution $0.00",
                           "3 of 3 Sites"]
    assert [(r["site"], r["value"]) for r in om["sites"]] == [  # review L1: the drawer row reads as the table cell
        ("Kobo", "$0.00"), ("Kisiwa", "$0.00 (estimate)"), ("Mto", "$0.00")]
    assert om["carried"] == ["Kisiwa: no service contractor invoice received; taken at its budget line for the month "
                             "(estimate)."]  # plant P6
    staff = step(v, "staff")["drawer"]
    assert staff["lines"][0] == "Actual $1,450.00 · Target $1,450.00 · Difference $0.00"
    assert staff["lines_org"] == ["The organisation's budget also states $1,200.00 for staff that no Site carries; it "
                                  "is listed, not added."]
    assert b["by_site"]["rows"] == [
        ["Kobo", "$883.00", "$1,445.00", "−$562.00", "+$38.00", "−$600.00", "$0.00", "$0.00"],
        ["Kisiwa", "−$250.00", "−$65.00", "−$185.00", "−$55.00", "−$130.00", "$0.00 (estimate)", "$0.00"],
        ["Mto", "$810.00", "$915.00", "−$105.00", "−$80.00", "−$25.00", "$0.00", "$0.00"]]
    assert b["by_site"]["total"] == ["3 of 3 Sites", "$1,443.00", "$2,295.00", "−$852.00", "−$97.00", "−$755.00",
                                     "$0.00", "$0.00"]
    c = v["cash"]
    assert c["text"] == ("In October, $8,870.00 was collected against $9,785.00 expected; $668.00 is still outstanding "
                         "and $150.00 is paid but in transit.")
    assert (c["word"], c["sites"]) == ("Estimated, not yet reconciled", "3 of 3 Sites")
    assert c["table"]["rows"] == [["Kobo", "$3,458.00", "$3,180.00", "$0.00", "$278.00"],
                                  ["Kisiwa", "$4,070.00", "$3,800.00", "$0.00", "$270.00"],
                                  ["Mto", "$2,160.00", "$1,890.00", "$150.00", "$120.00"]]
    assert c["table"]["total"] == ["3 of 3 Sites", "$9,688.00", "$8,870.00", "$150.00", "$668.00"]
    grow, opt, protect, assure = v["outcomes"]
    assert (grow["value"], grow["word"], grow["line"], grow["drawer"]) == (
        "−$97.00", "Emulated, not yet reconciled", "Revenue against target, 3 of 3 Sites", None)
    assert (opt["value"], opt["word"], opt["drawer"]) == ("−$755.00", "Estimated, not yet reconciled", None)
    assert (protect["value"], protect["word"], protect["drawer"]) == ("Not available yet", None, None)
    assert (assure["value"], assure["word"], assure["line"]) == (
        "Not yet reconciled", None, "1 budget disagreement · 91.5% of cost from figures received")
    assert assure["drawer"] == {"title": "Reconciliation with the management accounts",
                                "lines": [NOT_MATCHED.text, *NOT_MATCHED.details]}
    assert v["actions"] == {"title": "Actions in hand", "connected": False, "text": "Not available yet: an agreed "
                            "change is recorded as an Action with its owner and due date.", "rows": [], "more": 0}
    assert [(r["needs"], r["fills"], r["sites"]) for r in v["not_available"]["rows"]] == [
        ("the billing export", "Billing adjustments, Energy on unmapped meters and Tariff", ALL),
        ("a feeder meter export", "Energy delivered, Technical losses and Unexplained losses", ALL),
        ("a meter register with change dates", "Unexplained losses and Energy on unmapped meters", ALL),
        ("the customer meter reads for the month", "Unexplained losses and Energy on unmapped meters", ALL),
        ("the expected technical loss of each feeder, declared in the Site's setup",
         "Technical losses and Unexplained losses", ALL),
        ("the productive-use tariff", "Productive-use price", ALL),
        (EMS, THREE_FUEL, ALL), (CURVE, THREE_FUEL, ALL),
        ("tank dips at the start and end of the month", "Unexplained fuel", ALL),
        ("fuel delivery notes", "Unexplained fuel", ALL),
        ("the service contractor's invoices", "O&M (taken at its budget line meanwhile)", "Kisiwa"),
        ("budget lines for energy delivered, tariff and productive-use price",
         "Energy delivered, Tariff and Productive-use price", ALL)]
    assert v == json.loads(FIXTURE.read_text(encoding="utf-8"))


# --- test 4: the other worlds -----------------------------------------------------------------------------------

def test_4_a2_a_budget_that_cannot_be_added(monkeypatch) -> None:
    sv, _, _ = world("A")
    snap = sv.snapshot
    kisiwa = snap.sites["KISIWA-001"]
    targets = replace(kisiwa.targets, checks=(TargetCheck("contribution", D("-60.00"), None, "USD", False),))
    served = replace(sv, snapshot=replace(snap, sites={**snap.sites, "KISIWA-001": replace(kisiwa, targets=targets)}))
    v = view(served=served)
    assert v["notices"] == ["Kisiwa's budget states a contribution of −$60.00; its budget lines do not add up to a "
                            "figure yet, so they cannot be compared."]  # plant P17
    assert v["status_line"] == view()["status_line"]


def test_4_b_reconciled() -> None:
    v = view(standing=RECONCILED)
    assert not [s for s in strings(v) if "not yet reconciled" in s]
    assert v["status_line"] == ("Figures as of 20 November 2026, 08:00 UTC. Reconciled with the management accounts. "
                                "Kisiwa's budget disagrees with its own lines.")
    assert v["tiles"][0]["word"] == "Estimated" and step(v, "revenue")["word"] == "Emulated"
    assure = v["outcomes"][3]
    assert (assure["value"], assure["drawer"]["lines"]) == ("Reconciled", [RECONCILED.text])


def _action(i: int, title: str, hour: int, minute: int) -> AgreedAction:
    return AgreedAction(f"A-{i}", title, "KOBO-001", "candidate_l", "Peter", "Amina",
                        datetime(2026, 11, 20, hour, minute, tzinfo=timezone.utc), date(2026, 12, 15), "Open")


def test_4_c_an_agreed_change() -> None:
    title = "Lower the generator stop setting at Kobo to 70% battery charge"
    a = view(actions=AgreedActions(True, (_action(1, title, 9, 30),)))["actions"]
    assert a == {"title": "Actions in hand", "connected": True, "text": None, "more": 0, "rows": [
        {"title": title, "owner": "Owner Peter · due 15 December 2026", "agreed": "Agreed by Amina on 20 November 2026",
         "state": "Open"}]}
    empty = view(actions=AgreedActions(True, ()))["actions"]
    assert (empty["text"], empty["rows"], empty["more"]) == ("No change has been agreed yet.", [], 0)
    four = AgreedActions(True, tuple(_action(i, f"Change {i}", h, m)
                                     for i, h, m in ((4, 11, 0), (3, 10, 30), (2, 10, 0), (1, 9, 30))))
    c4 = view(actions=four)["actions"]  # plant P16
    assert [r["title"] for r in c4["rows"]] == ["Change 4", "Change 3", "Change 2"] and c4["more"] == 1


def test_4_d_mto_records_missing() -> None:
    v = view("D")
    assert v["headline"]["text"] == ("Contribution is $747.00 below target in October; cost and efficiency explain "
                                     "$730.00 of it. Compared for 2 of 3 Sites.")
    assert (v["tiles"][0]["value"], v["tiles"][0]["lines"]) == (
        "$633.00", ["Target $1,380.00 · 46% of target", "2 of 3 Sites", "89.8% of cost from figures received"])
    assert v["tiles"][1]["lines"] == ["Grow −$17.00 · Optimize −$730.00", "$747.00 of it not split to its drivers yet"]
    out = step(v, "revenue")["drawer"]["out"]
    assert len(out) == 1 and out[0].startswith("Mto: not compared until the billing export")
    assert out[0].endswith("; its own target is $915.00.")
    mto = v["bridge"]["by_site"]["rows"][2]
    assert mto == ["Mto", "Not available yet", "$915.00", *["Not compared"] * 5]


def test_4_e_out_of_date() -> None:
    v, a = view("E"), view("A")
    assert v["fresh"] == {"current": False, "untracked_text": None, "text": (
        "These figures are out of date: records have arrived since they were prepared for Kisiwa. They are shown as "
        "they were on 20 November 2026, 08:00 UTC.")}
    assert {k: x for k, x in v.items() if k not in ("fresh", "nav")} == {k: x for k, x in a.items()
                                                                          if k not in ("fresh", "nav")}


def test_4_f_no_snapshot_and_rebuild() -> None:
    sv, _, (w, s) = world("A")
    none = t3.reader(s).portfolio(w["tid"], "2026-09")
    v = view(served=none, month="2026-09")
    assert v == {"schema": "deep-dive-month-1", "operator": "Lakeside Power", "month": "2026-09",
                 "month_words": "September 2026", "nav": {"previous": "2026-08", "next": "2026-10"},
                 "state": "NO_SNAPSHOT", "state_text": "The figures for September 2026 have not been prepared yet."}
    rebuild = Served("REBUILD_NEEDED", None, AS_OF, Freshness(False, ("FORMAT",), (), (), ()))
    r = view(served=rebuild)
    assert (r["state"], r["state_text"]) == (
        "REBUILD_NEEDED", "The figures for October 2026 must be prepared again before they can be shown.")
    assert "tiles" not in r


def test_4_g_another_type_asked() -> None:
    v, a = view("G"), view("A")
    assert v["headline"]["text"] == a["headline"]["text"] + " Compared for 3 of 4 Sites."  # plant P2
    assert v["tiles"][0]["lines"][1] == "3 of 4 Sites"
    for g in v["bridge"]["groups"]:
        for s in g["steps"]:
            assert s["sites"] == "3 of 4 Sites" and s["drawer"]["out"] == ["Thika: not a mini-grid Site, not included."]
    assert [r[0] for r in v["bridge"]["by_site"]["rows"]] == ["Kobo", "Kisiwa", "Mto"]


def test_4_h_kobo_litres() -> None:
    v, a = view("H"), view("A")
    assert v["tiles"][1]["lines"][1] == "$252.00 of it not split to its drivers yet"
    fuel = step(v, "fuel_cost")["drawer"]
    stop = (f"Not split further until {EMS}, {CURVE}, tank dips at the start and end of the month, fuel delivery notes "
            f"and {SETUP}.")
    assert [(r["site"], r["value"], r["text"]) for r in fuel["sites"]] == [
        ("Kobo", "−$600.00", None), ("Kisiwa", "−$130.00", stop), ("Mto", "−$25.00", stop)]
    assert fuel["drivers"] == [  # plant P13
        {"label": "Diesel used", "value": "−$600.00", "sites": "1 of 3 Sites", "detail": "Actual 1,180 L · Target 700 L",
         "word": "Modelled, not yet reconciled"},
        {"label": "Diesel not shown to be avoidable", "value": "−$37.50", "sites": "1 of 3 Sites",
         "detail": "Actual 730 L · Target 700 L", "word": "Modelled, not yet reconciled"},
        {"label": "Diesel run while solar and battery could carry the load", "value": "−$412.50", "sites": "1 of 3 Sites",
         "detail": "Actual 330 L · Target 0 L", "word": "Modelled, not yet reconciled"},
        {"label": "Unexplained fuel", "value": "−$150.00", "sites": "1 of 3 Sites", "detail": "Actual 120 L · Target 0 L",
         "word": "Modelled, not yet reconciled"},
        # Known deviation KD1: a price does not sum across Sites (composes NONE), so the portfolio row has no actual
        # or target and section 3.2's rule ("detail when both are present") gives null; its effect is the Modelled
        # litres times the price difference, so its word is Modelled (spec 3.5 H's literal said Emulated).
        {"label": "Diesel price", "value": "$0.00", "sites": "1 of 3 Sites", "detail": None,
         "word": "Modelled, not yet reconciled"}]
    untracked = ("Not checked for later changes: Diesel not shown to be avoidable (Kobo), Diesel run while solar and "
                 "battery could carry the load (Kobo) and Unexplained fuel (Kobo).")
    assert v["fresh"]["untracked_text"] == untracked
    assert v["outcomes"][3]["drawer"]["lines"] == [NOT_MATCHED.text, *NOT_MATCHED.details, untracked]
    rows = {r["needs"]: (r["fills"], r["sites"]) for r in v["not_available"]["rows"]}
    for needs in (EMS, CURVE, "tank dips at the start and end of the month", "fuel delivery notes"):
        assert rows[needs][1] == "Kisiwa and Mto"
    order = [r["needs"] for r in v["not_available"]["rows"]]
    assert order[order.index("the service contractor's invoices") + 1] == SETUP
    assert rows[SETUP] == (THREE_FUEL, "Kisiwa and Mto")
    same = ("headline", "status_line", "notices", "cash", "actions", "decisions", "standing")
    assert {k: v[k] for k in same} == {k: a[k] for k in same}


# --- test 4 i: nothing compared (review H1; owner rule "missing is Not available yet, never 0") -----------------

def _paths(obj, path=""):
    """Every string of the payload with its path."""
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, x in obj.items():
            yield from _paths(x, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, x in enumerate(obj):
            yield from _paths(x, f"{path}[{i}]")


def test_4_i_nothing_compared(monkeypatch) -> None:  # review H1
    """Mto keeps its records in KES (both sides), Kobo and Kisiwa in USD: no portfolio row sums, so R has no effect
    (the designed `headline_na` state). A missing figure is never printed as 0; a line with no figure is left out."""
    real = V.site_bridge

    def in_kes(row):
        return replace(row, currency="KES" if row.currency is not None else None,
                       rows=tuple(in_kes(c) for c in row.rows))

    def site_bridge(inputs, targets):
        sb = real(inputs, targets)
        return replace(sb, roots={k: in_kes(r) for k, r in sb.roots.items()}) if sb.site_code == "MTO-001" else sb
    monkeypatch.setattr(V, "site_bridge", site_bridge)
    v = view()
    assert v["headline"] == {"text": "Contribution for October is not available yet.", "evidence": []}
    gap = v["tiles"][1]
    assert (gap["value"], gap["word"], gap["lines"]) == ("Not available yet", "Not available yet", [])
    b = v["bridge"]
    assert b["title"] is None
    assert [(g["label"], g["value"]) for g in b["groups"]] == [("Grow revenue", "Not available yet"),
                                                               ("Optimize cost and efficiency", "Not available yet")]
    for g in b["groups"]:
        for s in g["steps"]:
            assert s["value"] == "Not available yet"
            assert s["drawer"]["lines"] == ["3 of 3 Sites"], s["key"]
    grow, opt = v["outcomes"][:2]
    assert (grow["value"], grow["word"]) == (opt["value"], opt["word"]) == ("Not available yet", "Not available yet")
    assert b["by_site"]["total"][3:] == ["Not available yet"] * 5
    # The only zeros left are Sites' own figures (each Site's own row compares in its own currency).
    own = (".bridge.by_site.rows[", ".cash.table.rows[")
    zeros = [p for p, s in _paths(v) if "$0.00" in s]
    assert zeros and all(p.startswith(own) or ".drawer.sites[" in p for p in zeros), zeros
    # A residual with no figure is left out of the stops (`effect or 0` printed "$0.00").
    side, absent, stated = t5b.side, t5b._absent, t5b.stated
    gone = {"delivered_kwh": absent("delivered_kwh", "NOT_RECEIVED")}
    a = side("actual", stated={"revenue": stated("3458.00")}, **gone)
    t = side("target", stated={"revenue": stated("3420.00", "DECLARED")}, **gone)
    row, _ = _stop(a, t, "revenue")
    res = next(r for r in V.lowest(row) if r.kind == "RESIDUAL")
    v7 = V._View.__new__(V._View)
    v7.cur = "USD"
    v7.sb = {"KOBO-001": SimpleNamespace(actual=SimpleNamespace(values=a),
                                         targets=SimpleNamespace(structure=SimpleNamespace(values=t)))}
    assert v7.stop("KOBO-001", res) is not None
    assert v7.stop("KOBO-001", replace(res, effect=None)) is None


LEAD = [  # (gap, grow, optimize, headline, title)
    ("-100.00", "200.00", "-300.00", "Contribution is $100.00 below target in October; cost and efficiency explain "
     "$300.00, more than the whole gap.", "Cost and efficiency explain $300.00, more than the whole $100.00 gap. Open "
     "a step for what is behind it."),
    ("-100.00", "-120.00", "20.00", "Contribution is $100.00 below target in October; Grow revenue explains $120.00, "
     "more than the whole gap.", None),
    ("-10.00", "0.00", "0.00", "Contribution is $10.00 below target in October.",
     "The $10.00 gap, by heading. Open a step for what is behind it."),
    ("50.00", "30.00", "20.00", "Contribution is $50.00 above target in October; Grow revenue explains $30.00 of it.",
     None),
    # L5 (added; spec L1 to L4 never put the larger heading on the other sign, so plant P14 survived them): Grow
    # +500.00 narrows a -100.00 gap and is the larger; only Optimize widens it.
    ("-100.00", "500.00", "-50.00", "Contribution is $100.00 below target in October; cost and efficiency explain "
     "$50.00 of it.", "Cost and efficiency explain $50.00 of the $100.00 gap. Open a step for what is behind it."),
]


@pytest.mark.parametrize(("gap", "grow", "opt", "head", "title"), LEAD)
def test_4_lead_vectors(gap, grow, opt, head, title) -> None:  # plant P14
    subject, big = W.named(D(gap), D(grow), D(opt))
    g, b = W.money(D(gap), "USD"), (W.money(big, "USD") if big is not None else None)
    assert W.headline(g, b, subject, "2026-10", 3, 3)["text"] == head
    if title is not None:
        assert W.bridge_title(g, b, subject) == title
    assert W.tile_rest(W.money(D("40.00"), "USD"), W.money(D("-100.00"), "USD")) == (
        "$40.00 not split to its drivers yet, offsetting the gap")


# --- test 5: words ----------------------------------------------------------------------------------------------

WORDS = [  # (evidence, origins, word)
    ("NOT_AVAILABLE", (), "Not available yet"), ("ESTIMATED", ("observed-financial",), "Estimated"),
    ("MODELLED", ("field-integrated",), "Modelled"), ("RECORDED", ("source-emulated",), "Emulated"),
    ("MEASURED", ("demo-simulated",), "Simulated"), ("RECORDED", ("unknown",), "Estimated"),
    ("RECORDED", (), "Estimated"), ("RECORDED", ("observed-financial",), "Recorded"),
    ("DECLARED", ("field-integrated",), "Recorded"), ("MEASURED", ("bench-tested",), "Measured"),
    ("DERIVED", ("observed-financial",), "Calculated"), ("RECORDED", ("observed-financial", "source-emulated"),
                                                         "Emulated"),  # plant P9
]


@pytest.mark.parametrize(("ev", "origins", "expected"), WORDS)
def test_5_words(ev, origins, expected) -> None:
    assert W.word(ev, origins, RECONCILED, "USD") == expected
    suffixed = expected if expected == "Not available yet" else f"{expected}, not yet reconciled"  # plant P4
    assert W.word(ev, origins, NOT_MATCHED, "USD") == suffixed
    assert "Verified" not in (W.word(ev, origins, RECONCILED, "USD"), suffixed)


# --- test 6: one contribution -----------------------------------------------------------------------------------

def test_6_one_contribution(monkeypatch) -> None:
    a, d = view("A"), view("D")
    assert not [s for s in strings(a) if "$1,693.00" in s]  # plant P1
    picked = {k: d[k] for k in ("tiles", "headline", "outcomes")} | {"totals": d["bridge"]["totals"]}
    assert not [s for s in strings(picked) if "$883.00" in s]
    assert a["tiles"][0]["value"] == a["bridge"]["totals"]["actual"] == "$1,443.00"
    assert d["tiles"][0]["value"] == d["bridge"]["totals"]["actual"] == "$633.00"
    sv, _, _ = world("A")
    cls = type(sv.snapshot)

    def boom(*_a, **_k):
        raise AssertionError("month_view read the uncarried composition")
    monkeypatch.setattr(cls, "actual", boom)
    monkeypatch.setattr(cls, "targets", boom)
    _CACHE.pop("A_spy", None)
    assert view(served=sv) == a


# --- test 7: stops ----------------------------------------------------------------------------------------------

def _stop(a, t, root: str):
    row = bridge(MG, a, t, root)
    v = V._View.__new__(V._View)
    v.cur = "USD"
    v.sb = {"KOBO-001": SimpleNamespace(actual=SimpleNamespace(values=a),
                                        targets=SimpleNamespace(structure=SimpleNamespace(values=t)))}
    return row, v.stops("KOBO-001", row)


def test_7_stops_name_their_records() -> None:  # plant P11
    side, absent, stated = t5b.side, t5b._absent, t5b.stated
    gone = {"delivered_kwh": absent("delivered_kwh", "NOT_RECEIVED")}
    row, s = _stop(side("actual", stated={"revenue": stated("3458.00")}, **gone),
                   side("target", stated={"revenue": stated("3420.00", "DECLARED")}, **gone), "revenue")
    assert s == ["The rest of revenue: +$38.00. Not split further until a feeder meter export and a budget line for "
                 "energy delivered."]
    gone = {f: absent(f, "NOT_RECEIVED") for f in ("delivered_kwh", "productive_tariff")}
    row, s = _stop(side("actual", stated={"revenue": stated("3458.00")}, **gone),
                   side("target", stated={"revenue": stated("3420.00", "DECLARED")}, **gone), "revenue")
    assert row.reason == "DETAIL_NOT_AVAILABLE"
    assert s == ["Not split further until a feeder meter export, the productive-use tariff and budget lines for energy "
                 "delivered and productive-use price."]
    row, s = _stop(side("actual", stated={"revenue": stated("3500.00")}), side("target"), "revenue")
    assert row.reason == "RECORD_AND_FACTORS_DIFFER"
    assert s == ["Not split further: the records state $3,500.00 and its parts add to $3,458.00, $42.00 apart."]
    row, s = _stop(side("actual", om=absent("om", "NOT_RECEIVED")), side("target"), "contribution")
    assert row.reason == "GAP_NOT_AVAILABLE"
    assert s == ["Not compared until the service contractor's invoices."]
    row, s = _stop(side("actual"), side("target", currency="KES"), "contribution")
    assert s == ["Not compared: the actual and the target are in different currencies (KES and USD)."]
    assert W.stop_text("NO_RULE", (), ()) == "Not split further: no rule splits it exactly yet."
    for reason in ("RULE_NOT_DECLARED", "PRICE_NOT_DECLARED", "SPLIT_INEXACT"):
        assert reason in T.NO_RULE


# --- the statements (D-SC1.28): every variant has a hand-written case that renders exactly --------------------------

from statement_cases import deep_dive as dd_cases  # noqa: E402
from statement_cases import worked  # noqa: E402


@pytest.mark.parametrize("case", dd_cases.CASES, ids=lambda c: f"{c.key}-{c.variant}")
def test_every_deep_dive_case_renders_exactly(case) -> None:
    from assetops_backend.i18n import message, render
    from assetops_backend.i18n import served as served_words
    from assetops_backend.i18n.render import _render
    msg = message(case.key, **case.facts)
    if case.evidence is None:
        assert render(msg) == case.english
    else:
        assert served_words(msg) == {"text": case.english, "evidence": case.evidence}
    trace: list = []
    _render(msg, None, case.evidence is not None, trace)
    assert trace[0] == (case.key, case.variant)


def test_every_deep_dive_variant_has_a_case() -> None:
    from assetops_backend.i18n.statements.en.deep_dive import STATEMENTS
    have = {(c.key, c.variant) for c in (*dd_cases.CASES, *worked.CASES)}
    # Parts (`part_only`) are rendered inside the statements that carry them (the cases' docstring).
    parts = {slot.get("key") for s in STATEMENTS.values() for slot in s.get("slots", {}).values()
             if isinstance(slot, dict) and slot.get("type") == "part"}
    want = {(k, v["id"]) for k, s in STATEMENTS.items() if not s.get("part_only") and k not in parts
            for v in s["variants"]}
    assert want - have == set()
