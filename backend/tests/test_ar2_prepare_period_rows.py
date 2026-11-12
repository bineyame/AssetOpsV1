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
    assert [a for a, _ in calls] == [("-m", "assetops_backend.chain.period_backfill", "build", "--site", c, "--quiet")
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
        < body.index("self-check")


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
