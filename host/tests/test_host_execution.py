"""A Draft created through the normal setup service, executed at host level.

The composing end of the slice. Everything here goes through
`RunSetupService.create_draft_run` against a Site instantiated by
`SiteCreationService`, so what is executed is what run setup actually freezes
rather than a record written to the shape a kernel expects.

It also holds the refusals, because a refusal is the composition leaf's and not
the kernel's: a `BLOCKED` Draft and a Draft frozen against another contract
version never reach a kernel at all.
"""

from __future__ import annotations

from dataclasses import fields, replace
from fractions import Fraction

import pytest
from fixtures import (
    HYBRID_TEMPLATE,
    draft,
    scenario,
    shipped_document,
    site_from_template,
)

from assetops_backend.runs.parsing import (
    parse_run_document,
    render_run_document,
)
from assetops_contracts.execution_contract import (
    EXECUTION_CONTRACT_VERSION,
    ExecutionContractIncompatible,
)
from assetops_contracts.trajectory import (
    IDENTITY_FIELDS_EXCLUDED,
    IDENTITY_FIELDS_READ,
)
from assetops_contracts.world_inputs import FrozenWorldInputs

from execution_adapter import (
    FrozenRunNotReconstructible,
    RunNotExecutable,
    frozen_world_inputs,
    run_to_end,
)

TANK = "fuel-tank-volume@fuel-tank"
CAPACITY = "fuel-tank-capacity@fuel-tank"
AFTER_DISPATCH = Fraction(18701, 50)
AFTER_REMOVAL = Fraction(12701, 50)


def _requires_demand(document: dict) -> dict:
    """The shipped document with site demand raised back to REQUIRED.

    The state the minimal fuel model does not carry. `REQUIRED` means an executor
    must model it, so run setup blocks the Draft - which is how this suite gets a
    `BLOCKED` run out of the real path rather than writing one.

    Raised at all three positions that name the state, because two positions
    disagreeing about a requirement is two answers to one question and the parser
    refuses the document.
    """
    for entry in document["timeline"]:
        if entry["event_id"] != "baseline-load-profile":
            continue
        entry["execution_requirement"] = "REQUIRED"
        for parameter in entry["parameters"]:
            parameter["execution_requirement"] = "REQUIRED"
    return document


class TestAReadyDraftExecutes:
    def test_the_shipped_draft_runs_to_the_end_of_its_interval(self) -> None:
        definition = scenario()
        run = draft(definition=definition)
        assert run.execution_status == "READY"

        executed = run_to_end(run, definition)

        assert executed.trajectory.outcome == "COMPLETED"
        assert executed.trajectory.is_complete
        assert len(executed.trajectory.boundaries) == 165
        assert executed.trajectory.run_id == run.run_id

    def test_the_trajectory_is_the_one_derived_by_hand(self) -> None:
        """The same numbers the simulator suite asserts, out of the product path.

        Both suites have to agree, or one of them is measuring something the
        product does not do. The derivation lives in
        `simulator/tests/test_fuel_trajectory.py`; this is the same trajectory
        reached from a real Draft.
        """
        definition = scenario()
        executed = run_to_end(draft(definition=definition), definition)
        trajectory = executed.trajectory

        assert trajectory.boundary_at(0).stock(TANK) == Fraction(430)
        assert trajectory.boundary_at(1095).stock(TANK) == Fraction("426.50125")
        assert trajectory.boundary_at(1320).stock(TANK) == AFTER_DISPATCH
        assert trajectory.boundary_at(1545).stock(TANK) == AFTER_REMOVAL
        assert trajectory.boundary_at(2400).stock(TANK) == Fraction(500)
        assert trajectory.final.stock(TANK) == Fraction(500)
        assert trajectory.bounded_transitions[0].refused == Fraction("54.02")

    def test_the_bound_number_came_from_the_frozen_foundation_answer(
        self,
    ) -> None:
        """`D-2026-09-22-capacity-bound-source`, end to end.

        The document declares which state the capacity caps and states no number;
        the Site's Foundation declares 500 L; run setup freezes it as an
        initialization input; and the bound the kernel applies names that frozen
        row as its source. All three are asserted, because the interesting failure
        is a 500 that came from somewhere else.
        """
        from assetops_backend.scenarios.execution import declared_bounds

        definition = scenario()
        run = draft(definition=definition)
        executed = run_to_end(run, definition)

        assert declared_bounds(definition)[TANK] == (0.0, None)
        frozen = {
            item.addressed_key: item
            for item in run.deterministic_identity.initialization_inputs
        }
        assert frozen[CAPACITY].value == 500.0
        assert frozen[CAPACITY].answered_by == "SITE_FOUNDATION"
        assert "component fuel-tank property tank-capacity" in (
            frozen[CAPACITY].answered_by_detail
        )

        bound = executed.inputs.bound(TANK, "UPPER")
        assert bound is not None
        assert bound.value == Fraction(500)
        assert bound.source_address == CAPACITY
        assert bound.bound_case_id == "fuel-tank-capacity"
        assert bound.policy == "BOUNDED_AND_RECORDED"


