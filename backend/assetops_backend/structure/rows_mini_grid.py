"""3B1: the mini-grid structure, version 3 (spec §2; D-3B1.1, D-3B1.4, D-3B1.5; R9, R13, R19).

3B3 made it version 2: every row states `composes` (D-3B3.14), and the OPTION_ONLY leaves carry the
manifest's `neutral` literal (D-3B3.9). 4b1 made it version 3: `revenue` and `fuel_cost` name the record that
states their total (`stated_by`, D-4B.1, D-4B.10); no other row states. 4a made it version 4: `metered_kwh` and
`billed_kwh` name the record that states their kWh (D-4A.1).

One literal tuple of 47 rows: the 31 leaves in `canonical.leaves_of("MINI_GRID")` order,
then the 16 nodes in spec §2.2's order. Leaf units, sources, words and absence values are
literals here, never read from the catalogue or the manifest (R19); the parity test
compares them with the manifest, and the start-up check with the catalogue.

The rights nodes `cover_not_claimable` and `unclaimable_cover` and the operations measures
are not rows in version 1 (D-3B1.5).
"""

from __future__ import annotations

from decimal import Decimal

from assetops_backend.structure.registry import HOMES, FactorRow, FilledBy, Home, Tolerance
from assetops_contracts.canonical.units import DAY, HOUR, KW, KWH, L, MONEY, ONE, Unit

_GROW, _OPTIMIZE, _PROTECT = HOMES["grow"], HOMES["optimize"], HOMES["protect"]
_ABOVE, _CALENDAR = HOMES["above"], HOMES["calendar"]


def _leaf(factor_id: str, unit: Unit, home: Home, family: str, kind: str, absent: str,
          words: str | None = None, tolerance: Tolerance | None = None, *, composes: str,
          neutral: Decimal | None = None) -> FactorRow:
    return FactorRow(factor_id, None, unit, home, FilledBy(family, kind, words), absent, tolerance,
                     neutral=neutral, composes=composes)


def _node(factor_id: str, expression: str, unit: Unit, home: Home, *, composes: str,
          stated_by: FilledBy | None = None) -> FactorRow:
    return FactorRow(factor_id, expression, unit, home, None, None, None, composes=composes, stated_by=stated_by)


