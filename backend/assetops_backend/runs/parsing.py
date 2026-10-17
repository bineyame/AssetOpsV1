"""Strict parsing for run setup requests and for stored run documents.

Two halves, in one module because they are two readings of the same record and
a disagreement between them would be invisible: the request parser decides
what a run may be set up from, and the document parser decides what a stored
run is read back as. The store writes a document and immediately reads it back
through the second half before anything is moved into place, so a run that
could not be read is a run that is never written.

## What the request parser refuses

Unknown keys, above all. `run_id` is the one worth naming: a request that
could supply one would be a path from authored text to a run identity, and the
identity separation this slice protects would then depend on nobody trying.
There is no field for it, and a request that sends one is refused by name.

Missing fields and wrong types, because a missing seed is not a seed of zero
and a missing interval is not an interval of nothing. Nothing here defaults:
`D-2026-09-21-scenario-execution-contract` settles that an initial value with
no owner is refused when a definition is read, and a run input with no value
is the same fact one layer along.

Malformed intervals, in the four ways an interval can be malformed: an instant
that is not one, an end at or before its start, a length that is not a whole
number of minutes, and a length that is not a whole multiple of the timestep.
The last is the half-open time model rather than tidiness - a final step that
ran past the end of the interval would apply entries outside the interval the
run declared.

Units the contract does not know, and quantities the `invalid-rate` bound case
refuses. That case is `REFUSED_AT_PARSE` in `scenarios/execution.py` and this
is the second place it is a parse: the scenario parser refuses a negative
quantity in a non-negative dimension when the definition is read, and this
refuses the same thing when a run supplies one.

What it does NOT do is look anything up. Whether a Site is configured, whether
a scenario is saved, whether a profile exists, whether an entry falls inside
the interval - all of those are reads against a store or against a scenario,
and they belong to the service, in exactly the parser/service split the
scenario domain already uses for its target-site declaration.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, NoReturn

from assetops_contracts.control import DISCRETE_UNIT as DISCRETE_VALUE_UNIT
from assetops_contracts.execution_contract import MODEL_NEED_ONLY_UNITS
from assetops_contracts.observation import device_resolution

from assetops_backend.document_bounds import DocumentLimits, reject_oversized
from assetops_backend.runs.identity import validate_run_id
from assetops_backend.runs.models import (
    BLOCKING_REASON_KINDS,
    FROZEN_INPUT_ANSWERERS,
    RUN_EXECUTION_STATUSES,
    RUN_LIFECYCLE_STATUSES,
    BlockingReason,
    DeterministicIdentity,
    FrozenCause,
    FrozenDeclaredBound,
    FrozenForcing,
    FrozenInitializationInput,
    FrozenReportingPathCondition,
    FrozenInterval,
    FrozenModelNeed,
    FrozenBusAttachment,
    FrozenSiteControl,
    FrozenObservationBinding,
    FrozenParameter,
    FrozenProfileBinding,
    FrozenPublicationIdentity,
    FrozenSignalResolution,
    FrozenScenarioBinding,
    FrozenSignalMapping,
    FrozenSiteBinding,
    FrozenTemplateLineage,
    RegisteredBasis,
    SimulationRun,
    UnsupportedOptionalInput,
)
from assetops_backend.runs.ports import RunConfigurationInvalid
from assetops_backend.runs.refusals import refuse
from assetops_backend.scenarios.execution import (
    CANONICAL_UNITS,
    EXECUTION_CONTRACT_VERSION,
    NON_NEGATIVE_DIMENSIONS,
)
from assetops_backend.scenarios.identity import validate_scenario_id
from assetops_backend.scenarios.models import (
    BOUND_KINDS,
    CADENCE_OWNERSHIP,
    ENTRY_ISSUERS,
    EXECUTION_REQUIREMENTS,
    OBSERVATION_SOURCE_KINDS,
    PARAMETER_UNITS,
    STATE_EFFECT_DIRECTIONS,
    TIMING_SHAPES,
)
from assetops_backend.scenarios.ports import ScenarioConfigurationInvalid
from assetops_backend.sites.identity import validate_site_id
from assetops_backend.sites.ports import SiteConfigurationInvalid
from assetops_backend.state_refs import parse_state_ref

REQUEST_KEYS = frozenset(
    {
        "site_id",
        "foundation_version",
        "scenario_id",
        "scenario_version",
        "interval",
        "timestep_minutes",
        "seed",
        "model_profile",
        "publication_profile",
        "run_inputs",
        # S2-01a, API-only: what configuration had been recorded by this
        # instant. Optional; a registered Site's setup defaults it to the
        # server's now and freezes the resolved value.
        "knowledge_at",
    }
)

INTERVAL_KEYS = frozenset({"start_time", "end_time"})
PROFILE_KEYS = frozenset({"profile_id", "profile_version"})
TEMPLATE_LINEAGE_KEYS = frozenset({"template_id", "template_version"})
RUN_INPUT_KEYS = frozenset({"parameter_id", "value", "unit"})

#: An ISO-8601 instant in UTC, spelled the one way the rest of the product
#: spells one. A run interval is a product fact, so it has one spelling rather
#: than whatever a client happened to emit.
INSTANT_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

#: T025a. How a discrete member is spelled in a frozen run.
DISCRETE_MEMBER = re.compile(r"[A-Z][A-Z_]*")
PROFILE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

#: Bounds, so a request cannot ask for a run nothing could walk. Each is a
#: limit rather than a default: nothing here supplies a value, it only refuses
#: one that is outside.
MIN_TIMESTEP_MINUTES = 1
MAX_TIMESTEP_MINUTES = 1440
MAX_INTERVAL_MINUTES = 100_000
MAX_SEED = 2**31 - 1
MAX_VERSION = 10_000
MAX_RUN_INPUTS = 64

#: A run document is written by the product and read back by the product, so
#: it is bounded for the same reason every other stored document is: a
#: defective or hand-edited file must not be expanded in memory first.
RUN_DOCUMENT_LIMITS = DocumentLimits(
    max_nodes=8_000, max_text_length=200_000, max_nesting_depth=12
)

TIMESTEP_RULE = (
    f"A timestep is a whole number of minutes between {MIN_TIMESTEP_MINUTES} "
    f"and {MAX_TIMESTEP_MINUTES}, and the interval must be a whole multiple "
    "of it so that no step runs past the end of the interval."
)

INTERVAL_RULE = (
    "An interval is two UTC instants spelled as YYYY-MM-DDTHH:MM:SSZ, the "
    "end after the start, covering a whole number of minutes. It is "
    "half-open: the run covers its start instant up to but not including its "
    "end instant."
)

SEED_RULE = f"A seed is a whole number between 0 and {MAX_SEED}."


# --- The request ------------------------------------------------------------


@dataclass(frozen=True)
class RunInputValue:
    """One value the run supplies because the scenario says the run owns it."""

    parameter_id: str
    value: float
    unit: str


@dataclass(frozen=True)
class RunSetupRequest:
    """A structurally valid setup request, before anything is looked up.

    It carries no `run_id`, and that is structural: there is no field here for
    one, so no request can carry one however it is spelled.
    """

    site_id: str
    foundation_version: int
    scenario_id: str
    scenario_version: int
    start_time: str
    end_time: str
    duration_minutes: int
    timestep_minutes: int
    seed: int
    model_profile_id: str
    model_profile_version: int
    publication_profile_id: str
    publication_profile_version: int
    run_inputs: tuple[RunInputValue, ...]
    #: S2-01a: optional, registered Sites only. A UTC instant, or None for
    #: "the server's now at setup".
    knowledge_at: str | None = None


def parse_run_setup_request(request: Any) -> RunSetupRequest:
    """Validate one setup request into a domain record.

    Raises:
        RunSetupRefused: the request is not a well-formed setup request. No
            run identity is allocated and nothing is written.
    """
    if not isinstance(request, Mapping):
        raise refuse(
            "REQUEST_INVALID",
            "A run setup request must be an object declaring "
            f"{sorted(REQUEST_KEYS)}.",
        )

    reject_oversized(
        request,
        source="the run setup request",
        limits=RUN_DOCUMENT_LIMITS,
        invalid=_refuse_request,
        document_kind="Run setup request",
    )

    _reject_unknown_request_keys(request)

    site_id = _identity(
        validate_site_id,
        request.get("site_id"),
        SiteConfigurationInvalid,
        where="'site_id'",
    )
    scenario_id = _identity(
        validate_scenario_id,
        request.get("scenario_id"),
        ScenarioConfigurationInvalid,
        where="'scenario_id'",
    )

    foundation_version = _version(
        request.get("foundation_version"), where="'foundation_version'"
    )
    scenario_version = _version(
        request.get("scenario_version"), where="'scenario_version'"
    )

    timestep_minutes = _bounded_int(
        request.get("timestep_minutes"),
        where="'timestep_minutes'",
        minimum=MIN_TIMESTEP_MINUTES,
        maximum=MAX_TIMESTEP_MINUTES,
        rule=TIMESTEP_RULE,
    )
    seed = _bounded_int(
        request.get("seed"),
        where="'seed'",
        minimum=0,
        maximum=MAX_SEED,
        rule=SEED_RULE,
    )

    start_time, end_time, duration_minutes = _parse_interval(
        request.get("interval"), timestep_minutes=timestep_minutes
    )

    model_profile_id, model_profile_version = _parse_profile_selection(
        request.get("model_profile"), where="'model_profile'"
    )
    (
        publication_profile_id,
        publication_profile_version,
    ) = _parse_profile_selection(
        request.get("publication_profile"), where="'publication_profile'"
    )

    return RunSetupRequest(
        site_id=site_id,
        foundation_version=foundation_version,
        scenario_id=scenario_id,
        scenario_version=scenario_version,
        start_time=start_time,
        end_time=end_time,
        duration_minutes=duration_minutes,
        timestep_minutes=timestep_minutes,
        seed=seed,
        model_profile_id=model_profile_id,
        model_profile_version=model_profile_version,
        publication_profile_id=publication_profile_id,
        publication_profile_version=publication_profile_version,
        run_inputs=_parse_run_inputs(request.get("run_inputs")),
        knowledge_at=_knowledge_at(request.get("knowledge_at")),
    )


def _knowledge_at(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not INSTANT_PATTERN.match(value):
        raise refuse(
            "REQUEST_INVALID",
            "'knowledge_at' is optional and, when given, a UTC instant spelled "
            "as YYYY-MM-DDTHH:MM:SSZ: what configuration had been recorded by then.",
        )
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise refuse(
            "REQUEST_INVALID", f"'knowledge_at' {value!r} is not a real instant."
        ) from error
    return value


def _refuse_request(message: str) -> NoReturn:
    raise refuse("REQUEST_INVALID", message)


def _reject_unknown_request_keys(request: Mapping[str, Any]) -> None:
    unknown = sorted(set(request) - REQUEST_KEYS)
    if not unknown:
        return

    if "run_id" in unknown:
        raise refuse(
            "REQUEST_INVALID",
            "A run setup request may not supply 'run_id'. A run identity is "
            "allocated by run setup and is never taken from a request, from "
            "a site ID, or from a scenario label.",
        )

    raise refuse(
        "REQUEST_INVALID",
        f"A run setup request does not accept {unknown}. It declares "
        f"{sorted(REQUEST_KEYS)}.",
    )


def _identity(
    validator: Any, value: Any, error: type[Exception], *, where: str
) -> str:
    """Borrow another domain's identity rule and translate its refusal.

    A run names a Site and a scenario, so it must use their rules for what one
    looks like; two answers to that would let a run name an identity neither
    domain could ever hold. The other domain's exception is translated here,
    at the point of use, so no foreign error escapes through the run surface.
    """
    try:
        return str(validator(value, where=where))
    except error as failure:
        raise refuse("REQUEST_INVALID", str(failure)) from failure


def _version(value: Any, *, where: str) -> int:
    # `isinstance(True, int)` is True, so compare the type directly: a boolean
    # must not become version 1.
    if type(value) is not int or not 1 <= value <= MAX_VERSION:
        raise refuse(
            "REQUEST_INVALID",
            f"{where} must be a whole number between 1 and {MAX_VERSION}. A "
            "run freezes the exact version it was set up against, so the "
            "version is named rather than resolved to whatever is latest.",
        )
    return value


def _bounded_int(
    value: Any, *, where: str, minimum: int, maximum: int, rule: str
) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise refuse("REQUEST_INVALID", f"{where} is not usable. {rule}")
    return value


def _parse_interval(
    raw: Any, *, timestep_minutes: int
) -> tuple[str, str, int]:
    if not isinstance(raw, Mapping):
        raise refuse(
            "INTERVAL_INVALID",
            f"'interval' must be an object declaring {sorted(INTERVAL_KEYS)}. "
            f"{INTERVAL_RULE}",
        )

    unknown = sorted(set(raw) - INTERVAL_KEYS)
    if unknown:
        raise refuse(
            "INTERVAL_INVALID",
            f"'interval' does not accept {unknown}. {INTERVAL_RULE}",
        )

    start_time = _instant(raw.get("start_time"), where="'interval.start_time'")
    end_time = _instant(raw.get("end_time"), where="'interval.end_time'")

    start = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    end = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )

    seconds = (end - start).total_seconds()
    if seconds <= 0:
        raise refuse(
            "INTERVAL_INVALID",
            f"The interval ends at or before it starts. {INTERVAL_RULE}",
        )

    if seconds % 60 != 0:
        raise refuse(
            "INTERVAL_INVALID",
            f"The interval is not a whole number of minutes. {INTERVAL_RULE}",
        )

    duration_minutes = int(seconds // 60)

    if duration_minutes > MAX_INTERVAL_MINUTES:
        raise refuse(
            "INTERVAL_INVALID",
            f"The interval covers {duration_minutes} minutes, above the "
            f"limit of {MAX_INTERVAL_MINUTES}.",
        )

    if duration_minutes % timestep_minutes != 0:
        raise refuse(
            "INTERVAL_INVALID",
            f"The interval covers {duration_minutes} minutes, which is not a "
            f"whole multiple of the {timestep_minutes} minute timestep. "
            f"{TIMESTEP_RULE}",
        )

    return start_time, end_time, duration_minutes


def _instant(value: Any, *, where: str) -> str:
    if not isinstance(value, str) or not INSTANT_PATTERN.match(value):
        raise refuse(
            "INTERVAL_INVALID",
            f"{where} is not a UTC instant. {INTERVAL_RULE}",
        )
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise refuse(
            "INTERVAL_INVALID",
            f"{where} {value!r} is not a real instant. {INTERVAL_RULE}",
        ) from error
    return value


def _parse_profile_selection(raw: Any, *, where: str) -> tuple[str, int]:
    if not isinstance(raw, Mapping):
        raise refuse(
            "REQUEST_INVALID",
            f"{where} must be an object declaring {sorted(PROFILE_KEYS)}. A "
            "run freezes which versioned profile answered for it.",
        )

    unknown = sorted(set(raw) - PROFILE_KEYS)
    if unknown:
        raise refuse(
            "REQUEST_INVALID", f"{where} does not accept {unknown}."
        )

    profile_id = raw.get("profile_id")
    if not isinstance(profile_id, str) or not PROFILE_ID_PATTERN.match(
        profile_id
    ):
        raise refuse(
            "REQUEST_INVALID",
            f"{where}.profile_id {profile_id!r} is not a profile identity. "
            "Use lower-case words separated by hyphens.",
        )

    return profile_id, _version(
        raw.get("profile_version"), where=f"{where}.profile_version"
    )


def _parse_run_inputs(raw: Any) -> tuple[RunInputValue, ...]:
    """The values the run supplies, each one explicit.

    An empty list is a real answer and the shipped Fuel Loss Event's answer: it
    declares no value the run owns. A missing list is not the same thing, and
    is refused, because a request that forgot the field and a request that says
    there are none must not be the same request.
    """
    if not isinstance(raw, list):
        raise refuse(
            "REQUEST_INVALID",
            "'run_inputs' must be a list, and an empty list when the scenario "
            "declares no value the run owns. A missing list and an empty one "
            "are different statements.",
        )

    if len(raw) > MAX_RUN_INPUTS:
        raise refuse(
            "REQUEST_INVALID",
            f"'run_inputs' holds {len(raw)} values, above the limit of "
            f"{MAX_RUN_INPUTS}.",
        )

    values: list[RunInputValue] = []
    seen: set[str] = set()

    for index, entry in enumerate(raw):
        where = f"'run_inputs[{index}]'"
        if not isinstance(entry, Mapping):
            raise refuse(
                "REQUEST_INVALID",
                f"{where} must be an object declaring {sorted(RUN_INPUT_KEYS)}.",
            )

        unknown = sorted(set(entry) - RUN_INPUT_KEYS)
        if unknown:
            raise refuse(
                "REQUEST_INVALID", f"{where} does not accept {unknown}."
            )

        parameter_id = entry.get("parameter_id")
        if not isinstance(parameter_id, str) or not PROFILE_ID_PATTERN.match(
            parameter_id
        ):
            raise refuse(
                "REQUEST_INVALID",
                f"{where}.parameter_id {parameter_id!r} is not a parameter "
                "identity.",
            )

        if parameter_id in seen:
            raise refuse(
                "REQUEST_INVALID",
                f"{where}.parameter_id {parameter_id!r} is supplied twice. "
                "Two values for one parameter are two answers to one "
                "question.",
            )
        seen.add(parameter_id)

        values.append(
            RunInputValue(
                parameter_id=parameter_id,
                value=_quantity(entry.get("value"), where=where),
                unit=_unit(entry.get("unit"), where=where),
            )
        )

    return tuple(values)


def _quantity(value: Any, *, where: str) -> float:
    if type(value) not in (int, float) or isinstance(value, bool):
        raise refuse(
            "REQUEST_INVALID",
            f"{where}.value must be a number. A run supplies the value the "
            "scenario says it owns; there is no default for one.",
        )
    if not math.isfinite(float(value)):
        raise refuse(
            "UNIT_INVALID",
            f"{where}.value is not a finite quantity. The invalid-rate bound "
            "case refuses a quantity that is infinite or not a number when it "
            "is read, so no run and no kernel ever sees one.",
        )
    return float(value)


def _unit(value: Any, *, where: str) -> str:
    if value not in PARAMETER_UNITS:
        raise refuse(
            "UNIT_INVALID",
            f"{where}.unit {value!r} is not a unit this contract knows. The "
            f"units are {sorted(PARAMETER_UNITS)}.",
        )
    return str(value)


def reject_unusable_quantity(value: float, unit: str, *, where: str) -> None:
    """Refuse a negative quantity in a dimension where none is meaningful.

    The `invalid-rate` bound case in `scenarios/execution.py` is the one of
    four decidable without executing anything, and it is `REFUSED_AT_PARSE`.
    The scenario parser applies it when a definition is read; this applies the
    same rule to a value a run supplies, so the two cannot disagree about
    whether minus one hundred litres is an input.
    """
    dimension = CANONICAL_UNITS[unit].dimension
    if dimension in NON_NEGATIVE_DIMENSIONS and value < 0:
        raise refuse(
            "UNIT_INVALID",
            f"{where} is {value} {unit}, and a {dimension.lower().replace('_', ' ')} "
            "cannot be negative. The invalid-rate bound case refuses it when "
            "it is read rather than clamping it later.",
        )


# --- The stored document ----------------------------------------------------
#
# A run is written by the product and read back by the product, and it is
# still validated on the way in. The store writes, reads back through
# `parse_run_document`, and compares the result with the record it was given
# before anything is moved into place, so what lands in the store is provably
# what the service produced rather than whatever the writer emitted.


def _render_template_lineage(
    lineage: FrozenTemplateLineage | None,
) -> dict[str, Any]:
    if lineage is None:
        return {}
    return {
        "template_lineage": {
            "template_id": lineage.template_id,
            "template_version": lineage.template_version,
        }
    }


def _parse_template_lineage(
    site: Mapping[str, Any],
) -> FrozenTemplateLineage | None:
    """Lineage as frozen, or `None` when this run never recorded it.

    Absent means a run persisted before T025g: "not recorded", never inferred.
    Present means both keys, each a value or null together; a half-recorded
    lineage is a defect in the document, not an answer.
    """
    if "template_lineage" not in site:
        return None
    raw = _mapping(site.get("template_lineage"), where="site.template_lineage")
    unknown = sorted(str(key) for key in set(raw) - TEMPLATE_LINEAGE_KEYS)
    missing = sorted(TEMPLATE_LINEAGE_KEYS - set(raw))
    if unknown or missing:
        raise _bad(
            "'site.template_lineage' must declare exactly "
            f"{sorted(TEMPLATE_LINEAGE_KEYS)} in a run document."
        )
    template_id = _optional_text(raw, "template_id", where="site.template_lineage")
    template_version = _optional_whole(
        raw, "template_version", where="site.template_lineage"
    )
    if (template_id is None) != (template_version is None):
        raise _bad(
            "'site.template_lineage' must name a template and its version "
            "together, or neither, in a run document."
        )
    return FrozenTemplateLineage(
        template_id=template_id, template_version=template_version
    )


def render_run_document(record: SimulationRun) -> dict[str, Any]:
    """Render a run record as the document shape the store holds."""
    identity = record.deterministic_identity
    return {
        "run_id": record.run_id,
        "lifecycle_status": record.lifecycle_status,
        "execution_status": record.execution_status,
        "created_at": record.created_at,
        "deterministic_identity": {
            "site": {
                "site_id": identity.site.site_id,
                "foundation_version": identity.site.foundation_version,
                "foundation_valid_from": identity.site.foundation_valid_from,
                "site_type": identity.site.site_type,
                "timezone": identity.site.timezone,
                # Absent for a run frozen before T025g, so its stored document
                # round-trips unchanged and reads back as "not recorded".
                **_render_template_lineage(identity.site.template_lineage),
            },
            "scenario": {
                "scenario_id": identity.scenario.scenario_id,
                "scenario_version": identity.scenario.scenario_version,
                "resolved_parameters": [
                    {
                        "parameter_id": parameter.parameter_id,
                        "value": parameter.value,
                        "unit": parameter.unit,
                        "answered_by": parameter.answered_by,
                    }
                    for parameter in identity.scenario.resolved_parameters
                ],
                # W2-02: cold runs only; omitted (never null) for older runs.
                **_render_present(scenario_sha256=identity.scenario.scenario_sha256),
            },
            "interval": {
                "start_time": identity.interval.start_time,
                "end_time": identity.interval.end_time,
                "duration_minutes": identity.interval.duration_minutes,
                "timestep_minutes": identity.interval.timestep_minutes,
            },
            "seed": identity.seed,
            "profiles": {
                "model_profile_id": identity.profiles.model_profile_id,
                "model_profile_version": identity.profiles.model_profile_version,
                "publication_profile_id": (
                    identity.profiles.publication_profile_id
                ),
                "publication_profile_version": (
                    identity.profiles.publication_profile_version
                ),
                "execution_contract_version": (
                    identity.profiles.execution_contract_version
                ),
                **_render_present(
                    observation_profile_id=identity.profiles.observation_profile_id,
                    observation_profile_version=identity.profiles.observation_profile_version,
                    observation_sha256=identity.profiles.observation_sha256,
                ),
            },
            "initialization_inputs": [
                {
                    # The ADDRESS, in the field that used to hold a bare key.
                    # One field rather than three because the address is one
                    # declaration: a scope and a selector in separate fields
                    # could be written to contradict each other, and a
                    # document that says two things has to be adjudicated by
                    # whoever reads it next. A run frozen before T020A1
                    # carries a bare key here and still reads back, as an
                    # unqualified component reference, which is what it was.
                    "state_key": item.addressed_key,
                    "parameter_id": item.parameter_id,
                    "value": item.value,
                    "unit": item.unit,
                    "canonical_value": item.canonical_value,
                    "canonical_unit": item.canonical_unit,
                    "dimension": item.dimension,
                    "answered_by": item.answered_by,
                    "answered_by_detail": item.answered_by_detail,
                }
                for item in identity.initialization_inputs
            ],
            # The causal projection, frozen since T021's review. A run used to
            # carry the values a scenario declared and nothing about when they
            # act, so the same persisted run executed against the same document
            # version with one offset moved produced a different trajectory.
            "causes": [
                {
                    "state_key": item.addressed_key,
                    "event_id": item.event_id,
                    "direction": item.direction,
                    "parameter_id": item.parameter_id,
                    "canonical_value": item.canonical_value,
                    "canonical_unit": item.canonical_unit,
                    "dimension": item.dimension,
                    "timing_shape": item.timing_shape,
                    "offset_minutes": item.offset_minutes,
                    "duration_minutes": item.duration_minutes,
                }
                for item in identity.causes
            ],
            "forcings": [
                {
                    "state_key": item.addressed_key,
                    "event_id": item.event_id,
                    "parameter_id": item.parameter_id,
                    "canonical_value": item.canonical_value,
                    "canonical_unit": item.canonical_unit,
                    "dimension": item.dimension,
                    "timing_shape": item.timing_shape,
                    "offset_minutes": item.offset_minutes,
                    "duration_minutes": item.duration_minutes,
                    "execution_requirement": item.execution_requirement,
                    **(
                        {"issued_by": item.issued_by}
                        if item.issued_by is not None
                        else {}
                    ),
                }
                for item in identity.forcings
            ],
            "declared_bounds": [
                {
                    "state_key": item.addressed_key,
                    "bound_kind": item.bound_kind,
                    "source_state_key": item.source_addressed_key,
                    "source_parameter_id": item.source_parameter_id,
                }
                for item in identity.declared_bounds
            ],
            "reporting_path_conditions": [
                {
                    "state_key": item.addressed_key,
                    "event_id": item.event_id,
                    "timing_shape": item.timing_shape,
                    "offset_minutes": item.offset_minutes,
                    "duration_minutes": item.duration_minutes,
                }
                for item in identity.reporting_path_conditions
            ],
            "observation_bindings": [
                {
                    "source_id": item.source_id,
                    "source_kind": item.source_kind,
                    "device_id": item.device_id,
                    "signal_id": item.signal_id,
                    "cadence_ownership": item.cadence_ownership,
                    "cadence_minutes": item.cadence_minutes,
                }
                for item in identity.observation_bindings
            ],
            "publication": {
                "simulator_source_id": identity.publication.simulator_source_id,
                "gateway_id": identity.publication.gateway_id,
            },
            "signal_mappings": [
                {
                    "mapping_id": item.mapping_id,
                    "device_id": item.device_id,
                    "signal_id": item.signal_id,
                    "component_id": item.component_id,
                }
                for item in identity.signal_mappings
            ],
            "intervention_history": list(identity.intervention_history),
            # T024, execution contract 9: the model-owned Foundation needs and
            # the effective Site Controls, each with its provenance.
            "model_needs": [
                {
                    "state_key": item.addressed_key,
                    "property_key": item.property_key,
                    "value": item.value,
                    "unit": item.unit,
                    "canonical_value": item.canonical_value,
                    "canonical_unit": item.canonical_unit,
                    "dimension": item.dimension,
                    "declared_by": item.declared_by,
                    "answered_by": item.answered_by,
                    "answered_by_detail": item.answered_by_detail,
                    "foundation_version": item.foundation_version,
                    "foundation_valid_from": item.foundation_valid_from,
                    "property_source": item.property_source,
                    "property_source_version": item.property_source_version,
                }
                for item in identity.model_needs
            ],
            "site_controls": [
                {
                    "control_key": item.control_key,
                    "members": (
                        None if item.members is None else list(item.members)
                    ),
                    "declared_by": item.declared_by,
                    "answered_by": item.answered_by,
                    "answered_by_detail": item.answered_by_detail,
                    "foundation_version": item.foundation_version,
                    "foundation_valid_from": item.foundation_valid_from,
                    "source": item.source,
                    "source_version": item.source_version,
                }
                for item in identity.site_controls
            ],
            "bus_attachments": [
                {
                    "role": item.role,
                    "component_id": item.component_id,
                    "via_component_id": item.via_component_id,
                    "bus_component_id": item.bus_component_id,
                    "connection_ids": list(item.connection_ids),
                }
                for item in identity.bus_attachments
            ],
            # S2-01b: written only when frozen, so every earlier run's stored
            # document keeps its exact bytes.
            **(
                {
                    "signal_resolutions": [
                        {
                            "device_id": item.device_id,
                            "signal_id": item.signal_id,
                            "unit": item.unit,
                            "resolution": item.resolution,
                        }
                        for item in identity.signal_resolutions
                    ]
                }
                if identity.signal_resolutions
                else {}
            ),
        },
        "blocking_reasons": [
            {
                "kind": reason.kind,
                "subject": reason.subject,
                "statement": reason.statement,
            }
            for reason in record.blocking_reasons
        ],
        "unsupported_optional_inputs": [
            {
                "state_key": item.addressed_key,
                "execution_role": item.execution_role,
                "statement": item.statement,
            }
            for item in record.unsupported_optional_inputs
        ],
        # Absent for a legacy YAML Site's run, so its stored document
        # round-trips unchanged.
        **_render_registered_basis(record.registered_basis),
    }


def _render_registered_basis(basis: RegisteredBasis | None) -> dict[str, Any]:
    if basis is None:
        return {}
    return {
        "registered_basis": {
            "tenant_id": basis.tenant_id,
            "site_record_id": basis.site_record_id,
            "foundation_revision_id": basis.foundation_revision_id,
            "foundation_version": basis.foundation_version,
            "foundation_valid_from": basis.foundation_valid_from,
            "foundation_valid_to": basis.foundation_valid_to,
            "foundation_content_sha256": basis.foundation_content_sha256,
            "binding_set_id": basis.binding_set_id,
            "binding_set_revision_id": basis.binding_set_revision_id,
            "binding_set_version": basis.binding_set_version,
            "binding_valid_from": basis.binding_valid_from,
            "binding_valid_to": basis.binding_valid_to,
            "snapshot_schema": basis.snapshot_schema,
            "snapshot_sha256": basis.snapshot_sha256,
            "snapshot_canonical": basis.snapshot_canonical,
            "source_start": basis.source_start,
            "knowledge_at": basis.knowledge_at,
            "site_display_name": basis.site_display_name,
            "selection": basis.selection,
            "current_registration_gaps": list(basis.current_registration_gaps),
        }
    }


REGISTERED_BASIS_KEYS = frozenset(
    {
        "tenant_id",
        "site_record_id",
        "foundation_revision_id",
        "foundation_version",
        "foundation_valid_from",
        "foundation_valid_to",
        "foundation_content_sha256",
        "binding_set_id",
        "binding_set_revision_id",
        "binding_set_version",
        "binding_valid_from",
        "binding_valid_to",
        "snapshot_schema",
        "snapshot_sha256",
        "snapshot_canonical",
        "source_start",
        "knowledge_at",
        "site_display_name",
        "selection",
        "current_registration_gaps",
    }
)
#: Whole-second UTC for valid times; `knowledge_at` may carry the fraction of
#: the clock reading it was resolved from.
_BASIS_INSTANT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")


def _parse_registered_basis(raw: Any, *, source: str) -> RegisteredBasis:
    where = "registered_basis"
    basis = _mapping(raw, where="run")
    unknown = sorted(set(basis) - REGISTERED_BASIS_KEYS)
    missing = sorted(REGISTERED_BASIS_KEYS - set(basis))
    if unknown or missing:
        raise _bad(
            f"'run.registered_basis' in {source} has unknown keys {unknown} "
            f"or lacks {missing}."
        )

    def instant(key: str, *, optional: bool = False) -> str | None:
        value = basis.get(key)
        if value is None and optional:
            return None
        if not isinstance(value, str) or not _BASIS_INSTANT.match(value):
            raise _bad(f"'{where}.{key}' in {source} is not a UTC instant.")
        return value

    gaps = basis.get("current_registration_gaps")
    if not isinstance(gaps, list) or not all(isinstance(g, str) for g in gaps):
        raise _bad(f"'{where}.current_registration_gaps' in {source} must be a list of codes.")
    try:
        return RegisteredBasis(
            tenant_id=_text(basis, "tenant_id", where=where),
            site_record_id=_text(basis, "site_record_id", where=where),
            foundation_revision_id=_text(basis, "foundation_revision_id", where=where),
            foundation_version=_whole(basis, "foundation_version", where=where),
            foundation_valid_from=instant("foundation_valid_from"),
            foundation_valid_to=instant("foundation_valid_to", optional=True),
            foundation_content_sha256=_text(basis, "foundation_content_sha256", where=where),
            binding_set_id=_text(basis, "binding_set_id", where=where),
            binding_set_revision_id=_text(basis, "binding_set_revision_id", where=where),
            binding_set_version=_whole(basis, "binding_set_version", where=where),
            binding_valid_from=instant("binding_valid_from"),
            binding_valid_to=instant("binding_valid_to", optional=True),
            snapshot_schema=_text(basis, "snapshot_schema", where=where),
            snapshot_sha256=_text(basis, "snapshot_sha256", where=where),
            snapshot_canonical=_text(basis, "snapshot_canonical", where=where),
            source_start=instant("source_start"),
            knowledge_at=instant("knowledge_at"),
            site_display_name=_text(basis, "site_display_name", where=where),
            selection=_text(basis, "selection", where=where),
            current_registration_gaps=tuple(gaps),
        )
    except ValueError as error:
        raise _bad(f"{error} Read from {source}.") from error


def _bad(message: str) -> RunConfigurationInvalid:
    return RunConfigurationInvalid(message)


def _raise_invalid(message: str) -> NoReturn:
    raise _bad(message)


def _mapping(raw: Any, *, where: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise _bad(f"'{where}' must be an object in a run document.")
    return raw


def _text(raw: Mapping[str, Any], key: str, *, where: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise _bad(f"'{where}.{key}' must be non-empty text in a run document.")
    return value


def _optional_text(raw: Mapping[str, Any], key: str, *, where: str) -> str | None:
    value = raw.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise _bad(
            f"'{where}.{key}' must be non-empty text or absent in a run "
            "document."
        )
    return value


def _whole(raw: Mapping[str, Any], key: str, *, where: str) -> int:
    value = raw.get(key)
    if type(value) is not int:
        raise _bad(f"'{where}.{key}' must be a whole number in a run document.")
    return value


def _optional_whole(
    raw: Mapping[str, Any], key: str, *, where: str
) -> int | None:
    value = raw.get(key)
    if value is None:
        return None
    if type(value) is not int:
        raise _bad(
            f"'{where}.{key}' must be a whole number or absent in a run "
            "document."
        )
    return value


def _optional_real(
    raw: Mapping[str, Any], key: str, *, where: str
) -> float | None:
    """A number, or nothing, and nothing is a real answer."""
    if raw.get(key) is None:
        return None
    return _real(raw, key, where=where)


def _real(raw: Mapping[str, Any], key: str, *, where: str) -> float:
    value = raw.get(key)
    if type(value) not in (int, float) or isinstance(value, bool):
        raise _bad(f"'{where}.{key}' must be a number in a run document.")
    if not math.isfinite(float(value)):
        raise _bad(f"'{where}.{key}' must be a finite number in a run document.")
    return float(value)


def _choice(
    raw: Mapping[str, Any], key: str, *, where: str, allowed: frozenset[str]
) -> str:
    value = _text(raw, key, where=where)
    if value not in allowed:
        raise _bad(
            f"'{where}.{key}' must be one of {sorted(allowed)} in a run "
            f"document, got {value!r}."
        )
    return value


def _entries(raw: Mapping[str, Any], key: str, *, where: str) -> list[Any]:
    value = raw.get(key)
    if not isinstance(value, list):
        raise _bad(f"'{where}.{key}' must be a list in a run document.")
    return value


def parse_run_document(document: Any, *, source: str) -> SimulationRun:
    """Validate one stored run document into a domain record.

    Strict in the same way every other parser in this product is strict: the
    document is the product's own output, and a hand-edited store must not be
    able to introduce a run identity, a status, or an answerer the product
    would never have written.

    Raises:
        RunConfigurationInvalid: the document is not a valid run.
    """
    if not isinstance(document, Mapping):
        raise _bad(f"A run document must be a mapping in {source}.")

    reject_oversized(
        document,
        source=source,
        limits=RUN_DOCUMENT_LIMITS,
        invalid=_raise_invalid,
        document_kind="Run document",
    )

    run_id = validate_run_id(document.get("run_id"), where=f"run_id in {source}")
    lifecycle_status = _choice(
        document, "lifecycle_status", where="run", allowed=RUN_LIFECYCLE_STATUSES
    )
    execution_status = _choice(
        document, "execution_status", where="run", allowed=RUN_EXECUTION_STATUSES
    )
    created_at = _text(document, "created_at", where="run")
    if not INSTANT_PATTERN.match(created_at):
        raise _bad(
            f"'run.created_at' must be a UTC instant spelled as "
            f"YYYY-MM-DDTHH:MM:SSZ in {source}."
        )

    identity = _parse_identity(
        _mapping(document.get("deterministic_identity"), where="run")
    )

    reasons = tuple(
        _parse_blocking_reason(entry)
        for entry in _entries(document, "blocking_reasons", where="run")
    )

    optional = tuple(
        _parse_unsupported_optional_input(entry)
        for entry in _entries(
            document, "unsupported_optional_inputs", where="run"
        )
    )

    try:
        return SimulationRun(
            run_id=run_id,
            lifecycle_status=lifecycle_status,
            execution_status=execution_status,
            created_at=created_at,
            deterministic_identity=identity,
            blocking_reasons=reasons,
            unsupported_optional_inputs=optional,
            registered_basis=(
                None
                if document.get("registered_basis") is None
                else _parse_registered_basis(document["registered_basis"], source=source)
            ),
        )
    except ValueError as error:
        # The record's own invariant: a run is READY exactly when it carries
        # no blocking reason. A stored document that disagrees is invalid
        # rather than a run in a state the product can produce.
        raise _bad(f"{error} Read from {source}.") from error


def _parse_blocking_reason(entry: Any) -> BlockingReason:
    raw = _mapping(entry, where="blocking_reason")
    return BlockingReason(
        kind=_choice(
            raw, "kind", where="blocking_reason", allowed=BLOCKING_REASON_KINDS
        ),
        subject=_text(raw, "subject", where="blocking_reason"),
        statement=_text(raw, "statement", where="blocking_reason"),
    )


def _parse_unsupported_optional_input(entry: Any) -> UnsupportedOptionalInput:
    raw = _mapping(entry, where="unsupported_optional_input")
    return UnsupportedOptionalInput(
        # The address, in the field that used to hold a bare key, exactly as
        # the initialization row does it. A record written before T020A1
        # carries a bare key and reads back as the unqualified component
        # reference it was.
        state_ref=parse_state_ref(
            raw.get("state_key"),
            where="unsupported_optional_input.state_key",
            source="a run document",
            invalid=_raise_invalid,
        ),
        execution_role=_text(
            raw, "execution_role", where="unsupported_optional_input"
        ),
        statement=_text(raw, "statement", where="unsupported_optional_input"),
    )


_SHA256_HEX = re.compile(r"[0-9a-f]{64}")
_COLD_PROFILE_KEYS = ("observation_profile_id", "observation_profile_version", "observation_sha256")


def _render_present(**fields: Any) -> dict[str, Any]:
    """W2-02: the cold identity keys a run writes only when it has them (omit, never null)."""
    return {key: value for key, value in fields.items() if value is not None}


def _parse_cold_identity(
    scenario: Mapping[str, Any], profiles: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """W2-02: the four cold identity keys are all present (a cold run) or all absent (every older run)."""
    present = ["scenario_sha256" in scenario] + [key in profiles for key in _COLD_PROFILE_KEYS]
    if not any(present):
        return {}, {}
    if not all(present):
        raise _bad(
            "a cold run freezes scenario_sha256, observation_profile_id, observation_profile_version "
            "and observation_sha256 together."
        )
    scenario_sha = _text(scenario, "scenario_sha256", where="scenario")
    observation_sha = _text(profiles, "observation_sha256", where="profiles")
    for name, value in (("scenario_sha256", scenario_sha), ("observation_sha256", observation_sha)):
        if not _SHA256_HEX.fullmatch(value):
            raise _bad(f"'{name}' is not a lowercase 64-hex SHA-256.")
    return {"scenario_sha256": scenario_sha}, {
        "observation_profile_id": _text(profiles, "observation_profile_id", where="profiles"),
        "observation_profile_version": _whole(profiles, "observation_profile_version", where="profiles"),
        "observation_sha256": observation_sha,
    }


def _parse_identity(raw: Mapping[str, Any]) -> DeterministicIdentity:
    site = _mapping(raw.get("site"), where="deterministic_identity")
    scenario = _mapping(raw.get("scenario"), where="deterministic_identity")
    interval = _mapping(raw.get("interval"), where="deterministic_identity")
    profiles = _mapping(raw.get("profiles"), where="deterministic_identity")
    publication = _mapping(
        raw.get("publication"), where="deterministic_identity"
    )

    # Read before the projection collections, because whether they are required
    # depends on it. A malformed version is refused here rather than defaulting,
    # which is what would decide the question by accident.
    contract_version = _whole(
        profiles, "execution_contract_version", where="profiles"
    )

    cold_scenario, cold_profile = _parse_cold_identity(scenario, profiles)

    history = _entries(raw, "intervention_history", where="deterministic_identity")
    for entry in history:
        if not isinstance(entry, str) or not entry:
            raise _bad(
                "'deterministic_identity.intervention_history' holds an entry "
                "that is not an identity."
            )

    return DeterministicIdentity(
        site=FrozenSiteBinding(
            site_id=_text(site, "site_id", where="site"),
            foundation_version=_whole(site, "foundation_version", where="site"),
            foundation_valid_from=_text(
                site, "foundation_valid_from", where="site"
            ),
            site_type=_text(site, "site_type", where="site"),
            timezone=_text(site, "timezone", where="site"),
            template_lineage=_parse_template_lineage(site),
        ),
        scenario=FrozenScenarioBinding(
            scenario_id=_text(scenario, "scenario_id", where="scenario"),
            scenario_version=_whole(
                scenario, "scenario_version", where="scenario"
            ),
            resolved_parameters=tuple(
                _parse_parameter(entry)
                for entry in _entries(
                    scenario, "resolved_parameters", where="scenario"
                )
            ),
            **cold_scenario,
        ),
        interval=FrozenInterval(
            start_time=_text(interval, "start_time", where="interval"),
            end_time=_text(interval, "end_time", where="interval"),
            duration_minutes=_whole(
                interval, "duration_minutes", where="interval"
            ),
            timestep_minutes=_whole(
                interval, "timestep_minutes", where="interval"
            ),
        ),
        seed=_whole(raw, "seed", where="deterministic_identity"),
        profiles=FrozenProfileBinding(
            model_profile_id=_text(profiles, "model_profile_id", where="profiles"),
            model_profile_version=_whole(
                profiles, "model_profile_version", where="profiles"
            ),
            publication_profile_id=_text(
                profiles, "publication_profile_id", where="profiles"
            ),
            publication_profile_version=_whole(
                profiles, "publication_profile_version", where="profiles"
            ),
            execution_contract_version=contract_version,
            **cold_profile,
        ),
        initialization_inputs=tuple(
            _parse_initialization_input(entry)
            for entry in _entries(
                raw, "initialization_inputs", where="deterministic_identity"
            )
        ),
        # Defaulting to empty when absent is what preserves readback of a run
        # frozen before the projection existed. It is safe only because
        # `refuse_incompatible_execution` refuses to execute a run frozen at
        # another contract version, so an empty projection can never be
        # mistaken for a run that declared no causes.
        causes=tuple(
            _parse_frozen_cause(entry)
            for entry in _projection_entries(
                raw, "causes", contract_version=contract_version
            )
        ),
        forcings=tuple(
            _parse_frozen_forcing(entry)
            for entry in _projection_entries(
                raw, "forcings", contract_version=contract_version
            )
        ),
        declared_bounds=tuple(
            _parse_frozen_declared_bound(entry)
            for entry in _projection_entries(
                raw, "declared_bounds", contract_version=contract_version
            )
        ),
        reporting_path_conditions=tuple(
            _parse_frozen_reporting_path_condition(entry)
            for entry in _projection_entries(
                raw,
                "reporting_path_conditions",
                contract_version=contract_version,
            )
        ),
        observation_bindings=tuple(
            _parse_observation_binding(entry)
            for entry in _entries(
                raw, "observation_bindings", where="deterministic_identity"
            )
        ),
        publication=FrozenPublicationIdentity(
            simulator_source_id=_optional_text(
                publication, "simulator_source_id", where="publication"
            ),
            gateway_id=_optional_text(
                publication, "gateway_id", where="publication"
            ),
        ),
        signal_mappings=tuple(
            _parse_signal_mapping(entry)
            for entry in _entries(
                raw, "signal_mappings", where="deterministic_identity"
            )
        ),
        intervention_history=tuple(history),
        # Required at this build's version and empty below it, by the same
        # rule as the causal projection: a version-9 record that omitted its
        # needs would execute an experiment it does not describe.
        model_needs=tuple(
            _parse_model_need(entry)
            for entry in _projection_entries(
                raw, "model_needs", contract_version=contract_version
            )
        ),
        site_controls=tuple(
            _parse_site_control(entry)
            for entry in _projection_entries(
                raw, "site_controls", contract_version=contract_version
            )
        ),
        # Optional at every version: a version-9 record written before the
        # arrangement was frozen reads back with none, and the model refuses
        # to execute it (its resolver requires every attachment) rather than
        # this parser refusing an owner's stored run.
        bus_attachments=tuple(
            _parse_bus_attachment(entry)
            for entry in (
                _entries(raw, "bus_attachments", where="deterministic_identity")
                if raw.get("bus_attachments") is not None
                else []
            )
        ),
        signal_resolutions=_parse_signal_resolutions(raw),
    )


def _parse_signal_resolutions(
    raw: Mapping[str, Any],
) -> tuple[FrozenSignalResolution, ...]:
    """S2-01b: the frozen device resolutions, absent on every earlier run.

    A stored list is never empty, because an empty one is not written; one
    that is would be a document this build did not write.
    """
    if raw.get("signal_resolutions") is None:
        return ()
    entries = _entries(raw, "signal_resolutions", where="deterministic_identity")
    if not entries:
        raise _bad(
            "'deterministic_identity.signal_resolutions' is written only when a "
            "resolution was frozen, so it is never an empty list."
        )
    frozen: list[FrozenSignalResolution] = []
    for entry in entries:
        item = _mapping(entry, where="signal_resolution")
        resolution = _text(item, "resolution", where="signal_resolution")
        try:
            device_resolution(resolution)
        except ValueError as error:
            raise _bad(f"'signal_resolution.resolution': {error}") from error
        frozen.append(
            FrozenSignalResolution(
                device_id=_text(item, "device_id", where="signal_resolution"),
                signal_id=_text(item, "signal_id", where="signal_resolution"),
                unit=_text(item, "unit", where="signal_resolution"),
                resolution=resolution,
            )
        )
    return tuple(frozen)

def _parse_model_need(entry: Any) -> FrozenModelNeed:
    """One model-owned Foundation need (T024), with its absent case checked."""
    raw = _mapping(entry, where="model_need")
    unit = _text(raw, "unit", where="model_need")
    if unit not in PARAMETER_UNITS and unit not in MODEL_NEED_ONLY_UNITS:
        raise _bad(f"'model_need.unit' {unit!r} is not a unit this contract knows.")
    value = _optional_real(raw, "value", where="model_need")
    canonical_value = _optional_real(raw, "canonical_value", where="model_need")
    if (value is None) != (canonical_value is None):
        raise _bad(
            "'model_need.value' and its canonical restatement are absent "
            "together or present together."
        )
    source = _optional_text(raw, "property_source", where="model_need")
    source_version = _optional_whole(
        raw, "property_source_version", where="model_need"
    )
    if (value is None) != (source is None) or (source is None) != (
        source_version is None
    ):
        raise _bad(
            "'model_need' carries a value exactly when it carries the "
            "property's source and source version: an answer is never frozen "
            "without the declaration that supplied it."
        )
    return FrozenModelNeed(
        state_ref=parse_state_ref(
            raw.get("state_key"),
            where="model_need.state_key",
            source="a run document",
            invalid=_raise_invalid,
        ),
        property_key=_text(raw, "property_key", where="model_need"),
        value=value,
        unit=unit,
        canonical_value=canonical_value,
        canonical_unit=_text(raw, "canonical_unit", where="model_need"),
        dimension=_text(raw, "dimension", where="model_need"),
        declared_by=_text(raw, "declared_by", where="model_need"),
        answered_by=_choice(
            raw, "answered_by", where="model_need", allowed=FROZEN_INPUT_ANSWERERS
        ),
        answered_by_detail=_text(raw, "answered_by_detail", where="model_need"),
        foundation_version=_whole(raw, "foundation_version", where="model_need"),
        foundation_valid_from=_text(
            raw, "foundation_valid_from", where="model_need"
        ),
        property_source=source,
        property_source_version=source_version,
    )


def _parse_bus_attachment(entry: Any) -> FrozenBusAttachment:
    """One component's attachment to the bus (T024 fix round)."""
    raw = _mapping(entry, where="bus_attachment")
    connections = raw.get("connection_ids")
    if (
        not isinstance(connections, list)
        or not connections
        or not all(isinstance(item, str) and item for item in connections)
    ):
        raise _bad(
            "'bus_attachment.connection_ids' is a non-empty list of declared "
            "connection identities."
        )
    return FrozenBusAttachment(
        role=_text(raw, "role", where="bus_attachment"),
        component_id=_text(raw, "component_id", where="bus_attachment"),
        via_component_id=_optional_text(
            raw, "via_component_id", where="bus_attachment"
        ),
        bus_component_id=_text(raw, "bus_component_id", where="bus_attachment"),
        connection_ids=tuple(connections),
    )


