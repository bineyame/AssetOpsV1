"""DS1b: the generator's canonical record writers (spec `specs/DS1b-canonical-writers/spec.md`).

Writes the month cost lines (EXPENSE), the customer-compensation credit notes (ADJUSTMENT) and the operator's
budget lines (BUDGET_LINE) as canonical v1 batches, for the history months and October. October is read from the
manifest view's `period` records, the history months from the generated history (money in cents). Nothing else
is read. Every batch passes `parse_batch`; the same inputs give the same bytes.

The evidence word follows the path: these records stand in for an operator's export, so every batch is
`source-emulated` (D-DS1B.5). An estimate is never written as a record (D-DS1B.7), and a budget line is written
only from a leaf's own field (R1). Every present field not written is returned with its reason.

Standard library, `assetops_contracts.canonical` and the world modules only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from types import MappingProxyType
from zoneinfo import ZoneInfo

from assetops_contracts.canonical import LEAF_FACTORS, BatchResult, CanonicalRefused, parse_batch

from .leaves import MONEY_LEAVES
from .months import parse_month, period_end
from .view import ManifestView

# Tenant vertical -> structure key (spec §2). EV_DEPOT is the demonstration's only EV business model.
STRUCTURE_KEY = MappingProxyType({"MINI_GRID": "MINI_GRID", "COLD_CHAIN": "COLD_CHAIN", "EV_DEPOT": "EV_DEPOT_CAPTIVE"})


@dataclass(frozen=True)
class Writer:
    """One actual-side month record (spec §2.1).

    `code` is the EXPENSE category or the ADJUSTMENT reason code; `ref` the EXPENSE counterparty or the
    ADJUSTMENT approver. Both references are source text, never a named person or counterparty (R5).
    """

    kind: str
    code: str
    ref: str
    source_type: str


_OM = Writer("EXPENSE", "OM", "om-contractor", "expense_ledger")
_STAFF = Writer("EXPENSE", "STAFF", "payroll", "expense_ledger")

# Spec §2.1: record field -> writer. The field is also the leaf's factor ID.
ACTUAL_WRITERS = MappingProxyType({
    "MINI_GRID": MappingProxyType({
        "om": _OM,
        "staff": _STAFF,
        "liability": Writer("ADJUSTMENT", "CUSTOMER_COMPENSATION", "finance-lead", "billing_export"),
    }),
    "COLD_CHAIN": MappingProxyType({
        "maint": _OM,
        "staff": _STAFF,
        "liability": Writer("ADJUSTMENT", "CUSTOMER_COMPENSATION", "finance-lead", "customer_invoicing"),
    }),
    "EV_DEPOT_CAPTIVE": MappingProxyType({
        "maintenance": _OM,
    }),
})

# Spec §2.2: leaf -> the record fields its `factor_map` expression passes through as whole `|` alternatives, in
# order. The first field is the leaf's own line; a later one is a fallback (R1).
PASS_THROUGH = MappingProxyType({
    "MINI_GRID": MappingProxyType({
        "delivered_kwh": ("delivered_kwh", "billed_kwh"),
        "technical_loss_kwh": ("technical_loss_kwh", "expected_technical_loss_kwh"),
        "unexplained_loss_kwh": ("unexplained_kwh",),
        "adjustments_kwh": ("adjustments_kwh",),
        "unmapped_kwh": ("unbilled_mapping_kwh",),
        "in_transit": ("in_transit",),
        "outstanding": ("outstanding",),
        "necessary_l": ("necessary_l", "diesel_l"),
        "candidate_l": ("candidate_l",),
        "unexplained_l": ("unexplained_l",),
        "om": ("om",),
        "staff": ("staff",),
        "hours_per_day": ("reduced_hours_per_day",),
        "major_assets": ("major_assets",),
        "unserved_critical_kwh": ("unserved_critical_kwh",),
        "customer_hours_interrupted": ("customer_hours_interrupted",),
        "field_visits": ("field_visits",),
        "liability": ("liability",),
        "dawn_days_below": ("dawn_days_below_safeguard",),
    }),
    "COLD_CHAIN": MappingProxyType({
        "crate_days": ("crate_days",),
        "staff": ("staff",),
        "maint": ("maint",),
        "liability": ("liability",),
        "outstanding": ("outstanding",),
        "excursion_crates": ("excursion_crates",),
        "excursion_days": ("excursion_days",),
        "batches_exposed": ("batches_exposed",),
        "cooling_minutes_unavailable": ("cooling_minutes_unavailable",),
    }),
    "EV_DEPOT_CAPTIVE": MappingProxyType({
        "nights_in_period": ("nights",),
        "peak_kwh": ("peak_kwh",),
        "kwh_2200_2400": ("kwh_2200_2400", "offpeak_kwh", "kwh"),
        "kwh_0000_0500": ("kwh_0000_0500",),
        "max_kw": ("max_kw",),
        "maintenance": ("maintenance",),
        "spare_bus_nights": ("spare_bus_nights",),
    }),
})

# R4: record fields the `factor_map` reads only inside an expression, never as a whole alternative.
READ_IN_EXPRESSION = MappingProxyType({
    "MINI_GRID": frozenset({"reduced_capacity_from"}),
    "COLD_CHAIN": frozenset({"backup_unproven_from", "kwh", "unproven_nights_rota_covered",
                             "unproven_nights_without_stock"}),
    "EV_DEPOT_CAPTIVE": frozenset({"charger_out_from", "failed_chargers", "short_nights_from"}),
})

SOURCE_ORDER = ("expense_ledger", "billing_export", "customer_invoicing", "budget_workbook")
SOURCE_SYSTEM = "assetops-world-generator"
PROVENANCE = "source-emulated"
SOURCE_VERSION = "1"
VERSION_REF = "budget-2026-v1"

NOT_A_MONTH_RECORD = "NOT_A_MONTH_RECORD"
ESTIMATED_NOT_RECEIVED = "ESTIMATED_NOT_RECEIVED"
ZERO_NO_ROW = "ZERO_NO_ROW"
NOT_OWN_LINE = "NOT_OWN_LINE"
READ_IN_AN_EXPRESSION = "READ_IN_AN_EXPRESSION"
NOT_READ_BY_A_LEAF = "NOT_READ_BY_A_LEAF"

_DECIMAL_TEXT = re.compile(r"-?[0-9]+(\.[0-9]+)?([eE][-+]?[0-9]+)?", re.ASCII)
_DATE_TEXT = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", re.ASCII)


@dataclass(frozen=True)
class RecordsResult:
    batches: tuple[BatchResult, ...]
    unwritten: tuple[tuple[str, str, str, str, str, str], ...]


def batch_file_name(b: BatchResult) -> str:
    return f"{b.batch.tenant_code}.{b.batch.source_type}.json"


def _refuse(text: str) -> ValueError:
    return ValueError(text)


def money_text(cents: int) -> str:
    """Cents as decimal text with two places (P10)."""
    if cents < 0:
        return "-" + money_text(-cents)
    return f"{cents // 100}.{cents % 100:02d}"


def _check_tables() -> None:
    """R11: a money field maps to a money leaf, and a field mapped to a money leaf is a money field."""
    for key, leaves in PASS_THROUGH.items():
        for leaf, fields in leaves.items():
            for field in fields:
                if (field in MONEY_LEAVES) != LEAF_FACTORS[leaf].money:
                    raise _refuse(f"DS1B_MONEY_MISMATCH {key} {field}")
    for key, writers in ACTUAL_WRITERS.items():
        for field in writers:
            if (field in MONEY_LEAVES) != LEAF_FACTORS[field].money:
                raise _refuse(f"DS1B_MONEY_MISMATCH {key} {field}")


def _as_of(view: dict) -> date:
    text = view.get("as_of")
    if not isinstance(text, str) or _DATE_TEXT.fullmatch(text) is None:
        raise _refuse("DS1B_AS_OF")
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise _refuse("DS1B_AS_OF") from None


class _Month:
    """One Site's month: its two sides and its coverage, and how its numbers become text."""

    def __init__(self, tenant: str, code: str, month: str, sides: dict, coverage: dict, october: bool) -> None:
        self.tenant = tenant
        self.code = code
        self.month = month
        self.sides = sides
        self.coverage = coverage
        self.october = october

    def where(self, side: str, field: str) -> str:
        return f"{self.tenant}/{self.code}/{self.month} {side} {field}"

    def cents(self, side: str, field: str) -> int:
        value = self.sides[side][field]
        if not self.october:
            if type(value) is not int:
                raise _refuse(f"DS1B_NUMBER {self.where(side, field)}")
            return value
        scaled = Fraction(self._decimal(side, field)) * 100
        if scaled.denominator != 1:
            raise _refuse(f"DS1B_MONEY {self.where(side, field)}")
        return int(scaled)

    def text(self, side: str, field: str) -> str:
        """A written field as canonical decimal text: money as cents with two places."""
        if field in MONEY_LEAVES:
            return money_text(self.cents(side, field))
        value = self.sides[side][field]
        if not self.october:
            if type(value) is not int:
                raise _refuse(f"DS1B_NUMBER {self.where(side, field)}")
            return str(value)
        return format(self._decimal(side, field), "f")

    def _decimal(self, side: str, field: str) -> Decimal:
        value = self.sides[side][field]
        if type(value) is int:
            return Decimal(value)
        if not isinstance(value, str) or _DECIMAL_TEXT.fullmatch(value) is None:
            raise _refuse(f"DS1B_NUMBER {self.where(side, field)}")
        try:
            number = Decimal(value)
        except InvalidOperation:
            raise _refuse(f"DS1B_NUMBER {self.where(side, field)}") from None
        if not number.is_finite():
            raise _refuse(f"DS1B_NUMBER {self.where(side, field)}")
        return number


