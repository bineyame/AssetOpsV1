"""3A3 (spec `specs/3A3-emulators-contract-test/spec.md` §2.5; D-3A3.4): emulated native exports for the deep-dive month.

For each mini-grid tenant (RC5) and the view's accounting period only, four native CSV files in the illustrative
layouts of `assetops_contracts.native`: billing (forty customers per Site, kWh split evenly, remainder to the first
customers), mobile-money collections (customers paid in order), the expense ledger (400-litre fuel deliveries, then
DS1b's O&M and staff lines) and the budget (node lines from the plan and prices, then DS1b's O&M and staff lines).

Totals must equal the manifest per Site or the emulator stops (`EMU_REVENUE`, `EMU_COLLECTIONS`, `EMU_FUEL`); a price
or quantity that is not whole in its unit stops it too (`EMU_PRICE`, `EMU_QUANTITY`). ESTIMATED coverage writes
nothing (GAP-1). Every field the manifest holds that no file carries is listed in `unwritten` with its reason; DS1b's
rows for fields this module did write are dropped. These files reach the store only through 3A2's intake
(D-3A3.1); nothing here touches a store.

Standard library, `assetops_contracts` (`canonical`, `native`) and the world modules only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from assetops_contracts.canonical import CanonicalRefused, parse_record, to_canonical_json
from assetops_contracts.native import LAYOUTS, render_layout

from .months import days_in, parse_month, period_end
from .records import build_records, money_text
from .view import ManifestView

KEYS = ("billing", "collections", "expenses", "budget")
CUSTOMERS = 40
DELIVERY_L = 400
SOURCE_VERSION = "1"
VERSION_REF = "budget-2026-v1"
#: Budget lines this module writes: (factor ID, line label, source, field, form). Order of spec §2.5.
BUDGET_LINES = (
    ("revenue", "revenue", "plan", "revenue", "money"),
    ("fuel_cost", "diesel_cost", "plan", "diesel_cost", "money"),
    ("billed_kwh", "billed_kwh", "plan", "billed_kwh", "whole"),
    ("diesel_l", "diesel_l", "plan", "diesel_l", "whole"),
    ("tariff", "tariff_usd_per_kwh", "prices", "tariff_usd_per_kwh", "price"),
    ("diesel_price", "diesel_usd_per_l", "prices", "diesel_usd_per_l", "price"),
)
BUDGET_ORDER = ("revenue", "fuel_cost", "om", "staff", "billed_kwh", "diesel_l", "tariff", "diesel_price")
EXPENSE_ORDER = ("FUEL", "OM", "STAFF")

NOT_ON_PATH_VERTICAL = "NOT_ON_PATH_VERTICAL"
NOT_IN_LAYOUT = "NOT_IN_LAYOUT"
PLAN_FIELD_ABSENT = "PLAN_FIELD_ABSENT"
AS_UNPAID_CHARGES = "AS_UNPAID_CHARGES"


@dataclass(frozen=True)
class ExportFile:
    tenant: str
    key: str
    layout_id: str
    records: tuple[dict, ...]
    data: bytes


@dataclass(frozen=True)
class ExportsResult:
    files: tuple[ExportFile, ...]
    unwritten: tuple[tuple[str, ...], ...]


def file_name(f: ExportFile) -> str:
    return f"{f.tenant}.{f.key}.csv"


def _layout_id(key: str) -> str:
    return f"{key}-illustrative-1"


def _number(v: object) -> Decimal:
    return Decimal(str(v))


def _cents(v: object, error: str) -> int:
    scaled = _number(v) * 100
    if scaled != scaled.to_integral_value():
        raise ValueError(error)
    return int(scaled)


def _whole(v: object, error: str) -> int:
    number = _number(v)
    if number != number.to_integral_value():
        raise ValueError(error)
    return int(number)


class _Site:
    def __init__(self, tenant: dict, site: dict, month: str, zone: ZoneInfo, currency: str) -> None:
        self.tenant = tenant["tenant"]
        self.prices = tenant.get("prices", {})
        self.name = site["site"]
        self.code = site["code"]
        period = site.get("period", {})
        self.a = period.get("actual", {})
        self.p = period.get("plan", {})
        self.cov = period.get("coverage", {})
        self.month = month
        self.zone = zone
        self.currency = currency

    def where(self) -> str:
        return f"{self.tenant}/{self.code}"

    def price(self, name: str) -> object | None:
        table = self.prices.get(name)
        return table.get(self.name) if isinstance(table, dict) else None

    def price_cents(self, name: str) -> int:
        value = self.price(name)
        if value is None:
            raise ValueError(f"EMU_PRICE {self.where()} {name}")
        return _cents(value, f"EMU_PRICE {self.where()} {name}")

    def record_id(self, side: str, name: str) -> str:
        return f"gen:{self.code}:{self.month}:{side}:{name}"

    def at(self, day: int, hour: int, minute: int = 0) -> str:
        year, number = parse_month(self.month)
        return datetime(year, number, day, hour, minute, tzinfo=self.zone).isoformat()

    def checked(self, name: str, record: dict) -> dict:
        try:
            parse_record(record)
        except CanonicalRefused:
            raise ValueError(f"EMU_FORMAT {self.where()} {name}") from None
        return record


def _charges(s: _Site) -> list[tuple[str, int, int]]:
    """Each customer's (ref, kWh, cents)."""
    billed = _whole(s.a["billed_kwh"], f"EMU_QUANTITY {s.where()} billed_kwh")
    tariff = s.price_cents("tariff_usd_per_kwh")
    out = []
    for i in range(1, CUSTOMERS + 1):
        kwh = billed // CUSTOMERS + (1 if i <= billed % CUSTOMERS else 0)
        out.append((f"{s.code}-C-{i:04d}", kwh, kwh * tariff))
    revenue = _number(s.a["revenue"]) * 100
    if sum(c for _, _, c in out) != revenue:
        raise ValueError(f"EMU_REVENUE {s.where()}")
    return out


