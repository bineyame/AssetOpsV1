"""E4 D-E4.8 (C4): the Performance comparison runs only when a Site's DB watermark changed or no report exists.
No database: a fake `py` and a fake mark reader stand in for the children and the read."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import demo_combined as tool  # noqa: E402


def _demo(tmp_path: Path, marks: dict, returncode: int = 0, with_report: bool = True):
    d = tool.Demo.__new__(tool.Demo)
    d.work, d.tree = tmp_path / "work", tmp_path / "work" / "tree"
    d.work.mkdir(parents=True)
    if with_report:
        report = d.tree / "var" / "evidence" / "migration-performance" / "kobo-001"
        report.mkdir(parents=True)
        (report / "r.json").write_text("{}", encoding="utf-8")
    d.calls = []
    d.marks = marks

    def py(*argv, label="", **_):
        d.calls.append(label)
        return subprocess.CompletedProcess([], returncode if label == "performance" else 0, stdout="ok\n")

    d.py = py
    d.read_site_mark = lambda site: d.marks[site]
    d.story = lambda: {"sites": ["kobo"]}
    d.write_prebuilt_routes = lambda: None
    return d


def test_due_with_no_report_no_mark_or_changed_mark_and_not_on_equal(tmp_path) -> None:
    rep = tmp_path / "rep"
    assert tool.performance_due("KOBO-001", "cic:5", {"KOBO-001": "cic:5"}, rep)  # no report dir
    rep.mkdir()
    assert tool.performance_due("KOBO-001", "cic:5", {"KOBO-001": "cic:5"}, rep)  # dir without a report file
    (rep / "a.json").write_text("{}", encoding="utf-8")
    assert tool.performance_due("KOBO-001", "cic:5", {}, rep)  # no mark
    assert tool.performance_due("KOBO-001", "cic:6", {"KOBO-001": "cic:5"}, rep)  # changed
    assert not tool.performance_due("KOBO-001", "cic:5", {"KOBO-001": "cic:5"}, rep)  # equal, report present


def test_unchanged_mark_runs_performance_once_and_prebuild_twice(tmp_path) -> None:
    d = _demo(tmp_path, {"KOBO-001": "cic:7"})
    d.performance_and_prebuild()
    d.performance_and_prebuild()
    assert d.calls.count("performance") == 1 and d.calls.count("prebuild") == 2
    assert json.loads((d.work / tool.PERFORMANCE_MARKS_FILE).read_text()) == {"KOBO-001": "cic:7"}


def test_changed_mark_between_calls_runs_performance_twice(tmp_path) -> None:
    d = _demo(tmp_path, {"KOBO-001": "cic:7"})
    d.performance_and_prebuild()
    d.marks["KOBO-001"] = "cic:8"
    d.performance_and_prebuild()
    assert d.calls.count("performance") == 2
    assert tool.read_marks(d.work / tool.PERFORMANCE_MARKS_FILE) == {"KOBO-001": "cic:8"}


def test_missing_report_runs_performance_despite_equal_mark(tmp_path) -> None:
    d = _demo(tmp_path, {"KOBO-001": "cic:7"}, with_report=False)
    tool.write_marks(d.work / tool.PERFORMANCE_MARKS_FILE, {"KOBO-001": "cic:7"})
    d.performance_and_prebuild()
    assert d.calls.count("performance") == 1


def test_failed_run_records_no_mark(tmp_path) -> None:
    d = _demo(tmp_path, {"KOBO-001": "cic:7"}, returncode=1)
    d.performance_and_prebuild()
    assert d.calls.count("performance") == 1
    assert not (d.work / tool.PERFORMANCE_MARKS_FILE).exists()
    d.performance_and_prebuild()  # still due: it runs again
    assert d.calls.count("performance") == 2


def test_marks_are_written_atomically(tmp_path, monkeypatch) -> None:
    path = tmp_path / "performance-marks.json"
    replaced = []
    real = tool.os.replace

    def spy(src, dst):
        assert Path(src).parent == path.parent and Path(src).read_text(encoding="utf-8")  # complete temp, same folder
        replaced.append((Path(src), Path(dst)))
        real(src, dst)

    monkeypatch.setattr(tool.os, "replace", spy)
    tool.write_marks(path, {"KOBO-001": "cic:1"})
    assert replaced and replaced[0][1] == path and not replaced[0][0].exists()
    assert tool.read_marks(path) == {"KOBO-001": "cic:1"}


def test_an_unreadable_mark_is_due_and_raises_nothing(tmp_path, monkeypatch) -> None:
    import psycopg

    def refuse(*a, **kw):
        raise psycopg.OperationalError("connection refused")

    monkeypatch.setattr(psycopg, "connect", refuse)
    d = _demo(tmp_path, {})
    d.url = "postgresql+psycopg://x:y@127.0.0.1:1/none_test"
    mark = tool.Demo.read_site_mark(d, "KOBO-001")
    assert mark is None
    assert tool.performance_due("KOBO-001", mark, {"KOBO-001": "cic:7"}, d.tree / "var" / "evidence" /
                                "migration-performance" / "kobo-001")
