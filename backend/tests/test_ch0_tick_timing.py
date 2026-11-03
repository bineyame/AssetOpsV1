"""CH-0 U3 (pure, no database): the tick's one `assetops.perf` line per tick, with each Site stage's elapsed time,
its share of the stage bound read from `TickLimits`, and the stage child's peak memory; the stderr handler the
tick CLI installs so the line is actually emitted (QW-1/QW-2 review L1); and `_peak_rss_kb`.

The schedule store and the stage runner are recording fakes, as in `test_w402_mini_stage.py`.
"""

from __future__ import annotations

import io
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from assetops_backend import perf
from assetops_backend.scheduling import run as run_module
from assetops_backend.scheduling import stages as stages_module
from assetops_backend.scheduling import tick as tick_module
from assetops_backend.scheduling.tick import (
    PERF_HANDLER_NAME,
    STAGE_LIMIT_FIELDS,
    ScheduleTick,
    SiteResult,
    TickLimits,
    TickReport,
    enable_perf_log,
    tick_perf_line,
)

UTC = timezone.utc
T, S = UUID(int=1), UUID(int=2)
NOW = datetime(2026, 11, 3, tzinfo=UTC)
SITE_STAGES = ("s3", "cold_assess", "ev_assess", "mini", "opportunity", "s4", "consequence", "cold_consequence",
               "ev_consequence")


class FakeStore:
    def claim_tick(self, environment, token, owner, lease):
        return {"claimed": True, "db_now": NOW, "retry_due_at": None, "consecutive_failures": 0}

    def release_tick(self, *a):
        return True

    def fail_tick(self, *a):
        return True

    def site_heads(self):
        return []

    def cursor(self, environment):
        return None

    def set_cursor(self, *a):
        return True

    def finish_tick(self, *a, **k):
        return True

    def claim_site(self, t, s, token, owner, lease):
        return {"claimed": True, "matched_fence": None, "matched_version": None, "consecutive_failures": 0}

    def set_stage(self, *a):
        return True

    def record_s3(self, *a):
        return True

    record_mini = record_opportunity = record_consequence = record_s3

    def record_s4(self, *a, **k):
        return True

    def db_now(self):
        return NOW

    def release_site(self, *a, **k):
        return True


