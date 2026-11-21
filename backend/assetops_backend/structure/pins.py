"""3B2: each stored Finding mechanism pinned to the factor it observes (spec §2, §4; D-3B2.1 to D-3B2.15).

A pin is a code row keyed by mechanism, read at query time: no Finding column (D-3B2.1). A pinned Finding's
category is its factor's home category (OD-21). The outcome map's literal stays until 3B5 (D-3B2.3); `parity()`
lists where the two readings differ, and each difference is ruled (D-3B2.4).

`check.check_pins` refuses a bad pin at start-up. This module never imports `check`. `registry.REGISTRIES`, `PINS`
and `outcome_map.ENTRIES` are read through their modules at call time (D-3B2.11).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from assetops_backend.outcomes import outcome_map as _outcome_map
from assetops_backend.outcomes.catalogue import OUTCOME_BY_KEY
from assetops_backend.structure import registry as _registry


@dataclass(frozen=True)
class Pin:
    mechanism: str
    structure_key: str
    factor_id: str


#: D-3B2.7: a pin's one domain, the `catalogue.py` domain values.
DOMAIN_OF_STRUCTURE: Mapping[str, str] = MappingProxyType({
    "MINI_GRID": "mini_grid",
    "COLD_CHAIN": "cold_chain",
    "EV_DEPOT_CAPTIVE": "ev_charging",
})

#: Design §4: today's stored mechanisms on structures that have a registry.
PINS: Mapping[str, Pin] = MappingProxyType({
    "GENERATOR_SUPPORT_CANDIDATE": Pin("GENERATOR_SUPPORT_CANDIDATE", "MINI_GRID", "candidate_l"),
    "UNEXPLAINED_FUEL": Pin("UNEXPLAINED_FUEL", "MINI_GRID", "unexplained_l"),
    # 3B6 (D-3B6.5): pinned to leaves under Protect P1.
    "COLD_START_FAILURE": Pin("COLD_START_FAILURE", "COLD_CHAIN", "uncovered_nights"),
    "COLD_EXCURSION": Pin("COLD_EXCURSION", "COLD_CHAIN", "excursion_crates"),
    "EV_INTERRUPTION": Pin("EV_INTERRUPTION", "EV_DEPOT_CAPTIVE", "chargers_in_service"),
})

#: D-3B2.2: mechanism -> structure key, for registries that do not exist yet. 3B6 moved the three into `PINS`; empty
#: until another structure has pending mechanisms.
PENDING_PINS: Mapping[str, str] = MappingProxyType({})

_PLACEMENTS = frozenset({_registry.HOMES["above"], _registry.HOMES["calendar"]})


def pin_of(mechanism: str) -> Pin | None:
    """The mechanism's pin; `None` when pending or unknown."""
    return PINS.get(mechanism)


def pinned_category(mechanism: str) -> str | None:
    """The home category of the pinned factor's row, read at call time; `None` when pending, unknown, or when the
    row's home is a placement (`ABOVE`, `CALENDAR`)."""
    pin = pin_of(mechanism)
    if pin is None:
        return None
    category = _registry.REGISTRIES[pin.structure_key].row(pin.factor_id).home.category
    return None if category in _PLACEMENTS else category


@dataclass(frozen=True)
class Divergence:
    mechanism: str
    literal_category: str | None
    registry_category: str | None
    literal_lens: str | None
    registry_lens: str | None


def _literal_category(mechanism: str, domain: str) -> str | None:
    moves, _ = _outcome_map.outcome_roles(_outcome_map.finding_signal_key(mechanism), domain)
    return OUTCOME_BY_KEY[moves[0]].category if moves else None


def parity() -> tuple[Divergence, ...]:
    """One entry per pinned mechanism whose outcome-map reading differs from its registry reading, compared in the
    pin's own domain only (D-3B2.7)."""
    out: list[Divergence] = []
    lens = _outcome_map.LENS_OF_CATEGORY
    for mechanism, pin in PINS.items():
        literal = _literal_category(mechanism, DOMAIN_OF_STRUCTURE[pin.structure_key])
        pinned = pinned_category(mechanism)
        entry = Divergence(mechanism, literal, pinned, lens.get(literal), lens.get(pinned))
        if (entry.literal_category, entry.literal_lens) != (entry.registry_category, entry.registry_lens):
            out.append(entry)
    return tuple(out)


__all__ = ["DOMAIN_OF_STRUCTURE", "PENDING_PINS", "PINS", "Divergence", "Pin", "parity", "pin_of",
           "pinned_category"]
