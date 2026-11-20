"""3A3 (spec §2.2, §2.3; D-3A3.2, D-3A3.9, D-3A3.10): native CSV layouts, read and rendered by one engine.

A `Layout` is data: its columns, each filling one or more canonical record paths (through an optional value map),
and the constants written on every record. `read_layout` turns a native file into a canonical batch object (plus the
file row of each record and the rows it refuses itself); `render_layout` turns canonical records back into the native
file. The emulators render with it; the backend's `LayoutReader` reads with it. `3A6` loads `Layout` values from
profile files without changing this contract.

A layout carries no provenance: the reader is told it (D-3A3.10). Standard library and `assetops_contracts.canonical`
only.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Context, Decimal, Inexact, InvalidOperation, Rounded
from types import MappingProxyType
from typing import Mapping, Sequence
from zoneinfo import ZoneInfo

from assetops_contracts.canonical import SOURCE_TYPES, CanonicalRefused
from assetops_contracts.native.xlsx import XlsxBad, XlsxNumber, xlsx_rows

_BOM = b"\xef\xbb\xbf"
_OBJECTS = ("subject", "amount", "quantity", "body", "clocks")
#: D-3A3.9: control characters a cell may not hold (tab, LF and CR are text).
_CONTROL = frozenset([*range(0x00, 0x09), 0x0B, 0x0C, *range(0x0E, 0x20), 0x7F])
#: D-3A6.4: Unicode categories a cell of a written column may not hold (tab, LF and CR excepted).
_INVISIBLE_CATEGORIES = frozenset({"Cc", "Cf", "Zl", "Zp", "Cs"})
_TEXT_CONTROLS = frozenset({"\t", "\n", "\r"})
_EMPTY: Mapping = MappingProxyType({})

#: D-3A6.6: closed-vocabulary canonical paths; a column writing one must carry a map, and a map sits only on one.
CODED_PATHS = frozenset({"kind", "status", "subject.kind", "quantity.unit", "body.line_type", "body.tariff_class",
                         "body.method", "body.category", "body.direction", "body.read_type", "body.contract_type",
                         "body.factor_id"})
DATE_FORMATS = ("YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY", "DD-MM-YYYY", "DD.MM.YYYY", "YYYY/MM/DD")
TIME_FORMATS = ("HH:MM", "HH:MM:SS")
MONTH_FORMATS = ("YYYY-MM", "MM/YYYY", "YYYYMM", "Mon-YYYY", "Month YYYY")
TYPES = ("text", "number", "date", "datetime", "month", "month_of")
_MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
           "November", "December")
_SERIAL_MIN, _SERIAL_MAX = 61, 73050  # D-3A6.13 b: 1900-03-01 to 2099-12-31
_EXCEL_EPOCH = date(1899, 12, 30)
_INSTANT = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?(Z|[+-][0-9]{2}:[0-9]{2})", re.ASCII)


@dataclass(frozen=True)
class FileRules:
    format: str = "csv"  # "csv" | "xlsx"
    encoding: str = "utf-8"  # csv only
    delimiter: str = ","  # csv only
    header_row: int = 1
    sheet: str | None = None  # xlsx only


@dataclass(frozen=True)
class ValueRules:
    decimal_mark: str = "."
    thousands_mark: str = ""
    negative: str = "minus"
    date_format: str = "YYYY-MM-DD"
    time_format: str = "HH:MM:SS"
    month_format: str = "YYYY-MM"
    timezone: str = "UTC"


@dataclass(frozen=True)
class Column:
    header: str  # the exact header cell
    paths: tuple[str, ...]  # canonical record paths the cell fills
    maps: Mapping[str, Mapping[str, str]] = _EMPTY  # path -> {native value: canonical value}
    types: Mapping[str, str] = _EMPTY  # path -> type; absent = "text" (3A6)
    scales: Mapping[str, str] = _EMPTY  # path -> exact decimal multiplier (3A6)


@dataclass(frozen=True)
class Layout:
    id: str  # reader id, also commercial_upload.reader
    source_type: str  # a key of SOURCE_TYPES
    source_system: str
    columns: tuple[Column, ...]
    constants: Mapping[str, str]  # path -> value, written under rule C
    personal: frozenset[tuple[str, str]] = frozenset()  # extra (path, class) for 3A2's pseudonymise
    file: FileRules = field(default_factory=FileRules)
    values: ValueRules = field(default_factory=ValueRules)
    record_id_join: tuple[str, ...] = ()
    version_digest: bool = False


@dataclass(frozen=True)
class NativeRead:
    obj: dict
    rows: tuple[int, ...]
    refused: Mapping[int, tuple[str, str]]


def _top(path: str) -> str | None:
    head = path.split(".", 1)[0]
    return head if head in _OBJECTS and "." in path else None


def _get(record: Mapping, path: str):
    value: object = record
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            return None
        value = value[part]
    return value


def _put(record: dict, path: str, value: str) -> None:
    parts = path.split(".")
    target = record
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = value


def check_layout(layout: Layout) -> None:
    """Import check: a known source type, each map one to one, and (D-3A6.6) a map on exactly the coded paths
    (`NATIVE_LAYOUT <id> <path>`)."""
    if layout.source_type not in SOURCE_TYPES:
        raise ValueError(f"NATIVE_LAYOUT {layout.id} source_type")
    for column in layout.columns:
        for path, mapping in column.maps.items():
            if path not in column.paths or len(set(mapping.values())) != len(mapping):
                raise ValueError(f"NATIVE_LAYOUT {layout.id} {path}")
            if path not in CODED_PATHS:
                raise ValueError(f"NATIVE_LAYOUT {layout.id} {path}")
        for path in column.paths:
            if path in CODED_PATHS and path not in column.maps:
                raise ValueError(f"NATIVE_LAYOUT {layout.id} {path}")


def _column_objects(layout: Layout) -> frozenset[str]:
    return frozenset(t for c in layout.columns for p in c.paths if (t := _top(p)) is not None)


# --- transforms (spec §2.4) -------------------------------------------------------------------------------------

class TransformFailed(ValueError):
    """A cell the type's grammar does not read (`NATIVE_FORMAT`)."""


