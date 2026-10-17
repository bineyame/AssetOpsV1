"""W2-01 COLDCHAIN Foundation rules, configuration readiness and the selected cold read.

Binding contract: `.agent/W2-technical-design-cold.md` section 3 (`D-2026-10-17-w2-01-answers` A-I and the
W2-02 channel closure) and the `GET /api/sites/{code}/cold/foundation` field row.

Three separate things are kept separate here, as the design requires:

- **Configuration readiness** says what the selected Foundation and binding set declare. It is never a claim
  that any temperature, start or transfer has been observed.
- **Commissioning** has no persisted evidence record yet, so it is always `UNCONFIRMED` with no IDs.
- **Gateway contact** is the selected Site's gateway diagnostic receive time; it is contact, not equipment
  health.

Pure functions only: no store, no SQL. The API module supplies the selected view and gateway facts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Mapping, NoReturn, Sequence

from assetops_backend.sites.binding_roles import (
    COLD_PERIODIC_CADENCE_SECONDS,
    COLD_POLICY_PROPERTIES,
    ROLE_SET_COLD_1,
    roles_for,
)
from assetops_backend.sites.models import COLD_PROPERTY_CARRIERS, SiteFoundation

COLD_SITE_TYPE = "COLDCHAIN"

#: The topology node role each cold-relevant component type must occupy (design section 3 A).
COLD_NODE_ROLES: dict[str, str] = {
    "COLD_ROOM": "COLD_ROOM",
    "TEMPERATURE_PROBE": "SENSOR",
    "COMPRESSOR": "COOLING",
    "TRANSFER_SWITCH": "SWITCH",
    "GENERATOR": "GENERATION",
    "AC_BUS": "BUS",
    "METER": "METERING",
}

#: The directed component-type pairs each medium may join in a COLDCHAIN topology (design section 3 A):
#: room -> primary chamber probe (SIGNAL), compressor -> room (THERMAL), and
#: meter -> transfer switch -> AC bus -> compressor plus generator -> transfer switch (AC).
COLD_EDGE_TYPES: dict[str, frozenset[tuple[str, str]]] = {
    "SIGNAL": frozenset({("COLD_ROOM", "TEMPERATURE_PROBE")}),
    "THERMAL": frozenset({("COMPRESSOR", "COLD_ROOM")}),
    "AC": frozenset({
        ("METER", "TRANSFER_SWITCH"),
        ("TRANSFER_SWITCH", "AC_BUS"),
        ("AC_BUS", "COMPRESSOR"),
        ("GENERATOR", "TRANSFER_SWITCH"),
    }),
}

#: Cold-specific value rules on top of the parser-wide unit ranges (design section 3 C).
_STRICTLY_POSITIVE = ("cold-thermal-capacity", "cold-heat-leak", "cold-cooling-capacity", "cold-start-timeout",
                      "cold-min-excursion")
_NONNEGATIVE = ("cold-door-heat", "cold-compressor-start-delay", "cold-probe-error", "cold-return-hysteresis")

#: Readiness wording. The first four are the design's verbatim publication-readiness messages.
MESSAGE_PROBE = "Add a chamber temperature probe and bind its °C reading"
MESSAGE_POLICY = "Set a lower and upper temperature policy for this room"
MESSAGE_START = "Bind the generator start request and result"
MESSAGE_TRANSFER = "Transfer position is not reported; switch state is unknown"
MESSAGE_NO_ROOM = "Declare a cold room"
CONTACT_UNVERIFIED = "Contact time cannot be verified"
CONTACT_UNAVAILABLE = "Gateway contact is not available"

READY = "READY_TO_REPORT"
INCOMPLETE = "CONFIGURATION_INCOMPLETE"


# --- Foundation validation (refuses, before anything is written) ----------------------------------------------


def validate_cold_foundation(foundation: SiteFoundation, *, source: str,
                             invalid: Callable[[str], NoReturn]) -> None:
    """Refuse a COLDCHAIN Foundation that breaks a section 3 rule. Runs after the shared strict parser."""
    types = {c.component_id: c.component_type for c in foundation.components}
    for component in foundation.components:
        values: dict[str, float] = {}
        for prop in component.properties or ():
            carrier = COLD_PROPERTY_CARRIERS.get(prop.property_key)
            if carrier is None:
                continue
            if component.component_type != carrier:
                invalid(f"{prop.property_key} belongs on a {carrier} component, not on {component.component_id} "
                        f"({component.component_type}), in {source}.")
            values[prop.property_key] = prop.value
        for key in _STRICTLY_POSITIVE:
            if key in values and not values[key] > 0:
                invalid(f"{key} on {component.component_id} must be greater than zero in {source}.")
        for key in _NONNEGATIVE:
            if key in values and values[key] < 0:
                invalid(f"{key} on {component.component_id} must not be negative in {source}.")
        for band in ("policy", "control"):
            low, high = values.get(f"cold-{band}-low"), values.get(f"cold-{band}-high")
            if (low is None) != (high is None):
                invalid(f"{component.component_id} declares only one end of its {band} band in {source}; "
                        "a band needs both a lower and an upper temperature.")
            if low is not None and high is not None and not low < high:
                invalid(f"{component.component_id}'s {band} band low ({low:g} degC) must be below its high "
                        f"({high:g} degC) in {source}.")
        hysteresis = values.get("cold-return-hysteresis")
        if hysteresis is not None:
            low, high = values.get("cold-control-low"), values.get("cold-control-high")
            if low is None or high is None:
                invalid(f"{component.component_id} declares a return hysteresis without a control band in {source}.")
            if not hysteresis < high - low:
                invalid(f"{component.component_id}'s return hysteresis ({hysteresis:g} degC) must be smaller than "
                        f"its control band width ({high - low:g} degC) in {source}.")
    if foundation.topology is not None:
        _validate_cold_topology(foundation, types, source=source, invalid=invalid)


def _validate_cold_topology(foundation: SiteFoundation, types: Mapping[str, str], *, source: str,
                            invalid: Callable[[str], NoReturn]) -> None:
    topology = foundation.topology
    assert topology is not None
    node_type: dict[str, str] = {}
    for node in topology.nodes:
        component_type = types[node.component_id]
        expected = COLD_NODE_ROLES.get(component_type)
        if expected is not None and node.node_role != expected:
            invalid(f"Topology node {node.node_id} ({component_type}) must have node role {expected}, not "
                    f"{node.node_role}, in {source}.")
        node_type[node.node_id] = component_type
    seen: set[tuple[str, str, str]] = set()
    signal_out: dict[str, str] = {}
    signal_in: dict[str, str] = {}
    successors: dict[str, list[str]] = {}
    for edge in topology.connections:
        pair = (node_type[edge.from_node], node_type[edge.to_node])
        allowed = COLD_EDGE_TYPES.get(edge.medium)
        if allowed is None or pair not in allowed:
            invalid(f"Connection {edge.connection_id} joins {pair[0]} to {pair[1]} over {edge.medium}, which a "
                    f"cold-chain topology does not declare, in {source}.")
        key = (edge.from_node, edge.to_node, edge.medium)
        if key in seen:
            invalid(f"Connection {edge.connection_id} duplicates {edge.from_node} -> {edge.to_node} "
                    f"({edge.medium}) in {source}.")
        seen.add(key)
        if edge.medium == "SIGNAL":
            if edge.from_node in signal_out:
                invalid(f"Room node {edge.from_node} already has a primary chamber probe "
                        f"({signal_out[edge.from_node]}); {edge.connection_id} would add a second, in {source}.")
            if edge.to_node in signal_in:
                invalid(f"Probe node {edge.to_node} is already the primary probe of room {signal_in[edge.to_node]}; "
                        f"{edge.connection_id} would link it to a second room, in {source}.")
            signal_out[edge.from_node] = edge.to_node
            signal_in[edge.to_node] = edge.from_node
        successors.setdefault(edge.from_node, []).append(edge.to_node)
    cycle = _find_cycle(successors)
    if cycle is not None:
        invalid(f"The topology has a directed cycle through {' -> '.join(cycle)} in {source}.")


def _find_cycle(successors: Mapping[str, Sequence[str]]) -> list[str] | None:
    WHITE, GREY, BLACK = 0, 1, 2
    colour: dict[str, int] = {}
    stack_path: list[str] = []

    def visit(node: str) -> list[str] | None:
        colour[node] = GREY
        stack_path.append(node)
        for nxt in successors.get(node, ()):
            state = colour.get(nxt, WHITE)
            if state == GREY:
                return stack_path[stack_path.index(nxt):] + [nxt]
            if state == WHITE:
                found = visit(nxt)
                if found is not None:
                    return found
        stack_path.pop()
        colour[node] = BLACK
        return None

    for start in sorted(successors):
        if colour.get(start, WHITE) == WHITE:
            found = visit(start)
            if found is not None:
                return found
    return None


# --- the selected read -----------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ContactFacts:
    """The selected Site gateway's latest diagnostic receive time and its freshness (S7 `freshness`)."""

    received_at: datetime | None
    freshness: str  # CURRENT | STALE | UNKNOWN


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def contact_document(facts: ContactFacts | None) -> dict[str, Any]:
    """Design section 3 D-I: CURRENT -> RECENT, STALE -> STALE, no diagnostic -> NEVER; a diagnostic whose
    freshness is UNKNOWN is STALE with a limitation, never a claim of recent contact."""
    if facts is None:
        return {"state": None, "as_of": None, "limitations": [CONTACT_UNAVAILABLE]}
    if facts.received_at is None:
        return {"state": "NEVER", "as_of": None, "limitations": []}
    if facts.freshness == "CURRENT":
        return {"state": "RECENT", "as_of": _iso(facts.received_at), "limitations": []}
    if facts.freshness == "STALE":
        return {"state": "STALE", "as_of": _iso(facts.received_at), "limitations": []}
    return {"state": "STALE", "as_of": _iso(facts.received_at), "limitations": [CONTACT_UNVERIFIED]}


