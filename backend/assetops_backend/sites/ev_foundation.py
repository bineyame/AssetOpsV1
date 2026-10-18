"""W2-05a EV_CHARGING Foundation rules: properties, topology and the connector enable schedule.

Binding contract: `.agent/W2-05a-build-spec.md` (`D-2026-10-18-w2-05-buildspec`, Architect answers Q1-Q8) and
`.agent/W2-technical-design-ev.md` section 2.

Two entry points, both pure (no store, no SQL):

- `validate_ev_foundation` runs after the shared strict parser on every EV import and every later revision
  (`record_at` re-parses through `site_parsing`), so a malformed EV Foundation is never stored. It needs only the
  document and the Site timezone.
- `validate_ev_schedule_interval` checks each schedule's explicit UTC offset and local endpoints against the
  Site zone over one revision's effective interval. The interval is not part of the document, so the
  Foundation service runs it where a revision row is planned (import and publish).

Absence of the feed, its `ev-site-import-limit`, or every connector is publishable: readiness explains it. A
declared charger or connector missing a required property, any wrong value, invalid topology or invalid schedule
refuses as `EvConfigurationInvalid` (`EV_CONFIGURATION_INVALID`) with the path to the offending position.
Topology follows the QC/QD rulings (`D-2026-10-18-w2-05-buildspec`): at most one `AC_BUS` feed; a meter, charger
or connector with more than one parent always refuses; once a feed is declared, every meter must be fed by it and
every charger must reach it through one meter; any nonempty schedule needs the full feed->meter->charger path.
"""

from __future__ import annotations

import re
from datetime import datetime, time, timedelta, timezone
from typing import Mapping, NoReturn, Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from assetops_backend.sites.models import EV_PROPERTY_CARRIERS, WEEKDAYS, SiteFoundation
from assetops_backend.sites.ports import SiteConfigurationInvalid

EV_SITE_TYPE = "EV_CHARGING"
EV_CONFIGURATION_INVALID = "EV_CONFIGURATION_INVALID"

#: The topology node role each EV component type must occupy.
EV_NODE_ROLES: dict[str, str] = {
    "AC_BUS": "BUS",
    "METER": "METERING",
    "EV_CHARGER": "CHARGER",
    "EV_CONNECTOR": "CONNECTOR",
}

#: The directed component-type pairs each medium may join: feed -> import meter -> charger over AC, charger ->
#: connector over SIGNAL. No parallel relation list exists.
EV_EDGE_TYPES: dict[str, frozenset[tuple[str, str]]] = {
    "AC": frozenset({("AC_BUS", "METER"), ("METER", "EV_CHARGER")}),
    "SIGNAL": frozenset({("EV_CHARGER", "EV_CONNECTOR")}),
}

#: The properties a declared charger / connector must carry (Q3).
CHARGER_REQUIRED = ("ev-charger-max-power",)
CONNECTOR_REQUIRED = (
    "ev-connector-max-power",
    "ev-connector-enabled",
    "ev-meter-resolution",
    "ev-meter-error-bound",
    "ev-status-cadence",
    "ev-meter-cadence",
    "ev-clock-error-bound",
)
_STRICTLY_POSITIVE = (
    "ev-site-import-limit",
    "ev-charger-max-power",
    "ev-connector-max-power",
    "ev-meter-resolution",
    "ev-status-cadence",
    "ev-meter-cadence",
    "ev-clock-error-bound",
)
_NONNEGATIVE = ("ev-meter-error-bound",)

#: Cadence ceilings in minutes (Q4): state <= 60 s, meter-governed channels <= 300 s.
CADENCE_CEILING_MINUTES: dict[str, float] = {"ev-status-cadence": 1.0, "ev-meter-cadence": 5.0}

_LOCAL_TIME = re.compile(r"^([01][0-9]|2[0-3]):([0-5][0-9])$")