def _parse_site_control(entry: Any) -> FrozenSiteControl:
    """One effective Site Control (T024), ordered, with its absent case."""
    raw = _mapping(entry, where="site_control")
    members_raw = raw.get("members")
    members: tuple[str, ...] | None
    if members_raw is None:
        members = None
    else:
        if not isinstance(members_raw, list) or not members_raw or not all(
            isinstance(item, str) and item for item in members_raw
        ):
            raise _bad(
                "'site_control.members' is null or a non-empty ordered list of "
                "component identities."
            )
        if len(set(members_raw)) != len(members_raw):
            raise _bad("'site_control.members' names a component twice.")
        members = tuple(members_raw)
    source = _optional_text(raw, "source", where="site_control")
    source_version = _optional_whole(raw, "source_version", where="site_control")
    if (members is None) != (source is None) or (source is None) != (
        source_version is None
    ):
        raise _bad(
            "'site_control' carries members exactly when it carries the "
            "control's source and source version."
        )
    return FrozenSiteControl(
        control_key=_text(raw, "control_key", where="site_control"),
        members=members,
        declared_by=_text(raw, "declared_by", where="site_control"),
        answered_by=_choice(
            raw,
            "answered_by",
            where="site_control",
            allowed=FROZEN_INPUT_ANSWERERS,
        ),
        answered_by_detail=_text(raw, "answered_by_detail", where="site_control"),
        foundation_version=_whole(raw, "foundation_version", where="site_control"),
        foundation_valid_from=_text(
            raw, "foundation_valid_from", where="site_control"
        ),
        source=source,
        source_version=source_version,
    )


