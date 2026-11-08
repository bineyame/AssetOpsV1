"""DEMO-A U6 / DEMO-SPARSE U6: the combined demo dataset's acceptance rows (build sheet DEMO-SPARSE §5, DEMO-COMBINED
§4), read through the served app in process (`host/lab_app.py` `app`, `TestClient`).

    python tools/demo_combined_finish.py check <database-url> <work>

`tools/demo_combined.py prepare` runs `check` as its last step (the self-check child) and fails the prepare on any
failed row; `backend/tests/test_demo_combined_postgres.py` imports `CHECKS` and runs each row as its own test. Rows
marked `idx` need IDX-GAPS (`assetops_backend.analytics.finding_index.POLICY_VERSION == "finding-index/2"`): until it
is present the self-check records them `skipped` and the build test skips them (at merge none may skip). SP-7 writes
to the dataset (add-day, tick), so it is a build-test row only (`mutates`).

Writes `<work>/check.json`: one entry per row with its status and the values it read.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

import demo_combined_rows as demo_rows
from assetops_backend.outcomes.display_code import display_code
from assetops_backend.site_outcomes.board import (
    OPP_THREAD_CLOSED, OPP_THREAD_MONITORING, OPP_THREAD_SEEN_AGAIN, THREAD_AFTER_JUDGED, THREAD_AFTER_NOT_JUDGED,
    THREAD_BEFORE)

KOBO, COLD, EV = "KOBO-001", "COLD-LAB-001", "EV-LAB-001"
CATEGORIES = ["GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"]
SAFEGUARD = " · checked here as a safeguard"
OUTSIDE = " · linked finding outside this view"
#: POLISH PA-2a (review M2): the trial cost line prefix, `site_outcomes/board.py` COST_PREFIX (was "not realised savings").
NOT_REALISED = "Estimated effect of the trial (not money saved): "
GAPS_TEXT = "{g} of the last 31 days have no checked readings yet"
IDX_POLICY = "finding-index/2"
#: U1 probe, `.agent/DEMO-SPARSE-trial-probe.md` P3 row (a): the chosen candidate and its recorded cost check.
#: FUEL-1 A3-R §3.9: with the declared idle fuel rate the trial hour is a `/2` MODELLED_IMPROVEMENT (was
#: MODELLED_NO_IMPROVEMENT, nominal 0); the figures are checked from stored values (`demo_rows.trial_cost`).
PROBE_CHOSEN = {"chosen": "a", "window_hour": "06:00", "cost_state": "MODELLED_IMPROVEMENT"}
#: A3-R §3.9: the three idle mornings (the probe's 200 min of Candidate time at 0 kW each).
IDLE_MORNINGS = (-14, -7, 0)


def idx_present() -> bool:
    from assetops_backend.analytics import finding_index

    return getattr(finding_index, "POLICY_VERSION", None) == IDX_POLICY


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_aligned_window(lo: datetime, hi: datetime) -> tuple[datetime, datetime]:
    """Estate scope accepts only UTC-midnight bounds: widen [lo, hi) to the UTC midnight at/before lo and at/after hi."""
    lo, hi = lo.astimezone(timezone.utc), hi.astimezone(timezone.utc)
    start = lo.replace(hour=0, minute=0, second=0, microsecond=0)
    end = hi.replace(hour=0, minute=0, second=0, microsecond=0)
    if end < hi:
        end += timedelta(days=1)
    return start, end


def at(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


@dataclass
class Ctx:
    client: Any
    work: Path
    story: dict = field(default_factory=dict)
    days: list = field(default_factory=list)
    docs: dict = field(default_factory=dict)
    cache: dict = field(default_factory=dict)
    url: str = ""

    @property
    def S(self) -> datetime:
        return at(self.story["S"])

    def day(self, offset: int) -> datetime:
        return self.S + timedelta(days=offset)

    def get(self, path: str, **params) -> dict:
        key = (path, tuple(sorted(params.items())))
        if key not in self.cache:
            r = self.client.get(path, params=params)
            assert r.status_code == 200, (path, params, r.status_code, r.text[:400])
            self.cache[key] = r.json()
        return self.cache[key]

    def board(self, code: str, lo: datetime, hi: datetime) -> dict:
        if code == KOBO:
            return self.get(f"/api/sites/{code}/outcome-board", date=lo.date().isoformat())
        return self.get(f"/api/sites/{code}/outcome-board", **{"from": iso(lo), "to": iso(hi)})

    def site_days(self, site: str) -> list[dict]:
        return [d for d in self.days if d["site"] == site]

    def site_day(self, site: str, kind: str) -> dict:
        return next(d for d in self.site_days(site) if d["kind"] == kind)

    def window(self, site: str, kind: str) -> tuple[datetime, datetime]:
        d = self.site_day(site, kind)
        return at(d["start"]), at(d["end"])


def rows(body: dict) -> dict[str, dict]:
    return {r["category"]: r for r in body["rows"]}


def items(row: dict) -> list[dict]:
    return [*row.get("issues", []), *row.get("in_hand", []), *row.get("earlier", []), *row.get("options", [])]


def finding_issues(row: dict, finding_id: str) -> list[dict]:
    return [i for i in row.get("issues", []) if i.get("kind") == "FINDING"
            and str((i.get("ref") or {}).get("finding_id")) == finding_id]


def walk(node: Any):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk(v)


CHECKS: list[tuple[str, bool, bool, Callable[[Ctx], dict]]] = []


def row(check_id: str, *, idx: bool = False, mutates: bool = False):
    def wrap(fn):
        CHECKS.append((check_id, idx, mutates, fn))
        return fn
    return wrap


# ---- Kobo (mini) ------------------------------------------------------------------------------------------------

def _kobo_board_s(ctx: Ctx) -> dict:
    return ctx.board(KOBO, ctx.S, ctx.day(1))


def _kobo_board_s1(ctx: Ctx) -> dict:
    return ctx.board(KOBO, ctx.day(1), ctx.day(2))


#: POLISH Addendum 10: verification outcomes that are final; a finished trial is listed under Earlier.
FINAL_VERIFICATION = frozenset({"VERIFIED", "INEFFECTIVE", "INCONCLUSIVE"})


def cost_row_action_links(cost: dict, action_id: str, action_code: str, verification_state: str | None):
    """CO-1's linkage assertions on day S's OPTIMIZE_COST row (POLISH Addendum 10, correcting Addendum 9 Q4).
    1. The Action is linked by href path `/sites/KOBO-001/actions/{id}`: under `earlier` when its verification outcome
       is final, else under `issues` + `in_hand`. A text match alone never passes (DEMO-A L2).
    2. Must-not-harm (LINK-LINEAGE): its href carries the Action id and the verification event; its text names the
       Action by display code. This is the guard that fails on the board from before LINK-LINEAGE, whose CO-3
       `earlier` line already carried the Action href (DEMO-A L2 review).
    3. The safeguards sentence (DEMO-A L1). Returns (must_not_harm, the linked items' texts)."""
    mnh = cost.get("must_not_harm") or {}
    href, text = mnh.get("href") or "", mnh.get("text") or ""
    assert action_id in href and "/verification?event_id=" in href, mnh
    assert display_code(action_code) in text, mnh
    assert "Reliable service and battery and generator life" in text, mnh
    path = f"/sites/{KOBO}/actions/{action_id}"
    column = (cost.get("earlier", []) if verification_state in FINAL_VERIFICATION
              else [*cost.get("issues", []), *cost.get("in_hand", [])])
    linked = [i.get("text") for i in column if (i.get("href") or "").split("?")[0] == path]
    assert linked, (verification_state, items(cost))
    return mnh, linked


@row("CO-1", idx=True)
def co1(ctx: Ctx) -> dict:
    k = ctx.docs["kobo"]
    body = _kobo_board_s(ctx)
    r = rows(body)
    cost, protect = r["OPTIMIZE_COST"], r["PROTECT_ASSET"]
    moves = finding_issues(cost, k["finding"])
    checked = [i for i in finding_issues(protect, k["finding"]) if i["text"].endswith(SAFEGUARD)]
    assert moves, cost["issues"]
    assert checked, protect["issues"]
    state = ((_action(ctx).get("verification") or {}).get("state")) or None
    mnh, on_cost_row = cost_row_action_links(cost, k["action"], k["action_code"], state)
    outside = [i["text"] for x in body["rows"] for i in items(x) if i["text"].endswith(OUTSIDE)]
    assert outside == [], outside
    # FIX-MAIN-1 R1 (Architect; expectation owner CH-3): since CH-3 the board reads "applied" from the thread state on
    # the board day, and the change is applied from the Site-local day of the Action's effective_from (after S). On
    # day S the primary Finding is therefore still open, and the row carries the thread's "Before the change" line.
    e = _kobo_change_day(ctx)
    assert e > ctx.S.astimezone(_kobo_zone(ctx)).date(), ("change day not after S", e, ctx.story["S"])
    outcomes = {o["key"]: (o["state"], o.get("reason")) for o in cost["outcomes"]}
    mg2 = outcomes.get("MG-2")
    assert mg2 == ("NEEDS_ATTENTION", "PRIMARY_FINDING_OPEN"), outcomes
    assert cost["state"] == "NEEDS_ATTENTION", (cost["state"], mg2)
    label = f"{e.day} {e:%b}"
    before = THREAD_BEFORE.format(e=label)
    after_prefix = THREAD_AFTER_JUDGED.split("{")[0]
    subline = cost.get("subline") or ""
    if before + THREAD_AFTER_NOT_JUDGED.format(e=label) in subline:
        after = "THREAD_AFTER_NOT_JUDGED"
    elif re.search(re.escape(before + after_prefix) + r".+ from \d{1,2} [A-Z][a-z]{2}", subline):
        after = "THREAD_AFTER_JUDGED"
    else:
        raise AssertionError(("no thread before-the-change line", before, subline))
    return {"cost_state": cost["state"], "finding": k["finding"], "must_not_harm": mnh,
            "action_on_cost_row": on_cost_row, "mg2": mg2, "change_day": e.isoformat(), "thread_after": after,
            "subline": subline, "r552": "resolved: refresh lineage"}


def _kobo_zone(ctx: Ctx):
    from zoneinfo import ZoneInfo

    if "kobo_zone" not in ctx.cache:
        site = ctx.get(f"/api/sites/{KOBO}")
        zone = next((n["timezone"] for n in walk(site) if isinstance(n.get("timezone"), str)), None)
        assert zone, ("no Site timezone", site)
        ctx.cache["kobo_zone"] = zone
    return ZoneInfo(ctx.cache["kobo_zone"])


def _kobo_change_day(ctx: Ctx):
    """The Site-local day of the story's Kobo Action effective_from: the thread's CHANGE_APPLIED day."""
    return at(ctx.story["kobo"]["action"]["effective_from"]).astimezone(_kobo_zone(ctx)).date()


@row("CO-1b", idx=True)
def co1b(ctx: Ctx) -> dict:
    """FIX-MAIN-1 R1: on S+1 (from the change day on) the Finding no longer holds an open primary signal, and the
    board carries the thread's monitoring line for the verified fix."""
    k = ctx.docs["kobo"]
    body = _kobo_board_s1(ctx)
    cost = rows(body)["OPTIMIZE_COST"]
    open_primary = [o for o in cost["outcomes"] if o.get("reason") == "PRIMARY_FINDING_OPEN"]
    assert not open_primary, (k["finding"], open_primary)
    want = "Fix verified, monitoring (" + display_code(k["action_code"]) + ")"
    texts = [v for n in walk(body) for v in n.values() if isinstance(v, str) and want in v]
    assert texts, (want, [r.get("subline") for r in body["rows"]])
    return {"cost_state": cost["state"], "monitoring": texts[0]}


@row("CO-2", idx=True)
def co2(ctx: Ctx) -> dict:
    k = ctx.docs["kobo"]
    ov = ctx.get(f"/api/sites/{KOBO}/overview", date=ctx.S.date().isoformat())
    assert ov["freshness"]["state"] == "CURRENT", ov["freshness"]
    index = ctx.get(f"/api/sites/{KOBO}/finding-index", domain="mini-grid-dispatch",
                    **{"from": iso(ctx.S), "to": iso(ctx.day(1))})
    assert index["status"] in ("CURRENT", "PARTIAL"), (index["status"], index.get("status_reasons"))
    assert k["finding"] in [str(x["finding_id"]) for x in index["rows"]], index["rows"]
    unsettled = [(o["key"], o.get("reason")) for x in _kobo_board_s(ctx)["rows"] for o in x["outcomes"]
                 if o["state"] == "UNKNOWN" and "unsettled" in (o.get("reason") or "")]
    assert not unsettled, unsettled
    return {"overview": ov["freshness"]["state"], "index": index["status"]}


def _action(ctx: Ctx) -> dict:
    return ctx.get(f"/api/sites/{KOBO}/actions/{ctx.docs['kobo']['action']}")


@row("CO-3", idx=True)
def co3(ctx: Ctx) -> dict:
    cc = (_action(ctx).get("verification") or {}).get("cost_check") or {}
    assert cc.get("state"), cc
    earlier = rows(_kobo_board_s(ctx))["OPTIMIZE_COST"]["earlier"]
    lines = [e.get("detail") for e in earlier if NOT_REALISED in (e.get("detail") or "")]
    assert lines, earlier
    return {"cost_check": cc.get("state"), "line": lines[0]}


@row("CO-5/SP-1", idx=True)
def sp1(ctx: Ctx) -> dict:
    cost = rows(ctx.board(KOBO, ctx.day(-28), ctx.day(-27)))["OPTIMIZE_COST"]
    day = next(d for d in ctx.docs["kobo"]["days"] if d["offset"] == -28)
    outcomes = {o["key"]: (o["state"], o.get("reason")) for o in cost["outcomes"]}
    if not day.get("findings"):  # U1 P1 gave the normal day 0 avoidable minutes: no Finding
        # DD1b2-R10: S-28 is a story-only 03:00-11:00Z run on Kobo's 24 h calendar (CH-1a), so the reading is not
        # complete and the objective is NOT_JUDGED. On track, or Unknown only with OBJECTIVE_NOT_JUDGED.
        assert cost["state"] in ("ON_TRACK", "UNKNOWN"), (cost["state"], outcomes)
        unknown = demo_rows.unknown_only_not_judged(outcomes)
        assert cost["state"] == "ON_TRACK" or unknown, ("UNKNOWN state with no not-judged outcome", outcomes)
        branch = "ON_TRACK" if cost["state"] == "ON_TRACK" else "NOT_JUDGED"
    else:  # R585 stays standing: record the measured values
        assert all(s != "UNKNOWN" for s, _ in outcomes.values()), outcomes
        branch = "R585_STANDING"
    return {"branch": branch, "state": cost["state"], "outcomes": outcomes}


@row("SP-3", idx=True)
def sp3(ctx: Ctx) -> dict:
    body = _kobo_board_s(ctx)
    gaps = next((n["finding_gaps"] for n in walk(body) if isinstance(n.get("finding_gaps"), dict)), None)
    assert gaps is not None, "no finding_gaps on the Kobo board"
    lo = ctx.day(-30).date()
    assessed = {d["day"] for d in ctx.site_days("kobo") if d["received_at"] is not None and lo <= at(d["day"] + "T00:00:00Z").date()
                <= ctx.S.date()}
    g = 31 - len(assessed)
    assert gaps["text"] == GAPS_TEXT.format(g=g), (gaps["text"], g)
    listed = {str(x)[:10] for x in gaps.get("days") or []}
    assert ctx.day(-10).date().isoformat() in listed, listed
    assert not (listed & assessed), listed & assessed
    return {"text": gaps["text"], "g": g}


@row("SP-4", idx=True)
def sp4(ctx: Ctx) -> dict:
    index = ctx.get(f"/api/sites/{KOBO}/finding-index", domain="mini-grid-dispatch",
                    **{"from": iso(ctx.day(-30)), "to": iso(ctx.day(1))})
    assert index["status"] == "PARTIAL", index["status"]
    gaps = {str(g.get("day"))[:10]: g.get("state") or g.get("status") for g in index.get("gaps") or []}
    # DD1b2-R10: the index works on UTC days, so a night run that starts at 21:00Z covers the next UTC day. The served
    # gap days must equal the UTC days of the window that no built run touches.
    want_gaps = demo_rows.expected_index_gaps(ctx.site_days("kobo"), ctx.day(-30), ctx.day(1))
    assert want_gaps, "no expected index gap: the set is empty"
    assert sorted(gaps) == want_gaps, (sorted(gaps), want_gaps)
    assert ctx.day(-3).date().isoformat() not in gaps, gaps
    want = {f for d in ctx.docs["kobo"]["days"] if d["offset"] in (-14, -7, 0) for f in d.get("findings") or []}
    got = {str(x["finding_id"]) for x in index["rows"]}
    assert want and want <= got, (want - got)
    return {"status": index["status"], "gaps": gaps, "findings": sorted(want)}


@row("SP-5")
def sp5(ctx: Ctx) -> dict:
    d = ctx.day(-21).date().isoformat()
    day = next(x for x in ctx.docs["kobo"]["days"] if x["offset"] == -21)
    assert day["kind"] == "overcast" and day.get("run_id"), day
    assert not day.get("findings"), day.get("findings")
    body = ctx.get(f"/api/sites/{KOBO}/performance/dispatch/windows/{d}")
    on = [n for n in walk(body) if n.get("first_on") is not None]
    assert on, "no generator interval on the overcast day"
    return {"day": d, "first_on": on[0].get("first_on"), "last_on": on[0].get("last_on")}


@row("SP-6")
def sp6(ctx: Ctx) -> dict:
    k = ctx.docs["kobo"]
    assert k["window_hour"] == PROBE_CHOSEN["window_hour"] and k["trial"]["chosen"] == PROBE_CHOSEN["chosen"], \
        (k["window_hour"], k["trial"])
    cc = (_action(ctx).get("verification") or {}).get("cost_check") or {}
    assert cc.get("state") == PROBE_CHOSEN["cost_state"], cc
    # FUEL-1 A3-R §3.9: the `nominal == 0` check is replaced by the stored-value checks of `demo_rows.trial_cost`
    return {"window_hour": k["window_hour"], "cost_check": cc,
            "trial": demo_rows.trial_cost(cc, _trial_result(ctx))}


def _trial_result(ctx: Ctx) -> dict:
    """FUEL-1 A3-R §3.9: ACT-001's latest stored trial cost row's `result` (SQL)."""
    import psycopg

    with psycopg.connect(ctx.url.replace("+psycopg", "")) as c:
        got = c.execute("SELECT result FROM trial_cost_comparison_revision WHERE action_id = %s "
                        "ORDER BY recorded_at DESC, revision_no DESC LIMIT 1", (ctx.docs["kobo"]["action"],)).fetchone()
    assert got is not None, "no stored trial cost row for the Kobo trial"
    return got[0] if isinstance(got[0], dict) else json.loads(got[0])


# ---- cold and EV -----------------------------------------------------------------------------------------------

@row("CO-5/SP-2")
def sp2(ctx: Ctx) -> dict:
    lo, hi = ctx.window("cold", "normal")
    protect = rows(ctx.board(COLD, lo, hi))["PROTECT_ASSET"]
    outcomes = {o["key"]: (o["state"], o.get("reason")) for o in protect["outcomes"]}
    # DD1b2-R10: the Cold `normal` run (16:00-17:05Z) is not a complete 24 h day, so CC-1/CC-6 are NOT_JUDGED and CC-5
    # has no declared objective; UNKNOWN only with OBJECTIVE_NOT_JUDGED, NO_OBJECTIVE only with NO_OBJECTIVE_DECLARED
    demo_rows.unknown_only_not_judged(outcomes)
    return {"state": protect["state"], "outcomes": outcomes}


@row("CO-7")
def co7(ctx: Ctx) -> dict:
    lo, hi = ctx.window("cold", "failure")
    body = ctx.board(COLD, lo, hi)
    earlier = [e for x in body["rows"] for e in x.get("earlier", []) if e.get("result_label")]
    assert earlier, [x.get("earlier") for x in body["rows"]]
    repeats = [w for w in body["warnings"] if w["kind"] == "REPEATED_MAINTENANCE_NO_RESULT"]
    assert repeats, [w["kind"] for w in body["warnings"]]
    return {"earlier": [(e["text"], e["result_label"]) for e in earlier], "repeat": repeats[0]["title"]}


def _ev_board(ctx: Ctx) -> dict:
    lo, hi = ctx.window("ev", "fault")
    return ctx.board(EV, lo, hi)


def covering(lo: datetime, hi: datetime) -> dict:
    a = lo.replace(hour=0, minute=0, second=0, microsecond=0)
    b = hi.replace(hour=0, minute=0, second=0, microsecond=0)
    b = b if b == hi else b + timedelta(days=1)
    return {"from": iso(a), "to": iso(b)}


@row("CO-9")
def co9(ctx: Ctx) -> dict:
    assure = rows(_ev_board(ctx))["ASSURE_PERFORMANCE"]
    assert assure["state"] != "UNKNOWN", (assure["state"], assure["outcomes"])
    body = ctx.get("/api/estate/portfolio", **covering(*ctx.window("ev", "fault")))
    cells = [x["state"] for o in body["objectives"] if o["site_code"] == EV for x in o["cells"] if x["key"] == "EVIDENCE"]
    assert len(cells) == 1 and cells[0] != "UNKNOWN", cells
    return {"assure": assure["state"], "portfolio_evidence": cells[0]}


@row("CO-10")
def co10(ctx: Ctx) -> dict:
    kobo = [(w["kind"], w["title"]) for w in _kobo_board_s(ctx)["warnings"]]
    assert ("PLAN_DUE_SOON", "Battery capacity test due soon") in kobo, kobo
    ev = [(w["kind"], w["title"]) for w in _ev_board(ctx)["warnings"]]
    assert ("PLAN_OVERDUE", "Connector inspection overdue") in ev, ev
    assert "CHARGER_FAULT_OVERDUE_INSPECTION" in [k for k, _ in ev], ev
    return {"kobo": kobo, "ev": ev}


# ---- estate and every Site -------------------------------------------------------------------------------------

def _estate(ctx: Ctx, lo: datetime, hi: datetime) -> tuple[dict, dict, dict, dict]:
    """(portfolio, outcome summary, Finding coverage by Site code, summary Site by code) over [lo, hi)."""
    days = {"from": iso(lo), "to": iso(hi)}
    body = ctx.get("/api/estate/portfolio", **days)
    summary = ctx.get("/api/estate/outcome-summary", **days)
    code_of = {o["site_id"]: o["site_code"] for o in body["objectives"]}
    coverage = {code_of.get(c["site_id"], c["site_id"]): c for c in (body.get("coverage") or {}).get("sites", [])}
    return body, summary, coverage, {x["site_code"]: x for x in summary["sites"]}


def _cov(c: dict | None) -> dict | None:
    return None if c is None else {k: c.get(k) for k in ("state", "source_freshness", "match_state", "job_state")}


@row("CO-6", idx=True)
def co6(ctx: Ctx) -> dict:
    """Addendum 2 ruling (i) with COV-PARTIAL §6: the week S-6d..S+1d. It always holds the EV fault Tuesday (Tue <= S),
    so cold and EV read their PERIOD (CH6b1-R3: the week, with the contained event window inside it). Kobo's estate coverage on `estate-coverage/2` is PARTIAL: the checked days
    are counted and every day with no run is named in `days.gaps`. The Portfolio status is PARTIAL or UNKNOWN, never
    CURRENT, and since FIX-COLD-DRAIN never PENDING on undrained cold/EV money. Kobo's outcome cells are its day-S
    board (`mini_summary_day(to)` = S for the midnight `to`, `site_outcomes/read.py:138`)."""
    from assetops_backend.estate.coverage import DAYS_CHECKED, DAYS_WITHHELD
    from assetops_backend.estate.money_invariants import double_count_violations

    body, summary, coverage, by_code = _estate(ctx, ctx.day(-6), ctx.day(1))
    codes = sorted({o["site_code"] for o in body["objectives"]})
    assert codes == sorted([KOBO, COLD, EV]), codes
    assert double_count_violations(body, financials=None) == []
    assert summary["objective_site_count"] == 3, summary.get("objective_site_count")
    basis = {code: x.get("window_basis") for code, x in by_code.items()}
    assert basis.get(COLD) == basis.get(EV) == "PERIOD", basis  # CH6b1-R Q2: the requested window
    # the gap days, from the data: Kobo days in the week with no run (so no available selection)
    ran = {d["day"] for d in ctx.site_days("kobo") if d["kind"] != "missing"}
    week = [(ctx.day(n)).date().isoformat() for n in range(-6, 1)]
    unassessed = [d for d in week if d not in ran]
    assert unassessed, (week, sorted(ran))
    kobo = coverage.get(KOBO)
    assert kobo is not None, coverage
    days = kobo.get("days") or {}
    assert kobo["state"] == "PARTIAL", (_cov(kobo), days)
    assert [g["day"] for g in days.get("gaps", [])] == unassessed, (days.get("gaps"), unassessed)
    assert days.get("requested") == 7 and days.get("checked") == 7 - len(unassessed), days
    g = len(unassessed)
    text = DAYS_CHECKED.format(c=7 - g, n=7, g=g, unit="day" if g == 1 else "days")
    if days.get("withheld"):
        text += DAYS_WITHHELD
    assert days.get("text") == text, (days.get("text"), text)
    assert body["status"] in ("PARTIAL", "UNKNOWN") and body["status"] != "CURRENT", (
        body["status"], body.get("coverage", {}).get("state"))
    listed = [r["finding_id"] for r in body.get("rows", []) if r.get("site_code") == KOBO]
    finding_listed = ctx.docs["kobo"]["finding"] in listed
    if not days.get("withheld"):
        assert finding_listed, (listed, body.get("total_count"))
    # DD1b2-R10 (CH-5a1): the Kobo board day is the Site-local day, so its window opens at the Site-local midnight of S
    local_s = iso(demo_rows.site_day_start(ctx.S.date(), _kobo_zone(ctx)))
    assert basis.get(KOBO) == "DAY" and (by_code[KOBO].get("window") or {}).get("from") == local_s, (
        local_s, by_code[KOBO])
    board = {r["category"]: r["state"] for r in _kobo_board_s(ctx)["rows"]}
    cells = {r["category"]: r["state"] for r in by_code[KOBO]["rows"]}
    assert cells == board, (cells, board)
    others = {code: _cov(coverage.get(code)) for code in (COLD, EV)}
    return {"status": body["status"], "kobo_coverage": _cov(kobo), "kobo_days": days,
            "kobo_unassessed_days": unassessed, "kobo_finding_in_rows": finding_listed,
            "cold_ev_coverage": others, "window_basis": basis, "kobo_cells_from_day_S": cells}


@row("CO-6b", idx=True)
def co6b(ctx: Ctx) -> dict:
    """Addendum 2: the day S. Kobo coverage CURRENT; cold PERIOD (the S failure night is the contained event); EV reads what it reads
    with no event on S (PERIOD unless S is a Tuesday): recorded and asserted as given, never forced."""
    body, summary, coverage, by_code = _estate(ctx, ctx.S, ctx.day(1))
    kobo = coverage.get(KOBO)
    assert kobo is not None and kobo["state"] == "CURRENT", _cov(kobo)
    assert (kobo.get("days") or {}).get("gaps") == [], kobo.get("days")
    basis = {code: x.get("window_basis") for code, x in by_code.items()}
    assert basis.get(COLD) == "PERIOD", basis  # CH6b1-R Q2: PERIOD over the requested window
    ev_on_s = any(d["day"] == ctx.S.date().isoformat() and d["kind"] != "missing" for d in ctx.site_days("ev"))
    assert basis.get(EV) == "PERIOD", (basis, ev_on_s)
    ev_cells = {r["category"]: r["state"] for r in by_code[EV]["rows"]}
    ev_portfolio = {x["key"]: x["state"] for o in body["objectives"] if o["site_code"] == EV for x in o["cells"]}
    return {"status": body["status"], "kobo_coverage": _cov(kobo), "window_basis": basis, "ev_event_on_S": ev_on_s,
            "ev_cells": ev_cells, "ev_portfolio_cells": ev_portfolio}


@row("CO-8")
def co8(ctx: Ctx) -> dict:
    body = ctx.get("/api/estate/portfolio", **{"from": iso(ctx.S), "to": iso(ctx.day(1))})
    keys = [f"{r['finding_id']}|{r['finding_revision_id']}" for r in body["rows"]]
    assert keys and all(k.count("|") == 1 and all(k.split("|")) for k in keys), keys
    assert ctx.docs["kobo"]["finding"] in [k.split("|")[0] for k in keys], keys
    return {"keys": keys}


def _boards(ctx: Ctx) -> dict[str, dict]:
    return {KOBO: _kobo_board_s(ctx), COLD: ctx.board(COLD, *ctx.window("cold", "failure")), EV: _ev_board(ctx)}


@row("CO-11")
def co11(ctx: Ctx) -> dict:
    from test_out_c1_never_money import money_hits

    k, c, e = ctx.docs["kobo"]["work"], ctx.docs["cold_work"], ctx.docs["ev_work"]
    counts = {KOBO: (len(k["visits"]), len(k["plans"])), COLD: (len(c["cases"]), len(c["plans"])),
              EV: (len(e["visits"]), len(e["plans"]))}
    assert all(v >= 2 and p >= 1 for v, p in counts.values()), counts
    objectives = {code: len(b.get("objectives") or []) for code, b in _boards(ctx).items()}
    assert all(n >= 1 for n in objectives.values()), objectives
    hits = {code: money_hits(b["warnings"]) for code, b in _boards(ctx).items()}
    assert not any(hits.values()), hits
    return {"visits_plans": counts, "objective_lines": objectives}


@row("CO-12")
def co12(ctx: Ctx) -> dict:
    out = {}
    for code, b in _boards(ctx).items():
        assert [r["category"] for r in b["rows"]] == CATEGORIES, (code, [r["category"] for r in b["rows"]])
        assert b["policy_versions"].get("warnings") and b["policy_versions"].get("objectives"), b["policy_versions"]
        out[code] = {"read_state": b["read_state"], "warnings": sorted({w["kind"] for w in b["warnings"]})}
    assert any(out[code]["warnings"] for code in out), out
    cc = (_action(ctx).get("verification") or {}).get("cost_check") or {}
    assert cc.get("state"), cc
    return out


# ---- WALK1 G1 (build sheet §5): declared prices fill Grow; partly checked weeks are counted -------------------

@row("WK-1")
def wk1(ctx: Ctx) -> dict:
    """WALK1-2: the Depot Grow row carries the estimated charging income at the declared tariff."""
    grow = rows(_ev_board(ctx))["GROW_REVENUE"]
    # DD1b2-R10: the earnings claim decides (CH-6a3 ONE-SOURCE); the fault run is 1 h of the session, so no day counts
    return demo_rows.wk1(grow)


@row("WK-2a")
def wk2a(ctx: Ctx) -> dict:
    """WALK1-3 / D-W1-13: on day S-1 (a cloudy, mill-working day) Kobo's Grow row leads with the estimated
    productive-use sales: 168.3 kWh measured x the declared 0.25 USD/kWh = 42.08 USD."""
    grow = rows(ctx.board(KOBO, ctx.day(-1), ctx.S))["GROW_REVENUE"]
    money = grow.get("headline_money") or {}
    assert grow["headline"] == "estimated productive-use sales", grow["headline"]
    assert Decimal(str(money.get("amount_high"))) == Decimal("42.08") and money.get("currency") == "USD", money
    sales = next(c for c in grow["contributors"] if c["key"] == "productive_sales")
    price = next(c for c in grow["contributors"] if c["key"] == "productive_price")
    return {"headline": grow["headline"], "money": money, "sales": sales["text"], "price": price["text"],
            "subline": grow["subline"], "state": grow["state"]}


@row("WK-2b")
def wk2b(ctx: Ctx) -> dict:
    """D-W1-13: on day S (sunny; the mill idle) the Grow headline carries no money, names the unused daytime solar,
    and the sales line states the measured zero use. Under outcome-status/3 the state follows the MG-1 objective
    verdict (WK-4), never OPPORTUNITY; the spare solar rides as `potential` (the second chip)."""
    # DD1b2-R Q10 / R6 O6 (Architect restatement with its cause: the potential moved to S-11, WK-2c; not edited to
    # pass): no money, the headline is NOT the kW pattern, the sales line, and "No potential found yet".
    grow = rows(_kobo_board_s(ctx))["GROW_REVENUE"]
    assert grow["state"] in ("ON_TRACK", "WATCH", "UNKNOWN"), grow["state"]
    out = demo_rows.wk2b(grow, re.compile(r"\d+–\d+ kW of daytime solar unused"))
    return {**out, "subline": grow["subline"], "state": grow["state"]}


@row("WK-2c")
def wk2c(ctx: Ctx) -> dict:
    """R3 §2-3 under "Leave it": on S-11 the Grow potential is the limited-evidence sentence; fails if any kW or money
    shows. The pinned study (`mill.json`) is LIMITED with 5 eligible days, reported."""
    grow = rows(ctx.board(KOBO, ctx.day(-11), ctx.day(-10)))["GROW_REVENUE"]
    mill = json.loads((ctx.work / "mill.json").read_text(encoding="utf-8"))
    return demo_rows.wk2c(grow, mill.get("study"))


@row("WK-4")
def wk4(ctx: Ctx) -> dict:
    """WALK1-3b (Addendum 2 §A2.4): Kobo's day-S Grow state is the month-to-date objective verdict, never Unknown
    beside the money, and its objective line reads the month so far."""
    grow = rows(_kobo_board_s(ctx))["GROW_REVENUE"]
    line = next(c for c in grow["contributors"] if c["key"] == "declared_objective:MG-1")
    text, state = line["text"], grow["state"]
    kpi = (grow.get("nodes") or {}).get("kpi") or {}
    complete = (kpi.get("days") or {}).get("complete")
    branch = demo_rows.wk4(state, text, complete)  # D-W1-15 too early; R10 no fully checked day; or judged
    return {"branch": branch, "state": grow["state"], "objective": line["text"], "chip": line["confidence"],
            "days": kpi.get("days"), "potential": grow.get("potential")}


@row("WK-3", idx=True)
def wk3(ctx: Ctx) -> dict:
    """WALK1-1: the story week's Portfolio counts state their basis (complete, or over the checked days)."""
    body, _, _, _ = _estate(ctx, ctx.day(-6), ctx.day(1))
    basis = (body.get("summary") or {}).get("count_basis")
    assert basis is not None, body.get("summary")
    return {"count_basis": basis, "checked_days": (body.get("summary") or {}).get("checked_days")}


@row("WK-6")
def wk6(ctx: Ctx) -> dict:
    """WALK1-5 (Addendum 7, G2): the Kobo productive-use opportunity page for the 5-day study ending S+1 (the
    `kobo-opportunity` capture). The board's Productive use link carries the 5 Site-local days it describes
    (`mini.renewable_href`); the opportunity list is read over exactly those bounds (Site-local midnights, never UTC
    midnights, or the list refuses INVALID_WINDOW). The Tariff line is the page's own `tariffDeclared` text, built
    from the served price fields, so the check asserts those served fields (a PRICED series with a positive value and
    a currency); the wording itself is pinned by vitest and the capture."""
    from urllib.parse import parse_qs, urlparse

    board = _kobo_board_s1(ctx)
    grow = next(r for r in board["rows"] if r["category"] == "GROW_REVENUE")
    use = next(c for c in grow["contributors"] if c["key"] == "productive_use")
    query = parse_qs(urlparse(use["href"]).query)
    assert set(query) == {"from", "to"}, ("Productive use link carries no window", use["href"])
    lo, hi = at(query["from"][0]), at(query["to"][0])
    assert hi - lo == timedelta(days=5), ("not five Site-local days", use["href"])
    listing = ctx.get(f"/api/sites/{KOBO}/opportunities", **{"from": iso(lo), "to": iso(hi), "limit": 100})
    found = [r["opportunity"] for r in listing["rows"] if r.get("opportunity")]
    assert found, ("no Kobo opportunity for the study ending S+1", iso(lo), iso(hi))
    opp = max(found, key=lambda o: o["last_day"])
    assert opp["last_day"] == ctx.day(1).date().isoformat(), (opp["last_day"], ctx.day(1).date().isoformat())
    assert opp["scenario_id"] is None, opp["scenario_id"]  # a linked what-if reads "Unavailable in this read"
    # Addendum 8: the page prices the study at the start of its latest noon window (the S+1 opportunity body's last
    # pinned day, Site-local 12:00; Kobo is Africa/Nairobi, no DST, so that is the study's end minus 12 hours). The
    # server selects nothing without `valid_at`.
    # DD1b2-R10: day rows no longer carry `mini_revision_id` (they carry `hours[]`), so the per-row pin is dropped. The
    # S+1 study is reported (its v3 November days are 8 h runs, so 0 eligible days is expected); the tariff is read on
    # the pinned mill study (`mill.json` `study.opportunity_id`): 5 eligible days, priced at its latest noon window.
    detail = ctx.get(f"/api/sites/{KOBO}/opportunities/{opp['id']}")
    s1 = {"code": opp["code"], "eligible_days": next((n.get("eligible_days") for n in walk(detail)
                                                      if "eligible_days" in n), None),
          "status": next((n.get("status") for n in walk(detail) if "eligible_days" in n), None)}
    mill = _mill(ctx)["study"]
    assert mill.get("opportunity_id"), ("mill.json names no study", mill)
    assert mill.get("eligible_days") == 5, ("the mill study's eligible days", mill.get("eligible_days"))
    mill_last = mill.get("last_day")  # the stored study's own last day (mill.json), Site-local
    assert mill_last, ("the mill study has no last_day", sorted(mill))
    valid_at = iso(demo_rows.site_day_start(datetime.fromisoformat(mill_last).date(), _kobo_zone(ctx))
                   + timedelta(hours=12))
    series = ctx.get(f"/api/sites/{KOBO}/financial-assumptions", key="productive_use_price_per_kwh", limit=1,
                     valid_at=valid_at)
    selection = series.get("selection") or {}
    assert selection.get("state") == "PRICED", (valid_at, selection)
    price = selection.get("price") or {}
    assert Decimal(str(price.get("value"))) > 0 and price.get("currency"), price
    tariff = f"Declared price · {Decimal(str(price['value'])).normalize():f} {price['currency']} per kWh"
    assert tariff == "Declared price · 0.25 USD per kWh", tariff
    return {"opportunity": opp["code"], "days": [opp["first_day"], opp["last_day"]], "valid_at": valid_at,
            "s1_study": s1, "mill_study_last_day": mill_last,
            "declared_price": f"{price['value']} {price['currency']} per kWh", "tariff": tariff, "link": use["href"],
            "path": f"/sites/{KOBO}/opportunities/{opp['id']}"}


# ---- DD-1b2b finish rows (R6 O4-O6, O16): never run on a whole build before the rehearsal ----------------------------

def _mill(ctx: Ctx) -> dict:
    return json.loads((ctx.work / "mill.json").read_text(encoding="utf-8"))


def _site_chain_days(ctx: Ctx, code: str, offsets) -> list[dict]:
    return [ctx.get(f"/api/sites/{code}/chain", date=ctx.day(n).date().isoformat()) for n in offsets]


def _mill_thread(ctx: Ctx) -> dict | None:
    """The Kobo headroom thread's record with events (`/threads/{id}`), found on the chain bodies of the story days."""
    for body in _site_chain_days(ctx, KOBO, (-8, -5, -1, 0, 1)):
        for t in body.get("threads", []):
            if t.get("mechanism") == demo_rows.HEADROOM:
                return ctx.get(f"/api/sites/{KOBO}/threads/{t['id']}")["thread"]
    return None


@row("F-DRAIN")
def f_drain(ctx: Ctx) -> dict:
    """R6 O4: both drains end at 0/0/0 (recounted from the records' end counts); over_n is reported."""
    out = {}
    for name in ("drain-1", "drain-2"):
        path = ctx.work / f"{name}.json"
        assert path.is_file(), f"{name}.json is missing: the drain did not run"
        out[name] = demo_rows.drain_summary(json.loads(path.read_text(encoding="utf-8")))
    return out


def _stored_headroom(ctx: Ctx) -> list[tuple]:
    """DD1b2-R10 F-COH: every Kobo study with the eligible days of its latest stored revision, read from the rows
    (not from a served body), so the expectation does not depend on what is under test."""
    import psycopg

    with psycopg.connect(ctx.url.replace("+psycopg", "")) as c:
        return c.execute(
            "SELECT o.id, o.last_day, CAST(r.result->>'eligible_days' AS int) FROM mini_opportunity o "
            "JOIN site s ON s.tenant_id = o.tenant_id AND s.id = o.site_id "
            "JOIN LATERAL (SELECT result FROM mini_opportunity_revision x WHERE x.tenant_id = o.tenant_id "
            "AND x.site_id = o.site_id AND x.opportunity_id = o.id ORDER BY x.revision_no DESC LIMIT 1) r ON true "
            "WHERE s.site_code = %s ORDER BY o.last_day, o.id", (KOBO,)).fetchall()


def _coh(ctx: Ctx):
    """Collect the bundle, write `expected_threads` generated from the build's documents into its manifest, check."""
    import tempfile

    sys.path.insert(0, str(Path(__file__).resolve().parent / "checks"))
    import chain_coherence as cc

    out = Path(tempfile.mkdtemp(prefix="dd1b2-coh-", dir=ctx.work))
    cc.collect(cc.InProcess(ctx.client), ctx.story, ctx.days, out, "in-process")
    bundle = cc.Bundle(out)
    portfolio = [r for w in bundle.estate_windows() for r in cc._rows(bundle.get(f"portfolio.{w}"))]
    docs = lambda n: json.loads((ctx.work / n).read_text(encoding="utf-8"))  # noqa: E731
    mill = docs("mill.json") if (ctx.work / "mill.json").is_file() else None
    unplaced: list = []
    stored = _stored_headroom(ctx)
    kisiwa = docs("kisiwa.json") if (ctx.work / "kisiwa.json").is_file() else None  # DIESEL-1-R3p §9p.7 item 5
    threads = demo_rows.build_expected_threads(docs("kobo.json"), docs("cold.json"), portfolio, mill, unplaced,
                                               demo_rows.headroom_opportunities(stored), kisiwa=kisiwa)
    ctx.cache["stored_headroom"] = [[str(o), str(last), e] for o, last, e in stored]
    ctx.cache["unplaced"] = unplaced
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    manifest["expected_threads"] = threads
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return cc, out, threads


@row("F-COH")
def f_coh(ctx: Ctx) -> dict:
    """R6 O4: `chain_coherence check` with no `--expect`. Any finding is a fault except COH-17 on the mill thread, and
    only if that thread recurs (Q7 entry, owner BL-07). ACT-002/003 "Action agreed" are in the generated threads."""
    cc, out, threads = _coh(ctx)
    demo_rows.require_ev_group(threads)  # R8 B3(a): an empty EV group makes COH-10 vacuous for EV
    thread = _mill_thread(ctx)
    recurs = bool(thread) and any(e.get("state") == "RECURRED" for e in thread.get("events", []))
    report = cc.check(cc.Bundle(out))
    recorded = [json.loads((ctx.work / n).read_text(encoding="utf-8")) for n in ("cold.json", "ev.json")]
    for p in ctx.work.glob("cold-replay-*/**/positive.json"):  # Cold's cold.json keeps no Action id; its replay record does
        recorded.append(json.loads(p.read_text(encoding="utf-8")))
    faults, allowed = demo_rows.coh_split(report["findings"], recurs, demo_rows.recorded_action_ids(*recorded))
    assert not faults, [f"{f['rule']} {f.get('site_code')} {f.get('window')}: {f['detail']}"[:300] for f in faults[:8]]
    ctx.cache["coh"] = (out, threads)
    return {"threads": [{k: (len(v) if isinstance(v, list) else v) for k, v in t.items()} for t in threads],
            "recurs": recurs, "stored_headroom": ctx.cache.get("stored_headroom"), "allowed_coh17": [a for a in allowed if a["rule"] == "COH-17"],
            "allowed_coh2": [{k: a.get(k) for k in ("site_code", "window", "subject", "reason")}
                             for a in allowed if a["rule"] == "COH-2"], "requests": report["bundle"]["request_count"],
            "unplaced": ctx.cache.get("unplaced", [])}  # R8 B3(b): ids on no Portfolio row, ruled by reviewer/Architect


@row("F-COH3")
def f_coh3(ctx: Ctx) -> dict:
    """R6 O4: non-vacuous. The same bundle with one expected thread naming a Finding no Portfolio row shows must make
    COH-10 fire; if it does not, the F-COH pass above proves nothing."""
    cc, out, threads = _coh(ctx)
    bogus = {"name": "f-coh3-bogus", "site_code": KOBO, "mechanism": "NONE",
             "findings": ["00000000-0000-0000-0000-000000000000"]}
    report = cc.check(cc.Bundle(out), None, [*threads, bogus])
    fired = [f for f in report["findings"] if f["rule"] == "COH-10" and f.get("subject") == "f-coh3-bogus"]
    assert fired, "COH-10 did not fire on a thread with no Findings: the coherence check is vacuous"
    return {"fired": len(fired)}


@row("F-CAL")
def f_cal(ctx: Ctx) -> dict:
    """R6 O4 / Q11: every Kobo local day from first evidence to today is read. A day with no built run (S-10, S-4, S-2,
    and any day after the last built one) is asserted NO_DATA; a built day is only recorded (no grade asserted)."""
    kobo = ctx.site_days("kobo")
    built = {at(d["start"]).astimezone(timezone(timedelta(hours=3))).date() for d in kobo
             if d.get("has_run", True) and d["kind"] != "missing"}
    first = min(at(d["start"]).astimezone(timezone(timedelta(hours=3))).date() for d in kobo if d.get("start"))  # R10
    today = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3))).date()
    want = demo_rows.calendar_expectations(first, today, built)
    got, bad = {}, {}
    for day, expected in want.items():
        body = ctx.get(f"/api/sites/{KOBO}/chain", date=day)
        grades = [d.get("grade") for d in body.get("days", []) if d.get("day") == day]
        got[day] = grades[0] if grades else None
        if expected and got[day] != expected:
            bad[day] = (expected, got[day])
    assert any(v == "NO_DATA" for v in want.values()), "F-CAL set has no NO_DATA day: the set is empty"
    assert not bad, bad
    return {"days": got, "no_data_asserted": sorted(d for d, v in want.items() if v)}


