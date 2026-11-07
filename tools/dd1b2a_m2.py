"""DD1b2-R3 M2: read-only measure of the pinned Kobo study's source class and in-memory figure. Writes nothing to the DB.

    python tools/dd1b2a_m2.py --db assetops_demo3_dd1b2q_test --out .agent/DD-1b2a-m2.json [--last-day 2026-10-21]

Uses the worker's own inputs: `projection.day_heads` and `MiniDepthRead.provenance_blocks`' link-row resolver, then
`projection.frozen_result(heads, "REGISTERED_SIMULATION")` in memory (what a rule that accepts one-basis runs would show).
Development only; never part of a prepare.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

DECLARED_PRICE = Decimal("0.25")  # USD per kWh, `demo_combined_finish.wk6` asserts "Declared price - 0.25 USD per kWh"


def main() -> None:
    from sqlalchemy import create_engine, text

    from assetops_backend.chain import vocabulary as v
    from assetops_backend.evidence import source_provenance as sp
    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.mini_decisions import projection
    from assetops_backend.mini_decisions.store import PostgresMiniDecisionStore
    from assetops_backend.mini_depth.read import MiniDepthRead
    from demo_combined import PG_PORT, PW

    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--last-day", default="2026-10-21")
    args = parser.parse_args()
    url = f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PG_PORT}/{args.db}"
    last = date.fromisoformat(args.last_day)
    store = PostgresMiniDecisionStore.from_url(url)
    reader = MiniDepthRead.from_url(url, build_link_rows_reader())
    engine = create_engine(url)
    out: dict = {"db": args.db, "last_day": args.last_day, "read_only": True}
    try:
        with engine.connect() as c0:
            tenant, site = c0.execute(text("SELECT tenant_id, id FROM site WHERE site_code = 'KOBO-001'")).one()
        with store.snapshot() as c:
            tz = store.site_timezone(c, tenant, site)[0]
            heads = projection.day_heads(store, c, tenant, site, tz, projection.study_days(last))
            present = [h for h in heads if h.mini_revision_id is not None]
            ids = sorted({str(i).lower() for h in present for i in h.evidence_ids})
            rows = list(reader._link_rows(c, tenant, site, ids))  # noqa: SLF001 - the worker's own resolver input
            links = {l.accepted_evidence_id: l for l in (sp.link_of(r) for r in rows)}
            result = sp.classify(ids, links)
            blocks = reader.provenance_blocks(
                c, tenant_id=tenant, site_id=site, selected_revision_ids=[h.mini_revision_id for h in present],
                selected_evidence_ids=[i for h in present for i in h.evidence_ids], pending_evidence_ids=None)
            worker_class = (blocks.get("selected_source_provenance") or {}).get("classification")
            hours_per_day: dict = {}
            for h in heads:
                hours_per_day[h.local_day.isoformat()] = hours_per_day.get(h.local_day.isoformat(), 0) + 1
        out["heads"] = {"days": sorted(hours_per_day), "hours_per_day": hours_per_day, "present": len(present),
                        "missing": len(heads) - len(present), "evidence_ids": len(ids)}
        out["resolver"] = {
            "state": result["state"], "worker_classification": worker_class,
            "reason_codes": [r["code"] for r in result["reasons"]],
            "reasons": [{k: val for k, val in r.items() if k != "accepted_evidence_ids"}
                        | {"accepted_evidence_id_count": len(r["accepted_evidence_ids"])} for r in result["reasons"]]}
        by_run: dict = {}
        for l in links.values():
            by_run.setdefault(l.run_id, {"identity": set(), "batches": set(), "n": 0})
            by_run[l.run_id]["identity"].add(l.run_identity_sha256)
            by_run[l.run_id]["batches"].add(l.batch_id)
            by_run[l.run_id]["n"] += 1
        runs = []
        with engine.connect() as c:
            for run_id, info in sorted(by_run.items(), key=lambda kv: str(kv[0])):
                batch_rows = c.execute(text(
                    "SELECT DISTINCT b.snapshot_sha256, b.foundation_revision_id::text, b.binding_set_revision_id::text "
                    "FROM ingestion_batch b WHERE b.id = ANY(CAST(:b AS uuid[]))"), {"b": sorted(info["batches"])}).all()
                runs.append({"run_id": run_id, "evidence_count": info["n"], "batches": len(info["batches"]),
                             "run_identity_sha256": sorted(info["identity"]),
                             "snapshot_sha256": sorted({r[0] for r in batch_rows}),
                             "foundation_revision_ids": sorted({r[1] for r in batch_rows}),
                             "binding_set_revision_ids": sorted({r[2] for r in batch_rows})})
            all_f = sorted({f for r in runs for f in r["foundation_revision_ids"]})
            all_b = sorted({f for r in runs for f in r["binding_set_revision_ids"]})
            out["foundation_revision_rows"] = [dict(r) for r in c.execute(text(
                "SELECT to_jsonb(x) AS row FROM foundation_revision x WHERE x.id = ANY(CAST(:i AS uuid[]))"),
                {"i": all_f}).mappings().all()]
            out["binding_set_revision_rows"] = [dict(r) for r in c.execute(text(
                "SELECT to_jsonb(x) AS row FROM signal_binding_set_revision x WHERE x.id = ANY(CAST(:i AS uuid[]))"),
                {"i": all_b}).mappings().all()]
        out["runs"] = runs
        out["runs_count"] = len(runs)
        out["fields_equal_across_runs"] = {k: len({json.dumps(r[k]) for r in runs}) == 1 for k in (
            "run_identity_sha256", "snapshot_sha256", "foundation_revision_ids", "binding_set_revision_ids")}
        frozen = projection.frozen_result(heads, "REGISTERED_SIMULATION")
        figure = {k: frozen[k] for k in ("status", "assessed_days", "eligible_days", "headroom_kw", "window_hours")}
        figure["limitation_codes"] = [x["code"] for x in frozen["limitations"]]
        figure["value_line"] = v.value_line(frozen["status"], frozen["headroom_kw"], frozen["window_hours"])
        if frozen["headroom_kw"] and frozen["window_hours"]:
            lo, hi = Decimal(frozen["headroom_kw"]["low"]), Decimal(frozen["headroom_kw"]["high"])
            hrs = Decimal(frozen["window_hours"])
            figure["money_line"] = {"declared_price_usd_per_kwh": str(DECLARED_PRICE), "kwh_low": str(lo * hrs),
                                    "kwh_high": str(hi * hrs), "usd_per_day_low": str(lo * hrs * DECLARED_PRICE),
                                    "usd_per_day_high": str(hi * hrs * DECLARED_PRICE),
                                    "basis": "headroom kW x window hours x declared price (arithmetic, not a served line)"}
        else:
            figure["money_line"] = None
        out["figure_if_registered_simulation"] = figure
    finally:
        store.dispose()
        engine.dispose()
    Path(args.out).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(json.dumps({k: out.get(k) for k in ("resolver", "runs_count", "fields_equal_across_runs",
                                              "figure_if_registered_simulation")}, indent=1, default=str)[:3500])


if __name__ == "__main__":
    main()
