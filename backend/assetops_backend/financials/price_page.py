"""PR-2a (BL-68): the read-only Site price page body (architect-answer-price-it-2026-11-10 §4.2; sequence rev 4-5).

One row per price the Site's figures use, set or not, in mock order (`frontend/mockups/v71/price-it.html` Part B):
the current value, basis, applies-from date, who set it and what uses it, plus a History of every stored revision
in plain words (first price, new price from a date, correction from a date with its reason). A model or data item
(`need`) gets the Part C block. Every word on the page is built here (CH-6b2); the frontend renders, never decides.

Pure: it takes the Site facts and the `AssumptionReadService.series` bodies and composes. It never reads a clock:
"current" is the series' latest effective assignment (the open-ended one, else the one starting last), never a
"today" default (WALK1-5). No form and no save: price entry is PR-3, which adds `entry` to this body.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from assetops_backend.financials.assumptions import SYSTEM_PUBLISHER
from assetops_backend.outcomes.price_action import NEED_TEXT, NEEDS_LABEL, PRICE_NOUN, STORED_KEYS

#: Rev 5 §5.3: actor id -> "Set by" words. The second entry is PR-3's site-admin entry service (D-PRICE.1),
#: shipped here so a saved price reads right whichever slice merges first. An unknown actor is named as such.
SET_BY_LABEL = {
    SYSTEM_PUBLISHER.actor_id: "AssetOps administrator",
    "service:operator-entry": "Entered by site admin",
}
UNKNOWN_SETTER = "Recorded by the server"

#: The sign-in sentence (rev 4 card; PR-1 fix round wording). PR-3 replaces it when entry is enabled.
SIGN_IN_TEXT = "Prices are set by your AssetOps administrator until sign-in is available."
INTRO_TEXT = "Every price this site's figures use: the current value, where it came from, and every earlier version."
TABLE_NOTE = "One row per price. \"Not set\" means the figures that need it read \"not priced\"."
NOT_SET = "Not set"
#: Default 3 (owner 2026-11-12): a key no figure reads yet; no button.
FUTURE_KEY_NOTE = "Saving this price comes once a figure uses it."
NEED_TITLE = "What is needed to price this"
NEED_MEANWHILE = "What AssetOps shows meanwhile: the measurements, never an amount, a range or \"≈\"."

BASIS_WORDS = {"AUTHORED_ESTIMATE": "An estimate", "CONTRACT_RATE": "A contract rate",
               "RECORDED_PURCHASE": "A recorded purchase"}
UNIT_WORDS = {"currency/L": "per litre", "currency/kWh": "per kWh"}


@dataclass(frozen=True)
class KeyWords:
    label: str
    detail: str
    per: str            # unit words for a key with no stored unit yet ("per visit")
    used_by: str
    used_by_detail: str


#: Price key -> its row words (mock Part B rows; nouns follow `price_action.PRICE_NOUN`).
KEY_WORDS = {
    "diesel_price_per_litre": KeyWords("Diesel price", "backup generator fuel", "per litre", "Fuel cost",
                                       "Backup running days"),
    "productive_use_price_per_kwh": KeyWords("Productive-use price", "per kWh sold", "per kWh",
                                             "Verification value", "Sales estimate of a productive-use action"),
    "ev_gross_tariff_per_kwh": KeyWords("Charging tariff", "gross, per kWh charged", "per kWh",
                                        "Charging revenue", "Gross tariff scenario"),
    "repair_visit_cost": KeyWords("Cost per visit", "call-out plus labour", "per visit", "1 early warning",
                                  "Visits without a result"),
    "planned_service_cost": KeyWords("Planned service cost", "per planned job", "per job",
                                     "Plan due soon, plan overdue", "the planned part only"),
    "charger_repair_cost": KeyWords("Repair cost", "per charger repair", "per repair", "Charger fault",
                                    "the repair part only"),
    "interrupted_session_cost": KeyWords("Cost per interrupted session", "penalty, goodwill or lost fee",
                                         "per session", "Charging session interrupted", "a lower bound"),
    "stock_value_at_risk": KeyWords("Stock value at risk", "per chamber load, an upper bound", "per chamber load",
                                    "Temperature excursion", "\"up to … at risk\", never a loss"),
}

#: Site type -> the prices its figures use or will use, in page order (stored keys first). Stored keys follow the
#: readers (`fuel_cost`, `mill_value`, `ev_money`); future keys follow `price_action.WARNING_SPEC` and the §3 table.
SITE_KEYS = {
    "MINIGRID": ("diesel_price_per_litre", "productive_use_price_per_kwh", "repair_visit_cost",
                 "planned_service_cost"),
    "COLDCHAIN": ("repair_visit_cost", "planned_service_cost", "stock_value_at_risk"),
    "EV_CHARGING": ("ev_gross_tariff_per_kwh", "charger_repair_cost", "interrupted_session_cost",
                    "repair_visit_cost", "planned_service_cost"),
}


def site_keys(site_type: str) -> tuple[str, ...]:
    """The keys of one Site type; an unknown type lists the stored keys only (never a guessed future key)."""
    return SITE_KEYS.get(site_type, STORED_KEYS)


def stored_keys(site_type: str) -> tuple[str, ...]:
    return tuple(k for k in site_keys(site_type) if k in STORED_KEYS)


def day_text(at: datetime, zone: ZoneInfo) -> str:
    local = at.astimezone(zone)
    return f"{local.day} {local:%b %Y}"


def moment_text(at: datetime, zone: ZoneInfo) -> str:
    local = at.astimezone(zone)
    return f"{local.day} {local:%b %Y}, {local:%H:%M}"


def amount_text(value: str) -> str:
    """The stored decimal without trailing zeros past two places ("1.4200" -> "1.42"); never a float."""
    try:
        d = Decimal(value)
    except InvalidOperation:
        return value
    text = format(d.normalize(), "f")
    whole, _, frac = text.partition(".")
    return f"{whole}.{frac.ljust(2, '0')}" if frac or "." in value else text


def value_text(price: Mapping[str, Any]) -> str:
    per = UNIT_WORDS.get(price["unit"], price["unit"])
    return f"{amount_text(price['value'])} {price['currency']} {per}"


def set_by(price: Mapping[str, Any]) -> str:
    return SET_BY_LABEL.get(price["actor"]["id"], UNKNOWN_SETTER)


def _current(series: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """The latest effective assignment: the open-ended one, else the one starting last. No clock is read."""
    timeline = series["timeline"]
    if not timeline:
        return None
    open_ended = [a for a in timeline if a["valid"]["to"] is None]
    return max(open_ended or timeline, key=lambda a: a["valid"]["from"])


def _headline(price: Mapping[str, Any], zone: ZoneInfo) -> str:
    start = day_text(price["authored_valid"]["from"], zone)
    if price["change_kind"] == "CORRECTION":
        return f"Correction from {start}"
    if price["change_kind"] == "SUCCESSION":
        return f"New price from {start}"
    return f"First price from {start}"


def history(series: Mapping[str, Any], zone: ZoneInfo) -> list[dict[str, Any]]:
    """Every stored revision, newest first, in plain words; a revision no current assignment cites is replaced."""
    cited = {a["revision_id"] for a in series["timeline"]}
    out = []
    for p in sorted(series["revisions"], key=lambda r: r["revision_no"], reverse=True):
        basis = BASIS_WORDS.get(p["basis"], p["basis"])
        until = p["authored_valid"]["to"]
        out.append({
            "revision_id": p["revision_id"], "revision_no": p["revision_no"], "change_kind": p["change_kind"],
            "headline": _headline(p, zone),
            "until_text": None if until is None else f"until {day_text(until, zone)}",
            "value_text": value_text(p), "basis_text": basis[:1].lower() + basis[1:],
            "source_reference": p["source_reference"],
            "reason": p["correction_reason"], "set_by_label": set_by(p),
            "recorded_text": f"recorded {moment_text(p['recorded_at'], zone)}",
            "replaced": p["revision_id"] not in cited,
            # MOCK DEVIATION (D-PRICE.3): the mock says "replaced by the correction above"; History can be filtered
            # (and capped), so the correction may not be above. Wording kept: "a later correction".
            "replaced_text": "replaced by a later correction" if p["revision_id"] not in cited else None,
        })
    return out


HISTORY_CAP = 200  # `AssumptionReadService.series` reads at most this many revisions per key
HISTORY_CAPPED_TEXT = f"Only the newest {HISTORY_CAP} versions are shown."


def capped_text(series: Mapping[str, Any] | None) -> str | None:
    """The one honest line when the series read stopped at its cap, so the History may be cut (review L4)."""
    return HISTORY_CAPPED_TEXT if series is not None and len(series["revisions"]) >= HISTORY_CAP else None


def row(key: str, series: Mapping[str, Any] | None, zone: ZoneInfo) -> dict[str, Any]:
    words = KEY_WORDS[key]
    stored = key in STORED_KEYS
    base = {"key": key, "noun": PRICE_NOUN.get(key, words.label.lower()), "label": words.label,
            "detail": words.detail, "stored": stored,
            "used_by": {"text": words.used_by, "detail": words.used_by_detail},
            "history_capped_text": capped_text(series)}
    current = None if series is None else _current(series)
    if current is None:
        return {**base, "state": "NOT_SET", "current": None, "not_set_text": NOT_SET,
                "note": None if stored else FUTURE_KEY_NOTE,
                "history": [] if series is None else history(series, zone), "history_title": None}
    price = current["price"]
    hist = history(series, zone)
    count = len(hist)
    return {**base, "state": "SET", "not_set_text": None, "note": None,
            "current": {"revision_id": price["revision_id"], "value": price["value"], "currency": price["currency"],
                        "unit": price["unit"], "value_text": value_text(price),
                        "amount_text": amount_text(price["value"]),
                        "per_text": f"{price['currency']} {UNIT_WORDS.get(price['unit'], price['unit'])}",
                        "basis_text": BASIS_WORDS.get(price["basis"], price["basis"]),
                        "source_reference": price["source_reference"],
                        "applies_from_text": day_text(current["valid"]["from"], zone),
                        "applies_until_text": None if current["valid"]["to"] is None
                        else f"until {day_text(current['valid']['to'], zone)}",
                        "set_by_label": set_by(price),
                        "recorded_text": f"recorded {moment_text(price['recorded_at'], zone)}"},
            "history": hist,
            "history_title": f"History of the {base['noun']} · {count} version{'' if count == 1 else 's'}"}


def need_block(need: str | None) -> dict[str, Any] | None:
    """Part C for a model, data or integration item; None for no or an unknown need key."""
    if need is None or need not in NEED_TEXT:
        return None
    return {"need_key": need, "title": NEED_TITLE, "text": NEED_TEXT[need], "meanwhile": NEED_MEANWHILE,
            "link_label": NEEDS_LABEL}


def compose(*, site_code: str, site_name: str, site_type: str, timezone: str,
            series: Mapping[str, Mapping[str, Any]], need: str | None, known_at: datetime | None,
            access_basis: str) -> dict[str, Any]:
    """The page body. `series` holds one `AssumptionReadService.series` body per stored key of the Site type."""
    zone = ZoneInfo(timezone)
    rows = [row(k, series.get(k), zone) for k in site_keys(site_type)]
    set_count = sum(1 for r in rows if r["state"] == "SET")
    return {
        "site_code": site_code, "site_name": site_name, "access_basis": access_basis,
        "title": f"{site_name} · Prices", "intro": INTRO_TEXT, "sign_in_text": SIGN_IN_TEXT,
        "table_title": f"All prices for {site_name}", "table_note": TABLE_NOTE,
        "count_text": f"{len(rows)} price{'' if len(rows) == 1 else 's'} · {set_count} set",
        "cutoff": {"known_at": known_at,
                   "text": None if known_at is None else f"Prices as known at {moment_text(known_at, zone)}."},
        "prices": rows, "need": need_block(need),
    }