@row("MILL-3")
def mill3(ctx: Ctx) -> dict:
    """R6 O5 / Q10: outcome count 1; the verification page is VERIFIED and reads 42.00 -> 110.00 (a difference is a
    stop); the Action carries origin_opportunity_id and CHANGE_APPLIED; the baseline is not SHORT."""
    import psycopg

    m = _mill(ctx)
    action_id = m["action"]["id"]
    page = ctx.get(f"/api/sites/{KOBO}/domain-work/actions/{action_id}/verification")
    line = demo_rows.mill_page(page)
    with psycopg.connect(ctx.url.replace("+psycopg", "")) as c:
        count = c.execute("SELECT count(*) FROM verification_outcome WHERE domain_action_id = %s",
                          (action_id,)).fetchone()[0]
        origin = c.execute("SELECT origin_opportunity_id FROM domain_action WHERE id = %s", (action_id,)).fetchone()
    assert count == 1, ("outcome count", count)
    assert origin and origin[0] is not None, "the mill Action has no origin_opportunity_id"
    thread = _mill_thread(ctx)
    assert thread, "no headroom thread on the Kobo chain"
    states = [e.get("state") for e in thread.get("events", [])]
    assert "CHANGE_APPLIED" in states, states
    plan = page.get("plan") or {}
    assert len(plan.get("baseline_days") or []) >= 3 and len(plan.get("later_days") or []) >= 3, plan
    return {**line, "outcome_count": count, "origin_opportunity_id": str(origin[0]), "thread_events": states,
            "plan": plan}


