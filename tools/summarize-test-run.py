"""Summarise one backend test run directory, and optionally compare it with a baseline (PERF-01).

    python tools/summarize-test-run.py var/test-results/OPS-03/<run-id>
    python tools/summarize-test-run.py <run-dir> --compare <baseline-run-dir> [--extra <slow-tier-run-dir>]
        [--known-failure <junit-id>]...

Reads what tools/run-backend-suite-in-container.ps1 writes (junit.xml, collected.txt, phase-times.csv,
wall-time.txt, connections-peak.txt, memory-peak.txt) and writes report.md, summary.json and passed.txt into
the run directory. Standard library only, so it runs with any Python 3.10+ and needs no worktree imports.

--compare checks the phase-1 proof against a baseline: identical collected node IDs, identical JUnit pass list
(the run's pass list united with every --extra run, e.g. the separate slow-tier run), zero skips. A
--known-failure ID that fails in the baseline may fail again without breaking the proof; it must not pass in
one and fail in the other silently - both states are reported.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def junit_cases(run: Path) -> dict[str, str]:
    """`classname::name` -> passed | failed | skipped."""
    out: dict[str, str] = {}
    path = run / "junit.xml"
    if not path.exists():
        return out
    for case in ET.parse(path).getroot().iter("testcase"):
        key = f"{case.get('classname')}::{case.get('name')}"
        tags = {child.tag for child in case}
        if "failure" in tags or "error" in tags:
            state = "failed"
        elif "skipped" in tags:
            state = "skipped"
        else:
            state = "passed"
        if out.get(key) != "failed":  # an error in teardown after a pass counts as a failure
            out[key] = state
    return out


def junit_times(run: Path) -> dict[str, float]:
    path = run / "junit.xml"
    if not path.exists():
        return {}
    return {f"{c.get('classname')}::{c.get('name')}": float(c.get("time") or 0)
            for c in ET.parse(path).getroot().iter("testcase")}


def collected(run: Path) -> list[str]:
    path = run / "collected.txt"
    if not path.exists():
        return []
    return sorted(line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
                  if "::" in line and not line.startswith(("=", " ")))


def phases(run: Path) -> dict[str, dict[str, float]]:
    path = run / "phase-times.csv"
    out: dict[str, dict[str, float]] = collections.defaultdict(dict)
    if not path.exists():
        return out
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            out[row["nodeid"]][row["when"]] = float(row["duration_s"])
    return out


def read_text(run: Path, name: str) -> str:
    path = run / name
    return path.read_text(encoding="utf-8", errors="replace").strip() if path.exists() else ""


def summarise(run: Path) -> dict:
    cases = junit_cases(run)
    counts = collections.Counter(cases.values())
    ph = phases(run)
    setup = sum(p.get("setup", 0) for p in ph.values())
    call = sum(p.get("call", 0) for p in ph.values())
    teardown = sum(p.get("teardown", 0) for p in ph.values())
    files: dict[str, list[float]] = collections.defaultdict(lambda: [0, 0.0, 0.0, 0.0])
    for nodeid, p in ph.items():
        f = files[nodeid.split("::", 1)[0]]
        f[0] += 1
        f[1] += p.get("setup", 0)
        f[2] += p.get("call", 0)
        f[3] += p.get("teardown", 0)
    wall = re.search(r"wall_seconds=(\d+)", read_text(run, "wall-time.txt"))
    return {
        "run": run.name,
        "wall_seconds": int(wall.group(1)) if wall else None,
        "collected": len(collected(run)),
        "cases": len(cases),
        "passed": counts["passed"],
        "failed": counts["failed"],
        "skipped": counts["skipped"],
        "failed_ids": sorted(k for k, v in cases.items() if v == "failed"),
        "skipped_ids": sorted(k for k, v in cases.items() if v == "skipped"),
        "summed_test_seconds": round(sum(junit_times(run).values()), 1),
        "phase_seconds": {"setup": round(setup, 1), "call": round(call, 1), "teardown": round(teardown, 1)},
        "setup_share": round(setup / (setup + call + teardown), 3) if ph else None,
        "files": {k: {"tests": v[0], "setup": round(v[1], 1), "call": round(v[2], 1), "teardown": round(v[3], 1)}
                  for k, v in files.items()},
        "connections_peak": read_text(run, "connections-peak.txt"),
        "memory_peak": read_text(run, "memory-peak.txt"),
    }


def compare(run: Path, baseline: Path, extras: list[Path], known: set[str]) -> dict:
    base_ids = collected(baseline)
    run_ids = sorted(set(collected(run)).union(*(collected(e) for e in extras)))  # PERF-02: tiers collect apart
    base_cases = junit_cases(baseline)
    run_cases = dict(junit_cases(run))
    for extra in extras:
        for key, state in junit_cases(extra).items():
            if key in run_cases and run_cases[key] != state:
                run_cases[key] = "failed" if "failed" in (state, run_cases[key]) else state
            else:
                run_cases.setdefault(key, state)
    base_pass = {k for k, v in base_cases.items() if v == "passed"}
    run_pass = {k for k, v in run_cases.items() if v == "passed"}
    result = {
        "collected_identical": base_ids == run_ids and bool(base_ids),
        "collected_only_in_baseline": sorted(set(base_ids) - set(run_ids)),
        "collected_only_in_run": sorted(set(run_ids) - set(base_ids)),
        "cases_identical": set(base_cases) == set(run_cases),
        "pass_only_in_baseline": sorted(base_pass - run_pass - known),
        "pass_only_in_run": sorted(run_pass - base_pass - known),
        "known_failures": {k: [base_cases.get(k), run_cases.get(k)] for k in sorted(known)},
        "skipped_in_run": sorted(k for k, v in run_cases.items() if v == "skipped"),
        "unexpected_failures": sorted(k for k, v in run_cases.items() if v == "failed" and k not in known),
    }
    result["proof_passes"] = (result["collected_identical"] and result["cases_identical"]
                              and not result["pass_only_in_baseline"] and not result["pass_only_in_run"]
                              and not result["skipped_in_run"] and not result["unexpected_failures"])
    return result


def report(summary: dict, comparison: dict | None) -> str:
    s = summary
    lines = [f"# Backend run {s['run']}", "",
             f"- wall: {s['wall_seconds']} s ({(s['wall_seconds'] or 0) / 60:.1f} min)",
             f"- collected: {s['collected']}; JUnit cases: {s['cases']}; passed {s['passed']}, failed {s['failed']}, "
             f"skipped {s['skipped']}",
             f"- summed test time (JUnit): {s['summed_test_seconds']} s",
             f"- phases: set-up {s['phase_seconds']['setup']} s, call {s['phase_seconds']['call']} s, "
             f"teardown {s['phase_seconds']['teardown']} s; set-up share {s['setup_share']}",
             f"- connections: {s['connections_peak']}",
             f"- memory: {s['memory_peak']}", ""]
    if s["failed_ids"]:
        lines += ["## Failed", ""] + [f"- `{k}`" for k in s["failed_ids"]] + [""]
    if s["skipped_ids"]:
        lines += ["## Skipped", ""] + [f"- `{k}`" for k in s["skipped_ids"]] + [""]
    top = sorted(s["files"].items(), key=lambda kv: -(kv[1]["setup"] + kv[1]["call"] + kv[1]["teardown"]))[:40]
    lines += ["## Slowest 40 files (summed per-test phases)", "",
              "| file | tests | set-up s | call s | teardown s | set-up share |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for name, f in top:
        total = f["setup"] + f["call"] + f["teardown"]
        lines.append(f"| {name} | {f['tests']} | {f['setup']} | {f['call']} | {f['teardown']} | "
                     f"{f['setup'] / total if total else 0:.2f} |")
    if comparison is not None:
        lines += ["", "## Comparison with the baseline", "", "```json", json.dumps(comparison, indent=2), "```"]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--compare", type=Path)
    parser.add_argument("--extra", type=Path, action="append", default=[])
    parser.add_argument("--known-failure", action="append", default=[])
    args = parser.parse_args()
    summary = summarise(args.run)
    comparison = compare(args.run, args.compare, args.extra, set(args.known_failure)) if args.compare else None
    (args.run / "summary.json").write_text(json.dumps({"summary": summary, "comparison": comparison}, indent=2),
                                           encoding="utf-8")
    passed = sorted(k for k, v in junit_cases(args.run).items() if v == "passed")
    (args.run / "passed.txt").write_text("\n".join(passed) + "\n", encoding="utf-8")
    (args.run / "report.md").write_text(report(summary, comparison), encoding="utf-8")
    print(report(summary, comparison).split("## Slowest")[0])
    if comparison is not None:
        print(json.dumps({k: v for k, v in comparison.items() if not isinstance(v, list) or v}, indent=2))


if __name__ == "__main__":
    main()
