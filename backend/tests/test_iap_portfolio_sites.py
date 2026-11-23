"""IA-P P4a (`spec-period.md` P.8, tests 1 to 9 with 4b; D-IAP.9, D-IAP.20, D-IAP.26, handshake R8 and R9): E1, the
Sites rows for the same months as the Overview.

Pure: 5c World A, D (no Mto) and G (with Thika), P.7's World P and World X, read through the real `DeepDiveRead` with
the fakes of `test_iap_portfolio_period.py`. Every English literal is written by hand (W2).
`IAP_WRITE_FIXTURES=1` rewrites test 9's frontend fixtures from the view.
"""
from __future__ import annotations

import json
import os
from dataclasses import replace
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from assetops_backend.deep_dive import period as P
from assetops_backend.deep_dive import sites as S
from assetops_backend.deep_dive import tables as T
from assetops_backend.deep_dive import view as V
from assetops_backend.deep_dive.sites import SiteRef
from assetops_backend.deep_dive.view import month_view
from assetops_backend.deep_dive_api import build_deep_dive_router
from deep_dive_worlds import _x
from test_5c_deep_dive_api import LAKESIDE, PERSON_REQUIRED, UNAVAILABLE, Accounts
from test_5c_deep_dive_view import NAMES, NOT_MATCHED, OFF, world
from test_iap_portfolio_period import BAD_RANGE, FIXTURES, NO_SNAP, NOW, _world_p, period, read_of

ROUTE = "/api/portfolio/sites"
REFS = (SiteRef("KOBO-001", "Kobo", "MINIGRID"), SiteRef("KISIWA-001", "Kisiwa", "MINIGRID"),
        SiteRef("MTO-001", "Mto", "MINIGRID"))
THIKA = SiteRef("THIKA-001", "Thika", "COLDCHAIN")
NA = "Not available yet"
OPT, GROW = "Optimize cost and efficiency", "Grow revenue"
WORD = "Modelled, not yet reconciled"


def sites(months: dict, first: str, last: str, refs=REFS) -> dict:
    return read_of(months).sites(LAKESIDE, date.fromisoformat(first), date.fromisoformat(last), refs)


def figures(row: dict) -> tuple:
    return (row["site"], row["contribution"], row["gap"], row["driver"], row["driver_heading"])


def test_1_world_a_october() -> None:  # plant `order`
    got = sites({"2026-10": world("A")[0]}, "2026-10-01", "2026-10-31")
    assert list(got) == ["schema", "from", "to", "mode", "months", "served", "period_words", "notes", "shown", "nav",
                         "suggest", "as_of_text", "headline", "columns", "rows", "total", "without_target"]
    header = period({"2026-10": world("A")[0]}, "2026-10-01", "2026-10-31")
    assert {k: got[k] for k in list(got)[1:11]} == {k: header[k] for k in list(header)[1:11]}
    assert got["schema"] == "portfolio-sites-1" and got["mode"] == "month"
    assert got["columns"] == ["Site", "Group", "Contribution", "Gap to target", "Largest driver against target",
                              "Waiting for a choice"]
    assert [figures(r) for r in got["rows"]] == [
        ("Kobo", "$1,565.50 against a target of $1,445.00", "+$120.50", "No driver widens the gap", None),
        ("Mto", "$1,170.00 against a target of $915.00", "+$255.00", "Revenue −$80.00", GROW),
        ("Kisiwa", "$1,696.10 against a target of −$65.00", "+$1,761.10", "Revenue −$55.00", GROW)]
    assert [r["below"] for r in got["rows"]] == [False, False, False]
    assert [r["group"] for r in got["rows"]] == ["Mini-grid"] * 3
    assert [r["site_code"] for r in got["rows"]] == ["KOBO-001", "MTO-001", "KISIWA-001"]
    assert [r["gap_word"] for r in got["rows"]] == [WORD, WORD, WORD]
    assert all(r["months_text"] is None for r in got["rows"])
    assert got["total"] == {"gap": "+$2,136.60", "word": WORD}
    assert got["headline"] == {"text": "Every Site is on or above target in October", "evidence": [WORD]}
    assert got["as_of_text"] == "Figures as of 20 November 2026, 08:00 UTC."
    assert got["without_target"] == {"count": 0, "text": None}
    # R9: each compared row's gap is its Site's `by_site` Gap cell in October's month view, string for string.
    by_site = month_view(operator="Lakeside Power", month="2026-10", served=world("A")[0], standing=NOT_MATCHED,
                         actions=OFF, names=NAMES, now=NOW)["bridge"]["by_site"]["rows"]
    assert {r["site"]: r["gap"] for r in got["rows"]} == {cells[0]: cells[3] for cells in by_site}


