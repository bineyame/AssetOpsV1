"""DD2.5 (spec `specs/DD-demo-data/spec.md` §5.4; D-DD.28): the management-account statements file.

`{"schema": "assetops.world-statements/1", "tenant", "statements": [{"period", "currency", "revenue", "fuel_cost" |
"energy_cost", "source_ref"}]}`: one statement per month, each figure the sum of that month's emitted rows. Pure: rows
in, bytes out. Nothing here reads a store.
"""

from __future__ import annotations

import calendar
from decimal import Decimal

from .canonical import file_bytes
from .months import parse_month

SCHEMA = "assetops.world-statements/1"
COST_KEYS = ("fuel_cost", "energy_cost")


def source_ref(month: str) -> str:
    year, number = parse_month(month)
    return f"Emulated management accounts, {calendar.month_name[number]} {year}, final"


def _money(value: Decimal) -> str:
    return f"{value:.2f}"


def statements_document(tenant: str, currency: str, cost_key: str, figures: dict[str, tuple[Decimal, Decimal]]) -> dict:
    """`figures`: month -> (revenue, cost). One statement per month, in month order."""
    if cost_key not in COST_KEYS:
        raise ValueError(f"STATEMENT_COST_KEY {cost_key}")
    return {"schema": SCHEMA, "tenant": tenant, "statements": [
        {"period": month, "currency": currency, "revenue": _money(revenue), cost_key: _money(cost),
         "source_ref": source_ref(month)} for month, (revenue, cost) in sorted(figures.items())]}


def statements_bytes(tenant: str, currency: str, cost_key: str, figures: dict[str, tuple[Decimal, Decimal]]) -> bytes:
    return file_bytes(statements_document(tenant, currency, cost_key, figures))


def sum_by_month(rows: list[dict]) -> dict[str, Decimal]:
    """The amounts of emitted rows (`amount.value`), by recognition month."""
    out: dict[str, Decimal] = {}
    for r in rows:
        month = r["clocks"]["recognition_period"]
        out[month] = out.get(month, Decimal(0)) + Decimal(r["amount"]["value"])
    return out


def figures_from_rows(revenue_rows: list[dict], cost_rows: list[dict], months: list[str]) -> dict[str, tuple[Decimal, Decimal]]:
    """Revenue and cost per month from emitted rows. A month with neither is absent; a month with one is refused."""
    revenue, cost = sum_by_month(revenue_rows), sum_by_month(cost_rows)
    out = {}
    for month in months:
        if month not in revenue and month not in cost:
            continue
        if month not in revenue or month not in cost:
            raise ValueError(f"STATEMENT_INCOMPLETE {month}")
        out[month] = (revenue[month], cost[month])
    return out
