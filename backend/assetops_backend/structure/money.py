"""4b2: the money leaves and stated nodes from the operator's own records (spec §3; D-4B.3 to D-4B.9, D-4B.12 to
D-4B.15, D-4B.18).

`CommercialLeafSource` reads 3A4's month (`CommercialMonths.site_month`) and the kinds the store holds for the Site
(`latest_revisions`, D-4B.5), once per `ReadContext` object (D-4B.12). It serves the leaves `SOURCE_STATE` marks
`PROVIDED` or `PROVIDED_ELSE_ASSUMED` in spec §3.4's table and the nodes `STATED_STATE` marks `PROVIDED`; every
other leaf goes to the fallback (3B3's `ProductLeafSource`) unchanged. Unknown is never zero: a value with no line
behind it is a ZERO_WHEN_HELD row whose kind is held for the month. Sums are exact (D-3A4.9); the diesel price is
the one division. An absent value names the record 4b reads for it (`READ_AS`, D-4B.13).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Context, Decimal, Inexact, InvalidOperation, Rounded, localcontext
from types import MappingProxyType

from assetops_backend.commercial.months import CommercialMonths, MonthAmounts, MonthLine
from assetops_backend.commercial.store import CommercialStore
from assetops_backend.structure import registry as _registry
from assetops_backend.structure.check import StructureError
from assetops_backend.structure.evaluate import ORIGIN_ORDER, LeafValue, Missing
from assetops_backend.structure.read import SITE_TYPE_TO_STRUCTURE
from assetops_backend.structure.registry import FilledBy
from assetops_backend.structure.sources import (
    COMMERCIAL_KEYS,
    ENERGY_STATED,
    PROVIDED,
    PROVIDED_ELSE_ASSUMED,
    SOURCE_STATE,
    STATED_STATE,
    LeafSource,
    ReadContext,
)

#: D-4B.3: only these expense statuses are a cost; a QUOTE never is.
COST_STATUSES = ("INVOICED", "PAID")
CHARGE_RECORD = FilledBy("COMMERCIAL_RECORD", "CHARGE", "Billing export: the month's charges")
RECEIPT_RECORD = FilledBy("COMMERCIAL_RECORD", "RECEIPT", "Receipts for the month, with their payment status")
MONTH_OPEN = "MONTH_OPEN"
LITRES = "L"

_MG = _registry.REGISTRIES["MINI_GRID"]

#: D-4B.13, spec §3.4 "Names when absent": the record an absent value names. `outstanding` resolves per failing
#: kind; cases 2 and 4 (open month, mixed currency) name its `filled_by`.
READ_AS: Mapping[str, FilledBy | Mapping[str, FilledBy]] = MappingProxyType({
    "revenue": _MG.row("revenue").stated_by,
    "fuel_cost": _MG.row("fuel_cost").stated_by,
    "om": _MG.row("om").filled_by,
    "staff": _MG.row("staff").filled_by,
    "productive_kwh": _MG.row("productive_kwh").filled_by,
    "in_transit": RECEIPT_RECORD,
    "outstanding": MappingProxyType({"CHARGE": CHARGE_RECORD, "RECEIPT": _MG.row("outstanding").filled_by}),
    "diesel_price": _MG.row("diesel_price").filled_by,
})


def _exact() -> Context:
    """D-3A4.9: 200 digits, and any rounding is an error."""
    return Context(prec=200, traps=[Inexact, Rounded, InvalidOperation])


def _price_context() -> Context:
    return Context(prec=34, rounding=ROUND_HALF_EVEN)


def _dim(line: MonthLine, name: str) -> str | None:
    return dict(line.dims).get(name)


def _cost(category: str, measure: str = "AMOUNT") -> Callable[[MonthLine], bool]:
    def pick(line: MonthLine) -> bool:
        return (line.kind == "EXPENSE" and line.measure == measure and _dim(line, "category") == category
                and _dim(line, "status") in COST_STATUSES)
    return pick


def _amount(kind: str) -> Callable[[MonthLine], bool]:
    return lambda line: line.kind == kind and line.measure == "AMOUNT"


def _none(_line: MonthLine) -> bool:
    return False


@dataclass(frozen=True)
class _Row:
    """One row of spec §3.4 (all but `diesel_price`): value = Σ plus − Σ minus over the month's lines."""

    kinds: tuple[str, ...]
    plus: Callable[[MonthLine], bool]
    minus: Callable[[MonthLine], bool]
    evidence: str
    zero_when_held: bool
    money: bool