def _parse_parameter(entry: Any) -> FrozenParameter:
    raw = _mapping(entry, where="resolved_parameter")
    value = raw.get("value")
    if isinstance(value, bool) or type(value) not in (int, float, str):
        raise _bad(
            "'resolved_parameter.value' must be a number or text in a run "
            "document."
        )
    unit = _optional_text(raw, "unit", where="resolved_parameter")
    if unit is not None and unit not in PARAMETER_UNITS:
        raise _bad(
            f"'resolved_parameter.unit' {unit!r} is not a unit this contract "
            "knows."
        )
    return FrozenParameter(
        parameter_id=_text(raw, "parameter_id", where="resolved_parameter"),
        value=float(value) if not isinstance(value, str) else value,
        unit=unit,
        answered_by=_choice(
            raw,
            "answered_by",
            where="resolved_parameter",
            allowed=FROZEN_INPUT_ANSWERERS,
        ),
    )


def _parse_initialization_input(entry: Any) -> FrozenInitializationInput:
    """One frozen initial value, with its absent case checked.

    `value` may be absent, because a value the selected profile could not
    supply or locate blocks the run rather than refusing it and the record
    has to be able to say so. The two number fields are absent together: a
    canonical restatement of nothing is nothing, and a document carrying one
    without the other would be a run that half knows its own initial state.
    """
    raw = _mapping(entry, where="initialization_input")
    unit = _text(raw, "unit", where="initialization_input")
    value: float | str | None
    canonical_value: float | str | None
    if unit == DISCRETE_VALUE_UNIT:
        # T025a: a typed discrete member, which is its own canonical value.
        value = raw.get("value")
        canonical_value = raw.get("canonical_value")
        if value is not None and (
            not isinstance(value, str)
            or not DISCRETE_MEMBER.fullmatch(value)
            or canonical_value != value
        ):
            raise _bad(
                "'initialization_input.value' in unit 'state' is a discrete "
                "member name, restated unchanged as its canonical value."
            )
    elif unit not in PARAMETER_UNITS:
        raise _bad(
            f"'initialization_input.unit' {unit!r} is not a unit this "
            "contract knows."
        )
    else:
        value = _optional_real(raw, "value", where="initialization_input")
        canonical_value = _optional_real(
            raw, "canonical_value", where="initialization_input"
        )
    if (value is None) != (canonical_value is None):
        raise _bad(
            "'initialization_input.value' and its canonical restatement are "
            "absent together or present together. A run that had one without "
            "the other would half know its own initial state."
        )

    return FrozenInitializationInput(
        state_ref=parse_state_ref(
            raw.get("state_key"),
            where="initialization_input.state_key",
            source="a run document",
            invalid=_raise_invalid,
        ),
        parameter_id=_text(raw, "parameter_id", where="initialization_input"),
        value=value,
        unit=unit,
        canonical_value=canonical_value,
        canonical_unit=_text(
            raw, "canonical_unit", where="initialization_input"
        ),
        dimension=_text(raw, "dimension", where="initialization_input"),
        answered_by=_choice(
            raw,
            "answered_by",
            where="initialization_input",
            allowed=FROZEN_INPUT_ANSWERERS,
        ),
        answered_by_detail=_text(
            raw, "answered_by_detail", where="initialization_input"
        ),
    )