def _months(view: dict, history: dict, tenant: dict, site: dict) -> list[_Month]:
    out = []
    blocks = history["tenants"][tenant["tenant"]][site["site"]]
    for month in sorted(history["meta"]["months"]):
        block = blocks[month]
        sides = {"actual": block.get("actual", {}), "plan": block.get("plan", {})}
        out.append(_Month(tenant["tenant"], site["code"], month, sides, block.get("coverage", {}), False))
    period = site.get("period", {})
    sides = {"actual": period.get("actual", {}), "plan": period.get("plan", {})}
    out.append(_Month(tenant["tenant"], site["code"], view["accounting_period"], sides,
                      period.get("coverage", {}), True))
    return out


def _record_id(m: _Month, side: str, name: str) -> str:
    return f"gen:{m.code}:{m.month}:{side}:{name}"


def _actual(m: _Month, key: str, zone: ZoneInfo, currency: str, out: dict, unwritten: list) -> None:
    writers = ACTUAL_WRITERS[key]
    for field in sorted(m.sides["actual"]):
        writer = writers.get(field)
        if writer is None:
            unwritten.append((m.tenant, m.code, m.month, "actual", field, NOT_A_MONTH_RECORD))
            continue
        if m.coverage.get(field) == "ESTIMATED":
            unwritten.append((m.tenant, m.code, m.month, "actual", field, ESTIMATED_NOT_RECEIVED))
            continue
        cents = m.cents("actual", field)
        record_id = _record_id(m, "actual", field)
        record = {
            "format_version": 1,
            "kind": writer.kind,
            "source_record_id": record_id,
            "source_version": SOURCE_VERSION,
            "site_code": m.code,
            "subject": {"kind": "SITE", "ref": m.code},
        }
        if writer.kind == "EXPENSE":
            occurred = datetime.combine(period_end(m.month), time(17, 0), tzinfo=zone)
            record["clocks"] = {"occurred_at": occurred.isoformat(), "recognition_period": m.month}
            record["amount"] = {"value": money_text(cents), "currency": currency}
            record["status"] = "PAID"
            record["body"] = {"counterparty_ref": writer.ref, "category": writer.code, "document_ref": record_id}
        else:
            if cents == 0:
                unwritten.append((m.tenant, m.code, m.month, "actual", field, ZERO_NO_ROW))
                continue
            year, number = parse_month(m.month)
            record["clocks"] = {"effective_from": date(year, number, 1).isoformat(), "recognition_period": m.month}
            record["amount"] = {"value": money_text(-cents), "currency": currency}
            record["body"] = {"reason_code": writer.code, "authorised_by_ref": writer.ref, "document_ref": record_id}
        out[writer.source_type].append(((m.code, m.month, "actual", field), record))


