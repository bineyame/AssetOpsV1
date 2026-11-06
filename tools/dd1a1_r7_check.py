"""DD1a1-R7/R7b L2 checks on a finished `with` Kobo build (own *_test DB, read only).

    python tools/dd1a1_r7_check.py <db-name> [cut-night-start-utc=2026-11-04T21:00:00Z]

The cut night is [21:00Z, 03:00Z) around the reserve change at 00:00Z (the trial-after night). The unsplit reference
is the same hours of the previous day's night (no revision boundary inside it). Prints one line per check and
exits 1 on the first failure."""

from __future__ import annotations

import sys
from collections import defaultdict
from datetime import datetime, timedelta

import psycopg

SOC, GEN = ("battery-pcs-controller", "state-of-charge"), ("generator-controller", "status")


def main(db: str, night: str) -> int:
    lo = datetime.fromisoformat(night.replace("Z", "+00:00"))
    cut, hi = lo + timedelta(hours=3), lo + timedelta(hours=6)
    ref_lo = lo - timedelta(days=1)
    c = psycopg.connect(f"postgresql://assetops:assetops-local-dev@127.0.0.1:55432/{db}")
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(("PASS " if ok else "FAIL ") + name + (f" ({detail})" if detail else ""))
        if not ok:
            fails.append(name)

    rev = {r[0]: (r[1], r[2], r[3]) for r in c.execute("select id, version, valid_from, valid_to from foundation_revision")}
    rows = c.execute("select device_id, signal_id, source_time, foundation_revision_id, sequence_epoch, sequence, source_id, "
                     "normalized_value_text from accepted_evidence where source_time >= %s and source_time < %s",
                     (lo, hi)).fetchall()
    ref = c.execute("select device_id, signal_id, source_time from accepted_evidence where source_time >= %s and "
                    "source_time < %s", (ref_lo, ref_lo + timedelta(hours=6))).fetchall()
    check("night has rows (non-vacuous)", len(rows) > 0 and len(ref) > 0, f"{len(rows)} rows, reference {len(ref)}")

    # 1. A on v16, B on v17: no reading at/after 00:00Z cites v16 and none before cites v17.
    versions = defaultdict(set)
    for _, _, t, rid, *_ in rows:
        versions["A" if t < cut else "B"].add(rev[rid][0])
    check("A cites only the revision valid before 00:00Z, B only the one after",
          len(versions["A"]) == 1 and len(versions["B"]) == 1 and versions["A"] != versions["B"], str(dict(versions)))
    bad = [t for _, _, t, rid, *_ in rows if not (rev[rid][1] <= t and (rev[rid][2] is None or t < rev[rid][2]))]
    check("every reading cites the revision valid at its own source time", not bad, f"{len(bad)} outside")
    check("a revision boundary at the cut", any(v[2] == cut for v in rev.values()))

    # 2. Per signal, A's times plus B's equal the unsplit grid: none missing, none extra, no off-grid end stamp.
    got, want = defaultdict(list), defaultdict(list)
    for dev, sig, t, *_ in rows:
        got[(dev, sig)].append(t - lo)
    for dev, sig, t in ref:
        want[(dev, sig)].append(t - ref_lo)
    check("same signals", set(got) == set(want), f"{len(got)} vs {len(want)}")
    diff = [k for k in want if sorted(got[k]) != sorted(want[k])]
    check("per signal the split night's source times equal the unsplit grid", not diff,
          f"{len(want)} signals; differing {diff[:3]}")
    off = [(k, t) for k, v in got.items() for t in v if (t.total_seconds() // 60) % 5]
    check("no off-grid stamp", not off)

    # 3. one epoch, sequence 1..N over the whole stream.
    ep = defaultdict(set)
    for dev, sig, t, _, e, seq, src, _ in rows:
        ep[(src, dev, sig)].add(e)
    check("one epoch per stream across the cut", all(len(v) == 1 for v in ep.values()), f"{len(ep)} streams")
    allseq = defaultdict(list)
    for src, dev, sig, e, seq in c.execute("select source_id, device_id, signal_id, sequence_epoch, sequence from accepted_evidence"):
        allseq[(src, dev, sig, e)].append(seq)
    gaps = [k for k, v in allseq.items() if sorted(v) != list(range(1, len(v) + 1))]
    check("sequence 1..N in every stream and epoch", not gaps, f"{len(allseq)} streams; gaps {gaps[:2]}")

    # 4. no jump at the cut: SoC step across the seam is no larger than the night's other steps; generator unchanged.
    series = {k: sorted((t, float(v)) for d, s, t, *_rest, v in rows if (d, s) == k) for k in [SOC]}[SOC]
    steps = [abs(b[1] - a[1]) for a, b in zip(series, series[1:])]
    seam = next(abs(b[1] - a[1]) for a, b in zip(series, series[1:]) if a[0] < cut <= b[0])
    check("no SoC jump at 00:00Z", seam <= max(steps) and seam <= sorted(steps)[len(steps) // 2] * 3 + 0.05,
          f"seam {seam:.4f}, max step {max(steps):.4f}, median {sorted(steps)[len(steps)//2]:.4f}")
    gen = sorted((t, v) for d, s, t, *_r, v in rows if (d, s) == GEN)
    before = [v for t, v in gen if t < cut][-1]
    after = [v for t, v in gen if t >= cut][0]
    check("generator state unchanged across the seam", before == after, f"{before} -> {after}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "2026-11-04T21:00:00Z"))
