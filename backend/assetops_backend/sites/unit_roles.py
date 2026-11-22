"""Site figures from unit evidence: the one rule (D-DD.41, built in DD3.4 / DD3c; D-DD.44) and the lead-unit policy
read (D-DD.43). Pure; every reader of a `minigrid-roles-5` set calls this module, and no reader sums units itself.

- Power (and litres, each unit burnt on its own curve): the Site value at a step is the sum of the units' values; a
  unit with no value at that step makes the Site value absent there, named by unit. No imputation.
- `generator_state`: RUNNING if any unit runs, else STARTING if any starts, else STOPPED if any unit is not FAILED,
  else FAILED. A unit with no state makes the Site state absent (DD3c pre-flight Q4 default).
- `mini_backup_start_event`: the union in time order, each event keeping its unit; equal times in declared order.
- Site generator rating: the sum of the non-FAILED units' `generator-rated-power`.
- Site control policy: from the lead unit (first GENERATOR in declared order); a non-lead unit carrying a policy
  property is refused `TEL_FOUNDATION`.

One unit gives the unit's own value byte for byte (the same object), so a one-unit Site reads as today.
"""

from __future__ import annotations

from collections.abc import Callable, Hashable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import reduce
from operator import add
from typing import Any

GENERATOR = "GENERATOR"
RATING_KEY = "generator-rated-power"
#: The Site's one control policy, held on the lead unit (D-DD.43).
POLICY_KEYS: tuple[str, ...] = ("start-soc-threshold", "stop-soc-threshold", "start-delay", "minimum-runtime")
RUNNING, STARTING, STOPPED, FAILED = "RUNNING", "STARTING", "STOPPED", "FAILED"
REFUSED_CODE = "TEL_FOUNDATION"


@dataclass(frozen=True)
class SiteValue:
    """A Site figure at one step: `value` None means absent; `missing` names the units that made it so."""

    value: Any
    missing: tuple[str, ...]


class UnitRolesRefused(ValueError):
    def __init__(self, unit: str, detail: str) -> None:
        super().__init__(f"{REFUSED_CODE}: {detail}")
        self.code = REFUSED_CODE
        self.unit = unit


def _missing(values: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(unit for unit, v in values.items() if v is None)


def site_power(values: Mapping[str, Any]) -> SiteValue:
    """One step: unit -> value (None = no value). Summed without a start term, so one unit is its own object."""
    missing = _missing(values)
    if missing or not values:
        return SiteValue(None, missing)
    return SiteValue(reduce(add, values.values()), ())


#: Litres: each unit burnt on its own curve by the reader, then summed by the same rule.
site_litres = site_power


def site_power_series(series: Mapping[str, Mapping[Hashable, Any]]) -> dict[Hashable, SiteValue]:
    """unit -> {step: value}: the Site value at every step any unit has, in first-seen step order."""
    steps = dict.fromkeys(step for by_step in series.values() for step in by_step)
    return {step: site_power({unit: by_step.get(step) for unit, by_step in series.items()}) for step in steps}


def site_generator_state(states: Mapping[str, str | None]) -> SiteValue:
    missing = _missing(states)
    if missing or not states:
        return SiteValue(None, missing)
    if len(states) == 1:
        return SiteValue(next(iter(states.values())), ())
    present = set(states.values())
    for state in (RUNNING, STARTING):
        if state in present:
            return SiteValue(state, ())
    return SiteValue(STOPPED if present != {FAILED} else FAILED, ())


def site_events(events: Mapping[str, Iterable[Any]], *, at: Callable[[Any], Any]) -> tuple[tuple[str, Any], ...]:
    """The union of the units' events in time order, each as (unit, event); ties keep the units' given order."""
    tagged = [(unit, e) for unit, unit_events in events.items() for e in unit_events]
    return tuple(sorted(tagged, key=lambda pair: at(pair[1])))


def units(components: Sequence[Mapping[str, Any]], asset_type: str) -> tuple[Mapping[str, Any], ...]:
    """The Foundation's components of `asset_type`, in declared order."""
    return tuple(c for c in components if c.get("component_type") == asset_type)


def lead_unit(components: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    generators = units(components, GENERATOR)
    return generators[0] if generators else None


def _properties(unit: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return list(unit.get("properties") or ())


def lead_policy(components: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    """The lead unit's policy properties by key (the property records themselves); refused when a non-lead unit
    carries one."""
    generators = units(components, GENERATOR)
    for unit in generators[1:]:
        held = sorted({p.get("property_key") for p in _properties(unit)} & set(POLICY_KEYS))
        if held:
            raise UnitRolesRefused(str(unit.get("component_id")),
                                   f"non-lead unit {unit.get('component_id')} carries policy {held}")
    if not generators:
        return {}
    return {p["property_key"]: p for p in _properties(generators[0]) if p.get("property_key") in POLICY_KEYS}


def site_rating(components: Sequence[Mapping[str, Any]],
                states: Mapping[str, str | None] | None = None) -> SiteValue:
    """The sum of the non-FAILED units' rated power. `states` (unit -> state at the step) None: a Foundation-only
    read, every unit counts (pre-flight Q5 default)."""
    ratings: dict[str, Any] = {}
    for unit in units(components, GENERATOR):
        code = str(unit.get("component_id"))
        if states is not None:
            if states.get(code) is None:
                return SiteValue(None, _missing({c: states.get(c) for c in
                                                 (str(u.get("component_id")) for u in units(components, GENERATOR))}))
            if states[code] == FAILED:
                continue
        found = [p.get("value") for p in _properties(unit) if p.get("property_key") == RATING_KEY]
        ratings[code] = found[0] if len(found) == 1 else None
    return site_power(ratings)
