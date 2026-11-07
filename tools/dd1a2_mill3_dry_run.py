"""DD1a2-R G1 and G2 (L2, own `*_test` DB, never a demo prepare). Drives the Kobo child's own build path for a part of the
v3 day list: `demo_combined_kobo.configure_at` and `run_day`, the mini-depth worker and the snapshot builder.

    python tools/dd1a2_mill3_dry_run.py g1 <work>          one registered day of each steady profile (S-13, S-12, S-8)
    python tools/dd1a2_mill3_dry_run.py mill3 <work>       v3's S-14 to S-5, then `assess()` in memory (no Action recorded)
    python tools/dd1a2_mill3_dry_run.py story-only <work>  S-14 and S-7 alone, the comparison for the mill3 build

ASSETOPS_TEST_DATABASE_URL names the DB (recreated). Writes `<work>/<mode>.json`. Never calls `demo_combined.py prepare`,
the finish rows, Cold or EV. A failed gate is reported, never tuned.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

GENERATOR = "generator-state@generator"
MODES = {"g1": (-13, -12, -8), "mill3": tuple(range(-14, -4)), "story-only": (-14, -7)}


def _rows(c, sql: str, *args) -> list[dict]:
    from sqlalchemy import text

    return [dict(r) for r in c.execute(text(sql), *args).mappings().all()]


def _local_day(t: datetime) -> str:
    return (t + timedelta(hours=3)).date().isoformat()


def report(engine, site_id, days: list[dict]) -> dict:
    """Per Site-local day: the generator intervals with their classes, Findings and money, as stored."""
    with engine.connect() as c:
        windows = _rows(c, "SELECT DISTINCT ON (assessment_key) assessment_key, window_start, window_end, claim_level, "
                           "result FROM assessment_revision WHERE site_id = :s AND assessment_key LIKE 'dispatch:%' "
                           "ORDER BY assessment_key, revision_no DESC", {"s": site_id})
        findings = _rows(c, "SELECT DISTINCT ON (finding_id) finding_id::text AS id, episode_start, episode_end, "
                            "candidate_minutes, necessary_minutes, indeterminate_minutes, claim_level, title, claim "
                            "FROM finding_revision WHERE site_id = :s ORDER BY finding_id, revision_no DESC", {"s": site_id})
        money = _rows(c, "SELECT to_jsonb(r) - 'id' AS row FROM financial_consequence_revision r WHERE site_id = :s",
                      {"s": site_id})
        # No fuel signal reaches evidence on this Site, so litres are the registered probe's figure; this is the
        # generator's delivered energy per reading (kW, 5 minutes).
        power = _rows(c, "SELECT e.source_time, e.normalized_value_text AS v FROM accepted_evidence e WHERE e.site_id = :s "
                         "AND e.device_id = 'generator-controller' AND e.signal_id = 'ac-power' "
                         "AND e.normalized_value_text ~ '^[0-9.]+$'", {"s": site_id})
        gen = _rows(c, "SELECT DISTINCT e.source_time, e.normalized_value_text AS v FROM accepted_evidence e WHERE "
                       "e.site_id = :s AND e.device_id = 'generator-controller' AND e.signal_id = 'status' "
                       "ORDER BY e.source_time", {"s": site_id})
        unserved = _rows(c, "SELECT r.source_time, r.normalized_value_text AS req, d.normalized_value_text AS got FROM "
                            "accepted_evidence r JOIN accepted_evidence d ON d.site_id = r.site_id AND d.source_time = "
                            "r.source_time AND d.device_id = 'clinic-meter' AND d.signal_id = 'delivered-power' WHERE "
                            "r.site_id = :s AND r.device_id = 'clinic-meter' AND r.signal_id = 'requested-power'", {"s": site_id})
        signals = _rows(c, "SELECT DISTINCT device_id, signal_id FROM accepted_evidence WHERE site_id = :s", {"s": site_id})
    per_day: dict[str, dict] = {}
    for d in days:
        per_day.setdefault(d["day"], {"kind": None, "runs": [], "generator_local": [], "generator_kwh": 0.0,
                                      "findings": [], "windows": []})
        if not d["complement_of"]:
            per_day[d["day"]]["kind"] = d["kind"]
        if d["scenario"]:
            per_day[d["day"]]["runs"].append(d["scenario"]["scenario_id"])
    began = {}
    for r in gen:
        day = _local_day(r["source_time"])
        if day not in per_day:
            continue
        local = (r["source_time"] + timedelta(hours=3)).strftime("%H:%M")
        if r["v"] == "RUNNING" and day not in began:
            began[day] = local
        elif r["v"] != "RUNNING" and day in began:
            per_day[day]["generator_local"].append([began.pop(day), local])
    for day, a in began.items():
        per_day[day]["generator_local"].append([a, "end"])
    for r in power:
        day = _local_day(r["source_time"])
        if day in per_day:
            per_day[day]["generator_kwh"] += float(r["v"]) * 5 / 60
    for v in per_day.values():
        v["generator_kwh"] = round(v["generator_kwh"], 3)
    for r in unserved:  # R3 check 1; the residential meter records no requested power, so only the clinic is comparable
        day = _local_day(r["source_time"])
        if day in per_day:
            # [readings, delivered != requested, a value missing (not a number)]
            u = per_day[day].setdefault("clinic_readings_unserved", [0, 0, 0])
            u[0] += 1
            try:
                u[1] += abs(float(r["req"]) - float(r["got"])) > 1e-9
            except (TypeError, ValueError):
                u[2] += 1
    for f in findings:
        day = _local_day(f["episode_start"])
        if day in per_day:
            per_day[day]["findings"].append({k: str(v) if k in ("episode_start", "episode_end") else v
                                             for k, v in f.items() if k not in ("id", "claim")})
    for w in windows:
        day = _local_day(w["window_start"] + timedelta(hours=1)) if w["window_start"] else None
        if day in per_day:
            per_day[day]["windows"].append({"key": w["assessment_key"].split(":")[1], "claim_level": w["claim_level"],
                                            "start": str(w["window_start"]), "end": str(w["window_end"]),
                                            "counts": (w["result"] or {}).get("counts"),
                                            "intervals": (w["result"] or {}).get("intervals")})
    return {"days": per_day, "signals": signals, "money_rows": len(money), "money": [m["row"] for m in money], "findings_total": len(findings)}


def main(mode: str, work: Path) -> int:
    import pg_harness
    import psycopg
    import test_s1_bindings_postgres as pgb
    import test_s6_verification_replay as rp
    from sqlalchemy import create_engine, text
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    import demo_combined as dc
    import demo_combined_kobo as dk
    import demo_story_days as sd

    began = time.monotonic()
    url = pg_harness.fresh_database()
    assert url.split("/")[-1].endswith("_test") and "polish" not in url and "demo3" not in url, "own *_test DB only"
    os.environ["DATABASE_URL"] = url
    work.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(url.replace("+psycopg", "")) as c:
        db_now = c.execute("SELECT clock_timestamp()").fetchone()[0]
    story = dc.resolve_story(db_now, days_doc=sd.load())
    rows = story.pop("days")
    keep = MODES[mode]
    picked = [r for r in rows if r["site"] == "kobo" and r["offset"] in keep]
    if mode == "story-only":
        picked = [r for r in picked if not r["complement_of"]]
    k = story["kobo"]
    install_at = dc.at(k["install_at"])
    days = sd.from_payload(picked)
    engine = create_engine(url)
    store = PostgresFoundationStore(url)
    result = pgb.imported(store, when=dc.at(k["import_at"]))
    pgb.convert(store, pgb.BindingService(store, pgb.Clock(install_at)), result.tenant, result.site, pgb.FIXTURE)
    dk.configure_at(store, result, install_at)
    with engine.begin() as c:
        c.execute(text("UPDATE gateway SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})
        c.execute(text("UPDATE source SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})
    dk.publish_price(url, dc.at(k["price_recorded_at"]))
    first = next(d.received_at for d in days if d.has_run)
    runner = rp.LabRunner(store, engine, result, first + timedelta(minutes=5))
    tmp = Path(tempfile.mkdtemp(prefix="dd1a2-", dir=str(work)))
    dk._OUTAGE.clear()
    try:
        for day in days:
            if day.has_run:
                done = dk.run_day(store, runner, tmp, day, dk.MANIFEST_V3)
                print("run", day.day, day.kind, day.scenario["scenario_id"], done["run_id"], f"{time.monotonic() - began:.0f}s",
                      flush=True)
    finally:
        pg_harness.dispose(runner.findings)
    # the worker's and the snapshot builder's own entry points, in process
    from assetops_backend.chain import backfill

    total = 0
    while True:  # as `demo_combined.drain_mini`
        done = subprocess.run([sys.executable, "-m", "assetops_backend.mini_depth.worker", "run-pending", "--limit", "500"],
                              capture_output=True, text=True, check=True, env=os.environ)
        line = [x for x in done.stdout.splitlines() if x.startswith("[")]
        outcomes = json.loads(line[-1]) if line else []
        failed = [o for o in outcomes if o.get("status") == "FAILED"]
        total += len(outcomes)
        print("mini-depth", total, "failed", failed[:2], f"{time.monotonic() - began:.0f}s", flush=True)
        if len(outcomes) < 500:
            break
    backfill.main(["--site", "KOBO-001", "--steps", "a"])
    ticks = settle_money(engine, result.site.id) if mode != "g1" else None
    out: dict = {"mode": mode, "S": story["S"], "db": url.split("/")[-1], "report": report(engine, result.site.id, picked),
                 "money_a": ticks}
    if mode == "mill3":
        out["mill3"] = mill3(url, result, dc.at(story["S"]))
    out["wall_s"] = round(time.monotonic() - began, 1)
    (work / f"{mode}.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    pg_harness.dispose(store)
    engine.dispose()
    print("wrote", work / f"{mode}.json", "wall", out["wall_s"], flush=True)
    return 0


def settle_money(engine, site_id, limit: int = 12) -> dict:
    """DD1a2-R2 MONEY-A: the prepare's own scheduled tick (`demo_combined.TICK`, `--consequence-items 100`) until the
    consequence rows stop changing for two ticks (or `limit` ticks). Reports the rows; no pricing is added here."""
    import demo_combined as dc

    history, stable = [], 0
    for n in range(limit):
        done = subprocess.run([sys.executable, *dc.TICK, "--no-prebuild"], capture_output=True, text=True, env=os.environ)
        with engine.connect() as c:
            rows = _rows(c, "SELECT count(*) AS n FROM financial_consequence_revision WHERE site_id = :s", {"s": site_id})[0]["n"]
        line = [x for x in done.stdout.splitlines() if x.startswith("{")]
        history.append({"tick": n + 1, "exit": done.returncode, "rows": rows, "stdout_tail": (line[-1] if line else done.stdout)[-400:],
                        "stderr_tail": done.stderr[-200:] if done.returncode else ""})
        print("tick", n + 1, "exit", done.returncode, "consequence rows", rows, flush=True)
        stable = stable + 1 if n and history[-2]["rows"] == rows else 0
        if stable >= 2:
            break
    with engine.connect() as c:
        keys = _rows(c, "SELECT column_name FROM information_schema.columns WHERE table_name = 'financial_consequence_revision'")
        rows = _rows(c, "SELECT to_jsonb(r) AS row FROM financial_consequence_revision r WHERE site_id = :s", {"s": site_id})
    return {"ticks": history, "columns": [k["column_name"] for k in keys], "rows": [r["row"] for r in rows]}


def mill3(url: str, result, S: datetime) -> dict:
    """R12 item 3: `assess()` with an in-memory plan, the effective day S-9, the baseline by `choose_days`."""
    from zoneinfo import ZoneInfo

    from assetops_backend.actions import verification_families as vf
    from assetops_backend.chain.composition import build_chain_services

    services = build_chain_services(url)
    try:
        tz = "Africa/Addis_Ababa"
        eff = (S + timedelta(days=-9)).date()
        lo, hi = vf.baseline_candidates(eff)[-1], vf.later_candidates(eff)[-1]
        lo = min(lo, *vf.baseline_candidates(eff))
        rows = [r for r in services.reader.latest(result.tenant.id, result.site.id, lo, hi, [vf.MEASURE])
                if r.measure == vf.MEASURE]
        cands = vf.baseline_candidates(eff)
        selection = vf.baseline_selection(vf.judged_grades(rows, cands), eff)
        plan = {"basis": {"effective_day": eff.isoformat(), "timezone": tz}, "baseline_selection": selection}
        today = datetime.now(ZoneInfo(tz)).date()
        verdict = vf.assess(plan, rows, today)
        span = [eff + timedelta(days=n) for n in range(-5, 5)]
        grades = vf.judged_grades(rows, span)
        kwh = vf.day_kwh(rows, span)
        return {"effective_day": eff.isoformat(), "today": today.isoformat(), "baseline_selection": selection,
                "assess": {k: v for k, v in verdict.items()},
                "days": {d.isoformat(): {"grade": grades[d], "productive_kwh": kwh[d]} for d in span}}
    finally:
        services.dispose()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], Path(sys.argv[2])))