#: Through when an open-ended revision's zone must keep one offset: past the end of the explicit transition table
#: compiled zone files carry (2037) plus one full year of their recurring rule.
_FIXED_OFFSET_HORIZON_YEAR = 2039


class EvConfigurationInvalid(SiteConfigurationInvalid):
    """An EV Foundation refused before anything is written; `path` names the offending position."""

    code = EV_CONFIGURATION_INVALID

    def __init__(self, message: str, *, path: str) -> None:
        super().__init__(message)
        self.path = path


def _refuse(path: str, message: str, source: str) -> NoReturn:
    raise EvConfigurationInvalid(f"'{path}': {message} in {source}.", path=path)


# --- Foundation validation ----------------------------------------------------------------------------------


def validate_ev_foundation(foundation: SiteFoundation, *, timezone_name: str, source: str) -> None:
    """Refuse an EV_CHARGING Foundation that breaks a build-spec rule. Runs after the shared strict parser."""
    base = "site.foundation"
    types = {c.component_id: c.component_type for c in foundation.components}
    index_of = {c.component_id: i for i, c in enumerate(foundation.components)}
    enabled: dict[str, str] = {}
    for i, component in enumerate(foundation.components):
        where = f"{base}.components[{i}]"
        values: dict[str, float | str] = {}
        for j, prop in enumerate(component.properties or ()):
            carrier = EV_PROPERTY_CARRIERS.get(prop.property_key)
            if carrier is None:
                continue
            if component.component_type != carrier:
                _refuse(f"{where}.properties[{j}]",
                        f"{prop.property_key} belongs on a {carrier} component, not on {component.component_id} "
                        f"({component.component_type})", source)
            values[prop.property_key] = prop.value
        required = (CHARGER_REQUIRED if component.component_type == "EV_CHARGER"
                    else CONNECTOR_REQUIRED if component.component_type == "EV_CONNECTOR" else ())
        for key in required:
            if key not in values:
                _refuse(f"{where}.properties.{key}",
                        f"{component.component_type} {component.component_id} must declare {key}; a real Site "
                        "authors this value and there is no default", source)
        for key in _STRICTLY_POSITIVE:
            if key in values and not float(values[key]) > 0:
                _refuse(f"{where}.properties.{key}",
                        f"{key} on {component.component_id} must be greater than zero", source)
        for key in _NONNEGATIVE:
            if key in values and float(values[key]) < 0:
                _refuse(f"{where}.properties.{key}", f"{key} on {component.component_id} must not be negative",
                        source)
        for key, ceiling in CADENCE_CEILING_MINUTES.items():
            if key in values and float(values[key]) > ceiling:
                _refuse(f"{where}.properties.{key}",
                        f"{key} on {component.component_id} is {float(values[key]):g} min, above its "
                        f"{ceiling:g} min ceiling", source)
        if component.component_type == "EV_CONNECTOR":
            enabled[component.component_id] = str(values["ev-connector-enabled"])

    parents = _validate_ev_topology(foundation, types, base=base, source=source)
    _validate_schedules(foundation, types, index_of, enabled, parents, timezone_name=timezone_name, base=base,
                        source=source)


