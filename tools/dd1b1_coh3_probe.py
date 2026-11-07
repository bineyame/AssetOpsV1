"""DD1b1-R Q6: the COH-3 probe. Not a demo prepare: Cold's `failure` day and EV's `fault` day only, through each child's
own `build`, on this run's own `*_test` database; then backfill a-d, at most 3 ticks, the board and index reads and
`chain_coherence.collect`. No `demo_combined.py prepare`, no finish rows, no Kobo, no polish or demo3 database.

    python tools/dd1b1_coh3_probe.py <work>     writes <work>/probe.json and prints the pass/fail lines. Exit 1 on fail.

A fail is reported, never tuned. Cap: 20 minutes in all; past it the running child is killed and the probe reports.
"""

from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "checks"))

CAP_SECONDS = 20 * 60
MAX_TICKS = 1   # DD1b1-R2 §5: one tick (0 thread events are proved; DD-1b2 repeats it on the whole build)
COLD, EV = "COLD-LAB-001", "EV-LAB-001"


class Stop(Exception):
    pass


def child(argv: list[str], env: dict, log: Path, deadline: float) -> str:
    """One child under the cap. `subprocess.run` kills only its own PID when the cap passes."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise Stop(f"cap passed before {argv[:2]}")
    try:
        done = subprocess.run([sys.executable, *argv], env=env, cwd=str(ROOT), capture_output=True, text=True,
                              timeout=remaining)
    except subprocess.TimeoutExpired as error:
        raise Stop(f"cap passed in {argv[:2]}") from error
    log.write_text((done.stdout or "") + "\n--- stderr\n" + (done.stderr or ""), encoding="utf-8")
    if done.returncode != 0:
        raise Stop(f"{argv[:2]} exited {done.returncode}; see {log.name}: {(done.stderr or done.stdout)[-600:]}")
    return done.stdout


def _rows(c, sql: str, **params) -> list[dict]:
    from sqlalchemy import text

    return [dict(r._mapping) for r in c.execute(text(sql), params)]


def stored(engine) -> dict:
    with engine.connect() as c:
        return {
            "actions": _rows(c, "SELECT s.site_code, a.id, a.action_code, a.origin_finding_id, a.raised_at, a.recorded_at "
                                "FROM domain_action a JOIN site s ON s.id = a.site_id ORDER BY a.action_no"),
            "intents": _rows(c, "SELECT i.action_id, i.declared_at, i.recorded_at FROM domain_action_intent i"),
            "completes": _rows(c, "SELECT s.site_code, w.occurred_at, w.recorded_at, l.action_id "
                                  "FROM domain_action_case_link l JOIN work_event w ON w.case_id = l.case_id "
                                  "AND w.kind = 'COMPLETE' JOIN site s ON s.id = l.site_id"),
            "findings": _rows(c, "SELECT s.site_code, f.finding_id, f.mechanism, f.created_at FROM finding_revision f "
                                 "JOIN site s ON s.id = f.site_id"),
            "selections": _rows(c, "SELECT s.site_code, a.window_start, a.selected_at FROM analytic_run_selection a "
                                   "JOIN site s ON s.id = a.site_id"),
            "jobs": _rows(c, "SELECT s.site_code, j.domain, j.available_at, j.created_at FROM recompute_job j "
                             "JOIN site s ON s.id = j.site_id WHERE j.cause_evidence_id IS NOT NULL"),
            "threads": _rows(c, "SELECT DISTINCT ON (e.thread_id) s.site_code, t.mechanism, e.thread_id, e.state, "
                                "e.effective_day, c.action_id FROM finding_thread_event e "
                                "JOIN finding_thread t ON t.id = e.thread_id JOIN site s ON s.id = t.site_id "
                                "LEFT JOIN chain_action_thread c ON c.thread_id = e.thread_id "
                                "ORDER BY e.thread_id, e.seq DESC"),
            "event_count": _rows(c, "SELECT count(*) AS n FROM finding_thread_event")[0]["n"],
            # The BUILD asserts the POST answered COMPLETED; the stored COMPLETE event on the linked WR is that state.
            "linked_case_events": _rows(c, "SELECT DISTINCT k.kind AS case_kind, w.kind AS event FROM work_case k "
                                           "JOIN domain_action_case_link l ON l.case_id = k.id "
                                           "JOIN work_event w ON w.case_id = k.id"),
        }


def between(value, lo, hi) -> bool:
    return lo <= value <= hi


def judge(doc: dict, data: dict, pairs: list, coh3: list, received: dict, cold_doc: dict, boards: dict,
          step_d: dict, tick_events: int) -> dict:
    """Every item of the ruling's pass list; each is a named boolean, so a fail names what failed."""
    checks: dict[str, bool] = {}
    for code, site in ((COLD, "cold"), (EV, "ev")):
        at = received[site]
        checks[f"pairs.{site}>=1"] = sum(1 for p in pairs if p[0] == code) >= 1
        action = next((a for a in data["actions"] if a["site_code"] == code), None)
        checks[f"action.{site}.exists"] = action is not None
        if action is None:
            continue
        lo = at + timedelta(minutes=10)
        checks[f"action.{site}.raised_at"] = action["raised_at"] == lo
        checks[f"action.{site}.recorded_at"] = between(action["recorded_at"], lo, lo + timedelta(minutes=2))
        worker = at + timedelta(minutes=5)
        site_findings = [f for f in data["findings"] if f["site_code"] == code]
        checks[f"findings.{site}.non_empty"] = bool(site_findings)
        checks[f"findings.{site}.created_at"] = all(f["created_at"] == worker for f in site_findings)
        linked = [t for t in data["threads"] if t["site_code"] == code and t["action_id"] == action["id"]]
        checks[f"thread.{site}.linked"] = bool(linked)
        checks[f"thread.{site}.ACTION_IN_HAND"] = bool(linked) and all(t["state"] == "ACTION_IN_HAND" for t in linked)
        board = boards.get(code) or {}
        hrefs = [str(i.get("href")) for r in board.get("rows") or [] for i in r.get("in_hand") or []]
        checks[f"board.{site}.in_hand_lists_action"] = any(str(action["id"]) in h for h in hrefs)
    checks["coh3.findings==0"] = not coh3
    completes = [w for w in data["completes"] if w["site_code"] == COLD]
    at = received["cold"]
    checks["cold.complete.exists"] = bool(completes)
    checks["cold.complete.recorded_at"] = bool(completes) and all(
        between(w["recorded_at"], at + timedelta(minutes=6), at + timedelta(minutes=10) - timedelta(microseconds=1))
        for w in completes)
    checks["cold.no_CHANGE_APPLIED"] = not any(
        t["site_code"] == COLD and t["state"] == "CHANGE_APPLIED" for t in data["threads"])
    checks["cold.applied_skipped"] = any("APPLIED" in json.dumps(s, default=str) for s in step_d.get("skipped_causes", []))
    checks["tick.writes_no_thread_event"] = tick_events == 0
    protect = [r for r in (boards.get(COLD) or {}).get("rows") or [] if r.get("category") == "PROTECT_ASSET"]
    checks["cold.protect.NEEDS_ATTENTION"] = bool(protect) and protect[0].get("state") == "NEEDS_ATTENTION"
    checks["cold.wr_completed"] = any(e["case_kind"] == "MAINTENANCE_REQUEST" and e["event"] == "COMPLETE"
                                      for e in data["linked_case_events"])
    checks["cold.blocked_null"] = all(d.get("blocked") is None for d in cold_doc["days"])
    return checks


