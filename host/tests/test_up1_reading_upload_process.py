"""UP-1 no-DB tests: the host's field-process ports and the upload switch. No gateway, no database.

`check` runs the real `python -m assetops_field.csv_upload` on the pinned fixture; `send` is exercised with a fake
runner (the Postgres flow on its own `*_test` DB proves the real gateway path).
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

import reading_upload_process as up
from assetops_backend.config import ConfigurationError
from assetops_backend.reading_upload import service as svc
from assetops_field.export_csv import CSV_CODES

FIXTURE = up.ROOT / "contract-fixtures" / "telemetry" / "generic-interval-csv-v1" / "kobo-window.csv"


def test_the_product_restates_the_eight_csv_codes_exactly():
    assert svc.CSV_CODES == CSV_CODES


@pytest.mark.parametrize("value,expected", [(None, frozenset()), ("", frozenset()), ("KOBO-001", {"KOBO-001"}),
                                            (" kobo-001 ", {"KOBO-001"})])
def test_the_switch_is_off_by_default_and_names_kobo(value, expected):
    environ = {} if value is None else {up.SITES_ENV: value}
    assert up.sites_from_environment(environ) == frozenset(expected)


@pytest.mark.parametrize("value", ["COLD-LAB-001", "KOBO-001,EV-LAB-001"])
def test_any_other_site_refuses_startup(value):
    with pytest.raises(ConfigurationError):
        up.sites_from_environment({up.SITES_ENV: value})


def test_the_gateway_file_must_name_every_key(tmp_path):
    path = tmp_path / "gw.json"
    path.write_text(json.dumps({"gateway_address": "127.0.0.1:1"}), encoding="utf-8")
    with pytest.raises(ConfigurationError):
        up.gateway_from_environment({up.GATEWAY_ENV: str(path)})
    assert up.gateway_from_environment({}) is None


def test_check_runs_the_field_process_on_the_fixture():
    checked = up.ProcessFileChecker().check(FIXTURE.read_bytes())
    assert isinstance(checked, svc.Preview)
    assert (checked.rows, checked.cells) == (49, 196)
    assert checked.first_interval_end_by_role["pv_power"] == datetime(2026, 9, 30, 3, 0, tzinfo=timezone.utc)


def test_check_returns_the_field_refusal():
    refused = up.ProcessFileChecker().check(FIXTURE.read_bytes().replace(b"pv_ac_power", b"pv_power"))
    assert isinstance(refused, svc.FileRefusal) and refused.code == "HEADER_MISMATCH"
    assert len(refused.profile_sha256) == 64


def test_the_temp_file_is_removed_after_the_run():
    seen: list[Path] = []

    def runner(argv, **kw):
        seen.append(Path(argv[argv.index("--file") + 1]))
        assert seen[-1].read_bytes() == b"abc"
        return SimpleNamespace(returncode=0, stdout='{"ok": true}\n', stderr="")

    assert up.run_field(["check"], b"abc", runner, limits=up.CHECK_LIMITS, step="check") == (0, {"ok": True})
    assert not seen[0].exists()


def test_send_reads_the_field_summary():
    sent_doc = {"ok": True, "sent": {"session_ref": "field:x", "outcomes": {"ADMITTED": 150, "ALREADY_ADMITTED": 6,
                                                                              "HELD": 4},
                                     "held": {"pv-ac-power:UNIT_INCOMPATIBLE:unit": 4},
                                     "message_ids": ["m1", None, "m2"]}}

    def runner(argv, **kw):
        assert argv[7] == "send" and "--gateway-address" in argv  # ENV-1: after the four limit arguments
        return SimpleNamespace(returncode=0, stdout=json.dumps(sent_doc), stderr="")

    gateway = {k: "x" for k in up.GATEWAY_KEYS}
    delivered: list = []
    sent = up.ProcessReadingSender(gateway, runner=runner, deliver=delivered.append).send(b"data")
    assert (sent.admitted, sent.held, sent.message_ids) == (156, 4, ("m1", "m2"))
    assert sent.held_by_column == {"pv-ac-power": 4}
    assert delivered == [gateway]  # D-UP.2 (d): the host delivers once the send exits 0


@pytest.mark.parametrize("code,error", [(4, "GATEWAY_UNAVAILABLE"), (5, "IDENTITY_MISMATCH"), (3, "CONFIGURATION")])
def test_a_failed_send_is_gateway_unavailable(code, error):
    def runner(argv, **kw):
        return SimpleNamespace(returncode=code, stdout=json.dumps({"ok": False, "error": error}), stderr="")

    delivered: list = []
    with pytest.raises(svc.GatewayUnavailable):
        up.ProcessReadingSender({k: "x" for k in up.GATEWAY_KEYS}, runner=runner,
                                deliver=delivered.append).send(b"data")
    assert delivered == []  # nothing was sent, so nothing is delivered


def test_the_template_is_the_profile_header_and_passes_the_field_check():
    template = up.template_csv()
    assert not template.startswith(b"\xef\xbb\xbf") and template.endswith(b"\r\n")
    header = template.decode("ascii").strip()
    fixture_lines = FIXTURE.read_text(encoding="utf-8").splitlines()
    assert header == fixture_lines[0]  # the collector's own fixture carries the same header row
    filled = template + "\r\n".join(fixture_lines[1:4]).encode("ascii") + b"\r\n"
    assert isinstance(up.ProcessFileChecker().check(filled), svc.Preview)  # the real field process accepts it


def test_the_host_never_imports_the_field_adapters():
    source = Path(up.__file__).read_text(encoding="utf-8")
    assert "import assetops_field" not in source and "from assetops_field" not in source
    assert subprocess.run  # the ports reach the field adapters only by running them


# --- ENV-1 H0 to H7 (spec §2.3, §4; D-ENV1.2, D-ENV1.9 to D-ENV1.11, D-ENV1.16) ----------------------------------------

import ast  # noqa: E402
import dataclasses  # noqa: E402
import signal  # noqa: E402
import time  # noqa: E402
from datetime import timedelta  # noqa: E402
from uuid import uuid4  # noqa: E402

import threading  # noqa: E402

from assetops_backend.parse_slots import HostSlots, host_slots  # noqa: E402
from assetops_field import csv_upload  # noqa: E402

MIB = 2**20
HEADER = (b"timestamp_utc,pv_ac_power [kW],clinic_feeder_power [kW],mill_feeder_power [kW],"
          b"residential_feeder_power [kW]\r\n")


def two_mib(tail: str) -> bytes:
    """F1 / F2 by hand (spec §3): the header, then rows every 15 minutes from 2026-01-01T00:15:00Z, as many as fit in
    2,097,152 bytes."""
    out, size, t = [HEADER], len(HEADER), datetime(2026, 1, 1, 0, 15, tzinfo=timezone.utc)
    while True:
        row = f"{t:%Y-%m-%dT%H:%M:%SZ}{tail}\r\n".encode("ascii")
        if size + len(row) > 2 * MIB:
            return b"".join(out)
        out.append(row)
        size += len(row)
        t += timedelta(minutes=15)


F1 = two_mib(",12.5,3.25,1.5,7.75")
F2 = two_mib(",,,,")
F4 = FIXTURE.read_bytes()
F1_ROWS, F2_ROWS = 51_147, 80_655


def _ns() -> str:
    return f"t-{uuid4().hex[:12]}"


def _limits(memory: int = 512 * MIB, cpu: int = 30, wall: float = 60.0, wait: float = 60.0) -> up.FieldLimits:
    return up.FieldLimits(memory, cpu, wall, wait)


def _after_a_breach_the_next_check_reads() -> None:
    """H7: the next production check of F4 returns its preview."""
    checked = up.ProcessFileChecker().check(F4)
    assert isinstance(checked, svc.Preview) and checked.rows == 49


def test_h0_the_limits_are_pinned():
    assert (len(F1), F1.count(b"\r\n") - 1, len(F2), F2.count(b"\r\n") - 1) == (2_097_137, F1_ROWS, 2_097_140, F2_ROWS)
    assert up.CHECK_LIMITS == up.FieldLimits(512 * MIB, 30, 60.0, 60.0)
    assert up.SEND_LIMITS == up.FieldLimits(896 * MIB, 120, 270.0, 60.0)  # wall: D-ENV1.18/19 (129.2 s measured)
    assert dict(up.STEP_POOLS) == {"check": "reading", "send": "reading-send"}
    assert up.EXIT_LIMIT == csv_upload.EXIT_LIMIT == 7
    assert not hasattr(up, "TIMEOUT_SECONDS")
    for field in ("memory_bytes", "cpu_seconds", "wall_seconds", "slot_wait_seconds"):
        for bad in (0, -1, True):
            with pytest.raises(ValueError):
                dataclasses.replace(up.CHECK_LIMITS, **{field: bad})
    for field in ("memory_bytes", "cpu_seconds"):
        with pytest.raises(ValueError):
            dataclasses.replace(up.CHECK_LIMITS, **{field: 1.5})
    with pytest.raises(TypeError):
        up.ProcessFileChecker(limits=(1, 2, 3, 4))
    with pytest.raises(TypeError):
        up.ProcessReadingSender({k: "x" for k in up.GATEWAY_KEYS}, limits=None)


def test_h1_the_limit_arguments_come_first_with_each_step_limits():
    calls: list[tuple[list[str], dict]] = []

    def runner(argv, **kw):
        calls.append((list(argv), kw))
        return SimpleNamespace(returncode=2, stdout=json.dumps({"ok": False, "refusal": {
            "code": "EMPTY_FILE", "field": "", "detail": "", "profile_sha256": ""}}), stderr="")

    up.ProcessFileChecker(runner=runner).check(b"x")
    up.ProcessReadingSender({k: "x" for k in up.GATEWAY_KEYS}, runner=runner).send(b"x")
    for (argv, kw), limits, step in zip(calls, (up.CHECK_LIMITS, up.SEND_LIMITS), ("check", "send")):
        start = argv.index("-m")
        assert argv[start:start + 8] == ["-m", "assetops_field.csv_upload",
                                         "--limit-memory-bytes", str(limits.memory_bytes),
                                         "--limit-cpu-seconds", str(limits.cpu_seconds), step, "--profile"]
        assert kw["env"]["PYTHONDONTWRITEBYTECODE"] == "1"
        assert kw["timeout"] == limits.wall_seconds


def test_h2_memory_breach_is_coded():
    with pytest.raises(svc.ParseLimitBreach) as raised:
        up.ProcessFileChecker(limits=_limits(memory=96 * MIB)).check(F2)
    assert (raised.value.cause, raised.value.step) == ("memory", "check")
    _after_a_breach_the_next_check_reads()


def test_h3_cpu_and_wall_breaches_are_coded(monkeypatch):
    with pytest.raises(svc.ParseLimitBreach) as raised:
        up.ProcessFileChecker(limits=_limits(cpu=1)).check(F1)
    assert (raised.value.cause, raised.value.step) == ("cpu", "check")
    seen: list[Path] = []
    real_mkstemp = up.tempfile.mkstemp

    def mkstemp(**kw):
        handle, name = real_mkstemp(**kw)
        seen.append(Path(name))
        return handle, name

    monkeypatch.setattr(up.tempfile, "mkstemp", mkstemp)
    with pytest.raises(svc.ParseLimitBreach) as raised:
        up.ProcessFileChecker(limits=_limits(wall=0.5)).check(F1)
    assert (raised.value.cause, raised.value.step) == ("wall", "check")
    assert seen and not seen[0].exists()
    monkeypatch.undo()
    _after_a_breach_the_next_check_reads()


@pytest.mark.parametrize("code,stdout,stderr,cause", [
    (-9, "", "", "killed"),
    (7, json.dumps({"ok": False, "error": "LIMIT", "detail": "memory"}), "", "memory"),
    (-11, json.dumps({"ok": True, "preview": {}}), "", "crashed"),
    (-6, json.dumps({"ok": True, "preview": {}}), "", "crashed"),
    (1, "", "Traceback (most recent call last):\n  ...\nSystemError: x\n", "crashed"),
], ids=["killed", "memory", "segv", "abort", "no-json"])
def test_h4_return_codes_map_to_causes(code, stdout, stderr, cause):
    def runner(argv, **kw):
        return SimpleNamespace(returncode=code, stdout=stdout, stderr=stderr)

    with pytest.raises(svc.ParseLimitBreach) as raised:
        up.ProcessFileChecker(runner=runner).check(b"data")
    assert (raised.value.cause, raised.value.step) == (cause, "check")
    _after_a_breach_the_next_check_reads()


@pytest.mark.parametrize("code", [7, -11])
def test_h4_a_send_breach_never_delivers(code):
    def runner(argv, **kw):
        return SimpleNamespace(returncode=code, stdout="", stderr="")

    delivered: list = []
    with pytest.raises(svc.ParseLimitBreach) as raised:
        up.ProcessReadingSender({k: "x" for k in up.GATEWAY_KEYS}, runner=runner,
                                deliver=delivered.append).send(b"data")
    assert raised.value.step == "send" and delivered == []
    _after_a_breach_the_next_check_reads()


def test_h5_a_slot_wait_past_its_bound_is_coded():
    slots = HostSlots(_ns(), "r", 1)
    ran: list = []

    def runner(argv, **kw):
        ran.append(argv)
        return SimpleNamespace(returncode=0, stdout='{"ok": true}', stderr="")

    with slots.hold(1.0):
        raised = _bounded(lambda: up.ProcessFileChecker(runner=runner, limits=_limits(wait=0.2),
                                                        slots=slots).check(b"data"))
    assert isinstance(raised, svc.ParseLimitBreach), raised
    assert (raised.cause, raised.step, ran) == ("slot", "check", [])
    _after_a_breach_the_next_check_reads()


def _bounded(call) -> BaseException | None:
    """D-ENV1.22: a call whose slot wait must expire runs in a daemon thread, bounded by `join(5)`; its exception."""
    box: list = []

    def run() -> None:
        try:
            call()
            box.append(None)
        except BaseException as caught:  # noqa: BLE001 - handed back to the test
            box.append(caught)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    thread.join(5)
    assert not thread.is_alive(), "hold ignored its timeout"
    return box[0]


def test_h8_sends_run_one_at_a_time_in_their_own_pool():
    """D-ENV1.18: the send takes the one `reading-send` slot by default; the check's `reading` pool is separate."""
    ran: list = []
    delivered: list = []

    def runner(argv, **kw):
        ran.append(argv)
        return SimpleNamespace(returncode=2, stdout=json.dumps({"ok": False, "refusal": {
            "code": "EMPTY_FILE", "field": "", "detail": "", "profile_sha256": ""}}), stderr="")

    sender = up.ProcessReadingSender({k: "x" for k in up.GATEWAY_KEYS}, runner=runner, deliver=delivered.append,
                                     limits=dataclasses.replace(up.SEND_LIMITS, slot_wait_seconds=0.2))
    with host_slots("reading-send").hold(1.0):
        raised = _bounded(lambda: sender.send(b"data"))
        assert isinstance(raised, svc.ParseLimitBreach), raised
        assert (raised.cause, raised.step, ran, delivered) == ("slot", "send", [], [])
        up.ProcessFileChecker(runner=runner, limits=dataclasses.replace(up.CHECK_LIMITS, slot_wait_seconds=0.2)
                              ).check(b"data")
        assert len(ran) == 1


@pytest.mark.slow
def test_h6_production_memory_and_cpu_hold_the_legitimate_worst_case():
    limits = dataclasses.replace(up.CHECK_LIMITS, wall_seconds=600.0, slot_wait_seconds=600.0)
    for data, rows in ((F2, F2_ROWS), (F1, F1_ROWS)):
        started = time.monotonic()
        checked = up.ProcessFileChecker(limits=limits).check(data)
        assert isinstance(checked, svc.Preview) and checked.rows == rows
        print(f"ENV-1 H6 check rows={rows} wall={time.monotonic() - started:.1f}s")
    tree = ast.parse((up.ROOT / "host" / "lab_app.py").read_text(encoding="utf-8"))
    def name(node: ast.Call) -> str:
        return node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")

    built = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and name(node) in ("ProcessFileChecker", "ProcessReadingSender")]
    assert sorted(name(node) for node in built) == ["ProcessFileChecker", "ProcessReadingSender"]
    for node in built:  # no keyword at all, and only the gateway positionally: production runs the pinned limits
        assert node.keywords == [] and len(node.args) == (1 if name(node) == "ProcessReadingSender" else 0)