@row("MILL-3b")
def mill3b(ctx: Ctx) -> dict:
    """MV-1 (FUEL-1 §2.4): the same verification page carries the PRICED mill value; per_day is recomputed from the
    page's shown means and the v1 productive-use price fixture, never typed; the text and the cost line are the
    backend constants."""
    m = _mill(ctx)
    page = ctx.get(f"/api/sites/{KOBO}/domain-work/actions/{m['action']['id']}/verification")
    price = demo_rows.productive_price_v1(Path(__file__).resolve().parents[1] / "backend" / "conversions"
                                          / "demo-productive-price-publications.json")
    return demo_rows.mill_value_page(page, price)


@row("F-THREADS")
def f_threads(ctx: Ctx) -> dict:
    """R6 O5 / Q10: the mill Action's wire ref is DOMAIN_VERDICT with the verification page path and state VERIFIED;
    Cold and EV Action refs stay ACTION; every story board has no PRODUCER_NOT_SETTLED or PARTIAL row;
    `domain_action_index` is a successful read on Cold and EV; Cold and EV threads read "Action agreed" (ACT-002/003)
    or "No action agreed yet" (reported either way as found); the Kobo MG-1/MG-2 lines are recorded as shown."""
    m = _mill(ctx)
    action_id = m["action"]["id"]
    seen = [a for b in _site_chain_days(ctx, KOBO, (-8, -5, -1, 0, 1)) for a in b.get("actions", [])
            if str(a.get("id")) == str(action_id)]
    assert seen, ("the mill Action is on no Kobo chain body", action_id)
    mill_ref = seen[0].get("ref") or {}
    assert demo_rows.action_ref_kind(seen[0]) == "DOMAIN_VERDICT", mill_ref
    # DD1b2-R10: a domain intent's chain wire carries no `verification` (chain/site_chain.py:126, 142); the verdict
    # is the DOMAIN_VERDICT page (the same read MILL-3 makes), which must be VERIFIED
    assert seen[0].get("verification") is None, seen[0].get("verification")
    verdict = ctx.get(f"/api/sites/{KOBO}/domain-work/actions/{action_id}/verification")
    assert verdict.get("state") == "VERIFIED", ("DOMAIN_VERDICT page", verdict.get("state"), verdict.get("reasons"))
    other = {}
    for key, site in (("cold", COLD), ("ev", EV)):
        lo, hi = ctx.window(key, "failure" if key == "cold" else "fault")
        body = ctx.get(f"/api/sites/{site}/chain", **{"from": iso(lo), "to": iso(hi)})
        kinds = {str(a.get("code")): demo_rows.action_ref_kind(a) for a in body.get("actions", [])}
        assert all(k == "ACTION" for k in kinds.values()), kinds
        index = ctx.client.get(f"/api/sites/{site}/domain-work/action-index", params={"from": iso(lo), "to": iso(hi)})
        assert index.status_code == 200, (site, index.status_code, index.text[:200])
        other[site] = {"action_refs": kinds, "thread_states": [t.get("state_label") for t in body.get("threads", [])],
                       "action_index_rows": len(index.json().get("rows", []))}
    faults = {}
    for d in ctx.days:
        code = {"kobo": KOBO, "cold": COLD, "ev": EV}[d["site"]]
        if d.get("has_run", True) and d["kind"] != "missing":
            bad = demo_rows.board_faults(ctx.board(code, at(d["start"]), at(d["end"])))
            if bad:
                faults[f"{code} {d['day']}"] = bad
    assert not faults, faults
    k = rows(_kobo_board_s(ctx))
    # MB-1b (MB-1-R §3.4): the S-8 Grow row carries the mill's thread line; its kind and text are reported.
    s8 = mill_thread_line(ctx.board(KOBO, ctx.day(-8), ctx.day(-7)), m["action"]["code"], ctx.day(-8))
    return {"mill_ref": mill_ref, "cold_ev": other, "mill_line_s8": {"kind": s8["kind"], "text": s8["text"]},
            "mg": {"objective": next((c["text"] for c in k["GROW_REVENUE"]["contributors"]
                                      if c["key"].startswith("declared_objective")), None),
                   "cost_headline": k["OPTIMIZE_COST"].get("headline")},
            "boards_read": len(ctx.days)}