def _board_view(body) -> dict:
    rows = (body or {}).get("rows") or []
    return {"issues": [i.get("text") for r in rows for i in r.get("issues") or []],
            "in_hand": [(i.get("text"), i.get("state_label")) for r in rows for i in r.get("in_hand") or []],
            "protect": [r.get("state") for r in rows if r.get("category") == "PROTECT_ASSET"],
            "window": (body or {}).get("window")}


def extra_reads(cc, client, picked: list, bundle, boards: dict) -> dict:
    """DD1b1-R2 §3: Cold over the UTC day (the collected board), the event window and the local day, on one DB; EV over
    the UTC day and the event window."""
    out: dict = {}
    for d in cc.day_windows(picked):
        code, start = d["site_code"], next(r for r in picked if r["site"] == ("cold" if d["site_code"] == COLD else "ev"))
        reads = {"utc_day": {"from": d["from"], "to": d["to"]},
                 "event_window": {"from": start["start"], "to": start["end"]}}
        if code == COLD:
            local = cc.at(start["start"]).astimezone(__import__("zoneinfo").ZoneInfo("Africa/Addis_Ababa"))
            lo = cc._midnight(local).astimezone(__import__("datetime").timezone.utc)
            reads["local_day"] = {"from": cc.iso(lo), "to": cc.iso(lo + timedelta(days=1))}
        out[code] = {}
        for name, params in reads.items():
            status, body = client.get(f"/api/sites/{code}/outcome-board", params)
            out[code][name] = {"status": status, **_board_view(body if status == 200 else None), "params": params}
        status, chain = client.get(f"/api/sites/{code}/chain", {"from": d["from"], "to": d["to"]})
        out[code]["chain_has_action_agreed"] = status == 200 and "Action agreed" in json.dumps(chain)
    return out


