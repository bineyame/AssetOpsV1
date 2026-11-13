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
        manifest = demo.prepare(tool.CORE_SITES, days_file=str(sd.DEFAULT_FILE))  # K7-F: the default is four Sites
    finally:
        shutil.rmtree(demo.work, ignore_errors=True)
    assert manifest["sites"] == ["kobo", "cold", "ev"]
    objectives = [c for c in calls if c and str(c[0]).endswith("demo_declare_objectives.py")]
    assert len(objectives) == 3


def _evidence_demo(monkeypatch, tmp_path, codes_exit=None):
    demo = tool.Demo("assetops_polish_dsr67_test", "var/polish_dsr67")
    calls: list[tuple] = []

    def py(*argv, **kw):
        calls.append(argv)
        site = argv[argv.index("--site") + 1] if "--site" in argv else ""
        return subprocess.CompletedProcess(argv, (codes_exit or {}).get(site, 0), "", "")

    monkeypatch.setattr(demo, "py", py)
    monkeypatch.setattr(demo, "work", tmp_path)
    return demo, calls


def test_d_sr67_evidence_comparison_runs_for_every_story_site(monkeypatch, tmp_path) -> None:
    demo, calls = _evidence_demo(monkeypatch, tmp_path)
    demo.evidence_comparisons({"sites": ["kobo", "kisiwa", "ev", "cold"]})
    sites = [c[c.index("--site") + 1] for c in calls if "evidence_migration" in " ".join(c)]
    assert sites == ["KOBO-001", "KISIWA-001", "EV-LAB-001", "COLD-LAB-001"]


def test_d_sr67_exit_2_stops_the_prepare(monkeypatch, tmp_path) -> None:
    import pytest

    demo, calls = _evidence_demo(monkeypatch, tmp_path, {"KISIWA-001": 2})
    with pytest.raises(SystemExit) as exc:
        demo.evidence_comparisons({"sites": ["kobo", "kisiwa", "ev"]})
    assert "KISIWA-001" in str(exc.value) and "exit 2" in str(exc.value)
    assert len(calls) == 2  # EV never ran


def test_d_sr67_finish_runs_the_comparison_before_the_ticks(monkeypatch, tmp_path) -> None:
    demo, calls = _evidence_demo(monkeypatch, tmp_path)
    order: list[str] = []
    monkeypatch.setattr(demo, "evidence_comparisons", lambda story: order.append("evidence"))
    monkeypatch.setattr(demo, "drain_mini", lambda: order.append("mini"))
    monkeypatch.setattr(demo, "tick", lambda times=1: order.append("tick") or {})
    demo.finish({"sites": ["kobo", "ev"], "days": []})
    assert order[0] == "evidence" and order.index("tick") > order.index("evidence")


def test_d_sr67_serve_reruns_the_comparison_in_another_tree(monkeypatch, tmp_path) -> None:
    import pytest

    demo, calls = _evidence_demo(monkeypatch, tmp_path)
    (tmp_path / "story.json").write_text('{"sites": ["kobo"]}', encoding="utf-8")
    (tmp_path / demo.EVIDENCE_TREE_MARK).write_text("/some/other/tree", encoding="utf-8")
    monkeypatch.setattr(demo, "write_prebuilt_routes", lambda: (_ for _ in ()).throw(RuntimeError("past")))
    with pytest.raises(RuntimeError):
        demo.serve(1, 2)
    assert any("evidence_migration" in " ".join(c) for c in calls)
    calls.clear()
    (tmp_path / demo.EVIDENCE_TREE_MARK).write_text(str(demo.tree), encoding="utf-8")
    with pytest.raises(RuntimeError):
        demo.serve(1, 2)
    assert not calls
