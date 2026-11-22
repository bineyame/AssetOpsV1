"""3B6: the cold-room structure, version 1 (spec §2.2; D-3B6.1, D-3B6.2, D-3B6.9, D-3B6.10).

One literal tuple of 36 rows: the 23 leaves in `canonical.leaves_of("COLD_CHAIN")` order, then the 13 nodes in the
manifest's `structures.COLD_CHAIN` order. Every literal (unit, home, source, words, absence, composes, neutral) is
written here, never read from the catalogue or the manifest (W2): the parity test compares them with the manifest's
`structures`, `factor_map`, `home_categories.nodes` and `empty_states.leaf_sources`, and the start-up check with the
catalogue. No row states a total (D-3B6.2) or carries a tolerance (D-3B6.9). The rights node
`cover_not_claimable` is not a row (as for MINI_GRID, D-3B1.5).
"""

from __future__ import annotations

from decimal import Decimal

from assetops_backend.structure.registry import HOMES, FactorRow, FilledBy, Home
from assetops_contracts.canonical.units import DAY, KWH, MINUTE, MONEY, ONE, Unit

_GROW, _OPTIMIZE, _PROTECT = HOMES["grow"], HOMES["optimize"], HOMES["protect"]
_ABOVE, _CALENDAR = HOMES["above"], HOMES["calendar"]


def _leaf(factor_id: str, unit: Unit, home: Home, family: str, kind: str, absent: str,
          words: str | None = None, *, composes: str, neutral: Decimal | None = None,
          levers: tuple[str, ...] = ()) -> FactorRow:
    return FactorRow(factor_id, None, unit, home, FilledBy(family, kind, words), absent, None,
                     levers=levers, neutral=neutral, composes=composes)


def _node(factor_id: str, expression: str, unit: Unit, home: Home, *, composes: str,
          levers: tuple[str, ...] = ()) -> FactorRow:
    return FactorRow(factor_id, expression, unit, home, None, None, None, levers=levers, composes=composes)