def judge_r2(doc: dict, bundle, extra: dict, data: dict) -> dict:
    checks: dict[str, bool] = {}
    for code, site in ((COLD, "cold"), (EV, "ev")):
        e = extra.get(code) or {}
        day, event = e.get("utc_day") or {}, e.get("event_window") or {}
        checks[f"r2.{site}.utc_day.finding_in_issues"] = bool(day.get("issues"))
        checks[f"r2.{site}.utc_day.in_hand_open_no_suffix"] = bool(day.get("in_hand")) and all(
            label == "Open" for _, label in day["in_hand"])
        checks[f"r2.{site}.chain_action_agreed"] = bool(e.get("chain_has_action_agreed"))
        checks[f"r2.{site}.event_window.finding_shown"] = bool(event.get("issues"))
        checks[f"r2.{site}.event_window.action_not_listed"] = not event.get("in_hand")
    checks["r2.cold.utc_day.protect_needs_attention"] = (extra.get(COLD, {}).get("utc_day", {}).get("protect")
                                                         == ["NEEDS_ATTENTION"])
    checks["r2.objectives_instants.three_sites"] = sorted(doc["objectives_instants"]) == [
        "COLD-LAB-001", "EV-LAB-001", "KOBO-001"]
    checks["r2.declare.cold_ev_inserted"] = all(
        any(x.get("site_code") == c and not x.get("refused") and not x.get("skipped") for x in doc["declare"][c])
        for c in (COLD, EV))
    return checks


