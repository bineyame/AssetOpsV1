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

from assetops_backend.document_bounds import DocumentLimits, reject_oversized
from assetops_backend.runs.identity import validate_run_id
from assetops_backend.runs.models import (
    BLOCKING_REASON_KINDS,
    CADENCE_RESOLUTIONS,
    FROZEN_INPUT_ANSWERERS,
    RUN_EXECUTION_STATUSES,
    RUN_LIFECYCLE_STATUSES,
    BlockingReason,
    DeterministicIdentity,
    FrozenInitializationInput,
    FrozenInterval,
    FrozenObservationBinding,
    FrozenParameter,
    FrozenProfileBinding,
    FrozenPublicationIdentity,
    FrozenScenarioBinding,
    FrozenSignalMapping,
    FrozenSiteBinding,
    SimulationRun,
    UnsupportedOptionalInput,
)
from assetops_backend.runs.ports import RunConfigurationInvalid
from assetops_backend.runs.refusals import refuse
from assetops_backend.scenarios.execution import (
    CANONICAL_UNITS,
    NON_NEGATIVE_DIMENSIONS,
)
from assetops_backend.scenarios.identity import validate_scenario_id
from assetops_backend.scenarios.models import (
    CADENCE_OWNERSHIP,
    OBSERVATION_SOURCE_KINDS,
    PARAMETER_UNITS,
)
from assetops_backend.scenarios.ports import ScenarioConfigurationInvalid
from assetops_backend.sites.identity import validate_site_id
from assetops_backend.sites.ports import SiteConfigurationInvalid

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
    }
)

INTERVAL_KEYS = frozenset({"start_time", "end_time"})
PROFILE_KEYS = frozenset({"profile_id", "profile_version"})
RUN_INPUT_KEYS = frozenset({"parameter_id", "value", "unit"})

#: An ISO-8601 instant in UTC, spelled the one way the rest of the product
#: spells one. A run interval is a product fact, so it has one spelling rather
#: than whatever a client happened to emit.
INSTANT_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

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
    )


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
            },
            "initialization_inputs": [
                {
                    "state_key": item.state_key,
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
            "observation_bindings": [
                {
                    "source_id": item.source_id,
                    "source_kind": item.source_kind,
                    "device_id": item.device_id,
                    "signal_id": item.signal_id,
                    "cadence_ownership": item.cadence_ownership,
                    "cadence_minutes": item.cadence_minutes,
                    "cadence_resolution": item.cadence_resolution,
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
                "state_key": item.state_key,
                "execution_role": item.execution_role,
                "statement": item.statement,
            }
            for item in record.unsupported_optional_inputs
        ],
    }


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
        state_key=_text(raw, "state_key", where="unsupported_optional_input"),
        execution_role=_text(
            raw, "execution_role", where="unsupported_optional_input"
        ),
        statement=_text(raw, "statement", where="unsupported_optional_input"),
    )


def _parse_identity(raw: Mapping[str, Any]) -> DeterministicIdentity:
    site = _mapping(raw.get("site"), where="deterministic_identity")
    scenario = _mapping(raw.get("scenario"), where="deterministic_identity")
    interval = _mapping(raw.get("interval"), where="deterministic_identity")
    profiles = _mapping(raw.get("profiles"), where="deterministic_identity")
    publication = _mapping(
        raw.get("publication"), where="deterministic_identity"
    )

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
            execution_contract_version=_whole(
                profiles, "execution_contract_version", where="profiles"
            ),
        ),
        initialization_inputs=tuple(
            _parse_initialization_input(entry)
            for entry in _entries(
                raw, "initialization_inputs", where="deterministic_identity"
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
    if unit not in PARAMETER_UNITS:
        raise _bad(
            f"'initialization_input.unit' {unit!r} is not a unit this "
            "contract knows."
        )

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
        state_key=_text(raw, "state_key", where="initialization_input"),
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


def _parse_observation_binding(entry: Any) -> FrozenObservationBinding:
    """One frozen source, with the two cadence fields checked against each other.

    `cadence_ownership` is a closed vocabulary like every field beside it, and
    was read as free text until T019's review noticed the one that was not.

    The cross-field rule matters more. `cadence_resolution` says where the
    cadence came from and `cadence_minutes` is the cadence; a document saying
    the profile resolved one while carrying none, or saying nobody resolved
    one while carrying a number, is a run record that contradicts itself, and
    a reader of a stored run would have no way to tell which half is true.
    """
    raw = _mapping(entry, where="observation_binding")
    resolution = _choice(
        raw,
        "cadence_resolution",
        where="observation_binding",
        allowed=CADENCE_RESOLUTIONS,
    )
    minutes = _optional_whole(
        raw, "cadence_minutes", where="observation_binding"
    )

    if resolution == "MODEL_PROFILE" and minutes is None:
        raise _bad(
            "'observation_binding.cadence_resolution' is MODEL_PROFILE and no "
            "cadence is recorded. A resolution says where the cadence came "
            "from; it is not a cadence, and a run cannot have been resolved "
            "to nothing."
        )
    if resolution != "MODEL_PROFILE" and minutes is not None:
        raise _bad(
            f"'observation_binding.cadence_resolution' is {resolution} and a "
            "cadence is recorded anyway. Nothing but a publication profile "
            "may supply one, so a cadence beside any other resolution is a "
            "value with no owner."
        )
    if minutes is not None and minutes < 1:
        raise _bad(
            "'observation_binding.cadence_minutes' must be at least one "
            "minute. A source that reports every zero minutes reports at no "
            "rate, which is a different statement and has its own value."
        )

    return FrozenObservationBinding(
        source_id=_text(raw, "source_id", where="observation_binding"),
        source_kind=_choice(
            raw,
            "source_kind",
            where="observation_binding",
            allowed=OBSERVATION_SOURCE_KINDS,
        ),
        device_id=_optional_text(raw, "device_id", where="observation_binding"),
        signal_id=_optional_text(raw, "signal_id", where="observation_binding"),
        cadence_ownership=_choice(
            raw,
            "cadence_ownership",
            where="observation_binding",
            allowed=CADENCE_OWNERSHIP,
        ),
        cadence_minutes=minutes,
        cadence_resolution=resolution,
    )


def _parse_signal_mapping(entry: Any) -> FrozenSignalMapping:
    raw = _mapping(entry, where="signal_mapping")
    return FrozenSignalMapping(
        mapping_id=_text(raw, "mapping_id", where="signal_mapping"),
        device_id=_text(raw, "device_id", where="signal_mapping"),
        signal_id=_text(raw, "signal_id", where="signal_mapping"),
        component_id=_text(raw, "component_id", where="signal_mapping"),
    )
