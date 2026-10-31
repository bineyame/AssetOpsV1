"""DEMO-A U3 / DEMO-SPARSE U3: the Kobo (KOBO-001) story days of the combined demo dataset, run by
`tools/demo_combined.py` as a child.

    python tools/demo_combined_kobo.py build <database-url> <work>

It is the public replay of `backend/conversions/d-verification-window-v2.json` (the s602b REPLAY body,
`tools/s602b_verification_walkthrough.py`): two registered Lab runs of mini-grid v5 published by a real gateway
process, accepted by ordinary S2 batch ingestion, assessed (S3) and matched (S4); then recommendation -> accept ->
apply -> freeze plan -> later selection -> evaluation through the real Action API. The only change is the calendar:
a deep copy of the v2 manifest with every instant replaced from `<work>/story.json` (baseline received, assessed,
accepted, applied and frozen on story day S, the later run on S+1). Diesel price v1 is published at Kobo install
+ 1 h through the test-only recorded-time seam (DEMO-A0, Addendum 1 R1), so the trial is priced with a price known
before it. Then the prepared work records (two generator visits, two plans) through the work service.

DEMO-SPARSE: the Site is imported at `kobo.import_at` and converted at `kobo.install_at` (S-29d), the labelled demo
configurations take effect at commissioning (`configure_at`, Q1 ruling), and every Kobo entry of `<work>/days.json`
runs in build order: a day kind is one registered Lab run (`run_day`), the trial pair is the chain above at its place,
and a `missing` day writes nothing.
"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import demo_story_days as sd
from demo_combined import at, iso

FIXTURE_PRICES = Path(__file__).resolve().parents[1] / "backend" / "conversions" / "demo-diesel-price-publications.json"


def resolved_manifest(base: dict, story: dict) -> dict:
    """The v2 manifest on the story calendar: same scenario, seeds, profiles, reserve values and windows' length."""
    k = story["kobo"]
    M = copy.deepcopy(base)
    for name in ("baseline", "later"):
        for key in ("start", "end", "foundation_known_at", "received_at", "sequence_epoch"):
            M["runs"][name][key] = k["runs"][name][key]
    M["scenario"] = dict(k["runs"]["baseline"]["scenario"])
    M["action"].update({"finding_anchor_day": story["S_date"], "accept_at": k["action"]["accept_at"],
                        "apply_at": k["action"]["apply_at"], "effective_from": k["action"]["effective_from"]})
    M["plan"]["freeze_at"] = k["plan"]["freeze_at"]
    M["windows"]["baseline_start"] = k["windows"]["baseline_start"].replace("Z", "+00:00")
    M["windows"]["later_start"] = k["windows"]["later_start"].replace("Z", "+00:00")
    M["evaluate_at"] = k["evaluate_at"]
    return M


#: Q1 ruling (`.agent/DEMO-SPARSE-preflight.md`): the two labelled demo configurations take effect at Kobo
#: commissioning instead of their build dates; values byte-identical, only `effective_from` moves.
CONFIG_OFFSETS = {"properties": timedelta(minutes=10), "roles2": timedelta(minutes=10),
                  "roles3": timedelta(minutes=20), "known": timedelta(minutes=30)}


def configure_at(store, result, install_at: datetime) -> dict:
    """`pub.configure` on the story calendar: S3 demo configuration (generator values + roles-2) at install + 10 min,
    the S6 verification configuration (roles-3) at install + 20 min, both recorded at install + 30 min."""
    import test_s6_verification_publication as pub
    from assetops_backend.sites.binding_service import BindingService
    from assetops_backend.sites.demo_configuration import apply_demo_configuration

    s3, ver = copy.deepcopy(pub.S3_DEMO), copy.deepcopy(pub.VERIFICATION)
    s3["component_properties"]["effective_from"] = iso(install_at + CONFIG_OFFSETS["properties"])
    s3["bindings"]["effective_from"] = iso(install_at + CONFIG_OFFSETS["roles2"])
    ver["component_properties"]["effective_from"] = iso(install_at + CONFIG_OFFSETS["properties"])
    ver["bindings"]["effective_from"] = iso(install_at + CONFIG_OFFSETS["roles3"])
    for doc, base in ((s3, pub.S3_DEMO), (ver, pub.VERIFICATION)):
        assert doc["status"] == base["status"] and doc["status"].startswith("SIMULATED DEMO CONFIGURATION")
    clock = pub.registered.Clock(install_at + CONFIG_OFFSETS["known"])
    foundation, bindings = pub.registered.FoundationService(store, "demo", clock), BindingService(store, clock)
    apply_demo_configuration(store, foundation, bindings, result.tenant, result.site, s3)
    applied = apply_demo_configuration(store, foundation, bindings, result.tenant, result.site, ver)
    assert applied.periods[-1]["role_set"] == "minigrid-roles-3"
    return {"labels": [s3["label"], ver["label"]],
            "properties_effective_from": s3["component_properties"]["effective_from"],
            "roles2_effective_from": s3["bindings"]["effective_from"],
            "roles3_effective_from": ver["bindings"]["effective_from"],
            "recorded_at": iso(install_at + CONFIG_OFFSETS["known"])}


