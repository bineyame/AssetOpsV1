"""DD-1b2b O9 (DD1a2-R3, DD1b2-R Q13): EX-1 on a CLONE of a whole build.

    python tools/demo_combined_ex1.py --db <clone db> --work <clone work> [--compare-only]

TREE FORM ONLY (DD1b2-R11 B1): run with cwd `<work>/tree/backend/tests`, `PYTHONPATH` the tree's nine parts
(`backend, backend/tests, contracts, gateway, simulator, host, host/tests, gateway/tests, tools`, each under `<work>/tree`)
and `DATABASE_URL` / `ASSETOPS_TEST_DATABASE_URL` the clone's URL, with this file run from the worktree. Outside that
form the tool refuses: the worktree form composes over the worktree's own `var/` and reads a degraded board.
Before the first read it reruns the S2 comparison on the copy (a TEMPLATE clone changes the database name and the store
root, which the comparison is bound to) and asserts the Kobo S board reads AVAILABLE.

Reads the Kobo S and S+1 boards (whole rows plus `read_state`; Findings compared as a set per row), runs
`demo_combined.py add-day --site KOBO-001 --kind normal --assess-now` (timed), then `tick --until-drained` (timed, tick
count from `<work>/tick-until-drained.json`), reads again, and compares. Prints one JSON document and writes
`<work>/ex1.json`. `DAY_NOT_IN_PAST` is not a fault: the add is refused before 11:00Z on S+2; rerun on the same clone
after 11:00Z. Never run on the rehearsal DB itself. Not covered here (declared): the check that S+2's renewable
selections exist before the first tick, which needs a stored-row query (handoff, O8 sixth measure).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
KOBO = "KOBO-001"


LISTS = ("issues", "in_hand", "earlier", "options")
O9_KEYS = ("assure_headline", "assure_count", "assure_state", "cost_lines")


def tree_form(backend_file: str, work: Path) -> bool:
    """True when the imported backend lives under `<work>/tree` (R11 B1 (a))."""
    try:
        Path(backend_file).resolve().relative_to((Path(work) / "tree").resolve())
    except ValueError:
        return False
    return True


def _key(item: object) -> str:
    return json.dumps(item, sort_keys=True, default=str)


def canon_row(row: dict) -> dict:
    """A row as comparable data: each item list keeps its order for non-Findings, and Findings are a sorted set."""
    out = dict(row)
    for k in LISTS:
        items = row.get(k) or []
        findings = sorted(_key(i) for i in items if isinstance(i, dict) and i.get("kind") == "FINDING")
        others = [_key(i) for i in items if not (isinstance(i, dict) and i.get("kind") == "FINDING")]
        out[k] = {"findings": findings, "others": others}
    return out


def summarise(board_s: dict, board_s1: dict) -> dict:
    """The comparable facts of two boards: `read_state`, every row whole (canonical), and the O9 facts derived from them
    (Assure count and headline, every Action/trial line, Finding ids)."""
    out: dict = {}
    for name, board in (("S", board_s), ("S+1", board_s1)):
        rows = {r["category"]: r for r in board["rows"]}
        assure = rows.get("ASSURE_PERFORMANCE", {})
        texts = [i.get("text") for r in board["rows"] for k in LISTS for i in r.get(k, [])]
        out[name] = {"read_state": board.get("read_state"),
                     "rows": {c: canon_row(r) for c, r in rows.items()},
                     "assure_headline": assure.get("headline"), "assure_count": assure.get("count"),
                     "assure_state": assure.get("state"),
                     "cost_lines": [t for t in texts if t and ("trial" in t.lower() or "ACT-" in t)],
                     "findings": sorted(str((i.get("ref") or {}).get("finding_id"))
                                        for r in board["rows"] for i in r.get("issues", []) if i.get("kind") == "FINDING")}
    return out


def compare(before: dict, after: dict) -> dict:
    """Whole rows plus `read_state` are compared and every difference is recorded in `diff`. It FAILS (`unchanged`
    false, `failures` named) only on R6 O9's items: Assure count or headline or state, the trial/Action lines, a new
    Finding, and a `read_state` change."""
    diff: dict = {}
    failures: list[str] = []
    for day in before:
        b, a = before[day], after[day]
        if b["read_state"] != a["read_state"]:
            diff[f"{day}.read_state"] = (b["read_state"], a["read_state"])
            failures.append(f"{day}.read_state")
        for cat in sorted(set(b["rows"]) | set(a["rows"])):
            if b["rows"].get(cat) != a["rows"].get(cat):
                diff[f"{day}.row.{cat}"] = {"before": b["rows"].get(cat), "after": a["rows"].get(cat)}
        for key in O9_KEYS:
            if b[key] != a[key]:
                diff[f"{day}.{key}"] = (b[key], a[key])
                failures.append(f"{day}.{key}")
        new = sorted(set(a["findings"]) - set(b["findings"]))
        if new:
            diff[f"{day}.new_findings"] = new
            failures.append(f"{day}.new_findings")
    return {"unchanged": not diff, "passes": not failures, "failures": failures, "diff": diff}


def renewable_selections(url: str, site_code: str, lo, hi) -> int:
    """The stored renewable-hour selections (`mini_depth_selection`, domain `renewable`) of a Site whose hour starts in
    [lo, hi): the heads exist before any tick, so the tick can queue the study."""
    import psycopg

    with psycopg.connect(url.replace("+psycopg", "")) as c:
        return c.execute(
            "SELECT count(DISTINCT s.window_start) FROM mini_depth_selection s JOIN site st ON st.tenant_id = "
            "s.tenant_id AND st.id = s.site_id WHERE st.site_code = %s AND s.domain = 'renewable' "
            "AND s.window_start >= %s AND s.window_start < %s", (site_code, lo, hi)).fetchone()[0]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    p.add_argument("--work", required=True, type=Path)
    p.add_argument("--compare-only", action="store_true", help="read the boards twice around nothing (a self-test)")
    a = p.parse_args()
    sys.path.insert(0, str(TOOLS))
    import demo_combined as dc
    import demo_combined_finish as fin

    work = a.work if a.work.is_absolute() else dc.REPO / a.work
    import assetops_backend

    if not tree_form(assetops_backend.__file__, work):
        raise SystemExit(f"EX-1 refused: assetops_backend ({assetops_backend.__file__}) is not under {work / 'tree'}; "
                         f"run in the tree form (see this file's docstring)")
    url = f"postgresql+psycopg://assetops:{dc.PW}@127.0.0.1:{dc.PG_PORT}/{a.db}"
    # R11 B1 (b): the S2 comparison is bound to the database name and store root, which a copy changes
    s2 = dc.Demo(a.db, str(work)).py("-m", "assetops_backend.evidence_migration", "run", "--tenant", "demo",
                                      "--site", KOBO, label="ex1-s2-comparison")
    ctx = fin.load(work, fin.app_client(url, work))

    def read() -> dict:
        ctx.cache.clear()
        return summarise(fin._kobo_board_s(ctx), fin._kobo_board_s1(ctx))

    base = [sys.executable, str(TOOLS / "demo_combined.py"), "--db", a.db, "--work", str(work)]
    before, doc = read(), {"db": a.db, "s2_comparison_tail": s2.stdout.strip().splitlines()[-1:]}
    for day in before:
        if before[day]["read_state"] != "AVAILABLE":
            raise SystemExit(f"EX-1: the {day} board reads {before[day]['read_state']!r}, not AVAILABLE, after the "
                             f"S2 comparison rerun: stop")
    if not a.compare_only:
        t0 = time.monotonic()
        add = subprocess.run([*base, "add-day", "--site", KOBO, "--kind", "normal", "--assess-now"],
                             capture_output=True, text=True)
        doc["add_seconds"], doc["add_rc"] = round(time.monotonic() - t0, 1), add.returncode
        doc["add_tail"] = (add.stdout + add.stderr).strip().splitlines()[-3:]
        if "DAY_NOT_IN_PAST" in add.stdout + add.stderr:
            doc["refused"] = "DAY_NOT_IN_PAST: not a fault; rerun after 11:00Z on the same clone"
        elif add.returncode != 0:
            raise SystemExit(f"add-day failed rc={add.returncode}: {doc['add_tail']}")
        else:
            # R8 A: S+2's renewable selections must exist (stored rows) after the add and before the first tick
            doc["renewable_selections_s2"] = renewable_selections(url, fin.KOBO, ctx.day(2), ctx.day(3))
            if not doc["renewable_selections_s2"]:
                raise SystemExit("EX-1: no stored renewable selection for S+2 after the add: stop, tick not run")
            t1 = time.monotonic()
            tick = subprocess.run([*base, "tick", "--until-drained"], capture_output=True, text=True)
            doc["tick_seconds"], doc["tick_rc"] = round(time.monotonic() - t1, 1), tick.returncode
            drained = work / "tick-until-drained.json"
            if drained.is_file():
                rec = json.loads(drained.read_text(encoding="utf-8"))
                doc["ticks"], doc["over_n"] = rec["ticks"], rec["over_n"]
            if tick.returncode != 0:
                raise SystemExit(f"tick --until-drained failed rc={tick.returncode}")
    after = read()
    for day in after:
        if after[day]["read_state"] != "AVAILABLE":
            doc["after_not_available"] = day
    doc.update(before=before, after=after, comparison=compare(before, after))
    (work / "ex1.json").write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")
    print(json.dumps(doc, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
