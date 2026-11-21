"""4d unit 3 (spec §4.3): the litre inputs from the stores the product already has (D-4D.1).

`StoreLitreInputs.read` takes the Site's one generator and one fuel tank, K3's choice of the fuel curve over the month,
the tank's dips and deliveries, the generator's readings (A2's slot rule bound into `use`, D-4D.10's `held`), and the
selected dispatch facts (dispatch-3.3 since 0K4e) of every UTC day meeting `[lo - EDGE, hi + EDGE)`, whose state `day_state` decides (D-4D.12).
The stores are ports here; their adapters are reached only through `structure.litres.composition`.
"""

from __future__ import annotations

import bisect
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta
from fractions import Fraction
from typing import Any, Protocol
from uuid import UUID

from assetops_backend.chain.ports import SiteRef
from assetops_backend.financials.trial_fuel_comparison import WindowFacts, no_load_for, sfc_for
from assetops_backend.fuel_balance.rules import (
    GENERATOR_POWER, GENERATOR_STATE, ROLES, relevant_readings, use_from_readings)
from assetops_backend.fuel_balance.service import NO_LOAD_BASES, NO_LOAD_BASIS_KEY, no_load_basis
from assetops_backend.structure.litres.rules import (
    ASSESSED, EDGE, NO_READINGS, NOT_ASSESSED, NOT_ONE_EACH, ONE_EACH, UNAVAILABLE, DispatchDay, FuelCurve,
    LitreInputs, RunSpan, SpanUse, TankRecord)
from assetops_backend.structure.sources import month_window

READING_EDGE = timedelta(minutes=30)   # A2's slot rule looks this far either side of a slot (K3's read)


def day_state(available: bool, status: str | None, selected: bool, accepted_reading_count: int | None) -> str:
    """D-4D.12: only a CURRENT selection is analysed."""
    if not available:
        return UNAVAILABLE
    if not selected:
        return NO_READINGS if accepted_reading_count in (None, 0) else NOT_ASSESSED
    return ASSESSED if status == "CURRENT" else NOT_ASSESSED


class FuelReadPort(Protocol):
    def read_at(self, tenant_id: UUID, site_id: UUID, known_at: datetime, work: Callable[[Any], Any]) -> Any: ...


class DispatchSpansPort(Protocol):
    def dispatch_spans(self, tenant_id: UUID, site_id: UUID, lo: datetime, hi: datetime,
                       known_at: datetime) -> tuple[dict[str, Any], ...]: ...


def _instant(r: Any) -> datetime | None:
    return r.interval_end or r.source_time


def _never(a: datetime, b: datetime) -> SpanUse:
    raise AssertionError("use is never called for a Site without one generator and one tank")


def _later(a: datetime, b: datetime) -> datetime:
    return max(a, b)


def _earlier(a: datetime | None, b: datetime | None) -> datetime | None:
    return b if a is None else a if b is None else min(a, b)


class _Readings:
    """The generator's readings bound for `held` and `use` (spec §4.3 step 2)."""

    def __init__(self, readings: Sequence[Any], gen_id: str) -> None:
        timed = sorted(((t, r) for r in readings if (t := _instant(r)) is not None), key=lambda x: x[0])
        self._times = [t for t, _ in timed]
        self._all = [r for _, r in timed]
        self._gen = sorted(t for t, r in timed if r.role in (GENERATOR_POWER, GENERATOR_STATE) and r.asset_id == gen_id)
        self._gen_id = gen_id

    def held(self, a: datetime, b: datetime) -> bool:
        """Any generator power or state reading with its instant in `(a, b]` (D-4D.10)."""
        return bisect.bisect_right(self._gen, b) > bisect.bisect_right(self._gen, a)

    def use(self, a: datetime, b: datetime) -> SpanUse:
        i = bisect.bisect_left(self._times, a - READING_EDGE)
        j = bisect.bisect_right(self._times, b + READING_EDGE)
        u = use_from_readings(a, b, self._all[i:j], self._gen_id)
        return SpanUse(u["generator_kwh"], u["idle_seconds"])


class StoreLitreInputs:
    def __init__(self, fuel: FuelReadPort, assessments: DispatchSpansPort) -> None:
        self._fuel = fuel
        self._assessments = assessments

    def read(self, site: SiteRef, month: str, known_at: datetime) -> LitreInputs:
        lo, hi = month_window(month, site.timezone)[:2]

        def work(tx: Any) -> tuple[str, Callable, Callable, FuelCurve, tuple[TankRecord, ...]]:
            assets = tx.active_assets()
            gens = [a for a in assets if a.asset_type == "GENERATOR"]
            tanks = [a for a in assets if a.asset_type == "FUEL_TANK"]
            if len(gens) != 1 or len(tanks) != 1:
                return NOT_ONE_EACH, _never, lambda a, b: False, FuelCurve(None, None, None, None, None), ()
            gen, tank = gens[0], tanks[0]
            facts = WindowFacts((), False, None, None, lo, hi)       # K3's choice (fuel_balance/service.py:96-107)
            sfc = sfc_for(facts, tx.sfc_history(gen.id, lo, hi))
            rate = no_load_for(facts, tx.no_load_history(gen.id, lo, hi))
            if rate is not None:
                basis = no_load_basis(tx.properties(gen.asset_code, (NO_LOAD_BASIS_KEY,), lo, hi),
                                      str(rate.foundation_revision_id))
                rate = rate if basis in NO_LOAD_BASES else None
            if sfc is None:
                curve = FuelCurve(None, None, None, None, None)
            else:
                valid = (sfc.valid_from, sfc.valid_to)
                if rate is not None:
                    valid = (_later(valid[0], rate.valid_from), _earlier(valid[1], rate.valid_to))
                curve = FuelCurve(Fraction(sfc.value_l_per_kwh), f"foundation:{sfc.property_revision_id}",
                                  None if rate is None else Fraction(rate.value_l_per_h),
                                  None if rate is None else f"foundation:{rate.foundation_revision_id}", valid)
            records = tuple(TankRecord(r.kind, r.occurred_at, r.quantity_l, str(r.root_id))
                            for r in tx.fuel_records(tank.id, lo - EDGE, hi + EDGE))
            readings = relevant_readings(tx.readings(lo - EDGE - READING_EDGE, hi + EDGE + READING_EDGE, ROLES),
                                         tank.id, gen.id)
            bound = _Readings(readings, str(gen.id))
            return ONE_EACH, bound.use, bound.held, curve, records

        assets, use, held, curve, tank = self._fuel.read_at(site.tenant_id, site.site_id, known_at, work)
        days = tuple(
            DispatchDay(d["day"], state, d["run_id"] if state == ASSESSED else None,
                        tuple(RunSpan(s, e, c) for s, e, c in d["spans"]) if state == ASSESSED else ())
            for d in self._assessments.dispatch_spans(site.tenant_id, site.site_id, lo - EDGE, hi + EDGE, known_at)
            for state in (day_state(d["available"], d["status"], d["selected"], d["accepted_reading_count"]),))
        return LitreInputs(month, lo, hi, known_at, assets, days, use, held, curve, tank)


__all__ = ["DispatchSpansPort", "FuelReadPort", "StoreLitreInputs", "day_state"]
