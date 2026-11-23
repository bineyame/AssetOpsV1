"""DD4b run 5 (the packet's "Risk for DD6's world build"): the writer holds one day at a time.

`build_telemetry(..., sink=...)` hands each day file to the sink as it is made (the CLI writes and drops it); a vertical
run's day rows are released once the frame has written them; `EvSiteRun` keeps the charger draw of the current day
only. The bytes do not move: the sink receives exactly the files the collecting call returns."""

from __future__ import annotations

from datetime import date

import pytest

from assetops_simulator.world import telemetry as tel
from assetops_simulator.world.telemetry import TelemetryRefused
from assetops_simulator.world.telemetry_ev import EvSiteRun

from .test_dd4_ev_join import _decided, _sites
from .test_dd4_telemetry_ev import books, f_site, local


def _kas(**kw):
    return tel.build_telemetry({}, _sites(), {"EV-KAS": _decided("EV-KAS")}, start="2026-11-01", end="2026-11-02",
                               only=("EV-KAS",), **kw)


def test_w1_the_sink_gets_each_day_file_before_the_next_day_is_made(monkeypatch) -> None:
    log: list[str] = []
    advance = EvSiteRun.advance_day

    def logged(self):
        day = advance(self)
        log.append(f"advance {day.isoformat()}")
        return day

    monkeypatch.setattr(EvSiteRun, "advance_day", logged)
    got: list[tuple[str, bytes]] = []

    def sink(name: str, data: bytes) -> None:
        log.append(f"write {name.rsplit('/', 1)[1]}")
        got.append((name, data))

    streamed = _kas(sink=sink)
    assert log == ["advance 2026-11-01", "write EV-KAS.2026-11-01.readings.json",
                   "advance 2026-11-02", "write EV-KAS.2026-11-02.readings.json", "write measured.json"]
    assert streamed.files == ()  # nothing held: every file went to the sink
    collected = _kas()
    assert got == list(collected.files)  # byte parity with the collecting call, same order
    assert streamed.manifests == collected.manifests


def test_w2_the_frame_releases_a_vertical_days_rows_once_written(monkeypatch) -> None:
    released: list[date] = []
    release = EvSiteRun.release_day

    def logged(self, day):
        release(self, day)
        released.append(day)
        with pytest.raises(TelemetryRefused):
            self.day_records(day)

    monkeypatch.setattr(EvSiteRun, "release_day", logged)
    _kas(sink=lambda name, data: None)
    assert released == [date(2026, 11, 1), date(2026, 11, 2)]


def test_w3_the_ev_run_keeps_the_current_days_charger_draw_only() -> None:
    r = EvSiteRun(f_site("EV-KAS"), books("EV-KAS"), "2026-10-14", "2026-10-15")
    r.advance_day()
    first = r.charger_draw()
    assert first and all(local("2026-10-14T00:00:00") <= t < local("2026-10-15T00:00:00") for _, t in first)
    r.advance_day()
    second = r.charger_draw()
    assert second and all(local("2026-10-15T00:00:00") <= t < local("2026-10-16T00:00:00") for _, t in second)
