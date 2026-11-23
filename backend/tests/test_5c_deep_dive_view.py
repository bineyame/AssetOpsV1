"""5c unit 1 (spec sections 2, 3 and 6, tests 1 to 7): the month's deep-dive view, pure, over 3B7a's served snapshot.

Every English literal below is written by hand from spec section 3.5, changed only by the rules the packet lists
(PF2/D-4A.12 records, PF5 "when", PF8 headline object, D-3A7.16 standing details). Worlds are 5b section 5.2's
(3A4 `new_world()`, 4b's money fixture, 5a's steps 1 and 2, 5b's Mto step), built and served by 3B7a in memory.
"""
from __future__ import annotations

import json
import re
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
from assetops_backend.structure.attribution.portfolio import PortfolioRow
from assetops_backend.outcomes.catalogue import CATEGORIES
from assetops_backend.structure.expressions import names as expr_names
from assetops_backend.structure.registry import REGISTRIES
from assetops_backend.structure.targets.read import TargetCheck
from assetops_backend.structure_snapshot.model import Freshness, Served
from test_3a4_commercial_months import new_world
from pack_litres import with_litres
from deep_dive_worlds import gone, in_kes, world_h, world_x

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "5c" / "deep_dive_lakeside_2026-10.json"
MG = REGISTRIES["MINI_GRID"]
AS_OF = t3.AS_OF
NAMES = {"KOBO-001": "Kobo", "KISIWA-001": "Kisiwa", "MTO-001": "Mto"}
NOT_MATCHED = SimpleNamespace(
    reconciled=False, reason="THIS_MONTH_NOT_MATCHED",
    text="Not yet reconciled: October 2026 (the organisation) does not match the management accounts within 1%.",
    details=("Fuel cost (Recorded and Emulated): the accounts say $2,100.00 and the records say $2,006.40, $93.60 "
             "less (4.46%), beyond the $21.00 allowed (1%).",))  # re-pinned 2026-11-23 with the records (M rev 16.23)
RECONCILED = SimpleNamespace(
    reconciled=True, reason="RECONCILED",
    text="Reconciled: October 2026 (the organisation) matches the management accounts within 1%.", details=())
OFF = AgreedActions(False, ())

