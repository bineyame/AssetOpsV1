"""The one strict parser for shipped Site template documents.

There is no lenient path and no second parser. The same function validates the
shipped catalog today and any other template document a later slice meets, so
a document cannot be trusted more because of where it came from.

This module takes an already-loaded `Mapping` and returns domain records. It
therefore needs no exemption from the storage-technology guard in
`tools/check-architecture.ps1`: it never opens, reads, decodes, or locates
anything. If it ever needs `yaml`, `pathlib`, or a file handle, its signature
is wrong.

Two refusals carry product meaning rather than hygiene. A document declaring
`site_id` or `lifecycle_status` is refused by name, because that is a template
claiming to be a Site, and letting it through would merge template identity and
Site identity into one namespace. Everything else - unknown keys, unsupported
values, duplicate component identities, oversized documents, over-cardinality
collections - is refused because untrusted or defective configuration must fail
loudly rather than be normalized into a half-understood Site.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, NoReturn

from assetops_backend.sites.document_bounds import DocumentLimits, reject_oversized
from assetops_backend.sites.foundation_parsing import (
    FOUNDATION_CONTENT_KEYS,
    parse_foundation_content,
)
from assetops_backend.sites.models import (
    COMPONENT_TYPES,
    RATING_UNITS,
    SITE_TYPES,
    Rating,
    SiteTemplate,
    TemplateComponent,
    TemplateFoundation,
)
from assetops_backend.sites.ports import SiteTemplateConfigurationInvalid

# Fields that would make a template a Site. Refused by name so the message says
# what is actually wrong rather than "unknown key".
SITE_ONLY_FIELDS = ("site_id", "lifecycle_status", "location", "timezone")

TEMPLATE_KEYS = frozenset(
    {"template_id", "template_version", "display_name", "foundation"}
)
# The component list plus the four sections `foundation_parsing` validates.
# Extended from one place so a key this parser allows and the Site parser does
# not cannot exist: a template whose Foundation the Site store would refuse is
# a template that seeds an unreadable Site.
FOUNDATION_KEYS = (
    frozenset({"site_type", "summary", "components"}) | FOUNDATION_CONTENT_KEYS
)
COMPONENT_KEYS = frozenset({"component_id", "component_type", "display_name", "rating"})
RATING_KEYS = frozenset({"value", "unit"})

# Bounds. A pathological document is refused rather than accepted: without
# these, one shipped or later user-authored file can exhaust memory or fill a
# screen with ten thousand rows.
MAX_DOCUMENT_NODES = 2_000
MAX_DOCUMENT_TEXT_LENGTH = 64_000
MAX_NESTING_DEPTH = 8
MAX_COMPONENTS = 64
MAX_IDENTIFIER_LENGTH = 64
MAX_DISPLAY_NAME_LENGTH = 120
MAX_SUMMARY_LENGTH = 600
MAX_TEMPLATE_VERSION = 10_000

IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _invalid(message: str) -> NoReturn:
    raise SiteTemplateConfigurationInvalid(message)


def parse_site_template(document: Mapping[str, Any], *, source: str) -> SiteTemplate:
    """Validate one already-loaded template document into a domain record.

    Args:
        document: the loaded mapping. Never a path, handle, or YAML string.
        source: a human-readable name for the document, used in messages only.

    Raises:
        SiteTemplateConfigurationInvalid: the document is not a valid template.
    """
    if not isinstance(document, Mapping):
        raise SiteTemplateConfigurationInvalid(
            f"Template document must be a mapping in {source}"
        )

    _reject_oversized(document, source=source)

    nested_foundation = _as_mapping(document.get("foundation"), default={})
    for field in SITE_ONLY_FIELDS:
        if field in document or field in nested_foundation:
            raise SiteTemplateConfigurationInvalid(
                f"Template document in {source} declares {field!r}. A template "
                "is not a Site: it has no Site identity, lifecycle status, "
                "location, or place-bound timezone."
            )

    _reject_unknown_keys(document, TEMPLATE_KEYS, where="template", source=source)

    template_id = _require_identifier(document, "template_id", source=source)
    template_version = _require_version(document, source=source)
    display_name = _require_text(
        document,
        "display_name",
        max_length=MAX_DISPLAY_NAME_LENGTH,
        source=source,
    )

    if "foundation" not in document:
        raise SiteTemplateConfigurationInvalid(
            f"Template document in {source} is missing 'foundation'"
        )

    foundation = _parse_foundation(document["foundation"], source=source)

    return SiteTemplate(
        template_id=template_id,
        template_version=template_version,
        display_name=display_name,
        foundation=foundation,
    )


def _parse_foundation(raw: Any, *, source: str) -> TemplateFoundation:
    foundation = _as_mapping(raw, default=None)
    if foundation is None:
        raise SiteTemplateConfigurationInvalid(
            f"'foundation' must be a mapping in {source}"
        )

    _reject_unknown_keys(foundation, FOUNDATION_KEYS, where="foundation", source=source)

    site_type = _require_choice(
        foundation, "site_type", SITE_TYPES, where="foundation", source=source
    )
    summary = _require_text(
        foundation,
        "summary",
        max_length=MAX_SUMMARY_LENGTH,
        where="foundation",
        source=source,
    )

    raw_components = foundation.get("components")
    if not isinstance(raw_components, list) or not raw_components:
        raise SiteTemplateConfigurationInvalid(
            f"'foundation.components' must be a non-empty list in {source}"
        )
    if len(raw_components) > MAX_COMPONENTS:
        raise SiteTemplateConfigurationInvalid(
            f"'foundation.components' declares {len(raw_components)} components "
            f"in {source}, above the limit of {MAX_COMPONENTS}"
        )

    components = tuple(
        _parse_component(entry, index=index, source=source)
        for index, entry in enumerate(raw_components)
    )

    seen: set[str] = set()
    for component in components:
        if component.component_id in seen:
            raise SiteTemplateConfigurationInvalid(
                f"Duplicate 'component_id' {component.component_id!r} in {source}"
            )
        seen.add(component.component_id)

    content = parse_foundation_content(
        foundation,
        component_ids=frozenset(seen),
        where="foundation",
        source=source,
        invalid=_invalid,
    )

    return TemplateFoundation(
        site_type=site_type,
        summary=summary,
        components=components,
        topology=content.topology,
        devices=content.devices,
        signal_mappings=content.signal_mappings,
        control_assumptions=content.control_assumptions,
    )


def _parse_component(raw: Any, *, index: int, source: str) -> TemplateComponent:
    where = f"foundation.components[{index}]"
    component = _as_mapping(raw, default=None)
    if component is None:
        raise SiteTemplateConfigurationInvalid(
            f"'{where}' must be a mapping in {source}"
        )

    _reject_unknown_keys(component, COMPONENT_KEYS, where=where, source=source)

    component_id = _require_identifier(
        component, "component_id", where=where, source=source
    )
    component_type = _require_choice(
        component, "component_type", COMPONENT_TYPES, where=where, source=source
    )
    display_name = _require_text(
        component,
        "display_name",
        max_length=MAX_DISPLAY_NAME_LENGTH,
        where=where,
        source=source,
    )

    rating: Rating | None = None
    if component.get("rating") is not None:
        rating = _parse_rating(component["rating"], where=where, source=source)

    return TemplateComponent(
        component_id=component_id,
        component_type=component_type,
        display_name=display_name,
        rating=rating,
    )


def _parse_rating(raw: Any, *, where: str, source: str) -> Rating:
    rating = _as_mapping(raw, default=None)
    if rating is None:
        raise SiteTemplateConfigurationInvalid(
            f"'{where}.rating' must be a mapping in {source}"
        )

    _reject_unknown_keys(rating, RATING_KEYS, where=f"{where}.rating", source=source)

    value = rating.get("value")
    # `isinstance(True, int)` is True, so booleans must be excluded explicitly.
    if type(value) not in (int, float):
        raise SiteTemplateConfigurationInvalid(
            f"'{where}.rating.value' must be a number in {source}"
        )
    if value <= 0:
        raise SiteTemplateConfigurationInvalid(
            f"'{where}.rating.value' must be greater than zero in {source}"
        )

    unit = _require_choice(
        rating, "unit", RATING_UNITS, where=f"{where}.rating", source=source
    )

    return Rating(value=float(value), unit=unit)


def _as_mapping(value: Any, *, default: Any) -> Any:
    return value if isinstance(value, Mapping) else default


def _reject_unknown_keys(
    mapping: Mapping[str, Any],
    allowed: frozenset[str],
    *,
    where: str,
    source: str,
) -> None:
    unknown = sorted(str(key) for key in set(mapping) - allowed)
    if unknown:
        raise SiteTemplateConfigurationInvalid(
            f"Unknown {where} keys {unknown} in {source}"
        )


def _require_identifier(
    mapping: Mapping[str, Any],
    key: str,
    *,
    where: str = "template",
    source: str,
) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise SiteTemplateConfigurationInvalid(
            f"'{where}.{key}' must be a non-empty string in {source}"
        )
    if len(value) > MAX_IDENTIFIER_LENGTH:
        raise SiteTemplateConfigurationInvalid(
            f"'{where}.{key}' is longer than {MAX_IDENTIFIER_LENGTH} characters "
            f"in {source}"
        )
    if not IDENTIFIER_PATTERN.match(value):
        raise SiteTemplateConfigurationInvalid(
            f"'{where}.{key}' must be lowercase alphanumeric words separated by "
            f"a hyphen in {source}, got {value!r}"
        )
    return value


def _require_text(
    mapping: Mapping[str, Any],
    key: str,
    *,
    max_length: int,
    where: str = "template",
    source: str,
) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SiteTemplateConfigurationInvalid(
            f"'{where}.{key}' must be a non-empty string in {source}"
        )
    if len(value) > max_length:
        raise SiteTemplateConfigurationInvalid(
            f"'{where}.{key}' is longer than {max_length} characters in {source}"
        )
    return value.strip()


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
        raise SiteTemplateConfigurationInvalid(
            f"'{where}.{key}' must be one of {sorted(allowed)} in {source}, "
            f"got {value!r}"
        )
    return value


def _require_version(mapping: Mapping[str, Any], *, source: str) -> int:
    value = mapping.get("template_version")
    if type(value) is not int:
        raise SiteTemplateConfigurationInvalid(
            f"'template.template_version' must be an integer in {source}"
        )
    if not 1 <= value <= MAX_TEMPLATE_VERSION:
        raise SiteTemplateConfigurationInvalid(
            f"'template.template_version' must be between 1 and "
            f"{MAX_TEMPLATE_VERSION} in {source}"
        )
    return value


def _reject_oversized(document: Any, *, source: str) -> None:
    """Bound node count, total text length, and nesting before validating.

    Walking first means a pathological document is refused before any
    field-level work is done on it. The walk itself is shared with the Site
    parser, so both document families are bounded by one implementation.
    """

    def invalid(message: str) -> NoReturn:
        raise SiteTemplateConfigurationInvalid(message)

    reject_oversized(
        document,
        source=source,
        limits=DocumentLimits(
            max_nodes=MAX_DOCUMENT_NODES,
            max_text_length=MAX_DOCUMENT_TEXT_LENGTH,
            max_nesting_depth=MAX_NESTING_DEPTH,
        ),
        invalid=invalid,
        document_kind="Template document",
    )
