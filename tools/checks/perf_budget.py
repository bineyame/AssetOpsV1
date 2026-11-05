"""CH-5b1 R5 (CH5b1-R Q4/Q5): the chain read-path budget guard (EX-3).

    python tools/checks/perf_budget.py --fixture
    python tools/checks/perf_budget.py --database-url <clone url> --work <dir with keys.json> [--runs 3]
                                       [--store on|off] [--report] [--record out.json]

Budgets live in `config/chain/perf-budgets-v1.json`, copied from design §11b and never edited to pass.

- `--fixture` (check-all) evaluates every `tools/checks/fixtures/perf_budget/*.json` record against the budgets and
  asserts the declared expectation (breach set, not-measured set, verdict). It needs no database.
- `--database-url` measures the probe's routes plus the four `/chain` routes through `tools/chain_perf_probe.py`'s
  helpers (imported unchanged): cold = one fresh process per run, warm = `--runs` repeats after one discarded request.
  It exits 1 on any breach or any not-measured budget (the finish checks and E4). `--report` prints the same rows,
  `BREACH` included, and exits 0 (per-slice runs only).

Verdict rules: a non-200 response or a missing route is a breach; cold is the median of the cold runs, warm is the
nearest-rank p95 of the warm runs, bytes is the largest warm body. A budget without a measurement is `NOT MEASURED`
and is never a pass.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import subprocess
import sys
from pathlib import Path

CHECKS = Path(__file__).resolve().parent
TOOLS = CHECKS.parent
REPO = TOOLS.parent
BUDGETS_PATH = REPO / "config" / "chain" / "perf-budgets-v1.json"
FIXTURES = CHECKS / "fixtures" / "perf_budget"

WEEK = "from=2026-10-25T00:00:00Z&to=2026-11-01T00:00:00Z"
#: The four chain routes, on the probe's windows (`tools/chain_perf_probe.py` URLS).
CHAIN_URLS = {
    "kobo_chain_31oct": "/api/sites/KOBO-001/chain?date=2026-10-31",
    "cold_chain_failure_night": "/api/sites/COLD-LAB-001/chain?from=2026-10-31T16:00:00Z&to=2026-10-31T17:05:00Z",
    "ev_chain_27oct": "/api/sites/EV-LAB-001/chain?from=2026-10-27T08:00:00Z&to=2026-10-27T09:00:00Z",
    "estate_chain_week": f"/api/estate/chain?{WEEK}",
}


def load_budgets(path: Path = BUDGETS_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def evaluate(budgets: dict, record: dict) -> list[tuple[str, str, object, object, str]]:
    """Rows (subject, check, value, limit, verdict); verdict in PASS, BREACH, NO_BUDGET, NOT_MEASURED."""
    rows: list[tuple[str, str, object, object, str]] = []
    routes = record.get("routes", {})
    for route, family in sorted(budgets["routes"].items()):
        data = routes.get(route)
        if data is None:
            rows.append((route, "route", "missing", "present", "BREACH"))
            continue
        bad = sorted({s for s in data.get("status", []) if s != 200})
        if bad or not data.get("status"):
            rows.append((route, "status", bad or "none", 200, "BREACH"))
        if family is None:
            rows.append((route, "budget", None, None, "NO_BUDGET"))
            continue
        b = budgets["families"][family]
        measured = (("cold_ms", statistics.median(data["cold_ms"]) if data.get("cold_ms") else None, b["cold_ms"]),
                    ("warm_p95_ms", p95(data["warm_ms"]) if data.get("warm_ms") else None, b["warm_p95_ms"]),
                    ("max_bytes", data.get("bytes"), b["max_bytes"]))
        for check, value, limit in measured:
            if value is None:
                rows.append((route, check, None, limit, "NOT_MEASURED"))
            else:
                rows.append((route, check, value, limit, "PASS" if value <= limit else "BREACH"))
    other = record.get("other", {})
    for name, spec in sorted(budgets["other"].items()):
        value = other.get(name)
        if value is None:
            rows.append((name, f"owner {spec['owner']}", None, spec["limit"], "NOT_MEASURED"))
        else:
            rows.append((name, "value", value, spec["limit"], "PASS" if value <= spec["limit"] else "BREACH"))
    return rows


def failed(rows) -> bool:
    return any(r[4] in ("BREACH", "NOT_MEASURED") for r in rows)


def print_rows(rows) -> None:
    for subject, check, value, limit, verdict in rows:
        label = "NOT MEASURED" if verdict == "NOT_MEASURED" else verdict
        print(f"{label:<12} {subject:<36} {check:<20} value={value} limit={limit}")


def run_fixtures(budgets: dict, folder: Path = FIXTURES) -> int:
    files = sorted(folder.glob("*.json"))
    if not files:
        print(f"FAIL no fixtures under {folder}: the self-test would be vacuous")
        return 1
    bad = 0
    for path in files:
        fx = json.loads(path.read_text(encoding="utf-8"))
        rows = evaluate(budgets, fx["record"])
        got = {"breaches": sorted([r[0], r[1]] for r in rows if r[4] == "BREACH"),
               "not_measured": sorted(r[0] for r in rows if r[4] == "NOT_MEASURED"),
               "verdict": "FAIL" if failed(rows) else "PASS"}
        want = {"breaches": sorted(fx["expect"]["breaches"]), "not_measured": sorted(fx["expect"]["not_measured"]),
                "verdict": fx["expect"]["verdict"]}
        if got != want:
            bad += 1
            print(f"FAIL {path.name}: expected {want}, got {got}")
        else:
            print(f"ok   {path.name}: {got['verdict']} ({len(got['breaches'])} breach, "
                  f"{len(got['not_measured'])} not measured)")
    print(f"perf_budget fixtures: {len(files) - bad}/{len(files)} as expected")
    return 1 if bad else 0


# --- database mode (the probe's helpers, unchanged) ---------------------------------------------------------------

def _probe():
    sys.path.insert(0, str(TOOLS))
    import chain_perf_probe

    return chain_perf_probe


def all_urls() -> dict[str, str]:
    return {**_probe().URLS, **CHAIN_URLS}


def _child(url: str, work: Path, key: str) -> int:
    probe = _probe()
    kept = probe.capture_scopes()
    c = probe.client(url, work)
    print("RESULT " + json.dumps(probe.one(c, kept, all_urls()[key])))
    return 0


def measure(url: str, work: Path, runs: int, store: str, keys: list[str]) -> dict:
    os.environ["ASSETOPS_RESPONSE_STORE"] = store  # inherited by the cold children (as the probe does)
    probe = _probe()
    urls = all_urls()
    record: dict = {"params": {"runs": runs, "store": store, "routes": keys}, "routes": {}}
    for k in keys:
        cold, status = [], []
        for _ in range(runs):
            out = subprocess.run([sys.executable, __file__, "--database-url", url, "--work", str(work), "--child", k],
                                 capture_output=True, text=True)
            line = next((ln for ln in out.stdout.splitlines() if ln.startswith("RESULT ")), None)
            if line is None:
                print(f"cold {k}: child failed rc={out.returncode}: {out.stderr[-300:]}")
                status.append(-1)
                continue
            res = json.loads(line[7:])
            cold.append(res["ms"])
            status.append(res["status"])
        record["routes"][k] = {"cold_ms": cold, "status": status}
    kept = probe.capture_scopes()
    c = probe.client(url, work)
    for k in keys:
        probe.one(c, kept, urls[k])  # discarded
        warm = [probe.one(c, kept, urls[k]) for _ in range(runs)]
        entry = record["routes"][k]
        entry["warm_ms"] = [w["ms"] for w in warm]
        entry["status"] += [w["status"] for w in warm]
        entry["bytes"] = max(w["bytes"] for w in warm)
    return record


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python tools/checks/perf_budget.py")
    p.add_argument("--fixture", action="store_true")
    p.add_argument("--database-url")
    p.add_argument("--work", type=Path)
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--store", choices=("on", "off"), default="on")
    p.add_argument("--report", action="store_true", help="print BREACH rows and exit 0 (per-slice runs only)")
    p.add_argument("--record", type=Path, help="write the measured record (fixture format) here")
    p.add_argument("--child", help=argparse.SUPPRESS)
    args = p.parse_args(argv)
    if args.child:
        return _child(args.database_url, args.work, args.child)
    budgets = load_budgets()
    if args.fixture:
        return run_fixtures(budgets)
    if not args.database_url or not args.work:
        p.error("--fixture, or --database-url with --work")
    record = measure(args.database_url, args.work, args.runs, args.store, sorted(budgets["routes"]))
    if args.record:
        args.record.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    rows = evaluate(budgets, record)
    print_rows(rows)
    verdict = "FAIL" if failed(rows) else "PASS"
    print(f"perf_budget: {verdict} ({sum(r[4] == 'BREACH' for r in rows)} breach, "
          f"{sum(r[4] == 'NOT_MEASURED' for r in rows)} not measured){' [report mode: exit 0]' if args.report else ''}")
    return 0 if args.report or verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
