"""CH-2 backfill (design §12; build sheet CH-2 §4): place every stored Finding and opportunity on its thread and link
every Action to its thread.

    python -m assetops_backend.chain.backfill [--tenant <slug>] [--site <code>] [--steps b,c] [--dry-run]

- (a) snapshots: runs only when CH-1a's `assetops_backend.chain.builder` is importable, else reports skipped.
- (b) `plan_place` over `sources()` in `(created_at, id)` order. (c) `link_action` over the unlinked Actions.
- (d) belongs to CH-3 and reports skipped; (e) is the coherence rule COH-11 (ruling R1).

`--dry-run` runs (b) and (c) in memory from the stored sources (SELECT only; it also reads a database below 0042)
and prints the planned threads, occurrences and links. A non-dry run is refused on the protected demonstration
databases. One JSON line per step. Exit 1 without DATABASE_URL, 2 for a refused tenant, Site or database.
The tick's `chain_threads` stage runs `run_threads` (steps b and c) for one Site.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Sequence
from uuid import UUID

from assetops_backend.chain.threads import MemoryThreads, ThreadRegistry
from assetops_backend.config import DEVELOPMENT_TENANT_SLUG, database_url

PROTECTED_DATABASES = ("assetops_polish_full_test", "assetops_demo3_full_test")
STEPS = ("a", "b", "c", "d", "e")


def run_threads(reader: Any, store: Any, tenant_id: UUID, site_id: UUID | None, steps: Sequence[str] = ("b", "c"),
                created_by: str = "backfill") -> list[dict[str, Any]]:
    """Steps (b) and (c) against the store (written). Returns one result per step run."""
    registry = ThreadRegistry(store, created_by)
    out: list[dict[str, Any]] = []
    if "b" in steps:
        report = registry.place_all(reader.sources(tenant_id, site_id))
        out.append({"step": "b", "counts": dict(sorted(report.counts.items())),
                    "written": sum(v for k, v in report.counts.items() if k not in ("ALREADY_PLACED", "MERGED_INTO"))})
    if "c" in steps:
        report = registry.link_all(reader.unlinked_actions(tenant_id, site_id))
        out.append({"step": "c", "counts": dict(sorted(report.counts.items())),
                    "written": report.counts.get("LINKED", 0)})
    return out


def dry_run(reader: Any, tenant_id: UUID, site_id: UUID | None, steps: Sequence[str]) -> list[dict[str, Any]]:
    """Steps (b) and (c) in memory; prints the planned rows per Site without writing anything."""
    memory = MemoryThreads()
    registry = ThreadRegistry(memory, "backfill")
    out: list[dict[str, Any]] = []
    codes = dict((str(sid), code) for sid, code in reader.site_ids(tenant_id))
    if "b" in steps:
        report = registry.place_all(reader.sources(tenant_id, site_id))
        labels = reader.opportunity_labels(tenant_id)
        threads = []
        for tid, t in sorted(memory.threads.items(), key=lambda kv: (codes.get(str(kv[1]["site_id"]), ""),
                                                                      kv[1]["mechanism"], kv[1]["subject_ref"])):
            occ = sorted((o for (x, _), o in memory.occurrences.items() if x == tid), key=lambda o: o["occurrence_no"])
            threads.append({"site_code": codes.get(str(t["site_id"])), "thread_id": str(tid),
                            "mechanism": t["mechanism"], "subject_kind": t["subject_kind"],
                            "subject_ref": t["subject_ref"], "finding_type": t["finding_type"],
                            "occurrences": [{"no": o["occurrence_no"],
                                             "finding_id": None if o["finding_id"] is None else str(o["finding_id"]),
                                             "opportunity": None if o["opportunity_id"] is None
                                             else labels.get(str(o["opportunity_id"])),
                                             "episode_start": None if o["episode_start"] is None
                                             else o["episode_start"].isoformat()} for o in occ]})
        out.append({"step": "b", "dry_run": True, "counts": dict(sorted(report.counts.items())),
                    "threads_planned": len(memory.threads), "occurrences_planned": len(memory.occurrences),
                    "events_planned": len(memory.events), "threads": threads})
    if "c" in steps:
        actions = reader.all_actions(tenant_id, site_id)
        report = registry.link_all(actions)
        code_of = {str(a["id"]): a["action_code"] for a in actions}
        out.append({"step": "c", "dry_run": True, "counts": dict(sorted(report.counts.items())),
                    "links": [{"action_code": code_of.get(str(link["action_id"])), "kind": kind,
                               "thread_id": str(link["thread_id"]), "origin_finding_id": str(link["origin_finding_id"])}
                              for (kind, _), link in sorted(memory.links.items(),
                                                            key=lambda kv: code_of.get(str(kv[0][1]), ""))]})
    return out


def _step_a(reader: Any, tenant_id: UUID, site_id: UUID | None, url: str | None, dry_run: bool,
            services: Any = None) -> dict[str, Any]:
    """Step (a): CH-1a `build_range` for each selected Site, from its first accepted evidence day to today (the
    snapshots CLI's default range). A dry run writes nothing and builds no services; it names the Sites."""
    sites = reader.site_ids(tenant_id)
    if site_id is not None:
        sites = [s for s in sites if s[0] == site_id]
    if dry_run:
        return {"step": "a", "dry_run": True, "sites": [code for _, code in sites],
                "note": "would build_range from each Site's first evidence day to today"}
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from assetops_backend.chain.composition import build_chain_services
    owns = services is None
    services = build_chain_services(url) if owns else services
    if services is None:
        return {"step": "a", "skipped": "no database URL"}
    results: list[dict[str, Any]] = []
    try:
        for _, code in sites:
            site = services.inputs.site(tenant_id, code)
            if site is None:
                results.append({"site_code": code, "skipped": "not found"})
                continue
            first = services.inputs.first_evidence_time(tenant_id, site.site_id)
            if first is None:
                results.append({"site_code": code, "written": 0, "considered": 0, "note": "no accepted evidence"})
                continue
            tz = ZoneInfo(site.timezone)
            from_day, to_day = first.astimezone(tz).date(), datetime.now(tz).date()
            out = services.builder.build_range(tenant_id, site, from_day, to_day)
            results.append({"site_code": code, "from": from_day.isoformat(), "to": to_day.isoformat(),
                            "considered": len(out), "written": sum(1 for w in out if w.written)})
    finally:
        if owns:
            services.dispose()
    return {"step": "a", "sites": results, "written": sum(r.get("written", 0) for r in results)}


def main(argv: Sequence[str] | None = None, *, reader: Any = None, store: Any = None,
         chain_services: Any = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m assetops_backend.chain.backfill")
    parser.add_argument("--tenant", default=DEVELOPMENT_TENANT_SLUG)
    parser.add_argument("--site")
    parser.add_argument("--steps", default="a,b,c,d,e")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    steps = [s.strip() for s in args.steps.split(",") if s.strip()]
    if any(s not in STEPS for s in steps):
        print(f"Unknown step in {args.steps!r}; steps are {','.join(STEPS)}.", file=sys.stderr)
        return 2
    if args.tenant != DEVELOPMENT_TENANT_SLUG:
        print(f"Tenant {args.tenant!r} is not the configured development tenant.", file=sys.stderr)
        return 2
    url = database_url()
    if reader is None:
        from assetops_backend.chain.composition import build_thread_sources
        reader = build_thread_sources(url)
    if reader is None:
        print("DATABASE_URL is not set; nothing was written.", file=sys.stderr)
        return 1
    if not args.dry_run and reader.database_name() in PROTECTED_DATABASES:
        print(f"Database {reader.database_name()!r} is read-only for the backfill; use --dry-run.", file=sys.stderr)
        return 2
    tenant_id = reader.tenant_id(args.tenant)
    if tenant_id is None:
        print(f"No tenant {args.tenant!r}; nothing was written.", file=sys.stderr)
        return 2
    site_id = None
    if args.site is not None:
        found = reader.site_ids(tenant_id, args.site)
        if not found:
            print(f"No Site {args.site!r}; nothing was written.", file=sys.stderr)
            return 2
        site_id = found[0][0]
    results: list[dict[str, Any]] = []
    if "a" in steps:
        results.append(_step_a(reader, tenant_id, site_id, url, args.dry_run, chain_services))
    work = [s for s in steps if s in ("b", "c")]
    if work and args.dry_run:
        results += dry_run(reader, tenant_id, site_id, work)
    elif work:
        if store is None:
            from assetops_backend.chain.composition import build_thread_store
            store = build_thread_store(url)
        results += run_threads(reader, store, tenant_id, site_id, work)
    if "d" in steps:
        results.append({"step": "d", "skipped": "CH-3 registers the lifecycle step"})
    if "e" in steps:
        results.append({"step": "e", "skipped": "replaced by coherence rule COH-11 (ruling R1)"})
    for result in results:
        print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