def _number_pattern(values: ValueRules) -> re.Pattern:
    t, d = values.thousands_mark, values.decimal_mark
    integer = "[0-9]+" if t == "" else rf"(?:[0-9]{{1,3}}(?:{re.escape(t)}[0-9]{{3}})+|[0-9]+)"
    body = rf"(?P<i>{integer})(?:{re.escape(d)}(?P<f>[0-9]+))?"
    if values.negative == "parentheses":
        return re.compile(rf"(?P<neg>\()?{body}(?(neg)\))", re.ASCII)
    return re.compile(rf"(?P<neg>-)?{body}", re.ASCII)


def _number(cell: str, values: ValueRules, scale: str | None) -> str:
    if isinstance(cell, XlsxNumber):
        out = str(cell)
    else:
        m = _number_pattern(values).fullmatch(cell)
        if m is None:
            raise TransformFailed(cell)
        integer, fraction, negative = m["i"], m["f"], m["neg"] is not None
        digits = integer.replace(values.thousands_mark, "") if values.thousands_mark else integer
        digits = digits.lstrip("0") or "0"
        out = ("-" if negative else "") + digits + (f".{fraction}" if fraction is not None else "")
    if scale is not None:
        ctx = Context(prec=60, traps=[Inexact, Rounded, InvalidOperation])
        try:
            out = format(ctx.multiply(Decimal(out), Decimal(scale)), "f")
        except (Inexact, Rounded, InvalidOperation):
            raise TransformFailed(cell) from None
    return out


def _date_pattern(fmt: str) -> re.Pattern:
    out = re.escape(fmt).replace("YYYY", "(?P<y>[0-9]{4})").replace("DD", "(?P<d>[0-9]{1,2})")
    return re.compile(out.replace("MM", "(?P<m>[0-9]{1,2})"), re.ASCII)


def _time_pattern(fmt: str) -> re.Pattern:
    out = re.escape(fmt).replace("HH", "(?P<H>[0-9]{2})").replace("SS", "(?P<S>[0-9]{2})")
    return re.compile(out.replace("MM", "(?P<M>[0-9]{2})"), re.ASCII)


def _serial(cell: XlsxNumber) -> tuple[date, Decimal]:
    try:
        value = Decimal(str(cell))
    except InvalidOperation:
        raise TransformFailed(cell) from None
    k = int(value.to_integral_value(rounding="ROUND_FLOOR"))
    if not _SERIAL_MIN <= k <= _SERIAL_MAX:  # the window first, before any date arithmetic (D-3A6.13 b)
        raise TransformFailed(cell)
    return _EXCEL_EPOCH + timedelta(days=k), value - k