class TestABlockedDraftCannotBeCoercedIntoExecution:
    def test_a_required_unmodelled_state_blocks_and_is_not_executed(
        self,
    ) -> None:
        definition = scenario(_requires_demand(shipped_document()))
        run = draft(definition=definition)

        assert run.execution_status == "BLOCKED"
        assert {reason.kind for reason in run.blocking_reasons} == {
            "STATE_NOT_SUPPORTED"
        }

        with pytest.raises(RunNotExecutable) as raised:
            run_to_end(run, definition)
        assert "BLOCKED" in str(raised.value)
        assert "STATE_NOT_SUPPORTED" in str(raised.value)
        assert "no mode in which they do" in str(raised.value)

    def test_the_inputs_are_not_built_either(self) -> None:
        """Not executed AND not projected: there is nothing to hand a kernel.

        A leaf that refused to run but still produced kernel input would leave a
        caller one function call away from running it anyway.
        """
        definition = scenario(_requires_demand(shipped_document()))
        with pytest.raises(RunNotExecutable):
            frozen_world_inputs(draft(definition=definition), definition)

    def test_there_is_no_argument_that_makes_it_run(self) -> None:
        """The refusal has no override, and the signatures are what say so."""
        import inspect

        assert set(inspect.signature(run_to_end).parameters) == {
            "run",
            "scenario",
            "model",
        }
        assert set(inspect.signature(frozen_world_inputs).parameters) == {
            "run",
            "scenario",
        }


class TestAnIncompatibleContractVersionCannotBeCoercedEither:
    def test_a_run_frozen_against_an_earlier_version_is_refused(self) -> None:
        """The trap the backlog names, exercised on a Draft this build froze.

        `refuse_incompatible_execution` is an equality test on an integer, so a
        Draft frozen before this build at the same number cannot be told apart
        from one frozen by it. Every Draft in this suite is regenerated in
        process for exactly that reason, and this test lowers the version on a
        rendered document rather than reading a local Draft, so what is refused is
        a run whose provenance is known.
        """
        definition = scenario()
        run = draft(definition=definition)
        document = render_run_document(run)
        document["deterministic_identity"]["profiles"][
            "execution_contract_version"
        ] = EXECUTION_CONTRACT_VERSION - 1

        earlier = parse_run_document(document, source="an earlier run")
        assert earlier.execution_status == "READY"

        with pytest.raises(ExecutionContractIncompatible) as raised:
            run_to_end(earlier, definition)
        assert "stays readable" in str(raised.value)
        assert "it is not executed" in str(raised.value)

    def test_reading_it_is_never_refused(self) -> None:
        """A run that cannot be executed is still a run somebody must inspect."""
        definition = scenario()
        document = render_run_document(draft(definition=definition))
        document["deterministic_identity"]["profiles"][
            "execution_contract_version"
        ] = 1
        earlier = parse_run_document(document, source="an earlier run")
        assert (
            earlier.deterministic_identity.profiles.execution_contract_version
            == 1
        )

    def test_a_later_version_is_refused_rather_than_assumed_compatible(
        self,
    ) -> None:
        definition = scenario()
        document = render_run_document(draft(definition=definition))
        document["deterministic_identity"]["profiles"][
            "execution_contract_version"
        ] = EXECUTION_CONTRACT_VERSION + 1
        later = parse_run_document(document, source="a later run")
        with pytest.raises(ExecutionContractIncompatible):
            run_to_end(later, definition)


