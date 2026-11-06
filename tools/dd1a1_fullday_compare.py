"""DD-1a1 L2: compare the `without` and `with` Kobo builds of tools/dd1a1_fullday_probe.py (two own *_test DBs).
Rows are compared with ids, uuids and timestamps removed (they differ by run), as sorted multisets of the rest.

    python tools/dd1a1_fullday_compare.py <db-without> <db-with>"""

from __future__ import annotations

import collections
import json
import re
import sys

from sqlalchemy import create_engine, text

BASE = "postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/"
TABLES = ("finding", "finding_revision", "action", "action_event", "action_policy_change", "work_case",
          "work_case_revision", "work_event", "verification_plan", "verification_metric", "verification_outcome",
          "trial_cost_comparison_revision", "financial_consequence_work", "financial_assumption_revision")
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|run-[0-9a-f]{32}")
TIME = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[^\"',}\]]*")


def rows(engine, table: str) -> collections.Counter:
    with engine.connect() as c:
        data = c.execute(text(f'select * from "{table}"')).mappings().all()
    out = collections.Counter()
    for r in data:
        out[json.dumps({k: TIME.sub("T", UUID.sub("ID", str(v))) for k, v in r.items()
                        if not (k == "id" or k.endswith("_id") or k.endswith("_at") or k.endswith("_no"))},
                       sort_keys=True)] += 1
    return out


def main(a: str, b: str) -> int:
    ea, eb = create_engine(BASE + a), create_engine(BASE + b)
    bad = 0
    for t in TABLES:
        ra, rb = rows(ea, t), rows(eb, t)
        same = ra == rb
        bad += not same
        print(f"{t:36} without {sum(ra.values()):3}  with {sum(rb.values()):3}  {'EQUAL' if same else 'DIFFERENT'}")
        if not same:
            for k in list((rb - ra))[:3]:
                print("   only with:", k[:400])
            for k in list((ra - rb))[:3]:
                print("   only without:", k[:400])
    return bad


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
