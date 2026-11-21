"""UP-1 (rev 7 section 7.5): the host's reading-upload ports, each one run of `python -m assetops_field.csv_upload`.

The dependency-direction guard lets only `field/` and `host/tests` import `assetops_field` (TEL-01 ruling D4: field
adapters run as separate processes), so the API never imports the collector: it writes the bytes to a private temp
file and runs the field process, which validates the whole file (`check`) or validates and admits it through the
demo upload gateway's authenticated channel (`send`). Nothing is admitted inside the API process.

Configuration (`ASSETOPS_READING_UPLOAD_GATEWAY`): a JSON file naming `gateway_address`, `ipc_credential`,
`snapshot_sha256` and `expect_identity` (a path), written when the demo upload gateway is started (pre-flight Q2).
Without it the dry run still works and a confirm answers 503 READING_UPLOAD_GATEWAY_UNAVAILABLE.

ENV-1 (spec §2.3; D-ENV1.2, D-ENV1.8 to D-ENV1.11): each run holds a host slot of the `reading` pool (per network
namespace), passes the memory and CPU limits the field process sets before it reads a byte, and waits a bounded wall
time. A breach raises `ParseLimitBreach` with its closed cause; the API logs it and answers 503. The limits are
D-ENV1.10's margin method over the measured runs of spec §0 on the reference host class (packet); retuning for a
slower class means re-running that measurement.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import astuple, dataclass, fields
from pathlib import Path
from typing import Any, Mapping

from assetops_backend.config import ConfigurationError
from assetops_backend.parse_slots import HostSlots, SlotWaitExpired, host_slots
from assetops_backend.reading_upload.service import (FileRefusal, GatewayUnavailable, ParseLimitBreach, Preview, Sent,
                                                     preview_from_document)

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "field" / "profiles" / "generic-interval-csv-illustrative-1.json"
SITES_ENV = "ASSETOPS_READING_UPLOAD_SITES"
GATEWAY_ENV = "ASSETOPS_READING_UPLOAD_GATEWAY"
#: D-17N.5: Kobo is the only Site with a CSV profile; any other code in the switch refuses startup.
SUPPORTED_SITES = frozenset({"KOBO-001"})
GATEWAY_KEYS = ("gateway_address", "ipc_credential", "snapshot_sha256", "expect_identity")
EXIT_OK, EXIT_REFUSED = 0, 2
EXIT_LIMIT = 7  # equal to `assetops_field.csv_upload.EXIT_LIMIT` (test H0 compares them)


@dataclass(frozen=True)
class FieldLimits:
    memory_bytes: int  # RLIMIT_AS of the child
    cpu_seconds: int  # RLIMIT_CPU soft; hard = soft + 1
    wall_seconds: float  # the subprocess timeout
    slot_wait_seconds: float  # how long a request waits for a host slot

    def __post_init__(self) -> None:
        for name, value in zip((f.name for f in fields(self)), astuple(self)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not value > 0:
                raise ValueError(f"field limit {name} must be a number > 0")
        for name in ("memory_bytes", "cpu_seconds"):
            if not isinstance(getattr(self, name), int):
                raise ValueError(f"field limit {name} must be an int")


#: D-ENV1.10's method on the pre-flight runs (packet): memory the next 128 MiB at or above 2x the largest floor, CPU
#: the next 10 s at or above 3x the largest run, wall 2x CPU, slot wait 60 s (a policy). Pinned by test H0.
CHECK_LIMITS = FieldLimits(512 * 2**20, 30, 60.0, 60.0)
SEND_LIMITS = FieldLimits(896 * 2**20, 120, 240.0, 60.0)
#: D-UP.2 (d): the host's delivery after a send; the gateway's 60 s upload interval is the backstop.
DELIVER_BOUND_SECONDS, DELIVER_BATCHES = 30.0, 50


def sites_from_environment(environ: Mapping[str, str] = os.environ) -> frozenset[str]:
    """`ASSETOPS_READING_UPLOAD_SITES`: unset or empty is off; otherwise a comma list of supported Site codes."""
    value = (environ.get(SITES_ENV) or "").strip()
    if not value:
        return frozenset()
    codes = frozenset(part.strip().upper() for part in value.split(",") if part.strip())
    unsupported = sorted(codes - SUPPORTED_SITES)
    if unsupported:
        raise ConfigurationError(f"{SITES_ENV} may name only {sorted(SUPPORTED_SITES)}, not {unsupported}")
    return codes


def gateway_from_environment(environ: Mapping[str, str] = os.environ) -> dict[str, str] | None:
    path = environ.get(GATEWAY_ENV)
    if not path:
        return None
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = [k for k in GATEWAY_KEYS if not isinstance(document.get(k), str) or not document[k]]
    if missing:
        raise ConfigurationError(f"{GATEWAY_ENV} file lacks {missing}")
    return {k: document[k] for k in GATEWAY_KEYS}


def _env() -> dict[str, str]:
    env = dict(os.environ)
    parts = [str(ROOT / "field"), str(ROOT / "gateway"), str(ROOT / "contracts")]
    if env.get("PYTHONPATH"):
        parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(parts)
    env["PYTHONDONTWRITEBYTECODE"] = "1"  # the child runs under RLIMIT_FSIZE 0
    return env


TIMESTAMP_HEADER = "timestamp_utc"


def template_csv(profile: Path = PROFILE) -> bytes:
    """The upload template: the CSV profile's header row (`timestamp_utc`, then `<column> [<unit>]` per profile row,
    in profile order; the collector's header rule). Plain ASCII, no byte-order mark, no data rows. Read from the
    profile document only (no field-adapter import)."""
    document = json.loads(profile.read_text(encoding="utf-8"))
    cells = [TIMESTAMP_HEADER] + [f"{row['csv']['column']} [{row['source_unit']}]" for row in document["rows"]]
    return (",".join(cells) + "\r\n").encode("ascii")


def run_field(argv: list[str], data: bytes, runner: Any = subprocess.run, *, limits: FieldLimits, step: str,
              slots: HostSlots | None = None) -> tuple[int, dict]:
    """Hold a `reading` host slot; write `data` to a private temp file; run the field process under `limits` with
    `--file <it>`; its exit code and JSON line. A limit, a lost slot wait or a death without an answer raises
    `ParseLimitBreach(cause, step)`."""
    if step not in ("check", "send"):
        raise ValueError(f"unknown parse step {step!r}")
    if not isinstance(limits, FieldLimits):
        raise TypeError("limits must be FieldLimits")
    slots = slots if slots is not None else host_slots("reading")
    try:
        with slots.hold(limits.slot_wait_seconds):
            handle, name = tempfile.mkstemp(prefix="reading-upload-", suffix=".csv")
            try:
                with os.fdopen(handle, "wb") as out:
                    out.write(data)
                command = [sys.executable, "-m", "assetops_field.csv_upload",
                           "--limit-memory-bytes", str(limits.memory_bytes),
                           "--limit-cpu-seconds", str(limits.cpu_seconds), *argv, "--file", name]
                try:
                    done = runner(command, capture_output=True, text=True, timeout=limits.wall_seconds, env=_env(),
                                  cwd=str(ROOT))
                except subprocess.TimeoutExpired:  # subprocess.run has killed and reaped the child
                    raise ParseLimitBreach("wall", step) from None
            finally:
                Path(name).unlink(missing_ok=True)
    except SlotWaitExpired:
        raise ParseLimitBreach("slot", step) from None
    code = done.returncode
    if code == EXIT_LIMIT:
        raise ParseLimitBreach("memory", step)
    if code == -signal.SIGXCPU:
        raise ParseLimitBreach("cpu", step)
    if code == -signal.SIGKILL:
        raise ParseLimitBreach("killed", step)
    if code < 0:
        raise ParseLimitBreach("crashed", step)
    lines = [line for line in (done.stdout or "").splitlines() if line.strip()]
    try:
        return code, json.loads(lines[-1])
    except (IndexError, ValueError):
        raise ParseLimitBreach("crashed", step) from None


def _refusal(document: Mapping[str, Any]) -> FileRefusal:
    r = document["refusal"]
    return FileRefusal(r["code"], r["field"], r["detail"], r.get("profile_sha256", ""))


def _limits(limits: Any) -> FieldLimits:
    if not isinstance(limits, FieldLimits):
        raise TypeError("limits must be FieldLimits")
    return limits


class ProcessFileChecker:
    def __init__(self, profile: Path = PROFILE, runner: Any = subprocess.run, limits: FieldLimits = CHECK_LIMITS,
                 slots: HostSlots | None = None) -> None:
        self._profile, self._runner = profile, runner
        self._limits, self._slots = _limits(limits), slots

    def check(self, data: bytes) -> Preview | FileRefusal:
        code, document = run_field(["check", "--profile", str(self._profile)], data, self._runner,
                                   limits=self._limits, step="check", slots=self._slots)
        if code == EXIT_OK and document.get("ok"):
            return preview_from_document(document["preview"])
        if code == EXIT_REFUSED and "refusal" in document:
            return _refusal(document)
        raise RuntimeError(f"the field check failed (exit {code}): {document}")


def deliver_now(gateway: Mapping[str, str], *, bound_seconds: float = DELIVER_BOUND_SECONDS,
                link_factory: Any = None, clock: Any = time.monotonic) -> int:
    """D-UP.2 (d): after a send, ask the upload gateway (over its IPC link) to deliver its sealed batches now:
    `deliver` 50 at a time until a pass attempts none, bounded at `bound_seconds`. Never raises: a failed or
    unfinished delivery leaves the upload SENT, and the gateway's 60 s upload interval (the backstop) delivers it.
    Returns the number of batches attempted."""
    attempted_total = 0
    try:
        if link_factory is None:
            from assetops_gateway.ipc import GatewayLink

            link_factory = GatewayLink
        link = link_factory(gateway["gateway_address"], Path(gateway["ipc_credential"]))
        deadline = clock() + bound_seconds
        while clock() < deadline:
            attempted = int(link.call("deliver", {"max_batches": DELIVER_BATCHES})["batches"]["attempted"])
            if not attempted:
                break
            attempted_total += attempted
    except Exception:  # noqa: BLE001 - the backstop delivers; the upload row is already SENT
        pass
    return attempted_total


class ProcessReadingSender:
    def __init__(self, gateway: Mapping[str, str], profile: Path = PROFILE, runner: Any = subprocess.run,
                 deliver: Any = deliver_now, limits: FieldLimits = SEND_LIMITS, slots: HostSlots | None = None) -> None:
        self._gateway, self._profile, self._runner = dict(gateway), profile, runner
        self._deliver = deliver
        self._limits, self._slots = _limits(limits), slots

    def send(self, data: bytes) -> Sent | FileRefusal:
        g = self._gateway
        code, document = run_field(["send", "--profile", str(self._profile), "--gateway-address", g["gateway_address"],
                                    "--ipc-credential", g["ipc_credential"], "--snapshot-sha256", g["snapshot_sha256"],
                                    "--expect-identity", g["expect_identity"]], data, self._runner,
                                   limits=self._limits, step="send", slots=self._slots)
        if code == EXIT_REFUSED and "refusal" in document:
            return _refusal(document)
        if code != EXIT_OK or not document.get("ok"):
            raise GatewayUnavailable(f"the field send failed (exit {code}): {document.get('error')}")
        sent = document["sent"]
        self._deliver(g)
        outcomes = sent["outcomes"]
        held_by_column: dict[str, int] = {}
        for key, count in sent["held"].items():
            column = key.split(":", 1)[0]
            held_by_column[column] = held_by_column.get(column, 0) + int(count)
        return Sent(session_ref=sent["session_ref"],
                    admitted=int(outcomes.get("ADMITTED", 0)) + int(outcomes.get("ALREADY_ADMITTED", 0)),
                    held=int(outcomes.get("HELD", 0)), message_ids=tuple(m for m in sent["message_ids"] if m),
                    held_by_column=held_by_column)
