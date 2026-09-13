"""Domain records for shipped Site configuration templates.

A template is not a Site. These records deliberately carry no `site_id`, no
lifecycle status, no location, and no timezone: a template lives in its own
identity space (`template_id`, `template_version`), cannot be listed as a Site,
targeted by a scenario, simulated, or receive evidence.

The Foundation content here is component truth declared by a shipped document.
It is not evidence: that a template declares a 100 kW PV array is not a claim
that any array exists, is commissioned, or has ever reported a measurement.
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
