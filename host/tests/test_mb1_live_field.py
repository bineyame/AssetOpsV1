"""MB-1 no-DB tests: the live-field switch, window, overlap rule, child commands, readings and stop (D-17N.6)."""

from __future__ import annotations

import json
import signal
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for part in ("tools", "backend/tests", "field/tests", "gateway/tests"):
    sys.path.insert(0, str(ROOT / part))

import demo_live_field as lf  # noqa: E402
import demo_upload_gateway as ug  # noqa: E402
import field_bench  # noqa: E402
import field_observation_fixtures as fixtures  # noqa: E402

from assetops_field.profile import load_profile  # noqa: E402

NOW = datetime(2026, 11, 17, 9, 7, 31, tzinfo=timezone.utc)


def test_the_switch_is_off_by_default_and_names_sites() -> None:
    assert not lf.live_switched_on({})
    assert not lf.live_switched_on({lf.SWITCH_ENV: " , "})
    assert lf.switched_sites({lf.SWITCH_ENV: "KOBO-001, COLD-LAB-001"}) == {"KOBO-001", "COLD-LAB-001"}


@pytest.mark.parametrize("environ, site, message", [
    ({}, "KOBO-001", "live Modbus is off"),
    ({lf.SWITCH_ENV: "COLD-LAB-001"}, "KOBO-001", "live Modbus is off"),
    ({lf.SWITCH_ENV: "KOBO-001"}, "COLD-LAB-001", "built for KOBO-001 only"),
    ({lf.SWITCH_ENV: "KOBO-001"}, "KOBO-001", "is missing"),  # no edge gateway file: serve is not running
])
def test_start_refuses_before_touching_anything(tmp_path: Path, environ, site, message) -> None:
    with pytest.raises(lf.LiveFieldRefused, match=message):
        lf.start(tmp_path, site, None, 2, environ=environ, now=lambda: NOW)
    assert not (tmp_path / "live-field").exists()


def test_the_window_floors_to_five_minutes_and_is_one_run_at_most() -> None:
    assert lf.live_window(None, 2, NOW) == (datetime(2026, 11, 17, 9, 5, tzinfo=timezone.utc),
                                           datetime(2026, 11, 17, 11, 5, tzinfo=timezone.utc))
    assert lf.live_window("2026-11-17T10:12:00Z", 8, NOW)[0] == datetime(2026, 11, 17, 10, 10, tzinfo=timezone.utc)
    for hours in (0, 9):
        with pytest.raises(lf.LiveFieldRefused, match="--hours"):
            lf.live_window(None, hours, NOW)
    with pytest.raises(lf.LiveFieldRefused, match="already over"):
        lf.live_window("2026-11-16T00:00:00Z", 8, NOW)
    with pytest.raises(lf.LiveFieldRefused, match="not a UTC instant"):
        lf.live_window("2026-11-17 10:00", 1, NOW)


def test_the_overlap_rule_refuses_signals_recorded_after_the_start() -> None:
    start = datetime(2026, 11, 17, 9, 0, tzinfo=timezone.utc)
    latest = {"mill-meter/active-power": start, "clinic-meter/active-power": start + timedelta(minutes=5),
              "pv-inverter-controller/ac-power": start - timedelta(hours=1)}
    assert lf.overlap_refusal(latest, start) == ["clinic-meter/active-power"]  # an interval ending at start is fine
    assert lf.overlap_refusal({}, start) == []