def _charge_records(s: _Site, charges: list[tuple[str, int, int]]) -> list[dict]:
    first = f"{s.month}-01"
    after = (period_end(s.month) + timedelta(days=1)).isoformat()
    out = []
    for i, (ref, kwh, cents) in enumerate(charges, start=1):
        name = f"charge-{i:04d}"
        out.append(s.checked(name, {
            "format_version": 1, "kind": "CHARGE", "source_record_id": s.record_id("actual", name),
            "source_version": SOURCE_VERSION, "site_code": s.code, "subject": {"kind": "CUSTOMER", "ref": ref},
            "clocks": {"effective_from": first, "effective_to": after, "recognition_period": s.month},
            "quantity": {"value": str(kwh), "unit": "kWh"},
            "amount": {"value": money_text(cents), "currency": s.currency},
            "body": {"account_ref": ref, "line_type": "USAGE", "tariff_code": "T-RES"}}))
    return out


def _receipt_records(s: _Site, charges: list[tuple[str, int, int]]) -> list[dict]:
    error = f"EMU_COLLECTIONS {s.where()}"
    collected = _cents(s.a.get("collected", 0), error)
    in_transit = _cents(s.a.get("in_transit", 0), error)
    outstanding = _cents(s.a.get("outstanding", 0), error)
    revenue = sum(c for _, _, c in charges)
    if collected + in_transit + outstanding != revenue or min(collected, in_transit, outstanding) < 0:
        raise ValueError(error)
    owed = [c for _, _, c in charges]
    last_day = period_end(s.month).day
    out: list[dict] = []
    position = 0
    for status, left in (("COLLECTED", collected), ("PAID_IN_TRANSIT", in_transit)):
        while left > 0:
            while owed[position] == 0:
                position += 1
            i = position + 1
            pay = min(owed[position], left)
            owed[position] -= pay
            left -= pay
            occurred = s.at(1 + (i - 1) % 28, 10) if status == "COLLECTED" else s.at(last_day, 19)
            name = f"receipt-{len(out) + 1:04d}"
            ref = charges[position][0]
            out.append(s.checked(name, {
                "format_version": 1, "kind": "RECEIPT", "source_record_id": s.record_id("actual", name),
                "source_version": SOURCE_VERSION, "site_code": s.code, "subject": {"kind": "CUSTOMER", "ref": ref},
                "clocks": {"occurred_at": occurred, "recognition_period": s.month},
                "amount": {"value": money_text(pay), "currency": s.currency}, "status": status,
                "body": {"payer_ref": ref, "method": "MOBILE_MONEY"}}))
    return out


