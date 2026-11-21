"""4a unit 2 (spec §4.2; D-4A.2, D-4A.3, D-4A.14, D-4A.23, D-4A.24): the energy inputs of one Site-month.

`feeder_month` (pure) turns the mini-depth reader's feeder rows into `FeederMonth`: one `minigrid-roles-4` set in force
over the whole month, its `feeder_demand` assets, each Site-local day's kWh from `productive_energy` (a day counts
only when fully measured without conflict), the origin of the readings used (SIMULATED is `demo-simulated`, any
other `unknown`) and the declared band of each feeder over every Foundation revision. `StoreEnergyInputs` adds the
commercial records (one `latest_revisions` call, one cutoff). A live read passes `known_at` None to both reads.
Nothing here catches a refusal or an outage.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID
from zoneinfo import ZoneInfo

from assetops_backend.chain.ports import SiteRef
from assetops_backend.commercial.months import _parse  # 3A4's rule: a stored canonical that does not parse raises
from assetops_backend.site_outcomes.productive_use import productive_energy
from assetops_backend.structure.energy.rules import (
    BINDINGS_CHANGED,
    CHANGED,
    DECLARED,
    NOT_BOUND,
    NOT_DECLARED,
    ONE_SET,
    Adjustment,
    Assignment,
    Charge,
    EnergyInputs,
    FeederInput,
    FeederMonth,
    MeterRead,
)
from assetops_backend.structure.evaluate import ORIGIN_UNKNOWN
from assetops_backend.structure.sources import month_window

BAND_KEY = "technical-loss-band"
SIMULATED, DEMO_SIMULATED = "SIMULATED", "demo-simulated"
KWH_UNIT = "kWh"
KINDS = ("CHARGE", "ADJUSTMENT", "CUSTOMER_METER_READ", "METER_ASSIGNMENT")


class FeederRowsPort(Protocol):
    def feeder_month(self, *, tenant_id: UUID, site_id: UUID, lo: datetime, hi: datetime,
                     known_at: datetime | None) -> Any: ...


class RevisionsPort(Protocol):
    def latest_revisions(self, tenant_id: UUID, *, site_id: UUID | None = None, kind: str | None = None,
                         recognition_period: str | None = None, known_at: datetime | None = None) -> Any: ...


def _covers(valid_from: datetime, valid_to: datetime | None, lo: datetime, hi: datetime) -> bool:
    return valid_from <= lo and (valid_to is None or valid_to >= hi)


def _band(foundations: Any, code: str) -> tuple[str, Decimal | None]:
    """D-4A.3: every revision declares the same band on the LOAD component named `code`, else not declared or
    changed."""
    values: list[Decimal | None] = []
    for row in foundations:
        content = row[3]
        found = None
        for comp in content.get("components") or ():
            if comp.get("component_id") == code and comp.get("component_type") == "LOAD":
                for prop in comp.get("properties") or ():
                    if prop.get("property_key") == BAND_KEY:
                        found = Decimal(str(prop.get("value")))
        values.append(found)
    if not values or any(v is None for v in values):
        return NOT_DECLARED, None
    if len(set(values)) > 1:
        return CHANGED, None
    return DECLARED, values[0]


def feeder_month(rows: Any, lo: datetime, hi: datetime, first: date, last: date, tz: str) -> FeederMonth:
    """Spec §4.2 "FeederMonth": the feeder side of one Site-month from the reader's rows."""
    days = (last - first).days + 1
    sets = tuple(rows.binding_sets)
    set_ids = {s[0] for s in sets}
    bindings = tuple(b for b in rows.feeder_bindings if b[0] in set_ids)
    if not sets or not bindings:
        return FeederMonth(NOT_BOUND, (), days)
    if len(sets) > 1 or not _covers(sets[0][1], sets[0][2], lo, hi) or \
            not all(_covers(b[2], b[3], lo, hi) for b in bindings):
        return FeederMonth(BINDINGS_CHANGED, (), days)
    codes = {str(asset_id): code for code, asset_id in rows.assets}
    zone = ZoneInfo(tz)
    edges = [datetime.combine(first + timedelta(days=k), time(0), zone).astimezone(timezone.utc)
             for k in range(days + 1)]
    feeders = []
    for asset_id in {b[1] for b in bindings}:
        mine = [r for r in rows.readings if str(r["asset_id"]) == str(asset_id)]
        day_kwh: list[Decimal | None] = []
        for k in range(days):
            got = productive_energy(mine, edges[k], edges[k + 1])
            whole = got["measured_seconds"] == int((edges[k + 1] - edges[k]).total_seconds())
            day_kwh.append(got["kwh"] if got["kwh"] is not None and not got["conflict_assets"] and whole else None)
        used = [r for r in mine if r.get("quality") == "GOOD" and r.get("value_kw") is not None
                and r["end"] > lo and r["start"] < hi]
        origins = {DEMO_SIMULATED if r.get("source_mode") == SIMULATED else ORIGIN_UNKNOWN for r in used}
        code = codes.get(str(asset_id), str(asset_id))
        state, pct = _band(rows.foundations, code)
        feeders.append(FeederInput(asset_id, code, tuple(day_kwh),
                                   tuple(o for o in (DEMO_SIMULATED, ORIGIN_UNKNOWN) if o in origins), state, pct))
    return FeederMonth(ONE_SET, tuple(sorted(feeders, key=lambda f: f.asset_code)), days)