def test_1b_sites_below_target(monkeypatch) -> None:  # plant `order`
    """World A's Sites are all on or above target (D-DD.164's figures), so the below-target rows are read on it with
    Kobo's and Mto's effects turned over: worst gap first, counted, and the cost step named."""
    real = V.site_bridge

    def turned(inputs, targets):
        sb = real(inputs, targets)
        if sb.site_code == "KISIWA-001":
            return sb
        root = sb.roots[T.ROOT]
        rows = tuple(replace(row, effect=-row.effect, rows=tuple(replace(c, effect=-c.effect) for c in row.rows))
                     for row in root.rows)
        return replace(sb, roots={**sb.roots, T.ROOT: replace(root, effect=-root.effect, rows=rows)})

    monkeypatch.setattr(V, "site_bridge", turned)
    monkeypatch.setattr(S, "_check_sum", lambda z, compared: None)  # the turned roots no longer add to R
    got = sites({"2026-10": world("A")[0]}, "2026-10-01", "2026-10-31")
    assert [(r["site"], r["gap"], r["below"], r["driver"], r["driver_heading"]) for r in got["rows"]] == [
        ("Mto", "−$255.00", True, "Fuel cost −$335.00", OPT), ("Kobo", "−$120.50", True, "Fuel cost −$82.50", OPT),
        ("Kisiwa", "+$1,761.10", False, "Revenue −$55.00", GROW)]
    assert got["headline"]["text"] == "2 of 3 Sites are below target in October"


def test_2_world_g_names_thika_by_its_type() -> None:
    got = sites({"2026-10": world("G")[0]}, "2026-10-01", "2026-10-31", (*REFS, THIKA))
    thika = got["rows"][-1]
    assert thika == {"site_code": "THIKA-001", "site": "Thika", "group": "Cold-chain",
                     "contribution": "No monthly figures for cold-chain Sites yet", "gap": NA, "gap_word": None,
                     "driver": NA, "driver_heading": None, "below": False, "months_text": None}
    assert got["without_target"] == {"count": 1, "text": "1 Site without a target is not in this figure"}
    ev = S._not_compared(SiteRef("EV-001", "Depot", "EV_CHARGING"))
    assert (ev["group"], ev["contribution"]) == ("EV charging", "No monthly figures for EV charging Sites yet")


def test_2_groups_equal_the_live_domain_words() -> None:
    # A copy of `frontend/src/estate/portfolioWords.ts` DOMAIN_WORD (the fixture the frontend renders).
    domain_word = {"MINIGRID": "Mini-grid", "COLDCHAIN": "Cold-chain", "EV_CHARGING": "EV charging"}
    assert {d: S._group(d) for d in domain_word} == domain_word


def test_3_no_snapshot_is_mode_none() -> None:
    got = sites({}, "2026-10-01", "2026-10-31")
    header = period({}, "2026-10-01", "2026-10-31")
    assert got["mode"] == "none" and {k: got[k] for k in list(got)[1:11]} == {k: header[k] for k in list(header)[1:11]}
    assert got["notes"] == ["No figures are served for October, so it is not in these figures.",
                            "This range holds no whole month with figures. Contribution against target is kept by "
                            "whole calendar month."]
    assert [r["site"] for r in got["rows"]] == ["Kobo", "Kisiwa", "Mto"]
    assert all(r["contribution"] == NA and r["gap"] == NA and not r["below"] for r in got["rows"])
    assert (got["headline"], got["total"], got["as_of_text"]) == (None, None, None)


def test_4_the_sum_check(monkeypatch) -> None:  # plant `sum`
    real = V.site_bridge

    def skew(inputs, targets):
        sb = real(inputs, targets)
        if sb.site_code != "MTO-001":
            return sb
        root = sb.roots[T.ROOT]
        return replace(sb, roots={**sb.roots, T.ROOT: replace(root, effect=root.effect - 1)})

    served = world("A")[0]
    z = P.Sums((P.MonthServed("2026-10", served, NOT_MATCHED),), NAMES)
    monkeypatch.setattr(V, "site_bridge", skew)
    bad = P.Sums((P.MonthServed("2026-10", served, NOT_MATCHED),), NAMES)
    bad.Rs = z.Rs  # the portfolio's R as served; Mto's own root no longer adds to it
    with pytest.raises(AssertionError, match="^SITES_SUM$"):
        S._check_sum(bad, [S._Site(bad, s.code) for s in REFS])