def publish_price(url: str, recorded_at: datetime) -> None:
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.publish_assumption import main as publish
    import pg_harness

    store = PostgresAssumptionStore(url, test_recorded_clock_override=lambda: recorded_at)
    try:
        code = publish(["fixture", "--site", "KOBO-001", "--file", str(FIXTURE_PRICES), "--step", "v1"], store=store)
    finally:
        pg_harness.dispose(store)
    if code != 0:
        raise SystemExit(f"diesel price v1 publication failed ({code})")


def write_work(url: str, store, result, story: dict) -> dict:
    from test_w401_work_service_postgres import PRINCIPAL, event, plan, record, request
    from assetops_backend.work.composition import build_work_service

    k = story["kobo"]
    tenant, site = result.tenant.id, result.site.id
    assets = store.registrations(tenant, site).assets
    by_type = {}
    for a in assets:
        by_type.setdefault(a.asset_type, []).append(a)
    work = build_work_service(url)
    out = {"visits": [], "plans": []}
    try:
        for v in k["visits"]:
            asset = by_type[v["asset_type"]][0]
            when = at(v["at"])
            s, case = work.create_case(tenant, site, request(
                f"demo3-kobo-{v['key']}", title=v["title"], occurred_at=iso(when), asset_id=str(asset.id),
                finding_links=[]), PRINCIPAL)
            assert s == 201, (v["key"], s, case)
            s, rec = work.post_record(tenant, site, case["id"], record(
                f"demo3-kobo-{v['key']}-rec", activity=v["title"], occurred_at=iso(when + timedelta(minutes=20)),
                outcome_note=v["note"]), PRINCIPAL)
            assert s == 201, (v["key"], s, rec)
            s, a = work.post_event(tenant, site, case["id"], event(
                "ASSIGN", {"assignee": "Site technician"}, f"demo3-kobo-{v['key']}-assign",
                occurred_at=iso(when + timedelta(minutes=21))), PRINCIPAL)
            assert s == 201, (v["key"], s, a)
            s, c = work.post_event(tenant, site, case["id"], event(
                "COMPLETE", {"maintenance_record_id": rec["id"]}, f"demo3-kobo-{v['key']}-complete",
                occurred_at=iso(when + timedelta(minutes=22))), PRINCIPAL)
            assert s == 201 and c["state"] == "COMPLETED", (v["key"], s, c)
            out["visits"].append({"key": v["key"], "id": case["id"], "code": case.get("code"), "record_id": rec["id"],
                                  "asset": asset.asset_code, "occurred_at": iso(when)})
        for p in k["plans"]:
            asset = by_type[p["asset_type"]][0]
            s, pl = work.post_plan(tenant, site, plan(
                f"demo3-kobo-{p['key']}", asset_id=str(asset.id), title=p["title"], trigger_kind=p["trigger_kind"],
                next_due_at=p["due_at"], next_due_hours=p["due_hours"], occurred_at=p["at"]), PRINCIPAL)
            assert s == 201, (p["key"], s, pl)
            out["plans"].append({"key": p["key"], "id": str(pl.get("canonical_plan_id") or pl.get("id")),
                                 "title": p["title"], "asset": asset.asset_code, "due_at": p["due_at"]})
    finally:
        work._store.dispose()
    return out


def day_manifest(base: dict, day: "sd.DayRun") -> dict:
    """The v2 manifest for one story day: that day's scenario and instants; seed and profiles unchanged."""
    M = copy.deepcopy(base)
    M["scenario"] = dict(day.scenario)
    M["runs"] = {"day": {"start": iso(day.start), "end": iso(day.end), "seed": base["runs"]["baseline"]["seed"],
                         "sequence_epoch": day.epoch, "foundation_known_at": iso(day.known_at),
                         "received_at": iso(day.received_at)}}
    return M


def findings_on(engine, site_id, day: str) -> list[str]:
    from sqlalchemy import text

    lo = at(day + "T00:00:00Z")
    with engine.connect() as c:
        rows = c.execute(text("SELECT DISTINCT finding_id FROM finding_revision WHERE site_id = :s AND "
                              "episode_start < :hi AND episode_end > :lo ORDER BY finding_id"),
                         {"s": site_id, "lo": lo, "hi": lo + timedelta(days=1)}).fetchall()
    return [str(r[0]) for r in rows]


