"""3B6: the captive EV depot structure, version 1 (spec §2.2; D-3B6.1, D-3B6.2, D-3B6.3, D-3B6.9).

One literal tuple of 42 rows: the 23 leaves in `canonical.leaves_of("EV_DEPOT_CAPTIVE")` order, then the 19 nodes in
the manifest's `structures.EV_DEPOT_CAPTIVE` order. Every literal is written here, never read from the catalogue or the
manifest (W2); the parity test compares them. There is no `revenue` row: the registry declares it not applicable
(`not_applicable`, D-3B6.3), and `contribution` is `0 - cost_to_serve` as the manifest states. No row states a total
(D-3B6.2), carries a tolerance (D-3B6.9) or a lever (step 6).
"""

from __future__ import annotations

from decimal import Decimal

from assetops_backend.structure.registry import HOMES, FactorRow, FilledBy, Home
from assetops_contracts.canonical.units import DAY, HOUR, KW, KWH, MONEY, ONE, Unit

_GROW, _OPTIMIZE, _PROTECT = HOMES["grow"], HOMES["optimize"], HOMES["protect"]
_ABOVE, _CALENDAR = HOMES["above"], HOMES["calendar"]


def _leaf(factor_id: str, unit: Unit, home: Home, family: str, kind: str, absent: str,
          words: str | None = None, *, composes: str, neutral: Decimal | None = None) -> FactorRow:
    return FactorRow(factor_id, None, unit, home, FilledBy(family, kind, words), absent, None,
                     neutral=neutral, composes=composes)


def _node(factor_id: str, expression: str, unit: Unit, home: Home, *, composes: str) -> FactorRow:
    return FactorRow(factor_id, expression, unit, home, None, None, None, composes=composes)


_REGISTER = "charger register (site configuration)"
_TOU = "CHARGE (utility time-of-use line)"