def _projection_entries(
    raw: Mapping[str, Any], key: str, *, contract_version: int
) -> list[Any]:
    """One projection collection, required at this build's contract version.

    ## Absence is tolerable only below the current version, and only there

    The first version of this said "absent means empty" for every run, on the
    reasoning that the contract version guard refuses to execute an earlier run
    anyway. T021's second review showed what that misses: a run frozen AT the
    current version with `causes` deleted parses, is READY, and executes - and the
    removal never happens while the trajectory reports COMPLETED. Deleting
    `declared_bounds` overfills the tank past its capacity. The version guard
    cannot help, because the version is the current one.

    So the rule is the one the version move actually asserts: a run at this
    build's version carries the projection, because that is what freezing
    differently MEANS. Below it, absence is what an earlier run legitimately has,
    and such a run is refused execution.

    An empty list is a real answer and stays one: a document with no state effects
    declares no causes. What is refused is the KEY being missing or null, which is
    a record that does not say.
    """
    if contract_version == EXECUTION_CONTRACT_VERSION:
        if raw.get(key) is None:
            raise _bad(
                f"'deterministic_identity.{key}' is required in a run frozen "
                f"against execution contract version {EXECUTION_CONTRACT_VERSION}"
                ", which freezes the causal projection. A record at this version "
                "carrying none of it would execute an experiment it does not "
                "describe: declare an empty list if the definition declares none."
            )
        return _entries(raw, key, where="deterministic_identity")
    if raw.get(key) is None:
        return []
    return _entries(raw, key, where="deterministic_identity")