def run_day(store, runner, tmp: Path, day: "sd.DayRun", base: dict) -> dict:
    """One registered Lab run on its story day: draft -> real gateway -> S2 acceptance at `received_at`; when the
    kind assesses at build, S3 assess + S4 match at `received_at + 5 min` (a `tick` day waits for the schedule)."""
    import test_s6_verification_replay as rp

    M = day_manifest(base, day)
    spec = M["runs"]["day"]
    run, _ = rp._draft(store, spec, M)
    published = rp._publish_and_accept(tmp / f"{day.day}-{day.kind}", run, spec["sequence_epoch"],
                                       rp._at(spec["received_at"]))
    if day.assess == "build":
        runner.now = max(runner.now, day.received_at + timedelta(minutes=5))
        runner.step({"do": "assess"}); runner.step({"do": "match"})
    return {"run_id": str(getattr(run, "run_id", None) or getattr(run, "id", "")), "published": published}


def build(url: str, work: Path, story: dict) -> dict:
    import pg_harness
    import test_s1_bindings_postgres as pgb
    import test_s6_verification_replay as rp
    from sqlalchemy import create_engine, text
    from test_s6_verification_plan_postgres import verifying
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    days = [d for d in sd.from_payload(json.loads((work / "days.json").read_text(encoding="utf-8"))["days"])
            if d.site == "kobo"]
    k = story["kobo"]
    install_at = at(k["install_at"])
    M = resolved_manifest(rp.MANIFESTS["v2"], story)
    tmp = Path(tempfile.mkdtemp(prefix="kobo-replay-", dir=str(work)))
    engine = create_engine(url)
    store = PostgresFoundationStore(url)
    result = pgb.imported(store, when=at(k["import_at"]))
    pgb.convert(store, pgb.BindingService(store, pgb.Clock(install_at)), result.tenant, result.site, pgb.FIXTURE)
    configuration = configure_at(store, result, install_at)
    with engine.begin() as c:
        c.execute(text("UPDATE gateway SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})
        c.execute(text("UPDATE source SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})
    publish_price(url, at(k["price_recorded_at"]))
    first = next(d.received_at for d in days if d.has_run)
    runner = rp.LabRunner(store, engine, result, first + timedelta(minutes=5))
    h = verifying(runner)
    published, records, ids = {}, [], {}
    try:
        for n, day in enumerate(days):
            entry = {"day": day.day, "offset": day.offset, "kind": day.kind, "as": day.as_kind,
                     "scenario": day.scenario, "run_id": None, "assess": day.assess,
                     "received_at": iso(day.received_at) if day.received_at else None}
            if day.kind == "trial-after":
                continue  # run by the trial-before entry's chain, next in the build order
            if day.kind == "trial-before":
                assert days[n + 1].kind == "trial-after", "the trial pair must be adjacent in the Kobo build order"
                ids = _trial_chain(store, runner, h, tmp, M, published)
                for d, name in ((day, "baseline"), (days[n + 1], "later")):
                    records.append({**entry, "day": d.day, "offset": d.offset, "kind": d.kind,
                                    "received_at": iso(d.received_at),
                                    "run_id": (ids["runs"][name] or [None])[0]})
                print("kobo trial", day.day, ids["action_code"], flush=True)
                continue
            if day.has_run:
                entry.update(run_day(store, runner, tmp, day, rp.MANIFESTS["v2"]))
            records.append(entry)
            print("kobo day", day.day, day.kind, entry.get("run_id"), flush=True)
        for r in records:
            r["findings"] = findings_on(engine, result.site.id, r["day"])
            r["status_after_build"] = ("NO_RUN" if r["kind"] == "missing" else
                                       "ASSESSED" if r["assess"] == "build" else "AWAITING_TICK")
        work_rows = write_work(url, store, result, story)
    finally:
        h.close()
        pg_harness.dispose(runner.findings)
        pg_harness.dispose(store)
        engine.dispose()
    ids.update({"install_at": k["install_at"], "import_at": k["import_at"],
                "price_recorded_at": k["price_recorded_at"], "configuration": configuration,
                "trial": k["trial"], "window_hour": k["trial"]["window_hour"],
                "published": published, "work": work_rows, "days": records})
    (work / "kobo.json").write_text(json.dumps(ids, indent=2, default=str), encoding="utf-8")
    cc = ids["cost_check"] or {}
    print("kobo:", len([r for r in records if r["run_id"]]), "runs; VERIFIED", ids["action_code"], "cost_check",
          cc.get("state"), cc.get("reason"))
    return ids


def _trial_chain(store, runner, h, tmp: Path, M: dict, published: dict) -> dict:
    """The DEMO-A chain (s602b REPLAY body) at the trial pair's place: baseline run, accept, apply, freeze, later
    run, evaluation through the real Action API."""
    import test_s6_verification_replay as rp

    act, win = M["action"], M["windows"]
    spec = M["runs"]["baseline"]
    base_run, _ = rp._draft(store, spec, M)
    published["baseline"] = rp._publish_and_accept(tmp / "baseline", base_run, spec["sequence_epoch"],
                                                   rp._at(spec["received_at"]))
    runner.now = max(runner.now, rp._at(spec["received_at"]) + timedelta(minutes=5))
    runner.step({"do": "assess"}); runner.step({"do": "match"})
    h.clock.at = rp._at(act["accept_at"])
    finding = h.findings()[act["finding_anchor_day"]]
    rec = h.recommendation(finding).json()
    made = h.accept(finding, rec["proposal"], idempotency_key="demo3-accept-0001")
    assert made.status_code == 201, made.text
    action_id = made.json()["action"]["action_id"]
    h.clock.at = rp._at(act["apply_at"])
    current = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}").json()["application_basis"][
        "current_foundation_revision_id"]
    applied = h.client.post(f"/api/sites/KOBO-001/actions/{action_id}/apply", json={
        "expected_foundation_revision_id": current, "value": act["reserve_new"],
        "effective_from": act["effective_from"], "idempotency_key": "demo3-apply-0001"})
    assert applied.status_code == 201, applied.text
    runner.now = max(runner.now, h.clock.at); runner.step({"do": "assess"}); runner.step({"do": "match"})
    h.clock.at = max(rp._at(M["plan"]["freeze_at"]), runner.now + timedelta(minutes=1))
    base = f"/api/sites/KOBO-001/actions/{action_id}/verification"
    frozen = h.client.post(f"{base}/plans", json={"baseline_start": win["baseline_start"],
                                                  "later_start": win["later_start"],
                                                  "idempotency_key": "demo3-freeze-0001"})
    assert frozen.status_code == 201, frozen.text
    plan = frozen.json()["plan"]
    spec = M["runs"]["later"]
    later_run, _ = rp._draft(store, spec, M)
    published["later"] = rp._publish_and_accept(tmp / "later", later_run, spec["sequence_epoch"],
                                                rp._at(spec["received_at"]))
    runner.now = max(runner.now, rp._at(spec["received_at"]) + timedelta(minutes=5))
    runner.step({"do": "assess"}); runner.step({"do": "match"})
    h.clock.at = max(rp._at(M["evaluate_at"]), runner.now + timedelta(minutes=1))
    bound = h.client.post(f"{base}/plans/{plan['plan_id']}/later-selection",
                          json={"idempotency_key": "demo3-bind-0001"})
    assert bound.status_code == 201, bound.text
    made = h.client.post(f"{base}/evaluations", json={"idempotency_key": "demo3-eval-0001"})
    assert made.status_code == 201, made.text
    outcome = made.json()["outcome"]
    assert outcome["outcome"] == "VERIFIED", outcome["reasons"]
    action = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}").json()
    events = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}/events").json()["events"]
    sources = outcome["basis"]["source_resolutions"]
    ids = {
        "manifest": {"base": "backend/conversions/d-verification-window-v2.json",
                     "story": "backend/conversions/demo-combined-story-v1.json",
                     "days": "backend/conversions/demo-story-days-v1.json", "scenario": M["scenario"],
                     "model_profile": M["model_profile"], "resolved": {k: M[k] for k in ("runs", "action", "plan",
                                                                                          "windows", "evaluate_at")}},
        "finding": str(finding), "finding_revision": rec["revision_id"],
        "action": action_id, "action_code": action["action"]["action_code"],
        "change": action["change"]["change_id"], "plan": plan["plan_id"],
        "outcome": outcome["outcome_id"], "outcome_recorded_at": outcome["recorded_at"],
        "outcome_reasons": outcome["reasons"],
        "cost_check": (action.get("verification") or {}).get("cost_check"),
        "events": [{"id": e["id"], "kind": e["kind"], "recorded_at": e["recorded_at"]} for e in events],
        "runs": {name: [r.get("run_id") for r in sources[name]["runs"]] for name in ("baseline", "later")},
    }
    return ids


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] != "build":
        raise SystemExit("usage: demo_combined_kobo.py build <database-url> <work>")
    work_dir = Path(sys.argv[3])
    build(sys.argv[2], work_dir, json.loads((work_dir / "story.json").read_text(encoding="utf-8")))
