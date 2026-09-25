"""Draft run setup: what is frozen, what is refused, and what blocks.

The load-bearing distinction in this file is the one `runs/refusals.py`
states, and every test here says which side of it the case falls on:

- a **refusal** means the request could not be frozen. No `run_id` was
  allocated and nothing was written, and each refusal test asserts the store
  is empty afterwards rather than only that an error was raised. An error
  raised after a write would look identical without that assertion.
- **`BLOCKED`** means everything was frozen and the run still may not
  execute. The Draft exists, it is persisted, and it carries inspectable
  reasons.

Every test starts from the one valid request in `run_fixtures.py` and breaks
it in exactly one way, so a refusal test is about the rule it names. A test
that built its own request could pass because the request was malformed in a
second way the service reached first - the shape of failure T017's review
found and T018 met twice more.
"""

from __future__ import annotations

from dataclasses import fields, replace

import pytest
from run_fixtures import (
    END_TIME,
    START_TIME,
    FakeRuns,
    FakeScenarios,
    FakeSites,
    component_property,
    default_supported_states,
    foundation_bound_states,
    model_profile,
    publication_profile,
    scenario,
    setup_request,
    site,
)
from scenario_fixtures import scenario_document

from assetops_backend.runs.models import (
    ANSWERER_BY_INITIALIZATION_OWNER,
    FROZEN_INPUT_ANSWERERS,
    RUN_EXECUTION_STATUSES,
    BlockingReason,
    DeterministicIdentity,
    SimulationRun,
)
from assetops_backend.runs.profiles import (
    MINIMAL_FUEL_TANK_MODEL,
    LAB_PUBLICATION_PROFILE,
    FoundationBinding,
    SupportedState,
    resolve_observation_binding,
    resolve_publication_identity,
)
from assetops_backend.runs.provenance import frozen_inputs
from assetops_backend.runs.refusals import RUN_SETUP_REFUSAL_KINDS, RunSetupRefused
from assetops_backend.runs.service import RunSetupService
from assetops_backend.runs.timezones import (
    TimeZoneDatabaseUnavailable,
    TimeZoneNotFound,
    validate_iana_timezone,
)
from assetops_backend.scenarios.execution import EXECUTION_CONTRACT_VERSION
from assetops_backend.scenarios.models import INITIALIZATION_OWNERS
from assetops_backend.scenarios.parsing import parse_scenario_document
from assetops_backend.scenarios.ports import ScenarioConfigurationInvalid
from assetops_backend.sites.models import Rating, SiteComponent


def service(
    *,
    runs: FakeRuns | None = None,
    sites: FakeSites | None = None,
    scenarios: FakeScenarios | None = None,
    model=None,
    publication=None,
) -> tuple[RunSetupService, FakeRuns]:
    """The service under test, with a store a test can inspect afterwards."""
    store = FakeRuns() if runs is None else runs
    return (
        RunSetupService(
            store,
            sites or FakeSites((site(),)),
            scenarios or FakeScenarios((scenario(),)),
            model_profiles=(model or model_profile(),),
            publication_profiles=(publication or publication_profile(),),
            now=lambda: "2026-09-21T09:00:00Z",
        ),
        store,
    )


def create(**overrides) -> tuple[SimulationRun, FakeRuns]:
    setup, store = service()
    return setup.create_draft_run(setup_request(**overrides)), store


def refuse(request: dict, **kwargs) -> tuple[RunSetupRefused, FakeRuns]:
    """Run one request that must be refused, and hand back the empty store."""
    setup, store = service(**kwargs)
    with pytest.raises(RunSetupRefused) as raised:
        setup.create_draft_run(request)
    return raised.value, store


class TestWhatAReadyDraftFreezes:
    def test_a_supported_scenario_reaches_ready(self) -> None:
        record, store = create()

        assert record.execution_status == "READY"
        assert record.lifecycle_status == "DRAFT"
        assert record.blocking_reasons == ()
        assert store.written == [record]

    def test_the_frozen_identity_carries_every_input_the_criterion_names(
        self,
    ) -> None:
        record, _ = create()
        identity = record.deterministic_identity

        assert identity.site.site_id == "MG-900"
        assert identity.site.foundation_version == 1
        assert identity.scenario.scenario_id == "example-scenario"
        assert identity.scenario.scenario_version == 2
        assert identity.interval.start_time == START_TIME
        assert identity.interval.end_time == END_TIME
        assert identity.interval.duration_minutes == 300
        assert identity.interval.timestep_minutes == 15
        assert identity.seed == 4242
        assert identity.profiles.model_profile_id == "example-model"
        assert identity.profiles.publication_profile_id == "example-publication"
        assert (
            identity.profiles.execution_contract_version
            == EXECUTION_CONTRACT_VERSION
        )
        assert [item.state_key for item in identity.initialization_inputs] == [
            "example-stored-volume"
        ]
        assert [item.source_id for item in identity.observation_bindings] == [
            "example-device-reading",
            "example-hand-record",
        ]
        assert identity.publication.simulator_source_id == (
            "example-simulator-source"
        )
        assert identity.publication.gateway_id == "example-gateway"
        assert [item.mapping_id for item in identity.signal_mappings] == [
            "example-store-level"
        ]

    def test_the_intervention_history_is_ordered_and_empty(self) -> None:
        """Nothing in this build can inject one, and the order is the record."""
        record, _ = create()

        assert record.deterministic_identity.intervention_history == ()
        assert isinstance(
            record.deterministic_identity.intervention_history, tuple
        )

    def test_the_run_freezes_the_site_time_zone(self) -> None:
        record, _ = create()

        assert record.deterministic_identity.site.timezone == "Africa/Kampala"

    def test_the_cadence_comes_from_the_publication_profile(self) -> None:
        record, _ = create()
        bindings = {
            binding.source_id: binding
            for binding in record.deterministic_identity.observation_bindings
        }

        device = bindings["example-device-reading"]
        assert device.cadence_minutes == 15

        # A person writing a value down reports at no rate, so there is no
        # cadence for anything to own and no reason to block. What that means
        # is read off the source kind rather than stored beside it.
        hand = bindings["example-hand-record"]
        assert hand.cadence_minutes is None
        assert hand.source_kind == "OPERATOR_RECORD"


class TestRunIdentity:
    def test_a_run_id_is_neither_the_site_nor_the_scenario(self) -> None:
        record, _ = create()

        assert record.run_id != record.deterministic_identity.site.site_id
        assert record.run_id != record.deterministic_identity.scenario.scenario_id
        assert record.run_id.startswith("run-")

    def test_two_drafts_from_identical_inputs_are_two_runs(self) -> None:
        """Overlapping Drafts are deliberately allowed, so identity is not
        derived from the inputs: two runs of one experiment are two runs."""
        setup, store = service()

        first = setup.create_draft_run(setup_request())
        second = setup.create_draft_run(setup_request())

        assert first.run_id != second.run_id
        assert (
            first.deterministic_identity == second.deterministic_identity
        ), "the frozen identity is the experiment, not the run"
        assert len(store.written) == 2

    def test_a_request_may_not_supply_a_run_id(self) -> None:
        error, store = refuse(setup_request(run_id="run-" + "0" * 32))

        assert error.kind == "REQUEST_INVALID"
        assert "run_id" in error.message
        assert store.written == []

    def test_a_scenario_label_never_becomes_a_site_id(self) -> None:
        record, _ = create()
        identity = record.deterministic_identity

        assert identity.site.site_id != identity.scenario.scenario_id
        assert identity.site.site_id == "MG-900"


