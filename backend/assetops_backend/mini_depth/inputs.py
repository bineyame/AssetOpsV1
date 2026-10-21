"""W4-02 unit 4 step 2: the cutoff-selected inputs of one Site-local hour, adapted for the pure rules.

`D-2026-10-20-w4-02-buildspec`. Closure 1 Q4 (one Site-local clock hour; first occurrence of local noon, a
nonexistent noon refuses `INVALID_WINDOW`), Q13 (own parameterized accepted-input query, `e.received_at <= :k AND
d.decided_at <= :k`, never the shared `_EVIDENCE`), Q15 (basis identities), closure 4 S8 (pinned `site.timezone`),
q3 ruling 4 (the last cutoff-visible supply state before the hour), q4 rulings 2-3 and q5 ruling 4 (the pinned
critical LOAD asset; only pinned generator/tank/critical rows reach fuel and backup) and q5 ruling 5 (the knowledge
cutoff is the caller's lease instant, used unchanged).

The SQL lives in `store.py:read_hour_rows` (the one mini-depth database module); this module only adapts its rows.
The caller owns the connection and its REPEATABLE READ transaction; nothing here reads a clock or writes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from assetops_backend.financials import fuel_cost
from assetops_backend.mini_depth import rules
from assetops_backend.mini_depth.store import read_hour_rows
from assetops_backend.mini_depth.rules import (
    FuelInputs, LoadAsset, Observation, Reading, RenewableInputs, SfcValue, Window,
)
from assetops_backend.sites.binding_roles import ROLE_SET_MINIGRID_4

#: Migration 0029's closed mini-depth gate roles: the only roles the hour query selects.
QUERY_ROLES: tuple[str, ...] = (
    "generator_state", "generator_power", "feeder_demand", "battery_soc", "pv_power", "pv_irradiance",
    "battery_power", "fuel_level", "pv_available_power", "pcs_discharge_capability",
    "critical_load_requested_power", "critical_load_delivered_power", "storage_charge_requested_power",
    "feeder_requested_power", "site_supply_state", "mini_backup_start_event", "mini_backup_bus_state",
)
#: STATE/EVENT roles adapted to `Observation`; every other role is a `Reading`.
OBSERVATION_ROLES = frozenset({rules.SITE_SUPPLY, rules.BACKUP_BUS, rules.START_EVENT})
CRITICAL_ROLES = (rules.CRITICAL_REQUESTED, rules.CRITICAL_DELIVERED)
#: Foundation property keys and the one unit each must carry (no conversion is guessed).
PROPERTY_UNITS: dict[str, str] = {"pv-available-uncertainty": "kW", "renewable-retained-margin": "kW",
                                  "backup-recovery-target": "min"}
INVALID_WINDOW = "INVALID_WINDOW"
CONFIGURATION_MISSING = "CONFIGURATION_MISSING"

class MiniInputsRefused(ValueError):
    """The hour cannot be assessed as asked: `code` is `INVALID_WINDOW` or `CONFIGURATION_MISSING`."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def zone(name: str | None) -> ZoneInfo:
    """S8: the pinned IANA zone; missing or invalid refuses `INVALID_WINDOW` rather than guessing UTC."""
    if not name:
        raise MiniInputsRefused(INVALID_WINDOW, "the Site has no time zone")
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise MiniInputsRefused(INVALID_WINDOW, f"unknown Site time zone {name!r}") from error


def local_hour(day: date, hour: int, tz_name: str) -> Window:
    """One Site-local clock hour `hour:00` on `day` as UTC `[start, start + 1 h)`: the first offset occurrence
    (fold 0); a nonexistent local instant refuses `INVALID_WINDOW` (closure 1 Q4)."""
    tz = zone(tz_name)
    naive = datetime.combine(day, time(hour))
    local = naive.replace(tzinfo=tz, fold=0)
    start = local.astimezone(timezone.utc)
    if start.astimezone(tz).replace(tzinfo=None) != naive:
        raise MiniInputsRefused(INVALID_WINDOW, f"{naive.isoformat()} does not exist in {tz_name}")
    return Window(start, start + timedelta(hours=1))


def local_noon(day: date, tz_name: str) -> Window:
    return local_hour(day, 12, tz_name)


def local_day_of(window: Window, tz_name: str) -> date:
    return window.start.astimezone(zone(tz_name)).date()


@dataclass(frozen=True)
class SelectedRow:
    """One selected accepted row's identity for the basis (Q15 `committed_watermark`, citations)."""

    evidence_id: UUID
    role: str
    asset_id: UUID | None
    decided_at: datetime
    prior: bool  # the q3-4 supply witness from before the hour