def _date(cell: str, values: ValueRules) -> date:
    if isinstance(cell, XlsxNumber):
        return _serial(cell)[0]
    m = _date_pattern(values.date_format).fullmatch(cell)
    if m is None:
        raise TransformFailed(cell)
    try:
        return date(int(m["y"]), int(m["m"]), int(m["d"]))
    except ValueError:
        raise TransformFailed(cell) from None


def _place(naive: datetime, values: ValueRules) -> datetime:
    zone = ZoneInfo(values.timezone)
    local = naive.replace(tzinfo=zone, fold=0)
    if local.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) != naive:
        raise TransformFailed(str(naive))  # a local time that does not exist there
    return local


def _datetime(cell: str, values: ValueRules) -> str | datetime:
    """An instant kept as is (its text), else the placed local datetime."""
    if isinstance(cell, XlsxNumber):
        day, fraction = _serial(cell)
        seconds = int((fraction * 86400).to_integral_value(rounding="ROUND_HALF_EVEN"))
        return _place(datetime(day.year, day.month, day.day) + timedelta(seconds=seconds), values)
    if _INSTANT.fullmatch(cell):
        return cell
    date_part, _, time_part = cell.partition(" ")
    if not _:
        raise TransformFailed(cell)
    day = _date(date_part, values)
    m = _time_pattern(values.time_format).fullmatch(time_part)
    if m is None:
        raise TransformFailed(cell)
    hour, minute, second = int(m["H"]), int(m["M"]), int(m.groupdict().get("S") or 0)
    if hour > 23 or minute > 59 or second > 59:
        raise TransformFailed(cell)
    return _place(datetime(day.year, day.month, day.day, hour, minute, second), values)


def _month_grammar(cell: str, values: ValueRules) -> str:
    fmt = values.month_format
    year = month = None
    if fmt == "YYYY-MM" and (m := re.fullmatch(r"([0-9]{4})-([0-9]{1,2})", cell, re.ASCII)):
        year, month = m[1], int(m[2])
    elif fmt == "MM/YYYY" and (m := re.fullmatch(r"([0-9]{1,2})/([0-9]{4})", cell, re.ASCII)):
        year, month = m[2], int(m[1])
    elif fmt == "YYYYMM" and (m := re.fullmatch(r"([0-9]{4})([0-9]{2})", cell, re.ASCII)):
        year, month = m[1], int(m[2])
    elif fmt == "Mon-YYYY" and (m := re.fullmatch(r"([A-Z][a-z]{2})-([0-9]{4})", cell, re.ASCII)):
        names = [n[:3] for n in _MONTHS]
        year, month = m[2], (names.index(m[1]) + 1 if m[1] in names else 0)
    elif fmt == "Month YYYY" and (m := re.fullmatch(r"([A-Z][a-z]+) ([0-9]{4})", cell, re.ASCII)):
        year, month = m[2], (_MONTHS.index(m[1]) + 1 if m[1] in _MONTHS else 0)
    if year is None or not 1 <= month <= 12:
        raise TransformFailed(cell)
    return f"{year}-{month:02d}"


def _month(cell: str, values: ValueRules) -> str:
    if isinstance(cell, XlsxNumber) and values.month_format != "YYYYMM":
        day = _serial(cell)[0]
        return f"{day.year:04d}-{day.month:02d}"
    return _month_grammar(str(cell), values)


def _month_of(cell: str, values: ValueRules) -> str:
    if isinstance(cell, XlsxNumber) and values.month_format == "YYYYMM":
        return _month_grammar(str(cell), values)
    try:
        moment = _datetime(cell, values)
    except TransformFailed:
        day = _date(cell, values)
        return f"{day.year:04d}-{day.month:02d}"
    if isinstance(moment, str):
        parsed = datetime.fromisoformat(moment.replace("Z", "+00:00"))
        moment = parsed.astimezone(ZoneInfo(values.timezone))
    return f"{moment.year:04d}-{moment.month:02d}"


