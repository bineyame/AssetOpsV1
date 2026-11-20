"""The leaf factor catalogue (2a spec §5; D-2A.3).

One ID and one unit for every leaf of the three declared structures. The IDs
are the pack manifest's `factor_map` keys; this module does not read the
manifest (the parity test compares the two). A shared ID (`staff`,
`outstanding`, `liability`, `period_days`) is one `Factor` across verticals.
An ID is never reused for a different quantity: a change of ID or unit is a
new format version, never an edit of this table (D-2A.2).

Which source fills a leaf and what its absence means (`filled_by`, `absent`)
belong to the structure registry (3B1, 3B6), not to this catalogue.
`penalty_rate` takes its value from the rights register 9a builds, not from a
v1 record field; `contract_crate_days` and `contract_rate` are option-only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from types import MappingProxyType

from assetops_contracts.canonical.units import Unit, parse_unit

STRUCTURE_KEYS = ("MINI_GRID", "COLD_CHAIN", "EV_DEPOT_CAPTIVE")

# The syntax of every factor ID, leaf or node. Always applied with `fullmatch`.
FACTOR_ID_PATTERN = re.compile(r"[a-z][a-z0-9_]{0,63}", re.ASCII)


@dataclass(frozen=True)
class Factor:
    id: str
    structures: frozenset[str]
    unit: Unit
    display: str

    @property
    def money(self) -> bool:
        return self.unit.is_money


_MG = ("MINI_GRID",)
_CC = ("COLD_CHAIN",)
_EV = ("EV_DEPOT_CAPTIVE",)
_MG_CC = ("MINI_GRID", "COLD_CHAIN")

# Spec §5's table, row for row: (factor ID, structure keys, unit text, display).
_TABLE = (
    ("delivered_kwh", _MG, "KWH", "kWh"),
    ("technical_loss_kwh", _MG, "KWH", "kWh"),
    ("unexplained_loss_kwh", _MG, "KWH", "kWh"),
    ("adjustments_kwh", _MG, "KWH", "kWh"),
    ("unmapped_kwh", _MG, "KWH", "kWh"),
    ("tariff", _MG, "MONEY/KWH", "per kWh"),
    ("productive_kwh", _MG, "KWH", "kWh"),
    ("productive_tariff", _MG, "MONEY/KWH", "per kWh"),
    ("in_transit", _MG, "MONEY", "money"),
    ("outstanding", _MG_CC, "MONEY", "money"),
    ("necessary_l", _MG, "L", "L"),
    ("candidate_l", _MG, "L", "L"),
    ("unexplained_l", _MG, "L", "L"),
    ("extra_l", _MG, "L", "L"),
    ("diesel_price", _MG, "MONEY/L", "per L"),
    ("battery_throughput_kwh", _MG, "KWH", "kWh"),
    ("wear_rate", _MG, "MONEY/KWH", "per kWh throughput"),
    ("om", _MG, "MONEY", "money"),
    ("staff", _MG_CC, "MONEY", "money"),
    ("collection_cost", _MG, "MONEY", "money"),
    ("reduced_days", _MG, "DAY", "days"),
    ("hours_per_day", _MG, "HOUR/DAY", "hours a day"),
    ("major_assets", _MG, "1", "assets"),
    ("unserved_critical_kwh", _MG, "KWH", "kWh"),
    ("customer_hours_interrupted", _MG, "HOUR", "customer-hours"),
    ("field_visits", _MG, "1", "visits"),
    ("liability", _MG_CC, "MONEY", "money"),
    ("period_days", _MG_CC, "DAY", "days"),
    ("standby_kw", _MG, "KWH/HOUR", "kW"),
    ("lost_unit_kw", _MG, "KWH/HOUR", "kW"),
    ("dawn_days_below", _MG, "DAY", "days"),
    ("crate_days", _CC, "DAY", "crate-days"),
    ("rate", _CC, "MONEY/DAY", "per crate-day"),
    ("contract_crate_days", _CC, "DAY", "crate-days"),
    ("contract_rate", _CC, "MONEY/DAY", "per crate-day"),
    ("base_kwh", _CC, "KWH", "kWh"),
    ("k_kwh_per_crate_day", _CC, "KWH/DAY", "kWh per crate-day"),
    ("model_factor", _CC, "1", "ratio"),
    ("excess_kwh", _CC, "KWH", "kWh"),
    ("elec_price", _CC, "MONEY/KWH", "per kWh"),
    ("maint", _CC, "MONEY", "money"),
    ("handling", _CC, "MONEY", "money"),
    ("uncovered_nights", _CC, "DAY", "nights"),
    ("backup_unproven_days", _CC, "DAY", "days"),
    ("excursion_crates", _CC, "1", "crates"),
    ("excursion_days", _CC, "DAY", "days"),
    ("batches_exposed", _CC, "1", "batches"),
    ("cooling_minutes_unavailable", _CC, "MINUTE", "minutes"),
    ("minutes_per_day", _CC, "MINUTE/DAY", "minutes a day"),
    ("capacity_crate_days", _CC, "DAY", "crate-days"),
    ("chargers_in_service", _EV, "1", "chargers"),
    ("chargers_installed", _EV, "1", "chargers"),
    ("charger_kw", _EV, "KWH/HOUR", "kW per charger"),
    ("import_limit_kw", _EV, "KWH/HOUR", "kW"),
    ("window_h", _EV, "HOUR/DAY", "hours a night"),
    ("buses", _EV, "1", "buses"),
    ("kwh_per_bus_night", _EV, "KWH/DAY", "kWh per bus-night"),
    ("nights_in_period", _EV, "DAY", "nights"),
    ("peak_kwh", _EV, "KWH", "kWh"),
    ("kwh_2200_2400", _EV, "KWH", "kWh"),
    ("kwh_0000_0500", _EV, "KWH", "kWh"),
    ("max_kw", _EV, "KWH/HOUR", "kW"),
    ("peak_price", _EV, "MONEY/KWH", "per kWh"),
    ("offpeak_price", _EV, "MONEY/KWH", "per kWh"),
    ("night_price", _EV, "MONEY/KWH", "per kWh"),
    ("demand_rate", _EV, "HOUR*MONEY/KWH", "per kW a month"),
    ("maintenance", _EV, "MONEY", "money"),
    ("short_nights", _EV, "DAY", "nights"),
    ("spare_bus_nights", _EV, "DAY", "bus-nights"),
    ("covered_bus_nights", _EV, "DAY", "bus-nights"),
    ("extra_missed_departures", _EV, "DAY", "departures (bus-nights)"),
    ("charger_out_days", _EV, "DAY", "days"),
    ("penalty_rate", _EV, "MONEY/DAY", "per missed departure"),
)


def _build() -> MappingProxyType:
    catalogue: dict[str, Factor] = {}
    for factor_id, structures, unit_text, display in _TABLE:
        if FACTOR_ID_PATTERN.fullmatch(factor_id) is None or factor_id in catalogue:
            raise ValueError(f"CANONICAL_FACTOR {factor_id}")
        catalogue[factor_id] = Factor(factor_id, frozenset(structures), parse_unit(unit_text), display)
    return MappingProxyType(catalogue)


LEAF_FACTORS = _build()


def leaves_of(key: str) -> tuple[str, ...]:
    """The leaf IDs of one structure key, in this catalogue's table order.

    The order is the table's, not the manifest's `factor_map` order. An unknown
    structure key raises `KeyError`.
    """
    if key not in STRUCTURE_KEYS:
        raise KeyError(key)
    return tuple(f.id for f in LEAF_FACTORS.values() if key in f.structures)