class TestRefusalsAllocateNoRun:
    """Every one of these is a request that could not be frozen."""

    def test_an_unconfigured_site_is_refused(self) -> None:
        error, store = refuse(setup_request(), sites=FakeSites(()))

        assert error.kind == "VERSION_UNAVAILABLE"
        assert store.written == []

    def test_a_foundation_version_that_is_not_current_is_refused(self) -> None:
        error, store = refuse(setup_request(foundation_version=2))

        assert error.kind == "VERSION_UNAVAILABLE"
        assert "foundation version" in error.message
        assert store.written == []

    def test_a_scenario_version_that_is_not_saved_is_refused(self) -> None:
        error, store = refuse(setup_request(scenario_version=9))

        assert error.kind == "VERSION_UNAVAILABLE"
        assert store.written == []

    def test_a_profile_version_that_does_not_exist_is_refused(self) -> None:
        error, store = refuse(
            setup_request(
                model_profile={"profile_id": "example-model", "profile_version": 7}
            )
        )

        assert error.kind == "VERSION_UNAVAILABLE"
        assert store.written == []

    def test_a_site_the_scenario_does_not_target_is_refused(self) -> None:
        error, store = refuse(
            setup_request(site_id="MG-901"),
            sites=FakeSites((site(), site(site_id="MG-901"))),
        )

        assert error.kind == "TARGET_TOPOLOGY_UNSUPPORTED"
        assert store.written == []

    def test_a_foundation_with_no_topology_is_refused(self) -> None:
        error, store = refuse(
            setup_request(), sites=FakeSites((site(topology=None),))
        )

        assert error.kind == "TARGET_TOPOLOGY_UNSUPPORTED"
        assert "topology" in error.message
        assert store.written == []

    def test_an_unconfigured_device_signal_is_refused(self) -> None:
        error, store = refuse(
            setup_request(), sites=FakeSites((site(devices=()),))
        )

        assert error.kind == "COMPONENT_OR_SIGNAL_UNRESOLVED"
        assert store.written == []

    def test_a_malformed_interval_is_refused(self) -> None:
        error, store = refuse(
            setup_request(
                interval={"start_time": END_TIME, "end_time": START_TIME}
            )
        )

        assert error.kind == "INTERVAL_INVALID"
        assert store.written == []

    def test_an_interval_that_is_not_a_multiple_of_the_timestep_is_refused(
        self,
    ) -> None:
        error, store = refuse(setup_request(timestep_minutes=7))

        assert error.kind == "INTERVAL_INVALID"
        assert "whole multiple" in error.message
        assert store.written == []

    def test_an_entry_outside_the_interval_is_refused_by_name(self) -> None:
        """`DISPATCH_RULES` commits the product to naming the entry."""
        error, store = refuse(
            setup_request(
                interval={
                    "start_time": START_TIME,
                    "end_time": "2026-09-21T01:00:00Z",
                }
            )
        )

        assert error.kind == "INTERVAL_INVALID"
        assert "draw-window" in error.message
        assert store.written == []

    def test_an_unknown_unit_is_refused(self) -> None:
        error, store = refuse(
            setup_request(
                run_inputs=[
                    {"parameter_id": "draw-rate", "value": 1, "unit": "furlongs"}
                ]
            )
        )

        assert error.kind == "UNIT_INVALID"
        assert store.written == []

    def test_a_negative_volume_is_refused_at_setup(self) -> None:
        """The `invalid-rate` bound case, applied to a value a run supplies."""
        document = scenario_document()
        document["public_parameters"][2]["ownership"]["owner"] = "RUN_OVERRIDE"

        error, store = refuse(
            setup_request(
                run_inputs=[
                    {"parameter_id": "starting-level", "value": -5, "unit": "L"}
                ]
            ),
            scenarios=FakeScenarios(
                (
                    parse_scenario_document(
                        document, source="a test", origin="SHIPPED"
                    ),
                )
            ),
        )

        assert error.kind == "UNIT_INVALID"
        assert store.written == []

    def test_an_unreal_time_zone_is_refused(self) -> None:
        error, store = refuse(
            setup_request(),
            sites=FakeSites((site(timezone="Africa/Atlantis"),)),
        )

        assert error.kind == "TIMEZONE_NOT_IANA"
        assert store.written == []


def foundation_owned_document() -> dict:
    """The example scenario with its initial value owned by the Foundation.

    Two edits, not one, and the second is the T020A narrowing: a parameter
    whose declared owner is the Site's Foundation states no value at all
    (`D-2026-09-22-foundation-value-declaration`), so the number comes out
    with the owner change. A document that kept it is refused by the parser,
    which is what every test below would otherwise trip over.
    """
    document = scenario_document()
    parameter = document["public_parameters"][2]
    parameter["ownership"]["owner"] = "SITE_FOUNDATION"
    parameter.pop("value")
    return document


