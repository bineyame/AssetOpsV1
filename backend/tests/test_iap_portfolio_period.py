"""IA-P P3a (`spec-period.md` P.7, tests 1 to 12; D-IAP.16, D-IAP.17, D-IAP.25): E2, the Overview on the date range.

Pure: 5c's World A served October store, World P (A plus a September copy), World G and World X, read through the real
`DeepDiveRead` with in-memory snapshot and standing fakes. Every English literal is written by hand (W2).
`IAP_WRITE_FIXTURES=1` rewrites the frontend fixtures of test 10 from the view (then the test is read again).
"""
from __future__ import annotations

import json
import os
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from assetops_backend.deep_dive import period as P
from assetops_backend.deep_dive import tables as T
from assetops_backend.deep_dive import view as V
from assetops_backend.deep_dive.actions import NotConnectedActions
from assetops_backend.deep_dive.read import DeepDiveRead
from assetops_backend.deep_dive.view import month_view
from assetops_backend.deep_dive_api import build_deep_dive_router
from assetops_backend.structure_snapshot.model import Served
from assetops_backend.i18n import message, render
from assetops_backend.i18n import served as served_words
from deep_dive_worlds import _x
from statement_cases import portfolio_period as period_cases
from statement_cases import portfolio_sites as sites_cases
from test_5c_deep_dive_api import LAKESIDE, PERSON_REQUIRED, UNAVAILABLE, Accounts, Registry
from test_5c_deep_dive_view import NAMES, NOT_MATCHED, OFF, world

NOW = datetime(2026, 11, 22, tzinfo=timezone.utc)
ROUTE = "/api/portfolio/period"
FIXTURES = Path(__file__).resolve().parents[2] / "frontend" / "src" / "estate" / "__tests__" / "fixtures" / "iap"
BAD_RANGE = {"code": "BAD_RANGE", "text": "Write the range as two days, YYYY-MM-DD, the first not after the last."}
TOO_LONG = {"code": "RANGE_TOO_LONG", "text": "The month figures cover at most 24 months. Narrow the date range."}
NOV_PARTIAL = ("November is only partly in this range, so it is not counted: the figures are kept by whole month.")
NONE_NOTE = ("This range holds no whole month with figures. Contribution against target is kept by whole calendar "
             "month.")
NO_SNAP = Served("NO_SNAPSHOT", None, None, None)


def as_september(standing):
    return SimpleNamespace(reconciled=standing.reconciled, reason=standing.reason,
                           text=standing.text.replace("October 2026", "September 2026"),
                           details=tuple(d.replace("October 2026", "September 2026") for d in standing.details))


def copy_to(served, month: str):
    """`Served` has no month field: the snapshot's (`spec-period.md` P.7). The Site snapshots' inputs and target
    structures carry the month too (5b's compose check), so they move with it (packet, Known Deviations)."""
    def site(s):
        targets = replace(s.targets, structure=replace(s.targets.structure, month=month))
        return replace(s, month=month, inputs=replace(s.inputs, month=month), targets=targets)
    snap = served.snapshot
    return replace(served, snapshot=replace(snap, month=month, sites={c: site(s) for c, s in snap.sites.items()}))


def _world_p(name: str = "A") -> dict:
    served, _, _ = world(name)
    return {"2026-09": copy_to(served, "2026-09"), "2026-10": served}


class Snapshots:
    def __init__(self, months: dict) -> None:
        self.months, self.asked = months, []

    def portfolio(self, tenant_id, month):
        self.asked.append(month)
        return self.months.get(month, NO_SNAP)


class Recon:
    def __init__(self, standing=NOT_MATCHED) -> None:
        self.standing_, self.asked = standing, []

    def standing(self, tenant_id, site_id, period, *, known_at=None):
        self.asked.append((site_id, period, known_at))
        return as_september(self.standing_) if period == "2026-09" else self.standing_


def read_of(months: dict, standing=NOT_MATCHED) -> DeepDiveRead:
    return DeepDiveRead(Snapshots(months), Recon(standing), NotConnectedActions(), lambda: NOW)


