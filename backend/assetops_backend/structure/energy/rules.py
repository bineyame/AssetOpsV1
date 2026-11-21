"""4a unit 1 (spec §2.4; D-4A.2 to D-4A.11, D-4A.16, D-4A.19, D-4A.24): where the kWh went, pure.

Energy delivered into the network is the bound feeders' readings over every Site-local day (D-4A.2); expected
technical loss is a declared band applied to that measurement (D-4A.3, D-4A.4); energy metered and billed are the
operator's own records; losses beyond the expected are delivered less technical less metered, signed (D-4A.5);
unmapped kWh is a join of reads to charges (D-4A.7), never a difference; the tariff is billed money over billed kWh
(D-4A.6). Each factor is judged by the steps of spec §2.4 in order; the first that applies gives the value or the
absence. Unknown is never zero: an absence names its record (`names`) by cause and note (`NOTES`).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Context, Decimal, Inexact, InvalidOperation, Rounded, localcontext
from types import MappingProxyType
from uuid import UUID

from assetops_backend.structure.evaluate import ORIGIN_ORDER, Coverage, LeafValue, Missing
from assetops_backend.structure.registry import FilledBy

OBSERVER = "energy-to-cash@1"
ENERGY_ORDER = ("delivered_kwh", "technical_loss_kwh", "metered_kwh", "unexplained_loss_kwh", "adjustments_kwh",
                "unmapped_kwh", "billed_kwh", "tariff")
ONE_SET, NOT_BOUND, BINDINGS_CHANGED = "ONE_SET", "NOT_BOUND", "BINDINGS_CHANGED"
DECLARED, NOT_DECLARED, CHANGED = "DECLARED", "NOT_DECLARED", "CHANGED"

FEEDER_NOT_BOUND = "FEEDER_NOT_BOUND"
FEEDER_BINDINGS_CHANGED = "FEEDER_BINDINGS_CHANGED"
FEEDER_READINGS_GAP = "FEEDER_READINGS_GAP"
LOSS_BAND_NOT_DECLARED = "LOSS_BAND_NOT_DECLARED"
LOSS_BAND_CHANGED = "LOSS_BAND_CHANGED"
METER_REF_CONFLICT = "METER_REF_CONFLICT"
METER_READ_STRADDLES = "METER_READ_STRADDLES"
METER_READS_OVERLAP = "METER_READS_OVERLAP"
METER_READS_INCOMPLETE = "METER_READS_INCOMPLETE"
NEEDS_ASSIGNMENT = "NEEDS:METER_ASSIGNMENT"
NEEDS_READ = "NEEDS:CUSTOMER_METER_READ"
NEEDS_CHARGE = "NEEDS:CHARGE"
NEEDS_ADJUSTMENT = "NEEDS:ADJUSTMENT"
MONTH_OPEN = "MONTH_OPEN"
CURRENCY_MISMATCH = "CURRENCY_MISMATCH:"
ZERO_DENOMINATOR = "ZERO_DENOMINATOR:billed_kwh"
#: Spec §2.4 "Notes, in one list": 5c maps each to a record (D-4A.12). The last two are parametrised forms.
NOTES = (FEEDER_NOT_BOUND, FEEDER_BINDINGS_CHANGED, FEEDER_READINGS_GAP, LOSS_BAND_NOT_DECLARED, LOSS_BAND_CHANGED,
         METER_REF_CONFLICT, METER_READ_STRADDLES, METER_READS_OVERLAP, METER_READS_INCOMPLETE, NEEDS_ASSIGNMENT,
         NEEDS_READ, NEEDS_CHARGE, NEEDS_ADJUSTMENT, MONTH_OPEN, CURRENCY_MISMATCH, ZERO_DENOMINATOR)

NOT_RECEIVED, NOT_CONNECTED, NOT_CALCULATED_YET = "NOT_RECEIVED", "NOT_CONNECTED", "NOT_CALCULATED_YET"
FEEDER_SOURCE = "readings:feeder_demand"
BAND_SOURCE = "foundation:technical-loss-band"
CUSTOMER_METER_READ, METER_ASSIGNMENT, CHARGE = "CUSTOMER_METER_READ", "METER_ASSIGNMENT", "CHARGE"
ADJUSTMENT = "ADJUSTMENT"
USAGE, STANDARD, PRODUCTIVE, METER = "USAGE", "STANDARD", "PRODUCTIVE", "METER"


@dataclass(frozen=True)
class FeederInput:
    asset_id: UUID
    asset_code: str
    day_kwh: tuple[Decimal | None, ...]     # one per Site-local day of the month; None = the day is not covered
    origins: tuple[str, ...]                # ORIGIN_ORDER order
    band_state: str                         # DECLARED | NOT_DECLARED | CHANGED
    band_pct: Decimal | None                # set only when DECLARED


@dataclass(frozen=True)
class FeederMonth:
    state: str                              # ONE_SET | NOT_BOUND | BINDINGS_CHANGED
    feeders: tuple[FeederInput, ...]        # sorted by asset_code; empty unless ONE_SET
    days: int                               # Site-local days in the month


@dataclass(frozen=True)
class Charge:
    """A CHARGE revision placed in the month (recognition_period == month)."""
    line_type: str
    tariff_class: str | None
    kwh: Decimal | None
    amount: Decimal
    currency: str
    subject: tuple[str, str] | None         # (kind, ref); the meter of a charge is subject.ref when kind is METER
    account_ref: str
    provenance: str
    source_system: str


@dataclass(frozen=True)
class Adjustment:
    """An ADJUSTMENT revision placed in the month with a kWh quantity, signed as recorded (D-4A.8)."""
    kwh: Decimal
    provenance: str
    source_system: str


@dataclass(frozen=True)
class MeterRead:
    """A CUSTOMER_METER_READ revision whose [effective_from, effective_to) meets the month."""
    meter_ref: str          # subject.ref (D-4A.24)
    body_meter_ref: str     # body.meter_ref
    start: date
    end: date
    kwh: Decimal
    provenance: str
    source_system: str


@dataclass(frozen=True)
class Assignment:
    """Every METER_ASSIGNMENT revision of the Site; `end` None is open."""
    meter_ref: str
    body_meter_ref: str
    customer_ref: str
    start: date
    end: date | None


@dataclass(frozen=True)
class EnergyInputs:
    month: str
    first: date
    next_first: date
    closed: bool
    feeders: FeederMonth
    held: frozenset[str]                    # kinds with any revision of the Site at the cutoff (D-4B.5)
    charges: tuple[Charge, ...]
    adjustments: tuple[Adjustment, ...]
    reads: tuple[MeterRead, ...]
    assignments: tuple[Assignment, ...]


@dataclass(frozen=True)
class EnergyMonth:
    values: Mapping[str, LeafValue]         # every factor of ENERGY_ORDER


def _context() -> Context:
    return Context(prec=34, rounding=ROUND_HALF_EVEN)


def _exact() -> Context:
    """D-3A4.9: sums of record quantities are exact (200 digits; any rounding is an error)."""
    return Context(prec=200, traps=[Inexact, Rounded, InvalidOperation])


def _norm(value: Decimal) -> Decimal:
    return value.copy_abs() if value == 0 else value


def _sum(values: Iterable[Decimal]) -> Decimal:
    with localcontext(_exact()):
        total = Decimal(0)
        for v in values:
            total = total + v
        return _norm(total)


def _origins(*groups: Iterable[str]) -> tuple[str, ...]:
    held = {o for g in groups for o in g}
    return tuple(o for o in ORIGIN_ORDER if o in held)


def _sources(*groups: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({s for g in groups for s in g}))


def _commercial(records: Sequence[Charge | Adjustment | MeterRead]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return (_sources(f"commercial:{r.source_system}" for r in records), _origins(r.provenance for r in records))


@dataclass(frozen=True)
class _No:
    """An absence before it is given its record: cause and note (and, on delivered, coverage)."""
    cause: str
    note: str | None
    coverage: Coverage | None = None


def _absent(fb: FilledBy, no: _No) -> LeafValue:
    return LeafValue(None, "NOT_AVAILABLE", (), no.coverage,
                     Missing(fb.kind, fb.family, no.cause, None, (), fb.words, None, no.note), None)


def _meets(start: date, end: date | None, first: date, next_first: date) -> bool:
    return start < next_first and (end is None or end > first)


class _Month:
    """One month's judgement; each factor is computed once, in ENERGY_ORDER."""

    def __init__(self, inputs: EnergyInputs) -> None:
        self.i = inputs
        held = inputs.held
        self.has_charge_kind = CHARGE in held
        self.has_adjustment_kind = ADJUSTMENT in held
        self.has_read_kind = CUSTOMER_METER_READ in held
        self.has_assignment_kind = METER_ASSIGNMENT in held
        self.standard = tuple(c for c in inputs.charges if c.line_type == USAGE and c.kwh is not None
                              and c.tariff_class in (STANDARD, None))
        self.productive = tuple(c for c in inputs.charges if c.line_type == USAGE and c.tariff_class == PRODUCTIVE)
        feeders = inputs.feeders
        self.one_set = feeders.state == ONE_SET
        self.coverage: Coverage | None = None
        if self.one_set:
            covered = sum(1 for d in range(feeders.days)
                          if all(f.day_kwh[d] is not None for f in feeders.feeders))
            self.coverage = Coverage(covered, feeders.days, MappingProxyType(
                {"COMPLETE": covered, "NO_DATA": feeders.days - covered}))

    # ---------------------------------------------------------------- feeders

    def delivered(self) -> LeafValue | _No:
        i, fm = self.i, self.i.feeders
        if fm.state == NOT_BOUND:
            return _No(NOT_CONNECTED, FEEDER_NOT_BOUND)
        if not i.closed:
            return _No(NOT_RECEIVED, MONTH_OPEN, self.coverage)
        if fm.state == BINDINGS_CHANGED:
            return _No(NOT_CALCULATED_YET, FEEDER_BINDINGS_CHANGED)
        assert self.coverage is not None
        if self.coverage.covered != fm.days:
            return _No(NOT_RECEIVED, FEEDER_READINGS_GAP, self.coverage)
        total = _sum(k for f in fm.feeders for k in f.day_kwh if k is not None)
        return LeafValue(total, "MEASURED", (FEEDER_SOURCE,), self.coverage, None, None,
                         _origins(*(f.origins for f in fm.feeders)))

    def technical(self, delivered: LeafValue | _No) -> LeafValue | _No:
        fm = self.i.feeders
        if fm.state == NOT_BOUND:
            return _No(NOT_CONNECTED, FEEDER_NOT_BOUND)
        if any(f.band_state == NOT_DECLARED for f in fm.feeders):
            return _No(NOT_CONNECTED, LOSS_BAND_NOT_DECLARED)
        if any(f.band_state == CHANGED for f in fm.feeders):
            return _No(NOT_CALCULATED_YET, LOSS_BAND_CHANGED)
        if isinstance(delivered, _No):
            return _No(delivered.cause, delivered.note)
        with localcontext(_context()):
            total = Decimal(0)
            for f in fm.feeders:
                assert f.band_pct is not None
                total += _sum(k for k in f.day_kwh if k is not None) * f.band_pct / 100
        return LeafValue(_norm(total), "MODELLED", (FEEDER_SOURCE, BAND_SOURCE), None, None, None,
                         delivered.origins)

    # ---------------------------------------------------------------- meter reads

    def inside(self) -> tuple[MeterRead, ...]:
        i = self.i
        return tuple(r for r in i.reads if r.start >= i.first and r.end <= i.next_first)

    def metered(self) -> tuple[int, LeafValue | _No]:
        """(step, result); step 0 for a value."""
        i = self.i
        if not self.has_read_kind:
            return 1, _No(NOT_CONNECTED, None)
        if not i.closed:
            return 2, _No(NOT_RECEIVED, MONTH_OPEN)
        if not self.has_assignment_kind:
            return 3, _No(NOT_CONNECTED, NEEDS_ASSIGNMENT)
        meeting = [r for r in i.reads if _meets(r.start, r.end, i.first, i.next_first)]
        spans = [a for a in i.assignments if _meets(a.start, a.end, i.first, i.next_first)]
        if any(r.meter_ref != r.body_meter_ref for r in meeting) or \
                any(a.meter_ref != a.body_meter_ref for a in spans):
            return 4, _No(NOT_CALCULATED_YET, METER_REF_CONFLICT)
        if any(not (r.start >= i.first and r.end <= i.next_first) for r in meeting):
            return 5, _No(NOT_CALCULATED_YET, METER_READ_STRADDLES)
        inside = self.inside()
        for n, a in enumerate(inside):
            for b in inside[n + 1:]:
                if a.meter_ref == b.meter_ref and a.start < b.end and b.start < a.end:
                    return 6, _No(NOT_CALCULATED_YET, METER_READS_OVERLAP)
        for a in spans:
            lo, hi = max(a.start, i.first), min(a.end or i.next_first, i.next_first)
            mine = sorted((r.start, r.end) for r in inside if r.meter_ref == a.meter_ref)
            if lo < hi and not _covers(mine, lo, hi):
                return 7, _No(NOT_RECEIVED, METER_READS_INCOMPLETE)
        if not inside:
            return 8, _No(NOT_RECEIVED, None)
        sources, origins = _commercial(inside)
        return 0, LeafValue(_sum(r.kwh for r in inside), "RECORDED", sources, None, None, None, origins)

    def unexplained(self, delivered: LeafValue | _No, technical: LeafValue | _No,
                    metered: LeafValue | _No) -> LeafValue | _No:
        for part in (delivered, technical, metered):
            if isinstance(part, _No):
                return _No(part.cause, part.note)
        assert isinstance(delivered, LeafValue) and isinstance(technical, LeafValue) and isinstance(metered, LeafValue)
        with localcontext(_context()):
            value = delivered.value - technical.value - metered.value
        return LeafValue(_norm(value), "MODELLED", _sources(delivered.sources, technical.sources, metered.sources),
                         None, None, None, _origins(delivered.origins, technical.origins, metered.origins))

    # ---------------------------------------------------------------- billing

    def adjustments(self) -> LeafValue | _No:
        i = self.i
        if not self.has_adjustment_kind:  # D-4A.8 / D-DS4.25: never sent is blank, not 0
            return _No(NOT_CONNECTED, NEEDS_ADJUSTMENT)
        if not i.closed:
            return _No(NOT_RECEIVED, MONTH_OPEN)
        if not i.charges:
            return _No(NOT_RECEIVED, NEEDS_CHARGE)
        basis: Sequence[Charge | Adjustment] = i.adjustments or i.charges
        sources, origins = _commercial(basis)
        return LeafValue(_sum(a.kwh for a in i.adjustments), "RECORDED", sources, None, None, None, origins)

    def _customer(self, read: MeterRead) -> str | None:
        """D-4A.7: the one assignment of the read's meter whose span contains the read's; none or several: None."""
        found = [a for a in self.i.assignments if a.meter_ref == read.meter_ref and a.start <= read.start
                 and (a.end is None or read.end <= a.end)]
        return found[0].customer_ref if len(found) == 1 else None

    def _charged(self, read: MeterRead) -> bool:
        customer = self._customer(read)
        for c in self.standard + self.productive:
            if c.subject == (METER, read.meter_ref):
                return True
            if (c.subject is None or c.subject[0] != METER) and customer is not None and c.account_ref == customer:
                return True
        return False

    def unmapped(self, metered_step: int, metered: LeafValue | _No) -> LeafValue | _No:
        i = self.i
        if not self.has_assignment_kind:
            return _No(NOT_CONNECTED, NEEDS_ASSIGNMENT)
        if not self.has_read_kind:
            return _No(NOT_CONNECTED, NEEDS_READ)
        if not self.has_charge_kind:
            return _No(NOT_CONNECTED, NEEDS_CHARGE)
        if not i.closed:
            return _No(NOT_RECEIVED, MONTH_OPEN)
        if isinstance(metered, _No) and 4 <= metered_step <= 8:
            return _No(metered.cause, metered.note)
        if not i.charges:
            return _No(NOT_RECEIVED, NEEDS_CHARGE)
        reads = self.inside()
        used = self.standard + self.productive
        sources, origins = _commercial(reads + used)
        return LeafValue(_sum(r.kwh for r in reads if not self._charged(r)), "DERIVED", sources, None, None, None,
                         origins)

    def billed(self) -> LeafValue | _No:
        i = self.i
        if not self.has_charge_kind:
            return _No(NOT_CONNECTED, None)
        if not i.closed:
            return _No(NOT_RECEIVED, MONTH_OPEN)
        if not i.charges:
            return _No(NOT_RECEIVED, None)
        sources, origins = _commercial(self.standard or i.charges)
        return LeafValue(_sum(c.kwh for c in self.standard if c.kwh is not None), "RECORDED", sources, None, None,
                         None, origins)

    def tariff(self) -> LeafValue | _No:
        i, s = self.i, self.standard
        if not self.has_charge_kind:
            return _No(NOT_CONNECTED, NEEDS_CHARGE)
        if not i.closed:
            return _No(NOT_RECEIVED, MONTH_OPEN)
        if not s:
            return _No(NOT_RECEIVED, NEEDS_CHARGE)
        currencies = sorted({c.currency for c in s})
        if len(currencies) >= 2:
            return _No(NOT_CALCULATED_YET, CURRENCY_MISMATCH + ",".join(currencies))
        kwh = _sum(c.kwh for c in s if c.kwh is not None)
        if kwh == 0:
            return _No(NOT_CALCULATED_YET, ZERO_DENOMINATOR)
        amount = _sum(c.amount for c in s)
        with localcontext(_context()):
            price = amount / kwh
        sources, origins = _commercial(s)
        return LeafValue(_norm(price), "DERIVED", sources, None, None, currencies[0], origins)