EMS = ("the EMS interval export (generator running and output, solar available power, battery charge)")
CURVE = "the generator's fuel curve (litres per kWh; litres per hour idle)"
SETUP = "a generator and a fuel tank declared in the Site's setup (litres are worked out for each)"
BILLING = "the billing export with each line's kWh and tariff"  # D-5C.25
LOSS_BAND = "each feeder's expected technical loss as declared in the Site's setup"  # D-5C.25
REVENUE_STOP = (f"Not split further until {BILLING}, a feeder meter export, a meter register with change dates, the "
                f"customer meter reads for the month, {LOSS_BAND}, the productive-use tariff and budget lines for "
                "energy delivered, tariff and productive-use price.")
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
    assert v["headline"] == {"text": "Contribution is $2,136.60 above target in October; cost and efficiency explain "
                                      "$2,233.60, more than the whole gap.", "evidence": ["Estimated, not yet reconciled"]}  # D-5C.20
    assert v["status_line"] == ("Figures as of 20 November 2026, 08:00 UTC. Not yet reconciled with the management "
                                "accounts. Kisiwa's budget disagrees with its own lines.")
    t0, t1, t2, t3_ = v["tiles"]
    assert t0 == {"key": "contribution", "label": "Contribution", "value": "$4,431.60",
                  "word": "Estimated, not yet reconciled",
                  "lines": ["Target $2,295.00 · 193% of target", "3 of 3 Sites", "86.7% of cost from figures received"],
                  "bar": {"actual": "4431.60", "target": "2295.00"}}
    assert (t1["label"], t1["value"], t1["word"], t1["lines"]) == (
        "Gap to target", "+$2,136.60", "Estimated, not yet reconciled",
        ["Grow −$97.00 · Optimize +$2,233.60", "$2,136.60 of it not split to its drivers yet"])
    assert (t2["label"], t2["value"], t2["word"], t2["lines"], t2["bar"]) == (
        "Plan spend", "Not available yet", None, ["No plan has been made yet"], None)
    assert (t3_["label"], t3_["value"], t3_["word"], t3_["lines"]) == (
        "Plan value, 12 months", "Not available yet", None,
        ["Each change is valued against doing nothing when decisions are recorded"])
    assert v["notices"] == ["Kisiwa's budget states a contribution of −$60.00; its budget lines add to −$65.00. The "
                            "target used is −$65.00."]
    b = v["bridge"]
    assert b["title"] == "Cost and efficiency explain $2,233.60, more than the whole $2,136.60 gap. Open a step for what is behind it."
    assert b["totals"] == {"actual_label": "Contribution, October", "actual": "$4,431.60", "target_label": "Target",
                           "target": "$2,295.00"}
    assert [(g["label"], g["value"]) for g in b["groups"]] == [("Grow revenue", "−$97.00"),
                                                               ("Optimize cost and efficiency", "+$2,233.60")]
    assert [(s["key"], s["value"], s["share"], s["word"], s["sites"]) for g in b["groups"] for s in g["steps"]] == [
        ("revenue", "−$97.00", "Offsets it", "Emulated, not yet reconciled", "3 of 3 Sites"),
        ("fuel_cost", "+$2,233.60", "100% of what widens the gap", "Emulated, not yet reconciled", "3 of 3 Sites"),
        ("om", "$0.00", "No effect", "Estimated, not yet reconciled", "3 of 3 Sites"),
        ("staff", "$0.00", "No effect", "Emulated, not yet reconciled", "3 of 3 Sites")]
    # Rev 4 (D-5C.27): each step's bar on the gap's scale, served as track percentages (97 / 2,233.60 = 4.34 %: the bars share the largest effect's scale).
    assert list(b) == ["title", "totals", "scale", "groups", "by_site"]
    assert list(step(v, "revenue")) == ["key", "label", "value", "share", "word", "sites", "bar", "drawer"]
    assert b["scale"] == A_SCALE
    assert {s["key"]: s["bar"] for g in b["groups"] for s in g["steps"]} == A_BARS
    rev = step(v, "revenue")["drawer"]
    assert rev["lines"] == ["Actual $9,688.00 · Target $9,785.00 · Difference −$97.00",
                            "Effect on contribution −$97.00", "3 of 3 Sites"]
    assert rev["sites"] == [{"site": "Kobo", "value": "+$38.00", "text": REVENUE_STOP},
                            {"site": "Kisiwa", "value": "−$55.00", "text": REVENUE_STOP},
                            {"site": "Mto", "value": "−$80.00", "text": REVENUE_STOP}]
    assert rev["drivers"] == [] and rev["out"] == [] and rev["carried"] == []
    fuel = step(v, "fuel_cost")["drawer"]
    assert fuel["lines"] == ["Actual $2,006.40 · Target $4,240.00 · Difference −$2,233.60",
                             "Effect on contribution +$2,233.60", "3 of 3 Sites"]
    assert [(r["site"], r["value"], r["text"]) for r in fuel["sites"]] == [
        ("Kobo", "+$82.50", FUEL_STOP), ("Kisiwa", "+$1,816.10", FUEL_STOP), ("Mto", "+$335.00", FUEL_STOP)]
    om = step(v, "om")["drawer"]
    assert om["lines"] == ["Actual $1,800.00 · Target $1,800.00 · Difference $0.00", "Effect on contribution $0.00",
                           "3 of 3 Sites"]
    assert [(r["site"], r["value"]) for r in om["sites"]] == [  # D-5C.23 (L1): the drawer row reads as the table cell
        ("Kobo", "$0.00"), ("Kisiwa", "$0.00 (at budget)"), ("Mto", "$0.00")]
    assert om["carried"] == ["Kisiwa: no service contractor invoice received; taken at its budget line for the month "
                             "(estimate)."]  # plant P6
    staff = step(v, "staff")["drawer"]
    assert staff["lines"][0] == "Actual $1,450.00 · Target $1,450.00 · Difference $0.00"
    assert staff["lines_org"] == ["The organisation's budget also states $1,200.00 for staff that no Site carries; it "
                                  "is listed, not added."]
    assert b["by_site"]["rows"] == [
        ["Kobo", "$1,565.50", "$1,445.00", "+$120.50", "+$38.00", "+$82.50", "$0.00", "$0.00"],
        ["Kisiwa", "$1,696.10", "−$65.00", "+$1,761.10", "−$55.00", "+$1,816.10", "$0.00 (at budget)", "$0.00"],
        ["Mto", "$1,170.00", "$915.00", "+$255.00", "−$80.00", "+$335.00", "$0.00", "$0.00"]]
    assert b["by_site"]["total"] == ["3 of 3 Sites", "$4,431.60", "$2,295.00", "+$2,136.60", "−$97.00", "+$2,233.60",
                                     "$0.00", "$0.00"]
    c = v["cash"]
    assert c["text"] == ("Of $9,688.00 billed for October, $8,870.00 has been collected, $150.00 is paid but in "
                         "transit and $668.00 is still outstanding.")
    assert (c["word"], c["sites"]) == ("Estimated, not yet reconciled", "3 of 3 Sites")
    assert c["table"]["rows"] == [["Kobo", "$3,458.00", "$3,180.00", "$0.00", "$278.00"],
                                  ["Kisiwa", "$4,070.00", "$3,800.00", "$0.00", "$270.00"],
                                  ["Mto", "$2,160.00", "$1,890.00", "$150.00", "$120.00"]]
    assert c["table"]["total"] == ["3 of 3 Sites", "$9,688.00", "$8,870.00", "$150.00", "$668.00"]
    grow, opt, protect, assure = v["outcomes"]
    assert (grow["value"], grow["word"], grow["line"], grow["drawer"]) == (
        "−$97.00", "Emulated, not yet reconciled", "Revenue against target, 3 of 3 Sites", None)
    assert (opt["value"], opt["word"], opt["drawer"]) == ("+$2,233.60", "Estimated, not yet reconciled", None)
    assert (protect["value"], protect["word"], protect["drawer"]) == ("Not available yet", None, None)
    assert (assure["value"], assure["word"], assure["line"]) == (
        "Not yet reconciled", None, "1 budget disagreement · 86.7% of cost from figures received")
    assert assure["drawer"] == {"title": "Reconciliation with the management accounts",
                                "lines": [NOT_MATCHED.text, *NOT_MATCHED.details]}
    assert v["actions"] == {"title": "Actions in hand", "connected": False, "text": "Not available yet: an agreed "
                            "change is recorded as an Action with its owner and due date.", "rows": [], "more": 0}
    assert [(r["needs"], r["fills"], r["sites"]) for r in v["not_available"]["rows"]] == [
        (BILLING, "Billing adjustments, Energy on unmapped meters and Tariff", ALL),
        ("a feeder meter export", "Energy delivered, Technical losses and Unexplained losses", ALL),
        ("a meter register with change dates", "Unexplained losses and Energy on unmapped meters", ALL),
        ("the customer meter reads for the month", "Unexplained losses and Energy on unmapped meters", ALL),
        (LOSS_BAND, "Technical losses and Unexplained losses", ALL),
        ("the productive-use tariff", "Productive-use price", ALL),
        (EMS, THREE_FUEL, ALL), (CURVE, THREE_FUEL, ALL),
        ("tank dips at the start and end of the month", "Unexplained fuel", ALL),
        ("fuel delivery notes", "Unexplained fuel", ALL),
        ("the service contractor's invoices", "O&M (taken at its budget line meanwhile)", "Kisiwa"),
        ("budget lines for energy delivered, tariff and productive-use price",
         "Energy delivered, Tariff and Productive-use price", ALL)]
    # D-5C.22 (L3): lists bounded by the Sites asked ship whole; the screen caps them. Only Actions has `more`.
    assert "more" not in b["by_site"] and "more" not in v["not_available"]
    assert all(set(s) == {"site", "value", "text"} for g in b["groups"] for st in g["steps"]
               for s in st["drawer"]["sites"])
    assert v == json.loads(FIXTURE.read_text(encoding="utf-8"))


#: D-DD.150-152 / D-DD.164 (2026-11-23, M rev 16.20/16.23): World A's figures moved with the 5b fixtures (re-pinned, b).
#: Rev 4 (D-5C.27): World A's step bars and scale (spec section 3.5); O&M and staff have effect 0, so no bar.
A_BARS = {"revenue": {"left": "0.00", "width": "4.34", "tone": "lowers"},
          "fuel_cost": {"left": "0.00", "width": "100.00", "tone": "raises"}, "om": None, "staff": None}
A_SCALE = {"target_at": "4.34", "actual_at": "100.00"}


# --- test 3 (class form, D-5C.20): the headline's evidence is the payload's own word for each figure it states ----

def _lead_world(monkeypatch, gap: str, grow: str, opt: str) -> None:
    """World A's portfolio with R's, revenue's and fuel cost's effects set to a lead vector (O&M and staff 0)."""
    real = V.portfolio_bridge
    effects = {T.ROOT: gap, T.REVENUE: grow, "fuel_cost": opt, "om": "0.00", "staff": "0.00"}

    def portfolio_bridge(*args, **kwargs):
        pb = real(*args, **kwargs)
        rows = dict(pb.rows[T.ROOT])
        for key, value in effects.items():
            rows[key] = replace(rows[key], effect=D(value))
        return replace(pb, rows={**pb.rows, T.ROOT: rows})
    monkeypatch.setattr(V, "portfolio_bridge", portfolio_bridge)


