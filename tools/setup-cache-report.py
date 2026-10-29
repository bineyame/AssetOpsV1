"""Summarise backend/tests/setup_cache.py logs of one run (PERF-02).

    python tools/setup-cache-report.py <run dir> [--out <file.md>]

Reads <run>/setup-cache/setup-cache-*.jsonl: per op family the number of hits (a restored copy), misses (built and
saved) and live runs (not cacheable, with the reasons), the seconds each took, the measured copy cost (hit
seconds), and in verify mode the copy-against-fresh comparison (row counts and content per table, UUID counter).
"""

from __future__ import annotations

import argparse
import collections
import json
import statistics
from pathlib import Path


def family(op: str) -> str:
    parts = op.split(".")
    module = parts[0].replace("test_", "")
    return f"{module}.{'.'.join(parts[1:])}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    rows = []
    for path in sorted((args.run / "setup-cache").glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            if not record.get("summary"):
                rows.append(record)
    by = collections.defaultdict(lambda: collections.defaultdict(list))
    reasons = collections.Counter()
    verify = collections.defaultdict(lambda: collections.Counter())
    mismatches = collections.defaultdict(collections.Counter)
    for r in rows:
        by[family(r["op"])][r["outcome"]].append(r.get("seconds", 0.0))
        if r["outcome"] == "live" and r.get("reason"):
            reasons[(family(r["op"]), r["reason"][:120])] += 1
        if r["outcome"] == "verify":
            f = family(r["op"])
            if "rows_equal" not in r:
                verify[f]["no saved fingerprint"] += 1
                continue
            verify[f]["compared"] += 1
            verify[f]["rows equal"] += bool(r["rows_equal"])
            verify[f]["uuid equal"] += bool(r.get("uuid_equal"))
            for t in r.get("count_mismatch", []):
                mismatches[f][f"count:{t}"] += 1
            for t in r.get("content_mismatch", []):
                mismatches[f][f"content:{t}"] += 1
            for t in r.get("tmp_path_in_rows", []):
                mismatches[f][f"tmp-path:{t}"] += 1
    hits = [s for f in by.values() for s in f.get("hit", [])]
    out = [f"# Set-up cache, run {args.run.name}", "",
           f"- ops: {len(rows)}; hits {len(hits)}, misses {sum(len(f.get('miss', [])) for f in by.values())}, "
           f"live {sum(len(f.get('live', [])) for f in by.values())}, verify {sum(len(f.get('verify', [])) for f in by.values())}",
           f"- measured copy cost (seconds per hit, restore of database + files + objects): "
           + (f"median {statistics.median(hits):.2f}, mean {statistics.mean(hits):.2f}, "
              f"p90 {sorted(hits)[int(len(hits) * 0.9)]:.2f}, total {sum(hits):.0f}" if hits else "no hits"), "",
           "| op family | hits | hit s | misses | miss s | live | live s | verify |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for f, d in sorted(by.items()):
        out.append(f"| {f} | {len(d.get('hit', []))} | {sum(d.get('hit', [])):.0f} | {len(d.get('miss', []))} | "
                   f"{sum(d.get('miss', [])):.0f} | {len(d.get('live', []))} | {sum(d.get('live', [])):.0f} | "
                   f"{len(d.get('verify', []))} |")
    if reasons:
        out += ["", "Live (not cached) reasons:", ""] + [f"- {n} x {f}: {why}" for (f, why), n in reasons.most_common(30)]
    if verify:
        out += ["", "## Copy against fresh build (verify mode)", "",
                "| op family | compared | rows equal | UUID counter equal | no saved fingerprint |",
                "| --- | ---: | ---: | ---: | ---: |"]
        for f, c in sorted(verify.items()):
            out.append(f"| {f} | {c['compared']} | {c['rows equal']} | {c['uuid equal']} | {c['no saved fingerprint']} |")
        if mismatches:
            out += ["", "Tables that differed (family: kind:table x times):", ""]
            for f, c in sorted(mismatches.items()):
                out.append(f"- {f}: " + ", ".join(f"{k} x{n}" for k, n in c.most_common(20)))
    text = "\n".join(out) + "\n"
    (args.out or args.run / "setup-cache-report.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
