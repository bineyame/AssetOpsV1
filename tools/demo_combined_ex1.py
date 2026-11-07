"""DD-1b2b O9 (DD1a2-R3, DD1b2-R Q13): EX-1 on a CLONE of a whole build.

    python tools/demo_combined_ex1.py --db <clone db> --work <clone work> [--compare-only]

Reads the Kobo S and S+1 boards (Assure count, trial line, Action words, Findings), runs
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


def summarise(board_s: dict, board_s1: dict) -> dict:
    """The comparable facts of two boards: the Assure row's count and headline, every Action/trial line, Findings."""
    out: dict = {}
    for name, board in (("S", board_s), ("S+1", board_s1)):
        rows = {r["category"]: r for r in board["rows"]}
        assure = rows.get("ASSURE_PERFORMANCE", {})
        texts = [i.get("text") for r in board["rows"] for k in ("issues", "in_hand", "earlier", "options")
                 for i in r.get(k, [])]
        out[name] = {"assure_headline": assure.get("headline"), "assure_count": assure.get("count"),
                     "assure_state": assure.get("state"),
                     "cost_lines": [t for t in texts if t and ("trial" in t.lower() or "ACT-" in t)],
                     "findings": sorted(str((i.get("ref") or {}).get("finding_id"))
                                        for r in board["rows"] for i in r.get("issues", []) if i.get("kind") == "FINDING")}
    return out


def compare(before: dict, after: dict) -> dict:
    """O9's pass condition: Assure count, trial line and Action words unchanged, and no new Finding."""
    diff: dict = {}
    for day in before:
        for key in ("assure_headline", "assure_count", "assure_state", "cost_lines"):
            if before[day][key] != after[day][key]:
                diff[f"{day}.{key}"] = (before[day][key], after[day][key])
        new = sorted(set(after[day]["findings"]) - set(before[day]["findings"]))
        if new:
            diff[f"{day}.new_findings"] = new
    return {"unchanged": not diff, "diff": diff}


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
    url = f"postgresql+psycopg://assetops:{dc.PW}@127.0.0.1:{dc.PG_PORT}/{a.db}"
    ctx = fin.load(work, fin.app_client(url, work))

    def read() -> dict:
        ctx.cache.clear()
        return summarise(fin._kobo_board_s(ctx), fin._kobo_board_s1(ctx))

    base = [sys.executable, str(TOOLS / "demo_combined.py"), "--db", a.db, "--work", str(work)]
    before, doc = read(), {"db": a.db}
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
    doc.update(before=before, after=after, comparison=compare(before, after))
    (work / "ex1.json").write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")
    print(json.dumps(doc, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