def test_4b_world_x_degrades(monkeypatch) -> None:
    real = V.site_bridge
    monkeypatch.setattr(V, "site_bridge", lambda inputs, targets: _x(real(inputs, targets)))
    got = sites({"2026-10": world("H")[0]}, "2026-10-01", "2026-10-31")
    assert [r["gap"] for r in got["rows"]] == [NA, NA, NA]
    assert got["headline"] == {"text": "No Sites have figures to compare with target in October", "evidence": []}
    assert got["total"] == {"gap": NA, "word": None}
    assert got["without_target"] == {"count": 0, "text": None}
    assert all(not row["below"] and row["driver_heading"] is None for row in got["rows"])


def test_zero_comparisons_preserve_range_and_domain_reasons(monkeypatch) -> None:
    real = V.site_bridge
    monkeypatch.setattr(V, "site_bridge", lambda inputs, targets: _x(real(inputs, targets)))
    depot = SiteRef("EV-001", "Depot", "EV_CHARGING")
    got = sites(_world_p("H"), "2026-09-01", "2026-10-31", (*REFS, THIKA, depot))
    assert got["mode"] == "period"
    assert got["headline"] == {
        "text": f"No Sites have figures to compare with target in {got['period_words']}", "evidence": [],
    }
    assert got["total"] == {"gap": NA, "word": None}
    assert got["without_target"] == {"count": 0, "text": None}
    assert [row["contribution"] for row in got["rows"]] == [
        NA, NA, NA, "No monthly figures for cold-chain Sites yet", "No monthly figures for EV charging Sites yet",
    ]


def test_5_route() -> None:
    class Registry:
        def tenant(self):
            return LAKESIDE

        def imported_sites(self):
            return tuple(SimpleNamespace(site_code=r.code, name=r.name, site_type=r.domain) for r in REFS)

    def client(read="world", real_data=False) -> TestClient:
        app = FastAPI()
        app.state.site_registry = Registry()
        app.include_router(build_deep_dive_router(read_of({"2026-10": world("A")[0]}) if read == "world" else read,
                                                  accounts=Accounts(), real_data=real_data,
                                                  unavailable=(OperationalError,)))
        return TestClient(app)

    got = client().get(ROUTE, params={"from": "2026-10-01", "to": "2026-10-31"})
    assert got.status_code == 200 and got.headers["cache-control"] == "no-store"
    assert got.json() == sites({"2026-10": world("A")[0]}, "2026-10-01", "2026-10-31")
    bad = client().get(ROUTE, params={"from": "2026-02-01", "to": "2026-02-30"})
    assert (bad.status_code, bad.json()) == (422, BAD_RANGE)
    assert (client(read=None).get(ROUTE, params={"from": "2026-10-01", "to": "2026-10-31"}).json()) == UNAVAILABLE
    who = client(real_data=True).get(ROUTE, params={"from": "2026-10-01", "to": "2026-10-31"})
    assert (who.status_code, who.json()) == (401, PERSON_REQUIRED)


def test_6_every_site_on_target_and_heading_words(monkeypatch) -> None:
    real = V.site_bridge

    def lift(inputs, targets):
        sb = real(inputs, targets)
        root = sb.roots[T.ROOT]
        return replace(sb, roots={**sb.roots, T.ROOT: replace(root, effect=abs(root.effect))})

    monkeypatch.setattr(V, "site_bridge", lift)
    monkeypatch.setattr(S, "_check_sum", lambda z, compared: None)  # the lifted roots no longer add to R
    got = sites({"2026-10": world("A")[0]}, "2026-10-01", "2026-10-31")
    assert got["headline"]["text"] == "Every Site is on or above target in October"
    monkeypatch.undo()
    rows = sites({"2026-10": world("A")[0]}, "2026-10-01", "2026-10-31")["rows"]
    kisiwa = next(row for row in rows if row["site_code"] == "KISIWA-001")
    assert kisiwa["driver_heading"] == V.W.heading_label(T.GROW)


