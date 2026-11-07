"""DD1b2-R probe, measures P5 to P7 (P1 to P4 are in `<work>/mill.json`, written by the real mill step). Development only;
never part of a prepare. Runs on a work folder that `prepare --sites kobo --no-finish` and `after-children` have built:

    python tools/dd1b2a_probe.py ticks --db <db> --work <work> --out .agent/DD-1b2a-probe.json

It samples before the ticks, then runs the real `Demo.tick(2)`, sampling after each tick, then reads the boards.
`sample` and `boards` are its children, run inside the private tree. A failed measure is reported, never tuned.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from datetime import timedelta
from pathlib import Path

BOARD_OFFSETS = (-15, -11, -8, -5, -1, 0, 1)
SITE = "KOBO-001"


def sample(url: str, work: Path, name: str) -> None:
    """The mill thread, the outcome count, the summary, and the pending `snapshots` events with their ids (P7)."""
    from sqlalchemy import create_engine, text

    from assetops_backend.actions.composition import build_action_store
    from assetops_backend.chain.composition import build_chain_services, load_event_register
    from demo_combined_mill import verification_service

    mill = json.loads((work / "mill.json").read_text(encoding="utf-8"))
    action_id = mill.get("action", {}).get("id")
    engine = create_engine(url)
    with engine.connect() as c:
        t, s = c.execute(text("SELECT tenant_id, id FROM site WHERE site_code = :c"), {"c": SITE}).one()
        def rows(sql: str, **kw) -> list:
            return [r[0] for r in c.execute(text(sql), {"s": s, **kw}).all()]
        link = rows("SELECT to_jsonb(x) FROM chain_action_thread x WHERE x.site_id = :s AND x.action_id = :a", a=action_id)
        thread = (link[0] if link else {}).get("thread_id")
        events = rows("SELECT jsonb_build_object('seq', e.seq, 'state', e.state, 'effective_day', e.effective_day, "
                      "'cause_kind', e.cause_kind, 'recorded_at', e.recorded_at) FROM finding_thread_event e "
                      "WHERE e.thread_id = :th ORDER BY e.seq", th=thread) if thread else []
        threads = rows("SELECT count(*) FROM finding_thread x WHERE x.site_id = :s")
        outcomes = rows("SELECT jsonb_build_object('outcome', o.outcome, 'recorded_at', o.recorded_at) FROM "
                        "verification_outcome o WHERE o.site_id = :s AND o.domain_action_id = :a", a=action_id)
        studies = rows("SELECT jsonb_build_object('first_day', o.first_day, 'last_day', o.last_day, 'created_at', "
                       "r.created_at, 'status', r.result->>'status', 'eligible_days', r.result->>'eligible_days') "
                       "FROM mini_opportunity_revision r JOIN mini_opportunity o ON o.id = r.opportunity_id WHERE "
                       "r.site_id = :s ORDER BY r.created_at, o.last_day")
        dirty = rows("SELECT count(*) FROM snapshot_dirty x WHERE x.site_id = :s")
    engine.dispose()
    register = load_event_register()
    types = sorted({k.partition("@")[0] for k in register.consumes("snapshots")})
    services = build_chain_services(url)
    store = build_action_store(url)
    try:
        pending = services.events.unconsumed("snapshots", t, s, types, 100000)
        summary = verification_service(store, services.reader, _wall()).domain_summary(t, s, action_id) if action_id else None
    finally:
        services.dispose()
        getattr(store, "dispose", lambda: None)()
    doc = {"name": name, "action_link": link, "thread_events": events, "threads_at_site": threads[0], "outcomes": outcomes,
           "studies": studies, "summary": summary, "snapshot_dirty": dirty[0], "pending_snapshots_count": len(pending),
           "pending_snapshots": [_event(e) for e in pending[:200]]}
    (work / f"sample-{name}.json").write_text(json.dumps(doc, indent=1, default=str), encoding="utf-8")
    print(name, "events", [e["state"] for e in events], "pending", len(pending), "dirty", dirty[0], "outcomes", len(outcomes))


def _wall():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)


def _event(event) -> dict:
    data = dataclasses.asdict(event) if dataclasses.is_dataclass(event) else dict(event._asdict())
    return {k: data.get(k) for k in data if k not in ("subject", "payload", "tenant_id", "site_id")}


def boards(url: str, work: Path) -> None:
    """P6: each board's Grow row as served, and the Portfolio's Grow line for the week ending S."""
    from demo_combined import at, iso, story_week_query
    from demo_combined_finish import app_client

    story = json.loads((work / "story.json").read_text(encoding="utf-8"))
    S, client = at(story["S"]), app_client(url, work)
    out: dict = {"boards": {}, "portfolio_week": None}
    for offset in BOARD_OFFSETS:
        day = (S + timedelta(days=offset)).date().isoformat()
        r = client.get(f"/api/sites/{SITE}/outcome-board", params={"date": day})
        body = r.json()
        grow = next((x for x in body.get("rows", []) if x.get("category") == "GROW_REVENUE"), None)
        out["boards"][f"S{offset:+d}"] = {"day": day, "http": r.status_code, "grow": grow,
                                          "failed_reads": body.get("failed_reads"), "status": body.get("status")}
    query = story_week_query(story)
    week = client.get(f"/api/estate/outcome-summary?{query}")
    out["portfolio_week"] = {"http": week.status_code, "query": query, "kobo": _kobo_summary(week)}
    out["S"] = iso(S)
    (work / "boards.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print("boards", {k: v["http"] for k, v in out["boards"].items()}, "portfolio", week.status_code)


def _kobo_summary(response) -> object:
    if response.status_code != 200:
        return response.text[:400]
    return next((x for x in response.json().get("sites", []) if x.get("site_code") == SITE), None)


def ticks(db: str, work_name: str, out: Path) -> None:
    from demo_combined import Demo

    this = str(Path(__file__).name)

    class Sampling(Demo):
        count = 0

        def child(self, *argv: str) -> None:
            done = self.py(str(self.tree / "tools" / this), *argv, cwd=self.tree / "backend" / "tests",
                           label=f"probe-{argv[0]}", check=False)
            print(done.stdout.strip().splitlines()[-1][:300] if done.stdout.strip() else "(no output)", flush=True)
            if done.returncode:
                print(done.stdout[-1500:], flush=True)

        def py(self, *argv, label="", **kw):
            done = super().py(*argv, label=label, **kw)
            if label == "tick":
                type(self).count += 1
                self.child("sample", self.url, str(self.work), f"after-tick-{type(self).count}")
            return done

    demo = Sampling(db, work_name)
    demo.child("sample", demo.url, str(demo.work), "before-ticks")
    demo.tick(times=2)
    demo.child("boards", demo.url, str(demo.work))
    read = lambda name: json.loads((demo.work / name).read_text(encoding="utf-8"))  # noqa: E731
    doc = {"db": db, "story": {k: read("story.json").get(k) for k in ("S", "code", "sites")},
           "mill": read("mill.json"), "after_children": read("after-children.json"),
           "samples": {n: read(f"sample-{n}.json") for n in ("before-ticks", "after-tick-1", "after-tick-2")},
           "boards": read("boards.json")}
    out.write_text(json.dumps(doc, indent=1, default=str), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "sample":
        sample(sys.argv[2], Path(sys.argv[3]), sys.argv[4])
    elif len(sys.argv) >= 2 and sys.argv[1] == "boards":
        boards(sys.argv[2], Path(sys.argv[3]))
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument("cmd", choices=["ticks"])
        parser.add_argument("--db", required=True)
        parser.add_argument("--work", required=True)
        parser.add_argument("--out", required=True)
        args = parser.parse_args()
        ticks(args.db, args.work, Path(args.out))