class TestNothingIsDefaulted:
    def test_a_value_the_run_owns_must_be_supplied(self) -> None:
        """`RUN_OVERRIDE` means the run supplies it. Falling back to the
        scenario's number would make the declared owner a suggestion."""
        document = scenario_document()
        document["public_parameters"][2]["ownership"]["owner"] = "RUN_OVERRIDE"

        error, store = refuse(
            setup_request(),
            scenarios=FakeScenarios(
                (
                    parse_scenario_document(
                        document, source="a test", origin="SHIPPED"
                    ),
                )
            ),
        )

        assert error.kind == "INITIALIZATION_INPUT_MISSING"
        assert "starting-level" in error.message
        assert store.written == []

    def test_a_supplied_run_value_is_the_one_frozen(self) -> None:
        document = scenario_document()
        document["public_parameters"][2]["ownership"]["owner"] = "RUN_OVERRIDE"
        scenarios = FakeScenarios(
            (
                parse_scenario_document(
                    document, source="a test", origin="SHIPPED"
                ),
            )
        )

        setup, _ = service(scenarios=scenarios)
        record = setup.create_draft_run(
            setup_request(
                run_inputs=[
                    {"parameter_id": "starting-level", "value": 250, "unit": "L"}
                ]
            )
        )

        initial = record.deterministic_identity.initialization_inputs[0]
        assert initial.value == 250.0
        assert initial.answered_by == "RUN_INPUT"

    def test_a_value_the_scenario_owns_may_not_be_overridden(self) -> None:
        error, store = refuse(
            setup_request(
                run_inputs=[
                    {"parameter_id": "starting-level", "value": 250, "unit": "L"}
                ]
            )
        )

        assert error.kind == "REQUEST_INVALID"
        assert "SCENARIO_INPUT" in error.message
        assert store.written == []

    def test_a_foundation_owned_value_still_needs_a_declared_binding(
        self,
    ) -> None:
        """Nothing matches a state to a component by the look of its name.

        It blocks rather than refusing since the T019 user review moved the
        line: the fix is to choose a profile that declares the binding, which
        is the fix for every blocking reason there is, and refusing would
        hand the person nothing to inspect.
        """
        document = foundation_owned_document()

        setup, store = service(
            scenarios=FakeScenarios(
                (
                    parse_scenario_document(
                        document, source="a test", origin="SHIPPED"
                    ),
                )
            )
        )
        record = setup.create_draft_run(setup_request())

        assert record.execution_status == "BLOCKED"
        assert [reason.kind for reason in record.blocking_reasons] == [
            "INITIAL_VALUE_NOT_RESOLVED"
        ]
        assert record.blocking_reasons[0].subject == "example-stored-volume"
        assert "binding" in record.blocking_reasons[0].statement
        assert store.written == [record]

        # Frozen in full, with the hole named rather than papered over.
        initial = record.deterministic_identity.initialization_inputs[0]
        assert initial.value is None
        assert initial.canonical_value is None
        assert initial.unit == "L"
        assert initial.answered_by == "MODEL_PROFILE"

    def test_the_declared_property_is_what_a_run_freezes(self) -> None:
        """The whole point of the carrier, end to end.

        The scenario declares the need and no number; the profile's binding
        names the component type, the property and the unit; the Foundation
        declares the property; and what the run freezes is the Foundation's
        value with the Foundation named as its answerer. The component here
        is rated 500 L and declares a 200 L capacity property deliberately:
        if the resolution still read the rating, the frozen value would be
        500 and this would fail.
        """
        setup, _ = service(
            scenarios=self._foundation_owned(),
            sites=FakeSites(
                (
                    site(
                        components=(
                            SiteComponent(
                                component_id="example-store",
                                component_type="FUEL_TANK",
                                display_name="Stored volume",
                                rating=Rating(value=500.0, unit="L"),
                                properties=(
                                    component_property(value=200.0),
                                ),
                            ),
                        )
                    ),
                )
            ),
            model=model_profile(supported_states=foundation_bound_states()),
        )
        record = setup.create_draft_run(setup_request())

        initial = record.deterministic_identity.initialization_inputs[0]
        assert initial.value == 200.0
        assert initial.answered_by == "SITE_FOUNDATION"
        assert "foundation version 1" in initial.answered_by_detail
        # The detail names the component and the property, because "the
        # foundation answered" is not the same fact as which declaration did.
        # The whole phrase, not the two identifiers: the state key here is
        # `example-stored-volume` and it contains `example-store`, so a
        # containment check on the name alone would pass against a detail that
        # named neither.
        assert (
            "component example-store property tank-capacity"
            in initial.answered_by_detail
        )

    def test_changing_one_property_changes_only_its_own_answer(self) -> None:
        """Two sites, one scenario, one profile: the answer follows the site.

        This is the property the carrier exists for. Nothing about the
        scenario or the profile changes between the two runs, so a frozen
        value that moved with the site's own declaration is the site being
        the authority - and a frozen value that did not would mean the number
        was still coming from somewhere else.
        """

        def frozen_for(capacity: float) -> float | None:
            setup, _ = service(
                scenarios=self._foundation_owned(),
                sites=FakeSites(
                    (
                        site(
                            components=(
                                SiteComponent(
                                    component_id="example-store",
                                    component_type="FUEL_TANK",
                                    display_name="Stored volume",
                                    rating=Rating(value=500.0, unit="L"),
                                    properties=(
                                        component_property(value=capacity),
                                    ),
                                ),
                            )
                        ),
                    )
                ),
                model=model_profile(
                    supported_states=foundation_bound_states()
                ),
            )
            record = setup.create_draft_run(setup_request())
            return record.deterministic_identity.initialization_inputs[0].value

        assert frozen_for(200.0) == 200.0
        assert frozen_for(320.0) == 320.0

    def _foundation_owned(self) -> FakeScenarios:
        return FakeScenarios(
            (
                parse_scenario_document(
                    foundation_owned_document(),
                    source="a test",
                    origin="SHIPPED",
                ),
            )
        )

    def test_two_foundation_answers_are_never_chosen_between(self) -> None:
        """Two components that both fit the binding are two answers.

        Blocks rather than refusing, by the same discriminator: a binding
        specific enough to tell them apart is a profile's to carry, so a
        different profile would resolve it.
        """
        setup, store = service(
            scenarios=self._foundation_owned(),
            sites=FakeSites(
                (
                    site(
                        components=(
                            SiteComponent(
                                component_id="example-store",
                                component_type="FUEL_TANK",
                                display_name="One store",
                                rating=Rating(value=200.0, unit="L"),
                            ),
                            SiteComponent(
                                component_id="second-store",
                                component_type="FUEL_TANK",
                                display_name="Another store",
                                rating=Rating(value=200.0, unit="L"),
                            ),
                        )
                    ),
                )
            ),
            model=model_profile(supported_states=foundation_bound_states()),
        )
        record = setup.create_draft_run(setup_request())

        assert [reason.kind for reason in record.blocking_reasons] == [
            "INITIAL_VALUE_NOT_RESOLVED"
        ]
        assert "more than one" in record.blocking_reasons[0].statement
        assert store.written == [record]

    def test_a_binding_that_matches_nothing_blocks(self) -> None:
        """The second case the user left to the Implementer.

        The Foundation's answer is only locatable through the profile's
        binding, so failing to locate it is a joint fact about the pair - and
        the profile is the half a person can change on the setup form. A
        binding on another component type or unit might match something this
        site does declare.
        """
        setup, store = service(
            scenarios=self._foundation_owned(),
            sites=FakeSites((site(components=()),)),
            model=model_profile(supported_states=foundation_bound_states()),
        )
        record = setup.create_draft_run(setup_request())

        assert [reason.kind for reason in record.blocking_reasons] == [
            "INITIAL_VALUE_NOT_RESOLVED"
        ]
        assert "declares no such component" in record.blocking_reasons[0].statement
        assert store.written == [record]

    def test_a_binding_in_another_unit_blocks(self) -> None:
        """The third case, decided beyond the two the user named.

        A binding whose unit is not the scenario's is the profile and the
        scenario disagreeing about what kind of quantity this is, and the
        profile is the changeable half. Leaving it a refusal while the cases
        either side of it moved would be one rule applied at one position.
        """
        bound_to_a_percentage = (
            SupportedState(
                state_key="example-stored-volume",
                scope="COMPONENT",
                supported_roles=frozenset(
                    {"CAUSAL_INPUT", "REPORTED_OBSERVATION"}
                ),
                foundation_binding=FoundationBinding(
                    component_type="BATTERY",
                    property_key="reserve-state-of-charge",
                    unit="%",
                ),
                statement="Bound to a property in the wrong quantity.",
            ),
            default_supported_states()[1],
        )

        setup, store = service(
            scenarios=self._foundation_owned(),
            sites=FakeSites(
                (
                    site(
                        components=(
                            SiteComponent(
                                component_id="example-battery",
                                component_type="BATTERY",
                                display_name="A battery",
                                rating=Rating(value=200.0, unit="kWh"),
                                properties=(
                                    component_property(
                                        property_key="reserve-state-of-charge",
                                        value=25.0,
                                        unit="%",
                                        kind="CONTROL",
                                    ),
                                ),
                            ),
                        )
                    ),
                )
            ),
            model=model_profile(supported_states=bound_to_a_percentage),
        )
        record = setup.create_draft_run(setup_request())

        assert [reason.kind for reason in record.blocking_reasons] == [
            "INITIAL_VALUE_NOT_RESOLVED"
        ]
        # The scenario declares litres and the binding a percentage, so the
        # two disagree about what kind of quantity this is. The phrase names
        # both halves; `"in L"` alone said nothing about the profile's unit,
        # which is the field `TestTheBindingsOwnUnitIsChecked` covers in
        # isolation.
        assert (
            "declares example-stored-volume in L"
            in record.blocking_reasons[0].statement
        )
        assert (
            "reserve-state-of-charge property declared in %"
            in record.blocking_reasons[0].statement
        )
        assert store.written == [record]

    def test_a_component_declaring_no_such_property_blocks(self) -> None:
        """The fifth case, and the one the record spent a decision on.

        The component the binding names is there; the property is not. It
        blocks rather than refusing
        (`D-2026-09-22-foundation-property-absent-blocks`): after T020A the
        binding names the property as much as the component type, so a
        different profile naming a different property may well find something
        this Foundation does declare - which is the discriminator, and the
        profile is the half a person can change on the setup form.

        This is also the case a Site created before T020A lands in: its
        components carry ratings and no properties at all, so its Drafts
        block here with the property named rather than failing to be created.
        """
        setup, store = service(
            scenarios=self._foundation_owned(),
            sites=FakeSites(
                (
                    site(
                        components=(
                            SiteComponent(
                                component_id="example-store",
                                component_type="FUEL_TANK",
                                display_name="Stored volume",
                                rating=Rating(value=500.0, unit="L"),
                                properties=None,
                            ),
                        )
                    ),
                )
            ),
            model=model_profile(supported_states=foundation_bound_states()),
        )
        record = setup.create_draft_run(setup_request())

        assert record.execution_status == "BLOCKED"
        assert [reason.kind for reason in record.blocking_reasons] == [
            "INITIAL_VALUE_NOT_RESOLVED"
        ]
        reason = record.blocking_reasons[0]
        assert reason.subject == "example-stored-volume"
        assert "tank-capacity" in reason.statement
        # The phrase, not the component id on its own. The state key here is
        # `example-stored-volume`, which CONTAINS `example-store` as a
        # substring, so a naive containment check passes against the
        # no-such-component message too - and a deliberate violation proved
        # exactly that before this line was written.
        assert "property of component example-store," in reason.statement
        assert "declares no such property on it" in reason.statement
        assert "another component" in reason.statement
        # The Draft is persisted and inspectable, which is the difference
        # between a blocking reason and a refusal.
        assert store.written == [record]

    def test_no_other_component_is_searched_for_a_convenient_value(
        self,
    ) -> None:
        """The absent-property case may not be rescued by a second asset.

        The binding names a FUEL_TANK and there are two, one of which does
        declare the property. Narrowing the candidate set to components that
        happen to declare it would resolve this to 320 L and call it an
        answer. It blocks instead, on the ambiguity, because which tank the
        binding means is a question only an addressed binding answers - and
        that is T020A1.
        """
        setup, _ = service(
            scenarios=self._foundation_owned(),
            sites=FakeSites(
                (
                    site(
                        components=(
                            SiteComponent(
                                component_id="example-store",
                                component_type="FUEL_TANK",
                                display_name="The tank the binding means",
                                rating=Rating(value=500.0, unit="L"),
                                properties=None,
                            ),
                            SiteComponent(
                                component_id="second-store",
                                component_type="FUEL_TANK",
                                display_name="A tank that does declare one",
                                rating=Rating(value=320.0, unit="L"),
                                properties=(component_property(value=320.0),),
                            ),
                        )
                    ),
                )
            ),
            model=model_profile(supported_states=foundation_bound_states()),
        )
        record = setup.create_draft_run(setup_request())

        reason = record.blocking_reasons[0]
        assert reason.kind == "INITIAL_VALUE_NOT_RESOLVED"
        assert "more than one" in reason.statement
        assert (
            record.deterministic_identity.initialization_inputs[0].value is None
        )

    def test_the_retired_contradiction_kind_is_gone_with_its_producer(
        self,
    ) -> None:
        """A refusal kind nothing can produce is a claim the product cannot make.

        `INITIAL_VALUE_ANSWERS_DISAGREE` had exactly one producer: a
        Foundation value compared against the number the scenario stated the
        Foundation declares. After
        `D-2026-09-22-foundation-value-declaration` there is no position in
        any document for that number, so the kind and its producer were
        retired together under
        `D-2026-09-22-expiry-follows-the-condition`.

        Both halves are asserted. The vocabulary no longer carries the name,
        and the parser refuses the document that was the only way to reach
        it - so a later change that re-added the kind would have to re-add
        the authoring position too, and this test would say so.
        """
        assert "INITIAL_VALUE_ANSWERS_DISAGREE" not in RUN_SETUP_REFUSAL_KINDS
        with pytest.raises(ValueError):
            RunSetupRefused("INITIAL_VALUE_ANSWERS_DISAGREE", "anything")

        document = scenario_document()
        document["public_parameters"][2]["ownership"]["owner"] = "SITE_FOUNDATION"
        with pytest.raises(ScenarioConfigurationInvalid) as raised:
            parse_scenario_document(document, source="a test", origin="SHIPPED")
        assert "states no number" in str(raised.value)

    def test_the_missing_run_override_keeps_its_own_refusal_line(self) -> None:
        """The kind that stays, and stays on the other side of the line.

        `INITIALIZATION_INPUT_MISSING` is a value whose DECLARED OWNER did
        not answer - a run override the request did not supply - and no
        profile can put it there, so it refuses rather than blocking. The
        retirement above took the contradiction out of the refusal
        vocabulary; it did not touch this.
        """
        missing = self._missing_run_override()

        assert missing.kind == "INITIALIZATION_INPUT_MISSING"
        assert missing.kind in RUN_SETUP_REFUSAL_KINDS

    def _missing_run_override(self) -> RunSetupRefused:
        document = scenario_document()
        document["public_parameters"][2]["ownership"]["owner"] = "RUN_OVERRIDE"
        error, store = refuse(
            setup_request(),
            scenarios=FakeScenarios(
                (
                    parse_scenario_document(
                        document, source="a test", origin="SHIPPED"
                    ),
                )
            ),
        )
        assert store.written == []
        return error

    def test_a_model_rule_value_with_no_rule_blocks(self) -> None:
        """No profile in this build carries a model-supplied initial value.

        T020A did not add that carrier either: a model profile declaring the
        need is option C of
        `D-2026-09-22-foundation-value-declaration`, a follower with a
        trigger rather than a slice. Until something carries it this is the
        profile failing to answer, which is the same fact as a missing
        binding."""
        document = scenario_document()
        document["public_parameters"][2]["ownership"]["owner"] = "MODEL_RULE"

        setup, store = service(
            scenarios=FakeScenarios(
                (
                    parse_scenario_document(
                        document, source="a test", origin="SHIPPED"
                    ),
                )
            )
        )
        record = setup.create_draft_run(setup_request())

        assert [reason.kind for reason in record.blocking_reasons] == [
            "INITIAL_VALUE_NOT_RESOLVED"
        ]
        assert store.written == [record]
        assert (
            record.deterministic_identity.initialization_inputs[0].value is None
        )


