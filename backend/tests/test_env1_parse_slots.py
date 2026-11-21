"""ENV-1 (spec §2.1, §2.2, §2.5; D-ENV1.3, D-ENV1.8, D-ENV1.13, D-ENV1.14): parse slots per network namespace,
S0 to S6. No database. Each test uses its own namespace, so nothing here waits on another test's or a server's slots.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from uuid import uuid4

import pytest

from assetops_backend import parse_slots
from assetops_backend.commercial.envelope import DEFAULT_LIMITS, ParseEnvelope
from assetops_backend.commercial.readers import LayoutReader, ReadContext
from assetops_backend.parse_slots import (DEFAULT_NAMESPACE, NAMESPACE_ENV, POOLS, HostSlots, SlotWaitExpired,
                                          host_slots, slot_namespace)
from assetops_contracts.native import compile_profile
from test_3a2_commercial_upload_service import T_SUBMIT
from test_3a6_source_profiles import KOBO_PROFILE, KOBO_SAMPLE, V1

CTX = ReadContext("acme", T_SUBMIT, False)
ROOT = Path(__file__).resolve().parents[2]


def _ns() -> str:
    return f"t-{uuid4().hex[:12]}"


def _kobo_reader() -> LayoutReader:
    reader = LayoutReader(compile_profile(json.loads(KOBO_PROFILE), 1), profile=(KOBO_PROFILE.decode("utf-8"), 1))
    assert reader.id == V1
    return reader


def _child_env(namespace: str | None = None) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT / "backend"), env.get("PYTHONPATH", "")])
    if namespace is not None:
        env[NAMESPACE_ENV] = namespace
    return env


def _spawn(code: str, env: dict[str, str]) -> subprocess.Popen:
    process = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True, env=env)
    return process


def _first_line(process: subprocess.Popen, timeout: float = 30.0) -> str:
    box: list[str] = []
    reader = threading.Thread(target=lambda: box.append(process.stdout.readline()), daemon=True)
    reader.start()
    reader.join(timeout)
    assert box, "the child printed nothing"
    return box[0].strip()


def _read_in_thread(envelope: ParseEnvelope, reader: LayoutReader) -> tuple[threading.Thread, list]:
    box: list = []
    thread = threading.Thread(target=lambda: box.append(envelope.read(reader, KOBO_SAMPLE, CTX)), daemon=True)
    thread.start()
    return thread, box


# --- S0 ---------------------------------------------------------------------------------------------------------------

def test_s0_pools_and_names_are_pinned() -> None:
    assert dict(POOLS) == {"commercial": 2, "reading": 2}
    assert (NAMESPACE_ENV, DEFAULT_NAMESPACE) == ("ASSETOPS_PARSE_SLOT_NAMESPACE", "assetops-parse")
    with pytest.raises(KeyError):
        host_slots("x")


# --- S1 ---------------------------------------------------------------------------------------------------------------

def test_s1_one_process_two_holders_at_most_and_sockets_not_inherited() -> None:
    slots = HostSlots(_ns(), "t", 2)
    lock = threading.Lock()
    active, peak, starts, ends = [0], [0], [], []
    before = set(os.listdir("/proc/self/fd"))
    inheritable: list[bool] = []

    def worker() -> None:
        with slots.hold(10.0):
            with lock:
                active[0] += 1
                peak[0] = max(peak[0], active[0])
                starts.append(time.monotonic())
                fds = set(os.listdir("/proc/self/fd")) - before
                for fd in fds:
                    try:
                        inheritable.append(os.get_inheritable(int(fd)))
                    except OSError:
                        pass
            time.sleep(0.3)
            with lock:
                active[0] -= 1
                ends.append(time.monotonic())

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert peak[0] == 2
    assert sorted(starts)[2] >= min(ends) - 0.01  # the third started only after one released
    assert inheritable and not any(inheritable)


# --- S2 ---------------------------------------------------------------------------------------------------------------

_HOLD_BOTH = """
import sys, time
from assetops_backend.parse_slots import HostSlots
s = HostSlots(sys.argv[1] if len(sys.argv) > 1 else {ns!r}, "t", 2)
with s.hold(5.0), s.hold(5.0):
    print("held", flush=True)
    time.sleep({sleep})
"""


def test_s2_slots_exclude_across_processes_and_a_killed_holder_frees_them() -> None:
    ns = _ns()
    child = _spawn(_HOLD_BOTH.format(ns=ns, sleep=1.0), _child_env())
    try:
        assert _first_line(child) == "held"
        with pytest.raises(SlotWaitExpired):
            with HostSlots(ns, "t", 2).hold(0.2):
                pass
        assert child.wait(30) == 0
        with HostSlots(ns, "t", 2).hold(1.0) as index:
            assert index in (0, 1)
    finally:
        child.kill()
        child.wait()
    killed = _spawn(_HOLD_BOTH.format(ns=ns, sleep=60.0), _child_env())
    try:
        assert _first_line(killed) == "held"
        with pytest.raises(SlotWaitExpired):
            with HostSlots(ns, "t", 2).hold(0.2):
                pass
        killed.send_signal(signal.SIGKILL)
        killed.wait(30)
        with HostSlots(ns, "t", 2).hold(1.0):
            pass
    finally:
        killed.kill()
        killed.wait()


_HOLD_READING = """
import time
from assetops_backend.parse_slots import host_slots
with host_slots("reading").hold(None) as index:
    print(index, flush=True)
    time.sleep(30)