class TestReconstructingFromFrozenContent:
    def test_the_current_site_changing_does_not_change_the_trajectory(
        self,
    ) -> None:
        """Criterion 2 and the mutation table's Site row.

        The Draft is frozen against a 500 L tank. A Site whose tank is later
        declared at 900 L changes nothing about this run, because the capacity the
        run executes is the one it froze. Asserted on the bound, the trajectory
        and the identity.
        """
        definition = scenario()
        run = draft(definition=definition)
        before = run_to_end(run, definition)

        changed_site = _with_tank_capacity(
            site_from_template(HYBRID_TEMPLATE, site_id="MG-001"), 900.0
        )
        assert _tank_capacity_of(changed_site) == 900.0

        after = run_to_end(run, definition)
        assert after.inputs.bound(TANK, "UPPER").value == Fraction(500)
        assert after.trajectory.boundaries == before.trajectory.boundaries
        assert after.trajectory.inputs_identity == (
            before.trajectory.inputs_identity
        )
        assert after.trajectory.content_digest == (
            before.trajectory.content_digest
        )

    def test_a_draft_frozen_against_the_changed_site_is_a_different_run(
        self,
    ) -> None:
        """The other side of it, so the test above is not about a dead input.

        If the Site's capacity could not reach a run at all, the previous test
        would pass against a kernel that ignored capacity entirely. A NEW Draft
        against the changed Site freezes 900 L, and its delivery is not bounded.
        """
        definition = scenario()
        changed_site = _with_tank_capacity(
            site_from_template(HYBRID_TEMPLATE, site_id="MG-001"), 900.0
        )
        executed = run_to_end(
            draft(definition=definition, site=changed_site), definition
        )
        assert executed.inputs.bound(TANK, "UPPER").value == Fraction(900)
        assert executed.trajectory.bounded_transitions == ()
        assert executed.trajectory.final.stock(TANK) == Fraction("554.02")

    def test_the_same_identity_produces_the_same_canonical_trajectory(
        self,
    ) -> None:
        definition = scenario()
        run = draft(definition=definition)
        first = run_to_end(run, definition)
        second = run_to_end(run, definition)
        assert first.inputs == second.inputs
        assert (
            first.trajectory.inputs_identity
            == second.trajectory.inputs_identity
        )
        assert (
            first.trajectory.content_digest == second.trajectory.content_digest
        )

    def test_a_changed_authored_value_cannot_reach_the_trajectory(self) -> None:
        """The values a run froze are the values it executes.

        The definition's starting level is edited to 999 L at the same scenario
        version, which is the worst case: nothing about the parameter SET changed,
        so the drift check has nothing to catch. It changes no trajectory anyway,
        because every number the adapter produces comes from the frozen run.
        """
        definition = scenario()
        run = draft(definition=definition)
        original = run_to_end(run, definition)

        edited = shipped_document()
        for parameter in edited["public_parameters"]:
            if parameter["parameter_id"] == "starting-fuel-level":
                parameter["value"] = 999
        for entry in edited["timeline"]:
            for parameter in entry.get("parameters", []):
                if parameter["parameter_id"] == "volume-removed":
                    parameter["value"] = 5

        executed = run_to_end(run, scenario(edited))
        assert executed.inputs.initial_value(TANK).value == Fraction(430)
        assert executed.trajectory.boundaries == original.trajectory.boundaries
        assert executed.trajectory.content_digest == (
            original.trajectory.content_digest
        )

    def test_a_definition_that_has_gained_an_entry_is_refused(self) -> None:
        """The half of structural drift a frozen run can see."""
        definition = scenario()
        run = draft(definition=definition)

        widened = shipped_document()
        widened["timeline"].append(
            {
                "event_id": "a-second-refuelling",
                "sequence": 9,
                "offset_minutes": 2430,
                "entry_kind": "EVENT",
                "category": "MAINTENANCE",
                "description": "A delivery this run never froze.",
                "execution_role": "CAUSAL_INPUT",
                "state_key": TANK,
                "execution_requirement": "REQUIRED",
                "timing": {"shape": "POINT"},
                "state_effect": {
                    "direction": "INCREASE",
                    "quantity_parameter_id": "second-volume-delivered",
                },
                "parameters": [
                    {
                        "parameter_id": "second-volume-delivered",
                        "display_name": "Volume delivered again",
                        "value": 50,
                        "unit": "L",
                        "execution_role": "CAUSAL_INPUT",
                        "state_key": TANK,
                        "execution_requirement": "REQUIRED",
                        "ownership": {
                            "owner": "SCENARIO_INPUT",
                            "initializes": False,
                        },
                    }
                ],
            }
        )

        with pytest.raises(FrozenRunNotReconstructible) as raised:
            run_to_end(run, scenario(widened))
        assert "second-volume-delivered" in str(raised.value)
        assert "gained or lost an entry" in str(raised.value)

    def test_a_definition_at_another_version_is_refused(self) -> None:
        definition = scenario()
        run = draft(definition=definition)
        later = shipped_document()
        later["version"]["scenario_version"] = 2
        later["version"]["supersedes"] = 1
        with pytest.raises(FrozenRunNotReconstructible) as raised:
            run_to_end(run, scenario(later))
        assert "froze version 1" in str(raised.value)
        assert "reinterpretation" in str(raised.value)


