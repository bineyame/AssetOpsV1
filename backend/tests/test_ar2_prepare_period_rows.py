"""ANY-1 AR-2 (D-ANY.6): the prepare builds the board's stored mini depth rows after the last drain, times itself
and is capped at 15 minutes; over the cap or on a failure it says so (kill switch) and the prepare goes on."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import demo_combined as dc  # noqa: E402


def _demo(tmp_path: Path, py):
    demo = dc.Demo.__new__(dc.Demo)
    demo.work, demo.deadline, demo.said = tmp_path, None, []
    demo.py = py
    return demo


def test_builds_each_mini_site_quietly_and_times_itself(tmp_path, monkeypatch) -> None:
    said: list[str] = []
    monkeypatch.setattr(dc, "say", said.append)
    calls, deadlines = [], []

    def py(*argv, **kw):
        calls.append((argv, kw.get("label")))
        deadlines.append(demo.deadline)
        return subprocess.CompletedProcess(argv, 0, '{"written": 4, "seconds": 1.0}\n', "")

    demo = _demo(tmp_path, py)
    steps: dict[str, float] = {}
    assert demo.build_period_rows({"sites": ["kobo", "cold", "ev", "kisiwa"]}, steps) is True
    assert [a for a, _ in calls] == [("-m", "assetops_backend.chain.period_backfill", "build", "--site", c, "--quiet",
                                      *(a for k in dc.Demo.BOARD_KINDS for a in ("--kind", k)))
                                     for c in ("KOBO-001", "KISIWA-001")]
    assert all(d is not None and d <= time.monotonic() + dc.Demo.PERIOD_ROWS_CAP_SECONDS for d in deadlines)
    assert demo.deadline is None  # the prepare's own deadline is restored
    assert {"period-rows KOBO-001", "period-rows KISIWA-001", "period-rows"} <= set(steps)
    assert json.loads((tmp_path / "period-rows.json").read_text())["ok"] is True
    assert not any("NOT COMPLETE" in s for s in said)


def test_cap_or_failure_is_reported_and_the_prepare_goes_on(tmp_path, monkeypatch) -> None:
    said: list[str] = []
    monkeypatch.setattr(dc, "say", said.append)

    def capped(*argv, **kw):
        raise SystemExit("WALL CAP reached during period-rows KOBO-001")

    demo = _demo(tmp_path, capped)
    demo.deadline = time.monotonic() + 3600
    saved = demo.deadline
    assert demo.build_period_rows({"sites": ["kobo"]}, {}) is False
    assert demo.deadline == saved
    assert any("ROW BUILD INCOMPLETE" in s and "ASSETOPS_PERIOD_READ_KINDS=" in s for s in said)
    assert json.loads((tmp_path / "period-rows.json").read_text())["ok"] is False

    def failing(*argv, **kw):
        return subprocess.CompletedProcess(argv, 1, "boom\n", "")

    said.clear()
    assert _demo(tmp_path, failing).build_period_rows({"sites": ["kisiwa"]}, {}) is False
    assert any("ROW BUILD FAILED for KISIWA-001" in s for s in said)


def test_finish_calls_the_row_build_after_drain_2() -> None:
    src = (ROOT / "tools" / "demo_combined.py").read_text(encoding="utf-8")
    body = src[src.index("    def finish(self"):src.index("    #: ANY-1 AR-2 (D-ANY.6)")]
    assert body.index('self.drain("drain-2")') < body.index("self.build_period_rows(story, steps)") \
        < body.index("self.build_day_rows(story, steps)") < body.index("self-check")


def test_day_kinds_build_in_their_own_step_with_a_30_minute_cap(tmp_path, monkeypatch) -> None:
    """D-SR.54: board kinds are explicit (no day kinds); the day step has its own cap and records seconds per hour."""
    monkeypatch.setattr(dc, "say", lambda *_: None)
    assert not set(dc.Demo.BOARD_KINDS) & set(dc.Demo.DAY_KINDS) and dc.Demo.DAY_ROWS_CAP_SECONDS == 1800
    calls, deadlines = [], []

    def py(*argv, **kw):
        calls.append(argv)
        deadlines.append(demo.deadline)
        return subprocess.CompletedProcess(argv, 0, '{"considered": 8, "written": 8, "seconds": 1.0}\n', "")

    demo = _demo(tmp_path, py)
    steps: dict[str, float] = {}
    assert demo.build_day_rows({"sites": ["kobo", "kisiwa"]}, steps) is True
    assert [a[-4:] for a in calls] == [("--kind", "mini_depth.fuel_day", "--kind", "mini_depth.backup_day")] * 2
    assert all(d is not None and d <= time.monotonic() + 1800 for d in deadlines) and demo.deadline is None
    doc = json.loads((tmp_path / "day-rows.json").read_text())
    assert doc["ok"] is True and doc["per_site"]["KOBO-001"]["hour_reads"] == 192 and "day-rows" in steps


def test_day_rows_failure_prints_the_rerun_command_and_goes_on(tmp_path, monkeypatch) -> None:
    said: list[str] = []
    monkeypatch.setattr(dc, "say", said.append)
    demo = _demo(tmp_path, lambda *a, **k: subprocess.CompletedProcess(a, 1, "boom\n", ""))
    assert demo.build_day_rows({"sites": ["kobo"]}, {}) is False
    assert any("rerun `period_backfill build --kind mini_depth.fuel_day --kind mini_depth.backup_day`" in s
               for s in said)

    def capped(*argv, **kw):
        raise SystemExit("WALL CAP reached during day-rows KOBO-001")

    said.clear()
    assert _demo(tmp_path, capped).build_day_rows({"sites": ["kobo"]}, {}) is False
    assert any("DAY ROW BUILD INCOMPLETE" in s and "rerun" in s for s in said)


def _serve_demo(tmp_path: Path, ok, versions=None):
    demo = dc.Demo.__new__(dc.Demo)
    demo.work = tmp_path
    demo.env = lambda keys=False: {}
    if ok is not None:
        doc = {"ok": ok}
        if versions is not False:
            doc["builder_versions"] = dc.row_builder_versions() if versions is None else versions
        (tmp_path / "period-rows.json").write_text(json.dumps(doc))
    return demo


def test_serve_env_sets_the_six_kinds_only_when_the_rows_are_ok(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("ASSETOPS_PERIOD_READ_KINDS", raising=False)
    got = _serve_demo(tmp_path, True).serve_env()["ASSETOPS_PERIOD_READ_KINDS"]
    assert got.split(",") == ["dispatch.day", "evidence.claim", "mini_depth.renewable", "mini_depth.fuel",
                              "mini_depth.service", "mini_depth.backup"]
    assert "fuel_day" not in got and "backup_day" not in got  # D-SR.52: day kinds are not gated by this list


def test_serve_env_leaves_the_kinds_off_when_failed_or_no_file(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("ASSETOPS_PERIOD_READ_KINDS", raising=False)
    assert _serve_demo(tmp_path, False).serve_env()["ASSETOPS_PERIOD_READ_KINDS"] == ""
    assert _serve_demo(tmp_path / "none", None).serve_env()["ASSETOPS_PERIOD_READ_KINDS"] == ""


def test_serve_env_operator_value_wins_including_empty(tmp_path, monkeypatch) -> None:
    demo = _serve_demo(tmp_path, True)
    monkeypatch.setenv("ASSETOPS_PERIOD_READ_KINDS", "dispatch.day")
    assert demo.serve_env()["ASSETOPS_PERIOD_READ_KINDS"] == "dispatch.day"
    monkeypatch.setenv("ASSETOPS_PERIOD_READ_KINDS", "")
    assert demo.serve_env()["ASSETOPS_PERIOD_READ_KINDS"] == ""


def test_serve_env_mini_kinds_off_when_rows_built_by_an_old_version(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.delenv("ASSETOPS_PERIOD_READ_KINDS", raising=False)
    running = dc.row_builder_versions()
    old = dict(running, mini_depth="mini-depth-rows-0")
    got = _serve_demo(tmp_path, True, old).serve_env()["ASSETOPS_PERIOD_READ_KINDS"].split(",")
    assert got == ["dispatch.day", "evidence.claim"]
    assert f"rebuild mini_depth rows: built by mini-depth-rows-0, code is {running['mini_depth']}" in capsys.readouterr().out


def test_serve_env_kinds_off_when_the_version_field_is_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("ASSETOPS_PERIOD_READ_KINDS", raising=False)
    got = _serve_demo(tmp_path, True, False).serve_env()["ASSETOPS_PERIOD_READ_KINDS"]
    assert not any(k.startswith("mini_depth.") for k in got.split(","))
