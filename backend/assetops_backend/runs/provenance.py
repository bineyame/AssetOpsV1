"""One row per frozen value, and who answered for it.

`D-2026-09-21-causal-runtime-before-golden-traces` requires that an initial
condition be explicit and attributable and that nothing hide or invent one.
T019's acceptance criterion says the same thing about the whole frozen
identity: each value names its Foundation, scenario, run, or versioned-profile
origin.

This module is that criterion, computed rather than described. It turns a
`DeterministicIdentity` into a flat list of rows, each carrying the value as
text and the answerer that produced it. A test in `test_run_setup.py` walks
`dataclasses.fields(DeterministicIdentity)` and fails if any field has no row,
so a field added to the identity fails the build until somebody says who
answers for it, rather than arriving on a screen in a column with nothing
under it.

The rows are derived from the identity rather than assembled beside it. Two
lists - one structured, one for reading - would be two places for a value to
drift, and the one that drifts is the one a person reads.

## Digits

Every digit in a row comes from the identity. `_number` renders a whole value
without a decimal point, because an author who wrote 430 did not write 430.0
and a screen that showed the second would be stating a precision the record
does not have - the same rule `scenarios/execution.py` converts through exact
ratios for.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from assetops_backend.runs.models import BlockingReason, DeterministicIdentity
from assetops_backend.scenarios.execution import (
    ExecutionContractIncompatible,
    refuse_incompatible_execution,
)


@dataclass(frozen=True)
class FrozenInput:
    """One frozen value, as a reader meets it.

    `identity_field` names the field of `DeterministicIdentity` this row came
    from, which is what makes the completeness test possible: it compares row
    coverage against the record rather than against a list somebody kept up to
    date by hand.

    `answered_by_detail` says which Foundation version, which scenario
    version, which run input or which profile version answered, so two rows
    with the same answerer are still two attributions.

    `blocking_statement` is why THIS row stands in the way, rather than a
    general remark about the run. A blocked run already lists its reasons in
    their own table; this puts the one that explains this row next to it,
    which is what a reader looking at two same-type assets needs - the two
    rows differ by a component id, and so do the two reasons.

    It appears on rows of two kinds, and this docstring said "only on a row
    whose value is missing" until a backup review checked it against the code
    below. That is the usual case: an initial value with no answer carries
    the reason it has none. The other is the execution-contract row, which
    has a value - the version the run froze - and carries the statement that
    this build will not execute a run frozen against it. Both are "why this
    row stops the run", which is what the field means; a missing value is one
    way for a row to do that and not the only one.
    """

    identity_field: str
    field: str
    value: str
    answered_by: str
    answered_by_detail: str
    blocking_statement: str | None = None


def _number(value: float) -> str:
    """A number as an author would write it."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _quantity(value: float, unit: str) -> str:
    return f"{_number(value)} {unit}"


def _contract_incompatibility(frozen_version: int) -> str | None:
    """Why this build will not execute this run, or nothing.

    The rule lives in `scenarios/execution.py`, which owns the contract, and
    is ASKED here rather than restated. A second copy of "the versions must
    match" is a second thing to keep true, and the last two rounds of this
    slice's predecessor both lost time to exactly that.
    """
    try:
        refuse_incompatible_execution(frozen_version)
    except ExecutionContractIncompatible as error:
        return str(error)
    return None


