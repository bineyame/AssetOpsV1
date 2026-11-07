"""DD-1b2b step 7 (DD1b2-R8 A): the reads after the prepare. Reads only; none of it is a `CHECKS` row.

    python <tree>/tools/demo_combined_after.py <db url> <work>          (tree form, R9 section 3)

O8 (H1 measurements: renewable selections, studies, mill thread, boards, Portfolio counts), O14 (unused solar), O15
(generator energy per steady-before night; litres are NOT stored on this Site, see `litre_note`). Writes
`<work>/after.json` and prints it. Never ticks and never writes to the database."""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

KOBO = "KOBO-001"
PRE, POST = (-13, -12, -11), (-8, -6, -5)  # O14's days
RENEWABLE_SQL = ("SELECT count(DISTINCT s.window_start) FROM mini_depth_selection s JOIN site st ON "
                 "st.tenant_id = s.tenant_id AND st.id = s.site_id WHERE st.site_code = %s AND s.domain = 'renewable' "
                 "AND s.window_start >= %s AND s.window_start < %s")
STUDY_SQL = ("SELECT o.id, o.first_day, o.last_day, CAST(r.result->>'eligible_days' AS int), r.result->>'status', "
             "o.public_no FROM mini_opportunity o JOIN site s ON s.tenant_id = o.tenant_id AND s.id = o.site_id "
             "JOIN LATERAL (SELECT result FROM mini_opportunity_revision x WHERE x.tenant_id = o.tenant_id AND "
             "x.site_id = o.site_id AND x.opportunity_id = o.id ORDER BY x.revision_no DESC LIMIT 1) r ON true "
             "WHERE s.site_code = %s ORDER BY o.last_day")
SERIES_SQL = ("SELECT x.device_id, x.signal_id, x.source_time, x.normalized_value_text FROM accepted_evidence x "
              "JOIN site s ON s.id = x.site_id WHERE s.site_code = %s AND x.source_time >= %s AND x.source_time < %s")


def connect(url: str):
    import psycopg

    return psycopg.connect(url.replace("+psycopg", ""))


def local_day(ts: datetime) -> date:
    return (ts.astimezone(timezone.utc) + timedelta(hours=3)).date()  # Kobo is Africa/Nairobi, no DST


def kwh_per_local_day(rows: list[tuple], pick) -> dict[str, Decimal]:
    """Sum 5-minute kW readings x 5/60 per Site-local day for the (device, signal) pairs `pick` accepts. Readings are
    deduplicated on (device, signal, source_time); a non-numeric value is skipped (dd1a2_mill3_dry_run.py:49-52)."""
    seen: set = set()
    out: dict[str, Decimal] = {}
    for device, signal, ts, value in rows:
        if not pick(device, signal) or (device, signal, ts) in seen:
            continue
        try:
            kw = Decimal(str(value))
        except Exception:  # noqa: BLE001
            continue
        seen.add((device, signal, ts))
        key = local_day(ts).isoformat()
        out[key] = out.get(key, Decimal(0)) + kw * Decimal(5) / Decimal(60)
    return out


def unused_solar(available: dict[str, Decimal], delivered: dict[str, Decimal], mill: dict[str, Decimal],
                 days: list[str]) -> dict:
    """O14: unused = available - delivered; the group means over `days`."""
    per = {d: {"available": float(available.get(d, 0)), "delivered": float(delivered.get(d, 0)),
               "unused": float(available.get(d, 0) - delivered.get(d, 0)), "mill": float(mill.get(d, 0))} for d in days}
    mean = {k: round(sum(v[k] for v in per.values()) / max(len(per), 1), 1) for k in ("available", "delivered", "unused", "mill")}
    return {"days": per, "mean": mean}


def quotable(pre_unused: float, post_unused: float) -> bool:
    """O14: "about 96 / about 22" may be quoted only if unused reads 96.4 and 22.4 (+-0.5)."""
    return abs(pre_unused - 96.4) <= 0.5 and abs(post_unused - 22.4) <= 0.5