@pytest.mark.parametrize("case", ["A", "B", "D", "L1", "L2", "L3", "L4"])
def test_3_headline_evidence_is_the_figures_words(case, monkeypatch) -> None:  # plant P22
    if case.startswith("L"):
        gap, grow, opt = LEAD[int(case[1]) - 1][:3]
        _lead_world(monkeypatch, gap, grow, opt)
    v = view("D" if case == "D" else "A", standing=RECONCILED if case == "B" else NOT_MATCHED)
    want = {v["tiles"][1]["word"]}
    text = v["headline"]["text"]
    if case.startswith("L"):
        assert text == LEAD[int(case[1]) - 1][3]
    named = {"cost and efficiency explain": 1, "Grow revenue explains": 0}
    for phrase, card in named.items():
        if phrase in text:
            want.add(v["outcomes"][card]["word"])
    assert set(v["headline"]["evidence"]) == want
    if case == "L2":  # Grow named: R's word and Grow's (Emulated) differ, so both are served
        assert want == {"Estimated, not yet reconciled", "Emulated, not yet reconciled"}


# --- DD3d.4: served money is whole cents (fuel cost is litres to the millilitre times a price) --------------------------

#: A figure's digits, as served: no money figure carries more than two places (a price per unit may carry four).
LONG_MONEY = re.compile(r"(?:[$€£]|[A-Z]{3} )[\d,]+\.\d{3,}(?! per )")


def world_c():
    """World A with Kobo's 634 L replaced by 739.383 L, so its fuel cost is 924.22875 and the portfolio's 2,138.12875."""
    if "C" not in _CACHE:
        litres = {"KOBO-001": {"necessary_l": D("739.383"), "candidate_l": D(0), "unexplained_l": D(0)}}
        _CACHE["C"] = served_world(fb=with_litres(litres=litres))
    return _CACHE["C"]


def test_served_money_is_whole_cents() -> None:
    sv, _, _ = world_c()
    fuel = sv.snapshot.sites["KOBO-001"].actual.values["fuel_cost"].value
    assert fuel == D("924.22875") and len(format(fuel, "f").split(".")[1]) > 2  # the stored value stays exact
    v = view("C", served=sv)
    assert v["tiles"][0]["value"] == "$4,299.87"
    assert v["tiles"][0]["bar"] == {"actual": "4299.87", "target": "2295.00"}
    assert [(r["site"], r["value"]) for r in step(v, "fuel_cost")["drawer"]["sites"]] == [
        ("Kobo", "−$49.23"), ("Kisiwa", "+$1,816.10"), ("Mto", "+$335.00")]
    assert step(v, "fuel_cost")["drawer"]["lines"][0] == ("Actual $2,138.13 · Target $4,240.00 · "
                                                          "Difference −$2,101.87")
    assert v["bridge"]["by_site"]["rows"][0][:3] == ["Kobo", "$1,433.77", "$1,445.00"]
    for payload in (v, view("A")):
        assert [x for x in strings(payload) if LONG_MONEY.search(x)] == []
        assert all(len(x.partition(".")[2]) == 2 for x in payload["tiles"][0]["bar"].values())


@pytest.mark.parametrize("value,text", [
    ("1565.500", "1565.50"), ("924.2285", "924.23"), ("924.225", "924.22"), ("924.235", "924.24"), ("-0.004", "0.00"),
    ("2295", "2295.00"), ("-65.00", "-65.00"), ("1234567.125", "1234567.12")])
def test_bar_text_is_moneys_rule(value: str, text: str) -> None:
    """The bar's plain decimals round as `deep_dive.money` does (cents, half-even), so the two never disagree."""
    assert W.plain(D(value)) == text
    shown = W.amount(D(value), "USD")
    if D(text) != 0:
        assert shown.replace("$", "").replace(",", "").replace("−", "-") == text


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
    assert v["headline"]["evidence"] == ["Estimated"]  # D-5C.20
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
    assert v["headline"]["text"] == ("Contribution is $1,881.60 above target in October; cost and efficiency explain "
                                     "$1,898.60, more than the whole gap. Compared for 2 of 3 Sites.")
    assert (v["tiles"][0]["value"], v["tiles"][0]["lines"]) == (
        "$3,261.60", ["Target $1,380.00 · 236% of target", "2 of 3 Sites", "83.6% of cost from figures received"])
    assert v["tiles"][1]["lines"] == ["Grow −$17.00 · Optimize +$1,898.60", "$1,881.60 of it not split to its drivers yet"]
    out = step(v, "revenue")["drawer"]["out"]
    assert len(out) == 1 and out[0].startswith(f"Mto: not compared until {BILLING}, ")
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
    assert v["tiles"][1]["lines"][1] == "$2,054.10 of it not split to its drivers yet"
    fuel = step(v, "fuel_cost")["drawer"]
    stop = (f"Not split further until {EMS}, {CURVE}, tank dips at the start and end of the month, fuel delivery notes "
            f"and {SETUP}.")
    assert [(r["site"], r["value"], r["text"]) for r in fuel["sites"]] == [
        ("Kobo", "+$82.50", None), ("Kisiwa", "+$1,816.10", stop), ("Mto", "+$335.00", stop)]
    word = "Modelled, not yet reconciled"
    assert fuel["drivers"] == [  # plants P13, P24 (D-5C.21: nested; a flattened list fails)
        {"key": "diesel_l", "label": "Diesel used", "value": "+$82.50", "sites": "1 of 3 Sites",
         "detail": "Actual 634 L · Target 700 L", "word": word, "children": [
             {"key": "necessary_l", "label": "Diesel not shown to be avoidable", "value": "+$375.00",
              "sites": "1 of 3 Sites", "detail": "Actual 400 L · Target 700 L", "word": word, "children": []},
             {"key": "candidate_l", "label": "Diesel run while solar and battery could carry the load",
              "value": "−$150.00", "sites": "1 of 3 Sites", "detail": "Actual 120 L · Target 0 L", "word": word,
              "children": []},
             {"key": "unexplained_l", "label": "Unexplained fuel", "value": "−$142.50", "sites": "1 of 3 Sites",
              "detail": "Actual 114 L · Target 0 L", "word": word, "children": []}]},
        # D-5C.24 (was KD1): a price does not sum across Sites (composes NONE), so the portfolio row has no actual or
        # target and section 3.2's rule gives no detail; its effect is the Modelled litres times the price
        # difference, so its word is Modelled.
        {"key": "diesel_price", "label": "Diesel price", "value": "$0.00", "sites": "1 of 3 Sites", "detail": None,
         "word": word, "children": []}]
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
    # Rev 4 (D-5C.27): H's bars and scale equal A's (the same step effects); `world_h` is this world.
    assert v["bridge"]["scale"] == A_SCALE
    assert {s["key"]: s["bar"] for g in v["bridge"]["groups"] for s in g["steps"]} == A_BARS
    assert world_h() == v


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


def _patch(monkeypatch, change) -> None:
    """Every Site bridge passed through `change` (a 4 i currency world)."""
    real = V.site_bridge
    monkeypatch.setattr(V, "site_bridge", lambda inputs, targets: change(real(inputs, targets)))


