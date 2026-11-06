"""DD1a1-R6 L2 check (own `*_test` DB, no prepare): the Kobo `degraded` day with and without its three complements.

    python tools/dd1a1_degraded_check.py <with|without> <work-dir>     (ASSETOPS_TEST_DATABASE_URL names the DB)

Calendar: one `degraded` day, then a `normal` day after it (the next Site-day's gateway). `without` removes the
`degraded` kind's complements (the v1 degraded delivery). Writes `<work>/degraded.json`: per run the delivery record,
the accepted evidence by `received_at` (count, first and last source time), the gateway outbox after each outage run,
the findings and analytic runs per day. `tools/dd1a1_degraded_check.py compare <without.json> <with.json>` asserts R6."""

from __future__ import annotations

import json
import sys
import tempfile
import time
from datetime import timedelta
from pathlib import Path


def main(mode: str, work: Path) -> None:
    import pg_harness
    import psycopg
    import test_s1_bindings_postgres as pgb
    import test_s6_verification_replay as rp
    from sqlalchemy import create_engine, text
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    import demo_combined as dc
    import demo_combined_kobo as dk
    import demo_story_days as sd
    from demo_combined import at, iso

    url = pg_harness.fresh_database()
    doc = sd.load(sd.V2_FILE)
    doc["sites"] = {"kobo": [{"day": "S-3d", "kind": "degraded"}, {"day": "S-1d", "kind": "normal"},
                          {"day": "S+0d", "kind": "trial-before"}, {"day": "S+1d", "kind": "trial-after"}]}
    if mode == "without":
        for spec in doc["kinds"]["kobo"].values():
            spec.pop("complement", None)
    work.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(url.replace("+psycopg", "")) as c:
        db_now = c.execute("SELECT clock_timestamp()").fetchone()[0]
    story = dc.resolve_story(db_now, days_doc=doc)
    days_payload = story.pop("days")
    (work / "days.json").write_text(json.dumps({"S": story["S"], "days": days_payload, "doc": doc}, indent=2),
                                    encoding="utf-8")
    story["code"], story["sites"] = "probe", ["kobo"]
    days = [d for d in sd.from_payload(days_payload) if d.site == "kobo" and d.has_run]
    k = story["kobo"]
    install_at = at(k["install_at"])
    tmp = Path(tempfile.mkdtemp(prefix="kobo-degraded-", dir=str(work)))
    engine = create_engine(url)
    store = PostgresFoundationStore(url)
    dk._OUTAGE.clear()
    result = pgb.imported(store, when=at(k["import_at"]))
    pgb.convert(store, pgb.BindingService(store, pgb.Clock(install_at)), result.tenant, result.site, pgb.FIXTURE)
    dk.configure_at(store, result, install_at)
    with engine.begin() as c:
        c.execute(text("UPDATE gateway SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})
        c.execute(text("UPDATE source SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})
    dk.publish_price(url, at(k["price_recorded_at"]))
    runner = rp.LabRunner(store, engine, result, days[0].received_at + timedelta(minutes=5))
    records = []
    began = time.monotonic()
    for day in days:
        out = dk.run_day(store, runner, tmp, day, dk.MANIFEST_V3)
        records.append({"day": day.day, "kind": day.kind, "epoch": day.epoch, "received_at": iso(day.received_at),
                        "start": iso(day.start), "end": iso(day.end),
                        "published": out["published"], "run_id": out["run_id"]})
        print("run", day.day, day.kind, out["published"].get("delivered_batches"), flush=True)
    with engine.connect() as c:
        evidence = [dict(r) for r in c.execute(text(
            "SELECT received_at, count(*) AS n, min(source_time) AS first, max(source_time) AS last "
            "FROM accepted_evidence WHERE site_id = :s GROUP BY received_at ORDER BY received_at"),
            {"s": result.site.id}).mappings()]
        runs = [dict(r) for r in c.execute(text(
            "SELECT cohort_status, count(*) AS n FROM analytic_run WHERE site_id = :s GROUP BY cohort_status"),
            {"s": result.site.id}).mappings()]
        # DD1a1-R6 grade: per story-run window, the latest assessment revision per key (claim level and result)
        grades = {d.day: [dict(r) for r in c.execute(text(
            "SELECT DISTINCT ON (assessment_key) assessment_key, claim_level, result FROM assessment_revision "
            "WHERE site_id = :s AND window_start < :hi AND window_end > :lo ORDER BY assessment_key, revision_no DESC"),
            {"s": result.site.id, "lo": d.start, "hi": d.end}).mappings()]
            for d in days if d.kind in ("degraded", "normal", "trial-before", "trial-after")}
    findings = {d.day: dk.findings_on(engine, result.site.id, d.day) for d in days}
    doc_out = {"mode": mode, "runs": records, "evidence": evidence, "analytic_runs": runs, "findings": findings,
               "grades": grades,
               "gateway_dirs": sorted(p.name for p in tmp.glob("gw-*")), "wall_s": round(time.monotonic() - began, 1)}
    (work / "degraded.json").write_text(json.dumps(doc_out, indent=2, default=str), encoding="utf-8")


def compare(without: str, with_: str) -> int:
    a, b = (json.loads(Path(p).read_text(encoding="utf-8")) for p in (without, with_))
    fails: list[str] = []

    def check(ok: bool, what: str) -> None:
        print(("PASS " if ok else "FAIL ") + what)
        if not ok:
            fails.append(what)

    dday = next(r["day"] for r in b["runs"] if r["kind"] == "degraded")
    by = {r["kind"]: r for r in b["runs"] if r["day"] == dday or r["kind"] == "normal"}
    base = next(r for r in a["runs"] if r["kind"] == "degraded")["published"]
    story = by["degraded"]["published"]
    ne = by["night-early"]["published"]
    check(ne.get("delivered_batches", ne.get("publications")) == ne["batches"] > 0,
          "1 night-early arrives in full")
    check(story["delivered_batches"] == story["batches"] // 2 == base["delivered_batches"]
          and story["batches"] == base["batches"], "2 story run delivers batches//2, equal to v1")
    check(by["steady-afternoon"]["published"]["delivered_batches"] == 0
          and by["night-late"]["published"]["delivered_batches"] == 0, "3 steady-afternoon and night-late deliver 0")
    def ts(v) -> str:  # one comparable UTC text for DB timestamps and ISO strings
        return str(v).replace("T", " ").replace("Z", "+00:00")[:19]

    story_rx = ts(by["degraded"]["received_at"])
    day_lo, day_hi = ts(by["night-early"]["start"]), ts(by["night-late"]["end"])
    day_ev = [e for e in b["evidence"] if ts(e["received_at"]) <= story_rx and ts(e["first"]) >= day_lo]
    last_story = max((ts(e["last"]) for e in day_ev), default=None)
    # 4 + 6: any group received after the story run that holds a reading of the degraded local day is a false fill,
    # on the same day (a later complement) or on any later day (another gateway).
    stray = [e for e in b["evidence"] if ts(e["received_at"]) > story_rx and ts(e["first"]) < day_hi]
    v1_rows = sum(e["n"] for e in a["evidence"] if ts(e["received_at"]) == story_rx)
    story_rows = sum(e["n"] for e in b["evidence"] if ts(e["received_at"]) == story_rx)
    check(bool(day_ev) and not stray,
          f"4 no reading of the day received after the story run (last delivered {last_story}); stray={stray}")
    print(f"INFO story-run rows: with {story_rows}, v1 {v1_rows} (the delivered half follows the gateway's batch "
          f"order, which follows the build's source ids)")
    w = (by["night-late"]["published"].get("withheld_after") or {}).get("delivery") or {}
    wstate = w.get("batches_by_state", {})
    own = [by[k]["published"].get("outbox_after", {}).get("delivery") or {} for k in ("steady-afternoon", "night-late")]
    check(wstate.get("ACKED") == story["delivered_batches"] and wstate.get("READY") == story["batches"] - wstate["ACKED"]
          and all(o.get("batches_by_state", {}).get("READY") == o.get("batch_count") > 0 for o in own),
          f"5 outbox at day end holds the withheld half {wstate} and every complement batch "
          f"{[o.get('batches_by_state') for o in own]}")
    check(len(b["gateway_dirs"]) == len(set(r["epoch"] for r in b["runs"])) and
          by["degraded"]["epoch"] != by["normal"]["epoch"], "6 next day has its own gateway state (and 4: none of the"
                                                             " withheld readings arrive later)")
    check(not any(r["cohort_status"] == "AMBIGUOUS" for r in b["analytic_runs"]), "7 0 AMBIGUOUS")
    check(a["findings"][dday] == b["findings"][dday], f"7 degraded-day findings equal to v1 ({b['findings'][dday]})")
    import re

    def norm(rows):  # ids and digests differ per build; the claim and the measured result must not
        return json.loads(re.sub(r'"[0-9a-f]{8}-[0-9a-f-]{27}"|"[0-9a-f]{40,64}"|"run-[0-9a-f]{32}"', '"#"',
                                 json.dumps(rows, sort_keys=True, default=str)))

    ga, gb = norm(a["grades"].get(dday, [])), norm(b["grades"].get(dday, []))
    check(bool(ga) and [(g["assessment_key"], g["claim_level"]) for g in ga]
          == [(g["assessment_key"], g["claim_level"]) for g in gb],
          f"7 degraded-day assessment claim levels equal to v1 {[(g['assessment_key'], g['claim_level']) for g in gb]}")
    print("INFO degraded-day assessment results equal to v1:", ga == gb)
    # analytic-run counts are not compared: complements are assessed too, so "with" holds more runs than v1
    return 1 if fails else 0


if __name__ == "__main__":
    if sys.argv[1] == "compare":
        raise SystemExit(compare(sys.argv[2], sys.argv[3]))
    main(sys.argv[1], Path(sys.argv[2]))