def _validate_ev_topology(foundation: SiteFoundation, types: Mapping[str, str], *, base: str,
                          source: str) -> dict[str, list[str]]:
    """Check the declared topology and return each component's parent components."""
    feeds_declared = [i for i, c in enumerate(foundation.components) if c.component_type == "AC_BUS"]
    if len(feeds_declared) > 1:
        extra = foundation.components[feeds_declared[1]]
        _refuse(f"{base}.components[{feeds_declared[1]}]",
                f"feed {extra.component_id} is a second AC_BUS; an EV Site declares at most one feed", source)
    feed_declared = bool(feeds_declared)
    parents: dict[str, list[str]] = {}
    noded: set[str] = set()
    topology = foundation.topology
    if topology is not None:
        node_component: dict[str, str] = {}
        for k, node in enumerate(topology.nodes):
            component_type = types[node.component_id]
            expected = EV_NODE_ROLES.get(component_type)
            if expected is not None and node.node_role != expected:
                _refuse(f"{base}.topology.nodes[{k}].node_role",
                        f"node {node.node_id} ({component_type}) must have node role {expected}, not "
                        f"{node.node_role}", source)
            node_component[node.node_id] = node.component_id
            noded.add(node.component_id)
        seen: set[tuple[str, str]] = set()
        successors: dict[str, list[str]] = {}
        for k, edge in enumerate(topology.connections):
            where = f"{base}.topology.connections[{k}]"
            a, b = node_component[edge.from_node], node_component[edge.to_node]
            pair = (types[a], types[b])
            allowed = EV_EDGE_TYPES.get(edge.medium)
            if allowed is None or pair not in allowed:
                _refuse(where, f"connection {edge.connection_id} joins {pair[0]} to {pair[1]} over {edge.medium}, "
                        "which an EV charging topology does not declare", source)
            if (edge.from_node, edge.to_node) in seen:
                _refuse(where, f"connection {edge.connection_id} duplicates {edge.from_node} -> {edge.to_node}",
                        source)
            seen.add((edge.from_node, edge.to_node))
            successors.setdefault(edge.from_node, []).append(edge.to_node)
            parents.setdefault(b, []).append(a)
        cycle = _find_cycle(successors)
        if cycle is not None:
            _refuse(f"{base}.topology.connections", f"the topology has a directed cycle through "
                    f"{' -> '.join(cycle)}", source)
    for i, component in enumerate(foundation.components):
        where = f"{base}.components[{i}]"
        cid, ctype = component.component_id, component.component_type
        mine = parents.get(cid, [])
        if ctype == "EV_CONNECTOR":
            if not mine:
                _refuse(where, f"connector {cid} has no parent charger in the topology", source)
            if len(mine) > 1:
                _refuse(where, f"connector {cid} has more than one parent charger ({', '.join(sorted(mine))})",
                        source)
        elif ctype == "EV_CHARGER":
            if len(mine) > 1:
                _refuse(where, f"charger {cid} is fed by more than one meter ({', '.join(sorted(mine))})", source)
            if feed_declared and not (mine and parents.get(mine[0])):
                _refuse(where, f"charger {cid} is not fed from the declared feed through one import meter", source)
        elif ctype == "METER":
            if len(mine) > 1:
                _refuse(where, f"import meter {cid} is fed by more than one feed ({', '.join(sorted(mine))})",
                        source)
            if not mine and feed_declared:
                _refuse(where, f"import meter {cid} is not connected to the declared feed", source)
    return parents


def _find_cycle(successors: Mapping[str, Sequence[str]]) -> list[str] | None:
    colour: dict[str, int] = {}
    path: list[str] = []

    def visit(node: str) -> list[str] | None:
        colour[node] = 1
        path.append(node)
        for nxt in successors.get(node, ()):
            state = colour.get(nxt, 0)
            if state == 1:
                return path[path.index(nxt):] + [nxt]
            if state == 0:
                found = visit(nxt)
                if found is not None:
                    return found
        path.pop()
        colour[node] = 2
        return None

    for start in sorted(successors):
        if colour.get(start, 0) == 0:
            found = visit(start)
            if found is not None:
                return found
    return None


def _minutes(text: str) -> int | None:
    match = _LOCAL_TIME.match(text)
    return None if match is None else int(match.group(1)) * 60 + int(match.group(2))


