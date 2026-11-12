"""SR-10/SR-11 real-data parity (D-SR.36/45/51-54/58/60) on the polish VPS DB. Reads only; writes the --record JSONs.

    PYTHONPATH=<sr11>/backend:<sr11>/backend/tests:<sr11>/contracts:<sr11>/simulator:<sr11>/gateway:<sr11>/field:<sr11>/host:<sr11>/tools \
    python sr10_sr11_parity.py --url <db url> --work <work dir with keys.json> --s 2026-11-10 \
        --record-fuel SR-10-parity.json --record-backup SR-11-parity.json

Per Site (KOBO-001, KISIWA-001) x window (7/14/31 days ending S) x domain (fuel, backup):
  missing_rows        D-SR.69: a stored row absent on a non-NO_DATA day (gate 0); NO_DATA days are listed in no_data_days,
                      expect 0 heads and must not read STILL_PROCESSING
  head_gaps           D-SR.69: stored hours with a live/FAILED job (job_state not SETTLED/NONE) or with accepted evidence
                      in the hour (any family, coarse) but no head (gate 0); partial days are expected
  hours_mismatch      stored day-row hours vs live `build_period(..., whole_day=True)` hours (gate 0)
  state_mismatch      route days[].state vs day_state() recomputed from live hours and a fresh ChainReader day grade (gate 0)
  duplicate_chain_ids backup only: chain_ids in more than one stored hour of a row or across days (gate 0)
  response_seconds    cold and warm GET (gate: cold <= 2.0 s)
  rows_on_off_equal   body with ASSETOPS_PERIOD_READ_KINDS empty == with both day kinds on (gate true)
"""
from __future__ import annotations