def test_7_world_p_two_months() -> None:
    got = sites(_world_p(), "2026-09-01", "2026-10-31")
    assert got["mode"] == "period"
    assert [figures(r)[:4] for r in got["rows"]] == [
        ("Kobo", "$3,131.00 against a target of $2,890.00", "+$241.00", "No driver widens the gap"),
        ("Mto", "$2,340.00 against a target of $1,830.00", "+$510.00", "Revenue −$160.00"),
        ("Kisiwa", "$3,392.20 against a target of −$130.00", "+$3,522.20", "Revenue −$110.00")]
    assert all(r["months_text"] is None for r in got["rows"])
    e2 = period(_world_p(), "2026-09-01", "2026-10-31")["body"]["tiles"][1]
    assert got["total"] == {"gap": "+$4,273.20", "word": e2["word"]} and e2["value"] == "+$4,273.20"
    assert got["headline"]["text"] == "Every Site is on or above target in September and October"


def test_8_a_site_compared_in_one_month() -> None:
    months = _world_p()
    sep = months["2026-09"]
    mto = sep.snapshot.sites["MTO-001"]
    # "Targets emptied": every target value withdrawn (an empty mapping breaks 5b's own bridge, not this view).
    values = {k: replace(f, value=None) for k, f in mto.targets.structure.values.items()}
    empty = replace(mto, targets=replace(mto.targets, structure=replace(mto.targets.structure, values=values)))
    months["2026-09"] = replace(sep, snapshot=replace(sep.snapshot, sites={**sep.snapshot.sites, "MTO-001": empty}))
    assert V._View(months["2026-09"], NOT_MATCHED, NAMES, "2026-09").R.k == 2  # shown in the packet
    got = sites(months, "2026-09-01", "2026-10-31")
    mto_row = next(r for r in got["rows"] if r["site"] == "Mto")
    assert mto_row["months_text"] == "Compared in 1 of 2 months"
    assert (mto_row["gap"], mto_row["contribution"]) == ("+$255.00", "$1,170.00 against a target of $915.00")
    z = P.Sums(read_of(months)._months(LAKESIDE, ("2026-09", "2026-10")), NAMES)
    assert P.exact_sum([S._Site(z, r.code).effect for r in REFS]) == P.exact_sum([R.effect for R in z.Rs])


# --- 9: the frontend fixtures are the view's (R8) ----------------------------------------------------------------

#: The IA-P fixture estate's other two Sites (`fixtures/iap/portfolio.json`), so the frontend's fixtures carry a
#: cold-chain and an EV row (MD-IAP-12) and E0's `waiting_by_site` keys are E1's codes (R8).
FIXTURE_REFS = (*REFS, SiteRef("COLD-001", "Cold Room", "COLDCHAIN"), SiteRef("EV-001", "Charge Hub", "EV_CHARGING"))


def _fixture_bodies() -> dict:
    return {"sites-2026-10.json": sites({"2026-10": world("A")[0]}, "2026-10-01", "2026-10-31", FIXTURE_REFS),
            "sites-2026-09-10.json": sites(_world_p(), "2026-09-01", "2026-10-31", FIXTURE_REFS),
            "sites-none-2026-11.json": sites({}, "2026-10-01", "2026-10-31", FIXTURE_REFS),
            # IA-P3 P4b (pre-flight Q9; D-IAP.25, D-IAP.26): World G names Thika on the Sites list and Outcomes.
            "sites-g-2026-10.json": sites({"2026-10": world("G")[0]}, "2026-10-01", "2026-10-31", (*REFS, THIKA)),
            "sites-g-2026-09-10.json": sites(_world_p("G"), "2026-09-01", "2026-10-31", (*REFS, THIKA))}


def test_9_fixtures_are_current() -> None:
    bodies = _fixture_bodies()
    if os.environ.get("IAP_WRITE_FIXTURES") == "1":
        for name, body in bodies.items():
            (FIXTURES / name).write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, body in bodies.items():
        assert json.loads((FIXTURES / name).read_text(encoding="utf-8")) == body, name
    portfolio = json.loads((FIXTURES / "portfolio.json").read_text(encoding="utf-8"))
    codes = {r["site_code"] for r in bodies["sites-2026-10.json"]["rows"]}
    assert set(portfolio["summary"]["waiting_by_site"]) <= codes