def period(months: dict, first: str, last: str, names=None) -> dict:
    return read_of(months).period(LAKESIDE, date.fromisoformat(first), date.fromisoformat(last),
                                  names if names is not None else NAMES)


def days(words: str, first: str, last: str) -> dict:
    return {"month_words": words, "from": first, "to": last}


# --- 1 -----------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("first,last,months,edges", [
    ("2026-11-15", "2026-11-21", (), (("2026-11", "PARTIAL"),)),
    ("2026-11-01", "2026-11-21", (), (("2026-11", "PARTIAL"),)),
    ("2026-10-23", "2026-11-21", (), (("2026-10", "PARTIAL"), ("2026-11", "PARTIAL"))),
    ("2026-10-01", "2026-10-31", ("2026-10",), ()),
    ("2026-10-01", "2026-11-21", ("2026-10",), (("2026-11", "PARTIAL"),)),
    ("2026-08-01", "2026-10-31", ("2026-08", "2026-09", "2026-10"), ()),
    ("2026-11-01", "2026-11-30", (), (("2026-11", "OPEN"),)),
])
def test_1_resolve(first, last, months, edges) -> None:  # plant `dayscut`
    p = P.resolve(date.fromisoformat(first), date.fromisoformat(last), NOW)
    assert (p.first, p.last) == (date.fromisoformat(first), date.fromisoformat(last))
    assert p.months == months and p.edges == edges


def test_1_resolve_refuses() -> None:
    with pytest.raises(ValueError, match="^RANGE_TOO_LONG$"):
        P.resolve(date(2024, 9, 1), date(2026, 9, 30), NOW)  # 25 whole months
    assert len(P.resolve(date(2024, 10, 1), date(2026, 9, 30), NOW).months) == 24
    with pytest.raises(ValueError, match="^BAD_RANGE$"):
        P.resolve(date(2026, 10, 2), date(2026, 10, 1), NOW)
    assert P.month_days("2026-02") == (date(2026, 2, 1), date(2026, 2, 28))
    assert P.month_days("2026-12") == (date(2026, 12, 1), date(2026, 12, 31))


# --- 2 and 3 -----------------------------------------------------------------------------------------------------

