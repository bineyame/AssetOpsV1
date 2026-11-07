"""DIESEL-K3 (`.agent/build-sheet-DIESEL-1.md` §9d.4): assess one named night, explicitly (no tick stage in v1).

`assess_night` runs in one store transaction: the Site's one active FUEL_TANK and one active GENERATOR, the night
window in the Site timezone, the closed-window check, the per-night lock, the inputs as known at the transaction's
`known_at`, `rules.assess`, the inputs digest, and an append only when the digest differs from the latest revision's.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Any, Iterable
from uuid import UUID

from assetops_backend.financials.trial_fuel_comparison import WindowFacts, no_load_for, sfc_for
from assetops_backend.fuel_balance import rules
from assetops_backend.fuel_balance.model import (
    ASSETS_UNSUPPORTED, CLOCK_BACKWARDS, WINDOW_OPEN, AssessResult, FuelBalanceRefused)
from assetops_backend.sites.models import STATE_PROPERTY_VALUES

ACCURACY_KEY = "fuel-level-sensor-accuracy"
ACCURACY_BASIS_KEY = "fuel-level-sensor-accuracy-basis"
NO_LOAD_BASIS_KEY = "generator-no-load-fuel-rate-basis"
NO_LOAD_BASES = STATE_PROPERTY_VALUES[NO_LOAD_BASIS_KEY]
_CLOSING_SEARCH = timedelta(minutes=rules.EDGE_SEARCH_MIN)


def _finite(value: Any) -> Fraction | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        out = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return Fraction(out) if out.is_finite() else None


def _one(values: list[tuple[Any, Any]], unit: str) -> Any:
    """The single declared value with this unit, else None (none, several or the wrong unit)."""
    return values[0][0] if len(values) == 1 and values[0][1] == unit else None


def accuracy_values(revisions: Iterable[Any]) -> list[rules.Declared]:
    """Each revision's tank `fuel-level-sensor-accuracy` (one finite value in L) with its basis (one state value)."""
    out = []
    for rev in revisions:
        value = _finite(_one(rev.values.get(ACCURACY_KEY, []), rules.LITRES))
        basis = _one(rev.values.get(ACCURACY_BASIS_KEY, []), "state")
        if value is not None:
            out.append(rules.Declared(value, basis if isinstance(basis, str) else None, rev.revision_id,
                                      rev.valid_from, rev.valid_to))
    return out


def no_load_basis(revisions: Iterable[Any], revision_id: str) -> str | None:
    for rev in revisions:
        if rev.revision_id == revision_id:
            basis = _one(rev.values.get(NO_LOAD_BASIS_KEY, []), "state")
            return basis if isinstance(basis, str) else None
    return None


class FuelBalanceService:
    def __init__(self, store: Any) -> None:
        self.store = store

    def assess_night(self, tenant_id: UUID, site_id: UUID, night_date: date) -> AssessResult:
        return self.store.transaction(tenant_id, site_id, lambda tx: self._assess(tx, night_date))

    @staticmethod
    def _assess(tx: Any, night_date: date) -> AssessResult:
        assets = tx.active_assets()
        tanks = [a for a in assets if a.asset_type == "FUEL_TANK"]
        generators = [a for a in assets if a.asset_type == "GENERATOR"]
        if len(tanks) != 1 or len(generators) != 1:
            raise FuelBalanceRefused(ASSETS_UNSUPPORTED, f"v1 assesses one fuel tank and one generator; the Site has "
                                                         f"{len(tanks)} active tanks and {len(generators)} generators")
        tank, gen = tanks[0], generators[0]
        start, end = rules.night_window(night_date, tx.timezone())
        known_at: datetime = tx.known_at
        if known_at < end + _CLOSING_SEARCH:
            raise FuelBalanceRefused(WINDOW_OPEN, f"night {night_date.isoformat()} closes at "
                                                  f"{(end + _CLOSING_SEARCH).isoformat()}")
        tx.lock(tank.id, night_date)
        latest = tx.latest(tank.id, night_date)
        if latest is not None and known_at < latest.recorded_at:
            raise FuelBalanceRefused(CLOCK_BACKWARDS, f"{known_at.isoformat()} is before revision {latest.revision}")

        records = tx.fuel_records(tank.id, start, end)
        accuracy = rules.declared_for(accuracy_values(tx.properties(tank.asset_code, (ACCURACY_KEY, ACCURACY_BASIS_KEY),
                                                                    start, end)),
                                      start, end, rules.ACCURACY_BASES)
        facts = WindowFacts(evidence_ids=(), complete=False, generator_kwh=None, feeder_demand_kwh=None,
                            start=start, end=end)
        sfc_value = sfc_for(facts, tx.sfc_history(gen.id, start, end))
        sfc = None if sfc_value is None else rules.Declared(
            Fraction(sfc_value.value_l_per_kwh), None, str(sfc_value.property_revision_id), sfc_value.valid_from,
            sfc_value.valid_to)
        rate = no_load_for(facts, tx.no_load_history(gen.id, start, end))
        no_load = None
        if rate is not None:
            basis = no_load_basis(tx.properties(gen.asset_code, (NO_LOAD_BASIS_KEY,), start, end),
                                  str(rate.foundation_revision_id))
            if basis in NO_LOAD_BASES:
                no_load = rules.Declared(Fraction(rate.value_l_per_h), basis, str(rate.foundation_revision_id),
                                         rate.valid_from, rate.valid_to)
        readings = rules.relevant_readings(tx.readings(start - _CLOSING_SEARCH, end + _CLOSING_SEARCH, rules.ROLES),
                                           tank.id, gen.id)
        result = rules.assess(start=start, end=end, tank_asset_id=tank.id, generator_asset_id=gen.id,
                              readings=readings, records=records, accuracy=accuracy, sfc=sfc, no_load=no_load)
        evidence_ids = sorted({r.id for r in readings})
        digest = rules.input_sha256(night_date=night_date, start=start, end=end, tank_asset_id=tank.id,
                                    generator_asset_id=gen.id, accuracy=accuracy, sfc=sfc, no_load=no_load,
                                    evidence_ids=evidence_ids, records=records)
        if latest is not None and latest.input_sha256 == digest:
            return AssessResult(latest, False)
        row = {"tank_asset_id": tank.id, "generator_asset_id": gen.id, "night_date": night_date,
               "window_start": start, "window_end": end, "state": result.state, "reason": result.reason,
               "residual_low": rules.fmt(result.residual_low), "residual_high": rules.fmt(result.residual_high),
               "gap_minutes": result.gap_minutes,
               "gap_spans": [[rules.iso(a), rules.iso(b)] for a, b in result.gap_spans],
               "limitations": list(result.limitations), "terms": result.terms, "evidence_ids": evidence_ids,
               "record_ids": sorted([r.root_id, r.head_id] for r in records), "input_sha256": digest}
        return AssessResult(tx.append(latest, row), True)
