"""S5-02: the repeatable owner walkthrough for the Overview's selected-day Finding list
(tasks/S5-02-overview-finding-list.md, "Reproducible owner walkthrough").

A thin wrapper over `tools/s404_finding_index_walkthrough.py` (the S4-04 index fixture: assessed empty 2026-10-25,
positive 2026-10-15, dirty 2026-10-27, failed 2026-11-05, unassessed 2026-10-30). The imported Overview additionally
needs the S2 Evidence comparison (`site_overview/route.py`, 409 AWAITING_EVIDENCE_MIGRATION otherwise), so `prepare`
runs `python -m assetops_backend.evidence_migration run --tenant demo --site KOBO-001` in the same work tree (as
`tools/s5_overview_walkthrough.py` does), then proves every day reads as an imported `site-window-summary-1` through
the served Overview and records the positive day's index first row against the Overview's known Finding.

No schedule is installed, so the Overview's freshness reads a stopped schedule; that limits money only, not the
known Finding or the list.

Commands (database `assetops_s404_owner*`, work directory `var/s404_owner*`; defaults below use the `_s502`
suffix, API 8952, web 5452):

    prepare | serve | tick | late | settle | gate --close | gate --open | drop     (as the S4-04 tool)

Run from the repository root with the repository venv (`.venv`).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import s402c_late_power_walkthrough as lr  # noqa: E402
import s404_finding_index_walkthrough as w  # noqa: E402
import s5_overview_walkthrough as s5  # noqa: E402

DEFAULTS = {"--db": "assetops_s404_owner_s502", "--work": "var/s404_owner_s502", "--api-port": "8952",
            "--web-port": "5452", "--tls-port": "8953", "--http-port": "8954"}
MANIFEST = "s502-manifest.json"
say, step = w.say, w.step


def with_defaults(argv: list[str]) -> list[str]:
    out = list(argv)
    for flag, value in DEFAULTS.items():
        if flag not in out:
            out += [flag, value]
    return out


def opt(argv: list[str], flag: str) -> str:
    return argv[argv.index(flag) + 1]


def overview_url(port: int, day: str) -> str:
    return f"http://127.0.0.1:{port}/api/sites/{w.SITE}/overview?date={day}"


def verify_overview(work: Path, db: str, port: int) -> list[str]:
    """Every fixture day must read as an imported Overview; the positive day's first index row is recorded."""
    proc = w.start_api(work, db, port)
    failures: list[str] = []
    out: dict[str, Any] = {"days": {}}
    try:
        w.wait_api(port, proc)
        for name, day in w.DAYS.items():
            status, body = w.get_json(overview_url(port, day))
            if status != 200 or not isinstance(body, dict) or body.get("schema_version") != "site-window-summary-1":
                failures.append(f"{name} {day}: Overview is not an imported site-window-summary-1 (HTTP {status})")
                out["days"][name] = {"http": status, "body": str(body)[:300]}
                continue
            k = body.get("known_finding") or {}
            out["days"][name] = {"http": 200, "window": body["window"], "freshness": body["freshness"]["state"],
                                 "freshness_reasons": body["freshness"]["reasons"][:6],
                                 "known_finding": [k.get("id"), k.get("revision_id"), k.get("selected_by")],
                                 "watermarks": body["watermarks"], "model_version": body.get("model_version"),
                                 "assessment": [body["assessment"].get("run_id"),
                                                body["assessment"].get("window_assessment_revision_id")]}
            idx_status, idx = w.get_json(w.index_url(port, body["window"]["start"], body["window"]["end"],
                                                     limit="2"))
            out["days"][name]["index"] = w.summary(idx_status, idx)
            if name == "positive" and idx_status == 200 and idx.get("rows"):
                first = idx["rows"][0]
                out["positive_parity"] = {
                    "index_first": [first["finding_id"], first["finding_revision_id"]],
                    "overview_known": [k.get("id"), k.get("revision_id")],
                    "equal": [first["finding_id"], first["finding_revision_id"]] == [k.get("id"), k.get("revision_id")],
                    "index_day": next((d for d in idx["watermarks"]["days"] if d["day"] == w.DAYS["positive"]), None),
                    "index_matcher": idx["watermarks"]["matcher"],
                }
        out["failures"] = failures
        (work / MANIFEST).write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    finally:
        proc.terminate()
        proc.wait(timeout=30)
    return failures


def main(argv: list[str] | None = None) -> int:
    argv = with_defaults(list(sys.argv[1:] if argv is None else argv))
    command = argv[0] if argv else ""
    if command == "tick":
        work = w.args_work(type("A", (), {"work": opt(argv, "--work")})())
        step("One explicit schedule pass (no OS schedule is installed), then the positive day's freshness")
        out = s5.tick(work, opt(argv, "--db"))
        proc = w.start_api(work, opt(argv, "--db"), int(opt(argv, "--api-port")) + 20)
        try:
            port = int(opt(argv, "--api-port")) + 20
            w.wait_api(port, proc)
            _, body = w.get_json(overview_url(port, w.DAYS["positive"]))
            f = (body or {}).get("freshness", {}) if isinstance(body, dict) else {}
            say(f"Positive day Overview freshness: {f.get('state')} {f.get('reasons')}")
        finally:
            proc.terminate()
            proc.wait(timeout=30)
        return 0 if out["exit"] == 0 else 1
    if command != "prepare":
        if command == "serve":
            web = int(opt(argv, "--web-port"))
            say("Overview owner URLs (after the frontend starts):")
            for name, day in w.DAYS.items():
                say(f"  {name:11} http://localhost:{web}/sites/{w.SITE}?date={day}")
        return w.main(argv)
    code = w.main(argv)
    work = w.args_work(type("A", (), {"work": opt(argv, "--work")})())
    db = opt(argv, "--db")
    if code != 0:
        say("S4-04 prepare reported failures; the Overview was not checked.")
        return code
    step("S2 Evidence comparison for KOBO-001 (opens the imported Overview)")
    done: subprocess.CompletedProcess = lr.tree_py(work, db, "-m", "assetops_backend.evidence_migration", "run",
                                                   "--tenant", "demo", "--site", w.SITE, cwd=".", check=False)
    say("  " + " | ".join((done.stdout or done.stderr).strip().splitlines()[-3:]))
    if done.returncode:
        say(f"Unmet precondition: the S2 Evidence comparison exited {done.returncode}; the Overview stays closed.")
        return 1
    step("Verify every day through the served Overview and the index preview")
    failures = verify_overview(work, db, int(opt(argv, "--api-port")))
    say(json.dumps(json.loads((work / MANIFEST).read_text(encoding="utf-8")).get("positive_parity"), indent=1))
    say(f"{len(failures)} Overview check(s) failed" + ("" if not failures else ":\n  " + "\n  ".join(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