def _fuel_records(s: _Site) -> list[dict]:
    litres = _whole(s.a["diesel_l"], f"EMU_QUANTITY {s.where()} diesel_l")
    price = s.price_cents("diesel_usd_per_l")
    deliveries = []
    left = litres
    while left > DELIVERY_L:
        deliveries.append(DELIVERY_L)
        left -= DELIVERY_L
    if left > 0:
        deliveries.append(left)
    total = sum(d * price for d in deliveries)
    if total != _number(s.a["diesel_cost"]) * 100:
        raise ValueError(f"EMU_FUEL {s.where()}")
    m = len(deliveries)
    out = []
    for k, amount_l in enumerate(deliveries, start=1):
        name = f"fuel-{k}"
        record_id = s.record_id("actual", name)
        out.append(s.checked(name, {
            "format_version": 1, "kind": "EXPENSE", "source_record_id": record_id, "source_version": SOURCE_VERSION,
            "site_code": s.code, "subject": {"kind": "SITE", "ref": s.code},
            "clocks": {"occurred_at": s.at(1 + (k - 1) * (days_in(s.month) // m), 9),
                       "recognition_period": s.month},
            "quantity": {"value": str(amount_l), "unit": "L"},
            "amount": {"value": money_text(amount_l * price), "currency": s.currency}, "status": "INVOICED",
            "body": {"counterparty_ref": "fuel-supplier", "category": "FUEL", "document_ref": record_id}}))
    return out


def _budget_records(s: _Site, unwritten: list) -> tuple[list[dict], set[str]]:
    out = []
    written: set[str] = set()
    for factor, line, source, field, form in BUDGET_LINES:
        value = s.p.get(field) if source == "plan" else s.price(field)
        if value is None:
            unwritten.append((s.tenant, s.code, s.month, "plan", field, PLAN_FIELD_ABSENT))
            continue
        body = {"factor_id": factor, "value": "", "version_ref": VERSION_REF, "line_ref": line}
        if form == "money":
            body["value"] = money_text(_cents(value, f"EMU_PRICE {s.where()} {field}"))
            body["currency"] = s.currency
        elif form == "whole":
            body["value"] = str(_whole(value, f"EMU_QUANTITY {s.where()} {field}"))
        else:
            body["value"] = f"{_number(value):.2f}"
            body["currency"] = s.currency
        out.append(s.checked(factor, {
            "format_version": 1, "kind": "BUDGET_LINE", "source_record_id": s.record_id("plan", factor),
            "source_version": SOURCE_VERSION, "site_code": s.code, "clocks": {"recognition_period": s.month},
            "body": body}))
        written.add(field)
    return out, written


def _map_values(layout_id: str, path: str) -> frozenset[str]:
    for column in LAYOUTS[layout_id].columns:
        if path in column.maps:
            return frozenset(column.maps[path].values())
    return frozenset()


def build_exports(view: dict, history: dict) -> ExportsResult:
    """The emulated native files and the unwritten list for a view and its generated history (spec §2.5)."""
    view = ManifestView.from_document(view)
    records = build_records(view, history)
    month = view["accounting_period"]
    zone = ZoneInfo(view["timezone_default"])
    currency = view["currency"]
    categories = _map_values("expenses-illustrative-1", "body.category")
    factors = _map_values("budget-illustrative-1", "body.factor_id")
    files: list[ExportFile] = []
    unwritten: list[tuple[str, ...]] = []
    in_scope = set()
    for tenant in view.get("tenants", []):
        if tenant.get("vertical") != "MINI_GRID":
            unwritten.append((tenant["tenant"], "*", "*", "*", "*", NOT_ON_PATH_VERTICAL))
            continue
        name = tenant["tenant"]
        in_scope.add(name)
        # DS1b's records of the month, by Site: EXPENSE to expenses, BUDGET_LINE to budget.
        ds1b: dict[tuple[str, str], list[dict]] = {}
        for batch in records.batches:
            if batch.batch.tenant_code != name:
                continue
            for record in json.loads(to_canonical_json(batch))["records"]:
                if record.get("clocks", {}).get("recognition_period") != month:
                    continue
                site = record.get("site_code", "")
                kind = record["kind"]
                body = record.get("body", {})
                if kind == "EXPENSE" and body.get("category") in categories:
                    ds1b.setdefault(("expenses", site), []).append(record)
                elif kind == "BUDGET_LINE" and body.get("factor_id") in factors:
                    ds1b.setdefault(("budget", site), []).append(record)
                else:
                    unwritten.append((name, site, month, kind, record["source_record_id"], NOT_IN_LAYOUT))
        out: dict[str, list[dict]] = {key: [] for key in KEYS}
        written: set[tuple[str, str, str, str, str]] = set()
        unpaid: set[str] = set()
        for site in sorted(tenant.get("sites", []), key=lambda x: x["code"]):
            s = _Site(tenant, site, month, zone, currency)
            if s.cov.get("revenue") != "ESTIMATED" and "billed_kwh" in s.a and "revenue" in s.a:
                charges = _charges(s)
                out["billing"] += _charge_records(s, charges)
                out["collections"] += _receipt_records(s, charges)
                for field in ("billed_kwh", "revenue", "collected", "in_transit"):
                    written.add((name, s.code, month, "actual", field))
                unpaid.add(s.code)
            if s.cov.get("diesel") != "ESTIMATED" and "diesel_l" in s.a and "diesel_cost" in s.a:
                out["expenses"] += _fuel_records(s)
                for field in ("diesel_l", "diesel_cost"):
                    written.add((name, s.code, month, "actual", field))
            out["expenses"] += sorted(ds1b.get(("expenses", s.code), []),
                                      key=lambda r: EXPENSE_ORDER.index(r["body"]["category"]))
            budget, fields = _budget_records(s, unwritten)
            budget += ds1b.get(("budget", s.code), [])
            out["budget"] += sorted(budget, key=lambda r: BUDGET_ORDER.index(r["body"]["factor_id"]))
            written |= {(name, s.code, month, "plan", field) for field in fields}
        for row in records.unwritten:
            tenant_name, code, row_month, side, field, reason = row
            if tenant_name != name or row_month != month or (tenant_name, code, row_month, side, field) in written:
                continue
            if side == "actual" and field == "outstanding" and code in unpaid:
                reason = AS_UNPAID_CHARGES
            unwritten.append((tenant_name, code, row_month, side, field, reason))
        for key in KEYS:
            if out[key]:
                layout_id = _layout_id(key)
                data = render_layout(LAYOUTS[layout_id], out[key])
                files.append(ExportFile(name, key, layout_id, tuple(out[key]), data))
    return ExportsResult(files=tuple(files), unwritten=tuple(sorted(unwritten)))