def _opp_line_text(item: dict) -> str:
    """The OPP_THREAD_* literal for an item's kind, formatted from the item's own fields only."""
    code, kind = display_code(item["action_code"]), item["kind"]
    if kind == "MONITORING":
        return OPP_THREAD_MONITORING.format(code=code, k=item["remaining_days"])
    if kind == "CLOSED":
        return OPP_THREAD_CLOSED.format(code=code, n=item["clean_days"])
    d = datetime.fromisoformat(item["effective_day"])
    return OPP_THREAD_SEEN_AGAIN.format(day=f"{d.day} {d:%b}", code=code)


def _mini_close_after() -> int:
    """The policy's close-after days for a MINIGRID Site (config/chain/thread-lifecycle-v1.json)."""
    cfg = json.loads((Path(__file__).resolve().parents[1] / "config" / "chain" / "thread-lifecycle-v1.json")
                     .read_text(encoding="utf-8"))["close_after_clean_complete_days"]
    return int(cfg.get("by_site_type", {}).get("MINIGRID", cfg["default"]))


def mill_thread_line(board: dict, code: str, day: Any = None, close_after: int | None = None) -> dict:
    """MILL-4 (MB-1-R §3.4): the board's Grow `thread_lines` hold exactly one item for the mill Action `code`, of kind
    MONITORING, CLOSED or RECURRED; its text is the matching literal formatted from its own fields; its ref is the
    THREAD page. With the board `day` (a date or datetime): its `effective_day` is not after that day, and a
    MONITORING line's `remaining_days` is within 0..close_after (the policy's, unless given). Returns the item."""
    grow = rows(board)["GROW_REVENUE"]
    mine = [t for t in grow.get("thread_lines", []) if t.get("action_code") == code]
    assert len(mine) == 1, ("mill thread lines on Grow", code, grow.get("thread_lines"))
    item = mine[0]
    assert item["kind"] in ("MONITORING", "CLOSED", "RECURRED"), item
    assert item["text"] == _opp_line_text(item), (item["text"], _opp_line_text(item))
    assert (item.get("ref") or {}).get("kind") == "THREAD", item.get("ref")
    if day is not None:
        board_day = day.date() if isinstance(day, datetime) else day
        assert datetime.fromisoformat(item["effective_day"]).date() <= board_day, ("line dated after the board day",
                                                                                   item["effective_day"], board_day)
        if item["kind"] == "MONITORING":
            limit = _mini_close_after() if close_after is None else close_after
            assert 0 <= item["remaining_days"] <= limit, ("remaining_days outside 0..close_after",
                                                          item["remaining_days"], limit)
    return item