def transform(type_: str, cell: str, values: ValueRules, *, scale: str | None = None) -> str:
    """Spec §2.4: the canonical text of `cell` under `type_`; `TransformFailed` when the cell does not read."""
    if type_ == "text":
        return cell
    if type_ == "number":
        return _number(cell, values, scale)
    if type_ == "date":
        return _date(cell, values).isoformat()
    if type_ == "datetime":
        moment = _datetime(cell, values)
        return moment if isinstance(moment, str) else moment.isoformat()
    if type_ == "month":
        return _month(cell, values)
    if type_ == "month_of":
        return _month_of(cell, values)
    raise ValueError(f"unknown type {type_}")


# --- reading (spec §2.2) ----------------------------------------------------------------------------------------

def _invisible(cell: str) -> bool:
    return any(ch not in _TEXT_CONTROLS and (ord(ch) in _CONTROL or unicodedata.category(ch) in _INVISIBLE_CATEGORIES)
               for ch in cell)


def split_file(layout: Layout, data: bytes) -> tuple[list[str], list[tuple[int, list[str]]]]:
    """Spec §2.2 `split_file`: the header row and the data rows (`(physical row, cells)`). A missing header row is
    `NATIVE_HEADER json`; the header's comparison is `read_rows`' first step."""
    rules = layout.file
    if rules.format == "xlsx":
        sheet_rows = xlsx_rows(data, rules.sheet or "")
        header: list[str] = []
        for number, cells in sheet_rows:
            if number == rules.header_row:
                header = list(cells)
        while header and header[-1] == "":
            header.pop()
        rows: list[tuple[int, list[str]]] = []
        for number, cells in sheet_rows:
            if number <= rules.header_row or all(c == "" for c in cells):
                continue
            cells = list(cells)
            while len(cells) > len(header) and cells[-1] == "":
                cells.pop()
            cells.extend([""] * (len(header) - len(cells)))
            rows.append((number, cells))
        return header, rows
    raw = bytes(data)
    if rules.encoding == "utf-8" and raw.startswith(_BOM):
        raw = raw[len(_BOM):]
    try:
        text = raw.decode(rules.encoding, errors="strict")
    except UnicodeDecodeError:
        raise CanonicalRefused("NATIVE_ENCODING", "json") from None
    reader = csv.reader(io.StringIO(text, newline=""), dialect="excel", delimiter=rules.delimiter, strict=True)
    all_rows: list[tuple[int, list[str]]] = []
    try:
        for cells in reader:
            all_rows.append((reader.line_num, cells))
    except csv.Error:
        raise CanonicalRefused("NATIVE_ROW", f"row.{reader.line_num}") from None
    if len(all_rows) < rules.header_row:
        raise CanonicalRefused("NATIVE_HEADER", "json")
    header = all_rows[rules.header_row - 1][1]
    return header, [(n, cells) for n, cells in all_rows[rules.header_row:] if cells]


def read_rows(layout: Layout, header: Sequence[str], rows: Sequence[tuple[int, Sequence[str]]], *, tenant_code: str,
              produced_at: str, provenance: str) -> NativeRead:
    """Spec §2.2 `read_rows`: the header compared first (`NATIVE_HEADER json`), then each row; a row problem refuses
    that row's index only."""
    if list(header) != [c.header for c in layout.columns]:
        raise CanonicalRefused("NATIVE_HEADER", "json")
    width = len(layout.columns)
    with_objects = _column_objects(layout)
    records: list[dict] = []
    numbers: list[int] = []
    refused: dict[int, tuple[str, str]] = {}

    def refuse(code: str, path: str) -> None:
        refused[len(records)] = (code, path)
        records.append({"format_version": 1})

    for n, cells in rows:
        numbers.append(n)
        if len(cells) != width:
            refuse("NATIVE_ROW", f"row.{n}")
            continue
        written = [(c, cell) for c, cell in zip(layout.columns, cells) if c.paths]
        bad = next((c for c, cell in written if isinstance(cell, XlsxBad)), None)
        if bad is not None:
            refuse("NATIVE_FORMAT", f"record.{bad.paths[0]}")
            continue
        if any(_invisible(cell) for _, cell in written):
            refuse("NATIVE_CHARACTER", f"row.{n}")
            continue
        record: dict = {"format_version": 1}
        wrote: set[str] = set()
        first_value: dict[str, str] = {}
        miss: str | None = None
        failed: str | None = None
        for column, cell in written:
            if cell == "":
                continue
            for path in column.paths:
                if path in column.maps:
                    value = column.maps[path].get(cell)
                    if value is None:
                        miss = miss or path
                        continue
                else:
                    try:
                        value = transform(column.types.get(path, "text"), cell, layout.values,
                                          scale=column.scales.get(path))
                    except TransformFailed:
                        failed = failed or path
                        continue
                _put(record, path, value)
                if path == column.paths[0]:
                    first_value[column.header] = value
                if (t := _top(path)) is not None:
                    wrote.add(t)
        if miss is not None:
            refuse("NATIVE_VALUE", f"record.{miss}")
            continue
        if failed is not None:
            refuse("NATIVE_FORMAT", f"record.{failed}")
            continue
        if layout.record_id_join:
            parts = [first_value.get(h) for h in layout.record_id_join]
            if any(p is not None and ":" in p for p in parts):
                refuse("NATIVE_FORMAT", "record.source_record_id")
                continue
            if all(p is not None for p in parts):
                _put(record, "source_record_id", ":".join(parts))
        if layout.version_digest:
            w = [first_value.get(c.header, "") for c, _ in written]
            _put(record, "source_version",
                 "r" + hashlib.sha256("\x1f".join(w).encode("utf-8")).hexdigest()[:16])
        for path, value in layout.constants.items():
            t = _top(path)
            if t is not None and t in with_objects and t not in wrote:
                continue  # rule C
            _put(record, path, value)
        records.append(record)
    obj = {"format_version": 1, "tenant_code": tenant_code, "source_type": layout.source_type,
           "source_system": layout.source_system, "provenance": provenance, "produced_at": produced_at,
           "records": records}
    return NativeRead(obj, tuple(numbers), MappingProxyType(refused))