def _plan(m: _Month, key: str, currency: str, out: dict, unwritten: list) -> None:
    leaves = PASS_THROUGH[key]
    own = {fields[0]: leaf for leaf, fields in leaves.items()}
    later = {field for fields in leaves.values() for field in fields[1:]}
    for field in sorted(m.sides["plan"]):
        leaf = own.get(field)
        if leaf is None:
            if field in later:
                reason = NOT_OWN_LINE
            elif field in READ_IN_EXPRESSION[key]:
                reason = READ_IN_AN_EXPRESSION
            else:
                reason = NOT_READ_BY_A_LEAF
            unwritten.append((m.tenant, m.code, m.month, "plan", field, reason))
            continue
        body = {"factor_id": leaf, "value": m.text("plan", field), "version_ref": VERSION_REF, "line_ref": field}
        if any(dimension == "MONEY" for dimension, _ in LEAF_FACTORS[leaf].unit.exponents):
            body["currency"] = currency
        record = {
            "format_version": 1,
            "kind": "BUDGET_LINE",
            "source_record_id": _record_id(m, "plan", leaf),
            "source_version": SOURCE_VERSION,
            "site_code": m.code,
            "clocks": {"recognition_period": m.month},
            "body": body,
        }
        out["budget_workbook"].append(((m.code, m.month, "plan", leaf), record))