@row("MILL-4")
def mill4(ctx: Ctx) -> dict:
    """MB-1b (FUEL-1 MB-1-R §3.4): the S+0 and S-8 Kobo boards' Grow row carries the mill's thread line (computed,
    never typed: kind, text and counts are reported as found)."""
    code = _mill(ctx)["action"]["code"]
    out = {}
    for name, n in (("S+0", 0), ("S-8", -8)):
        item = mill_thread_line(ctx.board(KOBO, ctx.day(n), ctx.day(n + 1)), code, ctx.day(n))
        out[name] = {k: item.get(k) for k in ("kind", "text", "effective_day", "remaining_days", "clean_days")}
    return out


@row("MILL-5")
def mill5(ctx: Ctx) -> dict:
    """MB-1a (FUEL-1 MB-1-R §2.5): the S+0 Kobo board's Assure row lists the mill (DOMAIN_VERDICT link, the backend's
    verified text), its headline count equals the verified entries, the week `/api/estate/chain` verified claim is
    Σ threads.verified + Σ threads.verified_actions with Kobo's mill counted once, and the mill's one stored
    `verification_outcome` is VERIFIED (SQL)."""
    m = _mill(ctx)
    action_id, code = m["action"]["id"], m["action"]["code"]  # `mill.json` (tools/demo_combined_mill.py:179)
    week = ctx.get("/api/estate/chain", **{"from": iso(ctx.day(-6)), "to": iso(ctx.day(1))})
    page = ctx.get(f"/api/sites/{KOBO}/domain-work/actions/{action_id}/verification")  # the MILL-3 verdict page read
    out = demo_rows.mill_assure(_kobo_board_s(ctx), week, action_id, code, page, KOBO)
    with psycopg.connect(ctx.url.replace("+psycopg", "")) as c:
        stored = [r[0] for r in c.execute("SELECT outcome FROM verification_outcome WHERE domain_action_id = %s",
                                          (action_id,)).fetchall()]
    assert stored == ["VERIFIED"], ("the mill's stored outcome", stored)
    return {**out, "stored_outcome": stored[0]}


