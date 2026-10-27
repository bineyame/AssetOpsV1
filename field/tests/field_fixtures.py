"""Shared helpers for `field/tests` (no conftest.py, ruling D4)."""

from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from typing import Any

GX1_PV_ROW: dict[str, Any] = {
    "row_id": "pv-ac-output",
    "status": "UNPINNED",
    "source_document": "third-party summary (aggsoft.com), Victron CCGX register list; not a vendor document",
    "device_id": "pv-inverter-controller",
    "signal_id": "ac-power",
    "role": "pv_power",
    "source_unit": "kW",
    "quantity": {"kind": "AC_POWER", "point": "AC output bus, AC-coupled PV only",
                 "sign": "positive = power delivered to the AC bus",
                 "phase_aggregation": "EXACT_SUM_L1_L2_L3"},
    "registers": [
        {"unit_id": 100, "function": 3, "address": 808, "type": "uint16", "word_order": "BIG"},
        {"unit_id": 100, "function": 3, "address": 809, "type": "uint16", "word_order": "BIG"},
        {"unit_id": 100, "function": 3, "address": 810, "type": "uint16", "word_order": "BIG"},
    ],
    "decode": "NUMBER",
    "sentinels": [65535],
    "scale_exponent": 0,
    "register_unit": "W",
    "unit_exponent": -3,
    "register_quantum": "1",
    "output_resolution": "0.001",
    "reading_class": "INTERVAL_SIGNAL",
    "span_seconds": 900,
    "cadence_seconds": 900,
    "poll_period_seconds": 300,
}

GX1_SOC_ROW: dict[str, Any] = {
    "row_id": "battery-soc",
    "status": "UNPINNED",
    "source_document": "third-party summary (aggsoft.com), Victron CCGX register list; not a vendor document",
    "device_id": "battery-pcs-controller",
    "signal_id": "state-of-charge",
    "role": "battery_soc",
    "source_unit": "%",
    "quantity": {"kind": "STATE_OF_CHARGE", "point": "battery bank as reported by the system",
                 "sign": "not applicable", "phase_aggregation": "SINGLE_REGISTER"},
    "registers": [{"unit_id": 100, "function": 3, "address": 843, "type": "uint16", "word_order": "BIG"}],
    "decode": "NUMBER",
    "sentinels": [65535],
    "scale_exponent": 0,
    "register_unit": "%",
    "unit_exponent": 0,
    "register_quantum": "1",
    "output_resolution": "1",
    "reading_class": "STATE_SIGNAL",
    "cadence_seconds": 900,
}

_BLOCK_SOURCE = "AssetOps illustrative block; not a vendor register map"
_BLOCK_POINT = "AssetOps illustrative block; not a vendor register"


def _block_row(address: int, device: str, signal: str, role: str, unit: str, reading_class: str,
               kind: str, sign: str) -> dict[str, Any]:
    row: dict[str, Any] = {
        "row_id": f"{device}-{signal}",
        "status": "ILLUSTRATIVE",
        "source_document": _BLOCK_SOURCE,
        "device_id": device,
        "signal_id": signal,
        "role": role,
        "source_unit": unit,
        "quantity": {"kind": kind, "point": _BLOCK_POINT, "sign": sign, "phase_aggregation": "SINGLE_REGISTER"},
        "registers": [{"unit_id": 101, "function": 3, "address": address, "type": "int32", "word_order": "BIG"}],
        "decode": "NUMBER",
        "sentinels": [2147483647],
        "scale_exponent": -6,
        "register_unit": unit,
        "unit_exponent": 0,
        "register_quantum": "1",
        "output_resolution": "0.000001",
        "reading_class": reading_class,
        "cadence_seconds": 300,
    }
    if reading_class == "INTERVAL_SIGNAL":
        row["span_seconds"] = 300
        row["poll_period_seconds"] = 60
    return row


