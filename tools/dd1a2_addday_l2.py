"""DD1a2-R Q8.3 L2 (own `*_test` DB that `dd1a2_mill3_dry_run.py mill3` built; never a prepare). Fills the `missing` day
S-10 through the add-day path: `plan_add_runs` (the Site-local `delivered_days` basis, FILL-1, three runs in source-time
order), then the Kobo child's `add_day`. Reports the runs, the evidence per Site-local day and the second fill's refusal.

    python tools/dd1a2_addday_l2.py <work> [steady-before-first]
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import psycopg


def main(work: Path, kind: str) -> int:
    import demo_combined as dc
    import demo_combined_kobo as dk
    import demo_story_days as sd

    url = os.environ["ASSETOPS_TEST_DATABASE_URL"]
    assert url.split("/")[-1].endswith("_test") and "polish" not in url and "demo3" not in url
    plain = url.replace("+psycopg", "")
    work.mkdir(parents=True, exist_ok=True)

    def now():
        with psycopg.connect(plain, autocommit=True) as c:
            return c.execute("SELECT clock_timestamp()").fetchone()[0]

    def delivered() -> set[str]:
        with psycopg.connect(plain, autocommit=True) as c:
            return {r[0] for r in c.execute(
                "SELECT DISTINCT to_char(e.source_time AT TIME ZONE s.timezone, 'YYYY-MM-DD') FROM accepted_evidence e "
                "JOIN ingestion_disposition d ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal "
                "JOIN site s ON s.id = e.site_id WHERE s.site_code = 'KOBO-001'").fetchall()}

    doc = sd.load()
    story = dc.resolve_story(now(), days_doc=doc)
    rows = story.pop("days")
    current = sd.from_payload([r for r in rows if r["site"] == "kobo" and -14 <= r["offset"] < -4])
    installs = {n: dc.at(story[n]["install_at"]) for n in dc.SITES}
    S = dc.at(story["S"])
    before = delivered()
    out: dict = {"S": story["S"], "kind": kind, "delivered_before": sorted(before)}
    day_text = "2026-10-26" if "2026-10-26" in before else None  # a rerun after the fill: only the checks below
    try:
        runs = sd.plan_add_runs(doc, current, "kobo", kind, S, now(), day="S-10d", delivered_days=before, installs=installs)
    except sd.StoryDaysError as err:
        out["plan_refusal"] = err.error_code
        runs = []
    if runs:
        planned = next(r for r in runs if not r.complement_of)
        day_text = planned.day
        out["planned"] = {"day": planned.day, "kind": planned.kind, "runs": [(r.scenario["scenario_id"], str(r.received_at),
                                                                              str(r.start), str(r.end)) for r in runs]}
        print("planned", out["planned"], flush=True)
        done = dk.add_day(url, work, [r.payload() for r in runs])
        out["added"] = {"run_id": done["run_id"], "findings": done.get("findings")}
    after = delivered()
    out["delivered_after_new"] = sorted(after - before)
    with psycopg.connect(plain, autocommit=True) as c:
        out["readings_on_day"] = c.execute(
            "SELECT count(*), min(e.source_time), max(e.source_time), min(e.received_at)::text FROM accepted_evidence e "
            "JOIN site s ON s.id = e.site_id "
            "WHERE s.site_code = 'KOBO-001' AND (e.source_time AT TIME ZONE s.timezone)::date = %s::date", (day_text,)).fetchone()
    out["readings_on_day"] = [str(x) for x in out["readings_on_day"]]
    try:
        sd.plan_add_runs(doc, current, "kobo", kind, S, now(), day="S-10d", delivered_days=after, installs=installs)
        out["second_fill"] = "NOT REFUSED"
    except sd.StoryDaysError as err:
        out["second_fill"] = err.error_code
    (work / "addday.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(json.dumps(out, default=str), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else "steady-before-first"))
