"""DD-1a1 R12 L2 check on two *_test DBs built by tools/dd1a1_fullday_probe.py (`without` / `with` full days).

    python tools/dd1a1_r12_check.py <db-without> <db-with> [<days.json of the build>]

Reports, per DB: generator starts per local day (UTC+3) and per complement window (night 21-03Z, afternoon/dusk 11-17Z
..., reported by UTC hour of the start), and the 14:00 (11:00Z) and 18:00-local (15:00Z) seams: the state-of-charge step across the seam
against the largest other step within 2 h either side (only a day that runs that complement has a real seam there). Fails (exit 1) if any generator start falls in the dusk
window 15:00Z-17:00Z of a local day. DD1a1-R13 standing checks (fail, exit 1): every complement seam's SoC step <= 0.5 pp (with an equal generator state across
it); a pure steady day (a `steady` local day with no story run, from days.json) has 0 starts 06:00-20:00 local (03Z-17Z);
MG-2 candidate-avoidable counts per window equal with and without. Findings/threads/money equality is `tools/dd1a1_fullday_compare.py`."""

from __future__ import annotations

import collections
import datetime as dt
import sys

import psycopg

BASE = "postgresql://assetops:assetops-local-dev@127.0.0.1:55432/"
UTC3 = dt.timezone(dt.timedelta(hours=3))


def starts(c):
    rows = c.execute("select source_time, normalized_value_text from accepted_evidence "
                     "where device_id='generator-controller' and signal_id='status' order by source_time").fetchall()
    return [t for (t0, v0), (t, v) in zip(rows, rows[1:]) if v0 != "RUNNING" and v == "RUNNING"]


def seams(c, hour):
    rows = c.execute("select source_time, normalized_value_text from accepted_evidence "
                     "where device_id='battery-pcs-controller' and signal_id='state-of-charge' order by source_time").fetchall()
    soc = {t.astimezone(dt.timezone.utc): float(v) for t, v in rows}
    out = []
    for day in sorted({t.date() for t in soc}):
        seam = dt.datetime(day.year, day.month, day.day, hour, 0, tzinfo=dt.timezone.utc)
        prev = max((t for t in soc if t < seam and t.date() == day), default=None)
        if prev is None or seam not in soc:
            continue
        window = sorted(t for t in soc if seam - dt.timedelta(hours=2) <= t <= seam + dt.timedelta(hours=2))
        steps = [abs(soc[b] - soc[a]) for a, b in zip(window, window[1:]) if (a, b) != (prev, seam)]
        out.append((day, round(soc[seam] - soc[prev], 3), round(max(steps), 3) if steps else None, (seam - prev)))
    return out


SEAM_MAX_PP = 0.5
#: DD1a1-R16: the seams that exist on a full day. The 06:00 story start is exempt (the story run starts from its declared state);
#: the joins are the story run's end (mill: 18:00 local = 15:00Z) and the day's last reading (24:00 local = 21:00Z minus one step).
FULL_DAY_SEAM_Z = (15,)


def full_days(days_json):
    """Local dates (UTC+3) of the Kobo days that carry complement runs in this build's days.json."""
    import json
    days = json.load(open(days_json, encoding="utf-8"))["days"]
    return sorted({d["day"] for d in days if d["site"] == "kobo" and d.get("complement_of")})


