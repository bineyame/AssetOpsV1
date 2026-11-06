"""DD-1a1 L2 probe (own `*_test` DB, no prepare): build the Kobo side of the demo story on the v2 day list, with or
without the steady complement runs, so the two builds can be compared (DD1a1-R3 Q1 checks, DD1a1-R Q6).

    python tools/dd1a1_fullday_probe.py <with|without> <work-dir>      (ASSETOPS_TEST_DATABASE_URL names the DB)

`without` removes every Kobo `complement` from the v2 kinds, which is the story-days-only calendar. Writes
`<work>/kobo.json` (the build record) and `<work>/probe.json` (counts and the compared figures)."""

from __future__ import annotations

import copy
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(mode: str, work: Path) -> None:
    import pg_harness
    import psycopg

    import demo_combined as dc
    import demo_combined_kobo as dk
    import demo_story_days as sd

    url = pg_harness.fresh_database()
    doc = sd.load(sd.V2_FILE)
    doc["sites"] = {"kobo": doc["sites"]["kobo"]}
    if mode == "without":
        for spec in doc["kinds"]["kobo"].values():
            spec.pop("complement", None)
    work.mkdir(parents=True, exist_ok=True)
    (work / "db.txt").write_text(url, encoding="utf-8")
    with psycopg.connect(url.replace("+psycopg", "")) as c:
        db_now = c.execute("SELECT clock_timestamp()").fetchone()[0]
    story = dc.resolve_story(db_now, days_doc=doc)
    days = story.pop("days")
    (work / "days.json").write_text(json.dumps({"S": story["S"], "days": days, "doc": doc}, indent=2), encoding="utf-8")
    story["code"], story["sites"] = "probe", ["kobo"]
    (work / "story.json").write_text(json.dumps(story, indent=2), encoding="utf-8")
    began = time.monotonic()
    dk.build(url, work, story)
    print("build wall s", round(time.monotonic() - began, 1), "runs", len([d for d in days if d["site"] == "kobo" and d["received_at"]]))


if __name__ == "__main__":
    main(sys.argv[1], Path(sys.argv[2]))