def run(work: Path, doc: dict, deadline: float) -> dict:
    import demo_combined as dc
    import demo_story_days as sd
    import pg_harness
    from sqlalchemy import create_engine, text

    # Unrouted, `fresh_database` would reset the shared base database in place, so routing is required here.
    os.environ.setdefault("ASSETOPS_TEST_DATABASE_URL",
                          f"postgresql+psycopg://assetops:{dc.PW}@127.0.0.1:{dc.PG_PORT}/assetops_test")
    pg_harness.route("dd1b1")
    if not pg_harness.routed():
        raise Stop("not routed to a run-owned database; refusing to reset the shared base database")
    url = pg_harness.fresh_database()
    db = url.rsplit("/", 1)[-1].split("?")[0]
    if not db.endswith("_test") or "polish" in db or "demo3" in db or db == "assetops_test":
        raise Stop(f"not this run's own *_test database: {db}")
    doc["database"] = db
    env = {**os.environ, "DATABASE_URL": url, "ASSETOPS_TEST_DATABASE_URL": url, "PYTHONUNBUFFERED": "1"}
    keys = {name: secrets.token_hex(32) for name in dc.KEY_NAMES}
    env.update(keys)
    (work / "keys.json").write_text(json.dumps(keys), encoding="utf-8")

    engine = create_engine(url)
    with engine.connect() as c:
        db_now = c.execute(text("SELECT clock_timestamp()")).scalar_one()
    story = dc.resolve_story(db_now, days_doc=sd.load())
    rows = story.pop("days")
    instants = dc.objectives_instants({**story, "days": rows})   # DD1b1-R2 §5: all three Sites on real v3, no prepare
    doc["objectives_instants"] = {k: dc.iso(v) for k, v in instants.items()}
    picked = [r for r in rows if (r["site"], r["kind"]) in (("cold", "failure"), ("ev", "fault"))]
    if sorted(r["site"] for r in picked) != ["cold", "ev"]:
        raise Stop(f"expected one Cold failure and one EV fault day: {picked}")
    story["sites"] = ["cold", "ev"]
    (work / "story.json").write_text(json.dumps(story, indent=1), encoding="utf-8")
    (work / "days.json").write_text(json.dumps({"days": picked}, indent=1), encoding="utf-8")
    received = {r["site"]: dc.at(r["received_at"]) for r in picked}
    doc["received_at"] = {k: dc.iso(v) for k, v in received.items()}

    t0 = time.monotonic()
    for site in ("cold", "ev"):
        child([str(ROOT / "tools" / f"demo_combined_{site}.py"), "build", url, str(work)], env,
              work / f"{site}.log", deadline)
        doc["seconds"][site] = round(time.monotonic() - t0)
    out = child(["-m", "assetops_backend.chain.backfill", "--steps", "a,b,c,d"], env, work / "backfill.log", deadline)
    doc["seconds"]["backfill"] = round(time.monotonic() - t0)
    reports = [json.loads(line) for line in out.splitlines() if line.startswith(("{", "["))]
    flat = [x for r in reports for x in (r if isinstance(r, list) else r.get("steps", [r]))]
    step_d = next((r for r in flat if r.get("step") == "d"), {})
    doc["step_d"] = step_d

    before = stored(engine)["event_count"]
    for n in range(MAX_TICKS):
        child([*dc.TICK, "--no-prebuild"], env, work / f"tick{n}.log", deadline)
    tick_events = stored(engine)["event_count"] - before
    doc["tick_events"], doc["ticks"] = tick_events, MAX_TICKS
    doc["seconds"]["ticks"] = round(time.monotonic() - t0)

    import chain_coherence as cc
    from demo_combined_finish import app_client

    bundle_dir = work / "bundle"
    cc.collect(cc.InProcess(app_client(url, work)), story, picked, bundle_dir, "in-process")
    bundle = cc.Bundle(bundle_dir)
    pairs = list(cc.coh3_pairs(bundle))
    coh3 = cc.coh3_action_on_board(bundle)
    boards = {b.get("site_code"): b for b in (bundle.get(f"board.{d}") for d in bundle.day_windows()) if b}
    extra = extra_reads(cc, app_client(url, work), picked, bundle, boards)
    doc["extra"] = extra
    doc["declare"] = {}
    for code, instant in instants.items():
        out = child([str(ROOT / "tools" / "demo_declare_objectives.py"), url,
                     str(ROOT / "backend" / "conversions" / "demo-objectives.json"), code, dc.iso(instant)], env,
                    work / f"objectives-{code}.log", deadline)
        doc["declare"][code] = [json.loads(x) for x in out.splitlines() if x.startswith("{")]
    data = stored(engine)
    cold_doc = json.loads((work / "cold.json").read_text(encoding="utf-8"))
    doc["coh3_pairs"] = pairs
    doc["coh3_findings"] = coh3
    doc["stored"] = data
    doc["boards"] = {code: {"window": b.get("window"),
                            "rows": [{"category": r.get("category"), "state": r.get("state"),
                                      "in_hand": r.get("in_hand")} for r in b.get("rows") or []]}
                     for code, b in boards.items()}
    doc["cold_blocked"] = [d.get("blocked") for d in cold_doc["days"]]
    doc["checks"] = judge(doc, data, pairs, coh3, received, cold_doc, boards, step_d, tick_events)
    doc["checks"].update(judge_r2(doc, bundle, extra, data))
    engine.dispose()
    return doc


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        raise SystemExit(__doc__)
    work = Path(argv[0]).resolve()
    work.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    doc: dict = {"probe": "DD1b1-R Q6", "cap_seconds": CAP_SECONDS, "seconds": {}, "stopped": None}
    try:
        run(work, doc, started + CAP_SECONDS)
    except Stop as stop:
        doc["stopped"] = str(stop)
    finally:
        import pg_harness

        pg_harness.cleanup()  # this run's own database and template
    doc["wall_seconds"] = round(time.monotonic() - started)
    checks = doc.get("checks") or {}
    doc["pass"] = doc["stopped"] is None and bool(checks) and all(checks.values())
    (work / "probe.json").write_text(json.dumps(doc, indent=1, default=str), encoding="utf-8")
    print(json.dumps({"pass": doc["pass"], "stopped": doc["stopped"], "wall_seconds": doc["wall_seconds"],
                      "seconds": doc["seconds"], "failed": [k for k, v in checks.items() if not v],
                      "pairs": len(doc.get("coh3_pairs") or [])}, default=str))
    return 0 if doc["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