class TestBlockedDraftsArePersisted:
    """A blocked run exists, is written, and says why it may not execute."""

    def test_an_unsupported_required_state_blocks_and_persists(self) -> None:
        setup, store = service(
            model=model_profile(
                supported_states=(default_supported_states()[0],)
            )
        )
        record = setup.create_draft_run(setup_request())

        assert record.execution_status == "BLOCKED"
        assert [reason.kind for reason in record.blocking_reasons] == [
            "STATE_NOT_SUPPORTED"
        ]
        assert record.blocking_reasons[0].subject == "example-demand"
        assert store.written == [record]

    def test_an_unsupported_role_on_a_supported_state_blocks(self) -> None:
        narrowed = (
            SupportedState(
                state_key="example-stored-volume",
                scope="COMPONENT",
                supported_roles=frozenset({"CAUSAL_INPUT"}),
                foundation_binding=None,
                statement="Caused but never reported.",
            ),
            default_supported_states()[1],
        )
        setup, store = service(model=model_profile(supported_states=narrowed))
        record = setup.create_draft_run(setup_request())

        assert [reason.kind for reason in record.blocking_reasons] == [
            "ROLE_NOT_SUPPORTED"
        ]
        assert store.written == [record]

    def test_one_unmodelled_state_is_one_row_however_many_roles(self) -> None:
        """`subject` exists so two reasons of one kind are two facts.

        A Foundation-owned value on a state the profile does not model used
        to produce three rows for one state: STATE_NOT_SUPPORTED once per
        execution role, differing only in which role the prose named, plus
        the unresolved initial value. A reader counting rows counted the
        same problem twice.
        """
        document = foundation_owned_document()
        scenarios = FakeScenarios(
            (
                parse_scenario_document(
                    document, source="a test", origin="SHIPPED"
                ),
            )
        )

        # The stored volume is used as a cause and as a reading, and this
        # profile models neither it nor anything else about it.
        setup, _ = service(
            scenarios=scenarios,
            model=model_profile(
                supported_states=(default_supported_states()[1],)
            ),
        )
        record = setup.create_draft_run(setup_request())

        about_the_state = [
            reason
            for reason in record.blocking_reasons
            if reason.subject == "example-stored-volume"
        ]
        assert [reason.kind for reason in about_the_state] == [
            "STATE_NOT_SUPPORTED",
            "INITIAL_VALUE_NOT_RESOLVED",
        ]
        # Two facts about one state: the profile cannot execute it, and
        # nothing answered for where it starts. Not the same fact twice.
        assert len({reason.kind for reason in about_the_state}) == 2

    def test_a_state_unsupported_in_two_roles_names_both(self) -> None:
        """The complementary half: a role failure really is one per role, so
        its subject carries the role and the two rows stay two."""
        narrowed = (
            SupportedState(
                state_key="example-stored-volume",
                scope="COMPONENT",
                supported_roles=frozenset({"FORCING_INPUT"}),
                foundation_binding=None,
                statement="Modelled, but in neither role this scenario uses.",
            ),
            default_supported_states()[1],
        )
        setup, _ = service(model=model_profile(supported_states=narrowed))
        record = setup.create_draft_run(setup_request())

        assert sorted(
            reason.subject
            for reason in record.blocking_reasons
            if reason.kind == "ROLE_NOT_SUPPORTED"
        ) == [
            "example-stored-volume as CAUSAL_INPUT",
            "example-stored-volume as REPORTED_OBSERVATION",
        ]

    def test_an_optional_unsupported_input_is_recorded_and_does_not_block(
        self,
    ) -> None:
        document = scenario_document()
        document["timeline"][0]["execution_requirement"] = "OPTIONAL"
        document["timeline"][0]["parameters"][0]["execution_requirement"] = (
            "OPTIONAL"
        )
        scenarios = FakeScenarios(
            (
                parse_scenario_document(
                    document, source="a test", origin="SHIPPED"
                ),
            )
        )

        setup, _ = service(
            scenarios=scenarios,
            model=model_profile(
                supported_states=(default_supported_states()[0],)
            ),
        )
        record = setup.create_draft_run(setup_request())

        assert record.execution_status == "READY"
        assert [
            item.state_key for item in record.unsupported_optional_inputs
        ] == ["example-demand"]

    def test_an_unresolved_cadence_blocks(self) -> None:
        setup, store = service(
            publication=publication_profile(cadence_minutes=None)
        )
        record = setup.create_draft_run(setup_request())

        assert [reason.kind for reason in record.blocking_reasons] == [
            "CADENCE_NOT_RESOLVED"
        ]
        assert record.blocking_reasons[0].subject == "example-device-reading"
        assert store.written == [record]

        binding = {
            item.source_id: item
            for item in record.deterministic_identity.observation_bindings
        }["example-device-reading"]
        assert binding.cadence_minutes is None
        assert binding.source_kind == "DEVICE_SIGNAL"

    def test_an_unresolved_source_identity_blocks(self) -> None:
        setup, store = service(
            publication=publication_profile(simulator_source_id=None)
        )
        record = setup.create_draft_run(setup_request())

        assert [reason.kind for reason in record.blocking_reasons] == [
            "SOURCE_IDENTITY_NOT_RESOLVED"
        ]
        assert store.written == [record]

    def test_an_unresolved_gateway_identity_blocks(self) -> None:
        setup, store = service(
            publication=publication_profile(gateway_id=None)
        )
        record = setup.create_draft_run(setup_request())

        assert [reason.kind for reason in record.blocking_reasons] == [
            "GATEWAY_IDENTITY_NOT_RESOLVED"
        ]
        assert store.written == [record]

    def test_an_unreached_reading_does_not_block_a_run(self) -> None:
        """Amendment 1's proposal (e), measured as an absence.

        Run setup has no kernel, so it cannot decide whether declared causes
        reach a declared reading: that is a statement about what a run would
        produce. An earlier version of this slice blocked on it. This is the
        same document that blocked then - one authored value changed so the
        causes do not reach the reading - and it is `READY` now.

        Asserted as `READY` rather than as "no observation reason", because
        an absence test that only looked for a kind would pass on a build
        where the reason had been renamed.
        """
        document = scenario_document()
        document["timeline"][2]["parameters"][0]["value"] = 180

        setup, store = service(
            scenarios=FakeScenarios(
                (
                    parse_scenario_document(
                        document, source="a test", origin="SHIPPED"
                    ),
                )
            )
        )
        record = setup.create_draft_run(setup_request())

        assert record.execution_status == "READY"
        assert record.blocking_reasons == ()
        assert store.written == [record]

    def test_no_blocking_kind_is_about_the_scenario_disagreeing_with_itself(
        self,
    ) -> None:
        """The vocabulary, not one code path.

        Every blocking kind says something about the selected profile: an
        input it does not model, or a value it does not resolve. A kind that
        judged the scenario's own arithmetic would be (e) returning, and
        deleting one call site would not stop it.
        """
        from assetops_backend.runs.models import BLOCKING_REASON_KINDS

        assert BLOCKING_REASON_KINDS == {
            "STATE_NOT_SUPPORTED",
            "ROLE_NOT_SUPPORTED",
            "CADENCE_NOT_RESOLVED",
            "SOURCE_IDENTITY_NOT_RESOLVED",
            "GATEWAY_IDENTITY_NOT_RESOLVED",
            "INITIAL_VALUE_NOT_RESOLVED",
        }

    def test_run_setup_never_reconciles(self) -> None:
        """The reference implementation has no caller in the run domain.

        A scan rather than a mock, because the point is that no module in the
        domain can reach it, not that one code path did not on one input.

        It looks for a call or an import rather than for the name, because
        the service's own docstring explains why it does not call it - and a
        scan that banned the word would ban the explanation, which is how a
        guard ends up relaxed by whoever meets it next.
        """
        import re
        from pathlib import Path

        domain = Path(__file__).resolve().parents[1] / "assetops_backend" / "runs"
        modules = sorted(domain.rglob("*.py"))
        reaches = re.compile(
            r"reconcile_reported_observations\s*\(|import[^\n]*"
            r"reconcile_reported_observations"
        )

        assert modules, "the run domain was not scanned, so this proves nothing"
        for module in modules:
            assert not reaches.search(
                module.read_text(encoding="utf-8")
            ), module.name

    def test_a_blocked_run_still_froze_everything(self) -> None:
        """A blocked Draft is a fully frozen Draft. If it were not, the
        refusal line would have moved and a reader would have nothing to
        inspect in order to decide what to change."""
        setup, _ = service(
            publication=publication_profile(
                cadence_minutes=None,
                simulator_source_id=None,
                gateway_id=None,
            )
        )
        record = setup.create_draft_run(setup_request())

        assert len(record.blocking_reasons) == 3
        assert record.deterministic_identity.site.site_id == "MG-900"
        assert record.deterministic_identity.initialization_inputs
        assert record.deterministic_identity.signal_mappings