def seam_check(c, label, days_json):
    """R16: on each full day, STOPPED on both sides of every join, SoC step <= 0.5 pp (fuel is not a persisted signal on
    this Site; the probe record `full_days` + the handover carry fuel, measured step 0.0 L); STOPPED at the day's last
    reading. Story-only days have no join and are not checked. Fails if the build has no full day."""
    soc = {t: float(v) for t, v in c.execute("select source_time, normalized_value_text from accepted_evidence where "
                                             "device_id='battery-pcs-controller' and signal_id='state-of-charge'")}
    gen = dict(c.execute("select source_time, normalized_value_text from accepted_evidence where "
                         "device_id='generator-controller' and signal_id='status'").fetchall())
    days, seen, worst, bad = full_days(days_json), 0, 0.0, []
    for day in days:
        d0 = dt.datetime.fromisoformat(day).replace(tzinfo=dt.timezone.utc)
        for hour in FULL_DAY_SEAM_Z:
            t = d0 + dt.timedelta(hours=hour)
            prev = t - dt.timedelta(minutes=5)
            if t not in soc or prev not in soc:
                bad.append((day, f"{hour}:00Z", "missing reading"))
                continue
            seen += 1
            step = abs(soc[t] - soc[prev])
            worst = max(worst, step)
            if step > SEAM_MAX_PP or gen.get(prev) != "STOPPED" or gen.get(t) != "STOPPED":
                bad.append((day, f"{hour}:00Z", round(step, 3), gen.get(prev), gen.get(t)))
        last = max((x for x in soc if x.date().isoformat() == day), default=None)
        end = d0 + dt.timedelta(hours=21, minutes=-5)
        if last != end or gen.get(last) != "STOPPED":
            bad.append((day, "day end", str(last), gen.get(last)))
    ok = seen > 0 and not bad
    print(f"{'PASS' if ok else 'FAIL'} full-day joins STOPPED both sides, SoC step <= {SEAM_MAX_PP} pp ({label}): "
          f"{len(days)} full day(s) {days}, {seen} joins, largest {worst:.3f} pp, {len(bad)} bad {bad[:5]}")
    return not ok


def pure_steady_check(c, days_json):
    """R13: a pure steady local day (UTC+3) has 0 generator starts 06:00-20:00 local."""
    import json
    days = json.load(open(days_json, encoding="utf-8"))["days"]
    kobo = [d for d in days if d["site"] == "kobo"]
    story = {d["day"] for d in kobo if not d.get("complement_of") and d["kind"] != "steady"}
    pure = sorted({d["day"] for d in kobo if d["kind"] == "steady" and not d.get("complement_of")} - story)
    if not pure:
        print("INFO pure steady day check: no pure steady day in this calendar (applies from DD-1a2/1b2)")
        return False
    bad = [t for t in starts(c) if t.astimezone(UTC3).date().isoformat() in pure and 6 <= t.astimezone(UTC3).hour < 20]
    print(f"{'FAIL' if bad else 'PASS'} pure steady days {pure}: starts 06:00-20:00 local {len(bad)}")
    return bool(bad)


def mg2_check(ca, cb):
    def cand(c):
        return {k: r["counts"].get("CANDIDATE_AVOIDABLE") for k, r in c.execute(
            "select distinct on (assessment_key) assessment_key, result from assessment_revision "
            "where assessment_key like 'dispatch:window:%' order by assessment_key, revision_no desc")}
    wa, wb = cand(ca), cand(cb)
    ok = bool(wa) and set(wa) <= set(wb) and all(wa[k] == wb[k] for k in wa)
    print(f"{'PASS' if ok else 'FAIL'} MG-2 candidate-avoidable counts per window equal with/without: {len(wa)} windows")
    return not ok


def main(a: str, b: str, days_json: str | None = None) -> int:
    bad = 0
    for label, db in (("without", a), ("with", b)):
        with psycopg.connect(BASE + db) as c:
            st = starts(c)
            per_day = collections.Counter(t.astimezone(UTC3).date().isoformat() for t in st)
            dusk = [t for t in st if 15 <= t.hour < 17]
            bad += bool(dusk)
            print(f"== {label} ({db}): generator starts {len(st)}; by local day {dict(sorted(per_day.items()))}")
            print("   starts (UTC):", [t.strftime("%m-%d %H:%MZ") for t in st])
            print(f"   dusk-window (15:00Z-17:00Z) starts: {len(dusk)}")
            for hour, name in ((11, "afternoon 14:00 local"), (15, "dusk 18:00 local")):
                for day, jump, biggest, gap in seams(c, hour):
                    print(f"   seam {day} {hour}:00Z ({name}): SoC step across seam {jump:+}, largest other step within +-2 h {biggest}")
    with psycopg.connect(BASE + b) as cb, psycopg.connect(BASE + a) as ca:
        bad += seam_check(cb, "with", days_json)
        if days_json:
            bad += pure_steady_check(cb, days_json)
        else:
            print("FAIL days.json is required (the full days are read from it)"); bad += 1
        bad += mg2_check(ca, cb)
    print("RESULT", "FAIL" if bad else "PASS (no dusk start, seams <= 0.5 pp, pure steady days quiet, MG-2 equal)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:4]))