def test_2_world_p_two_months() -> None:
    got = period(_world_p(), "2026-09-01", "2026-10-31")
    assert list(got) == ["schema", "from", "to", "mode", "months", "served", "period_words", "notes", "shown", "nav",
                         "suggest", "body"]
    assert (got["schema"], got["from"], got["to"], got["mode"]) == ("portfolio-period-1", "2026-09-01", "2026-10-31",
                                                                    "period")
    assert got["months"] == [{"month": "2026-09", "month_words": "September 2026", "from": "2026-09-01",
                              "to": "2026-09-30", "state": "SERVED"},
                             {"month": "2026-10", "month_words": "October 2026", "from": "2026-10-01",
                              "to": "2026-10-31", "state": "SERVED"}]
    assert got["served"] == ["2026-09", "2026-10"]
    assert got["period_words"] == "September and October"
    assert (got["notes"], got["shown"], got["nav"], got["suggest"]) == ([], None, None, None)
    b = got["body"]
    assert list(b) == ["as_of_text", "status_line", "fresh", "headline", "tiles", "notices", "months", "outcomes",
                       "actions"]
    assert b["as_of_text"] == "Figures as of 20 November 2026, 08:00 UTC."
    assert b["status_line"] == ("Figures as of 20 November 2026, 08:00 UTC. Not yet reconciled with the management "
                                "accounts. Kisiwa's budget disagrees with its own lines.")
    assert b["fresh"] is None
    assert b["headline"] == {"text": "Contribution is $1,704.00 below target across September and October; cost and "
                                     "efficiency explain $1,510.00 of it.",
                             "evidence": ["Estimated, not yet reconciled"]}
    t0, t1, t2, t3 = b["tiles"]
    assert (t0["key"], t0["label"], t0["value"], t0["word"]) == ("contribution", "Contribution", "$2,886.00",
                                                                 "Estimated, not yet reconciled")
    # P.5 and R2 (D-IAP.25): tile 1 keeps 5c's Sites line beside the target line.
    assert t0["lines"] == ["Target $4,590.00 · 63% of target", "3 of 3 Sites"]
    assert t0["bar"] == {"actual": "2886.00", "target": "4590.00"}
    assert (t1["key"], t1["label"], t1["value"], t1["word"]) == ("gap", "Gap to target", "−$1,704.00",
                                                                 "Estimated, not yet reconciled")
    assert t1["lines"] == ["Grow −$194.00 · Optimize −$1,510.00"] and t1["bar"] is None
    five_c = month_view(operator="Lakeside Power", month="2026-10", served=world("A")[0], standing=NOT_MATCHED,
                        actions=OFF, names=NAMES, now=NOW)["tiles"]
    assert [t2, t3] == five_c[2:]
    assert b["notices"] == []
    m = b["months"]
    assert (m["title"], m["columns"]) == ("Month by month", ["Month", "Contribution", "Gap to target",
                                                             "Largest driver against target"])
    for row, (month, words, first, last) in zip(m["rows"], (("2026-09", "September 2026", "2026-09-01", "2026-09-30"),
                                                            ("2026-10", "October 2026", "2026-10-01", "2026-10-31"))):
        assert row == {"month": month, "month_words": words, "from": first, "to": last, "state": "SERVED",
                       "contribution": "$1,443.00 against a target of $2,295.00", "gap": "−$852.00",
                       "gap_word": "Estimated, not yet reconciled", "driver": "Fuel cost −$755.00",
                       "driver_heading": "Optimize cost and efficiency", "sites": "3 of 3 Sites"}
    grow, optimize, protect, assure = b["outcomes"]
    assert grow == {"key": "grow", "label": "Grow revenue", "value": "−$194.00", "word": "Emulated, not yet reconciled",
                    "line": "Revenue against target, over 2 months", "drawer": None}
    assert optimize == {"key": "optimize", "label": "Optimize cost and efficiency", "value": "−$1,510.00",
                        "word": "Estimated, not yet reconciled",
                        "line": "Fuel, O&M and staff against target; cash collected is shown apart", "drawer": None}
    assert protect == {"key": "protect", "label": "Protect asset and capital", "value": "Not available yet",
                       "word": None, "line": "Limits, warranties and rights are not set up yet", "drawer": None}
    assert (assure["value"], assure["word"], assure["line"]) == ("Not yet reconciled", None, "0 of 2 months reconciled")
    assert assure["drawer"] == {"title": "Reconciliation with the management accounts", "lines": [
        "September 2026: Not yet reconciled: September 2026 (the organisation) does not match the management accounts "
        "within 1%.",
        "October 2026: Not yet reconciled: October 2026 (the organisation) does not match the management accounts "
        "within 1%."]}
    assert b["actions"] == {"title": "Actions in hand", "connected": False,
                            "text": b["actions"]["text"], "rows": [], "more": 0}


def test_3_one_figure() -> None:  # plant `onefig`
    months = _world_p()
    got = period(months, "2026-09-01", "2026-10-31")["body"]
    total = 0
    for row in got["months"]["rows"]:
        m = row["month"]
        standing = as_september(NOT_MATCHED) if m == "2026-09" else NOT_MATCHED
        view = month_view(operator="Lakeside Power", month=m, served=months[m], standing=standing, actions=OFF,
                          names=NAMES, now=NOW)
        assert row["gap"] == view["tiles"][1]["value"] and row["gap_word"] == view["tiles"][1]["word"]
        total += V._View(months[m], standing, NAMES, m).R.effect
    assert got["tiles"][1]["value"] == V.W.amount(total, "USD", "SIGNED")


# --- 4 to 8 ------------------------------------------------------------------------------------------------------

