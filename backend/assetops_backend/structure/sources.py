"""3B3: leaves from today's product (spec §3; D-3B3.3, D-3B3.4, D-3B3.11, D-3B3.12; P1-P4, P6, P10).

`SOURCE_STATE` states, per structure key and leaf, the honest source of 20 Nov 2026. A leaf rests on its own record
(`PROVIDED`) or on a person's declared value of the same quantity, labelled (`ASSUMED`); a measurement of a different
quantity fills nothing. Every `Missing` built here names the row's own `filled_by` record and passes `blocks=()`
(the evaluator fills them, P6). Each provider reuses today's function; nothing is copied.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Protocol
from uuid import UUID
from zoneinfo import ZoneInfo

from assetops_backend.chain.outcomes import AUTHORITY, month_sum
from assetops_backend.chain.strategies.graded_verdict import day_grades
from assetops_backend.chain.ports import SiteRef
from assetops_backend.chain.read import local_days
from assetops_backend.structure import registry as _registry
from assetops_backend.structure.check import StructureError
from assetops_backend.structure.evaluate import ORIGIN_UNKNOWN, Coverage, LeafValue, Missing
from assetops_backend.structure.read import SITE_TYPE_TO_STRUCTURE

PROVIDED, ASSUMED = "PROVIDED", "ASSUMED"
HELD_NOT_CALCULATED, NOT_CONNECTED, OPTION_ONLY = "HELD_NOT_CALCULATED", "NOT_CONNECTED", "OPTION_ONLY"
#: 4b2 (D-4B.6, D-4B.14): read from the leaf's own records; the labelled assumption only when none is held.
PROVIDED_ELSE_ASSUMED = "PROVIDED_ELSE_ASSUMED"
STATES = (PROVIDED, ASSUMED, HELD_NOT_CALCULATED, NOT_CONNECTED, OPTION_ONLY, PROVIDED_ELSE_ASSUMED)

#: D-3B3.3, D-3B3.11: the state of every leaf on 20 Nov 2026. A later slice changes one row and adds its provider.
SOURCE_STATE: Mapping[str, Mapping[str, str]] = MappingProxyType({
    "MINI_GRID": MappingProxyType({
        "delivered_kwh": HELD_NOT_CALCULATED,       # feeder demand readings; no monthly measure built
        "technical_loss_kwh": NOT_CONNECTED,
        "unexplained_loss_kwh": NOT_CONNECTED,
        "adjustments_kwh": NOT_CONNECTED,
        "unmapped_kwh": NOT_CONNECTED,
        "tariff": NOT_CONNECTED,
        "productive_kwh": PROVIDED,                 # its own record, CHARGE (productive class), now has an intake
        "productive_tariff": ASSUMED,
        "in_transit": PROVIDED,
        "outstanding": PROVIDED,
        "necessary_l": HELD_NOT_CALCULATED,         # dispatch gives minutes, not litres
        "candidate_l": HELD_NOT_CALCULATED,
        "unexplained_l": HELD_NOT_CALCULATED,       # the night-window residual is not a monthly litre
        "extra_l": OPTION_ONLY,
        "diesel_price": PROVIDED_ELSE_ASSUMED,
        "battery_throughput_kwh": OPTION_ONLY,
        "wear_rate": NOT_CONNECTED,
        "om": PROVIDED,
        "staff": PROVIDED,
        "collection_cost": OPTION_ONLY,
        "reduced_days": HELD_NOT_CALCULATED,        # work cases
        "hours_per_day": HELD_NOT_CALCULATED,       # work cases
        "major_assets": NOT_CONNECTED,
        "unserved_critical_kwh": PROVIDED,
        "customer_hours_interrupted": HELD_NOT_CALCULATED,  # backup hours
        "field_visits": HELD_NOT_CALCULATED,        # site-visit records
        "liability": NOT_CONNECTED,
        "period_days": PROVIDED,
        "standby_kw": NOT_CONNECTED,
        "lost_unit_kw": NOT_CONNECTED,
        "dawn_days_below": HELD_NOT_CALCULATED,     # battery state of charge
    }),
})

#: 4b2 (spec §3.2, D-4B.1): the nodes a record states, and their state. `CommercialLeafSource` serves the PROVIDED ones.
STATED_STATE: Mapping[str, Mapping[str, str]] = MappingProxyType({
    "MINI_GRID": MappingProxyType({"revenue": PROVIDED, "fuel_cost": PROVIDED}),
})
#: 4b2: the PROVIDED leaves whose only provider is `structure.money.CommercialLeafSource`. Read alone (no commercial
#: source wired), `ProductLeafSource` gives them NOT_CONNECTED naming their `filled_by`.
COMMERCIAL_LEAVES = frozenset({"productive_kwh", "in_transit", "outstanding", "om", "staff"})

#: D-3B3.11: the literal words of each ASSUMED leaf (the product never reads the manifest).
ASSUMPTION_WORDS: Mapping[str, str] = MappingProxyType({
    "productive_tariff": "Declared productive-use price per kWh, not a tariff schedule",
    "diesel_price": "Declared diesel price per litre, not a fuel invoice",
})
#: The assumption key each ASSUMED price leaf reads (P2).
PRICE_KEYS: Mapping[str, str] = MappingProxyType({
    "productive_tariff": "productive_use_price_per_kwh",
    "diesel_price": "diesel_price_per_litre",
})
CRITICAL_MEASURE = "critical_served"
NEUTRAL_SOURCE = "option-only neutral"


@dataclass(frozen=True)
class ReadContext:
    site: SiteRef
    month: str  # Site-local YYYY-MM
    known_at: datetime | None  # the snapshot cutoff and the assumption recorded_at (P3)


class LeafSource(Protocol):
    def leaf(self, ctx: ReadContext, factor_id: str) -> LeafValue: ...


class StatedSource(Protocol):
    """4b1 (spec §2.5): the value a record states for a node with `stated_by`."""

    def stated(self, ctx: ReadContext, factor_id: str) -> LeafValue: ...


#: `window_price(tenant, site, key, start, end, known_at) -> fuel_cost.PriceSelection` (P2).
WindowPrice = Callable[[UUID, UUID, str, datetime, datetime, "datetime | None"], Any]


def month_window(month: str, tz: str) -> tuple[datetime, datetime, date, date]:
    """P3: `[local midnight of day 1, local midnight of day 1 of the next month)` in the Site's zone, as UTC
    instants, with the first and last Site-local day."""
    year, mon = int(month[:4]), int(month[5:7])
    zone = ZoneInfo(tz)
    first = date(year, mon, 1)
    nxt = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)
    lo = datetime(first.year, first.month, 1, tzinfo=zone).astimezone(timezone.utc)
    hi = datetime(nxt.year, nxt.month, 1, tzinfo=zone).astimezone(timezone.utc)
    return lo, hi, first, nxt - timedelta(days=1)


def _absent(fb: Any, cause: str, note: str | None = None, coverage: Coverage | None = None) -> LeafValue:
    return LeafValue(None, "NOT_AVAILABLE", (), coverage, Missing(fb.kind, fb.family, cause, None, (), fb.words, None,
                                                                  note), None)


class ProductLeafSource:
    """Today's product sources (spec §3): the calendar, the `critical_served` snapshots and the declared prices."""

    def __init__(self, snapshot_reader: Any, window_price: WindowPrice, now: Callable[[], datetime]) -> None:
        self._snapshots = snapshot_reader
        self._window_price = window_price
        self._now = now  # "has the month closed" when no known_at is given

    def leaf(self, ctx: ReadContext, factor_id: str) -> LeafValue:
        key = SITE_TYPE_TO_STRUCTURE.get(ctx.site.site_type)
        if key is None:
            raise StructureError("STRUCTURE_NOT_DECLARED", str(ctx.site.site_type), ctx.site.site_code)
        row = _registry.REGISTRIES[key].row(factor_id)
        state = SOURCE_STATE[key][factor_id]
        fb = row.filled_by
        if state == OPTION_ONLY:
            return LeafValue(row.neutral, "NEUTRAL", (NEUTRAL_SOURCE,), None, None, None)
        if state == HELD_NOT_CALCULATED:
            return _absent(fb, "NOT_CALCULATED_YET")
        if state == NOT_CONNECTED or (state == PROVIDED and factor_id in COMMERCIAL_LEAVES):
            return _absent(fb, "NOT_CONNECTED")
        if factor_id == "period_days":
            return self._period_days(ctx)
        if factor_id == "unserved_critical_kwh":
            return self._unserved_critical(ctx, fb)
        if factor_id in PRICE_KEYS and state in (ASSUMED, PROVIDED_ELSE_ASSUMED):  # 4b2: the fallback's answer
            return self._price(ctx, factor_id, fb)
        raise StructureError("STRUCTURE_LEAF_INPUT", key, factor_id)  # a state with no provider: a code bug

    @staticmethod
    def _period_days(ctx: ReadContext) -> LeafValue:
        lo, hi, _, _ = month_window(ctx.month, ctx.site.timezone)
        days = len(local_days(lo, hi, ctx.site.timezone))
        return LeafValue(Decimal(days), "DERIVED", ("calendar",), None, None, None)

    def _unserved_critical(self, ctx: ReadContext, fb: Any) -> LeafValue:
        """D-3B3.12: a value only for a closed month with every expected day COMPLETE; coverage is always kept."""
        lo, hi, first, last = month_window(ctx.month, ctx.site.timezone)
        rows = self._snapshots.latest(ctx.site.tenant_id, ctx.site.site_id, first, last, [CRITICAL_MEASURE],
                                      ctx.known_at)
        value, days, unstated = month_sum(rows, CRITICAL_MEASURE, first, last, "unserved_kwh")
        # D-3B3.17: a COMPLETE day that states no value is unknown, so it is not covered.
        grades = day_grades(tuple(r for r in rows if r.measure == CRITICAL_MEASURE
                                  and AUTHORITY.get(r.evidence_class, False) and first <= r.local_day <= last))
        unknown = [d for d in unstated if grades.get(d) == "COMPLETE"]
        covered = days.complete - len(unknown)
        coverage = Coverage(covered, days.expected, MappingProxyType({
            "COMPLETE": days.complete, "PARTIAL": days.partial, "LOW": days.low, "NO_DATA": days.no_data,
            "NOT_EXPECTED": days.not_expected, "PENDING": days.pending}))
        if days.expected == 0:  # P4: no reading role declared over the month
            return _absent(fb, "NOT_CONNECTED", coverage=coverage)
        closed = hi <= (ctx.known_at if ctx.known_at is not None else self._now())
        if not closed or covered != days.expected or value is None:
            note = f"VALUE_NOT_STATED:{len(unknown)}" if closed and unknown and days.complete == days.expected \
                else None
            return _absent(fb, "NOT_RECEIVED", note=note, coverage=coverage)
        return LeafValue(value, "MEASURED", (f"snapshot:{CRITICAL_MEASURE}",), coverage, None, None,
                         (ORIGIN_UNKNOWN,))

    def _price(self, ctx: ReadContext, factor_id: str, fb: Any) -> LeafValue:
        """D-3B3.11: the operator's declared price of the same quantity, carried as a labelled assumption."""
        lo, hi, _, _ = month_window(ctx.month, ctx.site.timezone)
        selection = self._window_price(ctx.site.tenant_id, ctx.site.site_id, PRICE_KEYS[factor_id], lo, hi,
                                       ctx.known_at)
        if selection.state != "PRICED":
            return _absent(fb, "NOT_CONNECTED", note=selection.reason)
        missing = Missing(fb.kind, fb.family, "NOT_CONNECTED", "ASSUMPTION", (), fb.words,
                          ASSUMPTION_WORDS[factor_id], None)
        return LeafValue(selection.value, "ESTIMATED", (f"assumption:{selection.revision_id}",), None, missing,
                         selection.currency, (ORIGIN_UNKNOWN,))


__all__ = [
    "ASSUMPTION_WORDS", "COMMERCIAL_LEAVES", "PRICE_KEYS", "PROVIDED_ELSE_ASSUMED", "SOURCE_STATE", "STATED_STATE",
    "STATES", "LeafSource", "ProductLeafSource", "ReadContext",
    "StatedSource", "month_window",
]
