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


@dataclass(frozen=True)
class Rating:
    """A declared design rating for a template component.

    This is nameplate intent from the shipped document, never a measurement.
    """

    value: float
    unit: str


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

    T005 declares the archetype and its components. Topology connections,
    devices, signal mappings, and control assumptions belong to causal step 4
    and are deliberately absent rather than stubbed.
    """

    site_type: str
    summary: str
    components: tuple[TemplateComponent, ...]


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

    M1 carries the version, the start of the validity interval, and the
    component seed copied from the template. Topology connections, devices,
    signal mappings, and control assumptions are causal step 4 and are absent
    rather than stubbed.
    """

    version: int
    valid_from: str
    summary: str
    components: tuple[SiteComponent, ...]


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
