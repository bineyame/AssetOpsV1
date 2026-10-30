"""OUT-A1: the four outcome categories and the site-level outcome catalogue (build spec outcome sprint 2026-10-29
§1.1-1.2). Pure and versioned; `measured` is a constant per catalogue version."""
from __future__ import annotations

from dataclasses import dataclass

CATALOGUE_VERSION = "outcome-catalogue/2"

CATEGORIES = ("GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE")  # canonical order
CATEGORY_LABEL = {
    "GROW_REVENUE": "Grow revenue",
    "OPTIMIZE_COST": "Optimize cost and efficiency",
    "PROTECT_ASSET": "Protect asset and capital",
    "ASSURE_PERFORMANCE": "Assure performance and returns"}
CATEGORY_DEFINITION = {  # mock outcomes.js:12-15, verbatim
    "GROW_REVENUE": "Capture more value from existing infrastructure and expand earning potential",
    "OPTIMIZE_COST": "Eliminate avoidable expenditure and get more output from operational resources",
    "PROTECT_ASSET": "Preserve asset value, avoid premature replacement and reduce service disruption",
    "ASSURE_PERFORMANCE": "Establish with defensible evidence whether the infrastructure is delivering expected results"}
CATEGORY_ICON = {"GROW_REVENUE": "grow", "OPTIMIZE_COST": "cost", "PROTECT_ASSET": "protect",
                 "ASSURE_PERFORMANCE": "assure"}  # frontend icon keys, mock outcomes.js:37-41

# Coverage-domain literals of estate/coverage.py:25, copied (ruling A-Q5); a test asserts equality.
MINI, COLD, EV = "mini_grid", "cold_chain", "ev_charging"
DOMAINS = (MINI, COLD, EV)


@dataclass(frozen=True)
class SiteOutcome:
    key: str
    domain: str
    category: str
    label: str
    measured: bool
    missing_records: str | None


def _o(key: str, domain: str, category: str, label: str, missing: str | None = None) -> SiteOutcome:
    return SiteOutcome(key, domain, category, label, missing is None, missing)


# Order is the tie-break for a row's lead outcome (§1.2).
SITE_OUTCOMES = (
    _o("MG-1", MINI, "GROW_REVENUE", "Productive electricity sales"),
    _o("MG-6", MINI, "GROW_REVENUE", "Cash collected", "no billing or payment records"),
    _o("MG-3", MINI, "GROW_REVENUE", "Site profitability", "needs site income, operating cost and capital records"),
    _o("MG-2", MINI, "OPTIMIZE_COST", "Supply cost per kWh"),
    _o("MG-5", MINI, "PROTECT_ASSET", "Reliable service"),
    _o("MG-4", MINI, "PROTECT_ASSET", "Battery and generator life"),  # measured from C (R541 resolved)
    _o("MG-7", MINI, "ASSURE_PERFORMANCE", "Evidence quality"),
    _o("EV-3", EV, "GROW_REVENUE", "Charger use"),
    _o("EV-6", EV, "GROW_REVENUE", "Energy billed against metered", "no settlement records"),
    _o("EV-2", EV, "OPTIMIZE_COST", "Energy cost per km",
       "needs odometer readings; a tariff estimate exists in Financials"),
    _o("EV-1", EV, "PROTECT_ASSET", "Buses ready for service"),  # R520: mock "ready to run" (vocabulary guard)
    _o("EV-4", EV, "PROTECT_ASSET", "Charger life"),
    _o("EV-5", EV, "PROTECT_ASSET", "Room before expansion"),
    _o("EV-7", EV, "ASSURE_PERFORMANCE", "Evidence quality"),
    _o("CC-2", COLD, "GROW_REVENUE", "Paid cold-room use", "needs occupancy, storage contract, income and sales records"),
    _o("CC-4", COLD, "GROW_REVENUE", "Market value of produce", "needs market and sales records"),
    _o("CC-3", COLD, "OPTIMIZE_COST", "Cost per cooling unit"),  # measured from C (R541 resolved)
    _o("CC-1", COLD, "PROTECT_ASSET", "Stock kept saleable"),
    _o("CC-6", COLD, "PROTECT_ASSET", "Cooling continuity"),
    _o("CC-5", COLD, "PROTECT_ASSET", "Compressor life"),
    _o("CC-7", COLD, "ASSURE_PERFORMANCE", "Evidence quality"),
)
OUTCOME_BY_KEY = {o.key: o for o in SITE_OUTCOMES}

# Row-level sentence when every outcome in a (domain, category) row is not measured (§1.2).
ROW_NOT_MEASURED = {
    (COLD, "GROW_REVENUE"): "Needs occupancy, storage contract, income and sales records",
    (EV, "OPTIMIZE_COST"): "Energy cost per km needs odometer readings; a tariff estimate exists in Financials",
}
ROW_NOT_MEASURED_PREFIX = "Not measured yet · "


def row_not_measured(domain: str, category: str, lead: SiteOutcome) -> str:
    """The one line an all-unmeasured row shows: the ruled sentence, else the prefix plus the lead's records."""
    return ROW_NOT_MEASURED.get((domain, category)) or ROW_NOT_MEASURED_PREFIX + (lead.missing_records or "")
