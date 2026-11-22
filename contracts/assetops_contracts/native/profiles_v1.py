"""3A6 (spec §2.1, §2.5 step 6; D-3A6.1, D-3A6.3, D-3A6.6, D-3A6.16): a source profile compiled to the one engine.

A profile is a JSON object with closed keys at every level. `compile_profile` turns it into a `Layout` read by the same
engine as the illustrative layouts (`split_file`, `read_rows`); `run_probes` is the store-free half of the contract
test, run on the analyst's sample at admission. Standard library, `assetops_contracts.canonical` and
`native.layouts_v1` only.
"""

from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Callable, Mapping, Sequence
from zoneinfo import ZoneInfo

from assetops_contracts.canonical import SOURCE_TYPES, CanonicalRefused
from assetops_contracts.canonical.records_v1 import CLOCK_KEYS
from assetops_contracts.native.layouts_v1 import (
    CODED_PATHS,
    DATE_FORMATS,
    MONTH_FORMATS,
    BOOL_VALUES,
    TIME_FORMATS,
    TYPES,
    Column,
    FileRules,
    Layout,
    ValueRules,
    check_layout,
    read_rows,
)

SCHEMA = "assetops.source-profile"
_A = re.ASCII
_PROFILE_ID = re.compile(r"[a-z][a-z0-9-]{0,47}", _A)
_SOURCE_SYSTEM = re.compile(r"[a-z0-9][a-z0-9.-]{0,79}", _A)
_SCALE = re.compile(r"(0|[1-9][0-9]{0,11})(\.[0-9]{1,12})?", _A)
_ZONE = re.compile(r"[A-Za-z0-9_+-]+(/[A-Za-z0-9_+-]+)*", _A)
_PATH = re.compile(
    r"source_record_id|source_version|site_code|kind|status|subject\.(kind|ref)"
    rf"|clocks\.({'|'.join(CLOCK_KEYS)})|amount\.(value|currency)|quantity\.(value|unit)|body\.[a-z][a-z0-9_]{{0,63}}",
    _A)
_TOP = frozenset({"schema", "schema_version", "profile_id", "status", "source_type", "source_system", "file",
                  "values", "version", "columns", "constants", "personal"})
_TOP_OPTIONAL = frozenset({"record_id_join"})
_VALUES = frozenset({"decimal_mark", "thousands_mark", "negative", "date_format", "time_format", "month_format",
                     "timezone"})
_PROBE_CHARACTERS = ("\x00", "\x85", "\u200b", "\ufeff", "\u2028")


class ProfileInvalid(ValueError):
    """A profile that does not compile; `str` is `PROFILE_INVALID <where>` (the dotted key path)."""

    def __init__(self, where: str) -> None:
        super().__init__(where)
        self.where = where

    def __str__(self) -> str:
        return f"PROFILE_INVALID {self.where}"


def reader_id_for(profile_id: str, version: int) -> str:
    return f"profile.{profile_id}.v{version}"


