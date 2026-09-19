"""The one strict validator for the Foundation content below the components.

Topology, devices, signal availability, device-to-signal mappings, and control
assumptions are validated here, once, for both document families. The template
parser and the Site parser each own their identity and provenance rules, but
what a Foundation declares below its component list is the same thing whoever
wrote the document, so it is checked by the same code.

That matters more here than anywhere else in this package. The template parser
reads shipped configuration and the Site parser reads user-authored
configuration; two copies of these rules would let one of them drift into
accepting a topology the other refuses, and the Site created from a template
would then be validated more loosely than the template it came from.

This module takes already-loaded mappings and returns domain records. It never
opens, reads, decodes, or locates anything, so it needs no exemption from the
storage-technology guard in `tools/check-architecture.ps1`. It raises nothing
of its own either: the caller supplies the refusal, because a template refusal
and a Site refusal are different exception types and a user meets the second
one as product copy.

What is deliberately not here:

- No control state, setpoint, mode, or breaker position. Whether a breaker is a
  device, component state, or both is a product decision held for the T016
  user-review checkpoint, so a control assumption carries a declared statement
  and its provenance and nothing that could be mistaken for a control model.
- No runtime or evidence field on a device or a signal. A declared signal is
  signal AVAILABILITY - that a device is configured to be able to report it.
  There is nowhere here to put a reading, a timestamp, a health state, or a
  cadence, so nothing downstream can read one out of configuration.
- No inference. A mapping is declared or it does not exist. Nothing here
  derives one from a display name, a topology position, a protocol label, or a
  component type, because a derived mapping is a claim the document never made.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Mapping, NoReturn

from assetops_backend.sites.models import (
    CONNECTION_MEDIA,
    CONTROL_ASSUMPTION_BASES,
    DEVICE_TYPES,
    SIGNAL_UNITS,
    TOPOLOGY_NODE_ROLES,
    ControlAssumption,
    DeviceSignal,
    FoundationContent,
    FoundationDevice,
    FoundationTopology,
    SignalMapping,
    TopologyConnection,
    TopologyNode,
)

#: The four keys T014 adds to a Foundation document. Exported so that both
#: parsers extend their own allowlist from one place: a key allowed by one
#: parser and not the other would be a document the template store accepts and
#: the Site store refuses.
FOUNDATION_CONTENT_KEYS = frozenset(
    {"topology", "devices", "signal_mappings", "control_assumptions"}
)

TOPOLOGY_KEYS = frozenset({"nodes", "connections"})
TOPOLOGY_NODE_KEYS = frozenset({"node_id", "component_id", "node_role"})
CONNECTION_KEYS = frozenset({"connection_id", "from_node", "to_node", "medium"})
DEVICE_KEYS = frozenset(
    {"device_id", "device_type", "display_name", "component_id", "signals"}
)
SIGNAL_KEYS = frozenset({"signal_id", "display_name", "unit"})
SIGNAL_MAPPING_KEYS = frozenset(
    {"mapping_id", "device_id", "signal_id", "component_id"}
)
CONTROL_ASSUMPTION_KEYS = frozenset(
    {"assumption_id", "display_name", "component_id", "basis", "statement"}
)

# Cardinality bounds. A document that declares ten thousand connections is
# refused rather than rendered: a screen nobody can scroll past is the same
# defect as a store nobody can read, arriving one panel later.
MAX_TOPOLOGY_NODES = 64
MAX_CONNECTIONS = 128
# 64 rather than 128, and the difference is whether this cap can fire at all.
#
# A device carries an id, a name, a component reference and a signal list, and
# the document walker counts every key and scalar in it. Measured against the
# 2,000-node document ceiling, a document is refused for node count at 77
# devices - so a cap of 128 could never be reached. Such a document was refused,
# but for the wrong reason and with a message about node counts rather than
# about devices, which tells a reader nothing about what to remove.
#
# A cap that cannot fire is not protection. This one moves under the ceiling
# rather than the ceiling moving over it: raising the ceiling to reach the cap
# would have loosened a whole-document guard to make a per-section guard
# reachable, which is backwards.
#
# 64 leaves headroom under the 77 the ceiling refuses at, so the cap stays the
# first thing to fire even as a device grows more signals.
MAX_DEVICES = 64
MAX_SIGNALS_PER_DEVICE = 32
# 160 rather than 256, for the reason MAX_DEVICES is 64 rather than 128.
#
# Measured: the 2,000-node document ceiling starts refusing at 208 mappings, so
# a cap of 256 could never be reached and a 257-entry list was refused for node
# count instead - the wrong guard, with a message naming nodes rather than
# mappings. 160 leaves headroom under 208 so this stays the first guard to
# speak.
#
# Every cap in this module is measured that way by
# `TestEveryCapCanFire`: build a document at cap + 1 and read which guard
# answers. A cap above the ceiling is not a limit, it is a comment.
MAX_SIGNAL_MAPPINGS = 160
MAX_CONTROL_ASSUMPTIONS = 32

MAX_IDENTIFIER_LENGTH = 64
MAX_DISPLAY_NAME_LENGTH = 120
MAX_STATEMENT_LENGTH = 400

#: The same identifier shape every other identity in this package uses.
IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

Invalid = Callable[[str], NoReturn]


def parse_foundation_content(
    foundation: Mapping[str, Any],
    *,
    component_ids: frozenset[str],
    where: str,
    source: str,
    invalid: Invalid,
) -> FoundationContent:
    """Validate the four sections below a Foundation's component list.

    Args:
        foundation: the already-loaded Foundation mapping. Never a path or
            YAML text.
        component_ids: the component identities this same Foundation declares.
            Every component reference below is checked against these, which is
            what keeps topology and devices from naming a component that does
            not exist.
        where: the document path prefix for messages, such as `foundation` or
            `site.foundation`.
        source: a human-readable name for the document, used in messages only.
        invalid: raises the caller's refusal. A template refusal and a Site
            refusal are different types and a user reads the second one.

    Returns:
        The four sections, each `None` when the document declares none.
    """
    topology = _parse_topology(
        foundation.get("topology"),
        component_ids=component_ids,
        where=f"{where}.topology",
        source=source,
        invalid=invalid,
    )
    devices = _parse_devices(
        foundation.get("devices"),
        component_ids=component_ids,
        where=f"{where}.devices",
        source=source,
        invalid=invalid,
    )
    signal_mappings = _parse_signal_mappings(
        foundation.get("signal_mappings"),
        component_ids=component_ids,
        devices=devices,
        where=f"{where}.signal_mappings",
        source=source,
        invalid=invalid,
    )
    control_assumptions = _parse_control_assumptions(
        foundation.get("control_assumptions"),
        component_ids=component_ids,
        where=f"{where}.control_assumptions",
        source=source,
        invalid=invalid,
    )

    return FoundationContent(
        topology=topology,
        devices=devices,
        signal_mappings=signal_mappings,
        control_assumptions=control_assumptions,
    )


def render_foundation_content(content: FoundationContent) -> dict[str, Any]:
    """Render the four sections back into the document shape.

    Deterministic and total: all four keys are written in one fixed order, with
    `None` where the Foundation declares none, so a round trip through the
    parser returns an equal record. That is what lets a write prove that what
    it stored is what was validated.
    """
    topology = content.topology
    devices = content.devices
    mappings = content.signal_mappings
    assumptions = content.control_assumptions

    return {
        "topology": (
            None
            if topology is None
            else {
                "nodes": [
                    {
                        "node_id": node.node_id,
                        "component_id": node.component_id,
                        "node_role": node.node_role,
                    }
                    for node in topology.nodes
                ],
                "connections": [
                    {
                        "connection_id": connection.connection_id,
                        "from_node": connection.from_node,
                        "to_node": connection.to_node,
                        "medium": connection.medium,
                    }
                    for connection in topology.connections
                ],
            }
        ),
        "devices": (
            None
            if devices is None
            else [
                {
                    "device_id": device.device_id,
                    "device_type": device.device_type,
                    "display_name": device.display_name,
                    "component_id": device.component_id,
                    "signals": [
                        {
                            "signal_id": signal.signal_id,
                            "display_name": signal.display_name,
                            "unit": signal.unit,
                        }
                        for signal in device.signals
                    ],
                }
                for device in devices
            ]
        ),
        "signal_mappings": (
            None
            if mappings is None
            else [
                {
                    "mapping_id": mapping.mapping_id,
                    "device_id": mapping.device_id,
                    "signal_id": mapping.signal_id,
                    "component_id": mapping.component_id,
                }
                for mapping in mappings
            ]
        ),
        "control_assumptions": (
            None
            if assumptions is None
            else [
                {
                    "assumption_id": assumption.assumption_id,
                    "display_name": assumption.display_name,
                    "component_id": assumption.component_id,
                    "basis": assumption.basis,
                    "statement": assumption.statement,
                }
                for assumption in assumptions
            ]
        ),
    }


# --- Topology ---------------------------------------------------------------


def _parse_topology(
    raw: Any,
    *,
    component_ids: frozenset[str],
    where: str,
    source: str,
    invalid: Invalid,
) -> FoundationTopology | None:
    if raw is None:
        return None

    if not isinstance(raw, Mapping):
        invalid(
            f"'{where}' must be an object declaring nodes and connections, or "
            f"be absent, in {source}. An absent topology is the document "
            "declaring none; it is not a topology with nothing in it."
        )

    _reject_unknown_keys(raw, TOPOLOGY_KEYS, where=where, source=source, invalid=invalid)

    raw_nodes = _require_non_empty_list(
        raw.get("nodes"),
        where=f"{where}.nodes",
        source=source,
        limit=MAX_TOPOLOGY_NODES,
        invalid=invalid,
    )
    nodes = tuple(
        _parse_topology_node(
            entry,
            component_ids=component_ids,
            where=f"{where}.nodes[{index}]",
            source=source,
            invalid=invalid,
        )
        for index, entry in enumerate(raw_nodes)
    )
    _reject_duplicates(
        [node.node_id for node in nodes],
        kind="node_id",
        where=f"{where}.nodes",
        source=source,
        invalid=invalid,
    )

    # One node per component. Two nodes for one component would make the
    # topology ambiguous about where that component sits, and a later diagram
    # would have to pick one.
    _reject_duplicates(
        [node.component_id for node in nodes],
        kind="component_id",
        where=f"{where}.nodes",
        source=source,
        invalid=invalid,
    )

    node_ids = frozenset(node.node_id for node in nodes)

    raw_connections = _require_non_empty_list(
        raw.get("connections"),
        where=f"{where}.connections",
        source=source,
        limit=MAX_CONNECTIONS,
        invalid=invalid,
    )
    connections = tuple(
        _parse_connection(
            entry,
            node_ids=node_ids,
            where=f"{where}.connections[{index}]",
            source=source,
            invalid=invalid,
        )
        for index, entry in enumerate(raw_connections)
    )
    _reject_duplicates(
        [connection.connection_id for connection in connections],
        kind="connection_id",
        where=f"{where}.connections",
        source=source,
        invalid=invalid,
    )

    return FoundationTopology(nodes=nodes, connections=connections)


def _parse_topology_node(
    raw: Any,
    *,
    component_ids: frozenset[str],
    where: str,
    source: str,
    invalid: Invalid,
) -> TopologyNode:
    mapping = _require_mapping(raw, where=where, source=source, invalid=invalid)
    _reject_unknown_keys(
        mapping, TOPOLOGY_NODE_KEYS, where=where, source=source, invalid=invalid
    )

    node_id = _require_identifier(
        mapping, "node_id", where=where, source=source, invalid=invalid
    )
    component_id = _require_component_reference(
        mapping,
        "component_id",
        component_ids=component_ids,
        where=where,
        source=source,
        invalid=invalid,
    )
    node_role = _require_choice(
        mapping,
        "node_role",
        TOPOLOGY_NODE_ROLES,
        where=where,
        source=source,
        invalid=invalid,
    )

    return TopologyNode(
        node_id=node_id, component_id=component_id, node_role=node_role
    )


def _parse_connection(
    raw: Any,
    *,
    node_ids: frozenset[str],
    where: str,
    source: str,
    invalid: Invalid,
) -> TopologyConnection:
    mapping = _require_mapping(raw, where=where, source=source, invalid=invalid)
    _reject_unknown_keys(
        mapping, CONNECTION_KEYS, where=where, source=source, invalid=invalid
    )

    connection_id = _require_identifier(
        mapping, "connection_id", where=where, source=source, invalid=invalid
    )
    from_node = _require_node_reference(
        mapping, "from_node", node_ids=node_ids, where=where, source=source, invalid=invalid
    )
    to_node = _require_node_reference(
        mapping, "to_node", node_ids=node_ids, where=where, source=source, invalid=invalid
    )

    if from_node == to_node:
        invalid(
            f"'{where}' connects {from_node!r} to itself in {source}. A "
            "connection joins two topology nodes."
        )

    medium = _require_choice(
        mapping, "medium", CONNECTION_MEDIA, where=where, source=source, invalid=invalid
    )

    return TopologyConnection(
        connection_id=connection_id,
        from_node=from_node,
        to_node=to_node,
        medium=medium,
    )


# --- Devices and their signals ---------------------------------------------


def _parse_devices(
    raw: Any,
    *,
    component_ids: frozenset[str],
    where: str,
    source: str,
    invalid: Invalid,
) -> tuple[FoundationDevice, ...] | None:
    if raw is None:
        return None

    entries = _require_non_empty_list(
        raw, where=where, source=source, limit=MAX_DEVICES, invalid=invalid
    )
    devices = tuple(
        _parse_device(
            entry,
            component_ids=component_ids,
            where=f"{where}[{index}]",
            source=source,
            invalid=invalid,
        )
        for index, entry in enumerate(entries)
    )
    _reject_duplicates(
        [device.device_id for device in devices],
        kind="device_id",
        where=where,
        source=source,
        invalid=invalid,
    )

    return devices


def _parse_device(
    raw: Any,
    *,
    component_ids: frozenset[str],
    where: str,
    source: str,
    invalid: Invalid,
) -> FoundationDevice:
    mapping = _require_mapping(raw, where=where, source=source, invalid=invalid)
    _reject_unknown_keys(
        mapping, DEVICE_KEYS, where=where, source=source, invalid=invalid
    )

    device_id = _require_identifier(
        mapping, "device_id", where=where, source=source, invalid=invalid
    )
    device_type = _require_choice(
        mapping, "device_type", DEVICE_TYPES, where=where, source=source, invalid=invalid
    )
    display_name = _require_text(
        mapping,
        "display_name",
        max_length=MAX_DISPLAY_NAME_LENGTH,
        where=where,
        source=source,
        invalid=invalid,
    )
    component_id = _require_component_reference(
        mapping,
        "component_id",
        component_ids=component_ids,
        where=where,
        source=source,
        invalid=invalid,
    )

    entries = _require_non_empty_list(
        mapping.get("signals"),
        where=f"{where}.signals",
        source=source,
        limit=MAX_SIGNALS_PER_DEVICE,
        invalid=invalid,
    )
    signals = tuple(
        _parse_signal(
            entry, where=f"{where}.signals[{index}]", source=source, invalid=invalid
        )
        for index, entry in enumerate(entries)
    )
    _reject_duplicates(
        [signal.signal_id for signal in signals],
        kind="signal_id",
        where=f"{where}.signals",
        source=source,
        invalid=invalid,
    )

    return FoundationDevice(
        device_id=device_id,
        device_type=device_type,
        display_name=display_name,
        component_id=component_id,
        signals=signals,
    )


def _parse_signal(
    raw: Any, *, where: str, source: str, invalid: Invalid
) -> DeviceSignal:
    mapping = _require_mapping(raw, where=where, source=source, invalid=invalid)
    _reject_unknown_keys(
        mapping, SIGNAL_KEYS, where=where, source=source, invalid=invalid
    )

    signal_id = _require_identifier(
        mapping, "signal_id", where=where, source=source, invalid=invalid
    )
    display_name = _require_text(
        mapping,
        "display_name",
        max_length=MAX_DISPLAY_NAME_LENGTH,
        where=where,
        source=source,
        invalid=invalid,
    )
    unit = _require_choice(
        mapping, "unit", SIGNAL_UNITS, where=where, source=source, invalid=invalid
    )

    return DeviceSignal(signal_id=signal_id, display_name=display_name, unit=unit)


# --- Device-to-signal mappings ---------------------------------------------


def _parse_signal_mappings(
    raw: Any,
    *,
    component_ids: frozenset[str],
    devices: tuple[FoundationDevice, ...] | None,
    where: str,
    source: str,
    invalid: Invalid,
) -> tuple[SignalMapping, ...] | None:
    if raw is None:
        return None

    if devices is None:
        invalid(
            f"'{where}' is declared in {source} but no device is. A mapping "
            "binds a declared device signal to a declared component, so it "
            "cannot exist without the device that reports it."
        )

    declared_signals = {
        device.device_id: frozenset(signal.signal_id for signal in device.signals)
        for device in devices
    }

    entries = _require_non_empty_list(
        raw, where=where, source=source, limit=MAX_SIGNAL_MAPPINGS, invalid=invalid
    )
    mappings = tuple(
        _parse_signal_mapping(
            entry,
            component_ids=component_ids,
            declared_signals=declared_signals,
            where=f"{where}[{index}]",
            source=source,
            invalid=invalid,
        )
        for index, entry in enumerate(entries)
    )

    _reject_duplicates(
        [mapping.mapping_id for mapping in mappings],
        kind="mapping_id",
        where=where,
        source=source,
        invalid=invalid,
    )

    # One mapping per device signal. Two mappings for one signal would be two
    # answers to what that signal describes, and a later device row would have
    # to choose between them.
    _reject_duplicates(
        [f"{mapping.device_id}/{mapping.signal_id}" for mapping in mappings],
        kind="device signal",
        where=where,
        source=source,
        invalid=invalid,
    )

    return mappings


def _parse_signal_mapping(
    raw: Any,
    *,
    component_ids: frozenset[str],
    declared_signals: Mapping[str, frozenset[str]],
    where: str,
    source: str,
    invalid: Invalid,
) -> SignalMapping:
    mapping = _require_mapping(raw, where=where, source=source, invalid=invalid)
    _reject_unknown_keys(
        mapping, SIGNAL_MAPPING_KEYS, where=where, source=source, invalid=invalid
    )

    mapping_id = _require_identifier(
        mapping, "mapping_id", where=where, source=source, invalid=invalid
    )
    device_id = _require_identifier(
        mapping, "device_id", where=where, source=source, invalid=invalid
    )
    if device_id not in declared_signals:
        invalid(
            f"'{where}.device_id' names {device_id!r} in {source}, which no "
            "device in this foundation declares. A mapping names a declared "
            "device; it never introduces one."
        )

    signal_id = _require_identifier(
        mapping, "signal_id", where=where, source=source, invalid=invalid
    )
    if signal_id not in declared_signals[device_id]:
        invalid(
            f"'{where}.signal_id' names {signal_id!r} in {source}, which the "
            f"device {device_id!r} does not declare. A mapping can only bind a "
            "signal that device is declared to be able to report."
        )

    component_id = _require_component_reference(
        mapping,
        "component_id",
        component_ids=component_ids,
        where=where,
        source=source,
        invalid=invalid,
    )

    return SignalMapping(
        mapping_id=mapping_id,
        device_id=device_id,
        signal_id=signal_id,
        component_id=component_id,
    )


# --- Control assumptions ----------------------------------------------------


def _parse_control_assumptions(
    raw: Any,
    *,
    component_ids: frozenset[str],
    where: str,
    source: str,
    invalid: Invalid,
) -> tuple[ControlAssumption, ...] | None:
    if raw is None:
        return None

    entries = _require_non_empty_list(
        raw, where=where, source=source, limit=MAX_CONTROL_ASSUMPTIONS, invalid=invalid
    )
    assumptions = tuple(
        _parse_control_assumption(
            entry,
            component_ids=component_ids,
            where=f"{where}[{index}]",
            source=source,
            invalid=invalid,
        )
        for index, entry in enumerate(entries)
    )
    _reject_duplicates(
        [assumption.assumption_id for assumption in assumptions],
        kind="assumption_id",
        where=where,
        source=source,
        invalid=invalid,
    )

    return assumptions


def _parse_control_assumption(
    raw: Any,
    *,
    component_ids: frozenset[str],
    where: str,
    source: str,
    invalid: Invalid,
) -> ControlAssumption:
    mapping = _require_mapping(raw, where=where, source=source, invalid=invalid)
    _reject_unknown_keys(
        mapping, CONTROL_ASSUMPTION_KEYS, where=where, source=source, invalid=invalid
    )

    assumption_id = _require_identifier(
        mapping, "assumption_id", where=where, source=source, invalid=invalid
    )
    display_name = _require_text(
        mapping,
        "display_name",
        max_length=MAX_DISPLAY_NAME_LENGTH,
        where=where,
        source=source,
        invalid=invalid,
    )
    basis = _require_choice(
        mapping,
        "basis",
        CONTROL_ASSUMPTION_BASES,
        where=where,
        source=source,
        invalid=invalid,
    )
    statement = _require_text(
        mapping,
        "statement",
        max_length=MAX_STATEMENT_LENGTH,
        where=where,
        source=source,
        invalid=invalid,
    )

    # An assumption about the whole site names no component. `None` is that
    # statement, and the key has to be present to make it: a missing key is a
    # document that forgot, and the two are different.
    if "component_id" not in mapping:
        invalid(
            f"'{where}.component_id' is missing in {source}. An assumption "
            "about one component names it; an assumption about the site "
            "declares null. A missing key says neither."
        )

    component_id: str | None = None
    if mapping["component_id"] is not None:
        component_id = _require_component_reference(
            mapping,
            "component_id",
            component_ids=component_ids,
            where=where,
            source=source,
            invalid=invalid,
        )

    return ControlAssumption(
        assumption_id=assumption_id,
        display_name=display_name,
        component_id=component_id,
        basis=basis,
        statement=statement,
    )


# --- Shared field rules -----------------------------------------------------


def _require_mapping(
    raw: Any, *, where: str, source: str, invalid: Invalid
) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        invalid(f"'{where}' must be an object in {source}")
    return raw


def _require_non_empty_list(
    raw: Any, *, where: str, source: str, limit: int, invalid: Invalid
) -> list[Any]:
    if not isinstance(raw, list) or not raw:
        invalid(
            f"'{where}' must be a non-empty list in {source}. Leave it out "
            "entirely to declare none: an empty list would say this site has "
            "none, which is a different statement."
        )
    if len(raw) > limit:
        invalid(
            f"'{where}' declares {len(raw)} entries in {source}, above the "
            f"limit of {limit}"
        )
    return raw


def _reject_duplicates(
    values: list[str], *, kind: str, where: str, source: str, invalid: Invalid
) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            invalid(f"Duplicate {kind} {value!r} in '{where}' in {source}")
        seen.add(value)


def _reject_unknown_keys(
    mapping: Mapping[str, Any],
    allowed: frozenset[str],
    *,
    where: str,
    source: str,
    invalid: Invalid,
) -> None:
    unknown = sorted(str(key) for key in set(mapping) - allowed)
    if unknown:
        invalid(f"Unknown {where} keys {unknown} in {source}")


def _require_identifier(
    mapping: Mapping[str, Any], key: str, *, where: str, source: str, invalid: Invalid
) -> str:
    value = mapping.get(key)
    if (
        not isinstance(value, str)
        or not value
        or len(value) > MAX_IDENTIFIER_LENGTH
        or not IDENTIFIER_PATTERN.match(value)
    ):
        invalid(
            f"'{where}.{key}' must be lowercase alphanumeric words separated "
            f"by a hyphen in {source}, got {value!r}"
        )
    return value


def _require_component_reference(
    mapping: Mapping[str, Any],
    key: str,
    *,
    component_ids: frozenset[str],
    where: str,
    source: str,
    invalid: Invalid,
) -> str:
    value = _require_identifier(
        mapping, key, where=where, source=source, invalid=invalid
    )
    if value not in component_ids:
        invalid(
            f"'{where}.{key}' names the component {value!r} in {source}, which "
            "this foundation does not declare. The component list is the only "
            "component authority; nothing below it may introduce one."
        )
    return value


def _require_node_reference(
    mapping: Mapping[str, Any],
    key: str,
    *,
    node_ids: frozenset[str],
    where: str,
    source: str,
    invalid: Invalid,
) -> str:
    value = _require_identifier(
        mapping, key, where=where, source=source, invalid=invalid
    )
    if value not in node_ids:
        invalid(
            f"'{where}.{key}' names the topology node {value!r} in {source}, "
            "which this topology does not declare."
        )
    return value


def _require_text(
    mapping: Mapping[str, Any],
    key: str,
    *,
    max_length: int,
    where: str,
    source: str,
    invalid: Invalid,
) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        invalid(f"'{where}.{key}' must be a non-empty string in {source}")
    value = value.strip()
    if len(value) > max_length:
        invalid(
            f"'{where}.{key}' is longer than {max_length} characters in {source}"
        )
    if any(character < " " or character == "\x7f" for character in value):
        invalid(f"'{where}.{key}' contains a control character in {source}")
    return value


def _require_choice(
    mapping: Mapping[str, Any],
    key: str,
    allowed: frozenset[str],
    *,
    where: str,
    source: str,
    invalid: Invalid,
) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or value not in allowed:
        invalid(
            f"'{where}.{key}' must be one of {sorted(allowed)} in {source}, "
            f"got {value!r}"
        )
    return value