def _frozen_timing(raw: Mapping[str, Any], *, where: str) -> tuple[str, int, int | None]:
    """A frozen entry's shape, offset and length, checked as a set.

    A POINT with a length and a WINDOW without one are both documents saying two
    things, so they are refused here rather than resolved by whoever reads them
    next. An INTERVAL_WIDE entry declares no length because the length is the
    run's.
    """
    shape = _choice(raw, "timing_shape", where=where, allowed=TIMING_SHAPES)
    offset = _whole(raw, "offset_minutes", where=where)
    duration = _optional_whole(raw, "duration_minutes", where=where)
    if shape == "WINDOW" and duration is None:
        raise _bad(
            f"'{where}' is a WINDOW and declares no duration_minutes. A window "
            "with no length is not a window."
        )
    if shape == "WINDOW" and duration is not None and duration <= 0:
        # Refused here rather than reaching a kernel. The contract's own span
        # helper raises on a zero-length window, correctly - `point-applied-once`
        # is the rule for something that happens at an instant - and an
        # unclassified `ValueError` escaping mid-execution is not how this product
        # says no to a document.
        raise _bad(
            f"'{where}' is a WINDOW covering {duration} minutes. A window with "
            "zero or negative length is not a window; an entry that happens at "
            "an instant is a POINT."
        )
    if shape != "WINDOW" and duration is not None:
        raise _bad(
            f"'{where}' is a {shape} and declares duration_minutes. Only a "
            "window has a length of its own: a point happens at an instant and "
            "an interval-wide entry takes the run's."
        )
    return shape, offset, duration