"""

_TRY_READING = """
from assetops_backend.parse_slots import SlotWaitExpired, host_slots
try:
    with host_slots("reading").hold(0.2) as index:
        print(index, flush=True)
except SlotWaitExpired:
    print("expired", flush=True)
"""


def test_s2b_host_slots_through_the_environment() -> None:
    ns = _ns()
    holders = [_spawn(_HOLD_READING, _child_env(ns)) for _ in range(2)]
    try:
        assert sorted(_first_line(h) for h in holders) == ["0", "1"]
        third = subprocess.run([sys.executable, "-c", _TRY_READING], capture_output=True, text=True,
                               env=_child_env(ns), timeout=60)
        assert third.stdout.strip() == "expired", third.stderr
        other = subprocess.run([sys.executable, "-c", _TRY_READING], capture_output=True, text=True,
                               env=_child_env(_ns()), timeout=60)
        assert other.stdout.strip() == "0", other.stderr
    finally:
        for holder in holders:
            holder.kill()
            holder.wait()


# --- S3 ---------------------------------------------------------------------------------------------------------------

def test_s3_slot_namespace_rule(monkeypatch: pytest.MonkeyPatch) -> None:
    assert slot_namespace({}) == DEFAULT_NAMESPACE
    assert slot_namespace({NAMESPACE_ENV: ""}) == DEFAULT_NAMESPACE
    assert slot_namespace({NAMESPACE_ENV: "a-1"}) == "a-1"
    messages = set()
    for bad in ("A", "a b", "a/b", "-a", "a" * 49):
        with pytest.raises(ValueError) as raised:
            slot_namespace({NAMESPACE_ENV: bad})
        messages.add(str(raised.value))
    (said,) = messages  # one sentence whatever the value: it names the variable and the rule, never the value
    assert NAMESPACE_ENV in said and not any(bad in said for bad in ("a b", "a/b", "a" * 49, "-a "))
    monkeypatch.setenv(NAMESPACE_ENV, "A/B")
    envelope = ParseEnvelope()  # construction resolves nothing (D-ENV1.14)
    with pytest.raises(ValueError, match=NAMESPACE_ENV):
        envelope.read(_kobo_reader(), KOBO_SAMPLE, CTX)


# --- S4 ---------------------------------------------------------------------------------------------------------------

def test_s4_the_envelope_waits_for_its_host_slot() -> None:
    assert ParseEnvelope(DEFAULT_LIMITS)._slots_given is None
    slots = HostSlots(_ns(), "c", 1)
    reader = _kobo_reader()
    envelope = ParseEnvelope(DEFAULT_LIMITS, slots=slots)
    with slots.hold(1.0):
        thread, box = _read_in_thread(envelope, reader)
        thread.join(0.5)
        assert thread.is_alive() and not box
    thread.join(60)
    assert box, "the read did not finish after the slot was released"
    assert box[0].result.obj["records"] == reader.read(KOBO_SAMPLE, context=CTX).obj["records"]


# --- S5 ---------------------------------------------------------------------------------------------------------------

def test_s5_constructor_checks() -> None:
    for namespace in ("A", "", "-a", "a" * 49, 3):
        with pytest.raises(ValueError):
            HostSlots(namespace, "t", 1)  # type: ignore[arg-type]
    for pool in ("T", "1a", "", "a" * 33):
        with pytest.raises(ValueError):
            HostSlots("ns", pool, 1)
    for count in (0, True, -1, 1.0):
        with pytest.raises(ValueError):
            HostSlots("ns", "t", count)  # type: ignore[arg-type]
    slots = HostSlots(_ns(), "t", 1)
    for timeout in (0, -1):
        with pytest.raises(ValueError):
            with slots.hold(timeout):
                pass
    with pytest.raises(TypeError):
        ParseEnvelope(slots="x")  # type: ignore[arg-type]


# --- S6 ---------------------------------------------------------------------------------------------------------------

def test_s6_test_isolation_and_the_namespace_read_at_each_read(monkeypatch: pytest.MonkeyPatch) -> None:
    assert slot_namespace() != DEFAULT_NAMESPACE
    assert f"-{os.getpid()}-" in slot_namespace()  # this process (an xdist worker too) set its own
    envelope = ParseEnvelope()
    reader = _kobo_reader()
    ns = _ns()
    monkeypatch.setenv(NAMESPACE_ENV, ns)
    with HostSlots(ns, "commercial", 2).hold(1.0), HostSlots(ns, "commercial", 2).hold(1.0):
        thread, box = _read_in_thread(envelope, reader)
        thread.join(0.5)
        assert thread.is_alive() and not box
    thread.join(60)
    assert box, "the read did not finish after the slots were released"
    assert parse_slots.host_slots("commercial").namespace == ns