def read_layout(layout: Layout, data: bytes, *, tenant_code: str, produced_at: str, provenance: str) -> NativeRead:
    """Spec §2.2 "Reading": `split_file` then `read_rows`. A whole-file problem raises `CanonicalRefused`; a row
    problem refuses that row's index only."""
    header, rows = split_file(layout, data)
    return read_rows(layout, header, rows, tenant_code=tenant_code, produced_at=produced_at, provenance=provenance)


def is_profile_shaped(layout: Layout) -> bool:
    """True when any 3A6 field differs from its default (such a layout is read, never rendered)."""
    return (layout.file != FileRules() or layout.values != ValueRules() or layout.record_id_join != ()
            or layout.version_digest or any(c.types or c.scales for c in layout.columns))


def _render_error(layout: Layout, path: str) -> ValueError:
    return ValueError(f"NATIVE_RENDER {layout.id} {path}")


def _cell(layout: Layout, column: Column, record: Mapping) -> str:
    plain = [p for p in column.paths if p not in column.maps]
    if plain:
        chosen, value = plain[0], _get(record, plain[0])
        if value is not None and not isinstance(value, str):
            raise _render_error(layout, chosen)
        cell = "" if value is None else value
    else:
        chosen = column.paths[0]
        value = _get(record, chosen)
        if value is None:
            cell = ""
        else:
            if not isinstance(value, str):
                raise _render_error(layout, chosen)
            inverse = {v: k for k, v in column.maps[chosen].items()}
            if value not in inverse:
                raise _render_error(layout, chosen)
            cell = inverse[value]
    for path in column.paths:
        found = _get(record, path)
        if cell == "":
            expected = None
        elif path in column.maps:
            expected = column.maps[path].get(cell)
            if expected is None:
                raise _render_error(layout, path)
        else:
            expected = cell
        if found != expected:
            raise _render_error(layout, path)
    return cell


def render_layout(layout: Layout, records: Sequence[Mapping]) -> bytes:
    """Spec §2.2 "Rendering": the header, then one row per record in order. A record the layout cannot carry
    exactly raises `ValueError("NATIVE_RENDER <layout id> <path>")` (an emulator bug, never an operator's). A
    profile-shaped layout raises `NATIVE_RENDER <id> profile` (3A6: emulators render the illustrative layouts only)."""
    if is_profile_shaped(layout):
        raise ValueError(f"NATIVE_RENDER {layout.id} profile")
    out = io.StringIO()
    writer = csv.writer(out, dialect="excel", lineterminator="\n")
    writer.writerow([c.header for c in layout.columns])
    for record in records:
        for path, value in layout.constants.items():
            found = _get(record, path)
            if found is not None and found != value:
                raise _render_error(layout, path)
        writer.writerow([_cell(layout, column, record) for column in layout.columns])
    return out.getvalue().encode("utf-8")