@row("PV-A")
def pv_a(ctx: Ctx) -> dict:
    """PV-1 (FUEL-1 PV-1-R §5): on the week estate summary holding the S+0 Kobo board, the Assure card lists the mill
    line equal to its verdict page's value, the trial-fuel line iff ACT-001's cost check is credited (the case is
    reported), and no card string holds a sum of two same-currency amounts (`demo_rows.pv_values`)."""
    m = _mill(ctx)
    page = ctx.get(f"/api/sites/{KOBO}/domain-work/actions/{m['action']['id']}/verification")
    summary = ctx.get("/api/estate/outcome-summary", **{"from": iso(ctx.day(-6)), "to": iso(ctx.day(1))})
    action = _action(ctx)
    cc = (action.get("verification") or {}).get("cost_check")
    return demo_rows.pv_values(summary, page, m["action"]["code"], action.get("action_code") or "ACT-001", cc, KOBO)


KISIWA = "KISIWA-001"
KisiwaMissing = demo_rows.KisiwaMissing  # carry R3k2 L2: every KIS row fails on a dataset with no Kisiwa Site


@row("KIS-4")
def kis_4(ctx: Ctx) -> dict:
    """DIESEL-K4a (DIESEL-1-R3j §9j.9, written by K4a, run at E3): every SUPPORTED Kisiwa fuel Finding's
    `fuel-residual-1` litres equal its cited window's band, PRICED amounts equal litres x the stored price (whose
    revision a re-run of `select_window_price` at the window end reproduces), no `financial_consequence_revision` row
    cites a fuel Finding, and no stored or served amount is a sum (`demo_rows.kis4`). A dataset without the Kisiwa Site
    fails the row (DIESEL-1-R3k2 L2, carried by K7): `KisiwaMissing`."""
    import psycopg

    from assetops_backend.financials.composition import build_trial_comparison_ports

    url = ctx.url.replace("+psycopg", "")
    with psycopg.connect(url) as c:
        site = c.execute("SELECT tenant_id, id FROM site WHERE site_code_key = lower(%s)", (KISIWA,)).fetchone()
        if site is None:
            raise KisiwaMissing()  # carry R3k2 L2: a dataset without Kisiwa is a failure, not a skip
        t, s = site
        cols = lambda cur: [d.name for d in cur.description]  # noqa: E731

        def rows(sql: str, *p) -> list[dict]:
            cur = c.execute(sql, p)
            names = cols(cur)
            return [dict(zip(names, r)) for r in cur.fetchall()]

        windows = {str(r["id"]): r for r in rows("SELECT id, residual_low, residual_high, window_start, window_end "
                                                 "FROM fuel_balance_window WHERE site_id = %s", s)}
        findings = rows(
            "SELECT DISTINCT ON (r.finding_id) r.finding_id, r.id AS revision_id, r.lifecycle, "
            "r.claim->>'fuel_balance_window_id' AS window_id FROM finding_revision r WHERE r.site_id = %s "
            "AND r.domain = 'fuel_balance' ORDER BY r.finding_id, r.revision_no DESC", s)
        consequences = rows("SELECT * FROM fuel_residual_consequence_revision WHERE site_id = %s", s)
        dispatch = rows("SELECT finding_id, amount_low, amount_high FROM financial_consequence_revision "
                        "WHERE site_id = %s", s)
    select = build_trial_comparison_ports(ctx.url).price_selection
    prices = {}
    for f in findings:
        w = windows[str(f["window_id"])]
        p = select(t, s, w["window_start"], w["window_end"], w["window_end"])
        prices[str(f["window_id"])] = {"state": p.state, "revision_id": p.revision_id, "value": p.value}
    summary = ctx.get("/api/estate/outcome-summary", **{"from": iso(ctx.day(-6)), "to": iso(ctx.day(1))})
    served = [v for node in walk(summary) for x in node.values()
              for v in ([x] if isinstance(x, str) else x if isinstance(x, list) else []) if isinstance(v, str)]
    return {"kisiwa": "present", **demo_rows.kis4(windows, findings, consequences, prices, dispatch, served)}


@row("KIS-8a")
def kis_8a(ctx: Ctx) -> dict:
    """DIESEL-K4b (DIESEL-1-R3j §9j.12, written by K4b, run at E3): the week estate summary holding Kisiwa's S+0 board
    lists Kisiwa's night-4 unexplained-fuel line on the Protect card, built from its Protect node, and COH-17 row UF1
    passes on it (`demo_rows.kis8_protect`). Night 4 is the Site-local night starting S−6d (K7, §9l.3). A dataset
    without the Kisiwa Site is reported as such, never as a check."""
    summary = ctx.get("/api/estate/outcome-summary", **{"from": iso(ctx.day(-6)), "to": iso(ctx.day(1))})
    if not any(s.get("site_code") == KISIWA for s in summary.get("sites") or ()):
        return {"kisiwa": "not in this dataset (K7 adds it)", "checked": 0}
    return {"kisiwa": "present", **demo_rows.kis8_protect(summary, ctx.day(-6).date(), KISIWA)}


