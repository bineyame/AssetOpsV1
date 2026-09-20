"""The one strict parser for ScenarioDefinition documents, in both stores.

There is no lenient path, no shipped mode, and no second parser. A shipped
definition and a user-authored one cross exactly the same function, because a
document must not be trusted more for where it came from - the shipped Fuel
Loss Event is validated on every read by the same rules a user document meets.

This module takes an already-loaded `Mapping` and returns domain records. It
never opens, reads, decodes, or locates anything: if it ever needs `yaml`,
`pathlib`, or a file handle, its signature is wrong, and
`tools/check-architecture.ps1` fails the build if it acquires one.

## What this parser refuses, and what it deliberately does not

It refuses unknown keys, unsupported taxonomy values, malformed version fields,
duplicate timeline identities, malformed ordering and offset values, misplaced
private expectation fields, malformed target-site declarations, and a
target-site policy whose shape does not match the policy it declares.

It does **not** decide whether a declared target `site_id` names a Site that
exists. That is resolved by `ScenarioDetailService` against the `SiteRepository`
port and reported as a target-resolution state for the screen. The separation is
load-bearing in both directions: a shipped scenario naming a Site nobody has
configured must still be readable on a fresh checkout, and a scenario that
became unreadable because somebody removed a Site would take the catalog down
with it. So this module validates the *shape* of the declaration and nothing
else, and it never reaches into Site storage.

The one thing it borrows from the Site domain is the rule for what a `site_id`
looks like, because two answers to that would let a scenario declare a target
no Site could ever have. The Site error that rule raises is translated into
this package's vocabulary at the point of use, so no Site exception escapes
through the scenario port.

## Origin is not declared

`origin` is supplied by the store, not read from the document. A user-authored
scenario that could write `origin: SHIPPED` into its own file would be claiming
provenance it does not have.

Refusal messages here are product copy. A developer authoring a scenario meets
them, so each one names what is wrong and what would be acceptable instead.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, NoReturn

from assetops_backend.document_bounds import DocumentLimits, reject_oversized
from assetops_backend.scenarios.identity import validate_scenario_id
from assetops_backend.scenarios.models import (
    EVENT_CATEGORIES,
    EXPECTATION_KINDS,
    PARAMETER_UNITS,
    SCENARIO_ORIGINS,
    TARGET_SITE_POLICIES,
    TIMELINE_ENTRY_KINDS,
    PrivateExpectation,
    ScenarioDefinition,
    ScenarioParameter,
    ScenarioTargetSite,
    ScenarioVersion,
    TimelineEntry,
)
from assetops_backend.scenarios.ports import ScenarioConfigurationInvalid
from assetops_backend.sites.identity import validate_site_id
from assetops_backend.sites.ports import SiteConfigurationInvalid

SCENARIO_KEYS = frozenset(
    {
        "scenario_id",
        "display_name",
        "purpose",
        "version",
        "target_site",
        "timeline",
        "public_parameters",
        "private_expectations",
    }
)
VERSION_KEYS = frozenset(
    {"scenario_version", "version_valid_from", "supersedes"}
)
TARGET_SITE_KEYS = frozenset({"policy", "site_id", "template_id", "requirement"})
TIMELINE_ENTRY_KEYS = frozenset(
    {
        "event_id",
        "sequence",
        "offset_minutes",
        "entry_kind",
        "category",
        "description",
        "parameters",
    }
)
PARAMETER_KEYS = frozenset({"parameter_id", "display_name", "value", "unit"})
EXPECTATION_KEYS = frozenset(
    {"expectation_id", "display_name", "oracle_kind", "statement"}
)

#: Keys that name private test-oracle metadata. They are legal inside the
#: `private_expectations` section and nowhere else, and meeting one in a public
#: section is reported as a boundary violation rather than as a generic unknown
#: key: the author has put an expectation where authoring data goes, and the
#: refusal should say so.
#:
#: `expected_*` and `assert*` are included by prefix below rather than by name,
#: because the ways to spell an oracle field are open-ended and the ones worth
#: catching are the ones an author would reach for.
PRIVATE_EXPECTATION_KEYS = frozenset(
    {
        "private_expectations",
        "expectation_id",
        "expectation",
        "expectations",
        "oracle_kind",
        "oracle",
        "test_oracle",
    }
)
PRIVATE_EXPECTATION_KEY_PREFIXES = ("expected", "assert")

# Bounds. Without these one document can exhaust memory or fill the timeline
# with rows nobody can scroll past, and a catalog that cannot be opened is
# worse than a definition that was refused.
SCENARIO_DOCUMENT_LIMITS = DocumentLimits(
    max_nodes=4_000,
    max_text_length=80_000,
    max_nesting_depth=8,
)
MAX_TIMELINE_ENTRIES = 200
MAX_PARAMETERS_PER_ENTRY = 16
MAX_PUBLIC_PARAMETERS = 64
MAX_PRIVATE_EXPECTATIONS = 32
MAX_DISPLAY_NAME_LENGTH = 120
MAX_DESCRIPTION_LENGTH = 400
MAX_PURPOSE_LENGTH = 800
MAX_REQUIREMENT_LENGTH = 600
MAX_STATEMENT_LENGTH = 600
MAX_PARAMETER_TEXT_LENGTH = 120
MAX_SCENARIO_VERSION = 10_000
MAX_SEQUENCE = 10_000

#: The simulated interval a scenario describes is bounded. Ten thousand minutes
#: is a week of simulated time; an offset beyond it is a typo rather than an
#: intention, and a timeline a screen cannot present in order is not a timeline.
MAX_OFFSET_MINUTES = 10_000

MAX_TEMPLATE_ID_LENGTH = 64
IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

#: An ISO-8601 instant in UTC, spelled the one way the Site Foundation spells
#: its own validity instant. A version's validity is a product fact, so it has
#: one spelling rather than whatever a writer happened to emit.
VERSION_VALID_FROM_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
)

FREE_TEXT_RULE = (
    "Use plain text without control characters; it is stored and shown as "
    "text and is never an identifier, a file name, or part of an address."
)


def _invalid(message: str) -> NoReturn:
    raise ScenarioConfigurationInvalid(message)


def parse_scenario_document(
    document: Mapping[str, Any], *, source: str, origin: str
) -> ScenarioDefinition:
    """Validate one already-loaded scenario document into a domain record.

    Args:
        document: the loaded mapping. Never a path, handle, or YAML string.
        source: a human-readable name for the document, used in messages only.
        origin: which store this document came from. Supplied by the adapter,
            never read from the document.

    Raises:
        ScenarioConfigurationInvalid: the document is not a valid scenario.
    """
    if origin not in SCENARIO_ORIGINS:
        raise ScenarioConfigurationInvalid(
            f"Scenario origin must be one of {sorted(SCENARIO_ORIGINS)}, got "
            f"{origin!r}. Origin is supplied by the store that read the "
            "document, not declared by the document."
        )

    if not isinstance(document, Mapping):
        raise ScenarioConfigurationInvalid(
            f"Scenario document must be a mapping in {source}"
        )

    reject_oversized(
        document,
        source=source,
        limits=SCENARIO_DOCUMENT_LIMITS,
        invalid=_invalid,
        document_kind="Scenario document",
    )

    _reject_unknown_keys(document, SCENARIO_KEYS, where="scenario", source=source)

    scenario_id = validate_scenario_id(
        document.get("scenario_id"), where=f"'scenario.scenario_id' in {source}"
    )
    display_name = _require_free_text(
        document,
        "display_name",
        max_length=MAX_DISPLAY_NAME_LENGTH,
        where="scenario",
        source=source,
    )
    purpose = _require_free_text(
        document,
        "purpose",
        max_length=MAX_PURPOSE_LENGTH,
        where="scenario",
        source=source,
    )

    version = _parse_version(document.get("version"), source=source)
    target_site = _parse_target_site(document.get("target_site"), source=source)
    timeline = _parse_timeline(document.get("timeline"), source=source)
    public_parameters = _parse_public_parameters(
        document.get("public_parameters"), source=source
    )
    private_expectations = _parse_private_expectations(
        document.get("private_expectations"), source=source
    )

    return ScenarioDefinition(
        scenario_id=scenario_id,
        display_name=display_name,
        purpose=purpose,
        origin=origin,
        version=version,
        target_site=target_site,
        timeline=timeline,
        public_parameters=public_parameters,
        private_expectations=private_expectations,
    )


def _parse_version(raw: Any, *, source: str) -> ScenarioVersion:
    """The provisional versioning fields, validated strictly.

    Provisional is about which fields the project should carry, not about how
    carefully they are checked. A malformed version is refused here, because a
    run that later freezes a version must freeze something well formed.
    """
    if not isinstance(raw, Mapping):
        raise ScenarioConfigurationInvalid(
            f"'scenario.version' must be an object declaring "
            f"{sorted(VERSION_KEYS)} in {source}"
        )

    _reject_unknown_keys(raw, VERSION_KEYS, where="scenario.version", source=source)

    scenario_version = raw.get("scenario_version")
    # `isinstance(True, int)` is True, so compare the type directly: a boolean
    # must not become version 1.
    if (
        type(scenario_version) is not int
        or not 1 <= scenario_version <= MAX_SCENARIO_VERSION
    ):
        raise ScenarioConfigurationInvalid(
            f"'scenario.version.scenario_version' must be an integer between 1 "
            f"and {MAX_SCENARIO_VERSION} in {source}, got "
            f"{scenario_version!r}. Scenario identity and scenario version are "
            "distinct: the identity never changes and the version is what a "
            "future run freezes."
        )

    valid_from = raw.get("version_valid_from")
    if not isinstance(valid_from, str) or not VERSION_VALID_FROM_PATTERN.match(
        valid_from
    ):
        raise ScenarioConfigurationInvalid(
            f"'scenario.version.version_valid_from' must be a UTC instant such "
            f"as 2026-01-01T00:00:00Z in {source}, got {valid_from!r}"
        )

    supersedes = raw.get("supersedes")
    if supersedes is not None:
        if (
            type(supersedes) is not int
            or not 1 <= supersedes < scenario_version
        ):
            raise ScenarioConfigurationInvalid(
                f"'scenario.version.supersedes' must be null, or an integer "
                f"between 1 and {scenario_version - 1}, in {source}, got "
                f"{supersedes!r}. A version supersedes an earlier version of "
                "the same scenario; it cannot supersede itself or a version "
                "that does not exist yet."
            )

    return ScenarioVersion(
        scenario_version=scenario_version,
        version_valid_from=valid_from,
        supersedes=supersedes,
    )


def _parse_target_site(raw: Any, *, source: str) -> ScenarioTargetSite:
    """The target-site declaration: shape only, never a lookup.

    Both halves are refused here. A malformed declaration is one whose fields
    are the wrong type or absent. An invalid policy shape is one whose fields
    do not match the policy it declares - a `DECLARED_SITE` with no `site_id`,
    or a `TEMPLATE_DERIVED` that names one anyway. The second is the one worth
    naming separately: it is a document that looks complete and means two
    contradictory things.
    """
    if not isinstance(raw, Mapping):
        raise ScenarioConfigurationInvalid(
            f"'scenario.target_site' must be an object declaring which site "
            f"this scenario needs, in {source}"
        )

    _reject_unknown_keys(
        raw, TARGET_SITE_KEYS, where="scenario.target_site", source=source
    )

    policy = _require_choice(
        raw,
        "policy",
        TARGET_SITE_POLICIES,
        where="scenario.target_site",
        source=source,
    )
    requirement = _require_free_text(
        raw,
        "requirement",
        max_length=MAX_REQUIREMENT_LENGTH,
        where="scenario.target_site",
        source=source,
    )

    declared_site = raw.get("site_id")
    declared_template = raw.get("template_id")

    if policy == "DECLARED_SITE":
        if declared_template is not None:
            raise ScenarioConfigurationInvalid(
                f"'scenario.target_site' declares policy DECLARED_SITE and a "
                f"template_id in {source}. A declared-site target names the "
                "site it needs; a template is how a site would be built, which "
                "is the other policy."
            )
        try:
            site_id = validate_site_id(
                declared_site, where=f"'scenario.target_site.site_id' in {source}"
            )
        except SiteConfigurationInvalid as error:
            # Translated at the boundary. The site identity rule is the Site
            # domain's, and this parser borrows it rather than keeping a second
            # answer, but a Site exception must not escape through the
            # scenario port.
            raise ScenarioConfigurationInvalid(
                f"{error} A declared-site target must name the site it needs."
            ) from error

        return ScenarioTargetSite(
            policy=policy,
            site_id=site_id,
            template_id=None,
            requirement=requirement,
        )

    if declared_site is not None:
        raise ScenarioConfigurationInvalid(
            f"'scenario.target_site' declares policy TEMPLATE_DERIVED and a "
            f"site_id in {source}. A template-derived target has no site yet: "
            "the site would be created from the template, and naming one here "
            "would be two answers to which site the scenario runs against."
        )

    if (
        not isinstance(declared_template, str)
        or not declared_template
        or len(declared_template) > MAX_TEMPLATE_ID_LENGTH
        or not IDENTIFIER_PATTERN.match(declared_template)
    ):
        raise ScenarioConfigurationInvalid(
            f"'scenario.target_site.template_id' must name a site template as "
            f"lowercase alphanumeric words separated by a hyphen in {source}, "
            f"got {declared_template!r}"
        )

    return ScenarioTargetSite(
        policy=policy,
        site_id=None,
        template_id=declared_template,
        requirement=requirement,
    )


def _parse_timeline(raw: Any, *, source: str) -> tuple[TimelineEntry, ...]:
    if not isinstance(raw, list) or not raw:
        raise ScenarioConfigurationInvalid(
            f"'scenario.timeline' must be a non-empty list in {source}. A "
            "scenario with no authored timeline describes nothing happening."
        )
    if len(raw) > MAX_TIMELINE_ENTRIES:
        raise ScenarioConfigurationInvalid(
            f"'scenario.timeline' declares {len(raw)} entries in {source}, "
            f"above the limit of {MAX_TIMELINE_ENTRIES}"
        )

    entries = tuple(
        _parse_timeline_entry(entry, index=index, source=source)
        for index, entry in enumerate(raw)
    )

    seen: set[str] = set()
    previous_sequence = 0
    for entry in entries:
        if entry.event_id in seen:
            raise ScenarioConfigurationInvalid(
                f"Duplicate timeline 'event_id' {entry.event_id!r} in {source}. "
                "A timeline identity is unique within a scenario version and "
                "stable for the life of that version, because a future run "
                "refers to one by that address."
            )
        seen.add(entry.event_id)

        if entry.sequence <= previous_sequence:
            raise ScenarioConfigurationInvalid(
                f"Timeline 'sequence' {entry.sequence} for "
                f"{entry.event_id!r} in {source} does not follow the previous "
                f"entry's {previous_sequence}. The authored order is the order "
                "the document lists, and sequence numbers increase along it."
            )
        previous_sequence = entry.sequence

    return entries


def _parse_timeline_entry(raw: Any, *, index: int, source: str) -> TimelineEntry:
    where = f"scenario.timeline[{index}]"
    if not isinstance(raw, Mapping):
        raise ScenarioConfigurationInvalid(
            f"'{where}' must be an object in {source}"
        )

    _reject_unknown_keys(raw, TIMELINE_ENTRY_KEYS, where=where, source=source)

    event_id = raw.get("event_id")
    if (
        not isinstance(event_id, str)
        or len(event_id) > MAX_TEMPLATE_ID_LENGTH
        or not IDENTIFIER_PATTERN.match(event_id)
    ):
        raise ScenarioConfigurationInvalid(
            f"'{where}.event_id' must be lowercase alphanumeric words "
            f"separated by a hyphen in {source}, got {event_id!r}"
        )

    sequence = raw.get("sequence")
    if type(sequence) is not int or not 1 <= sequence <= MAX_SEQUENCE:
        raise ScenarioConfigurationInvalid(
            f"'{where}.sequence' must be an integer between 1 and "
            f"{MAX_SEQUENCE} in {source}, got {sequence!r}"
        )

    offset = raw.get("offset_minutes")
    if type(offset) is not int or not 0 <= offset <= MAX_OFFSET_MINUTES:
        raise ScenarioConfigurationInvalid(
            f"'{where}.offset_minutes' must be an integer between 0 and "
            f"{MAX_OFFSET_MINUTES} in {source}, got {offset!r}. An offset is "
            "measured from the start of the simulated interval; a scenario "
            "does not know when that interval is, because choosing it is run "
            "setup."
        )

    entry_kind = _require_choice(
        raw, "entry_kind", TIMELINE_ENTRY_KINDS, where=where, source=source
    )
    category = _require_choice(
        raw, "category", EVENT_CATEGORIES, where=where, source=source
    )
    description = _require_free_text(
        raw,
        "description",
        max_length=MAX_DESCRIPTION_LENGTH,
        where=where,
        source=source,
    )

    parameters = _parse_parameters(
        raw.get("parameters"),
        where=f"{where}.parameters",
        source=source,
        maximum=MAX_PARAMETERS_PER_ENTRY,
        required=False,
    )

    return TimelineEntry(
        event_id=event_id,
        sequence=sequence,
        offset_minutes=offset,
        entry_kind=entry_kind,
        category=category,
        description=description,
        parameters=parameters,
    )


def _parse_public_parameters(
    raw: Any, *, source: str
) -> tuple[ScenarioParameter, ...]:
    return _parse_parameters(
        raw,
        where="scenario.public_parameters",
        source=source,
        maximum=MAX_PUBLIC_PARAMETERS,
        required=False,
    )


def _parse_parameters(
    raw: Any, *, where: str, source: str, maximum: int, required: bool
) -> tuple[ScenarioParameter, ...]:
    if raw is None and not required:
        return ()

    if not isinstance(raw, list):
        raise ScenarioConfigurationInvalid(
            f"'{where}' must be a list of parameters, or absent, in {source}"
        )
    if len(raw) > maximum:
        raise ScenarioConfigurationInvalid(
            f"'{where}' declares {len(raw)} parameters in {source}, above the "
            f"limit of {maximum}"
        )

    parsed = tuple(
        _parse_parameter(entry, where=f"{where}[{index}]", source=source)
        for index, entry in enumerate(raw)
    )

    seen: set[str] = set()
    for parameter in parsed:
        if parameter.parameter_id in seen:
            raise ScenarioConfigurationInvalid(
                f"Duplicate 'parameter_id' {parameter.parameter_id!r} in "
                f"'{where}' in {source}"
            )
        seen.add(parameter.parameter_id)

    return parsed


def _parse_parameter(raw: Any, *, where: str, source: str) -> ScenarioParameter:
    if not isinstance(raw, Mapping):
        raise ScenarioConfigurationInvalid(
            f"'{where}' must be an object in {source}"
        )

    _reject_unknown_keys(raw, PARAMETER_KEYS, where=where, source=source)

    parameter_id = raw.get("parameter_id")
    if (
        not isinstance(parameter_id, str)
        or len(parameter_id) > MAX_TEMPLATE_ID_LENGTH
        or not IDENTIFIER_PATTERN.match(parameter_id)
    ):
        raise ScenarioConfigurationInvalid(
            f"'{where}.parameter_id' must be lowercase alphanumeric words "
            f"separated by a hyphen in {source}, got {parameter_id!r}"
        )

    display_name = _require_free_text(
        raw,
        "display_name",
        max_length=MAX_DISPLAY_NAME_LENGTH,
        where=where,
        source=source,
    )

    value = raw.get("value")
    unit = raw.get("unit")

    # `isinstance(True, int)` is True, so booleans are excluded by type: a
    # scenario parameter is a quantity or a phrase, never a flag.
    if type(value) in (int, float):
        if unit not in PARAMETER_UNITS:
            raise ScenarioConfigurationInvalid(
                f"'{where}.unit' must be one of {sorted(PARAMETER_UNITS)} in "
                f"{source}, got {unit!r}. A numeric parameter carries a unit, "
                "because a quantity without one cannot be read."
            )
        return ScenarioParameter(
            parameter_id=parameter_id,
            display_name=display_name,
            value=float(value),
            unit=unit,
        )

    if isinstance(value, str):
        if unit is not None:
            raise ScenarioConfigurationInvalid(
                f"'{where}.unit' must be absent when the value is text, in "
                f"{source}. A unit on a phrase is meaningless, and a screen "
                "would render it as though the phrase were a quantity."
            )
        text = _require_free_text(
            raw,
            "value",
            max_length=MAX_PARAMETER_TEXT_LENGTH,
            where=where,
            source=source,
        )
        return ScenarioParameter(
            parameter_id=parameter_id,
            display_name=display_name,
            value=text,
            unit=None,
        )

    raise ScenarioConfigurationInvalid(
        f"'{where}.value' must be a number with a unit, or text without one, "
        f"in {source}, got {value!r}"
    )


def _parse_private_expectations(
    raw: Any, *, source: str
) -> tuple[PrivateExpectation, ...]:
    """The private half, parsed into its own records.

    Absent is legal and means this scenario declares no expectations. It is not
    the same as a scenario whose expectations were hidden: nothing here hides
    anything, and what is parsed into this field is what the document put in
    the private section.
    """
    if raw is None:
        return ()

    where = "scenario.private_expectations"
    if not isinstance(raw, list):
        raise ScenarioConfigurationInvalid(
            f"'{where}' must be a list of expectations, or absent, in {source}"
        )
    if len(raw) > MAX_PRIVATE_EXPECTATIONS:
        raise ScenarioConfigurationInvalid(
            f"'{where}' declares {len(raw)} expectations in {source}, above "
            f"the limit of {MAX_PRIVATE_EXPECTATIONS}"
        )

    parsed: list[PrivateExpectation] = []
    seen: set[str] = set()

    for index, entry in enumerate(raw):
        entry_where = f"{where}[{index}]"
        if not isinstance(entry, Mapping):
            raise ScenarioConfigurationInvalid(
                f"'{entry_where}' must be an object in {source}"
            )

        _reject_unknown_keys(
            entry,
            EXPECTATION_KEYS,
            where=entry_where,
            source=source,
            private_section=True,
        )

        expectation_id = entry.get("expectation_id")
        if (
            not isinstance(expectation_id, str)
            or len(expectation_id) > MAX_TEMPLATE_ID_LENGTH
            or not IDENTIFIER_PATTERN.match(expectation_id)
        ):
            raise ScenarioConfigurationInvalid(
                f"'{entry_where}.expectation_id' must be lowercase "
                f"alphanumeric words separated by a hyphen in {source}, got "
                f"{expectation_id!r}"
            )
        if expectation_id in seen:
            raise ScenarioConfigurationInvalid(
                f"Duplicate 'expectation_id' {expectation_id!r} in {source}"
            )
        seen.add(expectation_id)

        parsed.append(
            PrivateExpectation(
                expectation_id=expectation_id,
                display_name=_require_free_text(
                    entry,
                    "display_name",
                    max_length=MAX_DISPLAY_NAME_LENGTH,
                    where=entry_where,
                    source=source,
                ),
                oracle_kind=_require_choice(
                    entry,
                    "oracle_kind",
                    EXPECTATION_KINDS,
                    where=entry_where,
                    source=source,
                ),
                statement=_require_free_text(
                    entry,
                    "statement",
                    max_length=MAX_STATEMENT_LENGTH,
                    where=entry_where,
                    source=source,
                ),
            )
        )

    return tuple(parsed)


def _require_free_text(
    mapping: Mapping[str, Any],
    key: str,
    *,
    max_length: int,
    where: str,
    source: str,
) -> str:
    name = f"'{where}.{key}'"
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ScenarioConfigurationInvalid(
            f"{name} is required in {source}. {FREE_TEXT_RULE}"
        )
    value = value.strip()
    if len(value) > max_length:
        raise ScenarioConfigurationInvalid(
            f"{name} is longer than {max_length} characters in {source}. "
            f"{FREE_TEXT_RULE}"
        )
    if any(character < " " or character == "\x7f" for character in value):
        raise ScenarioConfigurationInvalid(
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
        raise ScenarioConfigurationInvalid(
            f"'{where}.{key}' must be one of {sorted(allowed)} in {source}, "
            f"got {value!r}. The scenario taxonomy is closed: an unsupported "
            "value would put a category on a screen, and later into a run and "
            "a simulator, that nothing in the product can interpret."
        )
    return value


def _is_private_expectation_key(key: str) -> bool:
    lowered = key.casefold()
    return lowered in PRIVATE_EXPECTATION_KEYS or lowered.startswith(
        PRIVATE_EXPECTATION_KEY_PREFIXES
    )


def _reject_unknown_keys(
    mapping: Mapping[str, Any],
    allowed: frozenset[str],
    *,
    where: str,
    source: str,
    private_section: bool = False,
) -> None:
    unknown = sorted(str(key) for key in set(mapping) - allowed)
    if not unknown:
        return

    if not private_section:
        misplaced = [key for key in unknown if _is_private_expectation_key(key)]
        if misplaced:
            raise ScenarioConfigurationInvalid(
                f"Private expectation keys {misplaced} appear in '{where}' in "
                f"{source}. Test-oracle expectations live in the scenario's "
                "'private_expectations' section and nowhere else: public "
                "authoring data says what the simulated world does, and an "
                "expectation says what a test should later conclude about it."
            )

    raise ScenarioConfigurationInvalid(
        f"Unknown {where} keys {unknown} in {source}"
    )