def test_4_one_served_month_is_mode_month() -> None:
    months = _world_p()
    months["2026-09"] = NO_SNAP
    got = period(months, "2026-09-01", "2026-10-31")
    assert (got["mode"], got["served"], got["body"]) == ("month", ["2026-10"], None)
    assert got["notes"] == ["No figures are served for September, so it is not in these figures."]
    assert got["nav"] == {"previous": days("September 2026", "2026-09-01", "2026-09-30"), "next": None}
    assert got["shown"] == {"from": "2026-10-01", "to": "2026-10-31"}
    assert got["period_words"] == "October"
    assert got["months"][0]["state"] == "NO_SNAPSHOT"


def test_5_a_missing_month_is_named_and_counted_out() -> None:
    months = {**_world_p(), "2026-08": NO_SNAP}
    got = period(months, "2026-08-01", "2026-10-31")
    two = period(_world_p(), "2026-09-01", "2026-10-31")["body"]
    assert got["mode"] == "period" and got["body"]["tiles"][:2] == two["tiles"][:2]
    assert got["body"]["headline"] == two["headline"]
    rows = got["body"]["months"]["rows"]
    assert [r["month"] for r in rows] == ["2026-08", "2026-09", "2026-10"]
    assert rows[0] == {"month": "2026-08", "month_words": "August 2026", "from": "2026-08-01", "to": "2026-08-31",
                       "state": "NO_SNAPSHOT", "contribution": "The figures for August 2026 have not been prepared yet.",
                       "gap": None, "gap_word": None, "driver": None, "driver_heading": None, "sites": None}
    assert got["notes"][0] == "No figures are served for August, so it is not in these figures."
    assert got["shown"] == {"from": "2026-09-01", "to": "2026-10-31"}


def test_6_mode_none() -> None:
    got = period({"2026-10": world("A")[0]}, "2026-11-15", "2026-11-21")
    assert (got["mode"], got["months"], got["served"], got["period_words"]) == ("none", [], [], None)
    assert got["notes"] == [NOV_PARTIAL, NONE_NOTE]
    assert got["suggest"] == {"text": "Show October 2026", "from": "2026-10-01", "to": "2026-10-31"}
    assert (got["shown"], got["nav"], got["body"]) == (None, None, None)


def test_6_suggest_steps_back_at_most_twelve_months() -> None:
    r = read_of({})
    got = r.period(LAKESIDE, date(2026, 11, 15), date(2026, 11, 21), NAMES)
    assert got["suggest"] is None and r._snapshots.asked == [T.month_code(2026, 10 - i) for i in range(12)]


def test_7_shown_is_the_counted_months() -> None:
    got = period(_world_p(), "2026-09-01", "2026-11-21")
    assert got["mode"] == "period" and got["shown"] == {"from": "2026-09-01", "to": "2026-10-31"}
    assert got["notes"] == [NOV_PARTIAL]


def test_7_open_month_note() -> None:
    got = period({"2026-10": world("A")[0]}, "2026-10-01", "2026-11-30")
    assert got["notes"] == ["November has not closed yet, so it has no figures."] and got["mode"] == "month"


def test_8_currencies_are_not_added(monkeypatch) -> None:
    real = V.portfolio_bridge

    def kes(sites, asked, excluded, lines, month, key, version):
        pb = real(sites, asked, excluded, lines, month, key, version)
        if month != "2026-09":
            return pb
        rows = {root: {k: replace(r, currency="KES" if r.currency is not None else None) for k, r in by.items()}
                for root, by in pb.rows.items()}
        return replace(pb, rows=rows)

    monkeypatch.setattr(V, "portfolio_bridge", kes)
    b = period(_world_p(), "2026-09-01", "2026-10-31")["body"]
    for tile in b["tiles"][:2]:
        assert (tile["value"], tile["word"]) == ("Not available yet", None)
    assert b["notices"] == ["The months are in different currencies, so they are not added."]
    assert b["headline"]["text"] == "Contribution across September and October is not available yet."


# --- 9: the route ------------------------------------------------------------------------------------------------

def client(*, read="world", real_data=False, tenant=LAKESIDE) -> TestClient:
    if read == "world":
        read = read_of(_world_p())
    app = FastAPI()
    app.state.site_registry = Registry(tenant)
    app.include_router(build_deep_dive_router(read, accounts=Accounts(), real_data=real_data,
                                              unavailable=(OperationalError,)))
    return TestClient(app)


