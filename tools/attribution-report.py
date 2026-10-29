"""Attribution report for one or more instrumented backend runs (PERF-01).

    python tools/attribution-report.py <run-dir> [<more run dirs, e.g. the slow tier>] [--frontend <file>]
        [--overhead '{"wrapper_us_per_call": .., "listener_us_per_statement": ..}'] [--out <dir>]

Reads <run>/attribution/attribution-*.jsonl (backend/tests/phase_attribution.py), wall-time.txt and
memory-peak.txt, and writes attribution-report.md and attribution.json into --out (default: the first run dir).
Standard library only.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

PARTS = ("db", "install", "gateway", "build", "app", "subprocess", "setup_other", "checks", "teardown")
LABELS = {"db": "DB create/clone/drop + migrations", "install": "Site/Foundation install + credentials",
          "gateway": "gateway subprocess start/stop", "build": "replay / ingest / seed (site build)",
          "app": "app / router / TestClient start-up", "subprocess": "other child processes",
          "setup_other": "other fixture set-up", "checks": "the test's own work (remainder of call)",
          "teardown": "teardown"}
WORLD = ("db", "install", "gateway", "build")


def load(run: Path):
    rows, summaries = [], []
    for path in sorted((run / "attribution").glob("attribution-*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            (summaries if record.get("summary") else rows).append(record)
    wall = re.search(r"wall_seconds=(\d+)", (run / "wall-time.txt").read_text()) if (run / "wall-time.txt").exists() else None
    memory = (run / "memory-peak.txt").read_text().strip() if (run / "memory-peak.txt").exists() else ""
    return rows, summaries, int(wall.group(1)) if wall else None, memory


def parts(row) -> dict:
    out = {c: row["cats"].get(c, 0.0) for c in PARTS[:6]}
    out["setup_other"] = row["setup_other"]
    out["checks"] = row["checks"]
    out["teardown"] = row["teardown"]
    return out


def pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "-"


def analyse(run: Path, overhead: dict | None):
    rows, summaries, wall, memory = load(run)
    measured = sum(r["setup"] + r["call"] + r["teardown"] for r in rows)
    totals = collections.Counter()
    for r in rows:
        totals.update(parts(r))
    attributed = sum(totals.values())
    # workers and the idle tail
    workers = collections.defaultdict(list)
    for r in rows:
        workers[r["worker"]].append((r["t0"], r["t1"], r["setup"] + r["call"] + r["teardown"]))
    start = min(r["t0"] for r in rows)
    end = max(r["t1"] for r in rows)
    per_worker = {}
    for w, items in sorted(workers.items()):
        items.sort()
        busy = sum(i[2] for i in items)
        protocol = sum(i[1] - i[0] for i in items)
        per_worker[w] = {"tests": len(items), "first_start_s": round(items[0][0] - start, 1),
                         "last_end_s": round(items[-1][1] - start, 1), "tail_idle_s": round(end - items[-1][1], 1),
                         "test_phases_s": round(busy, 1), "protocol_s": round(protocol, 1)}
    span = end - start
    # files
    files = collections.defaultdict(collections.Counter)
    file_tests = collections.Counter()
    for r in rows:
        f = r["nodeid"].split("::", 1)[0]
        files[f].update(parts(r))
        file_tests[f] += 1
    # set-ups
    fp_count = collections.Counter()
    fp_world = collections.Counter()
    fp_tests = collections.defaultdict(set)
    for r in rows:
        world = sum(r["cats"].get(c, 0.0) for c in WORLD)
        builds = r["builds"]
        for b in builds:
            fp_count[b] += 1
            fp_world[b] += world / len(builds)
            fp_tests[b].add(r["nodeid"])
    built_tests = [r for r in rows if r["builds"]]
    # a test's set-up = the ordered tuple of its root builds (e.g. W4 _setup + _ingest + _reconcile is one set-up)
    composite = collections.Counter()
    composite_world = collections.Counter()
    composite_files = collections.defaultdict(set)
    for r in built_tests:
        key = " + ".join(r["builds"])
        composite[key] += 1
        composite_world[key] += sum(r["cats"].get(c, 0.0) for c in WORLD)
        composite_files[key].add(r["nodeid"].split("::", 1)[0])
    shapes = collections.Counter()
    for r in rows:
        if r["setup"] + r["call"] + r["teardown"] >= 5:
            for shape, n in r.get("check_writes", {}).items():
                shapes[shape] += n
    # read-only versus writes, heavy tests (>= 5 s)
    heavy = [r for r in rows if r["setup"] + r["call"] + r["teardown"] >= 5]
    def check_writes(r):
        return r["writes"].get("checks", 0)
    def setup_writes(r):
        return r["writes"].get("setup_other", 0)
    split = {
        "heavy_tests": len(heavy),
        "heavy_seconds": round(sum(r["setup"] + r["call"] + r["teardown"] for r in heavy), 1),
        "read_only_after_build": sum(1 for r in heavy if check_writes(r) == 0),
        "read_only_after_build_seconds": round(sum(r["setup"] + r["call"] + r["teardown"]
                                                   for r in heavy if check_writes(r) == 0), 1),
        "writes_after_build": sum(1 for r in heavy if check_writes(r) > 0),
        "writes_after_build_seconds": round(sum(r["setup"] + r["call"] + r["teardown"]
                                                for r in heavy if check_writes(r) > 0), 1),
        "heavy_with_root_build": sum(1 for r in heavy if r["builds"]),
        "heavy_with_root_build_read_only": sum(1 for r in heavy if r["builds"] and check_writes(r) == 0),
        "heavy_setup_fixture_writes": sum(1 for r in heavy if setup_writes(r) > 0),
        "check_write_histogram": dict(collections.Counter(
            "0" if check_writes(r) == 0 else "1-10" if check_writes(r) <= 10 else "11-100" if check_writes(r) <= 100
            else ">100" for r in heavy)),
    }
    calls = sum(s.get("wrapped_calls", 0) for s in summaries)
    statements = sum(s.get("statements", 0) for s in summaries)
    over = None
    if overhead:
        over = round(calls * overhead["wrapper_us_per_call"] / 1e6 + statements * overhead["listener_us_per_statement"]
                     / 1e6, 1)
    return {
        "run": run.name, "pytest_wall_s": wall, "memory_peak": memory, "tests": len(rows), "workers": len(workers),
        "measured_test_seconds": round(measured, 1), "attributed_seconds": round(attributed, 1),
        "unattributed_seconds": round(measured - attributed, 2),
        "totals": {k: round(totals[k], 1) for k in PARTS},
        "span_s": round(span, 1), "per_worker": per_worker,
        "worker_idle_s": round(len(workers) * span - measured, 1),
        "files": {f: {"tests": file_tests[f], "total": round(sum(c.values()), 1), **{k: round(c[k], 1) for k in PARTS}}
                  for f, c in files.items()},
        "setups": {"root_builds": sum(fp_count.values()), "distinct": len(fp_count),
                   "tests_with_a_build": len(built_tests),
                   "world_seconds_in_tests_with_a_build": round(sum(sum(r["cats"].get(c, 0.0) for c in WORLD)
                                                                    for r in built_tests), 1),
                   "by_fingerprint": sorted(({"fingerprint": fp, "builds": n, "world_seconds": round(fp_world[fp], 1),
                                              "files": sorted({t.split("::")[0] for t in fp_tests[fp]})}
                                             for fp, n in fp_count.items()), key=lambda d: -d["world_seconds"]),
                   "distinct_test_setups": len(composite),
                   "test_setups": sorted(({"setup": k, "tests": n, "world_seconds": round(composite_world[k], 1),
                                           "files": sorted(composite_files[k])} for k, n in composite.items()),
                                         key=lambda d: -d["world_seconds"])},
        "check_write_shapes_heavy": shapes.most_common(25),
        "read_only_split": split,
        "instrumentation": {"wrapped_calls": calls, "statements": statements, "overhead_s_estimate": over},
    }


def markdown(results: list[dict], frontend: str | None) -> str:
    out = ["# PERF-01 measured time attribution", ""]
    for a in results:
        m = a["measured_test_seconds"]
        out += [f"## Run {a['run']}", "",
                f"- pytest wall {a['pytest_wall_s']} s; {a['tests']} tests on {a['workers']} workers; first test start to "
                f"last test end {a['span_s']} s",
                f"- measured test time (sum of set-up + call + teardown) {m} s; attributed {a['attributed_seconds']} s; "
                f"unattributed {a['unattributed_seconds']} s",
                f"- worker idle inside the span (workers x span - measured) {a['worker_idle_s']} s",
                f"- memory: {a['memory_peak']}",
                f"- instrumentation: {a['instrumentation']}", "",
                "| part | seconds | share of measured | wall-equivalent min (/ workers) |", "| --- | ---: | ---: | ---: |"]
        for k in PARTS:
            v = a["totals"][k]
            out.append(f"| {LABELS[k]} | {v} | {pct(v, m)} | {v / a['workers'] / 60:.1f} |")
        out.append(f"| **total** | {round(sum(a['totals'].values()), 1)} | | |")
        out += ["", "### Workers and the idle tail", "", "| worker | tests | first start s | last end s | tail idle s | busy s |",
                "| --- | ---: | ---: | ---: | ---: | ---: |"]
        for w, d in a["per_worker"].items():
            out.append(f"| {w} | {d['tests']} | {d['first_start_s']} | {d['last_end_s']} | {d['tail_idle_s']} | "
                       f"{d['test_phases_s']} |")
        out += ["", "### Top 30 files by measured time", "",
                "| file | tests | total | db | install | gateway | build | app | subproc | setup other | checks | teardown |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for f, d in sorted(a["files"].items(), key=lambda kv: -kv[1]["total"])[:30]:
            out.append(f"| {f.replace('tests/', '')} | {d['tests']} | {d['total']} | " +
                       " | ".join(str(d[k]) for k in PARTS) + " |")
        s = a["setups"]
        out += ["", "### Site set-ups", "",
                f"- root builds {s['root_builds']} across {s['tests_with_a_build']} tests; distinct set-ups "
                f"{s['distinct']}; world time (db+install+gateway+build) in those tests "
                f"{s['world_seconds_in_tests_with_a_build']} s", "",
                "| builds | world s | fingerprint | files |", "| ---: | ---: | --- | --- |"]
        for d in s["by_fingerprint"][:60]:
            files = ", ".join(x.replace("tests/", "") for x in d["files"][:4]) + (" ..." if len(d["files"]) > 4 else "")
            out.append(f"| {d['builds']} | {d['world_seconds']} | `{d['fingerprint'][:140]}` | {files} |")
        out += ["", f"Distinct per-test set-ups (ordered root builds of one test): {s['distinct_test_setups']}", "",
                "| tests | world s | set-up | files |", "| ---: | ---: | --- | --- |"]
        for d in s["test_setups"][:60]:
            files = ", ".join(x.replace("tests/", "") for x in d["files"][:4]) + (" ..." if len(d["files"]) > 4 else "")
            out.append(f"| {d['tests']} | {d['world_seconds']} | `{d['setup'][:160]}` | {files} |")
        out += ["", "Most frequent write statements in the check phase of tests of 5 s or more:", ""]
        out += [f"- {n} x `{shape}`" for shape, n in a["check_write_shapes_heavy"]]
        out += ["", "### Read-only versus writes after the build (tests of 5 s or more)", "", "```json",
                json.dumps(a["read_only_split"], indent=2), "```", ""]
    if frontend:
        out += ["## Frontend", "", "```", frontend.strip(), "```", ""]
    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", nargs="+", type=Path)
    parser.add_argument("--frontend", type=Path)
    parser.add_argument("--overhead")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    overhead = json.loads(args.overhead) if args.overhead else None
    results = [analyse(run, overhead) for run in args.runs]
    frontend = args.frontend.read_text(encoding="utf-8", errors="replace") if args.frontend else None
    out = args.out or args.runs[0]
    out.mkdir(parents=True, exist_ok=True)
    (out / "attribution.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (out / "attribution-report.md").write_text(markdown(results, frontend), encoding="utf-8")
    print(markdown(results, frontend)[:6000])


if __name__ == "__main__":
    main()