def _properties(component: Mapping[str, Any]) -> dict[str, float]:
    return {p["property_key"]: p["value"] for p in component.get("properties") or ()}


def cold_foundation_document(
    *,
    revision: Any,
    binding_set: Any,
    assets_by_code: Mapping[str, Any],
    contact: ContactFacts | None,
) -> dict[str, Any]:
    """The `GET /api/sites/{code}/cold/foundation` body for one selected effective revision."""
    content = revision.content
    components = list(content.get("components") or ())
    by_id = {c["component_id"]: c for c in components}

    def asset_id(component_id: str) -> str | None:
        asset = assets_by_code.get(component_id)
        return None if asset is None else str(asset.id)

    topology = content.get("topology")
    node_component: dict[str, str] = {}
    edges: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []
    if topology is not None:
        for node in topology.get("nodes") or ():
            node_component[node["node_id"]] = node["component_id"]
            nodes.append({
                "node_id": node["node_id"],
                "component_id": node["component_id"],
                "asset_id": asset_id(node["component_id"]),
                "component_type": by_id.get(node["component_id"], {}).get("component_type"),
                "display_name": by_id.get(node["component_id"], {}).get("display_name"),
                "node_role": node["node_role"],
            })
        for edge in topology.get("connections") or ():
            edges.append({
                "connection_id": edge["connection_id"],
                "from_node": edge["from_node"],
                "to_node": edge["to_node"],
                "medium": edge["medium"],
            })

    def linked(room_id: str, medium: str, outgoing: bool) -> list[str]:
        found: list[str] = []
        for edge in edges:
            if edge["medium"] != medium:
                continue
            here, there = (edge["from_node"], edge["to_node"]) if outgoing else (edge["to_node"], edge["from_node"])
            if node_component.get(here) == room_id and there in node_component:
                found.append(node_component[there])
        return found

    bindings = tuple(binding_set.bindings) if binding_set is not None else ()
    roles = roles_for(ROLE_SET_COLD_1 if binding_set is None else binding_set.role_set)
    bound: dict[tuple[str, str | None], Any] = {}
    for row in bindings:
        bound[(row.role, None if row.asset_id is None else str(row.asset_id))] = row
    bound_roles = {row.role for row in bindings}

    messages: list[dict[str, Any]] = []

    def say(code: str, role: str | None, component_id: str | None, message: str, blocking: bool = True) -> None:
        messages.append({"code": code, "role": role, "component_id": component_id,
                         "asset_id": None if component_id is None else asset_id(component_id),
                         "message": message, "blocking": blocking})

    rooms: list[dict[str, Any]] = []
    room_components = [c for c in components if c.get("component_type") == "COLD_ROOM"]
    if not room_components:
        say("ROOM_MISSING", None, None, MESSAGE_NO_ROOM)
    for room in room_components:
        props = _properties(room)
        probes = linked(room["component_id"], "SIGNAL", outgoing=True)
        compressors = linked(room["component_id"], "THERMAL", outgoing=False)
        low, high = props.get(COLD_POLICY_PROPERTIES["cold_policy_low"]), props.get(
            COLD_POLICY_PROPERTIES["cold_policy_high"])
        rooms.append({
            "asset_id": asset_id(room["component_id"]),
            "policy": {"low": low, "high": high, "unit": "degC", "revision_id": str(revision.id)},
            "probe_ids": [a for a in (asset_id(p) for p in probes) if a is not None],
            "compressor_ids": [a for a in (asset_id(c) for c in compressors) if a is not None],
        })
        probe_bound = len(probes) == 1 and ("chamber_temperature", asset_id(probes[0])) in bound
        if not probe_bound:
            say("PROBE_MISSING", "chamber_temperature", room["component_id"], MESSAGE_PROBE)
        if low is None or high is None:
            say("POLICY_MISSING", "cold_policy_low" if low is None else "cold_policy_high", room["component_id"],
                MESSAGE_POLICY)

    if "backup_start_event" not in bound_roles:
        say("START_EVENT_MISSING", "backup_start_event", None, MESSAGE_START)
    for role in roles.values():
        if not role.required or role.covered_by != "CHANNEL":
            continue
        if role.role in ("chamber_temperature", "backup_start_event"):
            continue
        if role.cardinality == "PER_ASSET":
            for component in components:
                if component.get("component_type") == role.asset_type and (
                        role.role, asset_id(component["component_id"])) not in bound:
                    say("ROLE_UNBOUND", role.role, component["component_id"], f"Bind the {role.label.lower()}")
        elif role.role not in bound_roles:
            say("ROLE_UNBOUND", role.role, None, f"Bind the {role.label.lower()}")
    if "transfer_result" not in bound_roles:
        say("TRANSFER_UNREPORTED", "transfer_result", None, MESSAGE_TRANSFER, blocking=False)

    binding_items: list[dict[str, Any]] = []
    for row in sorted(bindings, key=lambda r: (r.role, str(r.asset_id))):
        role = roles.get(row.role)
        event = role is not None and role.value_kind == "EVENT"
        binding_items.append({
            "role": row.role,
            "asset_id": None if row.asset_id is None else str(row.asset_id),
            "source_id": str(row.source_id),
            "unit": row.canonical_unit,
            "cadence_seconds": None if event else COLD_PERIODIC_CADENCE_SECONDS,
            "publication_mode": "transition" if event else "periodic",
        })

    return {
        "foundation_revision_id": str(revision.id),
        "valid_from": _iso(revision.valid_from),
        "valid_to": _iso(revision.valid_to),
        "rooms": rooms,
        "topology": None if topology is None else {"nodes": nodes, "edges": edges},
        "bindings": binding_items,
        "readiness": {
            "state": INCOMPLETE if any(m["blocking"] for m in messages) else READY,
            "messages": messages,
        },
        "commissioning": {"state": "UNCONFIRMED", "evidence_ids": []},
        "contact": contact_document(contact),
    }


def assets_by_code(assets: Iterable[Any]) -> dict[str, Any]:
    return {asset.asset_code: asset for asset in assets}
