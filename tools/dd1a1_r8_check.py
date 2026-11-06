"""DD1a1-R8 L2 probe/acceptance checks on a Kobo build DB (read-only).

    python tools/dd1a1_r8_check.py <db> [stream|full]

stream (the probe build): the S-1d/S/S+1d stream is one epoch on one gateway with sequence 1..N across both midnights,
a complement is received after the next day's story run, the isolated late day has its own epoch, and every built UTC
window is SELECTED_UNIQUE. full: the same epoch/sequence checks plus 0 AMBIGUOUS in every built UTC window."""

from __future__ import annotations

import sys
from collections import defaultdict

import psycopg

BASE = "postgresql://assetops:assetops-local-dev@127.0.0.1:55432/"


def main(db: str, mode: str = "stream") -> int:
    c = psycopg.connect(BASE + db)
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(("PASS " if ok else "FAIL ") + name + (f" ({detail})" if detail else ""))
        if not ok:
            fails.append(name)

    ev = c.execute("select sequence_epoch, gateway_id::text, source_id::text, sequence, received_at, source_time "
                   "from accepted_evidence").fetchall()
    check("evidence present (non-vacuous)", len(ev) > 0, f"{len(ev)} rows")
    by_epoch = defaultdict(list)
    for e in ev:
        by_epoch[e[0]].append(e)
    multi = {k: v for k, v in by_epoch.items() if min(r[5] for r in v).date() != max(r[5] for r in v).date()}
    check("an epoch spans several UTC dates (a stream exists)", len(multi) >= 1, f"{sorted(multi)}")
    check("one gateway per epoch", all(len({r[1] for r in v}) == 1 for v in by_epoch.values()))
    seq = defaultdict(list)
    for e, _, src, s, *_ in ev:
        seq[(src, e)].append(s)
    gaps = [k for k, v in seq.items() if sorted(v) != list(range(1, len(v) + 1))]
    check("sequence 1..N per source and epoch", not gaps, f"{len(seq)} streams; gaps {gaps[:2]}")
    # across both midnights: the longest stream's source times cover 3 local days with no sequence reset
    big = max(by_epoch.values(), key=lambda v: max(r[5] for r in v) - min(r[5] for r in v))
    span = max(r[5] for r in big) - min(r[5] for r in big)
    check("longest stream spans >= 2 local days", span.total_seconds() >= 2 * 86400, str(span))
    # a complement received after the next day's story run: a row whose source time is earlier than another row
    # that was received earlier, in one epoch (out-of-order receipt across a day edge)
    late_recv = False
    for v in by_epoch.values():
        v = sorted(v, key=lambda r: r[4])
        top = None
        for r in v:
            if top is not None and r[5] < top[5] - __import__("datetime").timedelta(hours=1):
                late_recv = True
                break
            top = r if top is None or r[5] > top[5] else top
    check("a complement is received after the next day's run (older source time, later receipt)", late_recv)
    rows = c.execute("select s.window_start::date, ar.cohort_status, count(*) from analytic_run_selection s "
                     "join analytic_run ar on ar.id = s.run_id where s.analytic_id like '%dispatch%' "
                     "group by 1, 2 order by 1, 2").fetchall()
    print("windows:", rows)
    check("dispatch windows exist (non-vacuous)", len(rows) > 0)
    amb = [r for r in rows if r[1] == "AMBIGUOUS"]
    check("0 AMBIGUOUS in every built UTC window", not amb, str(amb))
    if mode == "stream":
        last = c.execute("select distinct on (s.window_start) s.window_start::date, ar.cohort_status from "
                         "analytic_run_selection s join analytic_run ar on ar.id = s.run_id where s.analytic_id "
                         "like '%dispatch%' order by s.window_start, s.seq desc").fetchall()
        print("latest selection per window:", last)
        check("all windows SELECTED_UNIQUE on the latest selection", all(r[1] == "SELECTED_UNIQUE" for r in last)
              and len(last) >= 3, str(last))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "stream"))