class TestTheStatusIsComputed:
    def test_a_ready_run_may_not_carry_a_reason(self) -> None:
        record, _ = create()

        with pytest.raises(ValueError):
            SimulationRun(
                run_id=record.run_id,
                lifecycle_status="DRAFT",
                execution_status="READY",
                created_at=record.created_at,
                deterministic_identity=record.deterministic_identity,
                blocking_reasons=(
                    __import__(
                        "assetops_backend.runs.models", fromlist=["BlockingReason"]
                    ).BlockingReason(
                        kind="STATE_NOT_SUPPORTED",
                        subject="anything",
                        statement="anything",
                    ),
                ),
                unsupported_optional_inputs=(),
            )

    def test_a_blocked_run_may_not_carry_none(self) -> None:
        record, _ = create()

        with pytest.raises(ValueError):
            SimulationRun(
                run_id=record.run_id,
                lifecycle_status="DRAFT",
                execution_status="BLOCKED",
                created_at=record.created_at,
                deterministic_identity=record.deterministic_identity,
                blocking_reasons=(),
                unsupported_optional_inputs=(),
            )

    def test_a_ready_run_may_not_carry_an_unanswered_initial_value(
        self,
    ) -> None:
        """A frozen identity with a hole in it is not a runnable identity.

        The absent case exists because something blocked the run, so a READY
        run carrying one would be a run whose status and whose inputs
        disagree. Constructed directly, because the service cannot produce
        it - which is the point of asserting it on the record.
        """
        record, _ = create()
        identity = record.deterministic_identity
        holed = replace(
            identity,
            initialization_inputs=(
                replace(
                    identity.initialization_inputs[0],
                    value=None,
                    canonical_value=None,
                ),
            ),
        )

        with pytest.raises(ValueError):
            SimulationRun(
                run_id=record.run_id,
                lifecycle_status="DRAFT",
                execution_status="READY",
                created_at=record.created_at,
                deterministic_identity=holed,
                blocking_reasons=(),
                unsupported_optional_inputs=(),
            )

    def test_an_unanswered_value_needs_a_reason_about_that_state(
        self,
    ) -> None:
        """The gap the final review constructed, closed.

        The first version of this invariant asked only whether the run
        carried ANY blocking reason, which its own docstring already claimed
        more than. A value absent for one state, beside a reason about an
        unrelated profile identity, satisfied it - a persisted Draft whose
        frozen table says "not resolved" for a state while the blocking table
        explains nothing about it.
        """
        record, _ = create()
        identity = record.deterministic_identity
        holed = replace(
            identity,
            initialization_inputs=(
                replace(
                    identity.initialization_inputs[0],
                    value=None,
                    canonical_value=None,
                ),
            ),
        )
        elsewhere = BlockingReason(
            kind="GATEWAY_IDENTITY_NOT_RESOLVED",
            subject="example-publication",
            statement="Nothing about the state whose value is missing.",
        )

        with pytest.raises(ValueError) as raised:
            SimulationRun(
                run_id=record.run_id,
                lifecycle_status="DRAFT",
                execution_status="BLOCKED",
                created_at=record.created_at,
                deterministic_identity=holed,
                blocking_reasons=(elsewhere,),
                unsupported_optional_inputs=(),
            )

        assert "example-stored-volume" in str(raised.value)

    def test_a_reason_about_the_same_state_satisfies_it(self) -> None:
        """The other half, so the rule is not simply refusing everything."""
        record, _ = create()
        identity = record.deterministic_identity
        state_key = identity.initialization_inputs[0].state_key
        holed = replace(
            identity,
            initialization_inputs=(
                replace(
                    identity.initialization_inputs[0],
                    value=None,
                    canonical_value=None,
                ),
            ),
        )

        blocked = SimulationRun(
            run_id=record.run_id,
            lifecycle_status="DRAFT",
            execution_status="BLOCKED",
            created_at=record.created_at,
            deterministic_identity=holed,
            blocking_reasons=(
                BlockingReason(
                    kind="INITIAL_VALUE_NOT_RESOLVED",
                    subject=state_key,
                    statement="The profile declares no binding for it.",
                ),
            ),
            unsupported_optional_inputs=(),
        )

        assert blocked.execution_status == "BLOCKED"

    def test_a_record_may_not_hold_half_an_absent_value(self) -> None:
        """The pairing the record's own docstring states as its property.

        It was enforced only where documents are read, so an in-process
        record could hold one number without the other.
        """
        record, _ = create()
        identity = record.deterministic_identity

        for absent, present in (("value", "canonical_value"), ("canonical_value", "value")):
            half = replace(
                identity,
                initialization_inputs=(
                    replace(
                        identity.initialization_inputs[0], **{absent: None}
                    ),
                ),
            )
            with pytest.raises(ValueError) as raised:
                SimulationRun(
                    run_id=record.run_id,
                    lifecycle_status="DRAFT",
                    execution_status="BLOCKED",
                    created_at=record.created_at,
                    deterministic_identity=half,
                    blocking_reasons=(
                        BlockingReason(
                            kind="INITIAL_VALUE_NOT_RESOLVED",
                            subject=identity.initialization_inputs[0].state_key,
                            statement="A reason about the same state.",
                        ),
                    ),
                    unsupported_optional_inputs=(),
                )
            assert present in str(raised.value) or "two numbers" in str(
                raised.value
            )

    def test_the_status_vocabulary_has_no_executing_value(self) -> None:
        """Nothing in this build can run, so no status says it did."""
        assert RUN_EXECUTION_STATUSES == {"READY", "BLOCKED"}


