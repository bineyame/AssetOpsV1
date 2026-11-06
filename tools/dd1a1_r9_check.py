"""DD1a1-R9 L2 check on a built `*_test` DB: the reserve-trial plan's baseline days.

    python tools/dd1a1_r9_check.py <db-name>

For each baseline day of every reserve-trial plan: every dispatch selection made after the plan was recorded is
compared with the pinned run on the facts the verification reads over [baseline_start, baseline_end)
(`verification._baseline_facts`). Each must be equal; the latest outcome must list the day as `reselected` when its
current run differs from the pinned one, and must be VERIFIED. Prints one PASS/FAIL line per check."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

import psycopg

BASE = "postgresql://assetops:assetops-local-dev@127.0.0.1:55432/"


def main(db: str) -> int:
    from assetops_backend.actions.verification import _baseline_facts
    from assetops_backend.analytics.composition import build_dispatch_read_service

    reads = build_dispatch_read_service(BASE.replace("postgresql:", "postgresql+psycopg:") + db)
    c = psycopg.connect(BASE + db)
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(("PASS " if ok else "FAIL ") + name + (f" ({detail})" if detail else ""))
        if not ok:
            fails.append(name)

    plans = c.execute("SELECT id, tenant_id, site_id, baseline_start, baseline_end, baseline_selection, recorded_at "
                      "FROM verification_plan ORDER BY recorded_at").fetchall()
    check("a reserve-trial plan exists (non-vacuous)", len(plans) >= 1, f"{len(plans)} plans")
    for pid, tenant, site, lo, hi, selection, frozen in plans:
        sel = selection if isinstance(selection, dict) else json.loads(selection)
        compared = 0
        for pin in sel["days"]:
            day = date.fromisoformat(str(pin["day"]))
            start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
            pinned = reads.store.run_detail(tenant, site, UUID(str(pin["run_id"])))
            want = _baseline_facts(None if pinned is None else pinned["revisions"], lo, hi)
            later = c.execute("SELECT seq, run_id, selected_at FROM analytic_run_selection WHERE site_id = %s "
                              "AND analytic_id LIKE 'dispatch%%' AND window_start = %s AND window_end = %s "
                              "AND selected_at > %s ORDER BY seq", (site, start, start + timedelta(days=1),
                                                                   frozen)).fetchall()
            for seq, run, at in later:
                if str(run) == str(pin["run_id"]):
                    continue
                got = _baseline_facts(reads.store.run_detail(tenant, site, run)["revisions"], lo, hi)
                compared += 1
                check(f"plan {pid} {day} seq {seq} at {at:%m-%d %H:%M}Z: baseline facts equal to pinned run",
                      want is not None and got == want, f"{len(want or [])} assessments")
            print(f"  {day}: pinned {pin['run_id']}, {len(later)} post-freeze selections, {compared} compared")
        out = c.execute("SELECT outcome, details FROM verification_outcome WHERE plan_id = %s ORDER BY recorded_at "
                        "DESC LIMIT 1", (pid,)).fetchone()
        check(f"plan {pid} latest outcome VERIFIED", out is not None and out[0] == "VERIFIED",
              None if out is None else out[0])
        if out is not None:
            details = out[1] if isinstance(out[1], dict) else json.loads(out[1])
            for d in details["days"]["baseline"]:
                moved_run = d["pinned_run_id"] != (d["status"] or {}).get("run_id")
                check(f"outcome baseline {d['day']}: moved=[] and reselected listed iff the run changed",
                      d["moved"] == [] and bool(d.get("reselected")) == moved_run,
                      json.dumps(d.get("reselected")))
    print("R9 check:", "FAIL " + ", ".join(fails) if fails else "PASS")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