def _batch(tenant: str, source_type: str, rows: list, produced_at: str) -> BatchResult:
    obj = {
        "format_version": 1,
        "tenant_code": tenant,
        "source_type": source_type,
        "source_system": SOURCE_SYSTEM,
        "provenance": PROVENANCE,
        "produced_at": produced_at,
        "records": [record for _, record in sorted(rows, key=lambda row: row[0])],
    }
    try:
        result = parse_batch(obj)
    except CanonicalRefused as refused:
        raise _refuse(f"DS1B_FORMAT {refused.code} {refused.path}") from None
    for outcome in result.outcomes:
        if isinstance(outcome, CanonicalRefused):
            raise _refuse(f"DS1B_FORMAT {outcome.code} {outcome.path}")
    return result


def build_records(view: dict, history: dict) -> RecordsResult:
    """The canonical batches and the unwritten list for a view and its generated history (spec §2, §3)."""
    _check_tables()
    view = ManifestView.from_document(view)
    as_of = _as_of(view)
    if view["accounting_period"] in history["meta"]["months"]:
        # The view's period would be written twice (a history month and the period), so the batch's own duplicate
        # check would refuse it; refuse it here, before any row is built, so the unwritten list never double-lists.
        raise _refuse(f"DS1B_FORMAT PERIOD_IN_HISTORY {view['accounting_period']}")
    zone = ZoneInfo(view["timezone_default"])
    currency = view["currency"]
    produced_at = datetime.combine(as_of, time(6, 0), tzinfo=zone).isoformat()
    batches: list[BatchResult] = []
    unwritten: list[tuple[str, str, str, str, str, str]] = []
    for tenant in view.get("tenants", []):
        key = STRUCTURE_KEY.get(tenant.get("vertical"))
        if key is None:
            raise _refuse(f"DS1B_VERTICAL {tenant['tenant']}")
        out: dict[str, list] = {source_type: [] for source_type in SOURCE_ORDER}
        for site in tenant.get("sites", []):
            for m in _months(view, history, tenant, site):
                _actual(m, key, zone, currency, out, unwritten)
                _plan(m, key, currency, out, unwritten)
        for source_type in SOURCE_ORDER:
            if out[source_type]:
                batches.append(_batch(tenant["tenant"], source_type, out[source_type], produced_at))
    return RecordsResult(batches=tuple(batches), unwritten=tuple(sorted(unwritten)))
