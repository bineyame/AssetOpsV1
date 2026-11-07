"""DD1b2-R6 O2 / R7 Q1-Q4: the R8 drain's counts and its stop logic.

`counts` runs inside the private tree (it imports the tree's `assetops_backend`) and prints one JSON line. The pure
functions (`site_total`, `n_for`, `step`) are the rule the parent applies after every raw tick. Nothing here is a tuned
number: 200 is the tick's own `chain_snapshot_items`, and N follows R6 O2 with R7 Q4 (the maximum over Sites).
"""
from __future__ import annotations

import json
import math
import sys

CHAIN_SNAPSHOT_ITEMS = 200  # `TickLimits.chain_snapshot_items`; the tick drains this many dirty rows per Site
FIELDS = ("dirty", "snapshots_pending", "threads_pending", "mini_deferred", "opportunity_live")
STUCK_IDS = 10


def site_total(site: dict) -> int:
    return sum(int(site[f]) for f in FIELDS)


def total(counts: dict) -> int:
    return sum(site_total(s) for s in counts.values())


def n_for(counts: dict) -> int:
    """R6 O2 with R7 Q4: N = the maximum over Sites of ceil((dirty + snapshots pending) / 200) + 2."""
    if not counts:
        return 2
    return max(math.ceil((int(s["dirty"]) + int(s["snapshots_pending"])) / CHAIN_SNAPSHOT_ITEMS) + 2
               for s in counts.values())


def signature(counts: dict) -> str:
    """What "flat" compares: every count and the stuck event ids per Site."""
    return json.dumps({k: {**{f: v[f] for f in FIELDS}, "ids": v.get("pending_ids", [])}
                       for k, v in sorted(counts.items())}, sort_keys=True)


def step(history: list[dict], ticks: int, n: int) -> tuple[str, str]:
    """Decide after tick number `ticks` (>= 1), given the counts read after each tick (`history[-1]` the latest).

    Returns ("done" | "continue" | "over_n" | "fail", reason). `over_n` means continue past N while the totals still
    fall; past 2N, or two consecutive flat ticks, is a fail (the same stuck ids on two ticks is a stop)."""
    latest = history[-1]
    if total(latest) == 0:
        return "done", "all counts are 0"
    if ticks > 2 * n:
        return "fail", f"past 2N: {ticks} ticks with N={n}"
    if len(history) >= 3 and signature(history[-1]) == signature(history[-2]) == signature(history[-3]):
        return "fail", "two flat ticks in a row (same counts and same pending event ids)"
    return ("over_n", f"tick {ticks} is past N={n}; counts still moving") if ticks > n else ("continue", "")


def tick_failures(output: str) -> dict:
    """DD1b2-R8 C1: what a non-zero tick says, per Site. The tick prints one JSON report; each Site's `failure` triple
    (stage, code, detail) is taken from it. If no JSON line parses, the last output line is kept, so the record is
    never empty."""
    lines = [x for x in output.splitlines() if x.startswith("{")]
    try:
        report = json.loads(lines[-1])
        sites = {s.get("site_code") or str(s.get("site_id")): s.get("failure")
                 for s in report.get("sites", []) if s.get("result") == "FAILED" or s.get("failure")}
        return {"outcome": report.get("outcome"), "failure": report.get("failure"), "sites": sites}
    except (IndexError, ValueError, AttributeError):
        tail = output.strip().splitlines()
        return {"unparsed": (tail[-1] if tail else "(no output)")[:300]}


def counts(url: str) -> dict:
    """Per Site (by code): dirty rows, pending `snapshots` and `threads` events, Kobo-style mini jobs still PENDING or
    LEASED, and live opportunity jobs (PENDING or LEASED). Counted from the DB, not from the tick's report."""
    from sqlalchemy import text

    from assetops_backend.analytics.composition import build_postgres_assessment_store
    from assetops_backend.chain.adapters.postgres_event_store import PostgresEventStore
    from assetops_backend.chain.composition import load_event_register

    register = load_event_register()
    types = {c: sorted({k.partition("@")[0] for k in register.consumes(c)}) for c in ("snapshots", "threads")}
    events = PostgresEventStore(url)
    assessment = build_postgres_assessment_store(url)
    out: dict[str, dict] = {}
    try:
        with events._engine.connect() as c:
            sites = c.execute(text("SELECT tenant_id, id, site_code FROM site ORDER BY site_code")).all()
        for tenant, site, code in sites:
            with events._engine.connect() as c:
                ids = [str(r[0]) for r in c.execute(text(
                    "SELECT o.event_id FROM event_outbox o WHERE o.tenant_id = :t AND o.site_id = :s "
                    "AND o.type = ANY(:ty) AND NOT EXISTS (SELECT 1 FROM event_consumption x WHERE x.consumer = 'snapshots' "
                    "AND x.event_id = o.event_id) ORDER BY o.event_id LIMIT :n"),
                    {"t": tenant, "s": site, "ty": types["snapshots"], "n": STUCK_IDS})]
            out[code] = {
                "dirty": events.queued(tenant, site),
                "snapshots_pending": events.pending("snapshots", tenant, site, types["snapshots"]),
                "threads_pending": events.pending("threads", tenant, site, types["threads"]),
                "mini_deferred": sum(1 for j in assessment.live_mini_jobs(tenant, site)
                                     if j["status"] in ("PENDING", "LEASED")),
                "opportunity_live": len(assessment.live_opportunity_jobs(tenant, site)),
                "pending_ids": ids,
            }
    finally:
        events.dispose()
        assessment.dispose() if hasattr(assessment, "dispose") else None
    return out


if __name__ == "__main__":
    import os

    if len(sys.argv) > 1 and sys.argv[1] == "counts":
        print(json.dumps(counts(os.environ["DATABASE_URL"]), default=str))
    else:
        raise SystemExit("usage: demo_combined_drain.py counts")