ROWS: tuple[FactorRow, ...] = (
    # ---- leaves (31)
    _leaf("delivered_kwh", KWH, Home(_GROW, "G1"), "READING", "feeder_demand", "MISSING", composes="SUM"),
    _leaf("technical_loss_kwh", KWH, Home(_OPTIMIZE, "O2"), "DECLARED", "expected_technical_loss_band", "MISSING",
          composes="SUM"),
    _leaf("unexplained_loss_kwh", KWH, Home(_OPTIMIZE, "O3"),
          "OBSERVER", "energy-to-cash@1 (feeder_demand, CUSTOMER_METER_READ)", "ZERO_WHEN_HELD", composes="SUM"),
    _leaf("adjustments_kwh", KWH, Home(_OPTIMIZE, "O3"), "COMMERCIAL_RECORD", "ADJUSTMENT", "ZERO_WHEN_HELD",
          composes="SUM"),
    _leaf("unmapped_kwh", KWH, Home(_OPTIMIZE, "O3"),
          "COMMERCIAL_RECORD", "CUSTOMER_METER_READ (meter register with effective dates)", "ZERO_WHEN_HELD",
          composes="SUM"),
    _leaf("tariff", MONEY / KWH, Home(_GROW, "G1"), "COMMERCIAL_RECORD", "TARIFF_SCHEDULE", "MISSING", composes="NONE"),
    _leaf("productive_kwh", KWH, Home(_GROW, "G3"),
          "COMMERCIAL_RECORD", "CHARGE (productive tariff class)", "ZERO_WHEN_HELD", composes="SUM"),
    _leaf("productive_tariff", MONEY / KWH, Home(_GROW, "G3"), "COMMERCIAL_RECORD", "TARIFF_SCHEDULE", "MISSING",
          composes="NONE"),
    _leaf("in_transit", MONEY, Home(_OPTIMIZE, "O3"), "COMMERCIAL_RECORD", "SETTLEMENT", "ZERO_WHEN_HELD",
          composes="SUM"),
    _leaf("outstanding", MONEY, Home(_OPTIMIZE, "O3"), "COMMERCIAL_RECORD", "RECEIPT", "ZERO_WHEN_HELD",
          composes="SUM"),
    _leaf("necessary_l", L, Home(_OPTIMIZE, "O1"), "OBSERVER",
          "dispatch-3.3 (generator_state, pv_available_power, battery_soc; FUEL_DELIVERY, TANK_DIP)", "MISSING",
          composes="SUM"),
    _leaf("candidate_l", L, Home(_OPTIMIZE, "O1"), "OBSERVER",
          "dispatch-3.3 (generator_state, pv_available_power, battery_soc)", "ZERO_WHEN_HELD", composes="SUM"),
    _leaf("unexplained_l", L, Home(_OPTIMIZE, "O1"), "OBSERVER",
          "fuel balance (FUEL_DELIVERY, TANK_DIP) minus dispatch-3.3", "ZERO_WHEN_HELD",
          tolerance=Tolerance(of_factor="diesel_l", pct=Decimal("2.0")), composes="SUM"),
    _leaf("extra_l", L, Home(_OPTIMIZE, "O1"), "OBSERVER", "forward replay (an option's extra running)", "OPTION_ONLY",
          composes="SUM", neutral=Decimal("0")),
    _leaf("diesel_price", MONEY / L, Home(_OPTIMIZE, "O1"), "COMMERCIAL_RECORD", "EXPENSE (FUEL)", "MISSING",
          composes="NONE"),
    _leaf("battery_throughput_kwh", KWH, Home(_OPTIMIZE, "O1"),
          "OBSERVER", "forward replay (throughput an option adds)", "OPTION_ONLY",
          composes="SUM", neutral=Decimal("0")),
    _leaf("wear_rate", MONEY / KWH, Home(_OPTIMIZE, "O1"), "DECLARED", "battery_wear_rate_assumption", "MISSING",
          composes="NONE"),
    _leaf("om", MONEY, Home(_OPTIMIZE, "O1"), "COMMERCIAL_RECORD", "EXPENSE (OM)", "MISSING",
          words="Service contractor invoice", composes="SUM"),
    _leaf("staff", MONEY, Home(_OPTIMIZE, "O1"), "COMMERCIAL_RECORD", "EXPENSE (STAFF)", "MISSING",
          words="Payroll summary", composes="SUM"),
    _leaf("collection_cost", MONEY, Home(_OPTIMIZE, "O1"),
          "COMMERCIAL_RECORD", "EXPENSE (an option's collection cost)", "OPTION_ONLY",
          composes="SUM", neutral=Decimal("0")),
    _leaf("reduced_days", DAY, Home(_PROTECT, "P2"), "OPERATIONAL_RECORD", "work case (failure and restore)", "ZERO_WHEN_HELD",
          composes="SUM"),
    _leaf("hours_per_day", HOUR / DAY, Home(_PROTECT, "P1"),
          "OPERATIONAL_RECORD", "work case (failure and restore)", "ZERO_WHEN_HELD", composes="NONE"),
    _leaf("major_assets", ONE, Home(_OPTIMIZE, "O2"), "DECLARED", "asset_register", "MISSING", composes="SUM"),
    _leaf("unserved_critical_kwh", KWH, Home(_PROTECT, "P1"), "READING", "critical_load_delivered_power", "ZERO_WHEN_HELD",
          composes="SUM"),
    _leaf("customer_hours_interrupted", HOUR, Home(_PROTECT, "P1"), "READING", "feeder supply-loss flag", "ZERO_WHEN_HELD",
          composes="SUM"),
    _leaf("field_visits", ONE, Home(_OPTIMIZE, "O2"), "OPERATIONAL_RECORD", "work case (field visit)", "ZERO_WHEN_HELD",
          composes="SUM"),
    _leaf("liability", MONEY, Home(_OPTIMIZE, "O1"), "COMMERCIAL_RECORD", "ADJUSTMENT (credit note)", "ZERO_WHEN_HELD",
          composes="SUM"),
    _leaf("period_days", DAY, Home(_CALENDAR, None), "CALENDAR", "period_days", "NEVER_EMPTY", composes="NONE"),
    _leaf("standby_kw", KW, Home(_PROTECT, "P1"), "DECLARED", "outage units (site configuration)", "ZERO_WHEN_HELD",
          composes="NONE"),
    _leaf("lost_unit_kw", KW, Home(_PROTECT, "P1"), "DECLARED", "outage units (site configuration)", "ZERO_WHEN_HELD",
          composes="NONE"),
    _leaf("dawn_days_below", DAY, Home(_PROTECT, "P1"), "READING", "battery_soc", "ZERO_WHEN_HELD", composes="SUM"),
    # ---- nodes (16), expressions verbatim from the manifest's structures.MINI_GRID
    _node("metered_kwh", "delivered_kwh - technical_loss_kwh - unexplained_loss_kwh", KWH, Home(_GROW, "G1"),
          composes="SUM",
          stated_by=FilledBy("COMMERCIAL_RECORD", "CUSTOMER_METER_READ", "Customer meter reads for the month")),
    _node("billed_kwh", "metered_kwh - adjustments_kwh - unmapped_kwh", KWH, Home(_GROW, "G1"), composes="SUM",
          stated_by=FilledBy("COMMERCIAL_RECORD", "CHARGE (USAGE kWh)", "Billing export: the month's billed kWh")),
    _node("revenue", "billed_kwh * tariff + productive_kwh * productive_tariff", MONEY, Home(_GROW, "G1"),
          composes="SUM", stated_by=FilledBy("COMMERCIAL_RECORD", "CHARGE", "Billing export: the month's charges")),
    _node("collected", "revenue - in_transit - outstanding", MONEY, Home(_OPTIMIZE, "O3"), composes="SUM"),
    _node("diesel_l", "necessary_l + candidate_l + unexplained_l + extra_l", L, Home(_OPTIMIZE, "O1"), composes="SUM"),
    _node("fuel_cost", "diesel_l * diesel_price", MONEY, Home(_OPTIMIZE, "O1"), composes="SUM",
          stated_by=FilledBy("COMMERCIAL_RECORD", "EXPENSE (FUEL)", "Fuel invoices for the month")),
    _node("battery_wear", "battery_throughput_kwh * wear_rate", MONEY, Home(_OPTIMIZE, "O1"), composes="SUM"),
    _node("cost_to_serve", "fuel_cost + om + staff + collection_cost + battery_wear", MONEY, Home(_OPTIMIZE, "O1"),
          composes="SUM"),
    _node("contribution", "revenue - cost_to_serve", MONEY, Home(_ABOVE, None), composes="SUM"),
    _node("obligation_hours_without_redundancy", "reduced_days * hours_per_day", HOUR, Home(_PROTECT, "P1"),
          composes="SUM"),
    _node("shortfall_backed", "min(1, floor(standby_kw / max(lost_unit_kw, 1)))", ONE, Home(_PROTECT, "P1"),
          composes="NONE"),
    _node("obligation_hours_without_backup", "obligation_hours_without_redundancy * (1 - shortfall_backed)",
          HOUR, Home(_PROTECT, "P1"), composes="SUM"),
    _node("replayed_dawn_days_below_safeguard", "dawn_days_below", DAY, Home(_PROTECT, "P1"), composes="SUM"),
    _node("asset_days_out_of_service", "reduced_days", DAY, Home(_PROTECT, "P2"), composes="SUM"),
    _node("asset_days_total", "major_assets * period_days", DAY, Home(_OPTIMIZE, "O2"), composes="SUM"),
    _node("asset_days_available", "asset_days_total - asset_days_out_of_service", DAY, Home(_OPTIMIZE, "O2"),
          composes="SUM"),
)
