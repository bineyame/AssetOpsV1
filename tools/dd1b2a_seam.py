"""DD1b2-R2 M0 / M1 measures, read-only on a kept `*_test` database (development only; never part of a prepare).

    python tools/dd1b2a_seam.py --db <db> --days 2026-10-16,2026-10-17 [--out <json>]

For each Site-local day (given as the local date) it reports, at the three day-edge instants the seam rule is about
(the day's 03:00Z, the next 21:00Z-style seam and 15:00Z, i.e. local 06:00, 00:00 and 18:00 as the Site's timezone has
them), every channel's quality, `unavailable_reason`, `interval_start` and the delivering batch's `received_at` (one
batch per run), plus the dispositions that are not ACCEPTED. It also reports `Demo.delivered_days`.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

PW = os.environ.get("ASSETOPS_PG_PASSWORD", "assetops-local-dev")
PORT = os.environ.get("ASSETOPS_PG_PORT", "55432")
SITE = "KOBO-001"


def measure(db: str, days: list[str]) -> dict:
    import psycopg

    out: dict = {"db": db, "seams": {}, "dispositions": {}, "delivered_days": None}
    with psycopg.connect(f"postgresql://assetops:{PW}@127.0.0.1:{PORT}/{db}", autocommit=True) as c:
        tz = c.execute("SELECT timezone FROM site WHERE site_code = %s", (SITE,)).fetchone()[0]
        out["timezone"] = tz
        for day in days:
            d0 = c.execute("SELECT (%s::date::timestamp) AT TIME ZONE %s", (day, tz)).fetchone()[0]
            for label, instant in (("start 00:00 local", d0), ("06:00 local", d0 + timedelta(hours=6)),
                                   ("18:00 local", d0 + timedelta(hours=18)), ("end 24:00 local", d0 + timedelta(hours=24))):
                rows = c.execute(
                    "SELECT e.device_id, e.signal_id, e.quality, e.unavailable_reason, e.interval_start, b.received_at "
                    "FROM accepted_evidence e JOIN site s ON s.id = e.site_id "
                    "JOIN ingestion_batch b ON b.id = e.batch_id AND b.site_id = e.site_id "
                    "WHERE s.site_code = %s AND e.source_time = %s ORDER BY e.device_id, e.signal_id", (SITE, instant)).fetchall()
                out["seams"][f"{day} {label}"] = {
                    "instant": instant.astimezone(timezone.utc).isoformat(),
                    "rows": [{"channel": f"{r[0]}/{r[1]}", "quality": r[2], "unavailable_reason": r[3],
                              "interval_start": None if r[4] is None else r[4].astimezone(timezone.utc).isoformat(),
                              "batch_received_at": r[5].astimezone(timezone.utc).isoformat()} for r in rows]}
        for decision, n in c.execute("SELECT decision, count(*) FROM ingestion_disposition GROUP BY 1").fetchall():
            out["dispositions"][decision] = n
        rows = c.execute(
            "SELECT DISTINCT to_char(COALESCE(e.interval_start, e.source_time) AT TIME ZONE s.timezone, 'YYYY-MM-DD') "
            "FROM accepted_evidence e JOIN ingestion_disposition d ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal "
            "JOIN site s ON s.id = e.site_id WHERE s.site_code = %s ORDER BY 1", (SITE,)).fetchall()
        out["delivered_days"] = [r[0] for r in rows]
    return out


def stored(db: str, work: Path, days: list[str]) -> dict:
    """M1 / P8: `daylight_hours` per day (knowledge cutoff the database clock), and the dry run's own per-day report
    (generator kWh, Findings, windows), as stored."""
    from datetime import date

    from sqlalchemy import create_engine, text

    import dd1a2_mill3_dry_run as dry
    from assetops_backend.mini_depth.store import daylight_hours, database_now

    engine = create_engine(f"postgresql+psycopg://assetops:{PW}@127.0.0.1:{PORT}/{db}")
    rows = json.loads((work / "days.json").read_text(encoding="utf-8"))["days"]
    out: dict = {"daylight": {}}
    with engine.connect() as c:
        tenant, site = c.execute(text("SELECT tenant_id, id FROM site WHERE site_code = :c"), {"c": SITE}).one()
        now = database_now(c)
        for day in days:
            d = daylight_hours(c, tenant, site, date.fromisoformat(day), now)
            out["daylight"][day] = {"hours": list(d.hours), "missing": list(d.missing), "measured": d.measured}
    rep = dry.report(engine, site, [r for r in rows if r["site"] == "kobo"])
    out["days"] = {k: v for k, v in rep["days"].items() if k in days}
    out["money_rows"] = rep["money_rows"]
    engine.dispose()
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--days", required=True, help="Site-local dates, comma separated")
    parser.add_argument("--out")
    parser.add_argument("--work", help="the work folder: adds daylight hours, generator kWh and Findings per day")
    args = parser.parse_args()
    result = measure(args.db, args.days.split(","))
    if args.work:
        result["stored"] = stored(args.db, Path(args.work), args.days.split(","))
    text = json.dumps(result, indent=2, default=str)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    summary = {k: sorted({(r["quality"], r["unavailable_reason"]) for r in v["rows"]}, key=str)
               for k, v in result["seams"].items()}
    print(json.dumps({"dispositions": result["dispositions"], "delivered_days": result["delivered_days"],
                      "seam_kinds": summary}, indent=1, default=str))


if __name__ == "__main__":
    main()
