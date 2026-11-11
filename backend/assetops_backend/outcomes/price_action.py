"""PR-1 (BL-68): the server-built `price_action` of an unpriced item (architect-answer-price-it-2026-11-10 §3, §4.1, §5).

Two shapes, and the words are the server's (CH-6b2): the frontend renders the link and never decides which items are
priceable.
- `{"kind": "SET_PRICE", "key", "label", "href", "link_ref"}` when one price fixes the item, or its simple part;
- `{"kind": "NEEDS_MODEL", "need_key", "text", "label", "href", "link_ref"}` when it needs a model, data or an
  integration. There is never an amount, a range or a "≈".

Both open the Site price page (`chain.refs` PRICES). Saving a price needs sign-in (BL-54); this module has no write
path. Pure: screen links come from the injected `links` (the `chain.refs` vocabulary: `prices_ref`, `href_for`), so
the package still imports nothing outside `outcomes`. No key or text carries money (`test_out_c1_never_money`).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SET_PRICE, NEEDS_MODEL = "SET_PRICE", "NEEDS_MODEL"

#: Price key -> the noun of "Set a {noun} for {site} →". The first three are stored today
#: (`financials/assumptions.py`); the rest arrive with PR-3's migration and read "Not set" until then.
PRICE_NOUN = {
    "diesel_price_per_litre": "diesel price",
    "ev_gross_tariff_per_kwh": "charging tariff",
    "productive_use_price_per_kwh": "productive-use price",
    "repair_visit_cost": "cost per visit",
    "planned_service_cost": "planned service cost",
    "charger_repair_cost": "repair cost",
    "interrupted_session_cost": "cost per interrupted session",
}
STORED_KEYS = ("diesel_price_per_litre", "ev_gross_tariff_per_kwh", "productive_use_price_per_kwh")

#: Need key -> the server's "what is needed" sentence (§5). Model, data and integration items only.
NEED_TEXT = {
    "battery_wear_model": "Battery wear is measured, not priced. Pricing it needs a tested wear model for this battery "
                          "type and its replacement cost. Meanwhile: cycles, depth of discharge and time at low "
                          "charge.",
    "demand_forecast": "The peak is measured, not priced. Pricing it needs your demand-charge tariff and a demand "
                       "forecast. Meanwhile: the peak, its time, and how close it came to the limit.",
    "bus_roster": "Time out of service is measured. What it cost depends on which buses needed this connector, which "
                  "needs the bus roster. Meanwhile: minutes out of service and sessions affected.",
    "stock_record": "Time above the limit is measured. The product loss needs the stock in the chamber at the time.",
    "repair_cost_record": "The repair is recorded; its cost is not. Pricing it needs the repair cost on the work "
                          "record.",
}
NEEDS_LABEL = "What is needed to price this →"
#: The site words when the reader has no Site name (a Site page, where the Site is the context).
THIS_SITE = "this site"


@dataclass(frozen=True)
class Spec:
    kind: str
    key: str | None = None
    need: str | None = None


def _set(key: str) -> Spec:
    return Spec(SET_PRICE, key=key)


def _need(need: str) -> Spec:
    return Spec(NEEDS_MODEL, need=need)


#: Early-warning kind (`warnings.KINDS`) -> spec (§3). Half-simple items link their simple part (a repair or service
#: cost); the history half stays named in `price_needs`. A test pins the keys to `warnings.KINDS`.
WARNING_SPEC = {
    "REPEATED_MAINTENANCE_NO_RESULT": _set("repair_visit_cost"),
    "PLAN_OVERDUE": _set("planned_service_cost"),
    "PLAN_DUE_SOON": _set("planned_service_cost"),
    "BATTERY_NEAR_RESERVE": _need("battery_wear_model"),
    "CHARGER_FAULT_OVERDUE_INSPECTION": _set("charger_repair_cost"),
    "CONNECTOR_OUT_OF_SERVICE": _need("bus_roster"),
    "PEAK_NEAR_IMPORT_LIMIT": _need("demand_forecast"),
}

#: Estate money-line category (`estate/financials.py`) -> spec, for an UNPRICED line (§3 row 1 and the cold rows).
MONEY_CATEGORY_SPEC = {
    "CANDIDATE_OPERATING_COST_EXPOSURE": _set("diesel_price_per_litre"),
    "GROSS_TARIFF_SCENARIO": _set("ev_gross_tariff_per_kwh"),
    "PRODUCTIVE_USE_CONTRIBUTION_SCENARIO": _set("productive_use_price_per_kwh"),
    "POTENTIAL_PRODUCT_EXPOSURE": _need("stock_record"),
    "RECORDED_REPAIR": _need("repair_cost_record"),
}

#: A mini Finding's fuel cost and a mill verification value are unpriced only for want of one stored price.
FINDING_FUEL_SPEC = _set("diesel_price_per_litre")
MILL_VALUE_SPEC = _set("productive_use_price_per_kwh")


def ref(spec: Spec, site_code: str, links: Any) -> dict[str, Any]:
    """The PRICES Ref of a spec at one Site."""
    return links.prices_ref(site_code, key=spec.key, need=spec.need)


def wire(spec: Spec | None, site_code: str, site_name: str | None, links: Any) -> dict[str, Any] | None:
    """The `price_action` body of one unpriced item; None without a spec."""
    if spec is None:
        return None
    link_ref = ref(spec, site_code, links)
    href = links.href_for(link_ref)
    if spec.kind == SET_PRICE:
        label = f"Set a {PRICE_NOUN[spec.key]} for {site_name or THIS_SITE} →"
        return {"kind": SET_PRICE, "key": spec.key, "label": label, "href": href, "link_ref": link_ref}
    return {"kind": NEEDS_MODEL, "need_key": spec.need, "text": NEED_TEXT[spec.need], "label": NEEDS_LABEL,
            "href": href, "link_ref": link_ref}