import argparse, json, os, sys, time
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SITES = ("KOBO-001", "KISIWA-001")
WINDOWS = (7, 14, 31)
DOMAINS = {"fuel": ("mini_depth.fuel_day", "fuel-range"), "backup": ("mini_depth.backup_day", "backup-range")}
KINDS_ENV = "ASSETOPS_PERIOD_READ_KINDS"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--s", default="2026-11-10")
    ap.add_argument("--record-fuel", type=Path)
    ap.add_argument("--record-backup", type=Path)
    a = ap.parse_args()
    os.environ["ASSETOPS_RESPONSE_STORE"] = "off"  # every GET computes from stored rows (the 2 s claim), nothing pre-built
    import chain_perf_probe
    c = chain_perf_probe.client(a.url, a.work)
    from assetops_backend.chain import period_backfill as pb
    from assetops_backend.chain.composition import build_chain_reader
    from assetops_backend.mini_depth import day_summary as ds
    from assetops_backend.mini_depth import period_rows as pr
    services = pb._default_services()
    tenant = services.inputs.tenant_id(pb.DEVELOPMENT_TENANT_SLUG)
    chain, dispose = build_chain_reader(a.url)
    S = date.fromisoformat(a.s)
    from sqlalchemy import create_engine, text
    eng = create_engine(a.url)

    def evid(w0, w1):
        with eng.connect() as cx:
            return bool(cx.execute(text("select 1 from accepted_evidence where site_id=:s and source_time>=:a and source_time<:b limit 1"),
                                   {"s": site.site_id, "a": w0, "b": w1}).first())
    report: dict[str, list] = {"fuel": [], "backup": []}
    failures: list[str] = []
    for code in SITES:
        site = services.inputs.site(tenant, code)
        from zoneinfo import ZoneInfo
        for n in WINDOWS:
            lo = datetime.combine(S - timedelta(days=n - 1), datetime.min.time(), tzinfo=timezone.utc)
            hi = datetime.combine(S + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
            path = lambda r: f"/api/sites/{code}/{r}?from={lo:%Y-%m-%dT%H:%M:%SZ}&to={hi:%Y-%m-%dT%H:%M:%SZ}"
            for domain, (kind, route) in DOMAINS.items():
                os.environ.pop(KINDS_ENV, None)
                t0 = time.perf_counter(); r1 = c.get(path(route)); cold = time.perf_counter() - t0
                t0 = time.perf_counter(); r2 = c.get(path(route)); warm = time.perf_counter() - t0
                os.environ[KINDS_ENV] = "mini_depth.fuel_day,mini_depth.backup_day"
                r3 = c.get(path(route)); os.environ.pop(KINDS_ENV, None)
                row = {"site": code, "window_days": n, "status": r1.status_code,
                       "response_seconds_cold": round(cold, 3), "response_seconds_warm": round(warm, 3),
                       "rows_on_off_equal": r1.status_code == r3.status_code and r1.content == r3.content}
                if r1.status_code != 200:
                    row["error"] = r1.text[:300]; report[domain].append(row); failures.append(f"{code} {n} {domain}: HTTP {r1.status_code}"); continue
                days = r1.json()["days"]
                day_dates = [date.fromisoformat(d["local_day"]) for d in days]
                row["days"] = len(days)
                # live hours per day through the kind builder's own MiniDepthRead (`build_period`, whole day)
                mini = services.period_builder._builders[kind]._mini
                grades = ds.day_grades(chain.request(tenant, None).day(site.site_id, "MINIGRID", day_dates))
                hm, sm, nodata, gaps, edge = [], [], [], [], []
                stored = {x.local_day: x for x in services.periods.read_latest(tenant, [site.site_id], [kind], day_dates[0], day_dates[-1], None)}
                for d in days:
                    ld = date.fromisoformat(d["local_day"])
                    built = mini.build_period(tenant_id=tenant, site_id=site.site_id, domain=domain, local_day=ld, whole_day=True)
                    live_hours = [] if built is None else built[2]
                    nd = grades.get(ld) == "NO_DATA"
                    if nd:
                        nodata.append({"day": d["local_day"], "state": d["state"], "stored": d.get("stored"),
                                       "heads": sum(1 for h in live_hours if h.get("head")),
                                       "ok": d["state"] != "STILL_PROCESSING"})
                    for h in live_hours:
                        if h.get("head") is None and not nd and h.get("job_state") in ("SETTLED", "NONE") and evid(h["window_start"], h["window_end"]):
                            edge.append({"day": d["local_day"], "hour": h["window_start"]})
                        if h.get("job_state") not in ("SETTLED", "NONE"):
                            gaps.append({"day": d["local_day"], "hour": h["window_start"], "job_state": h.get("job_state"), "head": h.get("head") is not None})
                    if ld in stored and json.dumps(stored[ld].body.get("hours"), sort_keys=True, default=str) != json.dumps(live_hours, sort_keys=True, default=str):
                        hm.append(d["local_day"])
                    if ld in stored:
                        summ = (ds.fuel_day_summary if domain == "fuel" else ds.backup_day_summary)(ld, [pr.hour_from_json(h, historical=False, pending=False) for h in live_hours])
                    else:
                        summ = None
                    want, _ = ds.day_state(domain, summ, grades.get(ld))
                    if want != d["state"]:
                        sm.append({"day": d["local_day"], "route": d["state"], "recomputed": want})
                row["missing_rows"] = [d["local_day"] for d in days if d.get("stored") is False and grades.get(date.fromisoformat(d["local_day"])) != "NO_DATA"]
                row["no_data_days"] = nodata
                row["head_gaps"] = gaps  # live/FAILED jobs: gate 0
                row["hours_with_evidence_no_head"] = edge  # reported, not gated: D-SR.69 "the partial days are expected"
                row["hours_mismatch_days"] = hm
                row["state_mismatch"] = sm
                if domain == "backup":
                    seen, dup = Counter(), set()
                    for d in days:
                        ids = {s["chain_id"] for s in (d.get("sequences") or ())}
                        for i in ids: seen[i] += 1
                    row["duplicate_chain_ids"] = sorted(i for i, k in seen.items() if k > 1)
                    # within one stored row: the same chain_id in more than one stored hour
                    for x in stored.values():
                        per = Counter()
                        for h in x.body.get("hours") or ():
                            res = (h.get("head") or {}).get("result") or {}
                            for s in (res.get("sequences") or ()):
                                per[s.get("chain_id")] += 1
                        row.setdefault("duplicate_chain_ids_in_row", []).extend(k for k, v in per.items() if v > 1 and k)
                bad = (row["missing_rows"] or gaps or any(not x["ok"] for x in nodata) or hm or sm or row.get("duplicate_chain_ids") or row.get("duplicate_chain_ids_in_row")
                       or cold > 2.0 or not row["rows_on_off_equal"])
                row["pass"] = not bad
                if bad: failures.append(f"{code} {n} {domain}")
                report[domain].append(row)
    dispose()
    for domain, rec in ((("fuel", a.record_fuel)), ("backup", a.record_backup)):
        if rec:
            rec.write_text(json.dumps({"S": a.s, "domain": domain, "pass": not [f for f in failures if f.endswith(domain) or "HTTP" in f],
                                       "rows": report[domain]}, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