ROWS: tuple[FactorRow, ...] = (
    # ---- leaves (23)
    _leaf("outstanding", MONEY, Home(_OPTIMIZE, "O3"), "COMMERCIAL_RECORD", "RECEIPT", "ZERO_WHEN_HELD",
          composes="SUM"),
    _leaf("staff", MONEY, Home(_OPTIMIZE, "O1"), "COMMERCIAL_RECORD", "EXPENSE (STAFF)", "MISSING",
          words="Payroll summary", composes="SUM"),
    _leaf("liability", MONEY, Home(_OPTIMIZE, "O1"), "COMMERCIAL_RECORD", "ADJUSTMENT (credit note)", "ZERO_WHEN_HELD",
          composes="SUM"),
    _leaf("period_days", DAY, Home(_CALENDAR, None), "CALENDAR", "period_days", "NEVER_EMPTY", composes="NONE"),
    _leaf("crate_days", DAY, Home(_GROW, "G1"), "COMMERCIAL_RECORD", "STORAGE_MOVEMENT (occupied crate-days)",
          "MISSING", composes="SUM"),
    _leaf("rate", MONEY / DAY, Home(_GROW, "G1"), "COMMERCIAL_RECORD", "TARIFF_SCHEDULE (storage rate card)",
          "MISSING", composes="NONE"),
    _leaf("contract_crate_days", DAY, Home(_GROW, "G3"),
          "COMMERCIAL_RECORD", "CONTRACT_DOCUMENT (an option's storage contract)", "OPTION_ONLY",
          composes="SUM", neutral=Decimal("0"), levers=("storage_contract",)),
    _leaf("contract_rate", MONEY / DAY, Home(_GROW, "G3"),
          "COMMERCIAL_RECORD", "CONTRACT_DOCUMENT (an option's storage contract)", "OPTION_ONLY",
          composes="NONE", neutral=Decimal("0")),
    _leaf("base_kwh", KWH, Home(_OPTIMIZE, "O1"), "DECLARED", "energy_model", "MISSING", composes="SUM"),
    _leaf("k_kwh_per_crate_day", KWH / DAY, Home(_OPTIMIZE, "O1"), "DECLARED", "energy_model", "MISSING",
          composes="NONE"),
    _leaf("model_factor", ONE, Home(_OPTIMIZE, "O1"), "DECLARED", "energy_model (an option's efficiency change)",
          "OPTION_ONLY", composes="NONE", neutral=Decimal("1")),
    _leaf("excess_kwh", KWH, Home(_OPTIMIZE, "O1"),
          "OBSERVER", "cold energy normalisation (CHARGE electricity bill, STORAGE_MOVEMENT)", "MISSING",
          composes="SUM", levers=("chamber_efficiency",)),
    _leaf("elec_price", MONEY / KWH, Home(_OPTIMIZE, "O1"), "COMMERCIAL_RECORD", "CHARGE (electricity bill)",
          "MISSING", composes="NONE"),
    _leaf("maint", MONEY, Home(_OPTIMIZE, "O1"), "COMMERCIAL_RECORD", "EXPENSE (OM)", "MISSING",
          words="Service contractor invoice", composes="SUM"),
    _leaf("handling", MONEY, Home(_OPTIMIZE, "O1"), "COMMERCIAL_RECORD", "EXPENSE (an option's handling cost)",
          "OPTION_ONLY", composes="SUM", neutral=Decimal("0")),
    _leaf("uncovered_nights", DAY, Home(_PROTECT, "P1"),
          "OPERATIONAL_RECORD", "work case (failed start, witnessed test) and the manual-start rota", "ZERO_WHEN_HELD",
          composes="SUM", levers=("backup_cover",)),
    _leaf("backup_unproven_days", DAY, Home(_PROTECT, "P1"),
          "OPERATIONAL_RECORD", "work case (failed start, witnessed test)", "ZERO_WHEN_HELD", composes="SUM"),
    _leaf("excursion_crates", ONE, Home(_PROTECT, "P1"),
          "OBSERVER", "exposure (chamber temperature, STORAGE_MOVEMENT)", "ZERO_WHEN_HELD", composes="SUM",
                levers=("backup_cover",)),
    _leaf("excursion_days", DAY, Home(_PROTECT, "P1"),
          "OBSERVER", "exposure (chamber temperature, STORAGE_MOVEMENT)", "ZERO_WHEN_HELD", composes="SUM"),
    _leaf("batches_exposed", ONE, Home(_PROTECT, "P1"),
          "OBSERVER", "exposure (chamber temperature, STORAGE_MOVEMENT)", "ZERO_WHEN_HELD", composes="SUM"),
    _leaf("cooling_minutes_unavailable", MINUTE, Home(_OPTIMIZE, "O2"), "READING", "cooling state", "ZERO_WHEN_HELD",
          composes="SUM"),
    _leaf("minutes_per_day", MINUTE / DAY, Home(_CALENDAR, None), "CALENDAR", "minutes_per_day", "NEVER_EMPTY",
          composes="NONE"),
    _leaf("capacity_crate_days", DAY, Home(_GROW, "G2"), "DECLARED", "room capacity (site configuration)", "MISSING",
          composes="SUM"),
    # ---- nodes (13), expressions verbatim from the manifest's structures.COLD_CHAIN
    _node("revenue", "crate_days * rate + contract_crate_days * contract_rate", MONEY, Home(_GROW, "G1"),
          composes="SUM"),
    _node("received", "revenue - outstanding", MONEY, Home(_OPTIMIZE, "O3"), composes="SUM"),
    _node("kwh_model", "(base_kwh + k_kwh_per_crate_day * (crate_days + contract_crate_days)) * model_factor", KWH,
          Home(_OPTIMIZE, "O1"), composes="SUM"),
    _node("kwh", "kwh_model + excess_kwh", KWH, Home(_OPTIMIZE, "O1"), composes="SUM"),
    _node("energy", "kwh * elec_price", MONEY, Home(_OPTIMIZE, "O1"), composes="SUM"),
    _node("cost_to_serve", "energy + staff + maint + liability + handling", MONEY, Home(_OPTIMIZE, "O1"),
          composes="SUM"),
    _node("contribution", "revenue - cost_to_serve", MONEY, Home(_ABOVE, None), composes="SUM"),
    _node("nights_without_backup_cover", "uncovered_nights", DAY, Home(_PROTECT, "P1"), composes="SUM",
          levers=("backup_cover",)),
    _node("days_backup_start_unproven", "backup_unproven_days", DAY, Home(_PROTECT, "P1"), composes="SUM"),
    _node("occupied_total_crate_days", "crate_days + contract_crate_days", DAY, Home(_GROW, "G1"), composes="SUM"),
    _node("crate_days_without_excursion", "crate_days - excursion_crates * excursion_days", DAY,
          Home(_OPTIMIZE, "O2"), composes="SUM"),
    _node("chamber_minutes", "period_days * minutes_per_day", MINUTE, Home(_OPTIMIZE, "O2"), composes="SUM"),
    _node("cooling_available_minutes", "chamber_minutes - cooling_minutes_unavailable", MINUTE, Home(_OPTIMIZE, "O2"),
          composes="SUM"),
)
