"""The pinned field profile (`assetops.field-profile` version 1).

Build spec 0.6 and ruling D4 "Rules held in the pinned profile". A profile is a
JSON document whose canonical SHA-256 is key-order independent. `load_profile`
refuses a document that breaks any rule with `ProfileRefused(code, field,
detail)`, where `field` is a JSON path such as `rows[0].registers[1].address`
and `code` is one of the nine `PROFILE_CODES`.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from assetops_contracts.observation import device_resolution
from assetops_contracts.source_envelope import canonical_json

PROFILE_CODES = (
    "SCHEMA_INVALID",
    "UNSUPPORTED_VALUE",
    "STATUS_INCONSISTENT",
    "POLL_PERIOD_NOT_DIVISOR",
    "CADENCE_NOT_ALIGNED",
    "DUPLICATE_SIGNAL",
    "REPORT_KEY_TOO_LONG",
    "RESOLUTION_FINER_THAN_QUANTUM",
    "SENTINEL_OUT_OF_RANGE",
)

SCHEMA = {"id": "assetops.field-profile", "version": 1}
STATUSES = ("PINNED", "UNPINNED", "ILLUSTRATIVE")  # strongest first
INTERFACES = ("MODBUS_TCP", "EXPORT_CSV")
READING_CLASSES = ("STATE_SIGNAL", "INTERVAL_SIGNAL")
REGISTER_TYPES = {"int16": (16, True), "uint16": (16, False), "int32": (32, True), "uint32": (32, False)}
WORD_ORDERS = ("BIG", "LITTLE")
FUNCTIONS = (3, 4)  # October: holding and input registers only
REPORT_KEY_MAX = 192
REPORT_KEY_PROBE_TIME = "2026-12-31T23:59:59Z"
SECONDS_PER_DAY = 86400

_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
_CSV_COLUMN = re.compile(r"[a-z][a-z0-9_]{0,63}")
_ENUM_CODE = re.compile(r"0|[1-9][0-9]*")
_ENUM_STATE = re.compile(r"[A-Z][A-Z0-9_]*")

_TOP_KEYS = frozenset(
    {"schema", "profile_id", "profile_version", "status", "interface", "source_timestamps", "coverage",
     "state_skew_max_seconds", "rows"}
)
_COMMON_ROW_KEYS = frozenset(
    {"row_id", "status", "source_document", "device_id", "signal_id", "role", "source_unit", "quantity",
     "reading_class", "cadence_seconds"}
)
_QUANTITY_KEYS = frozenset({"kind", "point", "sign", "phase_aggregation"})
_REGISTER_KEYS = frozenset({"unit_id", "function", "address", "type", "word_order"})
_NUMBER_KEYS = frozenset({"scale_exponent", "unit_exponent", "register_unit", "register_quantum", "output_resolution"})


class ProfileRefused(ValueError):
    """A field profile that breaks one of the 0.6 rules."""

    def __init__(self, code: str, field: str, detail: str) -> None:
        if code not in PROFILE_CODES:
            raise ValueError(f"unknown profile refusal code {code!r}")
        self.code, self.field, self.detail = code, field, detail
        super().__init__(f"{code} at {field}: {detail}")


@dataclass(frozen=True)
class RegisterRef:
    unit_id: int
    function: int
    address: int
    type: str
    word_order: str

    @property
    def bits(self) -> int:
        return REGISTER_TYPES[self.type][0]

    @property
    def words(self) -> int:
        return self.bits // 16

    @property
    def signed(self) -> bool:
        return REGISTER_TYPES[self.type][1]


@dataclass(frozen=True)
class CsvColumn:
    column: str


@dataclass(frozen=True)
class ProfileRow:
    row_id: str
    status: str
    source_document: str
    device_id: str
    signal_id: str
    role: str
    source_unit: str
    quantity: Mapping[str, str]
    reading_class: str
    span_seconds: int | None
    cadence_seconds: int
    poll_period_seconds: int | None
    output_resolution: Fraction | None
    registers: tuple[RegisterRef, ...] = ()
    decode: str | None = None
    enum_map: Mapping[int, str] | None = None
    sentinels: frozenset[int] = frozenset()
    scale_exponent: int | None = None
    unit_exponent: int | None = None
    register_unit: str | None = None
    register_quantum: Fraction | None = None
    csv: CsvColumn | None = None

    @property
    def word_count(self) -> int:
        return sum(register.words for register in self.registers)

    @property
    def exponent(self) -> int:
        if self.scale_exponent is None or self.unit_exponent is None:
            raise ValueError(f"row {self.row_id} is not a NUMBER row and has no exponent")
        return self.scale_exponent + self.unit_exponent


@dataclass(frozen=True)
class FieldProfile:
    profile_id: str
    profile_version: int
    status: str
    interface: str
    state_skew_max_seconds: int
    rows: tuple[ProfileRow, ...]
    sha256: str
    document: Mapping[str, Any]


def profile_sha256(document: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(document).encode("utf-8")).hexdigest()


def report_key_text(profile_id: str, profile_version: int, device_id: str, signal_id: str, source_time_z: str) -> str:
    """`<profile_id>:<profile_version>:<device_id>:<signal_id>:<source_time>` (D4 "Report key")."""
    return f"{profile_id}:{profile_version}:{device_id}:{signal_id}:{source_time_z}"


def load_profile(path: Path) -> FieldProfile:
    try:
        text = Path(path).read_bytes().decode("utf-8")
        document = json.loads(text, parse_float=Decimal)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProfileRefused("SCHEMA_INVALID", "$", f"not UTF-8 JSON: {error}") from error
    return parse_profile(document)


# --- parsing -------------------------------------------------------------------------------------------------


def _invalid(field: str, detail: str) -> ProfileRefused:
    return ProfileRefused("SCHEMA_INVALID", field, detail)


def _is_int(value: object) -> bool:
    return type(value) is int


def _int(document: Mapping[str, Any], key: str, path: str, low: int | None = None, high: int | None = None) -> int:
    value = document[key]
    field = f"{path}.{key}" if path else key
    if not _is_int(value):
        raise _invalid(field, "an integer is wanted")
    if (low is not None and value < low) or (high is not None and value > high):
        raise _invalid(field, f"{value} is outside {low}..{high}")
    return value


def _text(document: Mapping[str, Any], key: str, path: str) -> str:
    value = document[key]
    field = f"{path}.{key}" if path else key
    if not isinstance(value, str) or not value:
        raise _invalid(field, "a non-empty string is wanted")
    return value


def _keys(document: object, path: str, required: frozenset[str], allowed: frozenset[str] | None = None) -> None:
    if not isinstance(document, dict):
        raise _invalid(path or "$", "an object is wanted")
    allowed = required if allowed is None else allowed
    for key in sorted(document):
        if key not in allowed:
            raise _invalid(f"{path}.{key}" if path else key, "not a field here")
    for key in sorted(required):
        if key not in document:
            raise _invalid(f"{path}.{key}" if path else key, "required")


def _decimal(document: Mapping[str, Any], key: str, path: str) -> Fraction:
    try:
        return device_resolution(document[key])
    except ValueError as error:
        raise _invalid(f"{path}.{key}", str(error)) from error


def parse_profile(document: Mapping[str, Any]) -> FieldProfile:
    _keys(document, "", _TOP_KEYS)
    if document["schema"] != SCHEMA:
        raise _invalid("schema", f"{SCHEMA!r} is wanted")
    profile_id = _text(document, "profile_id", "")
    if not _ID.fullmatch(profile_id):
        raise _invalid("profile_id", f"{profile_id!r} does not match {_ID.pattern}")
    profile_version = _int(document, "profile_version", "", low=1)
    skew = _int(document, "state_skew_max_seconds", "", low=1, high=10)
    status = document["status"]
    if status not in STATUSES:
        raise _invalid("status", f"one of {list(STATUSES)} is wanted")
    interface = document["interface"]
    if interface not in INTERFACES:
        raise _invalid("interface", f"one of {list(INTERFACES)} is wanted")
    rows_document = document["rows"]
    if not isinstance(rows_document, list) or not rows_document:
        raise _invalid("rows", "a non-empty list is wanted")
    if document["source_timestamps"] != "UTC_Z_REQUIRED":
        raise ProfileRefused("UNSUPPORTED_VALUE", "source_timestamps", "only UTC_Z_REQUIRED is accepted in October")
    if document["coverage"] != "ALL_EXPECTED_POLLS":
        raise ProfileRefused("UNSUPPORTED_VALUE", "coverage", "only ALL_EXPECTED_POLLS is accepted in October")

    rows = tuple(_parse_row(row, f"rows[{index}]", interface) for index, row in enumerate(rows_document))

    row_ids: set[str] = set()
    signals: set[tuple[str, str]] = set()
    for index, row in enumerate(rows):
        if row.row_id in row_ids:
            raise _invalid(f"rows[{index}].row_id", f"{row.row_id!r} is not unique")
        row_ids.add(row.row_id)
        signal = (row.device_id, row.signal_id)
        if signal in signals:
            raise ProfileRefused("DUPLICATE_SIGNAL", f"rows[{index}]", f"{signal[0]}/{signal[1]} is declared twice")
        signals.add(signal)
        key = report_key_text(profile_id, profile_version, row.device_id, row.signal_id, REPORT_KEY_PROBE_TIME)
        if len(key) > REPORT_KEY_MAX:
            raise ProfileRefused("REPORT_KEY_TOO_LONG", f"rows[{index}]", f"{len(key)} > {REPORT_KEY_MAX} characters")
    if interface == "EXPORT_CSV" and len({row.span_seconds for row in rows}) != 1:
        raise _invalid("rows", "every row of one CSV profile has the same span_seconds")

    weakest = max(rows, key=lambda row: STATUSES.index(row.status)).status
    if status != weakest:
        raise ProfileRefused("STATUS_INCONSISTENT", "status", f"{status} is not the weakest row status {weakest}")

    return FieldProfile(
        profile_id=profile_id,
        profile_version=profile_version,
        status=status,
        interface=interface,
        state_skew_max_seconds=skew,
        rows=rows,
        sha256=profile_sha256(document),
        document=document,
    )


def _row_keys(row: Mapping[str, Any], path: str, interface: str) -> tuple[frozenset[str], frozenset[str]]:
    """The required and allowed key sets of one row, from its class, interface and decode."""
    if not isinstance(row, dict):
        raise _invalid(path, "an object is wanted")
    required = set(_COMMON_ROW_KEYS)
    reading_class = row.get("reading_class")
    if reading_class == "INTERVAL_SIGNAL":
        required.add("span_seconds")
        if interface == "MODBUS_TCP":
            required.add("poll_period_seconds")
    if interface == "MODBUS_TCP":
        required |= {"registers", "decode", "sentinels"}
        if row.get("decode") == "NUMBER":
            required |= _NUMBER_KEYS
        elif row.get("decode") == "ENUM":
            required.add("enum_map")
    else:
        required |= {"csv", "output_resolution"}
    return frozenset(required), frozenset(required)


def _parse_row(row: Mapping[str, Any], path: str, interface: str) -> ProfileRow:
    required, allowed = _row_keys(row, path, interface)
    # The class and decode keys are read before the key check so a missing or
    # misspelled one is named rather than reported as a forbidden neighbour.
    for key in ("reading_class", "decode") if interface == "MODBUS_TCP" else ("reading_class",):
        if key not in row:
            raise _invalid(f"{path}.{key}", "required")
    if row["reading_class"] not in READING_CLASSES:
        raise _invalid(f"{path}.reading_class", f"one of {list(READING_CLASSES)} is wanted")
    if interface == "MODBUS_TCP" and row["decode"] not in ("NUMBER", "ENUM"):
        raise _invalid(f"{path}.decode", "NUMBER or ENUM is wanted")
    _keys(row, path, required, allowed)

    row_id = _text(row, "row_id", path)
    if not _ID.fullmatch(row_id):
        raise _invalid(f"{path}.row_id", f"{row_id!r} does not match {_ID.pattern}")
    status = row["status"]
    if status not in STATUSES:
        raise _invalid(f"{path}.status", f"one of {list(STATUSES)} is wanted")
    source_document = _text(row, "source_document", path)
    device_id = _text(row, "device_id", path)
    signal_id = _text(row, "signal_id", path)
    role = _text(row, "role", path)
    source_unit = _text(row, "source_unit", path)
    quantity_document = row["quantity"]
    _keys(quantity_document, f"{path}.quantity", _QUANTITY_KEYS)
    quantity = {key: _text(quantity_document, key, f"{path}.quantity") for key in sorted(_QUANTITY_KEYS)}
    reading_class = row["reading_class"]

    cadence = _int(row, "cadence_seconds", path, low=1)
    span = _int(row, "span_seconds", path, low=1) if "span_seconds" in row else None
    period = _int(row, "poll_period_seconds", path, low=1) if "poll_period_seconds" in row else None
    if SECONDS_PER_DAY % cadence:
        raise ProfileRefused("CADENCE_NOT_ALIGNED", f"{path}.cadence_seconds", f"{cadence} does not divide 86400")
    if span is not None:
        if SECONDS_PER_DAY % span:
            raise ProfileRefused("CADENCE_NOT_ALIGNED", f"{path}.span_seconds", f"{span} does not divide 86400")
        if cadence % span:
            raise ProfileRefused("CADENCE_NOT_ALIGNED", f"{path}.cadence_seconds",
                                 f"{cadence} is not a whole multiple of span {span}")
    if period is not None and (period % 2 or period < 2 or span % period):
        raise ProfileRefused("POLL_PERIOD_NOT_DIVISOR", f"{path}.poll_period_seconds",
                             f"{period} is not an even divisor (>= 2) of span {span}")

    output_resolution = _decimal(row, "output_resolution", path) if "output_resolution" in row else None

    if interface == "EXPORT_CSV":
        csv_document = row["csv"]
        _keys(csv_document, f"{path}.csv", frozenset({"column"}))
        column = csv_document["column"]
        if not isinstance(column, str) or not _CSV_COLUMN.fullmatch(column):
            raise _invalid(f"{path}.csv.column", f"a header name matching {_CSV_COLUMN.pattern} is wanted")
        if reading_class != "INTERVAL_SIGNAL":
            raise _invalid(f"{path}.reading_class", "an EXPORT_CSV row is INTERVAL_SIGNAL")
        return ProfileRow(
            row_id=row_id, status=status, source_document=source_document, device_id=device_id,
            signal_id=signal_id, role=role, source_unit=source_unit, quantity=MappingProxyType(quantity),
            reading_class=reading_class, span_seconds=span, cadence_seconds=cadence, poll_period_seconds=None,
            output_resolution=output_resolution, csv=CsvColumn(column),
        )

    registers = _parse_registers(row["registers"], f"{path}.registers")
    decode = row["decode"]
    phase = quantity["phase_aggregation"]
    if len(registers) == 1 and phase != "SINGLE_REGISTER":
        raise _invalid(f"{path}.quantity.phase_aggregation", "SINGLE_REGISTER is wanted for a one-register row")

    enum_map: Mapping[int, str] | None = None
    scale_exponent = unit_exponent = None
    register_unit: str | None = None
    register_quantum: Fraction | None = None
    if decode == "ENUM":
        if len(registers) != 1 or registers[0].type != "uint16":
            raise _invalid(f"{path}.registers", "an ENUM row reads exactly one uint16 register")
        if source_unit != "state":
            raise _invalid(f"{path}.source_unit", "an ENUM row has source_unit 'state'")
        if reading_class != "STATE_SIGNAL":
            raise _invalid(f"{path}.reading_class", "an ENUM row is STATE_SIGNAL")
        enum_map = MappingProxyType(_parse_enum_map(row["enum_map"], f"{path}.enum_map"))
    else:
        if len(registers) > 1 and not phase.startswith("EXACT_SUM_"):
            raise _invalid(f"{path}.quantity.phase_aggregation",
                           "a multi-register NUMBER row is an exact sum (EXACT_SUM_*)")
        scale_exponent = _int(row, "scale_exponent", path, low=-12, high=12)
        unit_exponent = _int(row, "unit_exponent", path, low=-12, high=12)
        register_unit = _text(row, "register_unit", path)
        register_quantum = _decimal(row, "register_quantum", path)
        quantum_in_source = register_quantum * Fraction(10) ** (scale_exponent + unit_exponent)
        if output_resolution < quantum_in_source:
            raise ProfileRefused("RESOLUTION_FINER_THAN_QUANTUM", f"{path}.output_resolution",
                                 f"{row['output_resolution']} is finer than the register quantum in "
                                 f"{source_unit}")

    sentinels = _parse_sentinels(row["sentinels"], f"{path}.sentinels", registers)

    return ProfileRow(
        row_id=row_id, status=status, source_document=source_document, device_id=device_id,
        signal_id=signal_id, role=role, source_unit=source_unit, quantity=MappingProxyType(quantity),
        reading_class=reading_class, span_seconds=span, cadence_seconds=cadence, poll_period_seconds=period,
        output_resolution=output_resolution, registers=registers, decode=decode, enum_map=enum_map,
        sentinels=sentinels, scale_exponent=scale_exponent, unit_exponent=unit_exponent,
        register_unit=register_unit, register_quantum=register_quantum,
    )


def _parse_registers(document: object, path: str) -> tuple[RegisterRef, ...]:
    if not isinstance(document, list) or not document:
        raise _invalid(path, "a non-empty list is wanted")
    registers = []
    for index, register in enumerate(document):
        where = f"{path}[{index}]"
        _keys(register, where, _REGISTER_KEYS)
        unit_id = _int(register, "unit_id", where, low=0, high=255)
        function = register["function"]
        if not _is_int(function) or function not in FUNCTIONS:
            raise _invalid(f"{where}.function", "3 or 4 is wanted in October")
        address = _int(register, "address", where, low=0, high=65535)
        kind = register["type"]
        if kind not in REGISTER_TYPES:
            raise _invalid(f"{where}.type", f"one of {sorted(REGISTER_TYPES)} is wanted")
        if register["word_order"] not in WORD_ORDERS:
            raise _invalid(f"{where}.word_order", "BIG or LITTLE is wanted")
        ref = RegisterRef(unit_id, function, address, kind, register["word_order"])
        if address + ref.words - 1 > 65535:
            raise _invalid(f"{where}.address", "a 32-bit register cannot start at 65535")
        registers.append(ref)
    return tuple(registers)


def _parse_enum_map(document: object, path: str) -> dict[int, str]:
    if not isinstance(document, dict):
        raise _invalid(path, "an object is wanted")
    result: dict[int, str] = {}
    for code, state in sorted(document.items()):
        if not isinstance(code, str) or not _ENUM_CODE.fullmatch(code) or int(code) > 65535:
            raise _invalid(f"{path}.{code}", "a decimal code 0..65535 is wanted")
        if not isinstance(state, str) or not _ENUM_STATE.fullmatch(state):
            raise _invalid(f"{path}.{code}", f"state text matching {_ENUM_STATE.pattern} is wanted")
        result[int(code)] = state
    return result


def _parse_sentinels(document: object, path: str, registers: tuple[RegisterRef, ...]) -> frozenset[int]:
    if not isinstance(document, list):
        raise _invalid(path, "a list is wanted")
    # A sentinel is compared with each register's unsigned value, so it must be a
    # value every register of the row can hold (see the T1 question on mixed widths).
    bits = min(register.bits for register in registers)
    values = set()
    for index, value in enumerate(document):
        if not _is_int(value):
            raise _invalid(f"{path}[{index}]", "an integer is wanted")
        if not 0 <= value < 2**bits:
            raise ProfileRefused("SENTINEL_OUT_OF_RANGE", f"{path}[{index}]",
                                 f"{value} is not an unsigned {bits}-bit raw value")
        values.add(value)
    return frozenset(values)