class FakeRunner:
    """Canned stage results; stage `n` of the visit took `100 * n` ms in its child and peaked at `1000 + n` kB."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, float]] = []

    def run(self, stage, args, seconds):
        self.calls.append((stage, seconds))
        if stage == "discover":
            return {"code": "OK", "reconcile_ms": 5, "live_jobs": [], "pending_work_sites": [],
                    "inventory": [{"tenant_id": str(T), "site_id": str(S), "site_code": "KOBO-001",
                                   "lifecycle": "ACTIVE", "has_evidence": True, "enrolled": True}]}
        n = len(self.calls)
        base = {"s4": {"code": "SKIPPED_UNCHANGED_FENCE"}}.get(stage) or {
            "code": "OK", "processed": 0, "deferred": 0, "failed": 0, "selected": 0}
        return {**base, "elapsed_ms": 100 * n, "peak_rss_kb": 1000 + n}


@pytest.fixture
def perf_stream():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))
    level = perf.LOG.level
    perf.LOG.addHandler(handler)
    perf.LOG.setLevel(logging.INFO)
    try:
        yield stream
    finally:
        perf.LOG.removeHandler(handler)
        perf.LOG.setLevel(level)


def _lines(stream: io.StringIO) -> list[dict]:
    return [json.loads(x) for x in stream.getvalue().splitlines() if x.strip()]


def test_one_perf_line_per_tick_with_share_of_the_stage_bound(perf_stream) -> None:
    limits = TickLimits(s3_seconds=100, consequence_seconds=50)
    runner = FakeRunner()
    report = ScheduleTick(FakeStore(), runner, limits, environment="test").tick()
    assert report.outcome == "COMPLETED"
    lines = _lines(perf_stream)
    assert len(lines) == 1
    line = lines[0]
    assert line["route"] == "tick" and line["outcome"] == "COMPLETED" and isinstance(line["total_ms"], float)
    [site] = line["sites"]
    assert site["site_code"] == "KOBO-001" and set(site["stages"]) == set(SITE_STAGES)
    bounds = {stage: seconds for stage, seconds in runner.calls if stage != "discover"}
    for name, entry in site["stages"].items():
        result = report.selected[0].stages[name]
        limit_ms = int(getattr(limits, STAGE_LIMIT_FIELDS[name]) * 1000)
        assert limit_ms == int(bounds[name] * 1000)  # the logged bound is the one the stage ran under
        assert entry == {"elapsed_ms": result["elapsed_ms"], "limit_ms": limit_ms,
                         "share": round(result["elapsed_ms"] / limit_ms, 3), "peak_rss_kb": result["peak_rss_kb"]}
    assert site["stages"]["s3"] == {"elapsed_ms": 200, "limit_ms": 100_000, "share": 0.002, "peak_rss_kb": 1002}
    # the report carries the child's peak memory too, beside the keys it already copied
    assert report.as_json()["sites"][0]["stages"]["s3"]["peak_rss_kb"] == 1002


def test_no_line_when_the_tick_selected_nothing(perf_stream) -> None:
    class Skipped(FakeStore):
        def claim_tick(self, *a):
            return {"claimed": False, "db_now": NOW, "retry_due_at": None, "consecutive_failures": 0}

    assert ScheduleTick(Skipped(), FakeRunner(), TickLimits()).tick().outcome == "SKIPPED_CLAIMED"
    assert _lines(perf_stream) == []


def test_a_failed_tick_after_selection_still_logs_once(perf_stream) -> None:
    class Broken(FakeStore):
        def finish_tick(self, *a, **k):
            raise RuntimeError("store down")

    report = ScheduleTick(Broken(), FakeRunner(), TickLimits()).tick()
    assert report.outcome == "FAILED" and report.failure["code"]
    [line] = _lines(perf_stream)
    assert line["outcome"] == "FAILED" and line["sites"][0]["result"] == report.selected[0].result


def test_an_unmapped_stage_or_missing_elapsed_gives_null() -> None:
    site = SiteResult(T, S, "X", "EVIDENCE", stages={"mystery": {"code": "OK", "elapsed_ms": 10},
                                                       "s3": {"code": "OK"}})
    line = tick_perf_line(TickReport("COMPLETED", "test", UUID(int=3), selected=[site]), TickLimits(), 1.0)
    stages = line["sites"][0]["stages"]
    assert stages["mystery"] == {"elapsed_ms": 10, "limit_ms": None, "share": None, "peak_rss_kb": None}
    assert stages["s3"] == {"elapsed_ms": None, "limit_ms": 120_000, "share": None, "peak_rss_kb": None}


def test_a_logging_failure_does_not_change_the_report(monkeypatch) -> None:
    clean = ScheduleTick(FakeStore(), FakeRunner(), TickLimits(), environment="test").tick().as_json()

    def boom(*a, **k):
        raise OSError("log disk full")

    monkeypatch.setattr(perf.LOG, "info", boom)
    broken = ScheduleTick(FakeStore(), FakeRunner(), TickLimits(), environment="test").tick().as_json()
    assert {**broken, "token": None} == {**clean, "token": None}

    monkeypatch.setattr(tick_module, "tick_perf_line", boom)
    assert ScheduleTick(FakeStore(), FakeRunner(), TickLimits(), environment="test").tick().outcome == "COMPLETED"


def test_the_tick_cli_emits_the_perf_line_on_stderr_and_keeps_stdout(monkeypatch, capsys) -> None:
    """QW review L1: with no logging configured, the CLI's own handler makes the INFO line reach stderr."""
    level = perf.LOG.level
    monkeypatch.setattr(run_module, "build_schedule_store", lambda *a, **k: FakeStore())
    monkeypatch.setattr(run_module, "StageRunner", lambda url, limits: FakeRunner())
    try:
        assert run_module.main(["tick", "--environment", "test"]) == 0
        out, err = capsys.readouterr()
        [report] = [json.loads(x) for x in out.splitlines() if x.strip()]
        assert report["outcome"] == "COMPLETED"  # stdout is still only the report
        [line] = [x for x in err.splitlines() if x.startswith("assetops.perf ")]
        assert json.loads(line[len("assetops.perf "):])["sites"][0]["site_code"] == "KOBO-001"
        assert sum(h.get_name() == PERF_HANDLER_NAME for h in perf.LOG.handlers) == 1
        assert enable_perf_log() in perf.LOG.handlers  # idempotent
        assert sum(h.get_name() == PERF_HANDLER_NAME for h in perf.LOG.handlers) == 1
    finally:
        for handler in [h for h in perf.LOG.handlers if h.get_name() == PERF_HANDLER_NAME]:
            perf.LOG.removeHandler(handler)
        perf.LOG.setLevel(level)