def _kisiwa_fuel(ctx: Ctx) -> dict | None:
    """DIESEL-K6b: the Kisiwa FUEL_BALANCE Action with its fuel plan context, outcome, windows and threads, read once
    through the backend's own stores (None: no Kisiwa Site in this dataset; the rows then fail, carry R3k2 L2)."""
    if "kisiwa_fuel" in ctx.cache:
        return ctx.cache["kisiwa_fuel"]
    import psycopg

    from assetops_backend.actions.composition import build_action_store
    from assetops_backend.fuel_balance.composition import build_fuel_balance_store

    with psycopg.connect(ctx.url.replace("+psycopg", "")) as c:
        site = c.execute("SELECT tenant_id, id FROM site WHERE site_code_key = lower(%s)", (KISIWA,)).fetchone()
        if site is None:
            ctx.cache["kisiwa_fuel"] = None
            return None
        t, s = site
        found = c.execute("SELECT id FROM domain_action WHERE site_id = %s AND domain = 'FUEL_BALANCE' "
                          "ORDER BY recorded_at, id LIMIT 1", (s,)).fetchone()
        assert found is not None, "Kisiwa holds no FUEL_BALANCE Action (K7-D step 5 raises it)"
        aid = found[0]
        action_thread = c.execute("SELECT CAST(thread_id AS text) FROM chain_action WHERE id = %s", (aid,)).fetchone()
    store, fuel = build_action_store(ctx.url), build_fuel_balance_store(ctx.url)
    try:
        fc = store.fuel_plan_context(t, s, aid)
        outcomes = store.domain_outcomes(t, s, aid)
        plan = fc["plan"]
        assert plan is not None and outcomes, ("the Kisiwa fuel Action has no fuel plan or outcome", plan, outcomes)
        o = outcomes[0]
        pins = [o["details"]["baseline"], *o["details"]["later"]]
        read_back = {}
        for p in pins:
            w = fuel.window(t, s, p["window_id"])
            if w is not None:
                read_back[str(p["window_id"])] = {"revision": w.revision, "input_sha256": w.input_sha256}
        lo = datetime.fromisoformat(plan["later_selection_rule"]["candidates"]["from"]).date()
        windows = {w.night_date: w for w in fuel.windows(t, s, plan["basis"]["tank_asset_id"], lo,
                                                         lo + timedelta(days=14),
                                                         known_at=o["recorded_at"].astimezone(timezone.utc))}
        with psycopg.connect(ctx.url.replace("+psycopg", "")) as c:
            finding_thread = c.execute(
                "SELECT CAST(o.thread_id AS text) FROM finding_thread_occurrence o JOIN finding_thread t "
                "ON t.id = o.thread_id WHERE o.finding_id = %s AND t.mechanism = 'UNEXPLAINED_FUEL' LIMIT 1",
                (fc["action"]["origin_finding_id"],)).fetchone()
    finally:
        store.dispose()
        fuel.dispose()
    out = {"t": t, "s": s, "aid": str(aid), "fc": fc, "plan": plan, "outcome": o, "read_back": read_back,
           "windows": windows, "action_thread": None if action_thread is None else action_thread[0],
           "finding_thread": None if finding_thread is None else finding_thread[0]}
    ctx.cache["kisiwa_fuel"] = out
    return out


@row("KIS-5")
def kis_5(ctx: Ctx) -> dict:
    """DIESEL-K6b (DIESEL-1-R3m §9m.4, moved here from K9, run at E3): the Kisiwa fuel Action's stored verdict
    reproduces from its pinned windows (`demo_rows.kis5`); the served page has no value, cost check or money key, and
    the fixed H1 line. A dataset without the Kisiwa Site fails the row (`KisiwaMissing`, carry R3k2 L2, K7-F)."""
    k = _kisiwa_fuel(ctx)
    if k is None:
        raise KisiwaMissing()
    summary = ctx.get(f"/api/sites/{KISIWA}/domain-work/actions/{k['aid']}/fuel-verification")
    return {"kisiwa": "present", **demo_rows.kis5(k["plan"], k["outcome"], k["read_back"], k["windows"], summary)}


@row("KIS-10")
def kis_10(ctx: Ctx) -> dict:
    """DIESEL-K6b (DIESEL-1-R3m §9m.4, run at E3): fuel verification coherence (`demo_rows.kis10`): frozen before the
    first later night, effective at the case's COMPLETE, the origin and baseline pins, one thread, the Kisiwa board's
    FUEL_VERDICT Verified results entry on the outcome's Site-local day + 1, and no value line naming the Action."""
    from zoneinfo import ZoneInfo

    k = _kisiwa_fuel(ctx)
    if k is None:
        raise KisiwaMissing()  # carry R3k2 L2 (K7-F): a dataset without Kisiwa fails the row
    fc, o = k["fc"], k["outcome"]
    zone = ZoneInfo(fc["action"]["timezone"])
    lo = demo_rows.site_day_start(o["recorded_at"].astimezone(zone).date() + timedelta(days=1), zone)
    board = ctx.board(KISIWA, lo, lo + timedelta(days=1))
    s_from, s_to = utc_aligned_window(lo - timedelta(days=6), lo + timedelta(days=1))
    summary = ctx.get("/api/estate/outcome-summary", **{"from": iso(s_from), "to": iso(s_to)})
    lines = list(((summary.get("cards") or {}).get("ASSURE_PERFORMANCE") or {}).get("value_lines") or ())
    return {"kisiwa": "present", **demo_rows.kis10(k["plan"], fc["applied"], fc["action"], fc["origin_window_id"],
                                                   k["action_thread"], k["finding_thread"], board,
                                                   fc["action"]["action_code"], lines)}


@row("MONEY-B")
def money_b(ctx: Ctx) -> dict:
    """R6 O16, the part readable through the served boards: the Cost headline on one steady-before and one steady
    day is reported as shown, and WK-2a's 42.08 stays (that row). The fuel-row trace and the PRICED-0 days need stored
    rows and are NOT implemented here (handoff).
    FUEL-1 A3-R §3.9 (O16 extended): the three idle mornings S-14, S-7, S are fuel-cost-2 PRICED, idle-only and exact
    from stored values, their headline is `COST_IDLE` and their money the stored display (`demo_rows.idle_morning`),
    no shown string holds a sum of mornings, and the steady days carry no idle fuel (`demo_rows.steady_day`)."""
    stored = _consequence_heads(ctx)
    shown, mornings, bodies = {}, [], []
    for kind in ("steady-before", "steady"):
        day = next((d for d in ctx.site_days("kobo") if d["kind"] == kind), None)
        if day is not None:
            cost = rows(ctx.board(KOBO, at(day["start"]), at(day["end"])))["OPTIMIZE_COST"]
            shown[kind] = demo_rows.steady_day(day["day"], _on(stored, day), cost)
    assert shown, "no steady or steady-before Kobo day in days.json"
    for off in IDLE_MORNINGS:
        day = next(d for d in ctx.site_days("kobo") if d.get("offset") == off)
        board = ctx.board(KOBO, at(day["start"]), at(day["end"]))
        heads = _on(stored, day)
        assert len(heads) == 1, ("one head fuel row per idle morning", day["day"], len(heads))
        mornings.append(demo_rows.idle_morning(day["day"], heads[0], rows(board)["OPTIMIZE_COST"]))
        bodies.append(board)
    bodies.append(ctx.get("/api/estate/outcome-summary", **{"from": iso(ctx.day(-6)), "to": iso(ctx.day(1))}))
    # a body that spans the idle mornings (S-14, S-7, S), so a sum of mornings could appear in it
    bodies.append(ctx.get("/api/estate/outcome-summary", **{"from": iso(ctx.day(-14)), "to": iso(ctx.day(1))}))
    sums = demo_rows.never_summed([m["amount_high"] for m in mornings], bodies)
    assert sums > 0, "no sum of mornings checked"
    return {**shown, "idle_mornings": mornings, "sums_checked": sums}


def _consequence_heads(ctx: Ctx) -> list[dict]:
    """FUEL-1 A3-R §3.9: Kobo's head fuel consequence row per Finding (latest recorded revision), SQL column names."""
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(ctx.url.replace("+psycopg", ""), row_factory=dict_row) as c:
        return c.execute(
            "SELECT DISTINCT ON (r.finding_id) r.finding_id, r.window_start, r.state, r.model_id, r.idle_seconds, "
            "r.no_load_fuel_rate_l_per_h, r.no_load_fuel_rate_basis, r.sfc_upper_multiplier, r.quantity_high_exact, "
            "r.quantity_high, r.amount_low, r.amount_high, r.currency, r.price_value "
            "FROM financial_consequence_revision r JOIN site s ON s.id = r.site_id WHERE s.site_code = %s "
            "ORDER BY r.finding_id, r.recorded_at DESC, r.revision_no DESC", (KOBO,)).fetchall()


def _on(stored: list[dict], day: dict) -> list[dict]:
    lo, hi = at(day["start"]), at(day["end"])
    return [r for r in stored if lo <= r["window_start"] < hi]


@row("CH5D1-O1")
def ch5d1_o1(ctx: Ctx) -> dict:
    """FUEL-1 A3-R §3.9: the S Optimize card equals the one priced Site's (Kobo's) cost claim text, replacing
    CH5d1-R §4's "Not known yet" forecast (`demo_rows.optimize_card`)."""
    return demo_rows.optimize_card(ctx.get("/api/estate/outcome-summary",
                                           **{"from": iso(ctx.day(0)), "to": iso(ctx.day(1))}), KOBO)


@row("A3-PAGE")
def a3_page(ctx: Ctx) -> dict:
    """FUEL-1 A3-R §3.9: ACT-001's verification outcome body has `fuel_value` equal to `FUEL_VALUE_PAGE` built from
    the stored trial row (`demo_rows.trial_page`)."""
    body = ctx.get(f"/api/sites/{KOBO}/actions/{ctx.docs['kobo']['action']}/verification/outcome")
    return {"fuel_value": demo_rows.trial_page(body, _trial_result(ctx))}


# ---- DIESEL-K7 (ruling DIESEL-1-R3l §9l.3): KIS-3 and KIS-9, written by K7 -----------------------------------------

KISIWA_SITE = "KISIWA-001"