def _frozen_address(raw: Mapping[str, Any], key: str, *, where: str):
    return parse_state_ref(
        raw.get(key),
        where=f"{where}.{key}",
        source="a run document",
        invalid=_raise_invalid,
    )


def _parse_frozen_cause(entry: Any) -> FrozenCause:
    """One frozen change to world state, with its direction and its span."""
    raw = _mapping(entry, where="frozen_cause")
    shape, offset, duration = _frozen_timing(raw, where="frozen_cause")
    return FrozenCause(
        event_id=_text(raw, "event_id", where="frozen_cause"),
        state_ref=_frozen_address(raw, "state_key", where="frozen_cause"),
        direction=_choice(
            raw, "direction", where="frozen_cause", allowed=STATE_EFFECT_DIRECTIONS
        ),
        parameter_id=_text(raw, "parameter_id", where="frozen_cause"),
        # Absent when nobody answered for the magnitude, which blocks the run.
        # `SimulationRun` refuses an absent one with no reason beside it.
        canonical_value=_optional_real(
            raw, "canonical_value", where="frozen_cause"
        ),
        canonical_unit=_text(raw, "canonical_unit", where="frozen_cause"),
        dimension=_text(raw, "dimension", where="frozen_cause"),
        timing_shape=shape,
        offset_minutes=offset,
        duration_minutes=duration,
    )


