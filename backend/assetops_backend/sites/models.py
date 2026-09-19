"""Domain records for Site configuration templates and for Sites.

Two identity spaces live here and they never merge. A template has
`template_id` and `template_version`, no `site_id`, no lifecycle status, no
location, and no place-bound timezone; it cannot be listed as a Site, targeted
by a scenario, simulated, or receive evidence. A Site has `site_id` and nothing
else is its identity - not its display name, not the template it came from, and
not the shell it was created in.

Neither record type is a base, mode, or parameterization of the other, and the
Site records below repeat rather than reuse the template component shape,
because a Site's Foundation is a copy taken at creation time.

The Foundation content on both is component truth declared by a document. It is
not evidence: that a template or a Site declares a 100 kW PV array is not a
claim that any array exists, is commissioned, or has ever reported a
measurement.
"""

from __future__ import annotations

from dataclasses import dataclass

# The M1 Site types. A template declares which kind of Site it would produce;
# that is a statement about the archetype, not about any Site.
SITE_TYPES = frozenset({"MINIGRID", "COLDCHAIN"})

# Component archetypes a template may declare. Strict and closed: an
# unsupported component type is a configuration error, not a passthrough
# string, because later slices bind topology, devices, and signal mappings to
# these values.
COMPONENT_TYPES = frozenset(
    {
        "PV_ARRAY",
        "INVERTER",
        "BATTERY",
        "POWER_CONVERSION_SYSTEM",
        "GENERATOR",
        "FUEL_TANK",
        "AC_BUS",
        "LOAD",
        "COLD_ROOM",
        "METER",
    }
)

# Units a declared design rating may use. Also closed, for the same reason:
# a canonical unit vocabulary is what later telemetry mapping is checked
# against.
RATING_UNITS = frozenset({"kW", "kWh", "kVA", "V", "A", "Hz", "L"})

# --- Foundation content below the component list ----------------------------
#
# T014 adds topology, devices, signal availability, device-to-signal mappings,
# and control assumptions to what a Foundation may declare. Everything here is
# shared between a template's Foundation and a Site's Foundation, in the same
# way `Rating` already is: these are leaf value types, and a Site's copy is
# free to diverge in its VALUES without either Foundation growing a mode.
#
# Two vocabularies this slice deliberately does NOT settle, because the T016
# user-review checkpoint owns them:
#
#   - whether a breaker is a device, component state, or both, and what the
#     control state vocabulary is. `ControlAssumption` below therefore carries
#     a declared statement and its basis, not a control model.
#   - how cold-room process symbols relate to mini-grid electrical topology.
#     `TOPOLOGY_NODE_ROLES` carries only the electrical positions the shipped
#     hybrid mini-grid template needs to parse.

# Where a component sits in the site's electrical topology. Closed, because a
# later SLD archetype binds against these and an unrecognised role would be a
# node nothing could draw.
#
# This is topology position, not component identity: `component_type` remains
# the canonical vocabulary for what a component IS, and no component carries a
# second role axis.
#
# `GENERATION` rather than `SOURCE` deliberately. `source` already means where
# a Site's evidence comes from, and a topology role sharing that word would put
# two unrelated meanings of it on one screen.
TOPOLOGY_NODE_ROLES = frozenset(
    {
        "GENERATION",
        "CONVERSION",
        "STORAGE",
        "BUS",
        "METERING",
        "LOAD",
        "FUEL_STORAGE",
    }
)

# What flows along a connection. Closed for the same reason: a connection whose
# medium is not understood cannot be drawn or simulated, so it is a
# configuration error rather than a passthrough string.
CONNECTION_MEDIA = frozenset({"AC", "DC", "FUEL"})

# What kind of thing a declared device is. Deliberately small: only what the
# shipped hybrid mini-grid template needs. A device here is a configured asset,
# never an operating one - nothing in this record says a device exists, has
# been commissioned, or has ever reported.
DEVICE_TYPES = frozenset({"METER", "SENSOR", "CONTROLLER"})

# Units a declared signal may carry. Closed, and separate from `RATING_UNITS`:
# a nameplate rating and a reportable signal are different kinds of fact, and
# collapsing their vocabularies would let a rating unit onto a signal.
SIGNAL_UNITS = frozenset({"kW", "kWh", "V", "Hz", "L", "degC", "W/m2", "%"})