class TestEveryFrozenValueNamesAnAnswerer:
    def test_every_identity_field_is_represented(self) -> None:
        """The completeness guard: a field added to the frozen identity with
        no answerer fails here rather than arriving on a screen in a column
        with nothing under it.

        Top level only, which is why the audit below exists as well: this
        compares row coverage against the ten fields of the identity, and a
        field added to any of the records nested inside them would leave it
        passing. The review found exactly that.
        """
        record, _ = create()
        rows = frozen_inputs(record.deterministic_identity)

        assert rows, "the provenance rows are empty, so this proves nothing"
        covered = {row.identity_field for row in rows}
        declared = {field.name for field in fields(DeterministicIdentity)}

        assert covered == declared

    def test_every_nested_frozen_field_is_classified(self) -> None:
        """The audit the top-level check cannot be: every field of every
        record inside the frozen identity, classified as rendered on the
        summary or deliberately not.

        Not every nested value belongs on a screen - a canonical restatement
        of a value the row already shows is one number twice - so the honest
        guard is not "everything is rendered" but "somebody decided about
        everything". A field added anywhere in the frozen identity fails here
        until it is classified, which is the same shape as T017's identifier
        audit and exists for the same reason.
        """
        # Rendered on the setup summary as part of a row.
        rendered = {
            ("FrozenSiteBinding", "site_id"),
            ("FrozenSiteBinding", "foundation_version"),
            ("FrozenSiteBinding", "foundation_valid_from"),
            ("FrozenSiteBinding", "site_type"),
            ("FrozenSiteBinding", "timezone"),
            ("FrozenScenarioBinding", "scenario_id"),
            ("FrozenScenarioBinding", "scenario_version"),
            ("FrozenScenarioBinding", "resolved_parameters"),
            ("FrozenParameter", "parameter_id"),
            ("FrozenParameter", "value"),
            ("FrozenParameter", "unit"),
            ("FrozenParameter", "answered_by"),
            ("FrozenInterval", "start_time"),
            ("FrozenInterval", "end_time"),
            ("FrozenInterval", "duration_minutes"),
            ("FrozenInterval", "timestep_minutes"),
            ("FrozenProfileBinding", "model_profile_id"),
            ("FrozenProfileBinding", "model_profile_version"),
            ("FrozenProfileBinding", "publication_profile_id"),
            ("FrozenProfileBinding", "publication_profile_version"),
            ("FrozenProfileBinding", "execution_contract_version"),
            ("FrozenInitializationInput", "state_ref"),
            # The three fields of the address, all three of which
            # the rendered row shows: the row reads "Initial
            # fuel-tank-capacity@fuel-tank", which is the state key,
            # the scope and the component the run resolved.
            ("StateRef", "state_key"),
            ("StateRef", "scope"),
            ("StateRef", "component_id"),
            ("FrozenInitializationInput", "value"),
            ("FrozenInitializationInput", "unit"),
            ("FrozenInitializationInput", "answered_by"),
            ("FrozenInitializationInput", "answered_by_detail"),
            ("FrozenObservationBinding", "source_id"),
            ("FrozenObservationBinding", "cadence_minutes"),
            ("FrozenPublicationIdentity", "simulator_source_id"),
            ("FrozenPublicationIdentity", "gateway_id"),
            ("FrozenSignalMapping", "mapping_id"),
            ("FrozenSignalMapping", "device_id"),
            ("FrozenSignalMapping", "signal_id"),
            ("FrozenSignalMapping", "component_id"),
        }

        # Frozen and inspectable through the structured identity, and
        # deliberately not given a row of its own, with the reason.
        not_rendered = {
            # The parameter identity already names it on its row.
            ("FrozenInitializationInput", "parameter_id"),
            # A canonical restatement of the value beside it. One number
            # twice on a screen is one number that can disagree with itself.
            ("FrozenInitializationInput", "canonical_value"),
            ("FrozenInitializationInput", "canonical_unit"),
            ("FrozenInitializationInput", "dimension"),
            # The source's own identity is on the cadence row; what kind of
            # source it is, and which device and signal it names, belong to
            # the scenario surface that declares them.
            ("FrozenObservationBinding", "source_kind"),
            ("FrozenObservationBinding", "device_id"),
            ("FrozenObservationBinding", "signal_id"),
            # Who owns the cadence is the scenario's statement, and the row
            # carries what this run froze rather than restating it.
            ("FrozenObservationBinding", "cadence_ownership"),
        }

        from dataclasses import is_dataclass
        import typing

        import assetops_backend.runs.models as models

        def nested(record_type: type, seen: set[str]) -> set[tuple[str, str]]:
            if record_type.__name__ in seen:
                return set()
            seen.add(record_type.__name__)
            found: set[tuple[str, str]] = set()
            hints = typing.get_type_hints(record_type)
            for field in fields(record_type):
                found.add((record_type.__name__, field.name))
                for argument in _referenced_types(hints[field.name]):
                    if is_dataclass(argument):
                        found |= nested(argument, seen)
            return found

        def _referenced_types(annotation: object) -> list[object]:
            found = [annotation]
            for argument in typing.get_args(annotation):
                found.extend(_referenced_types(argument))
            return found

        declared = nested(models.DeterministicIdentity, set())
        # The top level has its own test; this audit is about what is inside.
        declared = {
            item for item in declared if item[0] != "DeterministicIdentity"
        }

        assert declared, "nothing was walked, so this audit proves nothing"
        assert declared == rendered | not_rendered, (
            "A field of the frozen deterministic identity is neither rendered "
            "on the setup summary nor classified as deliberately unrendered. "
            "Decide which it is; a frozen value nobody decided about is a "
            "value a reader cannot attribute."
        )

    def test_every_row_names_one_of_the_answerers(self) -> None:
        """Named for the set rather than for its size.

        It was `..._one_of_the_four_answerers` while the set had four, and
        T020 made it five. A test named for a count is a second place the
        count lives, and this one would have had to be renamed by whoever
        added the member - which is exactly the edit nothing forced.
        """
        record, _ = create()
        rows = frozen_inputs(record.deterministic_identity)

        assert rows
        for row in rows:
            assert row.answered_by in FROZEN_INPUT_ANSWERERS, row.field
            assert row.answered_by_detail.strip(), row.field
            assert row.value.strip(), row.field

    def test_no_row_names_an_answerer_its_own_detail_contradicts(self) -> None:
        """The shape the mislabel had, rather than a list of the rows that
        carried it.

        Every row says who answered and which record answered. Those are two
        statements about one fact, so a row whose detail names a publication
        profile while its answerer says the model profile is a row
        contradicting itself - which is what the cadence and both publication
        identity rows did until T020.
        """
        record, _ = create()
        rows = frozen_inputs(record.deterministic_identity)

        checked = 0
        for row in rows:
            detail = row.answered_by_detail
            if "publication profile" in detail:
                assert row.answered_by == "PUBLICATION_PROFILE", row.field
                checked += 1
            elif "model profile" in detail:
                assert row.answered_by == "MODEL_PROFILE", row.field
                checked += 1

        assert checked >= 3, "no profile-answered row was examined"

    def test_a_run_with_two_device_sources_has_two_cadence_rows(self) -> None:
        """A count of three was never the shape.

        The mislabel was on every row a publication profile answered, and how
        many that is depends on the scenario: a second device-signal source
        is a second cadence row. Built by adding a binding to a real frozen
        identity rather than by authoring a second source, because the
        scenario parser refuses a declared source nothing reports through -
        and what is being measured here is the row, not the document.
        """
        record, _ = create()
        identity = record.deterministic_identity
        device = identity.observation_bindings[0]
        assert device.source_kind == "DEVICE_SIGNAL"

        widened = replace(
            identity,
            observation_bindings=identity.observation_bindings
            + (replace(device, source_id="second-device-reading"),),
        )

        cadence_rows = [
            row
            for row in frozen_inputs(widened)
            if row.field.startswith("Cadence for")
        ]

        assert len(cadence_rows) == 3
        assert [
            row.answered_by
            for row in cadence_rows
            if row.value != "not applicable"
        ] == ["PUBLICATION_PROFILE", "PUBLICATION_PROFILE"]

    def test_the_answerers_correspond_to_the_initialization_owners(self) -> None:
        """What this can see, and what it cannot.

        It sees an initialization owner with no answerer, and an answerer
        mapped to from an owner that is not in the wider set. It CANNOT see a
        member of the wider set that nothing produces, because the second
        assertion is a subset - it has to be, since that set is deliberately
        wider than the owners. `PUBLICATION_PROFILE` is why: it answers for
        the cadence and the publication identities, which no initialization
        owner owns, and it was missing for a whole slice without this
        failing.
        """
        assert set(ANSWERER_BY_INITIALIZATION_OWNER) == set(
            INITIALIZATION_OWNERS
        )
        assert (
            set(ANSWERER_BY_INITIALIZATION_OWNER.values())
            <= FROZEN_INPUT_ANSWERERS
        )
        assert "PUBLICATION_PROFILE" not in set(
            ANSWERER_BY_INITIALIZATION_OWNER.values()
        )

    def test_a_whole_number_is_rendered_without_a_decimal_point(self) -> None:
        """An author who wrote 200 did not write 200.0."""
        record, _ = create()
        rows = {
            row.field: row.value
            for row in frozen_inputs(record.deterministic_identity)
        }

        assert rows["Initial example-stored-volume"] == "200 L"


class TestTimeZoneMembershipIsReal:
    def test_a_real_zone_is_accepted(self) -> None:
        assert (
            validate_iana_timezone("Africa/Kampala", where="a test")
            == "Africa/Kampala"
        )

    def test_a_zone_shaped_name_that_is_not_a_zone_is_refused(self) -> None:
        """Membership, not a pattern. `Area/Location` is the shape of almost
        every zone name and of every convincing typo."""
        with pytest.raises(TimeZoneNotFound):
            validate_iana_timezone("Africa/Atlantis", where="a test")

    def test_a_zone_with_no_area_is_still_accepted(self) -> None:
        """The complementary half: a pattern would have refused this one."""
        assert validate_iana_timezone("UTC", where="a test") == "UTC"

    def test_membership_is_case_sensitive(self) -> None:
        with pytest.raises(TimeZoneNotFound):
            validate_iana_timezone("africa/kampala", where="a test")


