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
import io
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Sequence

from assetops_contracts.canonical import SOURCE_TYPES, CanonicalRefused

_BOM = b"\xef\xbb\xbf"
_OBJECTS = ("subject", "amount", "quantity", "body", "clocks")
#: D-3A3.9: control characters a cell may not hold (tab, LF and CR are text).
_CONTROL = frozenset([*range(0x00, 0x09), 0x0B, 0x0C, *range(0x0E, 0x20), 0x7F])
_EMPTY: Mapping[str, Mapping[str, str]] = MappingProxyType({})


@dataclass(frozen=True)
class Column:
    header: str  # the exact header cell
    paths: tuple[str, ...]  # canonical record paths the cell fills
    maps: Mapping[str, Mapping[str, str]] = _EMPTY  # path -> {native value: canonical value}


@dataclass(frozen=True)
class Layout:
    id: str  # reader id, also commercial_upload.reader
    source_type: str  # a key of SOURCE_TYPES
    source_system: str
    columns: tuple[Column, ...]
    constants: Mapping[str, str]  # path -> value, written under rule C
    personal: frozenset[tuple[str, str]] = frozenset()  # extra (path, class) for 3A2's pseudonymise


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
    """Import check: a known source type, and each map one to one (`NATIVE_LAYOUT <id> <path>`)."""
    if layout.source_type not in SOURCE_TYPES:
        raise ValueError(f"NATIVE_LAYOUT {layout.id} source_type")
    for column in layout.columns:
        for path, mapping in column.maps.items():
            if path not in column.paths or len(set(mapping.values())) != len(mapping):
                raise ValueError(f"NATIVE_LAYOUT {layout.id} {path}")


def _column_objects(layout: Layout) -> frozenset[str]:
    return frozenset(t for c in layout.columns for p in c.paths if (t := _top(p)) is not None)


def read_layout(layout: Layout, data: bytes, *, tenant_code: str, produced_at: str, provenance: str) -> NativeRead:
    """Spec §2.2 "Reading", steps 1 to 7. A whole-file problem raises `CanonicalRefused`; a row problem refuses
    that row's index only."""
    raw = bytes(data)
    if raw.startswith(_BOM):
        raw = raw[len(_BOM):]
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise CanonicalRefused("NATIVE_ENCODING", "json") from None
    reader = csv.reader(io.StringIO(text, newline=""), dialect="excel", strict=True)
    header = [c.header for c in layout.columns]
    with_objects = _column_objects(layout)
    records: list[dict] = []
    rows: list[int] = []
    refused: dict[int, tuple[str, str]] = {}
    try:
        first = next(reader, None)
        if first != header:
            raise CanonicalRefused("NATIVE_HEADER", "json")
        for cells in reader:
            if not cells:
                continue
            n = reader.line_num
            index = len(records)
            rows.append(n)
            if len(cells) != len(header):
                records.append({"format_version": 1})
                refused[index] = ("NATIVE_ROW", f"row.{n}")
                continue
            if any(ord(ch) in _CONTROL for cell in cells for ch in cell):
                records.append({"format_version": 1})
                refused[index] = ("NATIVE_CHARACTER", f"row.{n}")
                continue
            record: dict = {"format_version": 1}
            wrote: set[str] = set()
            miss: str | None = None
            for column, cell in zip(layout.columns, cells):
                if cell == "":
                    continue
                for path in column.paths:
                    if path in column.maps:
                        value = column.maps[path].get(cell)
                        if value is None:
                            miss = miss or path
                            continue
                    else:
                        value = cell
                    _put(record, path, value)
                    if (t := _top(path)) is not None:
                        wrote.add(t)
            if miss is not None:
                records.append({"format_version": 1})
                refused[index] = ("NATIVE_VALUE", f"record.{miss}")
                continue
            for path, value in layout.constants.items():
                t = _top(path)
                if t is not None and t in with_objects and t not in wrote:
                    continue  # rule C
                _put(record, path, value)
            records.append(record)
    except csv.Error:
        raise CanonicalRefused("NATIVE_ROW", f"row.{reader.line_num}") from None
    obj = {"format_version": 1, "tenant_code": tenant_code, "source_type": layout.source_type,
           "source_system": layout.source_system, "provenance": provenance, "produced_at": produced_at,
           "records": records}
    return NativeRead(obj, tuple(rows), MappingProxyType(refused))


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
    exactly raises `ValueError("NATIVE_RENDER <layout id> <path>")` (an emulator bug, never an operator's)."""
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