# Where a declared control assumption comes from. Provenance about the
# assumption, not a control vocabulary: `TEMPLATE` is an assumption the
# archetype declared and the site copied, `SITE` is one declared for this site.
CONTROL_ASSUMPTION_BASES = frozenset({"TEMPLATE", "SITE"})


@dataclass(frozen=True)
class Rating:
    """A declared design rating for a template component.

    This is nameplate intent from the shipped document, never a measurement.
    """

    value: float
    unit: str


@dataclass(frozen=True)
class TopologyNode:
    """One position in the site's electrical topology.

    A node is not a component: it is the place a declared component occupies in
    the topology. `component_id` must name a component the same Foundation
    declares, which is what keeps the topology from becoming a second component
    authority.
    """

    node_id: str
    component_id: str
    node_role: str


@dataclass(frozen=True)
class TopologyConnection:
    """One declared connection between two topology nodes.

    Directed from `from_node` to `to_node`, and both must name nodes the same
    topology declares. The direction is the declared flow direction in the
    document; it is not a measurement and nothing here says anything is
    flowing.
    """

    connection_id: str
    from_node: str
    to_node: str
    medium: str


@dataclass(frozen=True)
class FoundationTopology:
    """The declared topology: what the nodes are and how they connect."""

    nodes: tuple[TopologyNode, ...]
    connections: tuple[TopologyConnection, ...]


@dataclass(frozen=True)
class DeviceSignal:
    """One signal a declared device is configured to be able to report.

    Signal AVAILABILITY, not a reading. That a device declares a `kW` signal is
    not a claim that any value has ever arrived, and this record has nowhere to
    put one.

    `signal_id` is unique within its device only. Two devices may both declare
    `ac-power`, and a mapping names the device and the signal together.
    """

    signal_id: str
    display_name: str
    unit: str


@dataclass(frozen=True)
class FoundationDevice:
    """One device the Foundation declares, and the signals it can report.

    `component_id` is the component the device is attached to, and it must name
    a component the same Foundation declares. A device is configured
    configuration: it is awaiting runtime and evidence, and nothing here states
    that it is reporting or that it is not.
    """

    device_id: str
    device_type: str
    display_name: str
    component_id: str
    signals: tuple[DeviceSignal, ...]


@dataclass(frozen=True)
class SignalMapping:
    """A declared binding from one device signal to the component it describes.

    This is the canonical device-to-signal fact. It is never inferred from a
    display name, a topology position, a protocol label, a simulator fixture
    name, or mockup text: if the document does not declare it, the product does
    not know it.

    The device it names must be declared, the signal must be one that device
    declares, and the component must be one the Foundation declares. A device
    attached to one component may map a signal to another - a site meter
    attached to the bus reporting the distribution load's consumption is the
    case this exists for.
    """

    mapping_id: str
    device_id: str
    signal_id: str
    component_id: str


@dataclass(frozen=True)
class ControlAssumption:
    """One declared assumption about how this site is expected to be operated.

    Deliberately not a control model. It carries an identity, what the
    assumption is about, where the assumption came from, and the assumption in
    words. It declares no control state, no setpoint, no mode, and no breaker
    position, because whether a breaker is a device, component state, or both
    is a product decision this slice does not make.

    `component_id` is `None` when the assumption is about the site rather than
    one component. Absent and `None` are the same fact here and both are
    written as `None`.
    """

    assumption_id: str
    display_name: str
    component_id: str | None
    basis: str
    statement: str


@dataclass(frozen=True)
class FoundationContent:
    """The four Foundation sections below the component list.

    Each is `None` when the document does not declare that section. `None` is the
    document being silent; there is no empty collection, because an empty list
    would let a screen state that a site has no devices when what is true is
    that its Foundation does not declare any.
    """

    topology: FoundationTopology | None = None
    devices: tuple[FoundationDevice, ...] | None = None
    signal_mappings: tuple[SignalMapping, ...] | None = None
    control_assumptions: tuple[ControlAssumption, ...] | None = None


@dataclass(frozen=True)
class TemplateComponent:
    """A component archetype a template declares.

    `component_id` is unique within the template only. It is not a device
    identity, not a signal identity, and not a Site identity.
    """

    component_id: str
    component_type: str
    display_name: str
    rating: Rating | None


@dataclass(frozen=True)
class TemplateFoundation:
    """The Foundation content a template would produce.

    T005 declared the archetype and its components. T014 adds the four sections
    below them, and each is `None` when the template document does not declare
    it: a template that declares no devices seeds a Site that declares no
    devices, and neither states that the site has none.
    """

    site_type: str
    summary: str
    components: tuple[TemplateComponent, ...]
    topology: FoundationTopology | None = None
    devices: tuple[FoundationDevice, ...] | None = None
    signal_mappings: tuple[SignalMapping, ...] | None = None
    control_assumptions: tuple[ControlAssumption, ...] | None = None


