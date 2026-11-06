"""DD1a1-R3 Q1 L2 checks on a finished pair of Kobo builds (own *_test DBs, read only).

    python tools/dd1a1_r3_check.py <without-db> <with-db> [<days.json of the build>]

Local time is UTC+3 (story window 06:00-14:00 local = 03:00Z-11:00Z); a steady night is [17:00Z, 03:00Z). Prints one
line per check and exits 1 on any failure; nothing is tuned. Check 2's ACT-K1 outcome/metrics and check 4's Findings,
events and money are the `dd1a1_fullday_compare` tables; this script adds the evidence-level measures."""

from __future__ import annotations

import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

import psycopg

URL = "postgresql://assetops:assetops-local-dev@127.0.0.1:55432/"
UTC = timezone.utc


def story_spans(days_json: str):
    """The closed [start, end] of every Kobo story run (a run with no `complement_of`) in the build's days.json."""
    import json
    days = json.load(open(days_json, encoding="utf-8"))["days"]
    return [(datetime.fromisoformat(d["start"].replace("Z", "+00:00")), datetime.fromisoformat(d["end"].replace("Z", "+00:00")))
            for d in days if d["site"] == "kobo" and not d.get("complement_of") and d.get("start")]


def main(a: str, b: str, days_json: str | None = None) -> int:
    ca, cb = psycopg.connect(URL + a), psycopg.connect(URL + b)
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(("PASS " if ok else "FAIL ") + name + (f" ({detail})" if detail else ""))
        if not ok:
            fails.append(name)

    def story_days(c):
        return sorted({t.date() for (t,) in c.execute("select source_time from accepted_evidence where "
                                                      "extract(hour from source_time at time zone 'UTC') = 3 and "
                                                      "extract(minute from source_time at time zone 'UTC') = 0")})

    days = story_days(cb)
    nights = []
    for d in days:
        lo = datetime(d.year, d.month, d.day, tzinfo=UTC) - timedelta(hours=7)
        hi = datetime(d.year, d.month, d.day, 3, tzinfo=UTC)
        n = cb.execute("select count(*) from accepted_evidence where source_time >= %s and source_time < %s",
                       (lo, hi)).fetchone()[0]
        if n:
            nights.append((d, lo, hi))
    check("nights exist in the with build (non-vacuous)", len(nights) > 0, f"{len(nights)} nights: {[str(n[0]) for n in nights]}")
    if days_json:  # DD1a1-R13: the windows come from the build's own story runs, not an assumed 03Z-11Z
        spans = story_spans(days_json)
        times = [t for (t,) in ca.execute("select source_time from accepted_evidence")]
        stray = [t for t in times if not any(lo <= t <= hi for lo, hi in spans)]
        check("the without build holds no evidence outside the story windows", bool(spans) and bool(times) and not stray,
              f"{len(spans)} story windows, {len(times)} readings, {len(stray)} outside")
    else:
        print("SKIP the without build holds no evidence outside the story windows (pass the build's days.json)")

    # 1. night shape: starts, none before 04:00 local (01:00Z), MG-5 critical supply (clinic delivered == requested)
    for d, lo, hi in nights:
        gen = cb.execute("select source_time, normalized_value_text from accepted_evidence where device_id = "
                         "'generator-controller' and signal_id = 'status' and source_time >= %s and source_time < %s "
                         "order by source_time", (lo, hi)).fetchall()
        starts = [t for (t0, v0), (t, v) in zip(gen, gen[1:]) if v0 != "RUNNING" and v == "RUNNING"]
        req = dict(cb.execute("select source_time, normalized_value_text::float from accepted_evidence where "
                              "device_id = 'clinic-meter' and signal_id = 'requested-power' and quality <> 'UNAVAILABLE' and source_time >= %s "
                              "and source_time < %s", (lo, hi)).fetchall())
        dlv = dict(cb.execute("select source_time, normalized_value_text::float from accepted_evidence where "
                              "device_id = 'clinic-meter' and signal_id = 'delivered-power' and quality <> 'UNAVAILABLE' and source_time >= %s "
                              "and source_time < %s", (lo, hi)).fetchall())
        short = [t for t in req if t in dlv and dlv[t] + 1e-6 < req[t]]
        early = [t for t in starts if t < d_to_utc(d) - timedelta(hours=2)]  # before 04:00 local = 01:00Z
        check(f"1 night {d}: {len(starts)} start(s) {[t.strftime('%H:%MZ') for t in starts]}, none before 04:00 local, "
              f"MG-5 supply complete", len(starts) <= 1 and not early and bool(req) and not short,
              f"{len(req)} clinic readings, {len(short)} short")
        run_min = sum(5 for t, v in gen if v == "RUNNING")
        print(f"INFO night {d}: generator RUNNING readings {run_min // 5} (5 min each); fuel/tank is not a "
              f"persisted signal on this Site (fuel_level role has 0 readings), so '0.0 L' is the step note, not measured")

    # 2. MG-2: the day windows grade identically with and without nights (claim level per window), no Candidate
    def windows(c):
        return {k: (cl, r["counts"]) for k, cl, r in c.execute(
            "select distinct on (assessment_key) assessment_key, claim_level, result from assessment_revision "
            "where assessment_key like 'dispatch:window:%' order by assessment_key, revision_no desc")}
    wa, wb = windows(ca), windows(cb)
    cand = {k: v[1].get("CANDIDATE_AVOIDABLE") for k, v in wb.items()}
    cand_a = {k: v[1].get("CANDIDATE_AVOIDABLE") for k, v in wa.items()}
    check("2 MG-2: candidate-avoidable interval counts per window equal with and without nights",
          bool(wa) and set(wa) <= set(wb) and all(cand[k] == cand_a[k] for k in wa),
          f"{[(k[-27:-17], cand_a[k], cand[k]) for k in sorted(wa)]}")
    # 3. each full day (with nights) grades COMPLETE; without nights the same window may be LIMITED (the missing night
    # hours), which is the intended gain, so only the with side is held to COMPLETE
    levels = {k[-27:-17]: wb[k][0] for k in wb}
    gained = [(k[-27:-17], wa[k][0], wb[k][0]) for k in wa if wa[k][0] != wb[k][0]]
    # DD1a1-R16: only the days that carry complement runs are full days; every other story day is story-only (partly checked)
    import json
    fulls = sorted({d["day"] for d in json.load(open(days_json, encoding="utf-8"))["days"]
                    if d["site"] == "kobo" and d.get("complement_of")}) if days_json else []
    full = {k: v for k, v in levels.items() if k in fulls}
    check("3 every full day grades COMPLETE with nights", bool(full) and set(full.values()) == {"COMPLETE"},
          f"full days {fulls} grade {full}; story-only days (not held to COMPLETE): "
          f"{ {k: v for k, v in levels.items() if k not in fulls} }")
    print(f"INFO windows whose grade differs without nights (without -> with): {gained}")
    # 3b. the daylight evidence is the same set of readings (mill, spare solar read only daylight 06:00-14:00 local)
    def day_set(c):
        return Counter(c.execute("select device_id, signal_id, source_time, normalized_value_text from "
                                 "accepted_evidence where extract(hour from source_time at time zone 'UTC') "
                                 "between 3 and 10").fetchall())
    sa, sb = day_set(ca), day_set(cb)
    check("3 the story-window readings are identical with and without nights (mill and spare solar read these)",
          sa == sb and bool(sa), f"{sum(sa.values())} vs {sum(sb.values())} readings; only-with {sum((sb - sa).values())}")
    # 5. the 06:00 seam, reported
    for d, lo, hi in nights:
        def at(t, sig, dev):
            return cb.execute("select normalized_value_text from accepted_evidence where device_id=%s and signal_id=%s "
                              "and source_time=%s", (dev, sig, t)).fetchone()
        before = hi - timedelta(minutes=5)
        print(f"SEAM {d} 06:00 local: SoC {at(before, 'state-of-charge', 'battery-pcs-controller')} -> "
              f"{at(hi, 'state-of-charge', 'battery-pcs-controller')}; generator "
              f"{at(before, 'status', 'generator-controller')} -> {at(hi, 'status', 'generator-controller')}")
    return 1 if fails else 0


def d_to_utc(d) -> datetime:  # the night ends 03:00Z on the story day
    return datetime(d.year, d.month, d.day, 3, tzinfo=UTC)


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:4]))