def frozen_inputs(
    identity: DeterministicIdentity,
    blocking_reasons: Sequence[BlockingReason] = (),
) -> tuple[FrozenInput, ...]:
    """Every frozen value on one run, with the answerer for each.

    `blocking_reasons` is optional and the rows are complete without it. When
    it is supplied, the reason an unresolved value is missing is carried on
    the row it is missing from, matched on the ADDRESS - which is what makes
    acceptance criterion 11 work at all. A run with two tanks has two "not
    resolved" rows and two reasons, and pairing them on the semantic state key
    would put one reason on both rows and the other on none.
    """
    explanations = {
        reason.subject: reason.statement for reason in blocking_reasons
    }
    site = identity.site
    scenario = identity.scenario
    interval = identity.interval
    profiles = identity.profiles

    site_detail = f"site {site.site_id} foundation version {site.foundation_version}"
    scenario_detail = (
        f"scenario {scenario.scenario_id} version {scenario.scenario_version}"
    )
    model_detail = (
        f"model profile {profiles.model_profile_id} version "
        f"{profiles.model_profile_version}"
    )
    publication_detail = (
        f"publication profile {profiles.publication_profile_id} version "
        f"{profiles.publication_profile_version}"
    )
    request_detail = "supplied by this run setup request"

    rows: list[FrozenInput] = [
        FrozenInput(
            identity_field="site",
            field="Site",
            value=site.site_id,
            answered_by="SITE_FOUNDATION",
            answered_by_detail=site_detail,
        ),
        FrozenInput(
            identity_field="site",
            field="Foundation version",
            value=str(site.foundation_version),
            answered_by="SITE_FOUNDATION",
            answered_by_detail=site_detail,
        ),
        FrozenInput(
            identity_field="site",
            field="Foundation valid from",
            value=site.foundation_valid_from,
            answered_by="SITE_FOUNDATION",
            answered_by_detail=site_detail,
        ),
        FrozenInput(
            identity_field="site",
            field="Site type",
            value=site.site_type,
            answered_by="SITE_FOUNDATION",
            answered_by_detail=site_detail,
        ),
        FrozenInput(
            identity_field="site",
            field="Site time zone",
            value=site.timezone,
            answered_by="SITE_FOUNDATION",
            answered_by_detail=site_detail,
        ),
        FrozenInput(
            identity_field="scenario",
            field="Scenario",
            value=scenario.scenario_id,
            answered_by="SCENARIO",
            answered_by_detail=scenario_detail,
        ),
        FrozenInput(
            identity_field="scenario",
            field="Scenario version",
            value=str(scenario.scenario_version),
            answered_by="SCENARIO",
            answered_by_detail=scenario_detail,
        ),
    ]

    for parameter in scenario.resolved_parameters:
        value = (
            parameter.value
            if parameter.unit is None
            else _quantity(float(parameter.value), parameter.unit)
        )
        rows.append(
            FrozenInput(
                identity_field="scenario",
                field=f"Parameter {parameter.parameter_id}",
                value=str(value),
                answered_by=parameter.answered_by,
                answered_by_detail=(
                    request_detail
                    if parameter.answered_by == "RUN_INPUT"
                    else scenario_detail
                ),
            )
        )

    rows.extend(
        [
            FrozenInput(
                identity_field="interval",
                field="Interval start",
                value=interval.start_time,
                answered_by="RUN_INPUT",
                answered_by_detail=request_detail,
            ),
            FrozenInput(
                identity_field="interval",
                field="Interval end",
                value=interval.end_time,
                answered_by="RUN_INPUT",
                answered_by_detail=request_detail,
            ),
            FrozenInput(
                identity_field="interval",
                field="Interval length",
                value=f"{interval.duration_minutes} minutes",
                answered_by="RUN_INPUT",
                answered_by_detail=request_detail,
            ),
            FrozenInput(
                identity_field="interval",
                field="Timestep",
                value=f"{interval.timestep_minutes} minutes",
                answered_by="RUN_INPUT",
                answered_by_detail=request_detail,
            ),
            FrozenInput(
                identity_field="seed",
                field="Seed",
                value=str(identity.seed),
                answered_by="RUN_INPUT",
                answered_by_detail=request_detail,
            ),
            FrozenInput(
                identity_field="profiles",
                field="Model profile",
                value=(
                    f"{profiles.model_profile_id} "
                    f"v{profiles.model_profile_version}"
                ),
                answered_by="RUN_INPUT",
                answered_by_detail=request_detail,
            ),
            FrozenInput(
                identity_field="profiles",
                field="Publication profile",
                value=(
                    f"{profiles.publication_profile_id} "
                    f"v{profiles.publication_profile_version}"
                ),
                answered_by="RUN_INPUT",
                answered_by_detail=request_detail,
            ),
            FrozenInput(
                identity_field="profiles",
                field="Execution contract",
                value=f"v{profiles.execution_contract_version}",
                answered_by="MODEL_PROFILE",
                answered_by_detail=(
                    "the execution contract these versioned rules are stated "
                    "against"
                ),
                # A run frozen under an earlier contract stays readable and
                # says here that this build will not execute it. That is the
                # run half of `D-2026-09-22-contract-version-scope`: an
                # incompatible run is refused execution rather than
                # reinterpreted, and the refusal is a fact on the run rather
                # than something the first executor will have to remember.
                # Asked of the function that owns the rule, so the screen and
                # a future kernel cannot disagree about which runs are
                # executable.
                blocking_statement=_contract_incompatibility(
                    profiles.execution_contract_version
                ),
            ),
        ]
    )

    if identity.initialization_inputs:
        for initial in identity.initialization_inputs:
            rows.append(
                FrozenInput(
                    identity_field="initialization_inputs",
                    # The ADDRESS, so two components of one type are two
                    # distinguishable rows on this table rather than two rows
                    # a reader has to tell apart by the detail column. On a
                    # resolved row the address names the asset that answered.
                    field=f"Initial {initial.addressed_key}",
                    # "not resolved" rather than a blank or a zero, the same
                    # words an unresolved cadence uses. A value nobody
                    # answered for is a fact about the run, and the row that
                    # carries it says whose answer is missing.
                    value=(
                        "not resolved"
                        if initial.value is None
                        else _quantity(initial.value, initial.unit)
                    ),
                    answered_by=initial.answered_by,
                    answered_by_detail=initial.answered_by_detail,
                    blocking_statement=(
                        None
                        if initial.value is not None
                        else explanations.get(initial.addressed_key)
                    ),
                )
            )
    else:
        rows.append(
            FrozenInput(
                identity_field="initialization_inputs",
                field="Initial world values",
                value="none declared",
                answered_by="SCENARIO",
                answered_by_detail=scenario_detail,
            )
        )

    if identity.observation_bindings:
        for binding in identity.observation_bindings:
            # Read off the two real fields rather than off a third that
            # restated them. A cadence present means a publication profile
            # declared one; absent on an operator record means there is no
            # rate to own; absent on a device signal means nobody declared
            # one.
            if binding.cadence_minutes is not None:
                value = f"{binding.cadence_minutes} minutes"
                answered_by = "PUBLICATION_PROFILE"
                detail = publication_detail
            elif binding.source_kind != "DEVICE_SIGNAL":
                value = "not applicable"
                answered_by = "SCENARIO"
                detail = (
                    f"{scenario_detail}, which declares this source reports "
                    "at no rate"
                )
            else:
                value = "not resolved"
                answered_by = "PUBLICATION_PROFILE"
                detail = (
                    f"{publication_detail}, which declares no cadence for a "
                    "configured device signal"
                )
            rows.append(
                FrozenInput(
                    identity_field="observation_bindings",
                    field=f"Cadence for {binding.source_id}",
                    value=value,
                    answered_by=answered_by,
                    answered_by_detail=detail,
                )
            )
    else:
        rows.append(
            FrozenInput(
                identity_field="observation_bindings",
                field="Observation sources",
                value="none declared",
                answered_by="SCENARIO",
                answered_by_detail=scenario_detail,
            )
        )

    rows.extend(
        [
            # Both come from the publication profile and both said the
            # model profile answered them. A row's answerer and the detail
            # beside it named two different things.
            FrozenInput(
                identity_field="publication",
                field="Simulator source",
                value=(
                    identity.publication.simulator_source_id
                    if identity.publication.simulator_source_id is not None
                    else "not resolved"
                ),
                answered_by="PUBLICATION_PROFILE",
                answered_by_detail=publication_detail,
            ),
            FrozenInput(
                identity_field="publication",
                field="Gateway",
                value=(
                    identity.publication.gateway_id
                    if identity.publication.gateway_id is not None
                    else "not resolved"
                ),
                answered_by="PUBLICATION_PROFILE",
                answered_by_detail=publication_detail,
            ),
        ]
    )

    if identity.signal_mappings:
        for mapping in identity.signal_mappings:
            rows.append(
                FrozenInput(
                    identity_field="signal_mappings",
                    field=f"Mapping {mapping.mapping_id}",
                    value=(
                        f"{mapping.device_id} {mapping.signal_id} "
                        f"to {mapping.component_id}"
                    ),
                    answered_by="SITE_FOUNDATION",
                    answered_by_detail=site_detail,
                )
            )
    else:
        rows.append(
            FrozenInput(
                identity_field="signal_mappings",
                field="Signal mappings",
                value="none declared",
                answered_by="SITE_FOUNDATION",
                answered_by_detail=site_detail,
            )
        )

    rows.append(
        FrozenInput(
            identity_field="intervention_history",
            field="Intervention history",
            # Ordered and empty. Nothing in this build can inject a runtime
            # event, so a Draft begins with none - and the order is part of
            # the identity even while the list has nothing in it.
            value=(
                "empty"
                if not identity.intervention_history
                else ", ".join(identity.intervention_history)
            ),
            answered_by="RUN_INPUT",
            answered_by_detail=request_detail,
        )
    )

    return tuple(rows)