_ROWS: Mapping[str, _Row] = MappingProxyType({
    "revenue": _Row(("CHARGE",), _amount("CHARGE"), _none, "RECORDED", False, True),
    "fuel_cost": _Row(("EXPENSE",), _cost("FUEL"), _none, "RECORDED", False, True),
    "om": _Row(("EXPENSE",), _cost("OM"), _none, "RECORDED", False, True),
    "staff": _Row(("EXPENSE",), _cost("STAFF"), _none, "RECORDED", False, True),
    "productive_kwh": _Row(
        ("CHARGE",),
        lambda line: (line.kind == "CHARGE" and line.measure == "QUANTITY" and _dim(line, "line_type") == "USAGE"
                      and _dim(line, "tariff_class") == "PRODUCTIVE"),
        _none, "RECORDED", True, False),
    "in_transit": _Row(("RECEIPT",),
                       lambda line: (line.kind == "RECEIPT" and line.measure == "AMOUNT"
                                     and _dim(line, "status") == "PAID_IN_TRANSIT"),
                       _none, "RECORDED", True, True),
    "outstanding": _Row(("CHARGE", "RECEIPT"), _amount("CHARGE"), _amount("RECEIPT"), "DERIVED", True, True),
})
DIESEL_PRICE = "diesel_price"


def _record(factor_id: str, kind: str | None) -> FilledBy:
    named = READ_AS[factor_id]
    if isinstance(named, Mapping):
        return named[kind] if kind is not None else _MG.row(factor_id).filled_by
    return named


def _absent(fb: FilledBy, cause: str, note: str | None = None) -> LeafValue:
    return LeafValue(None, "NOT_AVAILABLE", (), None, Missing(fb.kind, fb.family, cause, None, (), fb.words, None,
                                                              note), None)


def _currencies(lines: Sequence[MonthLine]) -> list[str]:
    return sorted({line.currency for line in lines if line.measure == "AMOUNT" and line.currency is not None})


def _mismatch(currencies: Sequence[str]) -> str:
    return "CURRENCY_MISMATCH:" + ",".join(currencies)


def _sum(lines: Sequence[MonthLine]) -> Decimal:
    total = Decimal(0)
    for line in lines:
        total = total + line.value
    return total


def _sources(lines: Sequence[MonthLine]) -> tuple[str, ...]:
    return tuple(sorted({f"commercial:{system}" for line in lines for system in line.source_systems}))


def _origins(lines: Sequence[MonthLine]) -> tuple[str, ...]:
    held = {line.provenance for line in lines}
    return tuple(o for o in ORIGIN_ORDER if o in held)


def used_lines(factor_id: str, lines: Sequence[MonthLine]) -> list[MonthLine]:
    """The lines this module sums into a money row (`revenue`, `fuel_cost`, ...): 3A7 reconciles the same lines
    the screen shows (D-3A7.1), so it reads them here rather than restating the filter."""
    return [line for line in lines if _ROWS[factor_id].plus(line)]


def line_sources(lines: Sequence[MonthLine]) -> tuple[str, ...]:
    """The lines' sources as this module names them (`commercial:<system>`, sorted, distinct)."""
    return _sources(lines)


def line_origins(lines: Sequence[MonthLine]) -> tuple[str, ...]:
    """The lines' distinct provenances, in `ORIGIN_ORDER`."""
    return _origins(lines)