@dataclass(frozen=True)
class SiteTemplate:
    """A shipped, read-only Site configuration template.

    `template_version` exists so that later drift between a template and the
    Sites derived from it stays inspectable. It is not a Site Foundation
    version and it is not Site identity.
    """

    template_id: str
    template_version: int
    display_name: str
    foundation: TemplateFoundation


# --- Site records ----------------------------------------------------------
#
# A Site is not a template and a template is not a Site. The two live in
# separate identity spaces and, below, in separate record types with no shared
# base class: `SiteComponent` deliberately repeats the field list of
# `TemplateComponent` rather than reusing it, because a Site's Foundation is a
# COPY taken at creation time and must be able to diverge from the template it
# came from without either type having to grow a mode or a flag.

# Where a Site is in its own life as a site. This project's extension: it is
# not source mode, not configuration origin, not evidence readiness, and not
# source health, and none of those may be derived from it or it from them.
LIFECYCLE_STATUSES = frozenset(
    {"PLANNED", "COMMISSIONED", "ACTIVE", "DECOMMISSIONED", "ARCHIVED"}
)

# Where this Site's configuration DOCUMENT came from: did the product ship it
# read-only, or did a user author it into the writable store?
CONFIGURATION_ORIGINS = frozenset({"SHIPPED", "USER"})

# Where this Site's EVIDENCE comes from. `SIMULATED` is provenance, never
# status, health, or an assessment. In M1 every `USER`-origin Site also has
# `SIMULATED` because the Lab is the only creation path; that is a coincidence
# of circumstance and must never become a derivation in either direction.
SOURCE_MODES = frozenset({"LIVE", "SIMULATED"})


@dataclass(frozen=True)
class SiteLocation:
    """Where a Site is, as identity-level configuration.

    Free text supplied by a user. It is never Site identity, never a lookup
    key, never a filename, and never part of a route.
    """

    country: str
    locality: str


@dataclass(frozen=True)
class SiteSource:
    """Provenance about where this Site's evidence comes from."""

    mode: str


@dataclass(frozen=True)
class SiteTemplateProvenance:
    """Which template a Site was instantiated from, recorded as provenance.

    Provenance only. `template_id` never becomes `site_id`, is never used for
    lookup, routing, or a filename, and a later change to the template never
    reaches back into a Site that was created from it.
    """

    template_id: str
    template_version: int


@dataclass(frozen=True)
class SiteComponent:
    """A component this Site's Foundation declares.

    Component truth copied from a template at creation time. It is not
    evidence: nothing here claims a device exists or has ever reported.
    """

    component_id: str
    component_type: str
    display_name: str
    rating: Rating | None


@dataclass(frozen=True)
class SiteFoundation:
    """The versioned, time-valid Foundation content of a Site.

    The version, the start of the validity interval, and the component seed
    copied from the template, plus the four sections T014 adds: topology,
    devices, device-to-signal mappings, and control assumptions.

    Each of the four is `None` when this Site's Foundation document declares
    none, and `None` is the only way to say that. There is no empty collection,
    because an empty list is a screen's licence to state that this site has no
    devices, and what the document supports is narrower: it declares none.
    """

    version: int
    valid_from: str
    summary: str
    components: tuple[SiteComponent, ...]
    topology: FoundationTopology | None = None
    devices: tuple[FoundationDevice, ...] | None = None
    signal_mappings: tuple[SignalMapping, ...] | None = None
    control_assumptions: tuple[ControlAssumption, ...] | None = None


@dataclass(frozen=True)
class SiteRecord:
    """One configured Site.

    `site_id` is the only Site identity. Display name, location, and template
    provenance are not identity, and neither is the shell that created it.

    The six provenance-and-status concepts stay separate on this record:
    `origin` is about the document, `source.mode` is about the evidence,
    `lifecycle_status` is about the site's own life. Integration readiness,
    evidence availability, and source health are derived later and have no
    field here, because nothing in this slice can source them truthfully.
    """

    site_id: str
    display_name: str
    site_type: str
    location: SiteLocation
    timezone: str
    lifecycle_status: str
    origin: str
    source: SiteSource
    template: SiteTemplateProvenance | None
    foundation: SiteFoundation