class TestTheTruthBarrierIsTheShapeOfTheInput:
    def test_the_frozen_world_inputs_have_no_field_for_an_oracle(self) -> None:
        """Criterion 5, structurally.

        A rule saying "do not read the expectations" is a rule an adapter can
        forget. A record with no field for them cannot be passed one, and the
        field list is asserted in full so a field added later has to be
        considered here.
        """
        names = {field.name for field in fields(FrozenWorldInputs)}
        assert names == {
            "run_id",
            "execution_contract_version",
            "site_id",
            "foundation_version",
            "scenario_id",
            "scenario_version",
            "model_profile_id",
            "model_profile_version",
            "publication_profile_id",
            "publication_profile_version",
            "interval",
            "seed",
            "initial_values",
            "bounds",
            "forcings",
            "causes",
            "unmodelled_addresses",
            "reporting_path_addresses",
            "intervention_history",
        }
        for forbidden in (
            "expectation",
            "oracle",
            "reconcil",
            "reported",
            "display_name",
            "device",
            "signal",
        ):
            assert not [name for name in names if forbidden in name], forbidden

    def test_the_identity_covers_every_field_or_excludes_it_deliberately(
        self,
    ) -> None:
        """A field added without entering the identity fails the build.

        Otherwise two runs differing in that field would claim one identity, and
        criterion 2's guarantee would quietly stop holding for it.
        """
        names = {field.name for field in fields(FrozenWorldInputs)}
        assert IDENTITY_FIELDS_READ | IDENTITY_FIELDS_EXCLUDED == names
        assert IDENTITY_FIELDS_READ & IDENTITY_FIELDS_EXCLUDED == frozenset()

    def test_no_authored_reading_reaches_the_inputs(self) -> None:
        definition = scenario()
        executed = run_to_end(draft(definition=definition), definition)
        parameter_ids = (
            {item.parameter_id for item in executed.inputs.initial_values}
            | {item.parameter_id for item in executed.inputs.forcings}
            | {item.parameter_id for item in executed.inputs.causes}
        )
        assert "level-after-the-gap" not in parameter_ids
        assert "hand-recorded-level" not in parameter_ids
        # And both readings ARE on the frozen run, so their absence above is a
        # filter doing something rather than nothing having been there to filter.
        # Without this the assertions above would pass against a run that never
        # froze a reading at all.
        run = draft(definition=definition)
        frozen = {
            item.parameter_id
            for item in run.deterministic_identity.scenario.resolved_parameters
        }
        assert {"level-after-the-gap", "hand-recorded-level"} <= frozen

    def test_changing_an_authored_reading_and_an_expectation_changes_nothing(
        self,
    ) -> None:
        """The mutation table's private-expectation row, and the reading with it.

        Both are edited to values nothing could mistake for the truth, a Draft is
        frozen from the edited document, and the trajectory it produces is
        identical - including the frozen inputs' identity, because the readings
        and the oracles never enter it.
        """
        definition = scenario()
        baseline = run_to_end(draft(definition=definition), definition)

        edited = shipped_document()
        for entry in edited["timeline"]:
            for parameter in entry.get("parameters", []):
                if parameter["parameter_id"] in {
                    "level-after-the-gap",
                    "hand-recorded-level",
                }:
                    parameter["value"] = 12
        for expectation in edited["private_expectations"]:
            expectation["statement"] = (
                "A deliberately false oracle, so a kernel reading one would "
                "produce a different world and be caught doing it."
            )

        changed = scenario(edited)
        executed = run_to_end(draft(definition=changed), changed)

        assert executed.inputs == replace(
            baseline.inputs, run_id=executed.inputs.run_id
        )
        assert executed.trajectory.inputs_identity == (
            baseline.trajectory.inputs_identity
        )
        assert executed.trajectory.boundaries == baseline.trajectory.boundaries