def _maps(path: str, pairs: Mapping[str, str]) -> Mapping[str, Mapping[str, str]]:
    return MappingProxyType({path: MappingProxyType(dict(pairs))})


BILLING = Layout(
    id="billing-illustrative-1",
    source_type="billing_export",
    source_system="illustrative-vending",
    columns=(
        Column("Invoice no", ("source_record_id",)),
        Column("Revision", ("source_version",)),
        Column("Site", ("site_code",)),
        Column("Account", ("subject.ref", "body.account_ref")),
        Column("Period start", ("clocks.effective_from",)),
        Column("Period end", ("clocks.effective_to",)),
        Column("Billing month", ("clocks.recognition_period",)),
        Column("kWh", ("quantity.value",)),
        Column("Amount", ("amount.value",)),
        Column("Currency", ("amount.currency",)),
        Column("Tariff", ("body.tariff_code",)),
    ),
    constants=MappingProxyType({"kind": "CHARGE", "subject.kind": "CUSTOMER", "quantity.unit": "kWh",
                                "body.line_type": "USAGE"}),
)

COLLECTIONS = Layout(
    id="collections-illustrative-1",
    source_type="mobile_money_statement",
    source_system="illustrative-mobile-money",
    columns=(
        Column("Transaction ID", ("source_record_id",)),
        Column("Site", ("site_code",)),
        Column("Paid at", ("clocks.occurred_at",)),
        Column("Month", ("clocks.recognition_period",)),
        Column("Payer", ("subject.ref", "body.payer_ref")),
        Column("Amount", ("amount.value",)),
        Column("Currency", ("amount.currency",)),
        Column("Status", ("status",), _maps("status", {"Settled": "COLLECTED", "Pending": "PAID_IN_TRANSIT"})),
    ),
    constants=MappingProxyType({"kind": "RECEIPT", "source_version": "1", "subject.kind": "CUSTOMER",
                                "body.method": "MOBILE_MONEY"}),
)

EXPENSES = Layout(
    id="expenses-illustrative-1",
    source_type="expense_ledger",
    source_system="illustrative-accounts",
    columns=(
        Column("Entry no", ("source_record_id",)),
        Column("Revision", ("source_version",)),
        Column("Site", ("site_code", "subject.ref")),
        Column("Date", ("clocks.occurred_at",)),
        Column("Month", ("clocks.recognition_period",)),
        Column("Category", ("body.category",), _maps("body.category", {"Diesel": "FUEL", "O&M": "OM",
                                                                        "Salaries": "STAFF"})),
        Column("Supplier", ("body.counterparty_ref",)),
        Column("Document", ("body.document_ref",)),
        Column("Litres", ("quantity.value",)),
        Column("Amount", ("amount.value",)),
        Column("Currency", ("amount.currency",)),
        Column("Status", ("status",), _maps("status", {"Invoiced": "INVOICED", "Paid": "PAID", "Quote": "QUOTE"})),
    ),
    constants=MappingProxyType({"kind": "EXPENSE", "subject.kind": "SITE", "quantity.unit": "L"}),
)

BUDGET = Layout(
    id="budget-illustrative-1",
    source_type="budget_workbook",
    source_system="illustrative-budget",
    columns=(
        Column("Line ID", ("source_record_id",)),
        Column("Revision", ("source_version",)),
        Column("Site", ("site_code",)),
        Column("Month", ("clocks.recognition_period",)),
        Column("Line", ("body.line_ref", "body.factor_id"),
               _maps("body.factor_id", {"revenue": "revenue", "diesel_cost": "fuel_cost", "om": "om", "staff": "staff",
                                        "billed_kwh": "billed_kwh", "diesel_l": "diesel_l",
                                        "tariff_usd_per_kwh": "tariff", "diesel_usd_per_l": "diesel_price"})),
        Column("Value", ("body.value",)),
        Column("Currency", ("body.currency",)),
        Column("Budget version", ("body.version_ref",)),
    ),
    constants=MappingProxyType({"kind": "BUDGET_LINE"}),
)

LAYOUTS: Mapping[str, Layout] = MappingProxyType({x.id: x for x in (BILLING, COLLECTIONS, EXPENSES, BUDGET)})

for _layout in LAYOUTS.values():
    check_layout(_layout)