@dataclass(frozen=True)
class HourInputs:
    tenant_id: UUID
    site_id: UUID
    window: Window
    local_day: date
    site_timezone: str
    knowledge_cutoff: datetime
    foundation_revision_id: UUID
    binding_set_revision_id: UUID
    readings: tuple[Reading, ...]
    observations: tuple[Observation, ...]
    selected: tuple[SelectedRow, ...]
    renewable: RenewableInputs
    loads: tuple[LoadAsset, ...]
    fuel: FuelInputs
    generator_asset_id: UUID | None
    tank_asset_id: UUID | None
    critical_asset_id: UUID | None
    recovery_target_min: Decimal | None
    #: property key -> the Foundation revision that supplied it (absent when not authored).
    property_revision_ids: Mapping[str, UUID]

    @property
    def committed_watermark(self) -> datetime | None:
        """Q15: the latest accepted disposition time in the selected set; null when empty."""
        return max((r.decided_at for r in self.selected), default=None)

    @property
    def evidence_ids(self) -> tuple[UUID, ...]:
        return tuple(sorted({r.evidence_id for r in self.selected}, key=str))

    def fuel_readings(self) -> list[Reading]:
        """q4 ruling 3: only the pinned generator's power and the pinned tank's level reach the fuel rule."""
        return [r for r in self.readings
                if (r.role == rules.GENERATOR_POWER and r.asset_id == self.generator_asset_id is not None)
                or (r.role == "fuel_level" and r.asset_id == self.tank_asset_id is not None)]

    def backup_readings(self) -> list[Reading]:
        """q4 ruling 3 / q5 ruling 4: the pinned generator and pinned critical rows; unrelated assets' rows are cited
        by the hour basis, not judged (the rule pins the critical asset too)."""
        return [r for r in self.readings
                if (r.role == rules.GENERATOR_POWER and r.asset_id == self.generator_asset_id is not None)
                or (r.role in CRITICAL_ROLES and r.asset_id == self.critical_asset_id is not None)]

    def digest_basis(self) -> dict[str, Any]:
        """The canonical identity the input digest covers (S8 puts `site_timezone` in it)."""
        return {
            "site_timezone": self.site_timezone,
            "window": [fuel_cost.iso(self.window.start), fuel_cost.iso(self.window.end)],
            "knowledge_cutoff": fuel_cost.iso(self.knowledge_cutoff),
            "foundation_revision_ids": [str(self.foundation_revision_id)],
            "binding_set_revision_ids": [str(self.binding_set_revision_id)],
            "accepted_evidence_ids": [str(i) for i in self.evidence_ids],
            "property_revision_ids": {k: str(v) for k, v in sorted(self.property_revision_ids.items())},
            "sfc_property_revision_ids": sorted(str(s.property_revision_id) for s in self.fuel.sfc),
            "critical_asset_id": None if self.critical_asset_id is None else str(self.critical_asset_id),
        }

    @property
    def input_sha256(self) -> str:
        """The 0029 column form `sha256:<64 lowercase hex>` of the canonical digest basis."""
        return "sha256:" + fuel_cost.sha256_canonical(self.digest_basis())


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _content(raw: Any) -> dict[str, Any]:
    return raw if isinstance(raw, dict) else json.loads(raw)


def _property(components: Sequence[Mapping[str, Any]], key: str) -> Decimal | None:
    """The single authored `key` with its declared unit across the Foundation's components; else None."""
    items = [p for c in components for p in (c.get("properties") or ()) if p.get("property_key") == key]
    if len(items) != 1 or items[0].get("unit") != PROPERTY_UNITS[key]:
        return None
    return _decimal(items[0].get("value"))


def _sfc(content: Mapping[str, Any], code: str | None) -> Decimal | None:
    """`fuel_cost` SFC selection: the single positive `specific-fuel-consumption` in L/kWh of the generator."""
    found = [p for c in content.get("components") or () if c.get("component_id") == code
             for p in (c.get("properties") or ()) if p.get("property_key") == fuel_cost.SFC_PROPERTY]
    if len(found) != 1 or found[0].get("unit") != fuel_cost.SFC_UNIT:
        return None
    value = _decimal(found[0].get("value"))
    return value if value is not None and value > 0 else None


def _one_bound(bindings: Sequence[Any], role: str) -> UUID | None:
    assets = {b[2] for b in bindings if b[1] == role}
    return next(iter(assets)) if len(assets) == 1 else None


