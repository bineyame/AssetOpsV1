"""The one strict parser for Site documents, in both stores.

There is no lenient path, no user mode, and no second parser. A user-authored
document is untrusted input and crosses exactly the same function as a shipped
one, because a document must not be trusted more for where it came from. The
fully materialized document is what is validated - not the request that
proposed it, and not a partially built record - so the thing that is written is
the thing that was checked.

This module takes an already-loaded `Mapping` and returns domain records, and
renders a record back into the same mapping shape. It never opens, reads,
decodes, or locates anything: serializing that mapping to bytes is an adapter's
job, and if this module ever needs `yaml`, `pathlib`, or a file handle then its
signature is wrong.

Refusal messages here are product copy. A user meets them in the create flow,
so each one names what is wrong and what would be acceptable instead.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, NoReturn

from assetops_backend.document_bounds import DocumentLimits, reject_oversized
from assetops_backend.sites.foundation_parsing import (
    FOUNDATION_CONTENT_KEYS,
    parse_foundation_content,
    render_foundation_content,
)
from assetops_backend.sites.identity import validate_site_id
from assetops_backend.sites.models import (
    COMPONENT_TYPES,
    CONFIGURATION_ORIGINS,
    LIFECYCLE_STATUSES,
    RATING_UNITS,
    SITE_TYPES,
    SOURCE_MODES,
    FoundationContent,
    Rating,
    SiteComponent,
    SiteFoundation,
    SiteLocation,
    SiteRecord,
    SiteSource,
    SiteTemplateProvenance,
)
from assetops_backend.sites.ports import SiteConfigurationInvalid

SITE_KEYS = frozenset(
    {
        "site_id",
        "display_name",
        "site_type",
        "location",
        "timezone",
        "lifecycle_status",
        "origin",
        "source",
        "template",
        "foundation",
    }
)
LOCATION_KEYS = frozenset({"country", "locality"})
SOURCE_KEYS = frozenset({"mode"})
TEMPLATE_KEYS = frozenset({"template_id", "template_version"})
# The T008 metadata and component list, plus the four sections
# `foundation_parsing` validates. Extended from the same constant the template
# parser extends, so the two document families cannot diverge into one store
# accepting a Foundation the other refuses.
FOUNDATION_KEYS = (
    frozenset({"version", "valid_from", "summary", "components"})
    | FOUNDATION_CONTENT_KEYS
)
COMPONENT_KEYS = frozenset({"component_id", "component_type", "display_name", "rating"})
RATING_KEYS = frozenset({"value", "unit"})

# Bounds. Without these one document can exhaust memory or fill the Sites
# index with rows nobody can scroll past, and an index that cannot be opened
# is worse than a create that was refused.
SITE_DOCUMENT_LIMITS = DocumentLimits(
    max_nodes=2_000,
    max_text_length=64_000,
    max_nesting_depth=8,
)
MAX_COMPONENTS = 64
MAX_DISPLAY_NAME_LENGTH = 120
MAX_SUMMARY_LENGTH = 600
MAX_LOCATION_FIELD_LENGTH = 120
MAX_TIMEZONE_LENGTH = 64
MAX_TEMPLATE_ID_LENGTH = 64
MAX_TEMPLATE_VERSION = 10_000
MAX_FOUNDATION_VERSION = 10_000

TEMPLATE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
COMPONENT_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# An IANA zone name, by shape: `Area/Location`, optionally `Area/Group/Place`.
# The shape is checked rather than membership of the tz database, because the
# database is an optional platform package on Windows and Site identity must
# not depend on which host validated the document.
TIMEZONE_PATTERN = re.compile(
    r"^[A-Za-z][A-Za-z0-9_+-]*(?:/[A-Za-z0-9][A-Za-z0-9_+-]*){1,2}$"
)

# An ISO-8601 instant in UTC. The Foundation validity interval is a product
# fact, so it has one spelling rather than whatever a writer happened to emit.
VALID_FROM_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

FREE_TEXT_RULE = (
    "Use plain text without control characters; it is stored and shown as "
    "text and is never an identifier, a file name, or part of an address."
)


@dataclass(frozen=True)
class CreateSiteRequest:
    """The identity-level fields a user supplies when creating a Site.

    Deliberately not a Site: it has no origin, no source mode, no lifecycle
    status, no template provenance, and no Foundation. Those are the service's
    to decide and the template's to seed, and a request object that carried
    them would let a caller choose its own provenance.
    """

    template_id: str
    site_id: str
    display_name: str
    country: str
    locality: str
    timezone: str


def _invalid(message: str) -> NoReturn:
    raise SiteConfigurationInvalid(message)


def parse_site_document(document: Mapping[str, Any], *, source: str) -> SiteRecord:
    """Validate one already-loaded Site document into a domain record.

    Args:
        document: the loaded mapping. Never a path, handle, or YAML string.
        source: a human-readable name for the document, used in messages only.

    Raises:
        SiteConfigurationInvalid: the document is not a valid Site.
    """
    if not isinstance(document, Mapping):
        raise SiteConfigurationInvalid(f"Site document must be a mapping in {source}")

    reject_oversized(
        document,
        source=source,
        limits=SITE_DOCUMENT_LIMITS,
        invalid=_invalid,
        document_kind="Site document",
    )

    _reject_unknown_keys(document, SITE_KEYS, where="site", source=source)

    site_id = validate_site_id(document.get("site_id"), where=f"'site.site_id' in {source}")
    display_name = _require_free_text(
        document,
        "display_name",
        max_length=MAX_DISPLAY_NAME_LENGTH,
        where="site",
        source=source,
    )
    site_type = _require_choice(
        document, "site_type", SITE_TYPES, where="site", source=source
    )
    lifecycle_status = _require_choice(
        document, "lifecycle_status", LIFECYCLE_STATUSES, where="site", source=source
    )
    origin = _require_choice(
        document, "origin", CONFIGURATION_ORIGINS, where="site", source=source
    )
    timezone = _require_timezone(document, source=source)
    location = _parse_location(document.get("location"), source=source)
    site_source = _parse_source(document.get("source"), source=source)
    template = _parse_template_provenance(document.get("template"), source=source)
    foundation = _parse_foundation(document.get("foundation"), source=source)

    return SiteRecord(
        site_id=site_id,
        display_name=display_name,
        site_type=site_type,
        location=location,
        timezone=timezone,
        lifecycle_status=lifecycle_status,
        origin=origin,
        source=site_source,
        template=template,
        foundation=foundation,
    )


def render_site_document(record: SiteRecord) -> dict[str, Any]:
    """Render a Site record back into the document shape the parser accepts.

    Deterministic and total: every field the parser requires is written, in one
    fixed order, with no store-specific detail. An adapter serializes this; a
    round trip through the parser must return an equal record, which is what
    lets a write prove that what it stored is what was validated.
    """
    return {
        "site_id": record.site_id,
        "display_name": record.display_name,
        "site_type": record.site_type,
        "location": {
            "country": record.location.country,
            "locality": record.location.locality,
        },
        "timezone": record.timezone,
        "lifecycle_status": record.lifecycle_status,
        "origin": record.origin,
        "source": {"mode": record.source.mode},
        "template": (
            None
            if record.template is None
            else {
                "template_id": record.template.template_id,
                "template_version": record.template.template_version,
            }
        ),
        "foundation": {
            "version": record.foundation.version,
            "valid_from": record.foundation.valid_from,
            "summary": record.foundation.summary,
            "components": [
                {
                    "component_id": component.component_id,
                    "component_type": component.component_type,
                    "display_name": component.display_name,
                    "rating": (
                        None
                        if component.rating is None
                        else {
                            "value": component.rating.value,
                            "unit": component.rating.unit,
                        }
                    ),
                }
                for component in record.foundation.components
            ],
            # The four sections T014 adds, written unconditionally with `None`
            # where the foundation declares none. Total rather than
            # conditional, so a round trip returns an equal record whether the
            # document declared them or not.
            **render_foundation_content(
                FoundationContent(
                    topology=record.foundation.topology,
                    devices=record.foundation.devices,
                    signal_mappings=record.foundation.signal_mappings,
                    control_assumptions=record.foundation.control_assumptions,
                )
            ),
        },
    }


def parse_create_site_request(request: Any) -> CreateSiteRequest:
    """Validate an untrusted create request into identity-level fields.

    This is not the document validation. It refuses a malformed request early
    with copy a user can act on; the materialized document is still validated
    in full by `parse_site_document` before anything is written.
    """
    if not isinstance(request, Mapping):
        raise SiteConfigurationInvalid(
            "The create request must be an object with the fields the create "
            "form supplies."
        )

    reject_oversized(
        request,
        source="the create request",
        limits=SITE_DOCUMENT_LIMITS,
        invalid=_invalid,
        document_kind="Create request",
    )

    allowed = frozenset(
        {"template_id", "site_id", "display_name", "location", "timezone"}
    )
    _reject_unknown_keys(request, allowed, where="request", source="the create request")

    template_id = _require_template_id(request, source="the create request")
    site_id = validate_site_id(request.get("site_id"), where="Site ID")
    display_name = _require_free_text(
        request,
        "display_name",
        max_length=MAX_DISPLAY_NAME_LENGTH,
        where="request",
        source="the create request",
        label="Display name",
    )
    location = _parse_location(
        request.get("location"),
        source="the create request",
        label_prefix="Location ",
    )
    timezone = _require_timezone(request, source="the create request", label="Timezone")

    return CreateSiteRequest(
        template_id=template_id,
        site_id=site_id,
        display_name=display_name,
        country=location.country,
        locality=location.locality,
        timezone=timezone,
    )


def _parse_location(
    raw: Any, *, source: str, label_prefix: str | None = None
) -> SiteLocation:
    if not isinstance(raw, Mapping):
        raise SiteConfigurationInvalid(
            f"'site.location' must be an object with a country and a locality "
            f"in {source}"
        )

    _reject_unknown_keys(raw, LOCATION_KEYS, where="site.location", source=source)

    country = _require_free_text(
        raw,
        "country",
        max_length=MAX_LOCATION_FIELD_LENGTH,
        where="site.location",
        source=source,
        label=None if label_prefix is None else f"{label_prefix}country",
    )
    locality = _require_free_text(
        raw,
        "locality",
        max_length=MAX_LOCATION_FIELD_LENGTH,
        where="site.location",
        source=source,
        label=None if label_prefix is None else f"{label_prefix}locality",
    )

    return SiteLocation(country=country, locality=locality)


def _parse_source(raw: Any, *, source: str) -> SiteSource:
    if not isinstance(raw, Mapping):
        raise SiteConfigurationInvalid(
            f"'site.source' must be an object declaring a mode in {source}"
        )

    _reject_unknown_keys(raw, SOURCE_KEYS, where="site.source", source=source)
    mode = _require_choice(
        raw, "mode", SOURCE_MODES, where="site.source", source=source
    )

    return SiteSource(mode=mode)


def _parse_template_provenance(
    raw: Any, *, source: str
) -> SiteTemplateProvenance | None:
    # Absent or null is meaningful: a Site that came from no template has no
    # template provenance, and inventing one would be a false claim about
    # where its Foundation came from.
    if raw is None:
        return None

    if not isinstance(raw, Mapping):
        raise SiteConfigurationInvalid(
            f"'site.template' must be an object or absent in {source}"
        )

    _reject_unknown_keys(raw, TEMPLATE_KEYS, where="site.template", source=source)

    template_id = _require_template_id(raw, source=source, where="site.template")
    version = raw.get("template_version")
    if type(version) is not int or not 1 <= version <= MAX_TEMPLATE_VERSION:
        raise SiteConfigurationInvalid(
            f"'site.template.template_version' must be an integer between 1 "
            f"and {MAX_TEMPLATE_VERSION} in {source}"
        )

    return SiteTemplateProvenance(template_id=template_id, template_version=version)


def _parse_foundation(raw: Any, *, source: str) -> SiteFoundation:
    if not isinstance(raw, Mapping):
        raise SiteConfigurationInvalid(
            f"'site.foundation' must be an object in {source}"
        )

    _reject_unknown_keys(raw, FOUNDATION_KEYS, where="site.foundation", source=source)

    version = raw.get("version")
    if type(version) is not int or not 1 <= version <= MAX_FOUNDATION_VERSION:
        raise SiteConfigurationInvalid(
            f"'site.foundation.version' must be an integer between 1 and "
            f"{MAX_FOUNDATION_VERSION} in {source}"
        )

    valid_from = raw.get("valid_from")
    if not isinstance(valid_from, str) or not VALID_FROM_PATTERN.match(valid_from):
        raise SiteConfigurationInvalid(
            f"'site.foundation.valid_from' must be a UTC instant such as "
            f"2026-01-01T00:00:00Z in {source}"
        )

    summary = _require_free_text(
        raw,
        "summary",
        max_length=MAX_SUMMARY_LENGTH,
        where="site.foundation",
        source=source,
    )

    components = raw.get("components")
    if not isinstance(components, list) or not components:
        raise SiteConfigurationInvalid(
            f"'site.foundation.components' must be a non-empty list in {source}"
        )
    if len(components) > MAX_COMPONENTS:
        raise SiteConfigurationInvalid(
            f"'site.foundation.components' declares {len(components)} components "
            f"in {source}, above the limit of {MAX_COMPONENTS}"
        )

    parsed = tuple(
        _parse_component(entry, index=index, source=source)
        for index, entry in enumerate(components)
    )

    seen: set[str] = set()
    for component in parsed:
        if component.component_id in seen:
            raise SiteConfigurationInvalid(
                f"Duplicate 'component_id' {component.component_id!r} in {source}"
            )
        seen.add(component.component_id)

    content = parse_foundation_content(
        raw,
        component_ids=frozenset(seen),
        where="site.foundation",
        source=source,
        invalid=_invalid,
    )

    return SiteFoundation(
        version=version,
        valid_from=valid_from,
        summary=summary,
        components=parsed,
        topology=content.topology,
        devices=content.devices,
        signal_mappings=content.signal_mappings,
        control_assumptions=content.control_assumptions,
    )


def _parse_component(raw: Any, *, index: int, source: str) -> SiteComponent:
    where = f"site.foundation.components[{index}]"
    if not isinstance(raw, Mapping):
        raise SiteConfigurationInvalid(f"'{where}' must be an object in {source}")

    _reject_unknown_keys(raw, COMPONENT_KEYS, where=where, source=source)

    component_id = raw.get("component_id")
    if (
        not isinstance(component_id, str)
        or len(component_id) > MAX_TEMPLATE_ID_LENGTH
        or not COMPONENT_ID_PATTERN.match(component_id)
    ):
        raise SiteConfigurationInvalid(
            f"'{where}.component_id' must be lowercase alphanumeric words "
            f"separated by a hyphen in {source}, got {component_id!r}"
        )

    component_type = _require_choice(
        raw, "component_type", COMPONENT_TYPES, where=where, source=source
    )
    display_name = _require_free_text(
        raw,
        "display_name",
        max_length=MAX_DISPLAY_NAME_LENGTH,
        where=where,
        source=source,
    )

    rating: Rating | None = None
    if raw.get("rating") is not None:
        rating = _parse_rating(raw["rating"], where=where, source=source)

    return SiteComponent(
        component_id=component_id,
        component_type=component_type,
        display_name=display_name,
        rating=rating,
    )


def _parse_rating(raw: Any, *, where: str, source: str) -> Rating:
    if not isinstance(raw, Mapping):
        raise SiteConfigurationInvalid(
            f"'{where}.rating' must be an object in {source}"
        )

    _reject_unknown_keys(raw, RATING_KEYS, where=f"{where}.rating", source=source)

    value = raw.get("value")
    # `isinstance(True, int)` is True, so booleans are excluded by type.
    if type(value) not in (int, float) or value <= 0:
        raise SiteConfigurationInvalid(
            f"'{where}.rating.value' must be a number greater than zero in {source}"
        )

    unit = _require_choice(
        raw, "unit", RATING_UNITS, where=f"{where}.rating", source=source
    )

    return Rating(value=float(value), unit=unit)


def _require_template_id(
    mapping: Mapping[str, Any], *, source: str, where: str = "request"
) -> str:
    value = mapping.get("template_id")
    if (
        not isinstance(value, str)
        or not value
        or len(value) > MAX_TEMPLATE_ID_LENGTH
        or not TEMPLATE_ID_PATTERN.match(value)
    ):
        raise SiteConfigurationInvalid(
            f"'{where}.template_id' must name a shipped template as lowercase "
            f"alphanumeric words separated by a hyphen in {source}, got "
            f"{value!r}"
        )
    return value


def _require_timezone(
    mapping: Mapping[str, Any], *, source: str, label: str = "'site.timezone'"
) -> str:
    value = mapping.get("timezone")
    if not isinstance(value, str) or not value.strip():
        raise SiteConfigurationInvalid(
            f"{label} is required in {source}. Use an IANA time zone name such "
            "as Africa/Kampala."
        )
    value = value.strip()
    if len(value) > MAX_TIMEZONE_LENGTH or not TIMEZONE_PATTERN.match(value):
        raise SiteConfigurationInvalid(
            f"{label} {value!r} is not an IANA time zone name in {source}. Use "
            "a name such as Africa/Kampala."
        )
    return value


def _require_free_text(
    mapping: Mapping[str, Any],
    key: str,
    *,
    max_length: int,
    where: str,
    source: str,
    label: str | None = None,
) -> str:
    name = label or f"'{where}.{key}'"
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SiteConfigurationInvalid(
            f"{name} is required in {source}. {FREE_TEXT_RULE}"
        )
    value = value.strip()
    if len(value) > max_length:
        raise SiteConfigurationInvalid(
            f"{name} is longer than {max_length} characters in {source}. "
            f"{FREE_TEXT_RULE}"
        )
    if any(character < " " or character == "\x7f" for character in value):
        raise SiteConfigurationInvalid(
            f"{name} contains a control character in {source}. {FREE_TEXT_RULE}"
        )
    return value


def _require_choice(
    mapping: Mapping[str, Any],
    key: str,
    allowed: frozenset[str],
    *,
    where: str,
    source: str,
) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or value not in allowed:
        raise SiteConfigurationInvalid(
            f"'{where}.{key}' must be one of {sorted(allowed)} in {source}, "
            f"got {value!r}"
        )
    return value


def _reject_unknown_keys(
    mapping: Mapping[str, Any],
    allowed: frozenset[str],
    *,
    where: str,
    source: str,
) -> None:
    unknown = sorted(str(key) for key in set(mapping) - allowed)
    if unknown:
        raise SiteConfigurationInvalid(
            f"Unknown {where} keys {unknown} in {source}"
        )