def _parse_frozen_forcing(entry: Any) -> FrozenForcing:
    """One frozen exogenous condition, with the window it is declared over."""
    raw = _mapping(entry, where="frozen_forcing")
    shape, offset, duration = _frozen_timing(raw, where="frozen_forcing")
    return FrozenForcing(
        event_id=_text(raw, "event_id", where="frozen_forcing"),
        state_ref=_frozen_address(raw, "state_key", where="frozen_forcing"),
        parameter_id=_text(raw, "parameter_id", where="frozen_forcing"),
        canonical_value=_optional_real(
            raw, "canonical_value", where="frozen_forcing"
        ),
        canonical_unit=_text(raw, "canonical_unit", where="frozen_forcing"),
        dimension=_text(raw, "dimension", where="frozen_forcing"),
        timing_shape=shape,
        offset_minutes=offset,
        duration_minutes=duration,
        execution_requirement=_choice(
            raw,
            "execution_requirement",
            where="frozen_forcing",
            allowed=EXECUTION_REQUIREMENTS,
        ),
        issued_by=(
            _choice(
                raw, "issued_by", where="frozen_forcing", allowed=ENTRY_ISSUERS
            )
            if "issued_by" in raw
            else None
        ),
    )


def _parse_frozen_declared_bound(entry: Any) -> FrozenDeclaredBound:
    """One frozen bound relationship: which state, and whose value bounds it."""
    raw = _mapping(entry, where="frozen_declared_bound")
    return FrozenDeclaredBound(
        state_ref=_frozen_address(
            raw, "state_key", where="frozen_declared_bound"
        ),
        bound_kind=_choice(
            raw, "bound_kind", where="frozen_declared_bound", allowed=BOUND_KINDS
        ),
        source_state_ref=_frozen_address(
            raw, "source_state_key", where="frozen_declared_bound"
        ),
        source_parameter_id=_text(
            raw, "source_parameter_id", where="frozen_declared_bound"
        ),
    )