def load_hour_inputs(c: Any, tenant_id: UUID, site_id: UUID, window: Window,
                     knowledge_cutoff: datetime) -> HourInputs:
    """Select (on the caller's connection) and adapt every input of one Site-local hour known at the cutoff."""
    k = knowledge_cutoff
    raw = read_hour_rows(c, tenant_id, site_id, window.start, window.end, k, role_set=ROLE_SET_MINIGRID_4,
                         roles=QUERY_ROLES, supply_role=rules.SITE_SUPPLY)
    tz_name = raw.timezone
    zone(tz_name)
    foundations = raw.foundations
    if len(foundations) != 1 or foundations[0][1] > window.start or (
            foundations[0][2] is not None and foundations[0][2] < window.end):
        raise MiniInputsRefused(CONFIGURATION_MISSING, "exactly one Foundation revision must cover the hour")
    f_id, content = foundations[0][0], _content(foundations[0][3])
    sets = raw.binding_sets
    if len(sets) != 1 or sets[0][1] > window.start or (sets[0][2] is not None and sets[0][2] < window.end):
        raise MiniInputsRefused(CONFIGURATION_MISSING, f"exactly one {ROLE_SET_MINIGRID_4} set must cover the hour")
    set_id = sets[0][0]
    bindings = raw.bindings
    by_id = {b[0]: b for b in bindings}
    assets = dict(raw.assets)
    codes = {v: key for key, v in assets.items()}
    components = list(content.get("components") or ())
    by_code = {x.get("component_id"): x for x in components}

    # Foundation properties (closure 1 Q9), each pinned to this Foundation revision.
    values = {key: _property(components, key) for key in PROPERTY_UNITS}
    property_revision_ids = {key: f_id for key, v in values.items() if v is not None}

    # q4 ruling 2 / q5 ruling 4: the first `critical-load-priority` member, a LOAD asset, and every bound critical
    # role names exactly that asset; otherwise no pin.
    controls = [x for x in content.get("site_controls") or () if x.get("control_key") == "critical-load-priority"]
    members = list(controls[0].get("members") or ()) if len(controls) == 1 else []
    critical = assets.get(members[0]) if members and (by_code.get(members[0]) or {}).get(
        "component_type") == "LOAD" else None
    bound_critical = {b[2] for b in bindings if b[1] in CRITICAL_ROLES}
    if critical is None or bound_critical != {critical}:
        critical = None

    feeders = sorted({b[2] for b in bindings if b[1] == rules.FEEDER_DEMAND}, key=str)
    requested = {b[2] for b in bindings if b[1] == rules.FEEDER_REQUESTED}
    loads = tuple(LoadAsset(a, codes.get(a, ""), str((by_code.get(codes.get(a)) or {}).get("display_name") or ""),
                            a == critical, a in requested) for a in feeders)
    generator, tank = _one_bound(bindings, rules.GENERATOR_POWER), _one_bound(bindings, "fuel_level")

    rows, prior = raw.accepted, raw.prior_supply
    readings: list[Reading] = []
    observations: list[Observation] = []
    selected: list[SelectedRow] = []
    foundation_ids = {f_id}
    for r, is_prior in [*((r, False) for r in rows), *((r, True) for r in prior)]:
        b = by_id.get(r[13])
        if b is None or b[1] != r[1] or b[2] != r[2] or b[3] > r[3] or (b[4] is not None and r[3] >= b[4]):
            continue  # not bound (in force) under the pinned roles-4 set: not an input of this hour
        selected.append(SelectedRow(r[0], r[1], r[2], r[15], is_prior))
        if r[1] in OBSERVATION_ROLES:
            observations.append(Observation(r[0], r[12], r[1], r[3], r[6], r[7] if r[1] != rules.START_EVENT else None,
                                            r[9], r[10], r[11]))
        else:
            readings.append(Reading(r[0], r[12], r[1], r[2], r[3], r[4], r[5], r[6], _decimal(r[7]), r[8]))
            if r[1] == rules.GENERATOR_POWER and r[2] == generator:
                foundation_ids.add(r[14])

    # SFC per `fuel_cost`: each as-accepted Foundation revision of the generator rows (and the pinned one), with
    # its validity range; the rule requires one in force over each whole interval.
    sfc: list[SfcValue] = []
    gen_code = codes.get(generator) if generator is not None else None
    for fr in sorted((raw.row_foundations[i] for i in foundation_ids if i in raw.row_foundations),
                     key=lambda x: str(x[0])):
        value = _sfc(_content(fr[3]), gen_code)
        if value is not None:
            sfc.append(SfcValue(fr[0], value, fr[1], fr[2]))

    return HourInputs(
        tenant_id=tenant_id, site_id=site_id, window=window, local_day=local_day_of(window, tz_name),
        site_timezone=tz_name, knowledge_cutoff=k, foundation_revision_id=f_id, binding_set_revision_id=set_id,
        readings=tuple(readings), observations=tuple(observations), selected=tuple(selected),
        renewable=RenewableInputs(values["pv-available-uncertainty"], values["renewable-retained-margin"],
                                  tuple(feeders), critical),
        loads=loads, fuel=FuelInputs(tuple(sfc), fuel_cost.MULTIPLIER), generator_asset_id=generator,
        tank_asset_id=tank, critical_asset_id=critical, recovery_target_min=values["backup-recovery-target"],
        property_revision_ids=property_revision_ids)
