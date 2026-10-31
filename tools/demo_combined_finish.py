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
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

KOBO, COLD, EV = "KOBO-001", "COLD-LAB-001", "EV-LAB-001"
CATEGORIES = ["GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"]
SAFEGUARD = " · checked here as a safeguard"
OUTSIDE = " · linked finding outside this view"
NOT_REALISED = "not realised savings"
GAPS_TEXT = "Not available yet · {g} of 31 days have no assessed readings"
IDX_POLICY = "finding-index/2"
#: U1 probe, `.agent/DEMO-SPARSE-trial-probe.md` P3 row (a): the chosen candidate and its recorded cost check.
PROBE_CHOSEN = {"chosen": "a", "window_hour": "06:00", "cost_state": "MODELLED_NO_IMPROVEMENT", "nominal": 0}


def idx_present() -> bool:
    from assetops_backend.analytics import finding_index

    return getattr(finding_index, "POLICY_VERSION", None) == IDX_POLICY


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    # Original §5 text, restored by LINK-LINEAGE §5: the board links the Action across the post-apply
    # BASIS_REFRESHED revision of the same Finding (D-2026-10-31 refresh lineage), so day S's Cost row carries the
    # Action's Must-not-harm line with its verification href and the Action itself.
    mnh = cost.get("must_not_harm") or {}
    href = mnh.get("href") or ""
    assert k["action"] in href and "/verification?event_id=" in href, mnh
    on_cost_row = [i["text"] for i in items(cost)
                   if k["action"] in (i.get("href") or "") or k["action_code"] in (i.get("text") or "")]
    assert on_cost_row, items(cost)
    outside = [i["text"] for x in body["rows"] for i in items(x) if i["text"].endswith(OUTSIDE)]
    assert outside == [], outside
    outcomes = {o["key"]: (o["state"], o.get("reason")) for o in cost["outcomes"]}
    mg2 = outcomes.get("MG-2")
    branches = {"PRIMARY_FINDING_APPLIED": "WATCH", "OBJECTIVE_MISSED": "NEEDS_ATTENTION"}
    assert mg2 is not None and mg2[1] in branches, outcomes
    assert cost["state"] == branches[mg2[1]], (cost["state"], mg2)
    return {"cost_state": cost["state"], "finding": k["finding"], "must_not_harm": mnh,
            "action_on_cost_row": on_cost_row, "mg2": mg2, "branch": mg2[1],
            "r552": "resolved: refresh lineage"}


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
    if not day.get("findings"):  # U1 P1 gave the normal day 0 avoidable minutes: no Finding, so On track
        assert cost["state"] == "ON_TRACK", (cost["state"], outcomes)
        branch = "ON_TRACK"
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
    assert gaps.get(ctx.day(-10).date().isoformat()) == "UNASSESSED", gaps
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
    assert float(cc.get("nominal") or 0) == PROBE_CHOSEN["nominal"], cc
    return {"window_hour": k["window_hour"], "cost_check": cc}


# ---- cold and EV -----------------------------------------------------------------------------------------------

@row("CO-5/SP-2")
def sp2(ctx: Ctx) -> dict:
    lo, hi = ctx.window("cold", "normal")
    protect = rows(ctx.board(COLD, lo, hi))["PROTECT_ASSET"]
    outcomes = {o["key"]: (o["state"], o.get("reason")) for o in protect["outcomes"]}
    if protect["state"] != "ON_TRACK":  # the recorded measured values (no status is forced)
        assert all(s != "UNKNOWN" for s, _ in outcomes.values()), outcomes
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
    so cold and EV read their LATEST_EVENT. Kobo's estate coverage on `estate-coverage/2` is PARTIAL: the checked days
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
    assert basis.get(COLD) == basis.get(EV) == "LATEST_EVENT", basis
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
    assert basis.get(KOBO) == "DAY" and (by_code[KOBO].get("window") or {}).get("from") == iso(ctx.S), by_code[KOBO]
    board = {r["category"]: r["state"] for r in _kobo_board_s(ctx)["rows"]}
    cells = {r["category"]: r["state"] for r in by_code[KOBO]["rows"]}
    assert cells == board, (cells, board)
    others = {code: _cov(coverage.get(code)) for code in (COLD, EV)}
    return {"status": body["status"], "kobo_coverage": _cov(kobo), "kobo_days": days,
            "kobo_unassessed_days": unassessed, "kobo_finding_in_rows": finding_listed,
            "cold_ev_coverage": others, "window_basis": basis, "kobo_cells_from_day_S": cells}


@row("CO-6b", idx=True)
def co6b(ctx: Ctx) -> dict:
    """Addendum 2: the day S. Kobo coverage CURRENT; cold LATEST_EVENT (the S failure night); EV reads what it reads
    with no event on S (PERIOD unless S is a Tuesday): recorded and asserted as given, never forced."""
    body, summary, coverage, by_code = _estate(ctx, ctx.S, ctx.day(1))
    kobo = coverage.get(KOBO)
    assert kobo is not None and kobo["state"] == "CURRENT", _cov(kobo)
    assert (kobo.get("days") or {}).get("gaps") == [], kobo.get("days")
    basis = {code: x.get("window_basis") for code, x in by_code.items()}
    assert basis.get(COLD) == "LATEST_EVENT", basis
    ev_on_s = any(d["day"] == ctx.S.date().isoformat() and d["kind"] != "missing" for d in ctx.site_days("ev"))
    assert basis.get(EV) == ("LATEST_EVENT" if ev_on_s else "PERIOD"), (basis, ev_on_s)
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
    have_idx, results, failed = idx_present(), {}, []
    for check_id, idx, mutates, fn in CHECKS:
        if mutates or (idx and not have_idx):
            results[check_id] = {"status": "skipped", "reason": "build test only" if mutates else "needs IDX-GAPS"}
            continue
        try:
            results[check_id] = {"status": "pass", "read": fn(ctx)}
        except Exception as exc:  # recorded per row; the prepare fails after all rows ran
            results[check_id] = {"status": "fail", "error": f"{type(exc).__name__}: {exc}"[:2000]}
            failed.append(check_id)
    (work / "check.json").write_text(json.dumps({"idx_present": have_idx, "rows": results}, indent=2, default=str),
                                     encoding="utf-8")
    passed = sum(r["status"] == "pass" for r in results.values())
    skipped = sum(r["status"] == "skipped" for r in results.values())
    print(f"self-check: {passed} pass, {len(failed)} fail {failed}, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] != "check":
        raise SystemExit("usage: demo_combined_finish.py check <database-url> <work>")
    raise SystemExit(run(sys.argv[2], Path(sys.argv[3])))