def _tank_capacity_of(site) -> float:
    for component in site.foundation.components:
        for prop in component.properties or ():
            if prop.property_key == "tank-capacity":
                return prop.value
    raise AssertionError("the fixture site declares no tank capacity")


def _with_tank_capacity(site, capacity: float):
    """The same Site with its tank capacity changed, as a later edit would.

    Built by replacing the property rather than by editing the template, because
    a template change leaves existing Sites alone and what this is about is the
    Site itself moving under a run that has already frozen it.
    """
    return replace(
        site,
        foundation=replace(
            site.foundation,
            components=tuple(
                replace(
                    component,
                    properties=tuple(
                        replace(prop, value=capacity)
                        if prop.property_key == "tank-capacity"
                        else prop
                        for prop in (component.properties or ())
                    ),
                )
                for component in site.foundation.components
            ),
        ),
    )


class TestARateDeclaredOverAWindow:
    """A rate state effect, integrated once at the input boundary.

    The shipped document no longer declares one - the dispatch window stopped
    naming a consumption rate when the coefficient moved to the machine - so this
    branch of the adapter had no document to exercise it. An untested branch that
    turns a rate into a quantity is a hole in the one place the numeric policy
    allows an approximation, so it gets a document of its own.

    The example is the contract's own: fourteen litres an hour over four hours is
    fifty-six litres, and through a binary float it is 56.00000000000001.
    """

    def _rate_document(self) -> dict:
        document = shipped_document()
        for entry in document["timeline"]:
            if entry["event_id"] != "unaccounted-fuel-removal":
                continue
            entry["timing"]["duration_minutes"] = 240
            entry["state_effect"] = {
                "direction": "DECREASE",
                "rate_parameter_id": "removal-rate",
            }
            entry["parameters"] = [
                {
                    "parameter_id": "removal-rate",
                    "display_name": "Rate fuel leaves the tank",
                    "value": 14,
                    "unit": "L/h",
                    "execution_role": "CAUSAL_INPUT",
                    "state_key": TANK,
                    "execution_requirement": "REQUIRED",
                    "ownership": {
                        "owner": "SCENARIO_INPUT",
                        "initializes": False,
                    },
                }
            ]
        return document

    def test_the_rate_becomes_the_exact_quantity_the_author_meant(self) -> None:
        definition = scenario(self._rate_document())
        executed = run_to_end(draft(definition=definition), definition)

        cause = next(
            item
            for item in executed.inputs.causes
            if item.event_id == "unaccounted-fuel-removal"
        )
        assert cause.quantity == Fraction(56)
        assert cause.canonical_unit == "L"
        assert cause.dimension == "VOLUME"
        assert cause.duration_minutes == 240

    def test_the_trajectory_moves_that_quantity_in_full(self) -> None:
        definition = scenario(self._rate_document())
        executed = run_to_end(draft(definition=definition), definition)
        trajectory = executed.trajectory

        assert trajectory.outcome == "COMPLETED", trajectory.failure
        # 374.02 after the dispatch, then 56 L over sixteen steps of 3.5 L.
        assert trajectory.boundary_at(1500).stock(TANK) == AFTER_DISPATCH
        assert trajectory.boundary_at(1515).stock(TANK) == (
            AFTER_DISPATCH - Fraction(7, 2)
        )
        assert trajectory.boundary_at(1740).stock(TANK) == (
            AFTER_DISPATCH - Fraction(56)
        )
        moved = sum(
            (
                event.declared
                for event in trajectory.applied_events
                if event.event_id == "unaccounted-fuel-removal"
            ),
            Fraction(0),
        )
        assert moved == Fraction(56)