def _mto_in_kes(sb):  # 4 i nothing compared: Mto in KES, Kobo and Kisiwa in USD
    return replace(sb, roots={k: in_kes(r) for k, r in sb.roots.items()}) if sb.site_code == "MTO-001" else sb


def _subset(sb):  # 4 i one-currency subset: Kobo and Kisiwa in KES, Mto USD with its fuel cost and cash missing
    if sb.site_code == "MTO-001":
        roots = dict(sb.roots)
        roots[T.ROOT] = gone(roots[T.ROOT], "fuel_cost")
        roots[T.CASH] = replace(roots[T.CASH], gap=None, effect=None, evidence="NOT_AVAILABLE", origins=(),
                                split="NOT_SPLIT", reason="GAP_NOT_AVAILABLE", rows=())
        return replace(sb, roots=roots)
    return replace(sb, roots={k: in_kes(r) for k, r in sb.roots.items()})


def _all_kes(sb):  # 4 i all KES
    return replace(sb, roots={k: in_kes(r) for k, r in sb.roots.items()})


def _two_currencies(sb):  # 4 i a heading over two currencies: fuel cost KES (Kobo, Kisiwa), O&M USD (Mto)
    root = sb.roots[T.ROOT]
    if sb.site_code == "MTO-001":
        return replace(sb, roots={**sb.roots, T.ROOT: gone(root, "fuel_cost")})
    return replace(sb, roots={**{k: in_kes(r) for k, r in sb.roots.items()}, T.ROOT: in_kes(gone(root, "om"))})


def _sides_differ(sb):  # 4 i a Site's own sides differ: Mto's actual in KES, its target in USD
    if sb.site_code != "MTO-001":
        return sb
    values = {f: (replace(x, currency="KES") if x.currency is not None else x) for f, x in sb.actual.values.items()}
    roots = {k: bridge(MG, values, sb.targets.structure.values, k) for k in sb.roots}
    return replace(sb, roots=roots, actual=replace(sb.actual, values=values))


#: The 4 i currency worlds: (change, world, standing).
CURRENCY_WORLDS = {"nothing": (_mto_in_kes, "A", "NOT_MATCHED"), "subset": (_subset, "H", "RECONCILED"),
                   "all_kes": (_all_kes, "A", "RECONCILED"), "two": (_two_currencies, "A", "RECONCILED"),
                   "sides": (_sides_differ, "A", "RECONCILED")}


def test_4_i_nothing_compared(monkeypatch) -> None:  # review H1
    """Mto keeps its records in KES (both sides), Kobo and Kisiwa in USD: no portfolio row sums, so R has no effect
    (the designed `headline_na` state). A missing figure is never printed as 0; a line with no figure is left out."""
    _patch(monkeypatch, _mto_in_kes)
    v = view()
    # Review L7: the headline says why (R's Sites hold KES and USD).
    assert v["headline"] == {"text": "Contribution for October is not available yet: the Sites' figures are in different currencies.",
                             "evidence": []}
    gap = v["tiles"][1]
    assert (gap["value"], gap["word"], gap["lines"]) == ("Not available yet", None, [])  # D-5C.26
    b = v["bridge"]
    assert b["title"] is None
    assert [(g["label"], g["value"]) for g in b["groups"]] == [("Grow revenue", "Not available yet"),
                                                               ("Optimize cost and efficiency", "Not available yet")]
    for g in b["groups"]:
        for s in g["steps"]:
            assert s["value"] == "Not available yet"
            assert s["drawer"]["lines"] == ["3 of 3 Sites"], s["key"]
    grow, opt = v["outcomes"][:2]
    assert (grow["value"], grow["word"]) == (opt["value"], opt["word"]) == ("Not available yet", None)  # D-5C.26
    assert b["by_site"]["total"][3:] == ["Not available yet"] * 5
    # The only zeros left are Sites' own figures (each Site's own row compares in its own currency).
    own = (".bridge.by_site.rows[", ".cash.table.rows[")
    zeros = [p for p, s in _paths(v) if "$0.00" in s]
    assert zeros and all(p.startswith(own) or ".drawer.sites[" in p for p in zeros), zeros
    # Currency (fix round 2): each Site's own figures print in its own currency, the portfolio's in the portfolio's.
    mto = b["by_site"]["rows"][2]
    assert mto[0] == "Mto" and all("KES" in c and "$" not in c for c in mto[1:3]), mto
    own_cells = [c for c in mto[1:] if c != "Not available yet"]
    assert own_cells and all("KES" in c and "$" not in c for c in own_cells), mto
    for row in (r for r in b["by_site"]["rows"] if r[0] != "Mto"):
        assert all("KES" not in c for c in row), row
    cash_mto = v["cash"]["table"]["rows"][2]
    assert cash_mto[0] == "Mto" and all("KES" in c and "$" not in c for c in cash_mto[1:]), cash_mto
    mto_drawer = [s for g in b["groups"] for st in g["steps"] for s in st["drawer"]["sites"] if s["site"] == "Mto"]
    assert mto_drawer and all("KES" in s["value"] and "$" not in s["value"] for s in mto_drawer), mto_drawer
    # No KES amount is printed with "$", and Kobo's and Kisiwa's figures never carry KES, anywhere in the payload.
    assert [p for p, s in _paths(v) if "KES" in s and "$" in s] == []
    kes = [p for p, s in _paths(v) if "KES" in s]
    assert kes and all(".by_site.rows[2]" in p or ".cash.table.rows[2]" in p or ".drawer." in p or ".out" in p
                       for p in kes), kes
    # A residual with no figure is left out of the stops (`effect or 0` printed "$0.00").
    side, absent, stated = t5b.side, t5b._absent, t5b.stated
    gone = {"delivered_kwh": absent("delivered_kwh", "NOT_RECEIVED")}
    a = side("actual", stated={"revenue": stated("3458.00")}, **gone)
    t = side("target", stated={"revenue": stated("3420.00", "DECLARED")}, **gone)
    row, _ = _stop(a, t, "revenue")
    res = next(r for r in V.lowest(row) if r.kind == "RESIDUAL")
    v7 = V._View.__new__(V._View)
    v7.cur = "USD"
    v7.sb = {"KOBO-001": SimpleNamespace(roots={T.ROOT: SimpleNamespace(currency="USD")},
                                         actual=SimpleNamespace(values=a),
                                         targets=SimpleNamespace(structure=SimpleNamespace(values=t)))}
    assert v7.stop("KOBO-001", res) is not None
    assert v7.stop("KOBO-001", replace(res, effect=None)) is None
    # A Site's stop prints its figure in the Site's own currency, whatever the portfolio's (fix round 2).
    kes = v7.stop("KOBO-001", replace(res, currency="KES"))
    assert "KES" in kes and "$" not in kes, kes
    vals = {"fuel_cost": SimpleNamespace(stated=True, value=D("5100"), computed=D("4995"), missing=None)}
    v7.sb["KOBO-001"] = SimpleNamespace(roots={T.ROOT: SimpleNamespace(currency="KES")},
                                        actual=SimpleNamespace(values=vals),
                                        targets=SimpleNamespace(structure=SimpleNamespace(values={})))
    differ = SimpleNamespace(kind="FACTOR", split="NOT_SPLIT", reason="RECORD_AND_FACTORS_DIFFER", currency="KES",
                             factor_id="fuel_cost", unobserved_actual=(), unobserved_target=())
    said = v7.stop("KOBO-001", differ)
    assert said and "KES" in said and "$" not in said, said