def test_9_route() -> None:
    c = client()
    got = c.get(ROUTE, params={"from": "2026-09-01", "to": "2026-10-31"})
    assert got.status_code == 200 and got.headers["cache-control"] == "no-store"
    assert got.json()["schema"] == "portfolio-period-1"
    for params in ({"from": "2026-02-01", "to": "2026-02-30"}, {"from": "2026-10-02", "to": "2026-10-01"},
                   {"from": "2026-10-01"}, {"from": "20261001", "to": "2026-10-31"}):
        bad = c.get(ROUTE, params=params)
        assert (bad.status_code, bad.json()) == (422, BAD_RANGE) and bad.headers["cache-control"] == "no-store"
    long = c.get(ROUTE, params={"from": "2024-09-01", "to": "2026-09-30"})
    assert (long.status_code, long.json()) == (422, TOO_LONG)
    none = client(read=None).get(ROUTE, params={"from": "2026-09-01", "to": "2026-10-31"})
    assert (none.status_code, none.json()) == (503, UNAVAILABLE)
    who = client(real_data=True).get(ROUTE, params={"from": "2026-09-01", "to": "2026-10-31"})
    assert (who.status_code, who.json()) == (401, PERSON_REQUIRED)
    fault = read_of({})
    fault._snapshots.portfolio = lambda t, m: (_ for _ in ()).throw(OperationalError("x", {}, Exception()))
    down = client(read=fault).get(ROUTE, params={"from": "2026-09-01", "to": "2026-10-31"})
    assert (down.status_code, down.json()) == (503, UNAVAILABLE)


# --- 10: the frontend fixtures are the view's --------------------------------------------------------------------

def _fixture_bodies() -> dict:
    sep_missing = {**_world_p(), "2026-09": NO_SNAP}
    return {"period-period-2026-09-10.json": period(_world_p(), "2026-09-01", "2026-10-31"),
            "period-month-2026-10.json": period(sep_missing, "2026-09-01", "2026-10-31"),
            "period-none-2026-11.json": period({"2026-10": world("A")[0]}, "2026-11-15", "2026-11-21")}


def test_10_fixtures_are_current() -> None:
    bodies = _fixture_bodies()
    if os.environ.get("IAP_WRITE_FIXTURES") == "1":
        for name, body in bodies.items():
            (FIXTURES / name).write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, body in bodies.items():
        assert json.loads((FIXTURES / name).read_text(encoding="utf-8")) == body, name


# --- 11 and 12 ---------------------------------------------------------------------------------------------------

def test_11_world_g_names_the_sites_not_compared() -> None:
    got = period(_world_p("G"), "2026-09-01", "2026-10-31", {**NAMES, "THIKA-001": "Thika"})["body"]
    assert got["headline"]["text"].endswith(" Compared for 3 of 4 Sites.")
    assert "3 of 4 Sites" in got["tiles"][0]["lines"]
    assert [r["sites"] for r in got["months"]["rows"]] == ["3 of 4 Sites", "3 of 4 Sites"]


def test_12_world_x_degrades(monkeypatch) -> None:
    real = V.site_bridge
    monkeypatch.setattr(V, "site_bridge", lambda inputs, targets: _x(real(inputs, targets)))
    got = period(_world_p("H"), "2026-09-01", "2026-10-31")["body"]
    assert got["tiles"][0]["value"] == "Not available yet" and got["tiles"][1]["value"] == "Not available yet"
    assert got["headline"]["text"] == "Contribution across September and October is not available yet."


@pytest.mark.parametrize("case", [*period_cases.CASES, *sites_cases.CASES], ids=lambda c: f"{c.key}-{c.variant}")
def test_statement_cases_render(case) -> None:
    msg = message(case.key, **case.facts)
    if case.evidence is None:
        assert render(msg) == case.english
    else:
        assert served_words(msg)["text"] == case.english