def _covers(spans: Sequence[tuple[date, date]], lo: date, hi: date) -> bool:
    """`[lo, hi)` lies inside the union of the sorted spans."""
    reach = lo
    for start, end in spans:
        if start > reach:
            break
        reach = max(reach, end)
        if reach >= hi:
            return True
    return reach >= hi


def month_energy(inputs: EnergyInputs, names: Mapping[str, FilledBy]) -> EnergyMonth:
    """Spec §2.4: every factor of `ENERGY_ORDER` for one Site-month; `names[f]` is what an absent `f` names."""
    m = _Month(inputs)
    delivered = m.delivered()
    technical = m.technical(delivered)
    metered_step, metered = m.metered()
    out = {
        "delivered_kwh": delivered,
        "technical_loss_kwh": technical,
        "metered_kwh": metered,
        "unexplained_loss_kwh": m.unexplained(delivered, technical, metered),
        "adjustments_kwh": m.adjustments(),
        "unmapped_kwh": m.unmapped(metered_step, metered),
        "billed_kwh": m.billed(),
        "tariff": m.tariff(),
    }
    return EnergyMonth(MappingProxyType({f: out[f] if isinstance(out[f], LeafValue) else _absent(names[f], out[f])
                                         for f in ENERGY_ORDER}))


__all__ = [
    "BINDINGS_CHANGED", "CHANGED", "DECLARED", "ENERGY_ORDER", "NOTES", "NOT_BOUND", "NOT_DECLARED", "OBSERVER",
    "ONE_SET", "Adjustment", "Assignment", "Charge", "EnergyInputs", "EnergyMonth", "FeederInput", "FeederMonth",
    "MeterRead", "month_energy",
]