def read_kwh(body: Mapping[str, Any], quantity: tuple[Decimal, str] | None) -> Decimal:
    """Spec §2.4 "Read kWh": the quantity of an INTERVAL read; `register_end - register_start` of a REGISTER read."""
    if body.get("read_type") == "REGISTER":
        return Decimal(str(body["register_end"])) - Decimal(str(body["register_start"]))
    assert quantity is not None and quantity[1] == KWH_UNIT
    return quantity[0]


class StoreEnergyInputs:
    """`EnergyInputsPort` over the mini-depth reader and the commercial store (spec §4.2)."""

    def __init__(self, mini: FeederRowsPort, store: RevisionsPort) -> None:
        self._mini = mini
        self._store = store

    def read(self, site: SiteRef, month: str, known_at: datetime | None, now: datetime) -> EnergyInputs:
        lo, hi, first, last = month_window(month, site.timezone)
        next_first = last + timedelta(days=1)
        closed = hi <= (known_at or now)
        rows = self._mini.feeder_month(tenant_id=site.tenant_id, site_id=site.site_id, lo=lo, hi=hi,
                                       known_at=known_at)
        feeders = feeder_month(rows, lo, hi, first, last, site.timezone)
        revisions = self._store.latest_revisions(site.tenant_id, site_id=site.site_id, known_at=known_at)
        held = frozenset(r.kind for r in revisions)
        charges, adjustments, reads, assignments = [], [], [], []
        for row in revisions:
            if row.kind not in KINDS:
                continue
            record = _parse(row)
            if row.kind == "CHARGE" and row.recognition_period == month:
                qty = record.quantity
                charges.append(Charge(
                    str(record.body["line_type"]), record.body.get("tariff_class"),
                    qty[0] if qty is not None and qty[1] == KWH_UNIT else None, record.amount[0], record.amount[1],
                    record.subject, str(record.body["account_ref"]), row.provenance, row.source_system))
            elif row.kind == "ADJUSTMENT" and row.recognition_period == month:
                qty = record.quantity
                if qty is not None and qty[1] == KWH_UNIT:
                    adjustments.append(Adjustment(qty[0], row.provenance, row.source_system))
            elif row.kind == "CUSTOMER_METER_READ":
                if row.effective_from < next_first and row.effective_to > first:
                    reads.append(MeterRead(record.subject[1], str(record.body["meter_ref"]), row.effective_from,
                                           row.effective_to, read_kwh(record.body, record.quantity), row.provenance,
                                           row.source_system))
            elif row.kind == "METER_ASSIGNMENT":
                assignments.append(Assignment(record.subject[1], str(record.body["meter_ref"]),
                                              str(record.body["customer_ref"]), row.effective_from,
                                              row.effective_to))
        return EnergyInputs(month, first, next_first, closed, feeders, held, tuple(charges), tuple(adjustments),
                            tuple(reads), tuple(assignments))


__all__ = ["BAND_KEY", "StoreEnergyInputs", "feeder_month", "read_kwh"]
