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

T018 adds the execution contract to that list, and the refusals there are the
ones that carry the most weight, because each closes a way for an authored
value to mean two things at once:

- an execution role whose entry kind cannot carry it - above all an evidence
  condition that tries to be a cause, which is the exact ambiguity the slice
  exists to remove;
- a reported observation that declares ownership, or carries a state effect.
  There is no field on a reported value that could name it as the source of an
  initial state or a transition, and that is the structural form of "an
  observation never prescribes private world state";
- a timing shape whose fields do not match it: a point with a length, a window
  without one, a rate applied at an instant;
- two answers to one initial world value, or none;
- a reporting cadence, closed at the vocabulary rather than at a position.
  No duration unit is an authoring unit, so a duration cannot be written as a
  parameter anywhere in a document, and a reported observation must be timed
  as a POINT, so it cannot be spread across a window either. Foundation
  declares that a signal can report and declares no cadence, and nothing here
  infers one from a device name, from display text, or from the spacing
  between authored entries. What this does NOT reach is prose: a description
  may say "every fifteen minutes" in English, and it is English, exactly as
  the breaker ban treats free text;
- a negative, infinite, or not-a-number quantity in a dimension where none is
  meaningful. That is the `invalid-rate` bound case in
  `scenarios/execution.py`, and it is the only one of the four this build can
  enforce end to end, because it is the only one decidable without executing
  anything.

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

## Identifiers are vocabulary

`scenario_id`, `event_id`, `parameter_id` and `expectation_id` are identifiers
this domain coins for its own parts, and every one of them is rendered as the
name of a thing. They are therefore scenario schema vocabulary and carry the
breaker/control ban: `_require_identifier` refuses one built from a banned
token, with the same rule text the vocabulary scan uses.

Enforcing it here rather than only in a test matters twice. A user-authored
document in `var/scenarios/` is never seen by a test and would otherwise put
`breaker-position` on a screen as a parameter name; and a rule enforced by a
value cannot be satisfied by a scan that turns out not to reach it, which is
exactly how the T017 review found this gap.

T018 adds three more positions this domain owns and therefore scans:
`source_id` and the `observation.source_id` that references it, and
`state_key`. A state key is where a breaker position would most plausibly
arrive next - a world state called `breaker-position` would read as perfectly
natural to an author - so it is validated as an identifier and refused on the
same rule.

Identifier-valued positions deliberately NOT covered are references into other
identity spaces, whose naming this domain does not own: `target_site.site_id`,
`target_site.template_id`, and the `device_id` and `signal_id` an observation
source borrows from the target Site's Foundation. Refusing a token there would
refuse a legitimately-named Site, template or device rather than protect
scenario vocabulary, and a guard that blocks something legitimate is a guard
somebody relaxes. Free-text fields are not covered either, for the reason
stated in `assetops_backend/control_vocabulary.py`: prose is English, not
schema.

## Origin is not declared

`origin` is supplied by the store, not read from the document. A user-authored
scenario that could write `origin: SHIPPED` into its own file would be claiming
provenance it does not have.

