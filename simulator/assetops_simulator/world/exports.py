"""3A3 (spec `specs/3A3-emulators-contract-test/spec.md` §2.5; D-3A3.4) and DD2.1 (DD spec §5.1; D-DD.48): emulated
native exports, one file per key for every month of the history and the view's accounting period.

For each mini-grid tenant (RC5), four native CSV files in the illustrative layouts of `assetops_contracts.native`:
billing (forty customers per Site, kWh split evenly, remainder to the first customers), mobile-money collections
(customers paid in order), the expense ledger (400-litre fuel notes, then DS1b's O&M and staff lines) and the budget
(node lines from the plan and prices, then DS1b's O&M and staff lines). Rows are ordered by (month, Site, row).

Billed kWh, revenue, collections and fuel are nodes of the world's structure (`structures.MINI_GRID`), evaluated every
month from that month's leaves through the manifest's `factor_map` (`NODES`, "node of `structures.MINI_GRID`,
evaluated on the month's leaves (D-DD.48)"). For the accounting period the evaluated node must equal the node the
period records, or the emulator stops (`EMU_NODE`). The manifest is not read here: `NODES` is a module table with a
parity test against the manifest (`simulator/tests/world/test_dd2_nodes.py`).

Totals must equal the nodes per Site or the emulator stops (`EMU_REVENUE`, `EMU_COLLECTIONS`, `EMU_FUEL`); a price
or quantity that is not whole in its unit stops it too (`EMU_PRICE`, `EMU_QUANTITY`). ESTIMATED coverage writes
nothing (GAP-1). Every field the manifest holds that no file carries is listed in `unwritten` with its reason; DS1b's
rows for fields this module did write are dropped. DS1b's ADJUSTMENT, METER_ASSIGNMENT and TARIFF_SCHEDULE records
are staged as canonical JSON (D-DD.54); every other DS1b record of a tenant off this path is listed. These files reach
the store only through 3A2's intake (D-3A3.1); nothing here touches a store.

Standard library, `assetops_contracts` (`canonical`, `native`) and the world modules only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from assetops_contracts.canonical import CanonicalRefused, parse_batch, parse_record, to_canonical_json
from assetops_contracts.native import LAYOUTS, render_layout

from .leaves import MONEY_LEAVES
from .months import days_in, parse_month, period_end
from .records import PASS_THROUGH, build_records, money_text
from .statements import figures_from_rows, statements_bytes
from .view import ManifestView

KEYS = ("billing", "collections", "expenses", "budget")
CUSTOMERS = 40
DELIVERY_L = 400
SOURCE_VERSION = "2"
#: The collections layout holds `source_version` as a constant (`collections-illustrative-1`), so a receipt keeps it.
RECEIPT_SOURCE_VERSION = LAYOUTS["collections-illustrative-1"].constants["source_version"]
VERSION_REF = "budget-2026-v1"
#: Budget lines this module writes: (factor ID, line label, source, field, form). Order of spec §2.5.
BUDGET_LINES = (
    ("revenue", "revenue", "plan", "revenue", "money"),
    ("fuel_cost", "diesel_cost", "plan", "diesel_cost", "money"),
    ("billed_kwh", "billed_kwh", "plan", "billed_kwh", "whole"),
    ("diesel_l", "diesel_l", "plan", "diesel_l", "whole"),
    ("tariff", "tariff_usd_per_kwh", "plan", "tariff_usd_per_kwh", "price"),
    ("diesel_price", "diesel_usd_per_l", "plan", "diesel_usd_per_l", "price"),
)
#: D-3A3.13: a budget unit price is the plan's own, plan money divided by plan quantity (never `tenant.prices`).
PRICE_FROM_PLAN = {"tariff": ("revenue", "billed_kwh"), "diesel_price": ("diesel_cost", "diesel_l")}
BUDGET_ORDER = ("revenue", "fuel_cost", "om", "staff", "billed_kwh", "diesel_l", "tariff", "diesel_price")
EXPENSE_ORDER = ("FUEL", "OM", "STAFF")
#: D-DD.53: a note that a disorder test dates is cut first, at its date; the rest fall on the cycle days at 10:00.
#: (test id, tenant, Site name, date, litres). The parity test reads the manifest's `disorder_tests`.
DATED_NOTES = (("OOO-1", "lakeside-power", "Kobo", "2026-10-26", 400),)
CYCLE_DAYS = (1, 8, 15, 22, 29)
NOTE_HOUR = 10
#: D-DD.54: the DS1b kinds staged as `<tenant>.<source_type>.json`.
STAGED_KINDS = frozenset({"METER_ASSIGNMENT", "TARIFF_SCHEDULE", "ADJUSTMENT"})

# --- D-DD.48: node of `structures.MINI_GRID`, evaluated on the month's leaves ------------------------------------------
#: (node, the manifest's expression text, the same expression). Dependency order. Leaves are the names of `factor_map`.
NODES = {
    "MINI_GRID": (
        ("metered_kwh", "delivered_kwh - technical_loss_kwh - unexplained_loss_kwh",
         lambda v: v["delivered_kwh"] - v["technical_loss_kwh"] - v["unexplained_loss_kwh"]),
        ("billed_kwh", "metered_kwh - adjustments_kwh - unmapped_kwh",
         lambda v: v["metered_kwh"] - v["adjustments_kwh"] - v["unmapped_kwh"]),
        ("revenue", "billed_kwh * tariff + productive_kwh * productive_tariff",
         lambda v: v["billed_kwh"] * v["tariff"] + v["productive_kwh"] * v["productive_tariff"]),
        ("collected", "revenue - in_transit - outstanding",
         lambda v: v["revenue"] - v["in_transit"] - v["outstanding"]),
        ("diesel_l", "necessary_l + candidate_l + unexplained_l + extra_l",
         lambda v: v["necessary_l"] + v["candidate_l"] + v["unexplained_l"] + v["extra_l"]),
        ("fuel_cost", "diesel_l * diesel_price", lambda v: v["diesel_l"] * v["diesel_price"]),
    ),
}
#: Leaves whose `factor_map` text ends in `| 0`: absent in the record reads 0. `delivered_kwh` and `necessary_l` are
#: required. `productive_kwh` and `extra_l` are the constant 0.
ZERO_LEAVES = frozenset({"technical_loss_kwh", "unexplained_loss_kwh", "adjustments_kwh", "unmapped_kwh", "in_transit",
                         "outstanding", "candidate_l", "unexplained_l"})
CONSTANT_LEAVES = {"productive_kwh": Decimal(0), "extra_l": Decimal(0)}
RECORD_LEAVES = ("delivered_kwh", "technical_loss_kwh", "unexplained_loss_kwh", "adjustments_kwh", "unmapped_kwh",
                 "in_transit", "outstanding", "necessary_l", "candidate_l", "unexplained_l")
#: Node -> the field the period record carries it as (checked in the accounting period, D-DD.48).
RECORDED = {"actual": (("metered_kwh", "metered_kwh"), ("billed_kwh", "billed_kwh"), ("revenue", "revenue"),
                       ("collected", "collected"), ("diesel_l", "diesel_l"), ("fuel_cost", "diesel_cost")),
            "plan": (("billed_kwh", "billed_kwh"), ("revenue", "revenue"), ("diesel_l", "diesel_l"),
                     ("fuel_cost", "diesel_cost"))}

NOT_ON_PATH_VERTICAL = "NOT_ON_PATH_VERTICAL"
NOT_IN_LAYOUT = "NOT_IN_LAYOUT"
PLAN_FIELD_ABSENT = "PLAN_FIELD_ABSENT"
PLAN_PRICE_UNDEFINED = "PLAN_PRICE_UNDEFINED"
SITE_NOT_IN_TENANT = "SITE_NOT_IN_TENANT"
NOT_IN_HISTORY = "NOT_IN_HISTORY"
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
    #: (file name, bytes): DS1b canonical JSON, staged (D-DD.54), by name.
    staged: tuple[tuple[str, bytes], ...] = ()
    #: (file name, bytes): `<tenant>.statements.json` (DD spec §5.4), by name.
    statements: tuple[tuple[str, bytes], ...] = ()


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


def _leaves(record: dict, money_in_cents: bool) -> dict[str, Decimal]:
    """The leaves of `structures.MINI_GRID` that a record carries, read as `factor_map` reads them (D-DD.48):
    the first present alternative, else 0 for a zero leaf, else absent. History money is integer cents."""
    out: dict[str, Decimal] = {leaf: Decimal(0) for leaf in ZERO_LEAVES} | dict(CONSTANT_LEAVES)
    for leaf in RECORD_LEAVES:
        for field in PASS_THROUGH["MINI_GRID"][leaf]:
            if field in record:
                value = _number(record[field])
                out[leaf] = value / 100 if money_in_cents and field in MONEY_LEAVES else value
                break
        else:
            if leaf not in ZERO_LEAVES:
                out.pop(leaf, None)
    return out


def evaluate_mini_grid(record: dict, *, money_in_cents: bool, tariff: Decimal, diesel_price: Decimal,
                       productive_tariff: Decimal) -> dict[str, Decimal]:
    """The nodes of `structures.MINI_GRID` that the record's leaves reach, exact (D-DD.48). A node whose required leaf
    is absent, and every node depending on it, is left out."""
    values = _leaves(record, money_in_cents) | {"tariff": tariff, "diesel_price": diesel_price,
                                                "productive_tariff": productive_tariff}
    nodes: dict[str, Decimal] = {}
    for name, _, fn in NODES["MINI_GRID"]:
        try:
            nodes[name] = fn(values | nodes)
        except KeyError:
            continue
    return nodes


class _Site:
    def __init__(self, tenant: dict, site: dict, month: str, zone: ZoneInfo, currency: str, *, actual: dict,
                 plan: dict, coverage: dict, recorded: dict | None, money_in_cents: bool) -> None:
        self.tenant = tenant["tenant"]
        self.prices = tenant.get("prices", {})
        self.name = site["site"]
        self.code = site["code"]
        self.cov = coverage
        self.month = month
        self.zone = zone
        self.currency = currency
        # D-DD.48: every book figure is a node evaluated on this month's leaves; October's must equal its record.
        productive = self.prices.get("productive_tariff_usd_per_kwh")
        if productive is None:
            raise ValueError(f"EMU_PRICE {self.where()} productive_tariff_usd_per_kwh")
        self.price_cents("tariff_usd_per_kwh")
        self.price_cents("diesel_usd_per_l")
        prices = {"tariff": _number(self.price("tariff_usd_per_kwh")),
                  "diesel_price": _number(self.price("diesel_usd_per_l")), "productive_tariff": _number(productive)}
        self.leaves = _leaves(actual, money_in_cents)
        self.n = evaluate_mini_grid(actual, money_in_cents=money_in_cents, **prices)
        evaluated_plan = evaluate_mini_grid(plan, money_in_cents=money_in_cents, **prices)
        if recorded is not None:
            for side, nodes in (("actual", self.n), ("plan", evaluated_plan)):
                for node, field in RECORDED[side]:
                    held = recorded.get(side, {}).get(field)
                    if node in nodes and held is not None and _number(held) != nodes[node]:
                        raise ValueError(f"EMU_NODE {self.where()} {month} {'plan.' if side == 'plan' else ''}{node}")
        #: the plan lines this module writes, under the names of the plan record (the budget lines' fields)
        self.p = {field: evaluated_plan[node] for node, field in
                  (("revenue", "revenue"), ("fuel_cost", "diesel_cost"), ("billed_kwh", "billed_kwh"),
                   ("diesel_l", "diesel_l")) if node in evaluated_plan}

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
    billed = _whole(s.n["billed_kwh"], f"EMU_QUANTITY {s.where()} billed_kwh")
    tariff = s.price_cents("tariff_usd_per_kwh")
    out = []
    for i in range(1, CUSTOMERS + 1):
        kwh = billed // CUSTOMERS + (1 if i <= billed % CUSTOMERS else 0)
        out.append((f"{s.code}-C-{i:04d}", kwh, kwh * tariff))
    revenue = s.n["revenue"] * 100
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
    collected = _cents(s.n["collected"], error)
    in_transit = _cents(s.leaves["in_transit"], error)
    outstanding = _cents(s.leaves["outstanding"], error)
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
                "source_version": RECEIPT_SOURCE_VERSION, "site_code": s.code, "subject": {"kind": "CUSTOMER", "ref": ref},
                "clocks": {"occurred_at": occurred, "recognition_period": s.month},
                "amount": {"value": money_text(pay), "currency": s.currency}, "status": status,
                "body": {"payer_ref": ref, "method": "MOBILE_MONEY"}}))
    return out


def _notes(s: _Site, litres: int) -> list[tuple[int, int, bool]]:
    """D-DD.53: (day, litres, carries the remainder). Dated notes first (cut first, so numbered first), at their dates; the rest in 400 L notes on the
    cycle days, the last carrying the remainder."""
    dated = [(int(date[8:10]), note_l) for _, tenant, site, date, note_l in DATED_NOTES
             if (tenant, site) == (s.tenant, s.name) and date[:7] == s.month]
    left = litres - sum(note_l for _, note_l in dated)
    if left < 0:
        raise ValueError(f"EMU_FUEL {s.where()}")
    cut = []
    while left > DELIVERY_L:
        cut.append(DELIVERY_L)
        left -= DELIVERY_L
    if left > 0:
        cut.append(left)
    notes = [(min(CYCLE_DAYS[i % len(CYCLE_DAYS)], days_in(s.month)), note_l, i == len(cut) - 1 and note_l < DELIVERY_L)
             for i, note_l in enumerate(cut)]
    return [(day, note_l, False) for day, note_l in dated] + notes


def _fuel_records(s: _Site) -> list[dict]:
    litres = _whole(s.n["diesel_l"], f"EMU_QUANTITY {s.where()} diesel_l")
    price = s.price_cents("diesel_usd_per_l")
    notes = _notes(s, litres)
    if sum(note_l for _, note_l, _ in notes) * price != s.n["fuel_cost"] * 100:
        raise ValueError(f"EMU_FUEL {s.where()}")
    out = []
    for k, (day, amount_l, remainder) in enumerate(notes, start=1):
        name = f"fuel-{k}"
        record_id = s.record_id("actual", name)
        document = f"{record_id} remainder {amount_l} L" if remainder else record_id
        out.append(s.checked(name, {
            "format_version": 1, "kind": "EXPENSE", "source_record_id": record_id, "source_version": SOURCE_VERSION,
            "site_code": s.code, "subject": {"kind": "SITE", "ref": s.code},
            "clocks": {"occurred_at": s.at(day, NOTE_HOUR), "recognition_period": s.month},
            "quantity": {"value": str(amount_l), "unit": "L"},
            "amount": {"value": money_text(amount_l * price), "currency": s.currency}, "status": "INVOICED",
            "body": {"counterparty_ref": "fuel-supplier", "category": "FUEL", "document_ref": document}}))
    return out


def _budget_records(s: _Site, unwritten: list) -> tuple[list[dict], set[str]]:
    out = []
    written: set[str] = set()
    for factor, line, source, field, form in BUDGET_LINES:
        if form == "price":
            money_field, qty_field = PRICE_FROM_PLAN[factor]
            money, qty = s.p.get(money_field), s.p.get(qty_field)
            if money is None or qty is None:
                unwritten.append((s.tenant, s.code, s.month, "plan", field, PLAN_FIELD_ABSENT))
                continue
            if _number(qty) == 0:
                unwritten.append((s.tenant, s.code, s.month, "plan", field, PLAN_PRICE_UNDEFINED))
                continue
            error = f"EMU_PLAN_PRICE {s.where()} {factor}"
            price = _cents(_number(money) / _number(qty), error)
            if price * _number(qty) != _number(money) * 100:
                raise ValueError(error)
            value = Decimal(price) / 100
        else:
            value = s.p.get(field)
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


def _site_month(tenant: dict, site: dict, month: str, history: dict, accounting_period: str, zone: ZoneInfo,
                currency: str) -> _Site:
    """One Site's month from the period (October, dollars) or the generated history (cents)."""
    period = site.get("period", {})
    if month == accounting_period:
        return _Site(tenant, site, month, zone, currency, actual=period.get("actual", {}),
                     plan=period.get("plan", {}), coverage=period.get("coverage", {}), recorded=period,
                     money_in_cents=False)
    block = history["tenants"][tenant["tenant"]][site["site"]][month]
    return _Site(tenant, site, month, zone, currency, actual=block.get("actual", {}), plan=block.get("plan", {}),
                 coverage=block.get("coverage", {}), recorded=None, money_in_cents=True)