def gx2_rows() -> list[dict[str, Any]]:
    """Profile `-2` rows as the TEL-05b table states them (used here for the decode round trip)."""
    status_row: dict[str, Any] = {
        "row_id": "generator-controller-status",
        "status": "ILLUSTRATIVE",
        "source_document": _BLOCK_SOURCE,
        "device_id": "generator-controller",
        "signal_id": "status",
        "role": "generator_state",
        "source_unit": "state",
        "quantity": {"kind": "OPERATING_STATE", "point": _BLOCK_POINT, "sign": "not applicable",
                     "phase_aggregation": "SINGLE_REGISTER"},
        "registers": [{"unit_id": 101, "function": 3, "address": 1000, "type": "uint16", "word_order": "BIG"}],
        "decode": "ENUM",
        "enum_map": {"0": "STOPPED", "1": "STARTING", "2": "RUNNING", "3": "FAILED"},
        "sentinels": [65535],
        "reading_class": "STATE_SIGNAL",
        "cadence_seconds": 300,
    }
    feeder = "positive = power drawn by the feeder"
    return [
        copy.deepcopy(GX1_PV_ROW),
        status_row,
        _block_row(1002, "generator-controller", "ac-power", "generator_power", "kW", "INTERVAL_SIGNAL",
                   "AC_POWER", "positive = power delivered to the AC bus"),
        _block_row(1004, "residential-meter", "active-power", "feeder_demand", "kW", "INTERVAL_SIGNAL",
                   "AC_POWER", feeder),
        _block_row(1006, "clinic-meter", "active-power", "feeder_demand", "kW", "INTERVAL_SIGNAL", "AC_POWER", feeder),
        _block_row(1008, "mill-meter", "active-power", "feeder_demand", "kW", "INTERVAL_SIGNAL", "AC_POWER", feeder),
        _block_row(1010, "pv-inverter-controller", "available-power", "pv_available_power", "kW", "INTERVAL_SIGNAL",
                   "AVAILABLE_AC_POWER", "positive = power the PV could deliver"),
        _block_row(1012, "battery-pcs-controller", "discharge-capability", "pcs_discharge_capability", "kW",
                   "INTERVAL_SIGNAL", "DISCHARGE_CAPABILITY", "positive = power the PCS could discharge"),
        _block_row(1014, "battery-pcs-controller", "state-of-charge", "battery_soc", "%", "STATE_SIGNAL",
                   "STATE_OF_CHARGE", "not applicable"),
    ]


def row_document(**overrides: Any) -> dict[str, Any]:
    """The `-1` PV row with top-level keys replaced; a value of `...` removes the key."""
    row = copy.deepcopy(GX1_PV_ROW)
    for key, value in overrides.items():
        if value is ...:
            row.pop(key, None)
        else:
            row[key] = value
    return row


def profile_document(**overrides: Any) -> dict[str, Any]:
    """A valid `-1`-shaped profile with top-level keys replaced; `...` removes the key."""
    document: dict[str, Any] = {
        "schema": {"id": "assetops.field-profile", "version": 1},
        "profile_id": "gx-system-illustrative-1",
        "profile_version": 1,
        "status": "UNPINNED",
        "interface": "MODBUS_TCP",
        "source_timestamps": "UTC_Z_REQUIRED",
        "coverage": "ALL_EXPECTED_POLLS",
        "state_skew_max_seconds": 2,
        "rows": [copy.deepcopy(GX1_PV_ROW), copy.deepcopy(GX1_SOC_ROW)],
    }
    for key, value in overrides.items():
        if value is ...:
            document.pop(key, None)
        else:
            document[key] = value
    return document


def at(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


class FakeWall:
    """A settable wall clock; each read then advances by `tick` (so a spin loop ends)."""

    def __init__(self, start: datetime, tick: timedelta = timedelta(0)) -> None:
        self.instant = start
        self.tick = tick
        self.reads = 0

    def __call__(self) -> datetime:
        current = self.instant
        self.instant = current + self.tick
        self.reads += 1
        return current

    def set(self, instant: datetime) -> None:
        self.instant = instant


class RecordingSleep:
    """Records each requested sleep and advances `wall` by it, so nothing really sleeps."""

    def __init__(self, wall: FakeWall | None = None) -> None:
        self.wall = wall
        self.calls: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)
        if self.wall is not None:
            self.wall.instant += timedelta(seconds=seconds)


class FakeLink:
    """Records `(op, body)` and answers from a script: a value, an exception, or a callable."""

    def __init__(self, script: dict[str, Any] | None = None) -> None:
        self.calls: list[tuple[str, Any]] = []
        self.script: dict[str, Any] = dict(script or {})

    def call(self, op: str, body: dict[str, Any] | None = None) -> Any:
        self.calls.append((op, copy.deepcopy(body)))
        answer = self.script.get(op)
        if isinstance(answer, list):
            answer = answer.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        if callable(answer):
            return answer(body)
        return copy.deepcopy(answer)

    @property
    def ops(self) -> list[str]:
        return [op for op, _ in self.calls]