def _validate_schedules(foundation: SiteFoundation, types: Mapping[str, str], index_of: Mapping[str, int],
                        enabled: Mapping[str, str], parents: Mapping[str, list[str]], *, timezone_name: str,
                        base: str, source: str) -> None:
    where = f"{base}.connector_enable_schedules"
    schedules = foundation.connector_enable_schedules or ()
    connectors = [cid for cid, ctype in types.items() if ctype == "EV_CONNECTOR"]
    if connectors and not schedules:
        _refuse(where, "every declared connector needs exactly one enable schedule entry; none is declared", source)
    seen: set[str] = set()
    for k, schedule in enumerate(schedules):
        at = f"{where}[{k}]"
        cid = schedule.connector_asset_id
        if types.get(cid) != "EV_CONNECTOR":
            _refuse(f"{at}.connector_asset_id", f"{cid} is a {types.get(cid)} component, not an EV_CONNECTOR",
                    source)
        if cid in seen:
            _refuse(f"{at}.connector_asset_id", f"connector {cid} already has an enable schedule entry", source)
        seen.add(cid)
        if schedule.time_zone != timezone_name:
            _refuse(f"{at}.time_zone", f"the schedule zone {schedule.time_zone} must equal the Site timezone "
                    f"{timezone_name}", source)
        by_day: dict[str, list[tuple[int, int, int]]] = {}
        for m, interval in enumerate(schedule.weekly):
            item = f"{at}.weekly[{m}]"
            if interval.weekday not in WEEKDAYS:
                _refuse(f"{item}.weekday", f"weekday must be one of {list(WEEKDAYS)}, got {interval.weekday!r}",
                        source)
            start, end = _minutes(interval.local_start), _minutes(interval.local_end)
            if start is None:
                _refuse(f"{item}.local_start", f"local time must be HH:MM, got {interval.local_start!r}", source)
            if end is None:
                _refuse(f"{item}.local_end", f"local time must be HH:MM, got {interval.local_end!r}", source)
            if not start < end:
                _refuse(item, f"the interval {interval.local_start}-{interval.local_end} is reversed or empty; an "
                        "interval is half-open within one local day", source)
            for other_start, other_end, other in by_day.get(interval.weekday, []):
                if start < other_end and other_start < end:
                    _refuse(item, f"{interval.weekday} {interval.local_start}-{interval.local_end} overlaps "
                            f"weekly[{other}] of connector {cid}", source)
            by_day.setdefault(interval.weekday, []).append((start, end, m))
        if schedule.weekly:
            if enabled.get(cid) == "DISABLED":
                _refuse(f"{at}.weekly", f"connector {cid} is DISABLED, so it cannot declare enabled hours", source)
            if not _has_supply_path(cid, types, parents):
                _refuse(f"{at}.weekly", f"connector {cid} declares enabled hours without a charger fed from a "
                        "declared feed through an import meter", source)
    for cid in connectors:
        if cid not in seen:
            _refuse(f"{base}.components[{index_of[cid]}]",
                    f"connector {cid} has no enable schedule entry; declare one (an empty weekly list means no "
                    "enabled hours)", source)


def _has_supply_path(connector: str, types: Mapping[str, str], parents: Mapping[str, list[str]]) -> bool:
    for charger in parents.get(connector, []):
        for meter in parents.get(charger, []):
            if any(types.get(feed) == "AC_BUS" for feed in parents.get(meter, [])):
                return True
    return False


# --- effective-interval schedule check -----------------------------------------------------------------------


