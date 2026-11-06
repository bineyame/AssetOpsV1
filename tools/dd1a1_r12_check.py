"""DD-1a1 R12 L2 check on two *_test DBs built by tools/dd1a1_fullday_probe.py (`without` / `with` full days).

    python tools/dd1a1_r12_check.py <db-without> <db-with>

Reports, per DB: generator starts per local day (UTC+3) and per complement window (night 21-03Z, afternoon/dusk 11-17Z
..., reported by UTC hour of the start), and the 14:00 (11:00Z) and 18:00-local (15:00Z) seams: the state-of-charge step across the seam
against the largest other step within 2 h either side (only a day that runs that complement has a real seam there). Fails (exit 1) if any generator start falls in the dusk
window 15:00Z-17:00Z of a local day. Findings/threads/money equality is `tools/dd1a1_fullday_compare.py`."""

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


def main(a: str, b: str) -> int:
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
    print("RESULT", "FAIL (a dusk start remains)" if bad else "PASS (no dusk generator start)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