def _parse_frozen_reporting_path_condition(
    entry: Any,
) -> FrozenReportingPathCondition:
    """One frozen condition on the path a reading travels."""
    raw = _mapping(entry, where="frozen_reporting_path_condition")
    shape, offset, duration = _frozen_timing(
        raw, where="frozen_reporting_path_condition"
    )
    return FrozenReportingPathCondition(
        event_id=_text(
            raw, "event_id", where="frozen_reporting_path_condition"
        ),
        state_ref=_frozen_address(
            raw, "state_key", where="frozen_reporting_path_condition"
        ),
        timing_shape=shape,
        offset_minutes=offset,
        duration_minutes=duration,
    )


def _parse_observation_binding(entry: Any) -> FrozenObservationBinding:
    """One frozen source, with the cadence a publication profile resolved.

    `cadence_ownership` is a closed vocabulary like every field beside it, and
    was read as free text until T019's review noticed the one that was not.

    There is no cross-field biconditional here any more, because there is no
    second field to check against. `cadence_resolution` restated what the
    source kind and the cadence already said, so the rule that checked them
    against each other was a record being checked against itself; T020
    deleted the field and the rule went with it. A stored document that still
    carries the key is read with the key ignored, which is how the Drafts
    written before this slice stay readable.

    What remains is a rule between two REAL fields: a person writing a value
    down reports at no rate, so an operator record carrying a cadence is a
    document contradicting itself rather than restating itself.
    """
    raw = _mapping(entry, where="observation_binding")
    source_kind = _choice(
        raw,
        "source_kind",
        where="observation_binding",
        allowed=OBSERVATION_SOURCE_KINDS,
    )
    minutes = _optional_whole(
        raw, "cadence_minutes", where="observation_binding"
    )

    if minutes is not None and source_kind != "DEVICE_SIGNAL":
        raise _bad(
            f"'observation_binding.cadence_minutes' is recorded for a "
            f"{source_kind} source. A person writing a value down reports at "
            "no rate, so there is no cadence for anything to own."
        )

    if minutes is not None and minutes < 1:
        raise _bad(
            "'observation_binding.cadence_minutes' must be at least one "
            "minute. A source that reports every zero minutes reports at no "
            "rate, which is a different statement and has its own absence."
        )

    return FrozenObservationBinding(
        source_id=_text(raw, "source_id", where="observation_binding"),
        source_kind=source_kind,
        device_id=_optional_text(raw, "device_id", where="observation_binding"),
        signal_id=_optional_text(raw, "signal_id", where="observation_binding"),
        cadence_ownership=_choice(
            raw,
            "cadence_ownership",
            where="observation_binding",
            allowed=CADENCE_OWNERSHIP,
        ),
        cadence_minutes=minutes,
    )


def _parse_signal_mapping(entry: Any) -> FrozenSignalMapping:
    raw = _mapping(entry, where="signal_mapping")
    return FrozenSignalMapping(
        mapping_id=_text(raw, "mapping_id", where="signal_mapping"),
        device_id=_text(raw, "device_id", where="signal_mapping"),
        signal_id=_text(raw, "signal_id", where="signal_mapping"),
        component_id=_text(raw, "component_id", where="signal_mapping"),
    )