def _kisiwa_read(ctx: Ctx) -> dict | None:
    """Kisiwa's stored rows (cached on `ctx`): the latest window per night as known now, the operational records, and
    the handover, calendar, build document and derived log. None when the dataset holds no Kisiwa Site."""
    if "kisiwa" in ctx.cache:
        return ctx.cache["kisiwa"]
    import psycopg

    with psycopg.connect(ctx.url.replace("+psycopg", "")) as c:
        site = c.execute("SELECT tenant_id, id FROM site WHERE site_code_key = lower(%s)", (KISIWA_SITE,)).fetchone()
        if site is None:
            ctx.cache["kisiwa"] = None
            return None

        def fetch(sql: str, *p) -> list[dict]:
            cur = c.execute(sql, p)
            names = [d.name for d in cur.description]
            return [dict(zip(names, r)) for r in cur.fetchall()]

        windows = fetch("SELECT DISTINCT ON (night_date) id, night_date, revision, recorded_at, state, reason, "
                        "residual_low, residual_high, gap_minutes, gap_spans, limitations, terms FROM fuel_balance_window "
                        "WHERE site_id = %s AND recorded_at <= clock_timestamp() ORDER BY night_date, revision DESC",
                        site[1])
        records = fetch("SELECT id, kind, body, occurred_at, recorded_at, quantity, source_document_sha256, case_id "
                        "FROM operational_record WHERE site_id = %s ORDER BY occurred_at, recorded_at", site[1])
    import demo_combined_kisiwa as kis

    calendar = ctx.story["kisiwa"]
    build = json.loads((ctx.work / "kisiwa.json").read_text(encoding="utf-8"))
    log_text = Path(build["log"]["path"]).read_text(encoding="utf-8")
    assert kis.lf_sha256(log_text) == build["log"]["sha256"], "the derived log changed after the build"
    nights = {r["night_date"]: r["k"] for r in calendar["runs"]}
    out = {"tenant_id": site[0], "site_id": site[1], "handover": kis.load_handover(), "calendar": calendar,
           "build": build, "actions": kis.parse_log(log_text)["actions"],
           "runs": [(at(r["start"]), at(r["end"])) for r in calendar["runs"]],
           "windows": {nights[w["night_date"].isoformat()]: w for w in windows if w["night_date"].isoformat() in nights},
           "records": records}
    ctx.cache["kisiwa"] = out
    return out


@row("KIS-3")
def kis_3(ctx: Ctx) -> dict:
    """KIS-3 (DIESEL-1-R3l §9l.3, moved from K9 to K7): Kisiwa's ten stored nights reproduce the handover's readings
    band (`demo_rows.kis3`). A dataset without the Kisiwa Site fails the row (`KisiwaMissing`, carry R3k2 L2)."""
    k = _kisiwa_read(ctx)
    if k is None:
        raise KisiwaMissing()
    return {"kisiwa": "present", **demo_rows.kis3(k["windows"], k["handover"], k["calendar"]["delta_days"])}


def _kisiwa_sql(ctx: Ctx, sql: str, *params) -> list[dict]:
    import psycopg

    with psycopg.connect(ctx.url.replace("+psycopg", "")) as c:
        cur = c.execute(sql, params)
        names = [d.name for d in cur.description]
        return [dict(zip(names, r)) for r in cur.fetchall()]


def _kisiwa_finding(ctx: Ctx, k: dict) -> dict | None:
    """KIS-9 (d): the fuel Finding read, from stored rows as known now: each fuel Finding's latest revision (its
    lifecycle, window id and revision, stamp), the mechanisms of the threads that hold it, its latest consequence
    (state and price revision), and the Site's diesel price v1 revision."""
    s = k["site_id"]
    found = _kisiwa_sql(
        ctx, "SELECT DISTINCT ON (r.finding_id) r.finding_id, r.id AS revision_id, r.lifecycle, r.created_at, "
        "r.claim->>'fuel_balance_window_id' AS window_id, (r.claim->>'window_revision')::int AS window_revision "
        "FROM finding_revision r WHERE r.site_id = %s AND r.domain = 'fuel_balance' "
        "ORDER BY r.finding_id, r.revision_no DESC", s)
    for f in found:
        f["thread_kinds"] = [r["mechanism"] for r in _kisiwa_sql(
            ctx, "SELECT t.mechanism FROM finding_thread t JOIN finding_thread_occurrence o ON o.thread_id = t.id "
            "WHERE o.site_id = %s AND o.finding_id = %s ORDER BY t.mechanism", s, f["finding_id"])]
        cons = _kisiwa_sql(ctx, "SELECT state, price_revision_id FROM fuel_residual_consequence_revision "
                                "WHERE finding_revision_id = %s", f["revision_id"])
        f["consequence_state"] = cons[0]["state"] if cons else None
        f["price_revision_id"] = cons[0]["price_revision_id"] if cons else None
    diesel = _kisiwa_sql(ctx, "SELECT id FROM financial_assumption_revision WHERE site_id = %s "
                              "AND assumption_key = 'diesel_price_per_litre' AND revision_no = 1", s)
    assert len(diesel) == 1, ("want exactly one diesel price v1 revision for the Site", diesel)
    return {"findings": found, "diesel_v1_revision_id": diesel[0]["id"]}


def _kisiwa_action(ctx: Ctx, k: dict) -> dict | None:
    """KIS-9 (e): the Action read: its origin Finding, the cases linked to it, the linked case's state (its
    latest work event's kind) and, K7-F, the stamps of its verification plans and outcomes."""
    s = k["site_id"]
    acts = _kisiwa_sql(ctx, "SELECT id, action_code, domain, origin_finding_id FROM domain_action WHERE site_id = %s "
                            "AND domain = 'FUEL_BALANCE'", s)
    assert len(acts) == 1, ("want exactly one FUEL_BALANCE Action", acts)
    a = acts[0]
    links = _kisiwa_sql(ctx, "SELECT case_id FROM domain_action_case_link WHERE site_id = %s AND action_id = %s "
                             "ORDER BY recorded_at", s, a["id"])
    assert links, ("the Action has no case link", a)
    case_id = links[-1]["case_id"]
    last = _kisiwa_sql(ctx, "SELECT kind FROM work_event WHERE site_id = %s AND case_id = %s "
                            "ORDER BY recorded_at DESC, id DESC LIMIT 1", s, case_id)
    plans = _kisiwa_sql(ctx, "SELECT recorded_at FROM verification_plan WHERE site_id = %s AND domain_action_id = %s "
                             "ORDER BY recorded_at", s, a["id"])
    outcomes = _kisiwa_sql(ctx, "SELECT recorded_at FROM verification_outcome WHERE site_id = %s "
                                "AND domain_action_id = %s ORDER BY recorded_at", s, a["id"])
    return {"origin_finding_id": a["origin_finding_id"], "case_id": case_id, "case_state": last[0]["kind"],
            "linked_case_ids": [r["case_id"] for r in links],
            "plan_recorded_at": [r["recorded_at"] for r in plans],  # K7-F: KIS-9 (e)
            "outcome_recorded_at": [r["recorded_at"] for r in outcomes]}


@row("KIS-9")
def kis_9(ctx: Ctx) -> dict:
    """KIS-9 (DIESEL-1-R3l §9l.3): Kisiwa story coherence: records, dip quantities, every action in one run, the
    Finding, the Action, every run's frozen log and history, and story-instant stamps (`demo_rows.kis9`)."""
    k = _kisiwa_read(ctx)
    if k is None:
        raise KisiwaMissing()
    return {"kisiwa": "present", **demo_rows.kis9(
        records=k["records"], handover=k["handover"], calendar=k["calendar"], build=k["build"], actions=k["actions"],
        runs=k["runs"], windows=k["windows"], finding=_kisiwa_finding(ctx, k), action=_kisiwa_action(ctx, k))}


# ---- runner ----------------------------------------------------------------------------------------------------

def load(work: Path, client) -> Ctx:
    read = lambda name: json.loads((work / name).read_text(encoding="utf-8"))
    ctx = Ctx(client=client, work=work, story=read("story.json"), days=read("days.json")["days"])
    ctx.docs["kobo"] = read("kobo.json")
    cold, ev = read("cold.json"), read("ev.json")
    ctx.docs["cold_work"] = next(d["work"] for d in cold["days"] if d["kind"] == "failure")
    ctx.docs["ev_work"] = next(d["fault_day"]["work"] for d in ev["days"] if d["kind"] == "fault")
    return ctx


def app_client(url: str, work: Path):
    os.environ["DATABASE_URL"] = os.environ["ASSETOPS_TEST_DATABASE_URL"] = url
    os.environ.update(json.loads((work / "keys.json").read_text(encoding="utf-8")))
    from fastapi.testclient import TestClient
    from lab_app import app

    return TestClient(app)


def run(url: str, work: Path) -> int:
    ctx = load(work, app_client(url, work))
    ctx.url = url
    have_idx, results, failed = idx_present(), {}, []
    for check_id, idx, mutates, fn in CHECKS:
        if mutates or (idx and not have_idx):
            results[check_id] = {"status": "skipped", "reason": "build test only" if mutates else "needs IDX-GAPS"}
            continue
        try:
            results[check_id] = {"status": "pass", "read": fn(ctx)}
        except Exception as exc:  # recorded per row; the prepare fails after all rows ran
            results[check_id] = demo_rows.failed_result(exc)
            failed.append(check_id)
    (work / "check.json").write_text(json.dumps({"idx_present": have_idx, "rows": results}, indent=2, default=str),
                                     encoding="utf-8")
    passed = sum(r["status"] == "pass" for r in results.values())
    skipped = sum(r["status"] == "skipped" for r in results.values())
    print(f"self-check: {passed} pass, {len(failed)} fail {failed}, {skipped} skipped")
    return 1 if failed else 0


def get_once(url: str, work: Path, path: str, params: str) -> int:
    """One GET through `host/lab_app.py` in this tree (the build test reads with the tree's file stores, which sit
    under its own REPO_ROOT): prints one JSON line {"status_code", "body"}."""
    r = app_client(url, work).get(path, params=json.loads(params))
    try:
        body = r.json()
    except ValueError:
        body = r.text[:2000]
    print(json.dumps({"status_code": r.status_code, "body": body}, default=str))
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "check":
        raise SystemExit(run(sys.argv[2], Path(sys.argv[3])))
    if len(sys.argv) == 6 and sys.argv[1] == "get":
        raise SystemExit(get_once(sys.argv[2], Path(sys.argv[3]), sys.argv[4], sys.argv[5]))
    raise SystemExit("usage: demo_combined_finish.py check <database-url> <work>; "
                     "demo_combined_finish.py get <database-url> <work> <path> <params-json>")
