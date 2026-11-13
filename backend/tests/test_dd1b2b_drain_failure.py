"""DD1b2-R8 C1/C2 L0 (no database): a drain failure never ends the prepare, a non-zero tick is recorded per Site, and
`manifest.json` is written whatever happens. The real `Demo.drain` and `Demo.build_and_record` run; only the children
(`py`, `counts`) are replaced."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import demo_combined as dc  # noqa: E402

ZERO = {"dirty": 0, "snapshots_pending": 0, "threads_pending": 0, "mini_deferred": 0, "opportunity_live": 0,
        "pending_ids": []}
BUSY = {**ZERO, "opportunity_live": 2}
TICK_FAIL = json.dumps({"outcome": "COMPLETED", "failure": None, "sites": [
    {"site_code": "KOBO-001", "result": "FAILED", "failure": ["MINI", "TIMEOUT", "stage mini exceeded 120 s"]},
    {"site_code": "EV-LAB-001", "result": "COMPLETED", "failure": None}]})


class Fake(dc.Demo):
    def __init__(self, work: Path, counts: list, tick_rc: int = 0, tick_out: str = "{}") -> None:  # noqa: D107
        self.work, self.tree, self.drains = work, work, {}
        self._counts, self.tick_rc, self.tick_out, self.ticks, self.prebuilds = list(counts), tick_rc, tick_out, 0, 0

    def counts(self) -> dict:
        item = self._counts.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    def performance_and_prebuild(self) -> None:
        self.prebuilds += 1

    def py(self, *argv, **kw):
        self.ticks += 1
        return subprocess.CompletedProcess(argv, self.tick_rc, self.tick_out, "")


def test_a_non_zero_tick_is_recorded_per_site_and_does_not_stop_the_drain(tmp_path) -> None:
    demo = Fake(tmp_path, [{"K": BUSY}, {"K": BUSY}, {"K": ZERO}], tick_rc=1, tick_out=TICK_FAIL)
    demo.defer_drain = True
    record = demo.drain("drain-1")
    assert record["verdict"] == "done" and record["ticks"] == 2 and demo.drain_failures == ()
    first = record["log"][0]
    assert first["tick_rc"] == 1
    assert first["tick_failure"]["sites"] == {"KOBO-001": ["MINI", "TIMEOUT", "stage mini exceeded 120 s"]}
    assert json.loads((tmp_path / "drain-1.json").read_text())["log"][0]["tick_rc"] == 1


def test_an_unparsable_tick_keeps_its_last_line(tmp_path) -> None:
    demo = Fake(tmp_path, [{"K": BUSY}, {"K": ZERO}], tick_rc=1, tick_out="Traceback\nboom")
    record = demo.drain("x")
    assert record["log"][0]["tick_failure"] == {"unparsed": "boom"}


@pytest.mark.parametrize("crash", [SystemExit("FAILED: drain-counts (exit 1); log x"), IndexError("list index")])
def test_a_counts_crash_writes_a_fail_record_and_the_deferred_drain_goes_on(tmp_path, crash) -> None:
    demo = Fake(tmp_path, [{"K": BUSY}, crash])
    demo.defer_drain = True
    record = demo.drain("drain-1")  # returns: the prepare would continue
    assert record["verdict"] == "fail" and "counts" in record["reason"]
    assert json.loads((tmp_path / "drain-1.json").read_text())["verdict"] == "fail"
    assert demo.drain_failures and demo.prebuilds == 1
    with pytest.raises(SystemExit) as stop:  # ... and the prepare ends non-zero only after its self-check
        demo.raise_deferred_drain()
    assert "DRAIN FAILED (deferred)" in str(stop.value) and demo.step == "drain (deferred)"


def test_a_flat_drain_is_deferred_inside_prepare_and_raises_outside_it(tmp_path) -> None:
    flat = [{"K": BUSY}] * 6
    deferred = Fake(tmp_path, flat)
    deferred.defer_drain = True
    assert deferred.drain("drain-2")["verdict"] == "fail" and deferred.drain_failures
    direct = Fake(tmp_path, flat)  # `tick --until-drained`: exit 1 stays
    with pytest.raises(SystemExit) as stop:
        direct.drain("tick-until-drained")
    assert "DRAIN FAILED" in str(stop.value) and "flat" in str(stop.value)
    assert json.loads((tmp_path / "tick-until-drained.json").read_text())["verdict"] == "fail"


def test_the_wall_cap_is_not_absorbed_by_the_drain(tmp_path) -> None:
    demo = Fake(tmp_path, [{"K": BUSY}, SystemExit("WALL CAP reached during drain-counts")])
    demo.defer_drain = True
    with pytest.raises(SystemExit):
        demo.drain("drain-1")


class DegradedFake(Fake):
    def performance_and_prebuild(self) -> None:
        self.prebuilds += 1
        raise dc.PrebuildRefused("prebuild DEGRADED: /api/x")


def test_a_degraded_prebuild_in_the_drain_is_deferred_and_the_prepare_ends_non_zero_after_the_self_check(tmp_path) -> None:
    demo = DegradedFake(tmp_path, [{"K": ZERO}, {"K": ZERO}])
    demo.defer_drain = True
    record = demo.drain("drain-1")  # returns: the prepare goes on to drain_failures and the self-check
    assert record["verdict"] == "done" and demo.drain_failures and "DEGRADED" in demo.drain_failures[0]
    with pytest.raises(SystemExit) as stop:
        demo.raise_deferred_drain()
    assert "DRAIN FAILED (deferred)" in str(stop.value) and "DEGRADED" in str(stop.value)
    direct = DegradedFake(tmp_path, [{"K": ZERO}, {"K": ZERO}])  # `tick --until-drained`: raises at the end
    with pytest.raises(SystemExit) as stop:
        direct.drain("tick-until-drained")
    assert "DRAIN FAILED" in str(stop.value) and "DEGRADED" in str(stop.value)


def test_a_degraded_prebuild_tick_does_not_stop_the_serve_loop(tmp_path, monkeypatch) -> None:
    import urllib.request

    state = {"ticked": False, "killed": False}
    api = type("Api", (), {"pid": 1, "poll": lambda self: 0 if state["ticked"] else None})()
    monkeypatch.setattr(dc.subprocess, "Popen", lambda *a, **k: api)
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: type("R", (), {"read": lambda s: b"ok"})())
    monkeypatch.setattr(dc, "_kill_tree", lambda pid: state.update(killed=True))
    monkeypatch.setattr(dc, "prewarm", lambda *a: None)
    monkeypatch.setattr(dc.time, "sleep", lambda s: None)
    demo = object.__new__(dc.Demo)
    demo.work = demo.tree = tmp_path
    demo.story = lambda: {}
    demo.write_prebuilt_routes = lambda: None
    demo.evidence_comparisons = lambda story: None  # D-SR.67: serve reruns it when the tree mark is missing
    demo.serve_env = lambda: {}
    demo.links = lambda web: None

    def tick(times=1):
        state["ticked"] = True
        raise dc.PrebuildRefused("prebuild DEGRADED: /api/x")

    demo.tick = tick
    demo.serve(8000, 5000)  # returns normally: the refusal is logged, not raised
    assert state["ticked"] and not state["killed"]


STORY = {"S": "2026-11-07", "code": "abc", "sites": ["kobo"], "installs": {"kobo": "x"}}


def _prepare_like(tmp_path, finish_build):
    demo = Fake(tmp_path, [])
    demo.db, demo.url = "assetops_demo3_x_test", "postgresql+psycopg://x"
    demo.finish_build = finish_build
    demo.py = lambda *a, **k: subprocess.CompletedProcess(a, 0, "built\n", "")
    return demo


def test_the_manifest_is_written_on_failure_with_failed_at_and_on_success_without(tmp_path) -> None:
    def boom(story, days, finish, timings, steps):
        timings["kobo-extra"] = 1.0
        raise SystemExit("SELF-CHECK FAILED")

    demo = _prepare_like(tmp_path, boom)
    demo.step = "self-check"
    with pytest.raises(SystemExit):
        demo.build_and_record(dict(STORY), [], True, 99, 0.0, 1.0)
    m = json.loads((tmp_path / "manifest.json").read_text())
    assert m["failed_at"] == "self-check" and "SELF-CHECK FAILED" in m["error"] and "kobo" in m["timings_seconds"]

    ok = _prepare_like(tmp_path / "ok", lambda *a: None)
    (tmp_path / "ok").mkdir()
    out = ok.build_and_record(dict(STORY), [], True, 99, 0.0, 1.0)
    assert out["failed_at"] is None and out["error"] is None
    assert json.loads((tmp_path / "ok" / "manifest.json").read_text())["failed_at"] is None