def _staged(batch_json: dict, kept: list[dict]) -> tuple[str, bytes]:
    obj = dict(batch_json, records=kept)
    try:
        parsed = parse_batch(obj)
    except CanonicalRefused as refused:
        raise ValueError(f"EMU_FORMAT staged {refused.code} {refused.path}") from None
    return f"{obj['tenant_code']}.{obj['source_type']}.json", to_canonical_json(parsed)


def build_exports(view: dict, history: dict, *, months: list[str] | tuple[str, ...] | None = None) -> ExportsResult:
    """The emulated native files, the staged DS1b JSON, the statements and the unwritten list for a view and its
    generated history (spec §2.5; DD spec §5.1). `months` defaults to every history month plus the accounting period."""
    view = ManifestView.from_document(view)
    records = build_records(view, history)
    accounting = view["accounting_period"]
    known = [*history["meta"]["months"], accounting]
    months = list(known) if months is None else sorted(months)
    for month in months:
        if month not in known:
            raise ValueError(f"EMU_MONTH {month}")
    zone = ZoneInfo(view["timezone_default"])
    currency = view["currency"]
    categories = _map_values("expenses-illustrative-1", "body.category")
    factors = _map_values("budget-illustrative-1", "body.factor_id")
    files: list[ExportFile] = []
    staged: list[tuple[str, bytes]] = []
    statements: list[tuple[str, bytes]] = []
    unwritten: list[tuple[str, ...]] = []
    for tenant in view.get("tenants", []):
        name = tenant["tenant"]
        on_path = tenant.get("vertical") == "MINI_GRID"
        if not on_path:
            unwritten.append((name, "*", "*", "*", "*", NOT_ON_PATH_VERTICAL))
        # DS1b's records of the months, by (key, month, Site): EXPENSE to expenses, BUDGET_LINE to budget; the staged
        # kinds to JSON (D-DD.54); every other record is listed.
        ds1b: dict[tuple[str, str, str], list[dict]] = {}
        for batch in records.batches:
            if batch.batch.tenant_code != name:
                continue
            batch_json = json.loads(to_canonical_json(batch))
            kept = []
            for record in batch_json["records"]:
                month = record.get("clocks", {}).get("recognition_period")
                if month not in months:
                    continue
                site = record.get("site_code", "")
                kind = record["kind"]
                body = record.get("body", {})
                if kind in STAGED_KINDS:
                    kept.append(record)
                elif not on_path:
                    unwritten.append((name, site, month, kind, record["source_record_id"], NOT_ON_PATH_VERTICAL))
                elif kind == "EXPENSE" and body.get("category") in categories:
                    ds1b.setdefault(("expenses", month, site), []).append(record)
                elif kind == "BUDGET_LINE" and body.get("factor_id") in factors:
                    ds1b.setdefault(("budget", month, site), []).append(record)
                else:
                    unwritten.append((name, site, month, kind, record["source_record_id"], NOT_IN_LAYOUT))
            if kept:
                staged.append(_staged(batch_json, kept))
        if not on_path:
            continue
        out: dict[str, list[dict]] = {key: [] for key in KEYS}
        written: set[tuple[str, str, str, str, str]] = set()
        unpaid: set[tuple[str, str]] = set()
        for month in months:
            for site in sorted(tenant.get("sites", []), key=lambda x: x["code"]):
                s = _site_month(tenant, site, month, history, accounting, zone, currency)
                if s.cov.get("revenue") != "ESTIMATED" and "billed_kwh" in s.n and "revenue" in s.n \
                        and "collected" in s.n:
                    charges = _charges(s)
                    out["billing"] += _charge_records(s, charges)
                    out["collections"] += _receipt_records(s, charges)
                    for field in ("billed_kwh", "revenue", "collected", "in_transit"):
                        written.add((name, s.code, month, "actual", field))
                    unpaid.add((s.code, month))
                else:
                    for node in ("billed_kwh", "revenue", "collected"):
                        if node not in s.n:
                            unwritten.append((name, s.code, month, "actual", node, NOT_IN_HISTORY))
                if s.cov.get("diesel") != "ESTIMATED" and "diesel_l" in s.n and "fuel_cost" in s.n:
                    out["expenses"] += _fuel_records(s)
                    for field in ("diesel_l", "diesel_cost"):
                        written.add((name, s.code, month, "actual", field))
                else:
                    for node in ("diesel_l", "fuel_cost"):
                        if node not in s.n:
                            unwritten.append((name, s.code, month, "actual", node, NOT_IN_HISTORY))
                out["expenses"] += sorted(ds1b.get(("expenses", month, s.code), []),
                                          key=lambda r: EXPENSE_ORDER.index(r["body"]["category"]))
                budget, fields = _budget_records(s, unwritten)
                budget += ds1b.get(("budget", month, s.code), [])
                out["budget"] += sorted(budget, key=lambda r: BUDGET_ORDER.index(r["body"]["factor_id"]))
                written |= {(name, s.code, month, "plan", field) for field in fields}
        codes = {x["code"] for x in tenant.get("sites", [])}
        for (_, month, site_code), kept in ds1b.items():  # every kept DS1b record is written or listed
            if site_code not in codes:
                unwritten += [(name, site_code, month, r["kind"], r["source_record_id"], SITE_NOT_IN_TENANT)
                              for r in kept]
        for row in records.unwritten:
            tenant_name, code, row_month, side, field, reason = row
            if tenant_name != name or row_month not in months \
                    or (tenant_name, code, row_month, side, field) in written:
                continue
            if side == "actual" and field == "outstanding" and (code, row_month) in unpaid:
                reason = AS_UNPAID_CHARGES
            unwritten.append((tenant_name, code, row_month, side, field, reason))
        for key in KEYS:
            if out[key]:
                layout_id = _layout_id(key)
                data = render_layout(LAYOUTS[layout_id], out[key])
                files.append(ExportFile(name, key, layout_id, tuple(out[key]), data))
        # DD spec §5.4: one statement per history month, each figure the sum of that month's emitted rows. The
        # accounting period stays in the walk definition (Kisiwa's disagreement).
        history_months = [m for m in months if m != accounting]
        figures = figures_from_rows(
            out["billing"], [r for r in out["expenses"] if r["body"]["category"] == "FUEL"], history_months)
        if figures:
            statements.append((f"{name}.statements.json", statements_bytes(name, currency, "fuel_cost", figures)))
    return ExportsResult(files=tuple(files), unwritten=tuple(sorted(unwritten)), staged=tuple(sorted(staged)),
                         statements=tuple(sorted(statements)))
