"""5c (spec sections 2.2, 2.3 and 3): the deep-dive's code constants, data and not prose (PF9). Every served string
is an SC-1 statement in `i18n/statements/en/deep_dive.py`; this module holds only factor ids, record keys, JSON
codes and the two plain-code helpers (month codes, the ISO instant) the view needs.
"""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from types import MappingProxyType

SCHEMA = "deep-dive-month-1"
#: Unit 2 (spec section 4.2): the route and its cache header (`deep_dive_api.py`).
ROUTE = "/api/portfolio/month"
NO_STORE: Mapping[str, str] = MappingProxyType({"Cache-Control": "no-store"})
MINI_GRID = "MINI_GRID"
ROOT = "contribution"
CASH = "collected"
COST = "cost_to_serve"
REVENUE = "revenue"
IN_TRANSIT = "in_transit"
OUTSTANDING = "outstanding"

#: D-5C.5: the waterfall's steps, the heading rows (test 1 proves them against the registry).
STEPS: Mapping[str, tuple[str, ...]] = MappingProxyType({MINI_GRID: ("revenue", "fuel_cost", "om", "staff")})
GROW, OPTIMIZE, PROTECT, ASSURE = "GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"

#: Spec section 3.1's codes in the payload.
TILE_KEYS = ("contribution", "gap", "plan_spend", "plan_value")
OUTCOME_KEYS: Mapping[str, str] = MappingProxyType({GROW: "grow", OPTIMIZE: "optimize", PROTECT: "protect",
                                                     ASSURE: "assure"})

#: Spec section 2.3 as amended by D-4A.12, D-4A.20 and D-4A.24 (PF2): the records that fill a gap, in this order.
RECORDS = ("BILLING", "FEEDER_METER", "METER_REGISTER", "METER_READS", "LOSS_BAND", "PRODUCTIVE_LINES",
           "PRODUCTIVE_TARIFF", "SETTLEMENTS", "RECEIPTS", "EMS", "FUEL_CURVE", "TANK_DIPS", "FUEL_DELIVERIES",
           "FUEL_INVOICES", "OM_INVOICES", "PAYROLL", "SITE_SETUP", "ANALYSING", "MONTH_CLOSE")
BUDGET_LINES = "BUDGET_LINES"
RECORD_KEYS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "revenue": ("BILLING",), "billed_kwh": ("BILLING",), "adjustments_kwh": ("BILLING",),
    "delivered_kwh": ("FEEDER_METER",), "technical_loss_kwh": ("FEEDER_METER", "LOSS_BAND"),
    "unexplained_loss_kwh": ("FEEDER_METER", "LOSS_BAND", "METER_READS", "METER_REGISTER"),
    "metered_kwh": ("METER_READS", "METER_REGISTER"), "unmapped_kwh": ("METER_READS", "METER_REGISTER", "BILLING"),
    "tariff": ("BILLING",), "productive_kwh": ("PRODUCTIVE_LINES",), "productive_tariff": ("PRODUCTIVE_TARIFF",),
    "in_transit": ("SETTLEMENTS",), "outstanding": ("RECEIPTS",), "necessary_l": ("EMS", "FUEL_CURVE"),
    "candidate_l": ("EMS", "FUEL_CURVE"), "unexplained_l": ("EMS", "FUEL_CURVE", "TANK_DIPS", "FUEL_DELIVERIES"),
    "fuel_cost": ("FUEL_INVOICES",), "diesel_price": ("FUEL_INVOICES",), "om": ("OM_INVOICES",),
    "staff": ("PAYROLL",)})
#: A leaf's `missing.note` adds its key; ANALYSING and MONTH_CLOSE replace the leaf's keys instead.
NOTE_KEYS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "GENERATOR_OR_TANK_NOT_DECLARED": ("SITE_SETUP",), "NO_RUNNING_RECORD": ("EMS",), "RUNNING_RECORD_GAP": ("EMS",),
    "GENERATOR_USE_INCOMPLETE": ("EMS",), "FUEL_CURVE_MISSING": ("FUEL_CURVE",),
    "NO_LOAD_RATE_MISSING": ("FUEL_CURVE",), "TANK_DIPS_MISSING": ("TANK_DIPS",), "TANK_DIPS_CONFLICT": ("TANK_DIPS",),
    "DISPATCH_NOT_ASSESSED": ("ANALYSING",), "SPANS_OVERLAP": ("ANALYSING",), "SPAN_CLASS_UNKNOWN": ("ANALYSING",),
    "MONTH_OPEN": ("MONTH_CLOSE",),
    "FEEDER_NOT_BOUND": ("FEEDER_METER",), "FEEDER_BINDINGS_CHANGED": ("FEEDER_METER",),
    "FEEDER_READINGS_GAP": ("FEEDER_METER",), "LOSS_BAND_NOT_DECLARED": ("LOSS_BAND",),
    "LOSS_BAND_CHANGED": ("LOSS_BAND",), "METER_READ_STRADDLES": ("METER_READS",),
    "METER_READS_OVERLAP": ("METER_READS",), "METER_READS_INCOMPLETE": ("METER_READS",),
    "NEEDS:CUSTOMER_METER_READ": ("METER_READS",), "NEEDS:METER_ASSIGNMENT": ("METER_REGISTER",),
    "NEEDS:CHARGE": ("BILLING",), "METER_REF_CONFLICT": ("METER_READS", "METER_REGISTER")})
REPLACING = ("ANALYSING", "MONTH_CLOSE")

#: Section 2.5 `carried`: the record noun of a carried leaf, as the statement's state.
CARRIED_STATE: Mapping[str, str] = MappingProxyType({"om": "OM", "staff": "STAFF"})
#: 5b's stop reasons that say no rule splits the row exactly.
NO_RULE = ("RULE_NOT_DECLARED", "PRICE_NOT_DECLARED", "SPLIT_INEXACT")
CURRENCY_PREFIX = "CURRENCY_MISMATCH:"
OUT_NOT_SPLIT = "NOT_SPLIT"
ACTUAL_PREFIX, TARGET_PREFIX = "actual:", "target:"
UNTRACKED_SEP = ":"
CURRENCY_SEP = ","
#: Section 3.2: a residual row's key in the portfolio rows.
RESIDUAL_PREFIX = "residual:"


#: Spec section 4.1: the only month the read accepts (fullmatch).
MONTH_PATTERN = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])")


def month_code(year: int, month: int) -> str:
    """`YYYY-MM` for a month, rolled across years."""
    year, month = year + (month - 1) // 12, (month - 1) % 12 + 1
    return f"{year:04d}-{month:02d}"


def iso_z(at: datetime) -> str:
    """The instant in UTC, ISO with `Z` (`2026-11-20T08:00:00Z`)."""
    return at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


#: A by-Site step cell's and its drawer row's amount form: a carried row names its source, " (at budget)"
#: (spec section 3.2, D-5C.23).
CELL_FORM = {True: "AT_BUDGET", False: "SIGNED"}

#: D-5C.27: a step bar's tone (effect below 0, else) and the places every track position is served with.
TONE_LOWERS, TONE_RAISES = "lowers", "raises"
BAR_MIN_WIDTH = "0.8"
BAR_PLACES = "0.01"

#: PF1: a registry unit's dimension name to its SC-1 `unit` vocabulary key (a driver's detail, section 3.2). Every
#: unit a MINI_GRID driver can show is here (test 1 proves it).
UNIT_WORDS: Mapping[str, str] = MappingProxyType({"KWH": "kWh", "L": "L"})
