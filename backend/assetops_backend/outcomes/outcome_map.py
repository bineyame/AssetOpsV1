"""OUT-A1: the outcome map, policy `outcome-map/1` (build spec outcome sprint 2026-10-29 §1.3, rulings A-Q2/Q3).

Pure and versioned, in the style of estate/placement.py. Each entry names the site-level outcomes a signal
**moves** (first = primary) and the outcomes it is **checked** against. Domain aliases (`@COST`, `@ASSET_LIFE`,
`@EVIDENCE`) resolve per Site domain; `@LINKED` is replaced by the caller's linked outcome keys, in the checked
role. The wire keeps every CHECKED item; only the list form hides a checked category that also moves."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from assetops_backend.outcomes.catalogue import CATEGORY_LABEL, COLD, DOMAINS, EV, MINI, OUTCOME_BY_KEY

POLICY_VERSION = "outcome-map/1"

ENTRIES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    # stored Finding mechanisms (the four that exist)
    "FINDING:GENERATOR_SUPPORT_CANDIDATE": (("MG-2",), ("MG-5", "MG-4")),  # mock outcomes.js:23 F-104
    "FINDING:COLD_START_FAILURE": (("CC-6", "CC-1"), ("CC-5", "CC-3")),  # F-118
    "FINDING:COLD_EXCURSION": (("CC-1",), ()),  # F-119
    "FINDING:EV_INTERRUPTION": (("EV-1", "EV-3"), ("EV-4",)),  # F-130
    # existing non-Finding signals (B)
    "SIGNAL:PRODUCTIVE_USE_HEADROOM": (("MG-1",), ("MG-2", "MG-5")),  # F-109 in the mock
    "SIGNAL:EVIDENCE_GAP": (("MG-7",), ("MG-2",)),  # F-108 in the mock (mini only)
    "SIGNAL:EVIDENCE_READINESS": (("@EVIDENCE",), ()),  # resolved per domain
    # early warnings (C); present from A so the map is complete
    "WARNING:REPEATED_MAINTENANCE_NO_RESULT": (("@COST",), ("@LINKED",)),
    "WARNING:PLAN_OVERDUE": (("@ASSET_LIFE",), ()),
    "WARNING:PLAN_DUE_SOON": (("@ASSET_LIFE",), ()),
    "WARNING:BATTERY_NEAR_RESERVE": (("MG-4",), ()),
    "WARNING:CHARGER_FAULT_OVERDUE_INSPECTION": (("EV-4",), ()),
    "WARNING:CONNECTOR_OUT_OF_SERVICE": (("EV-1",), ()),
    "WARNING:PEAK_NEAR_IMPORT_LIMIT": (("EV-5",), ("EV-1",)),
    "WARNING:CHARGERS_MOSTLY_IDLE": (("EV-3",), ("EV-1",)),
}
DOMAIN_ALIAS = {"@COST": {MINI: "MG-2", COLD: "CC-3", EV: "EV-2"},
                "@ASSET_LIFE": {MINI: "MG-4", COLD: "CC-5", EV: "EV-4"},
                "@EVIDENCE": {MINI: "MG-7", COLD: "CC-7", EV: "EV-7"}}

# Copied from analytics/adapters/postgres_finding_store.py:40 (a test asserts equality).
COLD_KIND_MECHANISM = {"EXCURSION": "COLD_EXCURSION", "START_RESPONSE": "COLD_START_FAILURE"}

UNMAPPED = "UNMAPPED"
_NOT_MAPPED: tuple[tuple[str, ...], tuple[str, ...]] = ((), ())


def finding_signal_key(mechanism: str | None) -> str:
    """The map key of a stored Finding mechanism; a missing mechanism maps to nothing."""
    return "FINDING:" + (mechanism or UNMAPPED)


def _resolve(keys: Sequence[str], domain: str, linked: Sequence[str]) -> list[str] | None:
    out: list[str] = []
    for key in keys:
        if key == "@LINKED":
            resolved = list(linked)
        elif key.startswith("@"):
            alias = DOMAIN_ALIAS.get(key, {}).get(domain)
            if alias is None:
                return None
            resolved = [alias]
        else:
            resolved = [key]
        for k in resolved:
            outcome = OUTCOME_BY_KEY.get(k)
            if outcome is None or outcome.domain != domain:
                return None
            if k not in out:
                out.append(k)
    return out


def outcome_roles(signal_key: str, domain: str, linked: Sequence[str] = ()) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(moves, checked) outcome keys after alias resolution; `moves[0]` is primary. `((), ())` when not mapped.
    Raises nothing."""
    entry = ENTRIES.get(signal_key)
    if entry is None or domain not in DOMAINS:
        return _NOT_MAPPED
    moves = _resolve(entry[0], domain, ())
    checked = _resolve(entry[1], domain, linked)
    if not moves or checked is None:
        return _NOT_MAPPED
    return tuple(moves), tuple(checked)


def _items(keys: Sequence[str], role: str) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = {}
    for k in keys:  # first-appearance category order, entry order inside (ruling A-Q3, mock byCat)
        groups.setdefault(OUTCOME_BY_KEY[k].category, []).append(k)
    return [{"category": cat, "label": CATEGORY_LABEL[cat], "role": role,
             "outcomes": [{"key": k, "label": OUTCOME_BY_KEY[k].label} for k in ks]}
            for cat, ks in groups.items()]


def categories_for(signal_key: str, domain: str, linked: Sequence[str] = ()) -> dict[str, Any]:
    """Wire `categories` object for one Finding/Action/warning. Unknown key or domain mismatch -> NOT_MAPPED."""
    moves, checked = outcome_roles(signal_key, domain, linked)
    if not moves:
        return {"policy_version": POLICY_VERSION, "state": "NOT_MAPPED", "items": []}
    return {"policy_version": POLICY_VERSION, "state": "MAPPED",
            "items": _items(moves, "MOVES") + _items(checked, "CHECKED")}