def test_perf_enable_log_is_idempotent_and_never_prints_a_line_twice() -> None:
    level, propagate = perf.LOG.level, perf.LOG.propagate
    stream, root_stream = io.StringIO(), io.StringIO()
    root_handler = logging.StreamHandler(root_stream)
    logging.getLogger().addHandler(root_handler)  # a configured root logger, as uvicorn/pytest would have
    try:
        first = perf.enable_log(stream)
        assert perf.enable_log(stream) is first and perf.enable_log() is first
        assert sum(h.get_name() == perf.HANDLER_NAME for h in perf.LOG.handlers) == 1
        assert perf.LOG.propagate is False and perf.LOG.level == logging.INFO
        perf.LOG.info('{"a": 1}')
        assert stream.getvalue() == 'assetops.perf {"a": 1}\n'  # exactly once
        assert root_stream.getvalue() == ""  # and not again through the root logger
        assert enable_perf_log(stream) is first  # the tick's helper reuses it
    finally:
        logging.getLogger().removeHandler(root_handler)
        for handler in [h for h in perf.LOG.handlers if h.get_name() == perf.HANDLER_NAME]:
            perf.LOG.removeHandler(handler)
        perf.LOG.setLevel(level)
        perf.LOG.propagate = propagate


def test_lab_app_enables_the_perf_log_once_at_start() -> None:
    source = (Path(__file__).resolve().parents[2] / "host" / "lab_app.py").read_text(encoding="utf-8")
    assert source.count("perf.enable_log()") == 1


def test_peak_rss_kb_is_an_int_or_none_and_never_raises(monkeypatch) -> None:
    peak = stages_module._peak_rss_kb()
    assert isinstance(peak, int) and peak > 0  # a real reading on this platform
    import ctypes

    monkeypatch.setattr(ctypes, "WinDLL", lambda *a, **k: (_ for _ in ()).throw(OSError("no dll")), raising=False)
    monkeypatch.setitem(__import__("sys").modules, "resource", None)  # `import resource` then raises
    assert stages_module._peak_rss_kb() is None


def test_the_stage_child_adds_peak_rss_and_changes_no_other_key(monkeypatch, capsys) -> None:
    monkeypatch.setitem(stages_module.STAGES, "probe", lambda url, args: {"code": "OK", "processed": 2})
    assert stages_module.main(["probe", "{}"]) == 0
    [line] = [x for x in capsys.readouterr().out.splitlines() if x.startswith("STAGE_RESULT ")]
    result = json.loads(line[len("STAGE_RESULT "):])
    assert set(result) == {"code", "processed", "peak_rss_kb"}
    assert (result["code"], result["processed"]) == ("OK", 2) and isinstance(result["peak_rss_kb"], int)