ROWS: tuple[FactorRow, ...] = (
    # ---- leaves (23)
    _leaf("chargers_in_service", ONE, Home(_PROTECT, "P1"),
          "OBSERVER", "charging capacity (charger register, ev_connector_state, ev_connector_fault)", "MISSING",
          composes="SUM"),
    _leaf("chargers_installed", ONE, Home(_OPTIMIZE, "O2"), "DECLARED", _REGISTER, "MISSING", composes="SUM"),
    _leaf("charger_kw", KW, Home(_PROTECT, "P1"), "DECLARED", _REGISTER, "MISSING", composes="NONE"),
    _leaf("import_limit_kw", KW, Home(_PROTECT, "P1"), "DECLARED", "grid connection (site configuration)", "MISSING",
          composes="NONE"),
    _leaf("window_h", HOUR / DAY, Home(_PROTECT, "P1"), "COMMERCIAL_RECORD", "FLEET_ROSTER", "MISSING",
          composes="NONE"),
    _leaf("buses", ONE, Home(_GROW, "G2"), "COMMERCIAL_RECORD", "FLEET_ROSTER", "MISSING", composes="SUM"),
    _leaf("kwh_per_bus_night", KWH / DAY, Home(_PROTECT, "P1"), "COMMERCIAL_RECORD", "FLEET_ROSTER", "MISSING",
          composes="NONE"),
    _leaf("nights_in_period", DAY, Home(_CALENDAR, None), "CALENDAR", "period nights", "NEVER_EMPTY",
          composes="NONE"),
    _leaf("peak_kwh", KWH, Home(_OPTIMIZE, "O1"), "COMMERCIAL_RECORD", _TOU, "ZERO_WHEN_HELD", composes="SUM"),
    _leaf("kwh_2200_2400", KWH, Home(_OPTIMIZE, "O1"), "COMMERCIAL_RECORD", _TOU, "MISSING", composes="SUM"),
    _leaf("kwh_0000_0500", KWH, Home(_OPTIMIZE, "O1"), "COMMERCIAL_RECORD", _TOU, "ZERO_WHEN_HELD", composes="SUM"),
    _leaf("max_kw", KW, Home(_OPTIMIZE, "O1"), "COMMERCIAL_RECORD", "CHARGE (utility demand line)", "ZERO_WHEN_HELD",
          composes="NONE"),
    _leaf("peak_price", MONEY / KWH, Home(_OPTIMIZE, "O1"), "COMMERCIAL_RECORD", "TARIFF_SCHEDULE", "MISSING",
          composes="NONE"),
    _leaf("offpeak_price", MONEY / KWH, Home(_OPTIMIZE, "O1"), "COMMERCIAL_RECORD", "TARIFF_SCHEDULE", "MISSING",
          composes="NONE"),
    _leaf("night_price", MONEY / KWH, Home(_OPTIMIZE, "O1"), "COMMERCIAL_RECORD", "TARIFF_SCHEDULE", "MISSING",
          composes="NONE"),
    _leaf("demand_rate", MONEY / KW, Home(_OPTIMIZE, "O1"), "COMMERCIAL_RECORD", "TARIFF_SCHEDULE", "MISSING",
          composes="NONE"),
    _leaf("maintenance", MONEY, Home(_OPTIMIZE, "O1"), "COMMERCIAL_RECORD", "EXPENSE (OM)", "MISSING",
          words="Service contractor invoice", composes="SUM"),
    _leaf("short_nights", DAY, Home(_PROTECT, "P1"),
          "OBSERVER", "charging capacity (FLEET_ROSTER, ev_connector_state)", "MISSING", composes="SUM"),
    _leaf("spare_bus_nights", DAY, Home(_PROTECT, "P1"), "COMMERCIAL_RECORD", "FLEET_ROSTER", "ZERO_WHEN_HELD",
          composes="SUM"),
    _leaf("covered_bus_nights", DAY, Home(_PROTECT, "P1"), "COMMERCIAL_RECORD", "FLEET_ROSTER (an option's cover)",
          "OPTION_ONLY", composes="SUM", neutral=Decimal("0")),
    _leaf("extra_missed_departures", DAY, Home(_PROTECT, "P1"),
          "COMMERCIAL_RECORD", "DEPARTURE (an option's extra misses)", "OPTION_ONLY",
          composes="SUM", neutral=Decimal("0")),
    _leaf("charger_out_days", DAY, Home(_PROTECT, "P2"), "OPERATIONAL_RECORD", "SERVICE_TICKET (fault and restore)",
          "ZERO_WHEN_HELD", composes="SUM"),
    _leaf("penalty_rate", MONEY / DAY, Home(_OPTIMIZE, "O1"),
          "DOCUMENT", "CONTRACT_DOCUMENT (service contract penalty term)", "ZERO_WHEN_HELD", composes="NONE"),
    # ---- nodes (19), expressions verbatim from the manifest's structures.EV_DEPOT_CAPTIVE
    _node("deliverable_kwh_night", "min(chargers_in_service * charger_kw, import_limit_kw) * window_h", KWH / DAY,
          Home(_PROTECT, "P1"), composes="NONE"),
    _node("scheduled_kwh_night", "(peak_kwh + kwh_2200_2400 + kwh_0000_0500) / nights_in_period", KWH / DAY,
          Home(_OPTIMIZE, "O2"), composes="NONE"),
    _node("supplied_kwh_night", "min(deliverable_kwh_night, scheduled_kwh_night)", KWH / DAY, Home(_PROTECT, "P1"),
          composes="NONE"),
    _node("required_kwh_night", "buses * kwh_per_bus_night", KWH / DAY, Home(_PROTECT, "P1"), composes="NONE"),
    _node("buses_short_per_night", "ceil(max(required_kwh_night - supplied_kwh_night, 0) / kwh_per_bus_night)", ONE,
          Home(_PROTECT, "P1"), composes="NONE"),
    _node("departures_required", "buses * nights_in_period", DAY, Home(_GROW, "G2"), composes="SUM"),
    _node("departures_missed",
          "max(buses_short_per_night * short_nights - spare_bus_nights - covered_bus_nights, 0)"
          " + extra_missed_departures",
          DAY, Home(_PROTECT, "P1"), composes="SUM"),
    _node("nights_below_required", "min(buses_short_per_night, 1) * short_nights", DAY, Home(_PROTECT, "P1"),
          composes="SUM"),
    _node("charger_days_out_of_service", "charger_out_days", DAY, Home(_PROTECT, "P2"), composes="SUM"),
    _node("departures_met", "departures_required - departures_missed", DAY, Home(_PROTECT, "P1"), composes="SUM"),
    _node("peak_cost", "peak_kwh * peak_price", MONEY, Home(_OPTIMIZE, "O1"), composes="SUM"),
    _node("offpeak_cost", "kwh_2200_2400 * offpeak_price", MONEY, Home(_OPTIMIZE, "O1"), composes="SUM"),
    _node("night_cost", "kwh_0000_0500 * night_price", MONEY, Home(_OPTIMIZE, "O1"), composes="SUM"),
    _node("demand_cost", "max_kw * demand_rate", MONEY, Home(_OPTIMIZE, "O1"), composes="SUM"),
    _node("energy_cost", "peak_cost + offpeak_cost + night_cost + demand_cost", MONEY, Home(_OPTIMIZE, "O1"),
          composes="SUM"),
    _node("penalties", "departures_missed * penalty_rate", MONEY, Home(_OPTIMIZE, "O1"), composes="SUM"),
    _node("cost_to_serve", "energy_cost + maintenance + penalties", MONEY, Home(_OPTIMIZE, "O1"), composes="SUM"),
    _node("cost_per_departure_met", "cost_to_serve / departures_met", MONEY / DAY, Home(_ABOVE, None),
          composes="NONE"),
    _node("contribution", "0 - cost_to_serve", MONEY, Home(_ABOVE, None), composes="SUM"),
)