class TestNothingIsInferredFromASite:
    """Cadence, source identity and gateway identity come from the profile.

    The structural half of this is in `tools/checks/run-setup.ps1`: the module
    that resolves all three imports nothing from the Site domain, and nothing
    else in the product may build the records they live in. This is the half a
    Python test can hold - the resolvers take a profile and the scenario's own
    declared source, and there is no parameter a Site could arrive through.
    """

    def test_the_resolvers_take_no_site(self) -> None:
        from inspect import signature

        for resolver in (resolve_observation_binding, resolve_publication_identity):
            annotations = [
                str(parameter.annotation)
                for parameter in signature(resolver).parameters.values()
            ]
            assert annotations, resolver.__name__
            for annotation in annotations:
                assert "Site" not in annotation, (
                    f"{resolver.__name__} takes {annotation}, so a site fact "
                    "can reach a value only a profile may answer for"
                )

    def test_the_declared_source_carries_no_rate_and_no_name(self) -> None:
        """What the resolver is handed cannot contain a cadence to read off.

        Pinned as an exact field list rather than as an absence, so a field
        added to the record fails here instead of silently becoming something
        a cadence could be inferred from.
        """
        from assetops_backend.scenarios.models import ObservationSource

        assert [field.name for field in fields(ObservationSource)] == [
            "source_id",
            "source_kind",
            "device_id",
            "signal_id",
            "cadence_ownership",
            "description",
        ]


class TestTheShippedProfiles:
    def test_the_shipped_model_profile_models_the_fuel_tank_and_no_more(
        self,
    ) -> None:
        """The honest state of this build, asserted rather than assumed.

        The first causal kernel is T021's and it models the tank. Widening
        this profile is widening the kernel, not editing a list.
        """
        assert {
            state.state_key for state in MINIMAL_FUEL_TANK_MODEL.supported_states
        } == {
            "fuel-tank-volume",
            "fuel-tank-capacity",
            "generator-specific-fuel-consumption",
            "generator-output-power",
        }

        # Two of the four are the site's to answer, and each names the
        # property it means rather than a unit a component happens to be
        # rated in.
        bound = {
            state.state_key: state.foundation_binding
            for state in MINIMAL_FUEL_TANK_MODEL.supported_states
            if state.foundation_binding is not None
        }
        assert {
            key: (
                binding.component_type,
                binding.property_key,
                binding.unit,
            )
            for key, binding in bound.items()
        } == {
            "fuel-tank-capacity": ("FUEL_TANK", "tank-capacity", "L"),
            "generator-specific-fuel-consumption": (
                "GENERATOR",
                "specific-fuel-consumption",
                "L/kWh",
            ),
        }

    def test_the_shipped_publication_profile_declares_all_three(self) -> None:
        assert LAB_PUBLICATION_PROFILE.device_signal_cadence_minutes is not None
        assert LAB_PUBLICATION_PROFILE.simulator_source_id is not None
        assert LAB_PUBLICATION_PROFILE.gateway_id is not None

    def test_every_refusal_kind_is_reachable_vocabulary(self) -> None:
        assert RUN_SETUP_REFUSAL_KINDS
        with pytest.raises(ValueError):
            RunSetupRefused("NOT_A_KIND", "anything")


class TestEveryRefusalKindIsReachable:
    """Each kind, produced by a request that produces it.

    The vocabulary test above proves only that an unknown kind is rejected.
    It would pass on a build where three of the nine were unreachable, and
    a refusal kind nothing can produce is a fact the product claims it can
    state and cannot. This maps each kind to the request that causes it and
    asserts the map covers the vocabulary exactly, so a kind added without a
    way to reach it fails here.
    """

    def _timezone_database_unavailable(self) -> RunSetupRefused:
        """The one kind no request shape can produce.

        It needs the zone database itself to be unreadable, which is a fact
        about the host. Patched rather than left untested, because "we could
        not look" and "it is not there" being different facts is a claim this
        slice makes and nothing else measured.
        """
        from assetops_backend.runs import timezones

        def unreadable() -> frozenset[str]:
            raise TimeZoneDatabaseUnavailable("no database on this host")

        original = timezones._known_zones
        timezones._known_zones = unreadable
        try:
            setup, store = service()
            with pytest.raises(RunSetupRefused) as raised:
                setup.create_draft_run(setup_request())
            assert store.written == []
            return raised.value
        finally:
            timezones._known_zones = original

    def test_each_kind_has_a_request_that_produces_it(self) -> None:
        produced = {
            refuse(setup_request(seed=-1))[0].kind,
            refuse(setup_request(), sites=FakeSites(()))[0].kind,
            refuse(
                setup_request(
                    interval={"start_time": END_TIME, "end_time": START_TIME}
                )
            )[0].kind,
            refuse(
                setup_request(),
                sites=FakeSites((site(timezone="Africa/Atlantis"),)),
            )[0].kind,
            self._timezone_database_unavailable().kind,
            refuse(
                setup_request(), sites=FakeSites((site(topology=None),))
            )[0].kind,
            refuse(setup_request(), sites=FakeSites((site(devices=()),)))[
                0
            ].kind,
            refuse(
                setup_request(
                    run_inputs=[
                        {
                            "parameter_id": "draw-rate",
                            "value": 1,
                            "unit": "furlongs",
                        }
                    ]
                )
            )[0].kind,
            self._missing_initialization_input().kind,
        }

        assert produced == RUN_SETUP_REFUSAL_KINDS

    def _missing_initialization_input(self) -> RunSetupRefused:
        document = scenario_document()
        document["public_parameters"][2]["ownership"]["owner"] = "RUN_OVERRIDE"
        error, store = refuse(
            setup_request(),
            scenarios=FakeScenarios(
                (
                    parse_scenario_document(
                        document, source="a test", origin="SHIPPED"
                    ),
                )
            ),
        )
        assert store.written == []
        return error

    def test_the_two_vocabularies_share_no_name(self) -> None:
        """A refusal kind and a blocking kind are opposite sides of the line
        this slice is organised around, so no string may be both. Asserted
        because the two that are about an initial value now sit close enough
        in meaning that a future kind could plausibly be added to the wrong
        set, or to both."""
        from assetops_backend.runs.models import BLOCKING_REASON_KINDS

        assert RUN_SETUP_REFUSAL_KINDS & BLOCKING_REASON_KINDS == set()
        assert "INITIALIZATION_INPUT_MISSING" in RUN_SETUP_REFUSAL_KINDS
        assert "INITIAL_VALUE_NOT_RESOLVED" in BLOCKING_REASON_KINDS

    def test_an_unreadable_zone_database_is_not_an_unreal_zone(self) -> None:
        """Two different facts, and the message says which one this is."""
        error = self._timezone_database_unavailable()

        assert error.kind == "TIMEZONE_DATABASE_UNAVAILABLE"
        # The service's own wrapper, which is the product copy a reader
        # meets. It says which fact this is, and it does not say the other.
        assert "statement about the database rather than about the site" in (
            error.message
        )
        assert "is not a name in the IANA" not in error.message

    def test_the_two_zone_failures_are_two_exceptions(self) -> None:
        """One level down, where the distinction is made.

        The service can only report what the zone module tells it, so the
        module is measured directly too: an empty database is not a zone that
        does not exist, and neither message claims the other's fact.
        """
        from assetops_backend.runs import timezones

        # The real rule, exercised through the real lookup: an empty database
        # is NO database rather than a database with nothing in it. Reading
        # it the other way would refuse every zone that exists, which is what
        # this project's Windows machines would have done without `tzdata`.
        timezones._known_zones.cache_clear()
        original = timezones.zoneinfo.available_timezones
        timezones.zoneinfo.available_timezones = lambda: set()
        try:
            with pytest.raises(TimeZoneDatabaseUnavailable):
                validate_iana_timezone("Africa/Kampala", where="a test")
        finally:
            timezones.zoneinfo.available_timezones = original
            timezones._known_zones.cache_clear()

        # And a real database that does not hold the name is the other fact.
        with pytest.raises(TimeZoneNotFound):
            validate_iana_timezone("Africa/Atlantis", where="a test")


class TestTheExecutionContractVersionMove:
    """The Foundation-value narrowing moves the number, and only forward.

    `D-2026-09-22-contract-version-scope`: the version moves when a change can
    alter the outcome for a document that was already valid. The shipped Fuel
    Loss Event as version two accepted it is refused by this parser, so it
    moved - from the two this slice found to a three.

    The absolute numbers are written relatively where they can be. Here they
    cannot: the point of the test is that the number CHANGED and that an
    earlier frozen run kept its own, and a relative assertion would pass on a
    build where nothing moved.
    """

    def test_the_version_moved_past_the_one_this_slice_found(self) -> None:
        assert EXECUTION_CONTRACT_VERSION == 4

    def test_a_new_draft_is_stamped_with_it(self) -> None:
        record, _ = create()

        assert (
            record.deterministic_identity.profiles.execution_contract_version
            == EXECUTION_CONTRACT_VERSION
        )

    def test_an_earlier_frozen_run_keeps_the_version_it_froze(self) -> None:
        """Never reinterpret an earlier frozen run under a new contract.

        A run document written under version two is read back as version two.
        It is not upgraded, not re-stamped, and not refused: a frozen run is a
        record of what this installation did, and the version is part of what
        it did.
        """
        from assetops_backend.runs.parsing import (
            parse_run_document,
            render_run_document,
        )

        record, _ = create()
        document = render_run_document(record)
        document["deterministic_identity"]["profiles"][
            "execution_contract_version"
        ] = 2

        reloaded = parse_run_document(document, source="an earlier run")

        assert (
            reloaded.deterministic_identity.profiles.execution_contract_version
            == 2
        )
        assert EXECUTION_CONTRACT_VERSION != 2