Refusal messages here are product copy. A developer authoring a scenario meets
them, so each one names what is wrong and what would be acceptable instead.
"""

from __future__ import annotations

import math
import re
from typing import Any, Mapping, NoReturn

from assetops_backend.control_vocabulary import (
    CONTROL_VOCABULARY_RULE,
    banned_tokens_in,
)
from assetops_backend.document_bounds import DocumentLimits, reject_oversized
from assetops_backend.scenarios.execution import (
    CANONICAL_UNITS,
    DURATION_UNIT_SPELLINGS,
    NON_NEGATIVE_DIMENSIONS,
    RATE_INTEGRALS,
)
from assetops_backend.scenarios.identity import validate_scenario_id
from assetops_backend.scenarios.models import (
    CADENCE_OWNERSHIP,
    EVENT_CATEGORIES,
    EXECUTABLE_ROLES,
    EXECUTION_REQUIREMENTS,
    EXECUTION_ROLES,
    EXPECTATION_KINDS,
    BOUND_KINDS,
    INITIALIZATION_OWNERS,
    OBSERVATION_SOURCE_KINDS,
    PARAMETER_UNITS,
    ROLES_BY_ENTRY_KIND,
    SCENARIO_ORIGINS,
    STATE_CHANGING_ROLES,
    STATE_EFFECT_DIRECTIONS,
    TARGET_SITE_POLICIES,
    TIMELINE_ENTRY_KINDS,
    TIMING_SHAPES,
    EntryTiming,
    ObservationBinding,
    ObservationSource,
    ParameterBound,
    ParameterOwnership,
    PrivateExpectation,
    ScenarioDefinition,
    ScenarioParameter,
    ScenarioTargetSite,
    ScenarioVersion,
    StateEffect,
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
        "observation_sources",
        "timeline",
        "public_parameters",
        "private_expectations",
    }
)
VERSION_KEYS = frozenset(
    {"scenario_version", "version_valid_from", "supersedes"}
)
TARGET_SITE_KEYS = frozenset({"policy", "site_id", "template_id", "requirement"})
OBSERVATION_SOURCE_KEYS = frozenset(
    {
        "source_id",
        "source_kind",
        "device_id",
        "signal_id",
        "cadence_ownership",
        "description",
    }
)
TIMELINE_ENTRY_KEYS = frozenset(
    {
        "event_id",
        "sequence",
        "offset_minutes",
        "entry_kind",
        "category",
        "description",
        "parameters",
        "execution_role",
        "state_key",
        "execution_requirement",
        "timing",
        "state_effect",
        "observation",
    }
)
TIMING_KEYS = frozenset({"shape", "duration_minutes"})
STATE_EFFECT_KEYS = frozenset(
    {"direction", "quantity_parameter_id", "rate_parameter_id"}
)
OBSERVATION_BINDING_KEYS = frozenset({"source_id", "reported_parameter_id"})
OWNERSHIP_KEYS = frozenset({"owner", "initializes"})
BOUND_KEYS = frozenset({"state_key", "bound_kind"})
PARAMETER_KEYS = frozenset(
    {
        "parameter_id",
        "display_name",
        "value",
        "unit",
        "execution_role",
        "state_key",
        "execution_requirement",
        "ownership",
        "bounds",
    }
)
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
MAX_OBSERVATION_SOURCES = 32
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
    observation_sources = _parse_observation_sources(
        document.get("observation_sources"), source=source
    )
    timeline = _parse_timeline(document.get("timeline"), source=source)
    public_parameters = _parse_public_parameters(
        document.get("public_parameters"), source=source
    )
    private_expectations = _parse_private_expectations(
        document.get("private_expectations"), source=source
    )

    scenario = ScenarioDefinition(
        scenario_id=scenario_id,
        display_name=display_name,
        purpose=purpose,
        origin=origin,
        version=version,
        target_site=target_site,
        observation_sources=observation_sources,
        timeline=timeline,
        public_parameters=public_parameters,
        private_expectations=private_expectations,
    )

    _validate_execution_contract(scenario, source=source)

    return scenario


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

    event_id = _require_identifier(
        raw, "event_id", where=where, source=source
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

    execution_role = _require_choice(
        raw, "execution_role", EXECUTION_ROLES, where=where, source=source
    )
    allowed_roles = ROLES_BY_ENTRY_KIND[entry_kind]
    if execution_role not in allowed_roles:
        raise ScenarioConfigurationInvalid(
            f"'{where}' is a {entry_kind} entry with execution role "
            f"{execution_role!r} in {source}. A {entry_kind} entry may carry "
            f"{sorted(allowed_roles)}. An evidence condition states what the "
            "evidence path is expected to be in, so it may be delivered as a "
            "reported observation or carried as description - it may never be "
            "a cause, because then one row would prescribe both a cause and "
            "its own expected result."
        )

    state_key, execution_requirement = _parse_execution_placement(
        raw, execution_role, where=where, source=source
    )

    timing = _parse_timing(
        raw.get("timing"), offset=offset, where=where, source=source
    )

    # A reading is taken at an instant. A window on one says either that the
    # source reported repeatedly across it - a cadence, which a scenario does
    # not own - or that the value is an aggregate over it, and this product
    # has no vocabulary for an aggregate. Both readings are refused rather
    # than one of them being guessed at.
    if execution_role == "REPORTED_OBSERVATION" and timing.shape != "POINT":
        raise ScenarioConfigurationInvalid(
            f"'{where}' is a reported observation timed as {timing.shape} in "
            f"{source}. A reading happens at an instant, so it is a POINT. A "
            "reading spread over a window would be a reporting cadence or an "
            "aggregate, and a scenario declares neither."
        )

    state_effect = _parse_state_effect(
        raw.get("state_effect"),
        execution_role=execution_role,
        timing=timing,
        where=where,
        source=source,
    )
    observation = _parse_observation_binding(
        raw.get("observation"),
        execution_role=execution_role,
        where=where,
        source=source,
    )

    return TimelineEntry(
        event_id=event_id,
        sequence=sequence,
        offset_minutes=offset,
        entry_kind=entry_kind,
        category=category,
        description=description,
        parameters=parameters,
        execution_role=execution_role,
        state_key=state_key,
        execution_requirement=execution_requirement,
        timing=timing,
        state_effect=state_effect,
        observation=observation,
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

    parameter_id = _require_identifier(
        raw, "parameter_id", where=where, source=source
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

    # Before anything else, because the generic unknown-unit refusal would be
    # true and useless here. A duration is not a parameter in this product:
    # an entry's length belongs to its timing, and a reporting rate belongs to
    # a versioned observation profile that does not exist yet.
    if isinstance(unit, str) and unit.casefold() in DURATION_UNIT_SPELLINGS:
        raise ScenarioConfigurationInvalid(
            f"'{where}.unit' is the duration {unit!r} in {source}. A scenario "
            "parameter may not carry a duration at all. An entry's length is "
            "declared by its timing, as 'duration_minutes' on a WINDOW; a "
            "reporting cadence is not a scenario's to declare, because a "
            "site's foundation declares that a signal can report and declares "
            "no rate, and one arrives when a versioned observation profile "
            "declares it."
        )

    execution_role = _require_choice(
        raw, "execution_role", EXECUTION_ROLES, where=where, source=source
    )
    state_key, execution_requirement = _parse_execution_placement(
        raw, execution_role, where=where, source=source
    )
    ownership = _parse_ownership(
        raw.get("ownership"),
        execution_role=execution_role,
        where=where,
        source=source,
    )
    bounds = _parse_parameter_bound(
        raw.get("bounds"),
        ownership=ownership,
        state_key=state_key,
        where=where,
        source=source,
    )

    # A Foundation-owned value has no value position at all
    # (`D-2026-09-22-foundation-value-declaration`). Checked before the
    # quantity branches below rather than inside them, because the point is
    # that no branch may accept one: a parameter the Site's Foundation
    # answers for declares the state, the unit and the owner, and states no
    # number.
    #
    # The rule is keyed on the OWNER, which is the only thing this document
    # carries that identifies these parameters - the binding that addresses a
    # Foundation property lives in the model profile, and this parser sees no
    # profile. So it reaches every `SITE_FOUNDATION` parameter, the tank
    # capacity as much as the consumption coefficient, and there is no field
    # to write an exemption in.
    if ownership is not None and ownership.owner == "SITE_FOUNDATION":
        # A Foundation-owned value must be an INITIAL world value in this
        # build, and the reason is that nothing else can carry one.
        #
        # A parameter states no number once its owner is the Foundation, so
        # the only place its answer can be frozen is a
        # `FrozenInitializationInput`, which has a shape for an absent value
        # and a blocking reason beside it. `initialization_inputs` builds
        # that collection from parameters whose ownership initializes, and
        # `FrozenParameter` has no shape for an absent value at all - so a
        # Foundation-owned parameter that does not initialize would be
        # declared, required, and then present in neither frozen collection.
        # That is not a value going unanswered, which blocks; it is a
        # declared need disappearing while the run reports `READY`, which is
        # a refusal turned into a wrong answer.
        #
        # An independent review found this combination accepted and produced
        # exactly that outcome, for a causal input and a forcing input alike.
        # It is closed here rather than patched downstream, because a rule
        # that depends on a later filter noticing is the shape this project
        # keeps paying for.
        #
        # The concept it refuses - a coefficient the Foundation answers for
        # that is not an initial world value - is legitimate and has no
        # carrier yet. The slice that needs one adds the carrier and this
        # refusal together; it is not something an author may reach by
        # writing `false` here.
        if not ownership.initializes:
            raise ScenarioConfigurationInvalid(
                f"'{where}' declares that the site's foundation owns it and "
                f"that it does not initialize, in {source}. A "
                "foundation-owned parameter states no number, so the only "
                "record a run has for its answer is an initial world value - "
                "and a value that neither initializes nor states a number "
                "would be declared, required, and frozen nowhere. Declare it "
                "as an initial world value, or give the number an owner that "
                "states one."
            )
        if "value" in raw:
            raise ScenarioConfigurationInvalid(
                f"'{where}' declares that the site's foundation owns it and "
                f"also states a value, in {source}. A foundation-owned "
                "parameter declares the need - the state, the unit, and that "
                "the foundation answers - and states no number. A number here "
                "would be a machine's physical property written into the "
                "story: run the same scenario against a different generator "
                "and it would still follow the story, now as a requirement "
                "that fails the run."
            )
        if unit not in PARAMETER_UNITS:
            raise ScenarioConfigurationInvalid(
                f"'{where}.unit' must be one of {sorted(PARAMETER_UNITS)} in "
                f"{source}, got {unit!r}. A foundation-owned parameter states "
                "no number and must still state the unit, because the unit is "
                "what run setup checks the foundation's own property against."
            )
        return ScenarioParameter(
            parameter_id=parameter_id,
            display_name=display_name,
            value=None,
            unit=unit,
            execution_role=execution_role,
            state_key=state_key,
            execution_requirement=execution_requirement,
            ownership=ownership,
            bounds=bounds,
        )

    # `isinstance(True, int)` is True, so booleans are excluded by type: a
    # scenario parameter is a quantity or a phrase, never a flag.
    if type(value) in (int, float):
        if unit not in PARAMETER_UNITS:
            raise ScenarioConfigurationInvalid(
                f"'{where}.unit' must be one of {sorted(PARAMETER_UNITS)} in "
                f"{source}, got {unit!r}. A numeric parameter carries a unit, "
                "because a quantity without one cannot be read."
            )
        _reject_unusable_quantity(float(value), unit, where=where, source=source)
        return ScenarioParameter(
            parameter_id=parameter_id,
            display_name=display_name,
            value=float(value),
            unit=unit,
            execution_role=execution_role,
            state_key=state_key,
            execution_requirement=execution_requirement,
            ownership=ownership,
            bounds=bounds,
        )

    if isinstance(value, str):
        if unit is not None:
            raise ScenarioConfigurationInvalid(
                f"'{where}.unit' must be absent when the value is text, in "
                f"{source}. A unit on a phrase is meaningless, and a screen "
                "would render it as though the phrase were a quantity."
            )
        if execution_role in EXECUTABLE_ROLES:
            raise ScenarioConfigurationInvalid(
                f"'{where}' carries text and the executable role "
                f"{execution_role!r} in {source}. An executor consumes "
                "quantities in canonical units; a phrase would have to be "
                "parsed out of display text, which is exactly what a canonical "
                "unit exists to avoid. Author it as a quantity with a unit, or "
                "mark it NON_EXECUTABLE_CONDITION."
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
            execution_role=execution_role,
            state_key=state_key,
            execution_requirement=execution_requirement,
            ownership=ownership,
            bounds=bounds,
        )

    raise ScenarioConfigurationInvalid(
        f"'{where}.value' must be a number with a unit, or text without one, "
        f"in {source}, got {value!r}"
    )


def _reject_unusable_quantity(
    value: float, unit: str, *, where: str, source: str
) -> None:
    """The `invalid-rate` bound case, enforced where it can be enforced.

    `scenarios/execution.py` declares four bound cases and this is the only one
    decidable without executing anything, so it is the only one this build
    holds end to end. Refusing here means no run setup and no kernel ever sees
    a rate or a quantity it would have to invent a rule for.
    """
    if not math.isfinite(value):
        raise ScenarioConfigurationInvalid(
            f"'{where}.value' is {value!r} in {source}. A quantity must be a "
            "finite number: an infinity or a not-a-number would reach a run as "
            "a state transition nothing could bound."
        )

    dimension = CANONICAL_UNITS[unit].dimension
    if value < 0 and dimension in NON_NEGATIVE_DIMENSIONS:
        raise ScenarioConfigurationInvalid(
            f"'{where}.value' is {value} {unit} in {source}, and a "
            f"{dimension.lower().replace('_', ' ')} cannot be negative. State "
            "the direction with the entry's state effect rather than with the "
            "sign of a quantity: a negative rate reaching a kernel would have "
            "to be clamped or reinterpreted, and this product does neither "
            "silently."
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

        expectation_id = _require_identifier(
            entry, "expectation_id", where=entry_where, source=source
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


def _parse_execution_placement(
    raw: Mapping[str, Any], execution_role: str, *, where: str, source: str
) -> tuple[str | None, str | None]:
    """The two fields an executable value must carry, and must not otherwise.

    An executable value names the state it concerns and says whether later run
    setup may proceed without support for it. A non-executable condition names
    neither, because nothing consumes it and a state key on a value nothing
    consumes would read as a claim about the world.
    """
    state_key = raw.get("state_key")
    requirement = raw.get("execution_requirement")

    if execution_role not in EXECUTABLE_ROLES:
        if state_key is not None or requirement is not None:
            raise ScenarioConfigurationInvalid(
                f"'{where}' declares role {execution_role!r} and also a state "
                f"key or an execution requirement in {source}. A "
                "non-executable condition is description: nothing consumes "
                "it, so naming a state for it would read as a claim about the "
                "world that no executor will ever make true."
            )
        return None, None

    if state_key is None:
        raise ScenarioConfigurationInvalid(
            f"'{where}.state_key' is required for the executable role "
            f"{execution_role!r} in {source}. An executable value names the "
            "world or reporting state it concerns, so later run setup can "
            "decide whether the chosen model profile supports it."
        )

    resolved_state_key = _require_identifier(
        raw, "state_key", where=where, source=source
    )
    resolved_requirement = _require_choice(
        raw,
        "execution_requirement",
        EXECUTION_REQUIREMENTS,
        where=where,
        source=source,
    )
    return resolved_state_key, resolved_requirement


def _parse_ownership(
    raw: Any, *, execution_role: str, where: str, source: str
) -> ParameterOwnership | None:
    """Who answers for a value an executor would consume.

    Present exactly for `CAUSAL_INPUT` and `FORCING_INPUT`. The refusal that
    matters is the one for `REPORTED_OBSERVATION`: a reported value with an
    ownership record could be named as the source of an initial world state,
    and that is the whole thing this slice exists to make impossible.

    `initializes: true` is narrower still and is confined to
    `STATE_CHANGING_ROLES`. A forcing input has an owner because a run has to
    know who answers for the profile it is put under, but the value of an
    exogenous state at every instant comes from that profile, including the
    first - so an initial-value declaration beside it would be a second answer
    to the same question. The T018 review found a forcing input initializing a
    world state while the screen said only a causal input could.
    """
    owns = execution_role in {"CAUSAL_INPUT", "FORCING_INPUT"}

    if not owns:
        if raw is not None:
            if execution_role == "REPORTED_OBSERVATION":
                raise ScenarioConfigurationInvalid(
                    f"'{where}' is a reported observation and declares "
                    f"ownership in {source}. A reported value never "
                    "initializes or transitions private world state: it is "
                    "what a source said, not what the world was told to do. "
                    "Declare the cause that produced it as its own causal "
                    "entry instead."
                )
            raise ScenarioConfigurationInvalid(
                f"'{where}' declares role {execution_role!r} and also "
                f"ownership in {source}. Only a causal or forcing input has "
                "an owner, because only those are consumed."
            )
        return None

    if not isinstance(raw, Mapping):
        raise ScenarioConfigurationInvalid(
            f"'{where}.ownership' must be an object declaring "
            f"{sorted(OWNERSHIP_KEYS)} in {source}. Every value an executor "
            "consumes has an owner that answers for it: the site's "
            "foundation, this scenario, a run override, or a versioned model "
            "rule. A value with no owner is one a trace could invent."
        )

    _reject_unknown_keys(
        raw, OWNERSHIP_KEYS, where=f"{where}.ownership", source=source
    )

    owner = _require_choice(
        raw,
        "owner",
        INITIALIZATION_OWNERS,
        where=f"{where}.ownership",
        source=source,
    )

    initializes = raw.get("initializes")
    if type(initializes) is not bool:
        raise ScenarioConfigurationInvalid(
            f"'{where}.ownership.initializes' must be true or false in "
            f"{source}, got {initializes!r}. It says whether this value is an "
            "initial world value or a coefficient a transition uses; those "
            "are different obligations and a run freezes them differently."
        )

    if initializes and execution_role not in STATE_CHANGING_ROLES:
        raise ScenarioConfigurationInvalid(
            f"'{where}' declares role {execution_role!r} and initializes the "
            f"world state {raw.get('owner')!r} answers for, in {source}. Only "
            f"{sorted(STATE_CHANGING_ROLES)} may reach initialization or a "
            "private-state transition. An exogenous state's value at every "
            "instant comes from the forcing profile itself, including the "
            "first, so an initial value declared beside it would be a second "
            "answer to what that state is when the interval starts."
        )

    return ParameterOwnership(owner=owner, initializes=initializes)


def _parse_parameter_bound(
    raw: Any,
    *,
    ownership: ParameterOwnership | None,
    state_key: str | None,
    where: str,
    source: str,
) -> ParameterBound | None:
    """That this world value limits another one.

    Optional, and allowed only on a declared INITIAL world value: a bound is
    itself a world value a run starts from, so whatever answers for the one
    answers for the other. A coefficient or a reported reading bounding
    something would be a limit with no owner.

    Without this declaration the contract knows a capacity and a volume as two
    unrelated state keys, which is how `reconcile_reported_observations` came
    to report a declared level above the capacity the same document declares.
    """
    if raw is None:
        return None

    if ownership is None or not ownership.initializes:
        raise ScenarioConfigurationInvalid(
            f"'{where}' declares a bound on another state without being an "
            f"initial world value itself, in {source}. A bound is a world "
            "value a run starts from and has to be owned like one."
        )

    if not isinstance(raw, Mapping):
        raise ScenarioConfigurationInvalid(
            f"'{where}.bounds' must be an object declaring "
            f"{sorted(BOUND_KEYS)} in {source}."
        )

    _reject_unknown_keys(
        raw, BOUND_KEYS, where=f"{where}.bounds", source=source
    )

    bounded = _require_identifier(
        raw, "state_key", where=f"{where}.bounds", source=source
    )
    if bounded == state_key:
        raise ScenarioConfigurationInvalid(
            f"'{where}.bounds' bounds {bounded!r}, which is the state this "
            f"value already is, in {source}. A bound limits another state; a "
            "value that bounded itself would say nothing."
        )

    bound_kind = _require_choice(
        raw, "bound_kind", BOUND_KINDS, where=f"{where}.bounds", source=source
    )

    return ParameterBound(state_key=bounded, bound_kind=bound_kind)


def _parse_timing(
    raw: Any, *, offset: int, where: str, source: str
) -> EntryTiming:
    """Where an entry sits in time, as a shape with validated fields.

    The shapes are distinct rather than a duration that may be absent: a point
    with a length and a window without one are both authoring mistakes with a
    plausible-looking document, and a screen cannot tell them apart from what
    the author meant.
    """
    if not isinstance(raw, Mapping):
        raise ScenarioConfigurationInvalid(
            f"'{where}.timing' must be an object declaring "
            f"{sorted(TIMING_KEYS)} in {source}. Every entry declares whether "
            "it happens at an instant, across a window, or for the whole "
            "interval, because a dispatcher cannot infer that from an offset."
        )

    _reject_unknown_keys(
        raw, TIMING_KEYS, where=f"{where}.timing", source=source
    )

    shape = _require_choice(
        raw, "shape", TIMING_SHAPES, where=f"{where}.timing", source=source
    )
    duration = raw.get("duration_minutes")

    if shape == "POINT":
        if duration is not None:
            raise ScenarioConfigurationInvalid(
                f"'{where}.timing' is a POINT and declares a length of "
                f"{duration!r} in {source}. A point happens at its offset and "
                "has no length; if it lasts, it is a WINDOW."
            )
        return EntryTiming(shape=shape, duration_minutes=None)

    if shape == "INTERVAL_WIDE":
        if duration is not None:
            raise ScenarioConfigurationInvalid(
                f"'{where}.timing' is INTERVAL_WIDE and declares a length of "
                f"{duration!r} in {source}. An interval-wide entry lasts as "
                "long as the run does, and how long that is belongs to run "
                "setup rather than to the scenario."
            )
        if offset != 0:
            raise ScenarioConfigurationInvalid(
                f"'{where}' is INTERVAL_WIDE and starts at offset {offset} in "
                f"{source}. An entry that holds for the whole interval starts "
                "when the interval does; one that starts later is a WINDOW "
                "with a length."
            )
        return EntryTiming(shape=shape, duration_minutes=None)

    if type(duration) is not int or not 1 <= duration <= MAX_OFFSET_MINUTES:
        raise ScenarioConfigurationInvalid(
            f"'{where}.timing.duration_minutes' must be an integer between 1 "
            f"and {MAX_OFFSET_MINUTES} for a WINDOW in {source}, got "
            f"{duration!r}. A window without a length has no end, so nothing "
            "can say which steps it is active for."
        )
    if offset + duration > MAX_OFFSET_MINUTES:
        raise ScenarioConfigurationInvalid(
            f"'{where}.timing' runs from {offset} to {offset + duration} "
            f"minutes in {source}, past the {MAX_OFFSET_MINUTES}-minute limit "
            "on where a scenario may place anything."
        )

    return EntryTiming(shape=shape, duration_minutes=duration)


def _parse_state_effect(
    raw: Any,
    *,
    execution_role: str,
    timing: EntryTiming,
    where: str,
    source: str,
) -> StateEffect | None:
    """What a causal entry changes. Present exactly for `CAUSAL_INPUT`.

    This is the whole of the private-state transition surface an authored
    scenario can reach, which is why every other role is refused one by name
    rather than by silence.
    """
    if execution_role != "CAUSAL_INPUT":
        if raw is not None:
            raise ScenarioConfigurationInvalid(
                f"'{where}' declares role {execution_role!r} and also a state "
                f"effect in {source}. Only a causal input changes private "
                "world state. A reported observation with one would be an "
                "authored reading writing itself into the world it claims to "
                "be reporting on."
            )
        return None

    if not isinstance(raw, Mapping):
        raise ScenarioConfigurationInvalid(
            f"'{where}.state_effect' must be an object declaring "
            f"{sorted(STATE_EFFECT_KEYS)} in {source}. A causal input says "
            "what it changes and by how much; one that does not is a cause "
            "with no consequence, and a kernel would have nothing to apply."
        )

    _reject_unknown_keys(
        raw, STATE_EFFECT_KEYS, where=f"{where}.state_effect", source=source
    )

    direction = _require_choice(
        raw,
        "direction",
        STATE_EFFECT_DIRECTIONS,
        where=f"{where}.state_effect",
        source=source,
    )

    quantity_id = raw.get("quantity_parameter_id")
    rate_id = raw.get("rate_parameter_id")

    if (quantity_id is None) == (rate_id is None):
        raise ScenarioConfigurationInvalid(
            f"'{where}.state_effect' must name exactly one of "
            "'quantity_parameter_id' and 'rate_parameter_id' in "
            f"{source}. A transition is either a quantity applied once or a "
            "rate applied across a window; declaring both, or neither, leaves "
            "the magnitude undefined."
        )

    if quantity_id is not None:
        resolved = _require_identifier(
            raw, "quantity_parameter_id", where=f"{where}.state_effect", source=source
        )
        return StateEffect(
            direction=direction,
            quantity_parameter_id=resolved,
            rate_parameter_id=None,
        )

    if timing.shape != "WINDOW":
        raise ScenarioConfigurationInvalid(
            f"'{where}.state_effect' applies a rate and the entry is timed as "
            f"{timing.shape} in {source}. A rate moves nothing at an instant "
            "and has no total over an interval nobody has chosen, so a rate "
            "effect belongs to a WINDOW with a declared length."
        )

    resolved = _require_identifier(
        raw, "rate_parameter_id", where=f"{where}.state_effect", source=source
    )
    return StateEffect(
        direction=direction,
        quantity_parameter_id=None,
        rate_parameter_id=resolved,
    )


def _parse_observation_binding(
    raw: Any, *, execution_role: str, where: str, source: str
) -> ObservationBinding | None:
    """Which source a reported entry arrives through, and which value it carries."""
    if execution_role != "REPORTED_OBSERVATION":
        if raw is not None:
            raise ScenarioConfigurationInvalid(
                f"'{where}' declares role {execution_role!r} and also an "
                f"observation binding in {source}. Only a reported "
                "observation arrives through a source."
            )
        return None

    if not isinstance(raw, Mapping):
        raise ScenarioConfigurationInvalid(
            f"'{where}.observation' must be an object declaring "
            f"{sorted(OBSERVATION_BINDING_KEYS)} in {source}. A reported value "
            "names the source it came through, because a reading with no "
            "source is indistinguishable from a value somebody wrote down as "
            "the answer."
        )

    _reject_unknown_keys(
        raw,
        OBSERVATION_BINDING_KEYS,
        where=f"{where}.observation",
        source=source,
    )

    return ObservationBinding(
        source_id=_require_identifier(
            raw, "source_id", where=f"{where}.observation", source=source
        ),
        reported_parameter_id=_require_identifier(
            raw,
            "reported_parameter_id",
            where=f"{where}.observation",
            source=source,
        ),
    )


def _parse_observation_sources(
    raw: Any, *, source: str
) -> tuple[ObservationSource, ...]:
    """The device and non-device sources this scenario's readings arrive through.

    Absent is legal and means the scenario authors no reported observation.
    Whether that is consistent with the timeline is checked once the timeline
    is parsed, so that a missing source is reported against the entry that
    wanted one.
    """
    if raw is None:
        return ()

    where = "scenario.observation_sources"
    if not isinstance(raw, list):
        raise ScenarioConfigurationInvalid(
            f"'{where}' must be a list of sources, or absent, in {source}"
        )
    if len(raw) > MAX_OBSERVATION_SOURCES:
        raise ScenarioConfigurationInvalid(
            f"'{where}' declares {len(raw)} sources in {source}, above the "
            f"limit of {MAX_OBSERVATION_SOURCES}"
        )

    parsed: list[ObservationSource] = []
    seen: set[str] = set()

    for index, entry in enumerate(raw):
        entry_where = f"{where}[{index}]"
        if not isinstance(entry, Mapping):
            raise ScenarioConfigurationInvalid(
                f"'{entry_where}' must be an object in {source}"
            )

        _reject_unknown_keys(
            entry, OBSERVATION_SOURCE_KEYS, where=entry_where, source=source
        )

        source_id = _require_identifier(
            entry, "source_id", where=entry_where, source=source
        )
        if source_id in seen:
            raise ScenarioConfigurationInvalid(
                f"Duplicate observation 'source_id' {source_id!r} in {source}"
            )
        seen.add(source_id)

        source_kind = _require_choice(
            entry,
            "source_kind",
            OBSERVATION_SOURCE_KINDS,
            where=entry_where,
            source=source,
        )
        description = _require_free_text(
            entry,
            "description",
            max_length=MAX_DESCRIPTION_LENGTH,
            where=entry_where,
            source=source,
        )
        cadence_ownership = _require_choice(
            entry,
            "cadence_ownership",
            CADENCE_OWNERSHIP,
            where=entry_where,
            source=source,
        )

        device_id = entry.get("device_id")
        signal_id = entry.get("signal_id")

        if source_kind == "DEVICE_SIGNAL":
            device_id = _require_foundation_reference(
                entry, "device_id", where=entry_where, source=source
            )
            signal_id = _require_foundation_reference(
                entry, "signal_id", where=entry_where, source=source
            )
            if cadence_ownership != "NOT_DECLARED":
                raise ScenarioConfigurationInvalid(
                    f"'{entry_where}' is a device signal and declares cadence "
                    f"ownership {cadence_ownership!r} in {source}. A site's "
                    "foundation declares that a signal can report and "
                    "declares no cadence, so the truthful answer here is "
                    "NOT_DECLARED until a versioned observation profile owns "
                    "one. Nothing may infer a cadence from a device name, "
                    "from display text, or from the spacing between entries."
                )
        else:
            if device_id is not None or signal_id is not None:
                raise ScenarioConfigurationInvalid(
                    f"'{entry_where}' is an {source_kind} source and names a "
                    f"device or a signal in {source}. A value a person wrote "
                    "down has its own identity and no device identity; "
                    "borrowing one would put a hand-recorded note into the "
                    "evidence path wearing a sensor's name."
                )
            if cadence_ownership != "NOT_APPLICABLE":
                raise ScenarioConfigurationInvalid(
                    f"'{entry_where}' is an {source_kind} source and declares "
                    f"cadence ownership {cadence_ownership!r} in {source}. A "
                    "person writing a value down has no reporting rate for "
                    "anyone to own, so the truthful answer is NOT_APPLICABLE."
                )

        parsed.append(
            ObservationSource(
                source_id=source_id,
                source_kind=source_kind,
                device_id=device_id,
                signal_id=signal_id,
                cadence_ownership=cadence_ownership,
                description=description,
            )
        )

    return tuple(parsed)


def _require_foundation_reference(
    mapping: Mapping[str, Any], key: str, *, where: str, source: str
) -> str:
    """A device or signal identity borrowed from the target Site's Foundation.

    Shape only, and deliberately not scanned for scenario vocabulary: the
    scenario domain does not own how a Site names its devices, and refusing a
    token here would refuse a legitimately-named device rather than protect
    anything of ours. Whether the identity resolves is the service's question,
    exactly as it is for a declared target Site.
    """
    value = mapping.get(key)
    if (
        not isinstance(value, str)
        or len(value) > MAX_TEMPLATE_ID_LENGTH
        or not IDENTIFIER_PATTERN.match(value)
    ):
        raise ScenarioConfigurationInvalid(
            f"'{where}.{key}' must name a configured device or signal as "
            f"lowercase alphanumeric words separated by a hyphen in {source}, "
            f"got {value!r}. A device-signal source reports through an "
            "identity the target site's foundation declares."
        )
    return value


def _validate_execution_contract(
    scenario: ScenarioDefinition, *, source: str
) -> None:
    """The rules that need the whole document, not one section of it.

    Each of these is a way for a document whose parts are all individually
    well formed to mean two things at once, which is the failure shape T018
    exists to close. They are checked here rather than inside a section
    because none of them can be: a state effect naming a parameter cannot be
    resolved until every parameter is parsed.
    """
    parameters: dict[str, ScenarioParameter] = {}
    for parameter in scenario.public_parameters:
        parameters[parameter.parameter_id] = parameter
    for entry in scenario.timeline:
        for parameter in entry.parameters:
            if parameter.parameter_id in parameters:
                raise ScenarioConfigurationInvalid(
                    f"Duplicate parameter identity "
                    f"{parameter.parameter_id!r} in {source}. A parameter "
                    "identity is unique across the whole definition, because "
                    "a state effect and an observation binding refer to one "
                    "by that name and two answers would make the reference "
                    "ambiguous."
                )
            parameters[parameter.parameter_id] = parameter

    _validate_initial_world_values(parameters, source=source)

    sources = {item.source_id: item for item in scenario.observation_sources}
    referenced: set[str] = set()

    for entry in scenario.timeline:
        _validate_entry_parameters(entry, source=source)
        _validate_entry_state_effect(entry, parameters, source=source)
        referenced |= _validate_entry_observation(
            entry, parameters, sources, source=source
        )

    unreferenced = sorted(set(sources) - referenced)
    if unreferenced:
        raise ScenarioConfigurationInvalid(
            f"Observation sources {unreferenced} are declared in {source} and "
            "no entry reports through them. A declared source nothing uses is "
            "a device identity on a screen with nothing behind it."
        )


def _validate_initial_world_values(
    parameters: Mapping[str, ScenarioParameter], *, source: str
) -> None:
    """One attributable answer per initial world value, and never two."""
    initializers: dict[str, str] = {}
    for parameter in parameters.values():
        ownership = parameter.ownership
        if ownership is None or not ownership.initializes:
            continue
        state_key = parameter.state_key
        if state_key is None:
            continue
        if state_key in initializers:
            raise ScenarioConfigurationInvalid(
                f"Both {initializers[state_key]!r} and "
                f"{parameter.parameter_id!r} initialize the state "
                f"{state_key!r} in {source}. An initial world value has one "
                "attributable owner: two would let a run start from whichever "
                "the code happened to read first."
            )
        initializers[state_key] = parameter.parameter_id


def _validate_entry_parameters(entry: TimelineEntry, *, source: str) -> None:
    """A parameter on an entry executes the way its entry does, or not at all."""
    for parameter in entry.parameters:
        if parameter.execution_role == "NON_EXECUTABLE_CONDITION":
            continue
        if parameter.execution_role != entry.execution_role:
            raise ScenarioConfigurationInvalid(
                f"Parameter {parameter.parameter_id!r} on entry "
                f"{entry.event_id!r} declares role "
                f"{parameter.execution_role!r} while the entry declares "
                f"{entry.execution_role!r}, in {source}. A parameter on an "
                "entry is part of that entry: it executes the way the entry "
                "does, or it is description. A third answer would let an "
                "executable value hide inside an entry nothing executes it "
                "with."
            )
        if parameter.state_key != entry.state_key:
            raise ScenarioConfigurationInvalid(
                f"Parameter {parameter.parameter_id!r} on entry "
                f"{entry.event_id!r} names state {parameter.state_key!r} "
                f"while the entry names {entry.state_key!r}, in {source}."
            )

    # The cadence prohibition used to live here, as a TIME-dimension check on
    # a reported observation's parameters. The T018 review found it closed one
    # position and left three open - a top-level duration, a duration on the
    # entry forcing the reporting path, and a reading timed as a window - so
    # it moved to where no position can escape it. A duration has no unit to
    # be written in (`DURATION_UNIT_SPELLINGS`), and a reading must be a POINT
    # (`_parse_timeline_entry`). Nothing is checked here any more because
    # there is nothing left that could reach this far.


def _validate_entry_state_effect(
    entry: TimelineEntry,
    parameters: Mapping[str, ScenarioParameter],
    *,
    source: str,
) -> None:
    effect = entry.state_effect
    if effect is None:
        return

    named = effect.quantity_parameter_id or effect.rate_parameter_id
    assert named is not None  # the section parser refuses neither and both
    parameter = parameters.get(named)
    if parameter is None:
        raise ScenarioConfigurationInvalid(
            f"Entry {entry.event_id!r} applies parameter {named!r} in "
            f"{source} and no parameter with that identity is declared. A "
            "state effect names a value the definition carries rather than "
            "repeating a number, so the screen and a kernel cannot disagree "
            "about the magnitude."
        )

    if parameter.execution_role != "CAUSAL_INPUT":
        raise ScenarioConfigurationInvalid(
            f"Entry {entry.event_id!r} applies parameter {named!r}, which "
            f"declares role {parameter.execution_role!r}, in {source}. Only a "
            "causal input may be the magnitude of a private-state transition."
        )

    if parameter.state_key != entry.state_key:
        raise ScenarioConfigurationInvalid(
            f"Entry {entry.event_id!r} changes state {entry.state_key!r} "
            f"using parameter {named!r}, which names state "
            f"{parameter.state_key!r}, in {source}."
        )

    if parameter.unit is None:
        raise ScenarioConfigurationInvalid(
            f"Entry {entry.event_id!r} applies parameter {named!r}, which "
            f"carries no unit, in {source}."
        )

    dimension = CANONICAL_UNITS[parameter.unit].dimension

    if effect.rate_parameter_id is not None:
        if dimension not in RATE_INTEGRALS:
            raise ScenarioConfigurationInvalid(
                f"Entry {entry.event_id!r} applies {named!r} as a rate and its "
                f"unit {parameter.unit!r} is a {dimension} in {source}. Only "
                f"{sorted(RATE_INTEGRALS)} can be accumulated across a window "
                "into a quantity this product knows how to apply."
            )
        return

    if dimension in RATE_INTEGRALS:
        raise ScenarioConfigurationInvalid(
            f"Entry {entry.event_id!r} applies {named!r} as a one-off quantity "
            f"and its unit {parameter.unit!r} is a rate in {source}. A rate is "
            "declared with 'rate_parameter_id' and applied across a window."
        )


def _validate_entry_observation(
    entry: TimelineEntry,
    parameters: Mapping[str, ScenarioParameter],
    sources: Mapping[str, ObservationSource],
    *,
    source: str,
) -> set[str]:
    binding = entry.observation
    if binding is None:
        return set()

    if binding.source_id not in sources:
        raise ScenarioConfigurationInvalid(
            f"Entry {entry.event_id!r} reports through source "
            f"{binding.source_id!r} in {source} and no such observation "
            "source is declared. Every reading names the device or the person "
            "it came through, and the declaration is where a reader finds out "
            "which."
        )

    reported = parameters.get(binding.reported_parameter_id)
    if reported is None:
        raise ScenarioConfigurationInvalid(
            f"Entry {entry.event_id!r} reports parameter "
            f"{binding.reported_parameter_id!r} in {source} and no parameter "
            "with that identity is declared."
        )

    if reported not in entry.parameters:
        raise ScenarioConfigurationInvalid(
            f"Entry {entry.event_id!r} reports parameter "
            f"{binding.reported_parameter_id!r}, which belongs to a different "
            f"entry, in {source}. A reading carries its own value."
        )

    if reported.execution_role != "REPORTED_OBSERVATION":
        raise ScenarioConfigurationInvalid(
            f"Entry {entry.event_id!r} reports parameter "
            f"{binding.reported_parameter_id!r}, which declares role "
            f"{reported.execution_role!r}, in {source}."
        )

    return {binding.source_id}


def _require_identifier(
    mapping: Mapping[str, Any], key: str, *, where: str, source: str
) -> str:
    """Validate one identifier this domain coins, shape and vocabulary.

    Two refusals, deliberately separate. The shape refusal is about spelling;
    the vocabulary refusal is about what the product is allowed to name, and it
    names the decision so an author meets the reason rather than a rule number.
    """
    value = mapping.get(key)
    if (
        not isinstance(value, str)
        or len(value) > MAX_TEMPLATE_ID_LENGTH
        or not IDENTIFIER_PATTERN.match(value)
    ):
        raise ScenarioConfigurationInvalid(
            f"'{where}.{key}' must be lowercase alphanumeric words separated "
            f"by a hyphen in {source}, got {value!r}"
        )

    banned = banned_tokens_in(value)
    if banned:
        raise ScenarioConfigurationInvalid(
            f"'{where}.{key}' {value!r} is built from control-state vocabulary "
            f"{banned} in {source}. {CONTROL_VOCABULARY_RULE}"
        )

    return value


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
