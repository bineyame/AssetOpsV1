"""DD-1b1 review H1: `Demo.prepare` must hand `finish` the plan with its `days`. Drives the real `prepare` with the
database and child processes stubbed, so `finish` and `objectives_instants` run on the dict prepare really builds.
No database, no child process."""
from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import demo_combined as tool  # noqa: E402
import demo_story_days as sd  # noqa: E402


class _Cursor:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class _Conn:
    def __init__(self, now):
        self.now = now

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, *args):
        return _Cursor((self.now,) if "clock_timestamp" in sql else None)


def test_three_site_prepare_finishes_with_the_plan_days(monkeypatch) -> None:
    import psycopg

    db_now = datetime(2026, 10, 31, 4, tzinfo=timezone.utc)
    demo = tool.Demo("assetops_polish_h1l0_test", "var/polish_h1l0")
    calls: list[tuple] = []

    def py(*argv, **kw):
        calls.append(argv)
        out = str(demo.tree) if kw.get("label") == "isolation" else ""
        return subprocess.CompletedProcess(argv, 0, out, "")

    monkeypatch.setattr(psycopg, "connect", lambda *a, **k: _Conn(db_now))
    monkeypatch.setattr(demo, "py", py)
    monkeypatch.setattr(demo, "drain", lambda name="drain": demo.drains.__setitem__(name, 0.0) or {})  # DD-1b2b O2: tested on its own (test_dd1b2b_drain.py)
    monkeypatch.setattr(tool.shutil, "which", lambda name: None)  # no git: the copy branch, stubbed below
    monkeypatch.setattr(tool.shutil, "copytree", lambda *a, **k: None)
    monkeypatch.setattr(tool.shutil, "copy2", lambda *a, **k: None)
    try:
        manifest = demo.prepare(days_file=str(sd.DEFAULT_FILE))
    finally:
        shutil.rmtree(demo.work, ignore_errors=True)
    assert manifest["sites"] == ["kobo", "cold", "ev"]
    objectives = [c for c in calls if c and str(c[0]).endswith("demo_declare_objectives.py")]
    assert len(objectives) == 3