def _has_control(text: str) -> bool:
    return any(unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp", "Cs") for ch in text)


def _int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _keys(obj: object, where: str, required: frozenset[str], optional: frozenset[str] = frozenset()) -> dict:
    if not isinstance(obj, dict):
        raise ProfileInvalid(where or "json")
    prefix = f"{where}." if where else ""
    for key in obj:
        if key not in required and key not in optional:
            raise ProfileInvalid(f"{prefix}{key}")
    for key in sorted(required):
        if key not in obj:
            raise ProfileInvalid(f"{prefix}{key}")
    return obj


def _choice(obj: dict, key: str, where: str, allowed) -> str:
    value = obj[key]
    if not isinstance(value, str) or value not in allowed:
        raise ProfileInvalid(f"{where}.{key}")
    return value


def _file(obj: object) -> FileRules:
    fmt = obj.get("format") if isinstance(obj, dict) else None
    if fmt == "csv":
        f = _keys(obj, "file", frozenset({"format", "encoding", "delimiter", "header_row"}))
        encoding = _choice(f, "encoding", "file", ("utf-8", "cp1252"))
        delimiter = _choice(f, "delimiter", "file", (",", ";", "\t", "|"))
        sheet = None
    elif fmt == "xlsx":
        f = _keys(obj, "file", frozenset({"format", "sheet", "header_row"}))
        sheet = f["sheet"]
        if not isinstance(sheet, str) or not 1 <= len(sheet) <= 31 or _has_control(sheet):
            raise ProfileInvalid("file.sheet")
        encoding, delimiter = "utf-8", ","
    else:
        raise ProfileInvalid("file.format" if isinstance(obj, dict) else "file")
    header_row = f["header_row"]
    if not _int(header_row) or not 1 <= header_row <= 20:
        raise ProfileInvalid("file.header_row")
    return FileRules(format=fmt, encoding=encoding, delimiter=delimiter, header_row=header_row, sheet=sheet)


def _values(obj: object) -> ValueRules:
    v = _keys(obj, "values", _VALUES)
    decimal = _choice(v, "decimal_mark", "values", (".", ","))
    thousands = _choice(v, "thousands_mark", "values", ("", ",", ".", " ", "'"))
    if thousands == decimal:
        raise ProfileInvalid("values.thousands_mark")
    negative = _choice(v, "negative", "values", ("minus", "parentheses"))
    date_format = _choice(v, "date_format", "values", DATE_FORMATS)
    time_format = _choice(v, "time_format", "values", TIME_FORMATS)
    month_format = _choice(v, "month_format", "values", MONTH_FORMATS)
    zone = v["timezone"]
    if not isinstance(zone, str) or not _ZONE.fullmatch(zone):
        raise ProfileInvalid("values.timezone")
    try:
        ZoneInfo(zone)
    except Exception:  # ZoneInfoNotFoundError, ValueError, OSError: the name does not load
        raise ProfileInvalid("values.timezone") from None
    return ValueRules(decimal_mark=decimal, thousands_mark=thousands, negative=negative, date_format=date_format,
                      time_format=time_format, month_format=month_format, timezone=zone)


def _text_value(value: object, where: str, low: int, high: int) -> str:
    if not isinstance(value, str) or not low <= len(value) <= high or _has_control(value):
        raise ProfileInvalid(where)
    return value


def compile_profile(obj: object, version: int) -> Layout:
    """Spec §2.1: the profile object as a `Layout` whose id is `reader_id_for(profile_id, version)`. Raises
    `ProfileInvalid(where)`."""
    if not _int(version) or not 1 <= version <= 9999:
        raise ValueError("version must be 1 to 9999")
    top = _keys(obj, "", _TOP, _TOP_OPTIONAL)
    if top["schema"] != SCHEMA:
        raise ProfileInvalid("schema")
    if not _int(top["schema_version"]) or top["schema_version"] != 1:
        raise ProfileInvalid("schema_version")
    profile_id = top["profile_id"]
    if not isinstance(profile_id, str) or not _PROFILE_ID.fullmatch(profile_id):
        raise ProfileInvalid("profile_id")
    if top["status"] not in ("ILLUSTRATIVE", "PINNED"):
        raise ProfileInvalid("status")
    source_type = top["source_type"]
    if not isinstance(source_type, str) or source_type not in SOURCE_TYPES:
        raise ProfileInvalid("source_type")
    system = top["source_system"]
    if not isinstance(system, str) or not _SOURCE_SYSTEM.fullmatch(system) or system.startswith("illustrative-"):
        raise ProfileInvalid("source_system")
    file_rules = _file(top["file"])
    value_rules = _values(top["values"])

    raw_columns = top["columns"]
    if not isinstance(raw_columns, list) or not 2 <= len(raw_columns) <= 60:
        raise ProfileInvalid("columns")
    writers: dict[str, str] = {}
    columns: list[Column] = []
    headers: list[str] = []
    for i, raw in enumerate(raw_columns):
        where = f"columns.{i}"
        c = _keys(raw, where, frozenset({"header", "paths"}))
        header = _text_value(c["header"], f"{where}.header", 1, 100)
        if header in headers:
            raise ProfileInvalid(f"{where}.header")
        headers.append(header)
        if not isinstance(c["paths"], list):
            raise ProfileInvalid(f"{where}.paths")
        paths: list[str] = []
        maps: dict[str, Mapping[str, str]] = {}
        types: dict[str, str] = {}
        scales: dict[str, str] = {}
        for j, raw_path in enumerate(c["paths"]):
            pw = f"{where}.paths.{j}"
            p = _keys(raw_path, pw, frozenset({"path", "type"}), frozenset({"map", "scale"}))
            path = p["path"]
            if not isinstance(path, str) or not _PATH.fullmatch(path):
                raise ProfileInvalid(f"{pw}.path")
            if path in writers:
                raise ProfileInvalid(f"{pw}.path")
            writers[path] = pw
            type_ = p["type"]
            if not isinstance(type_, str) or type_ not in TYPES:
                raise ProfileInvalid(f"{pw}.type")
            if "map" in p:
                mapping = p["map"]
                allowed = (type_ == "bool") or (type_ == "text" and path in CODED_PATHS)
                if (not allowed or not isinstance(mapping, dict) or not mapping
                        or any(not isinstance(k, str) or not isinstance(v, str) or not k or not v
                               or _has_control(k) or _has_control(v) for k, v in mapping.items())
                        or len(set(mapping.values())) != len(mapping)
                        or (type_ == "bool" and set(mapping.values()) != BOOL_VALUES)):
                    raise ProfileInvalid(f"{pw}.map")
                maps[path] = MappingProxyType(dict(mapping))
            elif path in CODED_PATHS or type_ == "bool":
                raise ProfileInvalid(f"{pw}.map")
            if "scale" in p:
                scale = p["scale"]
                if type_ != "number" or not isinstance(scale, str) or not _SCALE.fullmatch(scale):
                    raise ProfileInvalid(f"{pw}.scale")
                try:
                    if Decimal(scale) == 0:
                        raise ProfileInvalid(f"{pw}.scale")
                except InvalidOperation:
                    raise ProfileInvalid(f"{pw}.scale") from None
                scales[path] = scale
            if type_ != "text":
                types[path] = type_
            paths.append(path)
        columns.append(Column(header, tuple(paths), MappingProxyType(maps), MappingProxyType(types),
                              MappingProxyType(scales)))

    raw_constants = top["constants"]
    if not isinstance(raw_constants, dict):
        raise ProfileInvalid("constants")
    constants: dict[str, str] = {}
    for path, value in raw_constants.items():
        if not isinstance(path, str) or not _PATH.fullmatch(path) or path in writers:
            raise ProfileInvalid(f"constants.{path}")
        constants[path] = _text_value(value, f"constants.{path}", 1, 200)
        writers[path] = f"constants.{path}"

    join: tuple[str, ...] = ()
    if "record_id_join" in top:
        raw_join = top["record_id_join"]
        with_paths = {c.header for c in columns if c.paths}
        if (not isinstance(raw_join, list) or not 2 <= len(raw_join) <= 4 or len(set(map(str, raw_join))) != len(raw_join)
                or any(not isinstance(h, str) or h not in with_paths for h in raw_join)):
            raise ProfileInvalid("record_id_join")
        if "source_record_id" in writers:
            raise ProfileInvalid("record_id_join")
        join = tuple(raw_join)
    elif "source_record_id" not in writers or writers["source_record_id"].startswith("constants."):
        raise ProfileInvalid("columns")

    version_rule = _keys(top["version"], "version", frozenset({"from"}), frozenset({"value"}))
    source = version_rule["from"]
    digest = False
    if source == "constant":
        _keys(version_rule, "version", frozenset({"from", "value"}))
        value = _text_value(version_rule["value"], "version.value", 1, 40)
        if "status" in writers or "source_version" in writers:
            raise ProfileInvalid("version")
        constants["source_version"] = value
    elif source == "column":
        _keys(version_rule, "version", frozenset({"from"}))
        if "source_version" not in writers or writers["source_version"].startswith("constants."):
            raise ProfileInvalid("version")
    elif source == "row_digest":
        _keys(version_rule, "version", frozenset({"from"}))
        if "source_version" in writers:
            raise ProfileInvalid("version")
        digest = True
    else:
        raise ProfileInvalid("version.from")

    raw_personal = top["personal"]
    if not isinstance(raw_personal, list):
        raise ProfileInvalid("personal")
    personal: set[tuple[str, str]] = set()
    for i, item in enumerate(raw_personal):
        if (not isinstance(item, list) or len(item) != 2 or not isinstance(item[0], str)
                or not isinstance(item[1], str) or item[1] not in ("C", "M", "P")):
            raise ProfileInvalid(f"personal.{i}")
        personal.add((item[0], item[1]))

    layout = Layout(id=reader_id_for(profile_id, version), source_type=source_type, source_system=system,
                    columns=tuple(columns), constants=MappingProxyType(constants), personal=frozenset(personal),
                    file=file_rules, values=value_rules, record_id_join=join, version_digest=digest)
    try:
        check_layout(layout)
    except ValueError:
        raise ProfileInvalid("columns") from None
    return layout


# --- probes (spec §2.5 step 6) ----------------------------------------------------------------------------------

Rows = list[tuple[int, list[str]]]
Reader = Callable[..., object]


def _copy(rows: Sequence[tuple[int, Sequence[str]]]) -> Rows:
    return [(n, list(cells)) for n, cells in rows]


def _first_filled(rows: Rows, index: int) -> int | None:
    return next((k for k, (_, cells) in enumerate(rows) if index < len(cells) and cells[index] != ""), None)


def run_probes(layout: Layout, header: Sequence[str], rows: Sequence[tuple[int, Sequence[str]]], *, tenant_code: str,
               produced_at: str, provenance: str, read: Reader = read_rows) -> tuple[str, str] | None:
    """The first failing `(probe, where)`, or None when all six refuse what they must."""
    ctx = {"tenant_code": tenant_code, "produced_at": produced_at, "provenance": provenance}
    base = _copy(rows)
    if not base:
        return ("P2", "rows")

    def only(mutated: Rows, k: int, code: str) -> bool:
        try:
            result = read(layout, list(header), mutated, **ctx)
        except CanonicalRefused:
            return False
        return (len(result.obj["records"]) == len(mutated) and set(result.refused) == {k}
                and result.refused[k][0] == code)

    swapped = list(header)
    if len(swapped) < 2:
        return ("P1", "file")
    swapped[0], swapped[1] = swapped[1], swapped[0]
    try:
        read(layout, swapped, _copy(base), **ctx)
        return ("P1", "file")
    except CanonicalRefused as refused:
        if refused.code != "NATIVE_HEADER":
            return ("P1", "file")

    short = _copy(base)
    short[0] = (short[0][0], short[0][1][:-1])
    if not only(short, 0, "NATIVE_ROW"):
        return ("P2", f"row.{base[0][0]}")

    first_written = next((i for i, c in enumerate(layout.columns) if c.paths), None)
    if first_written is None:
        return ("P3", "columns")
    for ch in _PROBE_CHARACTERS:
        mutated = _copy(base)
        mutated[0][1][first_written] += ch
        if not only(mutated, 0, "NATIVE_CHARACTER"):
            return ("P3", f"U+{ord(ch):04X}")

    for i, column in enumerate(layout.columns):
        if not column.maps:
            continue
        k = _first_filled(base, i)
        if k is None:
            return ("P4", column.header)
        mutated = _copy(base)
        mutated[k][1][i] = mutated[k][1][i] + " ?"
        if not only(mutated, k, "NATIVE_VALUE"):
            return ("P4", column.header)

    for i, column in enumerate(layout.columns):
        for path in column.paths:
            if column.types.get(path, "text") == "text" or path in column.maps:
                continue  # a mapped path (DD2.2 `bool`) is probed by P4
            k = _first_filled(base, i)
            if k is None:
                return ("P5", column.header)
            mutated = _copy(base)
            mutated[k][1][i] = "?"
            if not only(mutated, k, "NATIVE_FORMAT"):
                return ("P5", column.header)

    for i, column in enumerate(layout.columns):
        if not column.paths:
            continue
        k = _first_filled(base, i)
        if k is None:
            return ("P6", column.header)
        mutated = _copy(base)
        mutated[k][1][i] = ""
        try:
            result = read(layout, list(header), mutated, **ctx)
        except CanonicalRefused:
            return ("P6", column.header)
        if len(result.obj["records"]) != len(mutated) or set(result.refused) - {k}:
            return ("P6", column.header)
        if k not in result.refused:
            record = result.obj["records"][k]
            if any(_holds(record, path) for path in column.paths):
                return ("P6", column.header)
    return None


def _holds(record: Mapping, path: str) -> bool:
    value: object = record
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return False
        value = value[part]
    return True