def validate_ev_schedule_interval(foundation: SiteFoundation, *, timezone_name: str, valid_from: datetime,
                                  valid_to: datetime | None, source: str) -> None:
    """Check every schedule occurrence in `[valid_from, valid_to)` against the Site zone (Q5).

    A bounded interval enumerates each occurrence: both local endpoints must exist, be unambiguous and carry the
    stated offset. An open-ended interval admits only a zone whose offset is fixed from `valid_from` on and equal
    to every stated offset; a zone with DST needs a bounded revision and a successor when its offset changes.
    """
    schedules = foundation.connector_enable_schedules or ()
    if not any(schedule.weekly for schedule in schedules):
        return
    base = "site.foundation.connector_enable_schedules"
    try:
        zone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError):
        _refuse(f"{base}[0].time_zone", f"the Site timezone {timezone_name} is not a known IANA zone, so no "
                "schedule occurrence can be resolved", source)
    if valid_to is None:
        fixed = _fixed_future_offset(zone, valid_from)
        for k, schedule in enumerate(schedules):
            for m, interval in enumerate(schedule.weekly):
                if fixed is None:
                    _refuse(f"{base}[{k}].weekly[{m}]",
                            f"the Site zone {timezone_name} changes its UTC offset after "
                            f"{valid_from.isoformat()}, so an open-ended revision cannot carry an enable schedule; "
                            "publish a bounded revision and a successor at the offset change", source)
                if interval.utc_offset_minutes != fixed:
                    _refuse(f"{base}[{k}].weekly[{m}].utc_offset_minutes",
                            f"the stated offset {interval.utc_offset_minutes} min does not match the "
                            f"{timezone_name} offset {fixed} min", source)
        return
    first = valid_from.astimezone(zone).date() - timedelta(days=1)
    last = valid_to.astimezone(zone).date() + timedelta(days=1)
    for k, schedule in enumerate(schedules):
        for m, interval in enumerate(schedule.weekly):
            where = f"{base}[{k}].weekly[{m}]"
            weekday = WEEKDAYS.index(interval.weekday)
            day = first + timedelta(days=(weekday - first.weekday()) % 7)
            offset = timedelta(minutes=interval.utc_offset_minutes)
            while day <= last:
                start = datetime.combine(day, _clock(interval.local_start))
                end = datetime.combine(day, _clock(interval.local_end))
                utc_start, utc_end = (start - offset).replace(tzinfo=timezone.utc), \
                    (end - offset).replace(tzinfo=timezone.utc)
                if utc_start < valid_to and utc_end > valid_from:
                    for key, local in (("local_start", start), ("local_end", end)):
                        problem = _local_problem(zone, local, interval.utc_offset_minutes)
                        if problem is not None:
                            _refuse(f"{where}.{key}", f"{interval.weekday} {local.isoformat()} in {timezone_name} "
                                    f"{problem}", source)
                day += timedelta(days=7)


def _clock(text: str) -> time:
    minutes = _minutes(text)
    assert minutes is not None
    return time(minutes // 60, minutes % 60)


def _local_problem(zone: ZoneInfo, local: datetime, stated_minutes: int) -> str | None:
    early = local.replace(tzinfo=zone, fold=0)
    late = local.replace(tzinfo=zone, fold=1)
    round_trip = early.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)
    if round_trip != local:
        return "does not exist (the local clock skips it)"
    if early.utcoffset() != late.utcoffset():
        return "is ambiguous (the local clock repeats it)"
    actual = early.utcoffset()
    assert actual is not None
    if actual != timedelta(minutes=stated_minutes):
        return (f"has UTC offset {int(actual.total_seconds() // 60)} min, not the stated "
                f"{stated_minutes} min")
    return None


def _fixed_future_offset(zone: ZoneInfo, valid_from: datetime) -> int | None:
    """The zone's offset in minutes if it never changes from `valid_from` on, else None."""
    instant = valid_from.astimezone(timezone.utc)
    horizon = datetime(max(_FIXED_OFFSET_HORIZON_YEAR, instant.year + 2), 1, 1, tzinfo=timezone.utc)
    first = instant.astimezone(zone).utcoffset()
    step = timedelta(hours=12)
    while instant < horizon:
        if instant.astimezone(zone).utcoffset() != first:
            return None
        instant += step
    assert first is not None
    return int(first.total_seconds() // 60)


__all__ = [
    "EV_CONFIGURATION_INVALID",
    "EV_SITE_TYPE",
    "EvConfigurationInvalid",
    "validate_ev_foundation",
    "validate_ev_schedule_interval",
]