# --- test 4 i, currency (review H3, M3): every figure prints in the currency of the rows it sums ---------------

def _owned(obj, path="", mto=False):
    """Every string of the payload with its path and whether it is Mto's own figure: a by-Site or cash row of Mto's,
    a drawer Site entry of Mto's, or a sentence about Mto."""
    if isinstance(obj, str):
        yield path, obj, mto or obj.startswith("Mto")
    elif isinstance(obj, dict):
        mine = mto or obj.get("site") == "Mto"
        for k, x in obj.items():
            yield from _owned(x, f"{path}.{k}", mine)
    elif isinstance(obj, list):
        mine = mto or (bool(obj) and obj[0] == "Mto")
        for i, x in enumerate(obj):
            yield from _owned(x, f"{path}[{i}]", mine)


def test_4_i_currency_one_currency_subset(monkeypatch) -> None:  # review H3, probe cur1
    """Kobo and Kisiwa keep KES, Mto USD, and Mto's fuel cost (and its cash) is not available: R sums nothing (two
    currencies), but the fuel cost step, its drivers, the Optimize heading and card, the by-Site total's fuel cell and
    the cash figures sum Kobo and Kisiwa only (2 of 3 Sites), in KES. No KES figure is printed with "$", and no figure
    of Mto's with KES. (Notices and the organisation's budget lines print in their own budget currency, USD, which
    this world does not change.)"""
    _patch(monkeypatch, _subset)
    v = view("H", standing=RECONCILED)  # H: Kobo's fuel cost splits into litres and price (drivers)
    assert v["headline"]["text"] == "Contribution for October is not available yet: the Sites' figures are in different currencies."
    b = v["bridge"]
    fuel = step(v, "fuel_cost")
    assert fuel["sites"] == "2 of 3 Sites"
    assert fuel["value"].startswith("+KES") and "$" not in fuel["value"], fuel["value"]  # the step
    opt = next(g for g in b["groups"] if g["key"] == T.OPTIMIZE)
    assert opt["value"] == fuel["value"]  # the heading: only fuel cost has a figure
    lines = fuel["drawer"]["lines"]
    assert lines[:2] and all("KES" in x and "$" not in x for x in lines[:2]), lines  # the drawer's figures
    drivers = [d for d in _paths(fuel["drawer"]["drivers"]) if d[0].endswith(".value") and d[1] != "Not available yet"]
    assert drivers and all("KES" in x and "$" not in x for _, x in drivers), drivers  # the drivers
    details = [x for p, x in _paths(fuel["drawer"]["drivers"]) if p.endswith(".detail")]
    assert details and not any("$" in x for x in details), details
    total = b["by_site"]["total"]
    assert total[1:4] == ["Not available yet"] * 3
    assert "KES" in total[4 + T.STEPS[T.MINI_GRID].index("fuel_cost")], total  # the by-Site total's fuel cell
    card = next(c for c in v["outcomes"] if c["label"] == "Optimize cost and efficiency")
    assert card["value"] == fuel["value"]  # the card
    cash = v["cash"]
    assert cash["sites"] == "2 of 3 Sites" and "KES" in cash["text"] and "$" not in cash["text"], cash["text"]
    assert all("KES" in x for x in cash["table"]["total"][2:]), cash["table"]["total"]
    assert cash["text"] == ("Of KES 7,528.00 billed for October, KES 6,980.00 has been collected, KES 0.00 is paid but "
                            "in transit and KES 548.00 is still outstanding."), cash["text"]  # D-5C.29, plant C3
    assert cash["table"]["total"] == ["2 of 3 Sites", "KES 7,528.00", "KES 6,980.00", "KES 0.00", "KES 548.00"]
    assert cash["table"]["rows"][2] == ["Mto", "Not available yet", "$1,890.00", "Not available yet",
                                        "Not available yet"]  # plant C4
    mto = b["by_site"]["rows"][2]
    assert mto[0] == "Mto" and "$" in mto[1] and "$" in mto[2], mto  # Mto's own figures in its own USD
    # Across the whole payload: no amount prints in a currency other than its rows'.
    wrong = [(p, x) for p, x, mine in _owned(v) if not p.startswith(".notices") and ".lines_org[" not in p
             and (("KES" in x) if mine else ("$" in x))]
    assert wrong == []
    assert [p for p, x, mine in _owned(v) if not mine and "KES" in x]


def test_4_i_currency_all_kes_no_dollar(monkeypatch) -> None:  # review M4: R and every Site in KES, plants RP5, RP6
    """R and every Site are in KES: every portfolio figure prints in KES and no "$" appears anywhere except in the
    notices and the organisation's budget lines (each in its own budget's currency, USD in this world)."""
    _patch(monkeypatch, _all_kes)
    v = view(standing=RECONCILED)
    dollars = [(p, x) for p, x in _paths(v) if "$" in x and not p.startswith(".notices") and ".lines_org[" not in p]
    assert dollars == [], dollars
    assert all("KES" in t["value"] for t in v["tiles"][:2]), v["tiles"]  # the tiles (RP5)
    totals = v["bridge"]["totals"]
    assert "KES" in totals["actual"] and "KES" in totals["target"], totals  # the totals (RP6)
    assert "KES" in v["headline"]["text"], v["headline"]
    assert [p for p, x in _paths(v) if "KES" in x]


def test_4_i_currency_card_word_beside_no_figure() -> None:  # review L9, probe P6; rev 4 D-5C.26 (plant L9)
    """World X: the Optimize heading would add KES fuel cost (Kobo) to USD O&M and staff (Kisiwa), so its card has no
    figure and, with no figure, no word (D-5C.26 revises L9: never "Not available yet" as the word)."""
    v = world_x()
    card = next(c for c in v["outcomes"] if c["label"] == "Optimize cost and efficiency")
    assert step(v, "fuel_cost")["value"] != "Not available yet"  # a step still has a figure
    assert (card["value"], card["word"]) == ("Not available yet", None), card


def test_4_i_currency_a_heading_over_two_currencies(monkeypatch) -> None:  # review H3, plant C3
    """Fuel cost sums Kobo and Kisiwa in KES (Mto's is missing) and O&M sums Mto alone in USD (Kobo's and Kisiwa's
    are missing): each step prints in its own currency, and the Optimize heading, which would add KES to USD, has no
    figure ("Not available yet"), nor has its card."""
    _patch(monkeypatch, _two_currencies)
    v = view(standing=RECONCILED)
    fuel, om = step(v, "fuel_cost"), step(v, "om")
    assert "KES" in fuel["value"] and "$" not in fuel["value"], fuel["value"]
    assert om["value"].startswith(("$", "−$", "+$")) and om["sites"] == "1 of 3 Sites", om
    opt = next(g for g in v["bridge"]["groups"] if g["key"] == T.OPTIMIZE)
    assert opt["value"] == "Not available yet"
    card = next(c for c in v["outcomes"] if c["label"] == "Optimize cost and efficiency")
    assert card["value"] == "Not available yet"