def test_child_commands_replay_at_real_time_and_poll_on_the_wall_clock(tmp_path: Path) -> None:
    start, end = lf.live_window(None, 3, NOW)
    emulator = lf.emulator_argv("py", tmp_path / "o.jsonl", start, end)
    value = dict(zip(emulator[2::2], emulator[3::2]))
    assert value["--replay-rate"] == "1" and value["--replay-start"] == value["--replay-wall-epoch"] == lf.zulu(start)
    assert value["--port"] == "5020" and value["--host"] == "127.0.0.1"
    gateway = {"gateway_address": "/w/gw.sock", "ipc_credential": "/w/gateway.credential", "snapshot_sha256": "a" * 64}
    poller = lf.poller_argv("py", gateway, tmp_path / "e.json", tmp_path / "p", end)
    assert poller[1:3] == ["-m", "assetops_field.modbus_poller"] and "--replay-start" not in poller
    assert poller[poller.index("--stop-at") + 1] == lf.zulu(end)
    assert poller[poller.index("--profile") + 1].endswith("gx-system-illustrative-2.json")
    env = lf.child_env(ROOT, {"X": "1"})
    assert env["X"] == "1" and env["PYTHONPATH"].split(":")[-1].endswith("field/tests")


@pytest.fixture(scope="module")
def prolonged_basis():
    import test_s6_verification_publication as s6

    store, result, _ = fixtures.registered.converted()
    s6.configure(store, result)
    run, _ = s6.draft(store)
    return run.registered_basis


def test_profile_2_binds_every_row_on_the_edge_epoch(tmp_path: Path, prolonged_basis) -> None:
    state = tmp_path / "gateways" / "kobo-edge"
    state.mkdir(parents=True)
    (state / ug.EPOCH_FILE).write_text("kobo-edge-0123456789ab", encoding="utf-8")
    ug.write_json(state / ug.BASIS_FILE, {"snapshot_text": prolonged_basis.snapshot_canonical, "claimed": {}})
    expect = lf.profile_expect(state)
    assert expect["sequence_epoch"] == "kobo-edge-0123456789ab"
    rows = json.loads(lf.PROFILE.read_text(encoding="utf-8"))["rows"]
    assert len(expect["row_sources"]) == len(rows) == 9
    assert len(field_bench.cohort_members(expect)) == len(set(expect["row_sources"].values()))  # a source per device


def test_the_live_window_readings_cover_every_profile_row(tmp_path: Path) -> None:
    from field_emulators.gx_server import ObservationTimeline

    manifest = fixtures.generate_live_window(tmp_path, "2026-11-17T09:05:00Z", "2026-11-17T17:05:00Z")
    assert manifest["window"] == {"start": "2026-11-17T09:05:00Z", "end": "2026-11-17T17:05:00Z"}
    documents = [json.loads(line) for line in (tmp_path / "observations.jsonl").read_text().splitlines()]
    assert {d["source_sample_time"] for d in documents} >= {"2026-11-17T09:05:00Z", "2026-11-17T17:05:00Z"}
    profile = load_profile(lf.PROFILE)
    timeline = ObservationTimeline(tmp_path / "observations.jsonl", profile)
    for row in profile.rows:
        assert [d for d in documents if (d["device_id"], d["signal_id"]) == (row.device_id, row.signal_id)
                and d["outcome"] == "REPORTED"], row.row_id
        assert timeline.observations(row.row_id), row.row_id


def test_stop_kills_live_children_by_pid_and_forgets_them(tmp_path: Path) -> None:
    folder = lf.live_dir(tmp_path)
    folder.mkdir()
    ug.write_json(folder / lf.PIDS, {"emulator": 11, "poller": 12, "window": ["a", "b"]})
    killed = []
    out = lf.stop(tmp_path, kill=lambda pid, sig: killed.append((pid, sig)), is_alive=lambda pid: pid == 12)
    assert killed == [(12, signal.SIGTERM)] and out == {"stopped": [{"poller": 12}]}
    assert not (folder / lf.PIDS).exists()
    assert lf.stop(tmp_path) == {"stopped": []}


def test_serve_starts_the_edge_gateway_for_either_switch_and_the_cli_has_live_field() -> None:
    import demo_combined

    source = Path(demo_combined.__file__).read_text(encoding="utf-8")
    assert "upload_gateway.upload_switched_on() or live_field.live_switched_on()" in source
    with pytest.raises(SystemExit):  # argparse: the step must be one of the four
        demo_combined.main(["--db", "x_test", "--work", "var/x", "live-field", "go"])
