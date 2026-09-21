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

from dataclasses import fields

import pytest
from run_fixtures import (
    END_TIME,
    START_TIME,
    FakeRuns,
    FakeScenarios,
    FakeSites,
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
    DeterministicIdentity,
    SimulationRun,
)
from assetops_backend.runs.profiles import (
    MINIMAL_FUEL_TANK_MODEL,
    LAB_PUBLICATION_PROFILE,
    SupportedState,
    resolve_observation_binding,
    resolve_publication_identity,
)
from assetops_backend.runs.provenance import frozen_inputs
from assetops_backend.runs.refusals import RUN_SETUP_REFUSAL_KINDS, RunSetupRefused
from assetops_backend.runs.service import RunSetupService
from assetops_backend.runs.timezones import (
    TimeZoneNotFound,
    validate_iana_timezone,
)
from assetops_backend.scenarios.execution import EXECUTION_CONTRACT_VERSION
from assetops_backend.scenarios.models import INITIALIZATION_OWNERS
from assetops_backend.scenarios.parsing import parse_scenario_document
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
        assert device.cadence_resolution == "MODEL_PROFILE"

        # A person writing a value down reports at no rate, so there is no
        # cadence for anything to own and no reason to block.
        hand = bindings["example-hand-record"]
        assert hand.cadence_minutes is None
        assert hand.cadence_resolution == "NOT_APPLICABLE"


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

    def test_a_foundation_owned_value_needs_a_declared_binding(self) -> None:
        """Nothing matches a state to a component by the look of its name."""
        document = scenario_document()
        document["public_parameters"][2]["ownership"]["owner"] = "SITE_FOUNDATION"

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
        assert "binding" in error.message
        assert store.written == []

    def test_a_foundation_that_disagrees_with_the_scenario_is_refused(
        self,
    ) -> None:
        """The scenario names the foundation as the authority, so its own
        number is the requirement to check rather than a value to discard."""
        document = scenario_document()
        document["public_parameters"][2]["ownership"]["owner"] = "SITE_FOUNDATION"
        scenarios = FakeScenarios(
            (
                parse_scenario_document(
                    document, source="a test", origin="SHIPPED"
                ),
            )
        )

        error, store = refuse(
            setup_request(),
            scenarios=scenarios,
            model=model_profile(supported_states=foundation_bound_states()),
        )

        assert error.kind == "INITIALIZATION_INPUT_MISSING"
        assert "200" in error.message and "500" in error.message
        assert store.written == []

    def test_a_foundation_that_agrees_is_frozen_from_the_foundation(
        self,
    ) -> None:
        document = scenario_document()
        document["public_parameters"][2]["ownership"]["owner"] = "SITE_FOUNDATION"
        scenarios = FakeScenarios(
            (
                parse_scenario_document(
                    document, source="a test", origin="SHIPPED"
                ),
            )
        )

        setup, _ = service(
            scenarios=scenarios,
            sites=FakeSites(
                (
                    site(
                        components=(
                            SiteComponent(
                                component_id="example-store",
                                component_type="FUEL_TANK",
                                display_name="Stored volume",
                                rating=Rating(value=200.0, unit="L"),
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

    def test_two_foundation_answers_are_refused_rather_than_chosen_between(
        self,
    ) -> None:
        document = scenario_document()
        document["public_parameters"][2]["ownership"]["owner"] = "SITE_FOUNDATION"
        scenarios = FakeScenarios(
            (
                parse_scenario_document(
                    document, source="a test", origin="SHIPPED"
                ),
            )
        )

        error, store = refuse(
            setup_request(),
            scenarios=scenarios,
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

        assert error.kind == "INITIALIZATION_INPUT_MISSING"
        assert "more than one" in error.message
        assert store.written == []


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
        assert binding.cadence_resolution == "NOT_RESOLVED"

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

    def test_an_unreached_reading_blocks_rather_than_rounding(self) -> None:
        """`D-2026-09-21-scenario-execution-contract`, applied.

        The Fuel Loss residual was accepted as stated rather than resolved,
        and the decision says what run setup does until one of the three ways
        out is chosen. The fixture reconciles exactly, so this changes one
        authored value to make it not reach - which is the same fact the
        shipped document has, in a document this test owns.
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

        assert record.execution_status == "BLOCKED"
        assert [reason.kind for reason in record.blocking_reasons] == [
            "OBSERVATION_NOT_ACCOUNTED_FOR"
        ]
        assert record.blocking_reasons[0].subject == "second-entry"
        assert store.written == [record]

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

    def test_the_status_vocabulary_has_no_executing_value(self) -> None:
        """Nothing in this build can run, so no status says it did."""
        assert RUN_EXECUTION_STATUSES == {"READY", "BLOCKED"}


class TestEveryFrozenValueNamesAnAnswerer:
    def test_every_identity_field_is_represented(self) -> None:
        """The completeness guard: a field added to the frozen identity with
        no answerer fails here rather than arriving on a screen in a column
        with nothing under it."""
        record, _ = create()
        rows = frozen_inputs(record.deterministic_identity)

        assert rows, "the provenance rows are empty, so this proves nothing"
        covered = {row.identity_field for row in rows}
        declared = {field.name for field in fields(DeterministicIdentity)}

        assert covered == declared

    def test_every_row_names_one_of_the_four_answerers(self) -> None:
        record, _ = create()
        rows = frozen_inputs(record.deterministic_identity)

        assert rows
        for row in rows:
            assert row.answered_by in FROZEN_INPUT_ANSWERERS, row.field
            assert row.answered_by_detail.strip(), row.field
            assert row.value.strip(), row.field

    def test_the_answerers_correspond_to_the_initialization_owners(self) -> None:
        assert set(ANSWERER_BY_INITIALIZATION_OWNER) == set(
            INITIALIZATION_OWNERS
        )
        assert (
            set(ANSWERER_BY_INITIALIZATION_OWNER.values())
            <= FROZEN_INPUT_ANSWERERS
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
        } == {"fuel-tank-volume", "fuel-tank-capacity"}

    def test_the_shipped_publication_profile_declares_all_three(self) -> None:
        assert LAB_PUBLICATION_PROFILE.device_signal_cadence_minutes is not None
        assert LAB_PUBLICATION_PROFILE.simulator_source_id is not None
        assert LAB_PUBLICATION_PROFILE.gateway_id is not None

    def test_every_refusal_kind_is_reachable_vocabulary(self) -> None:
        assert RUN_SETUP_REFUSAL_KINDS
        with pytest.raises(ValueError):
            RunSetupRefused("NOT_A_KIND", "anything")