class TestNoDeclaredNeedGoesMissing:
    """Every declared parameter is in exactly one frozen collection.

    The exclusion in `_freeze_identity` used to filter on `value is not None`,
    on the assumption that a valueless parameter was represented as a
    `FrozenInitializationInput`. An independent review showed the two facts
    are not the same one: a Foundation-owned parameter that did not initialize
    satisfied the filter and qualified for neither collection, so the row
    vanished, nothing blocked, and the run reported `READY`.

    The parser now refuses that combination and the filter is keyed on the
    frozen collection itself rather than on a proxy for it. This asserts the
    property both changes exist to hold, so a later slice that reopens either
    one fails here rather than in a run record nobody reads.
    """

    def declared_parameters(self, definition) -> set[str]:
        found = {
            parameter.parameter_id
            for parameter in definition.public_parameters
        }
        for entry in definition.timeline:
            found |= {
                parameter.parameter_id for parameter in entry.parameters
            }
        return found

    def assert_each_parameter_frozen_once(self, identity, definition) -> None:
        """Union, disjointness and no duplicates, in one place.

        Shared by the three cases below rather than written out in the first
        one, because the property is the same property whoever answered: a
        scenario-owned run, a Foundation that answers, and a Foundation that
        answers for nothing all have to freeze a row for every parameter.
        """
        resolved = [
            item.parameter_id for item in identity.scenario.resolved_parameters
        ]
        initialized = [
            item.parameter_id for item in identity.initialization_inputs
        ]

        # No parameter is in both, and none is in neither.
        assert set(resolved) & set(initialized) == set()
        assert set(resolved) | set(initialized) == self.declared_parameters(
            definition
        )
        # And nothing is frozen twice inside one collection either.
        assert len(resolved) == len(set(resolved))
        assert len(initialized) == len(set(initialized))

    def test_every_parameter_is_frozen_exactly_once(self) -> None:
        definition = scenario()
        setup, _ = service(scenarios=FakeScenarios((definition,)))
        record = setup.create_draft_run(setup_request())

        self.assert_each_parameter_frozen_once(
            record.deterministic_identity, definition
        )

    def test_it_holds_for_a_foundation_owned_value_too(self) -> None:
        """The shape the defect was found in, now representable only one way.

        The Foundation-owned parameter carries no number, so it is absent from
        `resolved_parameters` - and it is present in `initialization_inputs`,
        which is the collection that can hold an absent answer beside a
        blocking reason. Absent from one, never from both.
        """
        setup, _ = service(
            scenarios=FakeScenarios(
                (
                    parse_scenario_document(
                        foundation_owned_document(),
                        source="a test",
                        origin="SHIPPED",
                    ),
                )
            ),
            model=model_profile(supported_states=foundation_bound_states()),
        )
        record = setup.create_draft_run(setup_request())
        identity = record.deterministic_identity

        assert "starting-level" not in {
            item.parameter_id for item in identity.scenario.resolved_parameters
        }
        assert "starting-level" in {
            item.parameter_id for item in identity.initialization_inputs
        }

        # And the whole invariant, not only this parameter. A second review
        # pointed out that checking one row's presence and absence is not
        # completeness, and it was the packet that claimed completeness here.
        self.assert_each_parameter_frozen_once(
            identity,
            parse_scenario_document(
                foundation_owned_document(),
                source="a test",
                origin="SHIPPED",
            ),
        )

    def test_a_blocked_run_loses_no_row_either(self) -> None:
        """The case that matters most: an unanswered value is still a row.

        A run that dropped the row it could not answer would report exactly
        what the defect reported - nothing missing, nothing blocking - so the
        completeness property is asserted against a Foundation that answers
        for nothing rather than only against one that answers.
        """
        setup, _ = service(
            scenarios=FakeScenarios(
                (
                    parse_scenario_document(
                        foundation_owned_document(),
                        source="a test",
                        origin="SHIPPED",
                    ),
                )
            ),
            sites=FakeSites(
                (
                    site(
                        components=(
                            SiteComponent(
                                component_id="example-store",
                                component_type="FUEL_TANK",
                                display_name="Stored volume",
                                rating=Rating(value=500.0, unit="L"),
                                properties=None,
                            ),
                        )
                    ),
                )
            ),
            model=model_profile(supported_states=foundation_bound_states()),
        )
        record = setup.create_draft_run(setup_request())
        identity = record.deterministic_identity

        frozen = {
            item.state_key: item for item in identity.initialization_inputs
        }
        assert frozen["example-stored-volume"].value is None
        assert record.execution_status == "BLOCKED"
        assert [reason.subject for reason in record.blocking_reasons] == [
            "example-stored-volume"
        ]

        # The completeness half, on the outcome that matters most: a run that
        # could answer nothing still froze a row for everything it was asked.
        self.assert_each_parameter_frozen_once(
            identity,
            parse_scenario_document(
                foundation_owned_document(),
                source="a test",
                origin="SHIPPED",
            ),
        )


class TestTheBindingsOwnUnitIsChecked:
    """`FoundationBinding.unit` was read by nothing at all.

    Only the found property's unit was compared to the scenario's, so a
    profile could declare it would answer in `%`, find a property in `L`, and
    freeze 500 L under `READY`. An independent review reproduced that for two
    units. A declared unit that nothing checks is worse than no unit, because
    it reads as a guarantee.

    Three units have to agree - the scenario's, the binding's and the
    property's - and the two checks below close the triangle the existing
    wrong-unit test could not reach, because that test changed the component,
    the property and the binding together.
    """

    def bound_in(self, unit: str) -> tuple[SupportedState, ...]:
        """The default binding with its declared unit changed and nothing else.

        The component is untouched, the property is untouched, and the
        scenario still declares litres. Only the profile's claim moves, which
        is what makes this an isolated test of the field.
        """
        return (
            SupportedState(
                state_key="example-stored-volume",
                scope="COMPONENT",
                supported_roles=frozenset(
                    {"CAUSAL_INPUT", "REPORTED_OBSERVATION"}
                ),
                foundation_binding=FoundationBinding(
                    component_type="FUEL_TANK",
                    property_key="tank-capacity",
                    unit=unit,
                ),
                statement="Bound with a declared unit of its own.",
            ),
            default_supported_states()[1],
        )

    def run_with(self, unit: str):
        setup, store = service(
            scenarios=FakeScenarios(
                (
                    parse_scenario_document(
                        foundation_owned_document(),
                        source="a test",
                        origin="SHIPPED",
                    ),
                )
            ),
            model=model_profile(supported_states=self.bound_in(unit)),
        )
        return setup.create_draft_run(setup_request()), store

    def test_the_matching_unit_still_resolves(self) -> None:
        """Non-vacuous: without this, a resolver that blocked on every binding
        would satisfy both cases below."""
        record, _ = self.run_with("L")

        assert record.blocking_reasons == ()
        assert (
            record.deterministic_identity.initialization_inputs[0].value
            == 500.0
        )

    @pytest.mark.parametrize("unit", ["%", "L/kWh"])
    def test_a_binding_that_claims_another_unit_blocks(self, unit) -> None:
        record, store = self.run_with(unit)

        assert [reason.kind for reason in record.blocking_reasons] == [
            "INITIAL_VALUE_NOT_RESOLVED"
        ]
        reason = record.blocking_reasons[0]
        assert reason.subject == "example-stored-volume"
        # The message names both halves of the disagreement, and neither
        # phrase is reachable from the state key alone.
        assert f"binds it to the tank-capacity property declared in {unit}" in (
            reason.statement
        )
        assert "The profile and the scenario disagree" in reason.statement

        # The answer is absent rather than the wrong number, which is what
        # made this reproducible: it used to freeze 500 L and report READY.
        assert (
            record.deterministic_identity.initialization_inputs[0].value is None
        )
        assert store.written == [record]

    def test_a_binding_naming_a_unit_its_property_does_not_carry_blocks(
        self,
    ) -> None:
        """The third side of the triangle.

        A property key carries its unit from the closed vocabulary while a
        binding states one separately, so a profile can agree with the
        scenario and still name a unit the property it chose is not declared
        in. The scenario here declares `%`, the binding declares `%`, and
        `tank-capacity` is litres.
        """
        document = foundation_owned_document()
        document["public_parameters"][2]["unit"] = "%"

        setup, _ = service(
            scenarios=FakeScenarios(
                (
                    parse_scenario_document(
                        document, source="a test", origin="SHIPPED"
                    ),
                )
            ),
            model=model_profile(supported_states=self.bound_in("%")),
        )
        record = setup.create_draft_run(setup_request())

        reason = record.blocking_reasons[0]
        assert reason.kind == "INITIAL_VALUE_NOT_RESOLVED"
        assert "declares that property in L" in reason.statement
        assert (
            record.deterministic_identity.initialization_inputs[0].value is None
        )
