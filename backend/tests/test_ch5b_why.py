"""CH-5b2 L0 (build sheet CH-5b §5 item 1; rulings CH5b2-R): the "Why?" trace and the stored chain routes' 304.

- `why.trace` over fixture inputs for each category x Site type (a COMPLETE week), GAP-K7 (NO_DATA) ->
  `why.change.days`, an open thread with no Action -> `why.change.action`, CHANGE_APPLIED -> `why.change.verdict`;
  every non-root node has an id (Q3); `text` equals the §2.3 / CH5b2-R literals; the estate text sums no money.
- The routes over the CH-5a2 fixture app (`test_ch5a2_contract`): `CATEGORY_UNKNOWN` 422, `Cache-Control` on every
  route, no ETag with the store off; and with an in-memory store, a `304` on every one of the five routes answered
  with no composition (no read in the request's ledger), `*` only on a live row, a weak tag never matching.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from datetime import date, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import test_ch5a1_board_contract as BC
import test_ch5a2_contract as C2
from assetops_backend import read_scope
from assetops_backend.chain import why
from assetops_backend.chain.composition import chain_policy_versions, thread_lifecycle_policy
from assetops_backend.chain.grading import COMPLETE, LOW, NO_DATA, NOT_EXPECTED, PARTIAL, PENDING
from assetops_backend.chain.measures import measures_for
from assetops_backend.chain.read import SITE_TYPE_OF_DOMAIN, DayFacts
from assetops_backend.chain.response_store import HEADER, ResponseStore, tag_matches
from assetops_backend.chain_api import build_chain_router
from assetops_backend.outcomes.catalogue import CATEGORIES, COLD, EV, MINI
from assetops_backend.outcomes.display_code import display_code
from assetops_backend.outcomes.outcome_map import categories_for, thread_signal_key
from assetops_backend.site_outcomes.read import SiteOutcomeBoardService

MECHANISMS = {MINI: ("GENERATOR_SUPPORT_CANDIDATE", "PRODUCTIVE_USE_HEADROOM"),
              COLD: ("COLD_START_FAILURE", "COLD_EXCURSION"), EV: ("EV_INTERRUPTION",)}
NAMES = {MINI: "Kobo", COLD: "GreenHarvest", EV: "Depot"}
CLEAN = dict(thread_lifecycle_policy().clean_day_measures)
D1 = date(2026, 10, 1)


def _measures(domain: str) -> tuple[str, ...]:
    return tuple(m.key for m in measures_for(SITE_TYPE_OF_DOMAIN[domain]))


def _facts(domain: str, grades: list[str]) -> DayFacts:
    days = tuple(D1 + timedelta(days=i) for i in range(len(grades)))
    per = {d: {m: {"site": g} for m in _measures(domain)} for d, g in zip(days, grades) if g is not None}
    return DayFacts(days, per, True, "FULL", ())


def _thread(domain: str, mech: str, tid: str, state: str, fids: tuple[str, ...] = ("f1",)) -> dict[str, Any]:
    return {"id": tid, "mechanism": mech, "categories": categories_for(thread_signal_key(mech), domain),
            "state": state, "since": "2026-10-01",
            "occurrences": [{"finding_id": f, "opportunity_id": None, "code": None,
                             "day": (D1 + timedelta(days=i)).isoformat()} for i, f in enumerate(fids)]}


def _input(domain: str, category: str, facts: DayFacts, threads=(), actions=(), row=None, tf=None):
    return why.SiteTraceInput(site_code=f"{domain}-1", site_name=NAMES[domain], domain=domain, category=category,
                              row=row or {"state": "ON_TRACK", "state_label": "On track"}, facts=facts,
                              site_measures=_measures(domain), threads=list(threads), actions=list(actions),
                              clean_measures=CLEAN, trace_facts=tf or {})


def _non_root_have_ids(t: why.Trace) -> None:
    assert t.nodes[0]["kind"] == "row_state"
    assert all(n["ids"] for n in t.nodes[1:]), t.nodes
    assert all(set(n) == {"kind", "label_key", "ids", "basis", "grade"} for n in t.nodes)


@pytest.mark.parametrize("domain", [MINI, COLD, EV])
@pytest.mark.parametrize("category", CATEGORIES)
def test_complete_week_for_each_category_and_site_type(domain: str, category: str) -> None:
    threads = [_thread(domain, m, f"t{i}", "RESOLVED_MONITORING", (f"f{i}",)) for i, m in enumerate(MECHANISMS[domain])]
    actions = [{"id": f"a{i}", "code": f"ACT-00000{i}", "thread": f"t{i}", "verification": "VERIFIED"}
               for i in range(len(threads))]
    tf = {f"f{i}": {"revision_id": f"r{i}", "revision_no": 1, "analytic_run_id": f"run{i}", "cited": 3}
          for i in range(len(threads))}
    t = why.trace(_input(domain, category, _facts(domain, [COMPLETE] * 7), threads, actions, tf=tf))
    _non_root_have_ids(t)
    assert t.text["days_used"] == "7 of 7 days checked"
    assert t.text["would_change"] == "New readings that differ"
    assert 1 <= len(t.text["comes_from"]) <= 4
    related = why.related_threads(threads, category)
    used = why.used_measures(related, CLEAN, _measures(domain))
    if not related:
        assert t.text["comes_from"] == ["Nothing has been recorded for this yet"]
        assert [n["kind"] for n in t.nodes] == ["row_state"]
    else:
        kinds = {n["kind"] for n in t.nodes}
        assert {"finding", "thread", "action", "analytic"} <= kinds
        assert ("measure_day" in kinds) == bool(used)
        for m in used:
            assert f"{why.MEASURE_LABEL[m]} on 7 checked days" in t.text["comes_from"]
    assert t.text["title"] == f"{NAMES[domain]} · " + {"GROW_REVENUE": "Grow revenue",
                                                       "OPTIMIZE_COST": "Optimize cost and efficiency",
                                                       "PROTECT_ASSET": "Protect asset and capital",
                                                       "ASSURE_PERFORMANCE": "Assure performance and returns"}[category]
    assert t.text["evidence_label"] == f"{NAMES[domain]} evidence →"
    assert t.text["say"] == "On track"  # Q10: no headline -> the row's state label


def test_gap_k7_no_data_day_is_checking_more_days() -> None:
    gen = _thread(MINI, "GENERATOR_SUPPORT_CANDIDATE", "t1", "OPEN")
    t = why.trace(_input(MINI, "OPTIMIZE_COST", _facts(MINI, [NO_DATA]), [gen]))
    assert t.text["days_used"] == "1 Oct: too little data, not counted"
    assert t.text["would_change"] == "Checking 1 more day"
    # a missing snapshot row is NO_DATA too (Q9), and LOW is not counted as checked (CH5b2-R Q6, `readiness_of`)
    assert why.trace(_input(MINI, "OPTIMIZE_COST", _facts(MINI, [None]), [gen])).text["days_used"] \
        == "1 Oct: too little data, not counted"
    assert why.trace(_input(MINI, "OPTIMIZE_COST", _facts(MINI, [LOW]), [gen])).text["days_used"] \
        == "1 Oct: too little data, not counted"


@pytest.mark.parametrize("grade,line", [(COMPLETE, "1 Oct checked"), (PARTIAL, "1 Oct partly checked"),
                                        (PENDING, "1 Oct: not in yet")])
def test_one_day_lines(grade: str, line: str) -> None:
    assert why.trace(_input(EV, "PROTECT_ASSET", _facts(EV, [grade]))).text["days_used"] == line


def test_several_days_line_counts_each_class_and_skips_not_expected() -> None:
    facts = _facts(MINI, [COMPLETE, COMPLETE, COMPLETE, PARTIAL, LOW, NO_DATA, PENDING, NOT_EXPECTED])
    t = why.trace(_input(MINI, "OPTIMIZE_COST", facts))
    assert t.text["days_used"] == ("3 of 7 days checked · 1 partly checked · 2 with too little data, not counted"
                                   " · 1 not in yet")
    assert t.text["would_change"] == "Checking 4 more days"


def test_open_thread_without_an_action_needs_an_agreed_action() -> None:
    gen = _thread(MINI, "GENERATOR_SUPPORT_CANDIDATE", "t1", "OPEN")
    t = why.trace(_input(MINI, "OPTIMIZE_COST", _facts(MINI, [COMPLETE] * 3), [gen]))
    assert t.text["would_change"] == "An agreed action"
    assert t.text["comes_from"] == ["Generator time beyond need on 3 checked days"]
    assert t.unmatched == 1  # Q8: no board issue for f1, so no finding line


def test_change_applied_needs_the_check_after_the_change() -> None:
    gen = _thread(COLD, "COLD_START_FAILURE", "t1", "CHANGE_APPLIED", ("f1", "f2"))
    act = {"id": "a1", "code": "ACT-000001", "thread": "t1", "verification": None}
    row = {"state": "NEEDS_ATTENTION", "state_label": "Needs attention", "headline": "Backup did not start",
           "issues": [{"kind": "FINDING", "role": "MOVES", "text": "Backup did not start by itself",
                       "ref": {"finding_id": "F2"}}],
           "in_hand": [{"text": "ACT-000001", "state_label": "Change made",
                        "link_ref": {"kind": "ACTION", "site": "COLD-1", "id": "A1"}}]}
    t = why.trace(_input(COLD, "PROTECT_ASSET", _facts(COLD, [COMPLETE] * 2), [gen], [act], row=row))
    assert t.text["would_change"] == "The check after the change"
    assert t.text["say"] == "Backup did not start"  # Q10: the board row's headline verbatim
    assert t.text["comes_from"][-2:] == ["Backup did not start by itself, seen 2 times since 1 Oct",
                                        f"{display_code('ACT-000001')} · Change made"]
    assert t.unmatched == 0
    _non_root_have_ids(t)


def test_opportunity_origin_mini_action_line_or_counted_unmatched() -> None:
    """CH-9b1 merge note: a MINI domain Action on an opportunity thread (no Finding occurrence). With a board `in_hand`
    item for it the trace shows its code and state; without one it is counted unmatched, never an invented line."""
    gen = _thread(MINI, "GENERATOR_SUPPORT_CANDIDATE", "t1", "ACTION_IN_HAND")
    gen["occurrences"] = [{"finding_id": None, "opportunity_id": "o1", "code": None, "day": D1.isoformat()}]
    act = {"id": "a1", "code": "ACT-000007", "thread": "t1", "verification": None}
    row = {"state": "ON_TRACK", "state_label": "On track",
           "in_hand": [{"text": "ACT-000007", "state_label": "In hand",
                        "link_ref": {"kind": "ACTION", "site": "MINI-1", "id": "A1"}}]}
    shown = why.trace(_input(MINI, "OPTIMIZE_COST", _facts(MINI, [COMPLETE] * 3), [gen], [act], row=row))
    assert f"{display_code('ACT-000007')} · In hand" in shown.text["comes_from"]
    assert shown.unmatched == 1  # the opportunity occurrence has no board Finding line; the Action is matched
    bare = why.trace(_input(MINI, "OPTIMIZE_COST", _facts(MINI, [COMPLETE] * 3), [gen], [act]))
    assert all("ACT-" not in line and "Action" not in line for line in bare.text["comes_from"]), bare.text
    assert bare.unmatched == shown.unmatched + 1  # the Action without a board item is counted, not invented
    _non_root_have_ids(shown)


def test_comes_from_is_capped_at_four() -> None:
    threads = [_thread(MINI, "GENERATOR_SUPPORT_CANDIDATE", f"t{i}", "OPEN", (f"f{i}",)) for i in range(5)]
    row = {"state": "x", "state_label": "x", "issues": [{"kind": "FINDING", "role": "MOVES", "text": f"F{i}",
                                                          "ref": {"finding_id": f"f{i}"}} for i in range(5)]}
    t = why.trace(_input(MINI, "OPTIMIZE_COST", _facts(MINI, [COMPLETE]), threads, row=row))
    assert len(t.text["comes_from"]) == 4 and t.text["comes_from"][0].startswith("Generator time beyond need")


def test_estate_text_sums_no_money_and_picks_the_first_real_change() -> None:
    gen = _thread(MINI, "GENERATOR_SUPPORT_CANDIDATE", "t1", "OPEN")
    kobo = why.trace(_input(MINI, "OPTIMIZE_COST", _facts(MINI, [COMPLETE]), [gen]))
    cold = why.trace(_input(COLD, "OPTIMIZE_COST", _facts(COLD, [COMPLETE])))
    text = why.estate_text("OPTIMIZE_COST", [("GreenHarvest", cold), ("Kobo", kobo)])
    assert text["say"] == "Optimize cost and efficiency at 2 sites"
    assert text["comes_from"] == ["GreenHarvest: On track", "Kobo: On track"]
    assert text["days_used"] == "GreenHarvest: 1 Oct checked · Kobo: 1 Oct checked"
    assert text["would_change"] == "An agreed action"
    assert text["evidence_ref"] == {"kind": "ESTATE", "view": "findings"}
    assert "money" not in repr(text) and "amount" not in repr(text)


def test_estate_text_takes_the_cards_days_and_the_windows_open_days() -> None:
    """CH6b3-R3 M2: `days_used` replaces the per-Site join; `window_open` replaces the board-day count in
    "Checking n more days", and a Site with none open is skipped."""
    base = {"say": "s", "comes_from": [], "days_used": "board day", "evidence_ref": {}, "evidence_label": "e"}
    def trace(open_days, change):
        return why.Trace({**base, "would_change": change}, [], 0, open_days)
    kobo = trace(32, "Checking 32 more days")
    cold = trace(0, "An agreed action")
    sites = [("Kobo", kobo), ("Cold", cold)]
    assert why.estate_text("PROTECT_ASSET", sites)["would_change"] == "Checking 32 more days"      # unchanged default
    assert why.estate_text("PROTECT_ASSET", sites)["days_used"] == "Kobo: board day · Cold: board day"
    text = why.estate_text("PROTECT_ASSET", sites, None, "Kobo: 3 of 7 days checked", {"Kobo": 1})
    assert text["would_change"] == "Checking 1 more day" and text["days_used"] == "Kobo: 3 of 7 days checked"
    skipped = why.estate_text("PROTECT_ASSET", sites, None, "x", {"Kobo": 0})
    assert skipped["would_change"] == "An agreed action"


def test_category_outside_the_four_is_refused() -> None:
    with pytest.raises(why.CategoryUnknown):
        why.check_category("GROW")


# ---- the routes --------------------------------------------------------------------------------------------------

class Port(C2.Port):
    def trace_facts(self, tenant_id, site_id, finding_ids, known_at):
        self.calls.append(("trace_facts", (site_id, tuple(finding_ids))))
        return {f: {"revision_id": f"r-{f}", "revision_no": 1, "analytic_run_id": "run-1", "cited": 2}
                for f in finding_ids}


class Rows:
    """An in-memory `chain_response` port (the `PostgresResponseRows` shape)."""

    def __init__(self) -> None:
        self.rows: dict[tuple, tuple[bytes, str]] = {}
        self.w = "cic:1"

    def read(self, work):
        rows, w = self.rows, self.w

        class Snap:
            def watermark(self, tenant_id, site_ids):
                return w

            def sites(self, tenant_id):
                return [(str(s.site_id), s.site_code, s.timezone or "UTC") for s in (BC.KOBO, BC.COLD, BC.EV)]

            def lookup(self, route, key, watermark, version, now):
                return rows.get((route, key, watermark, version))

        return work(Snap())

    def insert(self, tenant_id, watermark, version, build_ms, until, items, now=None):
        for route, key, tag, body in items:
            self.rows[(route, key, watermark, version)] = (body, tag)
        return {r for r, *_ in items}

    def prune(self, keep):
        return 0

    def dispose(self):
        pass


def _client(responses=None) -> TestClient:
    services = replace(BC.services(Port(), []), threads=C2.Threads())
    app = FastAPI()
    app.include_router(build_chain_router(SiteOutcomeBoardService(services), C2.Registry(), estate=C2.EstateScope(),
                                          tenant=lambda: BC.TENANT, policy_versions=chain_policy_versions,
                                          lifecycle=thread_lifecycle_policy, responses=responses))
    return TestClient(app)


K = {"known_at": "2026-11-03T12:00:00Z"}
WEEK = {"from": "2026-10-25T00:00:00Z", "to": "2026-11-01T00:00:00Z", **K}
ROUTES = {
    "site_chain": ("/api/sites/KOBO-001/chain", {"date": "2026-11-01", **K}),
    "site_why": ("/api/sites/KOBO-001/chain/why", {"date": "2026-11-01", "category": "OPTIMIZE_COST", **K}),
    "thread": (f"/api/sites/KOBO-001/threads/{C2.T1}", K),
    "estate_chain": ("/api/estate/chain", WEEK),
    "estate_why": ("/api/estate/chain/why", {**WEEK, "category": "OPTIMIZE_COST"}),
}


def _get(c: TestClient, name: str, **kw: Any):
    path, params = ROUTES[name]
    return c.get(path, params=params, **kw)


def test_site_why_body_shape() -> None:
    r = _get(_client(), "site_why")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["schema_version"] == "outcome-chain-why-1" and body["category"] == "OPTIMIZE_COST"
    assert set(body["text"]) == {"title", "say", "comes_from", "days_used", "would_change", "evidence_ref",
                                 "evidence_label"}
    assert body["text"]["title"] == "Kobo · Optimize cost and efficiency"
    assert all(n["ids"] for n in body["nodes"][1:]) and body["nodes"][0]["kind"] == "row_state"
    assert {"thread", "finding", "analytic"} <= {n["kind"] for n in body["nodes"]}


def test_estate_why_has_a_trace_per_site_and_no_money() -> None:
    body = _get(_client(), "estate_why").json()
    assert [s["code"] for s in body["sites"]] == ["KOBO-001", "COLD-LAB-001", "EV-LAB-001"]
    assert body["text"]["say"] == "Optimize cost and efficiency at 3 sites"
    assert "money" not in repr(body) and "amount" not in repr(body)


@pytest.mark.parametrize("category", ["PROTECT_ASSET", "OPTIMIZE_COST", "ASSURE_PERFORMANCE"])
def test_estate_why_days_are_the_cards_days_and_never_the_board_days(category) -> None:
    """CH6b3-R3 M2 (route test): on a month window the "Why?" `days_used` equals the card's `days_line`
    (Optimize has none: Protect's), and "Checking n more days" is not the board day's 32-day count."""
    month = {"from": "2026-10-01T00:00:00Z", "to": "2026-11-01T00:00:00Z", **K}
    c = _client()
    cards = c.get("/api/estate/chain", params=month).json()["cards"]
    want = (cards.get(category) or {}).get("days_line") or cards["PROTECT_ASSET"]["days_line"]
    text = c.get("/api/estate/chain/why", params={**month, "category": category}).json()["text"]
    assert text["days_used"] == want
    assert "32" not in text["would_change"]


@pytest.mark.parametrize("path,params", [("/api/sites/KOBO-001/chain/why", {"date": "2026-11-01"}),
                                         ("/api/sites/KOBO-001/chain/why", {"date": "2026-11-01", "category": "X"}),
                                         ("/api/estate/chain/why", {**WEEK, "category": "grow"})])
def test_category_unknown_is_422(path, params) -> None:
    r = _client().get(path, params=params)
    assert r.status_code == 422 and r.json()["detail"]["code"] == "CATEGORY_UNKNOWN", r.text
    assert r.headers["Cache-Control"] == "private, no-cache"


@pytest.mark.parametrize("name", sorted(ROUTES))
def test_store_off_has_cache_control_and_no_etag(name: str) -> None:
    r = _get(_client(), name)
    assert r.status_code == 200, r.text
    assert r.headers["cache-control"] == "private, no-cache" and "etag" not in r.headers


@pytest.mark.parametrize("name", sorted(ROUTES))
def test_compose_only_store_sends_no_etag_so_no_304(name: str) -> None:
    c = _client(ResponseStore(Rows(), lambda: "v1", compose_only=True))
    r = _get(c, name, headers={"If-None-Match": "*"})
    assert r.status_code == 200 and "etag" not in r.headers and r.headers[HEADER] == "composed"


def _spied(monkeypatch) -> list:
    """Every compose scope opened (`ResponseStore._composed` opens `read_scope.fresh` before any compose read)."""
    seen: list = []
    real = read_scope.fresh

    @contextmanager
    def spy(route):
        with real(route) as sc:
            seen.append(sc)
            yield sc

    monkeypatch.setattr(read_scope, "fresh", spy)
    return seen


@pytest.mark.parametrize("name", sorted(ROUTES))
def test_304_on_every_route_with_no_composition(name: str, monkeypatch) -> None:
    rows = Rows()
    c = _client(ResponseStore(rows, lambda: "v1"))
    path, params = ROUTES[name]
    assert c.get(path, params={**params}, headers={"If-None-Match": "*"}).headers[HEADER] == "stored"  # no row yet
    first = c.get(path, params=params)
    assert first.status_code == 200 and first.headers[HEADER] == "hit"
    tag = first.headers["etag"]
    assert first.headers["cache-control"] == "private, no-cache"
    seen = _spied(monkeypatch)
    for header in (tag, f'"other", {tag}', "*"):
        r = c.get(path, params=params, headers={"If-None-Match": header})
        assert r.status_code == 304 and r.content == b"" and r.headers["etag"] == tag, (header, r.status_code)
        assert r.headers["cache-control"] == "private, no-cache"
    assert seen == []  # no compose scope was opened, so nothing was composed or read for the three 304s
    assert c.get(path, params=params, headers={"If-None-Match": "W/" + tag}).status_code == 200  # weak: no match
    assert seen == []  # a hit with a body still composes nothing
    rows.rows.clear()  # `*` with no live row composes
    assert c.get(path, params=params, headers={"If-None-Match": "*"}).status_code == 200 and len(seen) == 1
    rows.w = "cic:2"  # a new watermark: the old tag is not live, so a full body
    again = c.get(path, params=params, headers={"If-None-Match": tag})
    assert again.status_code == 200 and again.headers["etag"] != tag


def test_tag_matching_rules() -> None:
    assert tag_matches('"abc"', "abc") and tag_matches('"x", "abc"', "abc") and tag_matches("*", "abc")
    assert not tag_matches('W/"abc"', "abc") and not tag_matches('"abcd"', "abc") and not tag_matches(None, "abc")