def main(url: str, work: Path) -> int:
    import demo_combined_finish as fin  # needs the backend on the path; imported here so the pure parts test alone

    ctx = fin.load(work, fin.app_client(url, work))
    ctx.url = url
    S = ctx.S
    day = lambda n: (S + timedelta(days=n)).date().isoformat()  # noqa: E731
    doc: dict = {"S": S.isoformat()}
    with connect(url) as c:
        # ---- O8 (1): renewable selections per day; (2): every stored study
        doc["o8_renewable_selections"] = {f"S{n:+d} {day(n)}": c.execute(
            RENEWABLE_SQL, (KOBO, S + timedelta(days=n), S + timedelta(days=n + 1))).fetchone()[0] for n in (-3, -1, 0, 1)}
        studies = c.execute(STUDY_SQL, (KOBO,)).fetchall()
        doc["o8_studies"] = [{"public_no": s[5], "first_day": str(s[1]), "last_day": str(s[2]), "eligible_days": s[3],
                              "status": s[4]} for s in studies]
        # ---- O14 / O15 from accepted_evidence
        lo, hi = S + timedelta(days=-20), S + timedelta(days=-3)
        rows = c.execute(SERIES_SQL, (KOBO, lo, hi)).fetchall()
        pairs = sorted({(r[0], r[1]) for r in rows})
        doc["evidence_pairs"] = [list(p) for p in pairs]
        avail = kwh_per_local_day(rows, lambda d, s: (d, s) == ("pv-inverter-controller", "available-power"))
        deliv = kwh_per_local_day(rows, lambda d, s: (d, s) == ("pv-inverter-controller", "ac-power"))
        mill = kwh_per_local_day(rows, lambda d, s: "mill" in d and s in ("ac-power", "active-power", "power"))
        pre = unused_solar(avail, deliv, mill, [day(n) for n in PRE])
        post = unused_solar(avail, deliv, mill, [day(n) for n in POST])
        doc["o14"] = {"pre": pre, "post": post, "quote_96_22": quotable(pre["mean"]["unused"], post["mean"]["unused"])}
        gen = kwh_per_local_day(rows, lambda d, s: d == "generator-controller" and s == "ac-power")
        steady = [d["day"] for d in ctx.site_days("kobo") if d["kind"] in ("steady-before", "steady-before-first")]
        doc["o15"] = {"generator_kwh_by_local_day": {d: round(float(gen.get(d, 0)), 3) for d in steady},
                      "litre_note": "no fuel signal reaches evidence on this Site (0 fuel_level rows): litres are not "
                                    "stored and are NOT recomputed here; the stored measure is generator kWh"}
    # ---- O8 (3): the mill thread's events; (4): boards; (5): Portfolio counts; (6) is F-COH's allowed_coh17
    thread = fin._mill_thread(ctx)
    doc["o8_mill_thread_events"] = [(e.get("state"), e.get("effective_day") or e.get("day")) for e in
                                    (thread or {}).get("events", [])]
    boards = {}
    for n in (-5, -1, 0, 1):
        body = ctx.board(KOBO, S + timedelta(days=n), S + timedelta(days=n + 1))
        by = fin.rows(body)
        boards[f"S{n:+d}"] = {k: {"state": by[k]["state"], "headline": by[k].get("headline")}
                              for k in ("GROW_REVENUE", "ASSURE_PERFORMANCE") if k in by}
    doc["o8_boards"] = boards
    pf = {}
    for name, a, b in (("week", -6, 1), ("month", -29, 1)):
        body, *_ = fin._estate(ctx, S + timedelta(days=a), S + timedelta(days=b))
        pf[name] = body.get("summary")
    doc["o8_portfolio"] = pf
    (work / "after.json").write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")
    print(json.dumps(doc, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], Path(sys.argv[2])))
