"""Foundation revision content, digests and configuration gaps (S1-01).

The immutable `foundation_revision.content` is the source document's
`foundation` section exactly as the strict Site document parser renders it,
less the two fields the revision row owns as columns (`version`,
`valid_from`). Rebuilding a `SiteRecord` from a row therefore goes back
through the same strict parser that validated the import, so a stored
revision can never present a shape the legacy reader would refuse.

Configuration gaps are configuration facts only: what the Foundation and its
registrations do not declare. They are not observed source health and not
analytic readiness; binding completeness is reported separately (S1-02).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence
from zoneinfo import available_timezones

from assetops_backend.sites.foundation_records import Registrations, RevisionRow, StoredSite
from assetops_backend.sites.identity import validate_site_id
from assetops_backend.sites.models import SiteRecord
from assetops_backend.sites.ports import SiteConfigurationInvalid
from assetops_backend.sites.site_parsing import parse_site_document, render_site_document

CONTENT_SCHEMA_VERSION = 1

RESERVE_ASSET_TYPE = "BATTERY"
RESERVE_PROPERTY_KEY = "reserve-state-of-charge"
RESERVE_UNIT = "%"

#: The physical roles a MINIGRID Foundation must declare with a typed rating.
REQUIRED_MINIGRID_COMPONENTS: tuple[tuple[str, str], ...] = (
    ("GENERATOR", "generator"),
    ("PV_ARRAY", "PV array"),
    ("BATTERY", "battery"),
    ("POWER_CONVERSION_SYSTEM", "battery power conversion system"),
    ("FUEL_TANK", "fuel tank"),
    ("AC_BUS", "AC bus"),
    ("LOAD", "declared load"),
)
REQUIRED_SITE_CONTROLS = ("source-priority", "critical-load-priority")

#: Gap codes `configuration_gaps` derives from CURRENT mutable rows - the Site
#: row and the gateway/source registrations - rather than from the immutable
#: Foundation revision. A pinned historical snapshot is validated against its
#: own stored identity instead, so these are reported beside it, never used to
#: withdraw it (D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary). They
#: still refuse a current acquisition snapshot.
CURRENT_ROW_GAP_CODES = frozenset(
    {
        "SITE_CODE_INVALID",
        "SITE_NAME_MISSING",
        "SITE_TYPE_UNSUPPORTED",
        "SITE_TIMEZONE_INVALID",
        "GATEWAY_NOT_REGISTERED",
        "SOURCE_NOT_REGISTERED",
    }
)


def utc_text(instant: datetime) -> str:
    """The UTC instant spelling the Site document uses (`...Z`, whole seconds)."""
    return instant.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_utc_text(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def content_from_record(record: SiteRecord) -> dict[str, Any]:
    foundation = dict(render_site_document(record)["foundation"])
    foundation.pop("version")
    foundation.pop("valid_from")
    return foundation


def content_digest(content: Mapping[str, Any]) -> str:
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def site_document(site: StoredSite, revision: RevisionRow) -> dict[str, Any]:
    return {
        "site_id": site.site_code,
        "display_name": site.name,
        "site_type": site.site_type,
        "location": {"country": site.country, "locality": site.locality},
        "timezone": site.timezone,
        "lifecycle_status": site.lifecycle,
        "origin": site.origin,
        "source": {"mode": site.proposed_source_mode},
        "template": (
            None
            if site.template_id is None
            else {"template_id": site.template_id, "template_version": site.template_version}
        ),
        "foundation": {
            "version": revision.version,
            "valid_from": utc_text(revision.valid_from),
            **revision.content,
        },
    }


def record_at(site: StoredSite, revision: RevisionRow) -> SiteRecord:
    """The Site as configured by one stored revision, via the strict parser."""
    return parse_site_document(
        site_document(site, revision),
        source=f"foundation revision {revision.id} (v{revision.version})",
    )


def battery_reserve(content: Mapping[str, Any]) -> dict[str, Any] | None:
    for component in content.get("components") or ():
        if component.get("component_type") != RESERVE_ASSET_TYPE:
            continue
        for item in component.get("properties") or ():
            if item.get("property_key") == RESERVE_PROPERTY_KEY:
                return {"asset_code": component["component_id"], **item}
    return None


def with_battery_reserve(
    content: Mapping[str, Any], *, asset_code: str, value: float, source_version: int
) -> dict[str, Any]:
    """A copy of `content` whose battery reserve is `value` %.

    The caller re-validates the result through the strict parser, so the unit
    and range rule is the one typed-property rule the import already used.
    """
    updated = json.loads(json.dumps(content))
    for component in updated.get("components") or ():
        if component.get("component_id") != asset_code:
            continue
        if component.get("component_type") != RESERVE_ASSET_TYPE:
            raise SiteConfigurationInvalid(
                f"Component {asset_code!r} is not a battery; only the battery reserve "
                "state of charge can be published in this release."
            )
        properties = list(component.get("properties") or [])
        replacement = {
            "property_key": RESERVE_PROPERTY_KEY,
            "value": value,
            "unit": RESERVE_UNIT,
            "source": "SITE",
            "source_version": source_version,
        }
        for index, item in enumerate(properties):
            if item.get("property_key") == RESERVE_PROPERTY_KEY:
                properties[index] = replacement
                break
        else:
            properties.append(replacement)
        component["properties"] = properties
        return updated
    raise SiteConfigurationInvalid(
        f"This Site's Foundation declares no component {asset_code!r}."
    )


def with_component_properties(
    content: Mapping[str, Any], *, asset_code: str, properties: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """A copy of `content` with each property set on one component.

    Each item carries `property_key`, `value`, `unit`, `source` and
    `source_version`; an existing property of the same key is replaced in
    place. The caller re-validates the result through the strict parser.
    """
    updated = json.loads(json.dumps(content))
    for component in updated.get("components") or ():
        if component.get("component_id") != asset_code:
            continue
        current = list(component.get("properties") or [])
        for item in properties:
            replacement = {
                key: item[key] for key in ("property_key", "value", "unit", "source", "source_version")
            }
            for index, existing in enumerate(current):
                if existing.get("property_key") == replacement["property_key"]:
                    current[index] = replacement
                    break
            else:
                current.append(replacement)
        component["properties"] = current
        return updated
    raise SiteConfigurationInvalid(
        f"This Site's Foundation declares no component {asset_code!r}."
    )


# --- configuration gaps ------------------------------------------------------


@dataclass(frozen=True)
class ConfigurationGap:
    code: str
    subject: str
    message: str

    def to_wire(self) -> dict[str, str]:
        return {"code": self.code, "subject": self.subject, "message": self.message}


def configuration_gaps(
    site: StoredSite,
    revision: RevisionRow | None,
    registrations: Registrations,
) -> list[ConfigurationGap]:
    gaps: list[ConfigurationGap] = []

    def gap(code: str, subject: str, message: str) -> None:
        gaps.append(ConfigurationGap(code, subject, message))

    try:
        validate_site_id(site.site_code)
    except SiteConfigurationInvalid as error:
        gap("SITE_CODE_INVALID", "site", str(error))
    if not site.name.strip():
        gap("SITE_NAME_MISSING", "site", "The Site has no name.")
    if site.site_type != "MINIGRID":
        gap("SITE_TYPE_UNSUPPORTED", "site", f"Site type {site.site_type!r} is not MINIGRID.")
    if site.timezone not in available_timezones():
        gap("SITE_TIMEZONE_INVALID", "site", f"{site.timezone!r} is not an IANA time zone.")

    if revision is None:
        gap("NO_EFFECTIVE_REVISION", "foundation", "No Foundation revision is effective at this time.")
        return gaps

    content = revision.content
    components = list(content.get("components") or ())
    by_id = {c["component_id"]: c for c in components}
    for component_type, label in REQUIRED_MINIGRID_COMPONENTS:
        typed = [c for c in components if c.get("component_type") == component_type]
        if not typed:
            gap("COMPONENT_MISSING", component_type, f"No {label} component is declared.")
        for component in typed:
            if component.get("rating") is None:
                gap(
                    "COMPONENT_RATING_MISSING",
                    component["component_id"],
                    f"{component.get('display_name') or component['component_id']} declares no rating.",
                )

    topology = content.get("topology")
    bus_nodes: set[str] = set()
    if topology is None:
        gap("TOPOLOGY_MISSING", "topology", "The Foundation declares no topology.")
    else:
        nodes = {n["node_id"]: n for n in topology.get("nodes") or ()}
        adjacency: dict[str, set[str]] = {node_id: set() for node_id in nodes}
        for node in nodes.values():
            if node.get("component_id") not in by_id:
                gap(
                    "TOPOLOGY_REFERENCE_BROKEN",
                    node["node_id"],
                    f"Topology node {node['node_id']!r} names no component of this Site.",
                )
            elif by_id[node["component_id"]].get("component_type") == "AC_BUS":
                bus_nodes.add(node["node_id"])
        for connection in topology.get("connections") or ():
            ends = (connection.get("from_node"), connection.get("to_node"))
            if any(end not in nodes for end in ends):
                gap(
                    "TOPOLOGY_REFERENCE_BROKEN",
                    connection.get("connection_id", "connection"),
                    f"Connection {connection.get('connection_id')!r} names a node outside this Site.",
                )
                continue
            adjacency[ends[0]].add(ends[1])
            adjacency[ends[1]].add(ends[0])
        reached: set[str] = set(bus_nodes)
        frontier = list(bus_nodes)
        while frontier:
            for neighbour in adjacency[frontier.pop()]:
                if neighbour not in reached:
                    reached.add(neighbour)
                    frontier.append(neighbour)
        if not bus_nodes:
            gap("AC_BUS_PATH_MISSING", "topology", "No topology node is an AC bus.")
        else:
            for node_id in sorted(set(nodes) - reached):
                gap("AC_BUS_PATH_MISSING", node_id, f"Node {node_id!r} has no path to the AC bus.")

    if battery_reserve(content) is None:
        gap(
            "BATTERY_RESERVE_MISSING",
            "battery",
            "The battery declares no reserve state of charge.",
        )
    controls = {c.get("control_key") for c in content.get("site_controls") or ()}
    for key in REQUIRED_SITE_CONTROLS:
        if key not in controls:
            gap("SITE_CONTROL_MISSING", key, f"The Site Control {key!r} is not declared.")

    registered = {source.source_external_id for source in registrations.sources}
    if not registrations.gateways:
        gap("GATEWAY_NOT_REGISTERED", "gateway", "No gateway is registered for this Site.")
    for device in content.get("devices") or ():
        if device["device_id"] not in registered:
            gap(
                "SOURCE_NOT_REGISTERED",
                device["device_id"],
                f"Device {device['device_id']!r} has no registered source.",
            )
    return gaps