def test_4_i_currency_a_sites_own_sides_differ(monkeypatch) -> None:  # review H3, M3, probe cur2 (5b case (h))
    """Mto's actual is in KES and its target in USD: Mto prints each side in its own currency (never the portfolio's),
    and is out of every portfolio figure with the currency reason, not "not a mini-grid Site"."""
    _patch(monkeypatch, _sides_differ)
    v = view(standing=RECONCILED)
    b = v["bridge"]
    assert b["totals"]["actual"].startswith("$") and v["tiles"][0]["value"].startswith("$")  # R: Kobo and Kisiwa
    mto = b["by_site"]["rows"][2]
    assert mto[0] == "Mto" and mto[1].startswith("KES") and mto[2].startswith("$"), mto  # each side its own
    assert mto[3:] == ["Not compared"] * (1 + len(T.STEPS[T.MINI_GRID]))
    outs = [o for g in b["groups"] for s in g["steps"] for o in s["drawer"]["out"] if o.startswith("Mto")]
    assert outs and set(outs) == {"Mto: not compared: its actual and its target are in different currencies (KES and USD)."}, outs  # M3
    assert not [x for x in strings(v) if "not a mini-grid Site" in x]
    cash_mto = v["cash"]["table"]["rows"][2]
    assert cash_mto[0] == "Mto" and cash_mto[2].startswith("KES"), cash_mto
    # Across the whole payload: KES is Mto's actual side only; a "$" of Mto's is its target or its budget's notice.
    kes = [p for p, x, mine in _owned(v) if "KES" in x and not (mine and ".out[" not in p)]
    assert kes == [p for p, x, _ in _owned(v) if x.startswith("Mto: not compared: its actual and its target")]
    mto_usd = [p for p, x, mine in _owned(v) if mine and "$" in x and not p.startswith(".notices")]
    assert mto_usd == [".bridge.by_site.rows[2][2]"], mto_usd


def test_4_h_driver_detail_in_its_rows_currency() -> None:  # review H3, plant C7
    """A driver's detail prints its money or price in its own row's currency (World H's drivers are litres only)."""
    v = V._View.__new__(V._View)
    v.reg = MG
    kes = SimpleNamespace(actual=D("4595"), target=D("3865"), currency="KES")
    for key in ("om", "diesel_price"):
        said = v.driver_detail(key, kes)
        assert "KES" in said and "$" not in said, (key, said)


def _kwh_world(monkeypatch) -> None:
    """World A with the emulated budget's kWh shape (3A3 `budget-illustrative-1.csv` states kWh lines): revenue splits
    into energy delivered (kWh, with an actual and a target) and tariff (a price per kWh)."""
    real = V.portfolio_bridge

    def portfolio_bridge(*args, **kwargs):
        pb = real(*args, **kwargs)
        rows = dict(pb.rows[T.ROOT])
        rev = rows[T.REVENUE]
        rows["delivered_kwh"] = replace(rev, key="delivered_kwh", kind="VOLUME", actual=D("8550"), target=D("9000"),
                                        gap=D("-450"), effect=D("-112.50"))
        # D-5C.24: a price does not sum across Sites, so the portfolio's tariff row has no actual or target.
        rows["tariff"] = replace(rev, key="tariff", kind="PRICE", actual=None, target=None, gap=None,
                                 effect=D("15.50"))
        return replace(pb, rows={**pb.rows, T.ROOT: rows})
    monkeypatch.setattr(V, "portfolio_bridge", portfolio_bridge)


def test_4_h_driver_detail_kwh(monkeypatch) -> None:  # PF1 (DDR): VOCABULARY_UNKNOWN on a kWh driver; plant PF1
    """A kWh quantity and a price per kWh render their detail with the SC-1 unit word "kWh" (the registry's dimension
    name is "KWH"); the payload renders."""
    _kwh_world(monkeypatch)
    v = view()
    drivers = {d["key"]: d for d in step(v, "revenue")["drawer"]["drivers"]}
    assert drivers["delivered_kwh"]["detail"] == "Actual 8,550 kWh · Target 9,000 kWh"
    assert drivers["tariff"]["detail"] is None
    assert (drivers["delivered_kwh"]["value"], drivers["tariff"]["value"]) == ("−$112.50", "+$15.50")
    # The price form of the same unit (a Site's own tariff row has both sides).
    w = V._View.__new__(V._View)
    w.reg = MG
    said = w.driver_detail("tariff", SimpleNamespace(actual=D("0.27"), target=D("0.25"), currency="USD"))
    assert said == "Actual $0.27 per kWh · Target $0.25 per kWh", said


def test_1_driver_units_have_words() -> None:  # PF1: every driver a MINI_GRID step can show has a unit word
    from assetops_backend.i18n.statements.en.vocabulary import VOCABULARY
    from assetops_backend.structure.attribution.rules import BRIDGE_ROOTS
    v = V._View.__new__(V._View)
    v.reg = MG
    reachable = set().union(*(_reachable(r) for r in BRIDGE_ROOTS["MINI_GRID"]))
    seen = set()
    for f in sorted(reachable):
        unit = MG.row(f).unit
        others = [n for n, _ in unit.exponents if n != "MONEY"]
        if unit.is_money:
            continue
        # review L2: driver_detail reads UNIT_WORDS[others[0]], so a unit with two non-money dimensions must fail here
        assert len(others) == 1, (f, others)
        seen.add(others[0])
        assert T.UNIT_WORDS[others[0]] in VOCABULARY["unit"]["entries"], f
        assert v.driver_detail(f, SimpleNamespace(actual=D("2"), target=D("1"), currency="USD"))
    assert {"KWH", "L"} <= seen


def test_4_h_residual_is_last_of_its_parent() -> None:  # review L8, D-5C.21, plant RP4
    """A residual sits under the factor it splits, after that factor's other parts, whatever `pb.rows` order."""
    def row(effect: str):
        return SimpleNamespace(effect=D(effect), currency="USD", k=1, actual=None, target=None, evidence="DERIVED",
                               origins=())
    v = V._View.__new__(V._View)
    v.reg, v.n, v.standing = MG, 1, RECONCILED
    v.rows = {k: row("1") for k in ("revenue", "residual:revenue", "residual:billed_kwh", "billed_kwh",
                                    "delivered_kwh", "tariff")}

    def tree(nodes):
        return [(n["key"], tree(n["children"])) for n in nodes]
    assert tree(v.drivers("revenue")) == [
        ("billed_kwh", [("delivered_kwh", []), ("residual:billed_kwh", [])]), ("tariff", []),
        ("residual:revenue", [])]


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
    # D-5C.19 (H2): DECLARED with each origin, in section 2.4's order after SC-1f (plant P23).
    ("DECLARED", ("observed-financial",), "Recorded"), ("DECLARED", ("bench-tested",), "Recorded"),
    ("DECLARED", ("source-emulated",), "Emulated"), ("DECLARED", ("demo-simulated",), "Simulated"),
    ("DECLARED", ("unknown",), "Estimated"), ("DECLARED", (), "Estimated"),
    ("DECLARED", ("observed-financial", "source-emulated"), "Emulated"),
    ("DERIVED", ("observed-financial",), "Calculated"), ("RECORDED", ("observed-financial", "source-emulated"),
                                                         "Emulated"),  # plant P9
]