class CommercialLeafSource:
    """Implements `LeafSource` and `StatedSource` (spec §3.1)."""

    def __init__(self, months: CommercialMonths, store: CommercialStore, fallback: LeafSource) -> None:
        self._months = months
        self._store = store
        self._fallback = fallback
        self._last: tuple[ReadContext, MonthAmounts, frozenset[str]] | None = None

    # --- the ports ----------------------------------------------------------------------------------------------

    def leaf(self, ctx: ReadContext, factor_id: str) -> LeafValue:
        key = SITE_TYPE_TO_STRUCTURE.get(ctx.site.site_type)
        state = SOURCE_STATE.get(key, {}).get(factor_id) if key is not None else None
        if factor_id == DIESEL_PRICE and state == PROVIDED_ELSE_ASSUMED:
            return self._diesel_price(ctx)
        # 3B6 (D-3B6.18): `_ROWS` are mini-grid rows keyed by a factor ID other structures share (`staff`).
        if factor_id in _ROWS and state == PROVIDED and key in COMMERCIAL_KEYS:
            return self._judge(ctx, factor_id)
        return self._fallback.leaf(ctx, factor_id)

    def stated(self, ctx: ReadContext, factor_id: str) -> LeafValue:
        if factor_id in ENERGY_STATED:  # 4a: read without the energy source, the node folds from its expression
            return _absent(_MG.row(factor_id).stated_by, "NOT_CONNECTED")
        key = SITE_TYPE_TO_STRUCTURE.get(ctx.site.site_type)
        if key is None or STATED_STATE.get(key, {}).get(factor_id) != PROVIDED or factor_id not in _ROWS:
            raise StructureError("STRUCTURE_STATED", str(key), factor_id)
        return self._judge(ctx, factor_id)

    # --- one read per Site-month read (D-4B.12) -----------------------------------------------------------------

    def _month(self, ctx: ReadContext) -> tuple[MonthAmounts, frozenset[str]]:
        last = self._last
        if last is not None and last[0] is ctx:
            return last[1], last[2]
        site = ctx.site
        amounts = self._months.site_month(site.tenant_id, site.site_id, ctx.month, known_at=ctx.known_at)
        held = frozenset(r.kind for r in self._store.latest_revisions(site.tenant_id, site_id=site.site_id,
                                                                        known_at=ctx.known_at))
        self._last = (ctx, amounts, held)
        return amounts, held

    # --- spec §3.3, every row but the diesel price --------------------------------------------------------------

    def _judge(self, ctx: ReadContext, factor_id: str) -> LeafValue:
        row = _ROWS[factor_id]
        amounts, held = self._month(ctx)
        named = isinstance(READ_AS[factor_id], Mapping)  # a per-kind record: the note names the failing kind
        for kind in row.kinds:  # 1. connected (any month, D-4B.5)
            if kind not in held:
                return _absent(_record(factor_id, kind), "NOT_CONNECTED", f"NEEDS:{kind}" if named else None)
        if not amounts.closed:  # 2. D-4B.4
            return _absent(_record(factor_id, None), "NOT_RECEIVED", MONTH_OPEN)
        lines = amounts.lines
        in_month = {line.kind for line in lines}
        for kind in row.kinds:  # 3. received for the month
            if kind not in in_month:
                return _absent(_record(factor_id, kind), "NOT_RECEIVED", f"NEEDS:{kind}" if named else None)
        plus = [line for line in lines if row.plus(line)]
        minus = [line for line in lines if row.minus(line)]
        used = plus + minus
        if used:
            basis = used
        elif row.zero_when_held:  # a recorded zero: the kind is held for the month (step 3), nothing matched
            basis = [line for line in lines if line.kind in row.kinds]
        else:
            return _absent(_record(factor_id, None), "NOT_RECEIVED")
        currency = None
        if row.money:  # 4. one currency (R9: a recorded zero checks all AMOUNT lines of the kind)
            currencies = _currencies(basis)
            if len(currencies) >= 2:
                return _absent(_record(factor_id, None), "NOT_CALCULATED_YET", _mismatch(currencies))
            currency = currencies[0]
        with localcontext(_exact()):
            value = _sum(plus) - _sum(minus)
            if value == 0:
                value = value.copy_abs()
        return LeafValue(value, row.evidence, _sources(basis), None, None, currency, _origins(basis))

    # --- spec §3.3, the diesel price (D-4B.6, D-4B.14, D-4B.15) -------------------------------------------------

    def _diesel_price(self, ctx: ReadContext) -> LeafValue:
        amounts, held = self._month(ctx)
        fuel = [line for line in amounts.lines if _cost("FUEL")(line)]
        if "EXPENSE" not in held or not fuel:  # 1. no invoice to read: the labelled declared price
            return self._fallback.leaf(ctx, DIESEL_PRICE)
        fb = _record(DIESEL_PRICE, None)
        if not amounts.closed:  # 2. invoices exist; the assumption never hides them
            return _absent(fb, "NOT_RECEIVED", MONTH_OPEN)
        currencies = _currencies(fuel)
        if len(currencies) >= 2:  # 3.
            return _absent(fb, "NOT_CALCULATED_YET", _mismatch(currencies))
        litres = [line for line in amounts.lines if _cost("FUEL", "QUANTITY")(line) and line.unit == LITRES]
        with localcontext(_exact()):
            spent, burned = _sum(fuel), _sum(litres)
        if burned == 0:  # 4. D-4B.15
            return _absent(fb, "NOT_CALCULATED_YET", "ZERO_DENOMINATOR:fuel_litres")
        with localcontext(_price_context()):
            price = spent / burned
        used = fuel + litres
        return LeafValue(price, "DERIVED", _sources(used), None, None, currencies[0], _origins(used))


__all__ = ["CHARGE_RECORD", "COST_STATUSES", "READ_AS", "RECEIPT_RECORD", "CommercialLeafSource"]