@pytest.mark.parametrize(("ev", "origins", "expected"), WORDS)
def test_5_words(ev, origins, expected) -> None:
    assert W.word(ev, origins, RECONCILED, "USD") == expected
    suffixed = expected if expected == "Not available yet" else f"{expected}, not yet reconciled"  # plant P4
    assert W.word(ev, origins, NOT_MATCHED, "USD") == suffixed
    assert "Verified" not in (W.word(ev, origins, RECONCILED, "USD"), suffixed)


def test_5_record_words_hold_no_comma_outside_brackets() -> None:  # D-5C.25, plant P26
    """`needs` joins records with commas, so a record's own words hold none outside brackets."""
    from assetops_backend.i18n.statements.en.vocabulary import VOCABULARY
    entries = VOCABULARY["record"]["entries"]
    assert entries
    for key, forms in entries.items():
        for text in forms.values():
            depth, bare = 0, []
            for ch in text:
                depth += ch == "("
                depth -= ch == ")"
                if ch == "," and depth == 0:
                    bare.append(ch)
            assert not bare, (key, text)


# --- test 6: one contribution -----------------------------------------------------------------------------------

def test_6_one_contribution(monkeypatch) -> None:
    a, d = view("A"), view("D")
    assert not [s for s in strings(a) if "$2,735.50" in s]  # plant P1 (re-pinned: 4,431.60 less Kisiwa 1,696.10; was 1,693.00)
    picked = {k: d[k] for k in ("tiles", "headline", "outcomes")} | {"totals": d["bridge"]["totals"]}
    assert not [s for s in strings(picked) if "$1,565.50" in s]
    assert a["tiles"][0]["value"] == a["bridge"]["totals"]["actual"] == "$4,431.60"
    assert d["tiles"][0]["value"] == d["bridge"]["totals"]["actual"] == "$3,261.60"
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
    v.sb = {"KOBO-001": SimpleNamespace(roots={T.ROOT: SimpleNamespace(currency="USD")}, actual=SimpleNamespace(values=a),
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


# --- rev 4: bars (D-5C.27), no share without a gap (D-5C.28), no word beside no figure (D-5C.26) ---------------

def _bar(left: str, width: str, tone: str) -> dict:
    return {"left": left, "width": width, "tone": tone}


BARS = [  # (effects, gap, bars, scale): spec section 3.5 "Bars"
    ("V1", ("50.00", "-150.00"), "-100.00", [_bar("0.00", "33.33", "raises"), _bar("0.00", "100.00", "lowers")],
     {"target_at": "33.33", "actual_at": "100.00"}),
    ("V2", ("-1.00", "-999.00"), "-1000.00", [_bar("0.00", "0.80", "lowers"), _bar("0.10", "99.90", "lowers")],
     {"target_at": "0.00", "actual_at": "100.00"}),
    ("V3", (None, "-852.00"), "-852.00", [None, _bar("0.00", "100.00", "lowers")],
     {"target_at": "0.00", "actual_at": "100.00"}),
    ("V4", ("-97.00", "-755.00"), None, [None, None], None),
    ("V5", ("5.00", "-5.00"), "0.00", [None, None], None),
    ("V6", ("-150.00", "50.00"), "-100.00", [_bar("0.00", "100.00", "lowers"), _bar("66.67", "33.33", "raises")],
     {"target_at": "0.00", "actual_at": "66.67"}),
]


@pytest.mark.parametrize(("name", "effects", "gap", "bars", "scale"), BARS, ids=[b[0] for b in BARS])
def test_bars_vectors(name, effects, gap, bars, scale) -> None:  # D-5C.27; plant: a bar from the rounded share
    got = V.bridge_bars([D(e) if e is not None else None for e in effects], D(gap) if gap is not None else None)
    assert got == (bars, scale)


def test_bars_world_x_no_share_no_bar_no_word() -> None:  # D-5C.26 to D-5C.28; plant `or Decimal(0)`
    v = world_x()
    b = v["bridge"]
    steps = [s for g in b["groups"] for s in g["steps"]]
    assert [s["share"] for s in steps] == [None] * len(steps)  # D-5C.28: R has no effect
    assert not [x for x in strings(v) if "Offsets it" in x]
    assert [s["bar"] for s in steps] == [None] * len(steps) and b["scale"] is None  # D-5C.27
    assert any(s["share"] is None and s["value"] != "Not available yet" for s in steps)  # a step with a figure
    tiles = {t["key"]: t for t in v["tiles"]}
    revenue = step(v, "revenue")
    optimize = next(c for c in v["outcomes"] if c["key"] == "optimize")
    for slot in (tiles["contribution"], tiles["gap"], revenue, optimize):  # D-5C.26
        assert (slot["value"], slot["word"]) == ("Not available yet", None), slot
    assert not [w for w in _words(v) if w == "Not available yet"]


def test_bars_gap_zero_no_share() -> None:  # D-5C.28; plant `or Decimal(0)`
    """R's effect 0 with steps +5.00 and -5.00: nothing widens a gap of 0, so neither step has a share (and, V5, no
    bar). A gap of None is the same (World X)."""
    v = V._View.__new__(V._View)
    v.steps = ("revenue", "fuel_cost")
    row = lambda e: SimpleNamespace(effect=D(e), evidence="RECORDED", origins=("observed-financial",))  # noqa: E731
    v.rows = {"revenue": row("5.00"), "fuel_cost": row("-5.00")}
    for gap in (D("0.00"), None):
        v.R = SimpleNamespace(effect=gap)
        assert v.shares() == {}, gap
    v.R = SimpleNamespace(effect=D("-5.00"))  # the same steps against a gap: fuel cost widens it, revenue offsets it
    assert set(v.shares()) == {"revenue", "fuel_cost"}


def test_bars_gap_zero_whole_payload(monkeypatch) -> None:  # KD2 ruling (coordinator, 2026-11-21); plant: rest at 0
    """R's gap exactly 0 (steps +5.00 and -5.00, O&M and staff 0): the payload renders; the gap tile has no rest line
    (nothing to offset); no step reads "Offsets it"; no share, no bar, no scale."""
    _lead_world(monkeypatch, "0.00", "5.00", "-5.00")
    v = view()
    gap = v["tiles"][1]
    assert gap["value"] == "$0.00" and gap["word"] is not None  # D-5C.26: a figure, so a word
    assert not [x for x in gap["lines"] if "not split to its drivers" in x or "offsetting" in x], gap["lines"]
    assert gap["lines"] == ["Grow +$5.00 · Optimize −$5.00"], gap["lines"]
    steps = [s for g in v["bridge"]["groups"] for s in g["steps"]]
    assert [s["value"] for s in steps] == ["+$5.00", "−$5.00", "$0.00", "$0.00"]
    assert [s["share"] for s in steps] == [None] * 4
    assert not [x for x in strings(v) if "Offsets it" in x]
    assert [s["bar"] for s in steps] == [None] * 4 and v["bridge"]["scale"] is None


def _words(obj):
    """Every served word: each `word` key's value, and the headline's evidence."""
    if isinstance(obj, dict):
        for k, x in obj.items():
            if k == "word":
                yield x
            elif k == "evidence" and isinstance(x, list):
                yield from x
            else:
                yield from _words(x)
    elif isinstance(obj, list):
        for x in obj:
            yield from _words(x)


def _drivers(nodes):
    for n in nodes:
        yield n
        yield from _drivers(n["children"])


def _slots(v: dict):
    """Every figure slot (D-5C.26) as (path, figure absent, word)."""
    na = "Not available yet"
    for t in v["tiles"]:
        yield f"tiles.{t['key']}", t["value"] == na, t["word"]
    for g in v["bridge"]["groups"]:
        for s in g["steps"]:
            yield f"step.{s['key']}", s["value"] == na, s["word"]
            for d in _drivers(s["drawer"]["drivers"] if s["drawer"] is not None else []):
                yield f"driver.{s['key']}.{d['key']}", d["value"] == na, d["word"]
    for c in v["outcomes"]:
        if c["key"] != "assure":  # the Assure card is not a figure slot
            yield f"outcome.{c['key']}", c["value"] == na, c["word"]
    yield "cash", v["cash"]["table"]["total"][2] == na, v["cash"]["word"]  # the collected root's actual


CLASS_WORLDS = ["A", "B", "D", "G", "H", "X", *CURRENCY_WORLDS]


@pytest.mark.parametrize("name", CLASS_WORLDS)
def test_16_word_null_iff_figure_absent(name, monkeypatch) -> None:  # D-5C.26; plant: L9's card word
    if name == "X":
        v = world_x()
    elif name in CURRENCY_WORLDS:
        change, base, standing = CURRENCY_WORLDS[name]
        _patch(monkeypatch, change)
        v = view(base, standing=globals()[standing])
    else:
        v = view("A" if name == "B" else name, standing=RECONCILED if name == "B" else NOT_MATCHED)
    slots = list(_slots(v))
    if name != "nothing":  # World "nothing" compares nothing: every slot is absent
        assert any(not absent for _, absent, _ in slots)  # the set of slots with a figure is not empty
    if name in ("X", "nothing", "two"):  # these worlds also hold a computed slot with no figure (not only the plan)
        assert any(absent for p, absent, _ in slots if not p.startswith(("tiles.plan", "outcome.protect")))
    wrong = [(path, absent, word) for path, absent, word in slots if absent != (word is None)]
    assert wrong == [], wrong
    words = list(_words(v))
    assert words and "Not available yet" not in words
    assert None not in v["headline"]["evidence"]


# --- D-5C.29: the cash sentence states the bills and their three parts ---------------------------------------------

MONEY = re.compile(r"(?:KES |\$)[\d,]+\.\d\d")
SIDES_SENTENCE = ("Of $7,528.00 billed for October, $6,980.00 has been collected, $0.00 is paid but in transit and "
                  "$548.00 is still outstanding.")


@pytest.mark.parametrize("name", ["A", "D", "E", "G", "H", "X", *CURRENCY_WORLDS])
def test_cash_sentence_reconciles(name, monkeypatch) -> None:  # D-5C.29; plants C1, C2
    if name == "X":
        v = world_x()
    elif name in CURRENCY_WORLDS:
        change, base, standing = CURRENCY_WORLDS[name]
        _patch(monkeypatch, change)
        v = view(base, standing=globals()[standing])
    else:
        v = view(name)
    cash = v["cash"]
    tokens = MONEY.findall(cash["text"])
    total = cash["table"]["total"]
    na = "Not available yet"
    assert len(tokens) in (0, 1, 4), cash["text"]
    if len(tokens) == 4:
        figures = [D(t.replace("KES ", "").replace("$", "").replace(",", "")) for t in tokens]
        assert figures[0] == figures[1] + figures[2] + figures[3], cash["text"]
        assert total[1:5] == tokens, (total, tokens)
    else:
        assert [total[1], total[3], total[4]] == [na] * 3, total
    assert "expected" not in json.dumps(cash).lower()
    assert "expected" not in cash["text"]


def test_cash_sentence_literals(monkeypatch) -> None:  # D-5C.29
    d = view("D")["cash"]
    assert d["text"] == SIDES_SENTENCE
    assert d["table"]["total"] == ["2 of 3 Sites", "$7,528.00", "$6,980.00", "$0.00", "$548.00"]
    _patch(monkeypatch, _sides_differ)
    sides = view("A", standing=RECONCILED)["cash"]
    assert sides["text"] == SIDES_SENTENCE
    assert sides["table"]["total"][1:] == ["$7,528.00", "$6,980.00", "$0.00", "$548.00"]


def _row(key, actual, currency="USD", sites=("K", "L")):
    return PortfolioRow(key=key, kind="TERM", actual=None if actual is None else D(actual), target=None, gap=None,
                        effect=None, currency=currency, note=None, evidence="RECONCILED", origins=(), k=len(sites),
                        n=len(sites), out=tuple((c, ()) for c in sites), carried=())


def _parts(change=None, collected="100", revenue="120", transit="0", owed="20"):
    rows = {T.CASH: _row(T.CASH, collected), T.REVENUE: _row(T.REVENUE, revenue),
            T.IN_TRANSIT: _row(T.IN_TRANSIT, transit), T.OUTSTANDING: _row(T.OUTSTANDING, owed)}
    for key, row in (change or {}).items():
        if row is None:
            rows.pop(key)
        else:
            rows[key] = row
    return rows


def test_cash_parts_vectors() -> None:  # D-5C.29 (d); plant C2
    assert V.cash_parts(_parts(owed="10")) is None  # 100 != 120 - 0 - 10
    rows = _parts()
    assert V.cash_parts(rows) == (rows[T.REVENUE], rows[T.IN_TRANSIT], rows[T.OUTSTANDING])
    assert V.cash_parts(_parts({T.OUTSTANDING: _row(T.OUTSTANDING, "20", sites=("K", "L", "M"))})) is None
    assert V.cash_parts(_parts({T.REVENUE: _row(T.REVENUE, "120", currency="KES")})) is None
    assert V.cash_parts(_parts({T.IN_TRANSIT: None})) is None
