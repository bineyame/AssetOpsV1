"""Two components of one type, resolved independently or blocked visibly.

T020A built the typed property carrier and left this open on purpose: an
unqualified binding resolved exactly one candidate or blocked, and a site with
two tanks had one `fuel-tank-volume` between them. This is the slice that
closes it, and the tests below are its acceptance criteria.

## How these tests avoid passing on adjacent text

Everything here is near-identical by construction. `example-stored-volume`,
`example-stored-volume@north-tank` and `example-stored-volume@south-tank` differ
by a suffix, and the first is a substring of the other two. T020A lost three
rounds to assertions satisfied by text they were not testing, so:

- membership is asserted on whole sets, with `==`, so an extra or a missing
  address fails rather than being absorbed;
- lookups are by exact address into a dict keyed on the address, so a wrong
  key raises rather than returning the sibling's row;
- the CAPACITIES DIFFER, 500 against 800, so which number was frozen is the
  evidence for which component answered - a test on two equal values would
  pass against a resolver that picked either.
"""

from __future__ import annotations

import pytest
from addressed_fixtures import (
    LOAD_MILL,
    LOAD_RES,
    NORTH_CAPACITY,
    NORTH_TANK,
    SOUTH_CAPACITY,
    SOUTH_TANK,
    repeated_load_document,
    twin_components,
    twin_document,
    twin_profile,
    twin_site,
)
from run_fixtures import (
    FakeRuns,
    FakeScenarios,
    FakeSites,
    component_property,
    publication_profile,
    setup_request,
    site,
)

from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.parsing import (
    parse_run_document,
    render_run_document,
)
from assetops_backend.runs.profiles import FoundationBinding
from assetops_backend.runs.provenance import frozen_inputs
from assetops_backend.runs.service import (
    RunSetupService,
    requirement_conflicts,
)
from assetops_backend.scenarios.parsing import parse_scenario_document
from assetops_backend.scenarios.ports import ScenarioConfigurationInvalid
from assetops_backend.sites.models import Rating, SiteComponent

NORTH_VOLUME = f"example-stored-volume@{NORTH_TANK}"
SOUTH_VOLUME = f"example-stored-volume@{SOUTH_TANK}"
NORTH_LEVEL = f"example-stored-level@{NORTH_TANK}"
SOUTH_LEVEL = f"example-stored-level@{SOUTH_TANK}"


def scenario(document: dict | None = None):
    return parse_scenario_document(
        twin_document() if document is None else document,
        source="a test",
        origin="SHIPPED",
    )


def run(
    *,
    document: dict | None = None,
    site_record=None,
    model=None,
) -> tuple[SimulationRun, FakeRuns]:
    """One Draft set up against the two-of-everything site."""
    store = FakeRuns()
    setup = RunSetupService(
        store,
        FakeSites((twin_site() if site_record is None else site_record,)),
        FakeScenarios((scenario(document),)),
        model_profiles=(twin_profile() if model is None else model,),
        publication_profiles=(publication_profile(),),
        now=lambda: "2026-09-21T09:00:00Z",
    )
    record = setup.create_draft_run(
        setup_request(
            scenario_id="twin-asset-scenario",
            scenario_version=1,
            model_profile={
                "profile_id": "twin-asset-model",
                "profile_version": 1,
            },
        )
    )
    return record, store


def frozen_by_address(record: SimulationRun) -> dict:
    return {
        item.addressed_key: item
        for item in record.deterministic_identity.initialization_inputs
    }


def reasons_by_subject(record: SimulationRun) -> dict[str, str]:
    return {
        reason.subject: reason.statement
        for reason in record.blocking_reasons
    }


class TestTwoSameTypeComponentsResolveIndependently:
    """Acceptance criterion 2, and the outcome the whole slice exists for."""

    def test_each_tank_freezes_its_own_capacity(self) -> None:
        record, store = run()

        assert record.execution_status == "READY"
        assert record.blocking_reasons == ()
        assert store.written == [record]

        frozen = frozen_by_address(record)
        # The whole set, so a third row or a missing one fails here.
        assert set(frozen) == {
            NORTH_VOLUME,
            SOUTH_VOLUME,
            NORTH_LEVEL,
            SOUTH_LEVEL,
        }
        assert frozen[NORTH_VOLUME].value == NORTH_CAPACITY
        assert frozen[SOUTH_VOLUME].value == SOUTH_CAPACITY
        assert NORTH_CAPACITY != SOUTH_CAPACITY

    def test_each_frozen_row_keeps_its_own_reference(self) -> None:
        record, _ = run()
        frozen = frozen_by_address(record)

        north = frozen[NORTH_VOLUME].state_ref
        south = frozen[SOUTH_VOLUME].state_ref

        # One semantic state, two addresses. Both halves matter: the key
        # stayed semantic and the identity did not leak into it.
        assert north.state_key == south.state_key == "example-stored-volume"
        assert north.component_id == NORTH_TANK
        assert south.component_id == SOUTH_TANK

    def test_the_attribution_names_the_component_that_answered(self) -> None:
        """Acceptance criterion 11's first half: which asset supplied it.

        Asserted as `component <id> property <key>`, a phrase the sibling's
        row cannot contain, rather than as the bare id - `north-tank` appears
        in both rows' addresses and would pass against a detail that named
        the wrong asset.
        """
        record, _ = run()
        frozen = frozen_by_address(record)

        assert (
            f"component {NORTH_TANK} property tank-capacity"
            in frozen[NORTH_VOLUME].answered_by_detail
        )
        assert (
            f"component {SOUTH_TANK} property tank-capacity"
            in frozen[SOUTH_VOLUME].answered_by_detail
        )

    def test_changing_only_the_second_capacity_moves_only_its_answer(
        self,
    ) -> None:
        """The metamorphic half. One number changes and one row follows it."""
        before = frozen_by_address(run()[0])

        components = list(twin_components())
        components[1] = SiteComponent(
            component_id=SOUTH_TANK,
            component_type="FUEL_TANK",
            display_name="South fuel tank",
            rating=Rating(value=SOUTH_CAPACITY, unit="L"),
            properties=(component_property(value=1200.0),),
        )
        after = frozen_by_address(
            run(site_record=twin_site(components=tuple(components)))[0]
        )

        assert after[SOUTH_VOLUME].value == 1200.0
        assert after[NORTH_VOLUME].value == before[NORTH_VOLUME].value
        assert after[NORTH_LEVEL].value == before[NORTH_LEVEL].value


class TestTheProfileNamesNoFixture:
    """Acceptance criterion 3: scope is declared, component ids are not."""

    def test_the_same_profile_resolves_a_different_sites_components(
        self,
    ) -> None:
        """One profile, two sites, two component identities.

        The scenario leaves the selector off, so the only thing that can
        choose a component is the Foundation being asked. A profile that had
        pinned an id would resolve one of these and block the other.
        """
        document = twin_document(
            north_volume="example-stored-volume", south_volume=None
        )

        answers = {}
        for component_id in ("alpha-tank", "beta-tank"):
            record, _ = run(
                document=document,
                site_record=site(
                    components=(
                        SiteComponent(
                            component_id=component_id,
                            component_type="FUEL_TANK",
                            display_name="The only tank",
                            rating=Rating(value=NORTH_CAPACITY, unit="L"),
                            properties=(component_property(value=640.0),),
                        ),
                    )
                ),
            )
            assert record.execution_status == "READY"
            frozen = frozen_by_address(record)
            address = f"example-stored-volume@{component_id}"
            assert address in frozen
            answers[component_id] = frozen[address].value

        assert answers == {"alpha-tank": 640.0, "beta-tank": 640.0}

    def test_no_shipped_or_fixture_profile_names_a_component(self) -> None:
        """A binding that named an id would make a simulator a fixture."""
        from dataclasses import fields

        from assetops_backend.runs.profiles import MODEL_PROFILES

        binding_fields = {field.name for field in fields(FoundationBinding)}
        assert binding_fields == {"component_type", "property_key", "unit"}

        declared = [
            state
            for profile in MODEL_PROFILES
            for state in profile.supported_states
        ]
        assert declared, "no shipped profile states, so this proves nothing"
        for state in declared:
            assert state.scope in {"SITE", "COMPONENT"}

    def test_a_site_scoped_state_may_not_carry_a_binding(self) -> None:
        from assetops_backend.runs.profiles import SupportedState

        with pytest.raises(ValueError) as raised:
            SupportedState(
                state_key="example-demand",
                scope="SITE",
                supported_roles=frozenset({"FORCING_INPUT"}),
                foundation_binding=FoundationBinding(
                    component_type="LOAD",
                    property_key="tank-capacity",
                    unit="L",
                ),
                statement="A site-wide state with a component binding.",
            )

        assert "no component for such a binding to find" in str(raised.value)

    def test_a_scope_disagreement_blocks_rather_than_guessing(self) -> None:
        record, _ = run(model=twin_profile(volume_scope="SITE"))

        assert record.execution_status == "BLOCKED"
        subjects = reasons_by_subject(record)
        assert NORTH_VOLUME in subjects
        assert "two different quantities" in subjects[NORTH_VOLUME]


class TestAnExplicitSelectorSelectsThatComponentAndNoOther:
    """Acceptance criterion 4, including the fallback that must not happen."""

    def test_a_named_component_the_site_does_not_declare_blocks(self) -> None:
        document = twin_document(
            north_volume="example-stored-volume@missing-tank"
        )
        record, store = run(document=document)

        assert record.execution_status == "BLOCKED"
        subjects = reasons_by_subject(record)
        assert "example-stored-volume@missing-tank" in subjects
        assert (
            "declares no component with that identity"
            in subjects["example-stored-volume@missing-tank"]
        )
        assert store.written == [record]

    def test_another_matching_component_does_not_answer_for_it(self) -> None:
        """The fallback acceptance criterion 4 forbids.

        Two real fuel tanks are on this site, both declaring `tank-capacity`,
        and the document names a third that does not exist. Neither of the two
        answers - proved on the VALUE, because a resolver that fell back would
        have frozen 500 or 800 here rather than nothing.
        """
        document = twin_document(
            north_volume="example-stored-volume@missing-tank"
        )
        record, _ = run(document=document)

        frozen = frozen_by_address(record)
        assert frozen["example-stored-volume@missing-tank"].value is None
        assert (
            frozen["example-stored-volume@missing-tank"].canonical_value
            is None
        )
        # And the sibling still answered, so the block is about one address.
        assert frozen[SOUTH_VOLUME].value == SOUTH_CAPACITY

    def test_a_named_component_of_the_wrong_type_blocks(self) -> None:
        """It exists, it is named, and it is a generator.

        Nothing looks for a `FUEL_TANK` elsewhere: two are declared on this
        site and neither is consulted.
        """
        document = twin_document(
            north_volume="example-stored-volume@site-generator"
        )
        record, _ = run(document=document)

        subjects = reasons_by_subject(record)
        address = "example-stored-volume@site-generator"
        assert address in subjects
        assert "which the foundation of site" in subjects[address]
        assert "GENERATOR" in subjects[address]
        assert frozen_by_address(record)[address].value is None

    def test_a_named_component_without_the_property_blocks(self) -> None:
        components = twin_components(south_properties=None)
        record, _ = run(site_record=twin_site(components=components))

        subjects = reasons_by_subject(record)
        assert SOUTH_VOLUME in subjects
        assert "declares no such property on it" in subjects[SOUTH_VOLUME]
        # The north tank declares it and is unaffected.
        assert frozen_by_address(record)[NORTH_VOLUME].value == NORTH_CAPACITY


class TestAnUnqualifiedBindingResolvesOneCandidateOrBlocks:
    """Acceptance criterion 5, the case T020A tested as this slice's."""

    def unqualified(self, **kwargs):
        return run(
            document=twin_document(
                north_volume="example-stored-volume", south_volume=None
            ),
            **kwargs,
        )

    def test_two_candidates_leave_it_unanswered_and_blocked(self) -> None:
        record, store = self.unqualified()

        assert record.execution_status == "BLOCKED"
        subjects = reasons_by_subject(record)
        assert "example-stored-volume" in subjects
        statement = subjects["example-stored-volume"]
        assert "without saying which component it is about" in statement
        # Both candidates named, so the author is told what to choose between.
        assert NORTH_TANK in statement
        assert SOUTH_TANK in statement
        assert store.written == [record]

        frozen = frozen_by_address(record)
        assert frozen["example-stored-volume"].value is None

    def test_removing_one_candidate_resolves_it(self) -> None:
        """The same document, one component fewer, and it resolves.

        This is what makes the ambiguity test non-vacuous: the block above is
        about the second candidate and not about the document.
        """
        record, _ = self.unqualified(
            site_record=twin_site(components=twin_components(south=None))
        )

        assert record.execution_status == "READY"
        frozen = frozen_by_address(record)
        assert f"example-stored-volume@{NORTH_TANK}" in frozen
        assert frozen[f"example-stored-volume@{NORTH_TANK}"].value == (
            NORTH_CAPACITY
        )

    def test_no_candidate_is_a_different_reason(self) -> None:
        record, _ = self.unqualified(
            site_record=site(
                components=(
                    SiteComponent(
                        component_id="a-battery",
                        component_type="BATTERY",
                        display_name="Battery",
                        rating=Rating(value=215.0, unit="kWh"),
                        properties=None,
                    ),
                )
            )
        )

        subjects = reasons_by_subject(record)
        assert "declares no such component" in subjects[
            "example-stored-volume"
        ]

    def test_a_second_candidate_without_the_property_still_blocks(
        self,
    ) -> None:
        """The candidate set is the components OF THE TYPE.

        Narrowing it to the components that happen to declare the property
        would turn this into a silent choice: the other tank would answer
        because the first one could not, which is the fallback the whole
        module refuses.
        """
        record, _ = self.unqualified(
            site_record=twin_site(
                components=twin_components(south_properties=None)
            )
        )

        assert record.execution_status == "BLOCKED"
        assert "more than one" in reasons_by_subject(record)[
            "example-stored-volume"
        ]


class TestUnitMismatchIsStillABlockingCondition:
    """Acceptance criterion 6, carried forward to the addressed grain."""

    def test_a_binding_in_another_unit_blocks_the_addressed_input(
        self,
    ) -> None:
        record, _ = run(
            model=twin_profile(
                binding=FoundationBinding(
                    component_type="FUEL_TANK",
                    property_key="reserve-state-of-charge",
                    unit="%",
                )
            )
        )

        assert record.execution_status == "BLOCKED"
        subjects = reasons_by_subject(record)
        # One reason per ADDRESS, so both tanks are reported rather than one.
        assert {NORTH_VOLUME, SOUTH_VOLUME} <= set(subjects)
        for address in (NORTH_VOLUME, SOUTH_VOLUME):
            assert "disagree about what kind of quantity" in subjects[address]

    def test_a_property_in_another_unit_than_the_binding_blocks(self) -> None:
        components = twin_components(
            south_properties=(
                component_property(
                    property_key="reserve-state-of-charge",
                    value=25.0,
                    unit="%",
                ),
            )
        )
        record, _ = run(site_record=twin_site(components=components))

        subjects = reasons_by_subject(record)
        assert SOUTH_VOLUME in subjects
        assert "declares no such property on it" in subjects[SOUTH_VOLUME]


class TestTwoComponentIdsAreNotOneDuplicate:
    """Acceptance criterion 7."""

    def test_two_addresses_of_one_state_key_both_parse(self) -> None:
        definition = scenario()
        addresses = {
            parameter.addressed_key
            for parameter in definition.public_parameters
        }

        assert addresses == {
            NORTH_VOLUME,
            SOUTH_VOLUME,
            NORTH_LEVEL,
            SOUTH_LEVEL,
        }

    def test_one_address_declared_twice_is_still_refused(self) -> None:
        document = twin_document(south_volume=NORTH_VOLUME)

        with pytest.raises(ScenarioConfigurationInvalid) as raised:
            parse_scenario_document(
                document, source="a test", origin="SHIPPED"
            )

        assert "initialize the state" in str(raised.value)
        assert NORTH_VOLUME in str(raised.value)

    def test_mixing_a_qualified_and_an_unqualified_form_is_refused(
        self,
    ) -> None:
        """The hole addressing opens, closed at the parser.

        An unqualified reference resolves to whichever component of the bound
        type the site declares - possibly the very one already named - so a
        document declaring both would freeze two answers onto one address.
        """
        document = twin_document(south_volume="example-stored-volume")

        with pytest.raises(ScenarioConfigurationInvalid) as raised:
            parse_scenario_document(
                document, source="a test", origin="SHIPPED"
            )

        assert "without naming a component" in str(raised.value)
        assert "Name the component on both, or on neither" in str(
            raised.value
        )


class TestRequirementConflictsAreDetectableAtTheAddress:
    """Acceptance criterion 8. T020B owns the final refusal behaviour."""

    def test_a_clean_document_reports_none(self) -> None:
        assert requirement_conflicts(scenario()) == ()

    def test_two_requirements_for_one_address_and_role_are_reported(
        self,
    ) -> None:
        document = twin_document()
        document["timeline"][0]["parameters"][0][
            "execution_requirement"
        ] = "OPTIONAL"

        conflicts = requirement_conflicts(scenario(document))

        assert [conflict.addressed_key for conflict in conflicts] == [
            "site:example-demand"
        ]
        assert conflicts[0].execution_role == "FORCING_INPUT"
        assert conflicts[0].requirements == ("OPTIONAL", "REQUIRED")

    def test_two_components_at_different_requirements_are_not_a_conflict(
        self,
    ) -> None:
        """Two addresses are two requirements, which is the point.

        Reporting them as a disagreement would be the collapse this slice
        just stopped doing, wearing a different name.
        """
        document = repeated_load_document()
        document["timeline"][2]["execution_requirement"] = "OPTIONAL"
        document["timeline"][2]["parameters"][0][
            "execution_requirement"
        ] = "OPTIONAL"

        assert requirement_conflicts(scenario(document)) == ()


class TestDynamicInitializationIsAddressedToo:
    """Acceptance criterion 9: one tank's level cannot start its sibling."""

    def test_each_tank_starts_from_its_own_level(self) -> None:
        record, _ = run()
        frozen = frozen_by_address(record)

        assert frozen[NORTH_LEVEL].value == 200.0
        assert frozen[SOUTH_LEVEL].value == 350.0
        assert frozen[NORTH_LEVEL].answered_by == "SCENARIO"
        assert frozen[SOUTH_LEVEL].answered_by == "SCENARIO"

    def test_changing_one_starting_level_moves_only_that_tank(self) -> None:
        record, _ = run(document=twin_document(south_level=90.0))
        frozen = frozen_by_address(record)

        assert frozen[SOUTH_LEVEL].value == 90.0
        assert frozen[NORTH_LEVEL].value == 200.0

    def test_a_scenario_owned_level_keeps_the_address_it_was_authored_at(
        self,
    ) -> None:
        """Nothing resolves a scenario-owned value against the Foundation.

        Its address is the author's and stays exactly as written, which is why
        a run input or a scenario number cannot acquire a component it was
        never about.
        """
        record, _ = run()
        frozen = frozen_by_address(record)

        assert frozen[NORTH_LEVEL].state_ref.component_id == NORTH_TANK
        assert frozen[SOUTH_LEVEL].state_ref.component_id == SOUTH_TANK


class TestTheResolvedAddressSurvivesTheRecord:
    """Acceptance criterion 10: serialization, reload and reordering."""

    def test_a_frozen_run_round_trips_through_its_document(self) -> None:
        record, _ = run()
        reloaded = parse_run_document(
            render_run_document(record), source="a test"
        )

        before = frozen_by_address(record)
        after = frozen_by_address(reloaded)

        assert set(after) == set(before)
        for address, item in after.items():
            assert item.state_ref == before[address].state_ref
            assert item.value == before[address].value
            assert item.answered_by_detail == before[address].answered_by_detail

    def test_an_unqualified_reference_is_frozen_as_the_component_that_answered(
        self,
    ) -> None:
        """What the run froze is that tank's number, and the record says so.

        A reader of a frozen run must not have to re-run the resolution
        against a Foundation that may have changed since.
        """
        record, _ = run(
            document=twin_document(
                north_volume="example-stored-volume", south_volume=None
            ),
            site_record=twin_site(components=twin_components(south=None)),
        )

        frozen = frozen_by_address(record)
        assert "example-stored-volume" not in frozen
        assert f"example-stored-volume@{NORTH_TANK}" in frozen

        document = render_run_document(record)
        rendered = {
            item["state_key"]
            for item in document["deterministic_identity"][
                "initialization_inputs"
            ]
        }
        assert f"example-stored-volume@{NORTH_TANK}" in rendered

    def test_reordering_the_components_changes_nothing(self) -> None:
        straight = frozen_by_address(run()[0])
        reversed_order = frozen_by_address(
            run(
                site_record=twin_site(
                    components=twin_components(order_reversed=True)
                )
            )[0]
        )

        assert set(reversed_order) == set(straight)
        for address, item in reversed_order.items():
            assert item.value == straight[address].value
            assert item.answered_by_detail == straight[address].answered_by_detail

    def test_a_run_frozen_before_addressing_still_reads_back(self) -> None:
        """Acceptance criterion 13's preservation half.

        A Draft written under the previous contract carries a bare state key,
        and it is read as what it was: an unqualified component reference. It
        is not upgraded, not re-resolved, and not refused.
        """
        record, _ = run()
        document = render_run_document(record)
        identity = document["deterministic_identity"]
        identity["profiles"]["execution_contract_version"] = 3
        for item in identity["initialization_inputs"]:
            item["state_key"] = item["state_key"].split("@")[0].removeprefix(
                "site:"
            )
        # The two capacity rows collapse onto one bare key, so drop one: an
        # older document could not have carried both, which is the whole
        # reason this slice exists.
        identity["initialization_inputs"] = [
            item
            for item in identity["initialization_inputs"]
            if item["parameter_id"] in {"north-capacity", "north-start"}
        ]

        reloaded = parse_run_document(document, source="an earlier run")

        frozen = frozen_by_address(reloaded)
        assert set(frozen) == {
            "example-stored-volume",
            "example-stored-level",
        }
        assert frozen["example-stored-volume"].state_ref.scope == "COMPONENT"
        assert frozen["example-stored-volume"].state_ref.component_id is None
        assert (
            reloaded.deterministic_identity.profiles.execution_contract_version
            == 3
        )


class TestTheRunDetailDistinguishesSameTypeAssets:
    """Acceptance criterion 11."""

    def test_each_initial_value_is_its_own_row_named_by_address(self) -> None:
        record, _ = run()
        rows = {
            row.field: row
            for row in frozen_inputs(
                record.deterministic_identity, record.blocking_reasons
            )
            if row.identity_field == "initialization_inputs"
        }

        assert set(rows) == {
            f"Initial {NORTH_VOLUME}",
            f"Initial {SOUTH_VOLUME}",
            f"Initial {NORTH_LEVEL}",
            f"Initial {SOUTH_LEVEL}",
        }
        assert rows[f"Initial {NORTH_VOLUME}"].value == "500 L"
        assert rows[f"Initial {SOUTH_VOLUME}"].value == "800 L"

    def test_the_reason_sits_beside_the_input_it_is_about(self) -> None:
        """One unresolved tank, one reason, and it is on the right row."""
        components = twin_components(south_properties=None)
        record, _ = run(site_record=twin_site(components=components))

        rows = {
            row.field: row
            for row in frozen_inputs(
                record.deterministic_identity, record.blocking_reasons
            )
        }

        unresolved = rows[f"Initial {SOUTH_VOLUME}"]
        assert unresolved.value == "not resolved"
        assert unresolved.blocking_statement is not None
        assert SOUTH_TANK in unresolved.blocking_statement
        assert "declares no such property on it" in (
            unresolved.blocking_statement
        )

        # The sibling resolved and carries no reason at all, which is what
        # makes the pairing a pairing rather than a banner on every row.
        resolved = rows[f"Initial {NORTH_VOLUME}"]
        assert resolved.value == "500 L"
        assert resolved.blocking_statement is None

    def test_rows_are_complete_without_the_reasons(self) -> None:
        """The reasons are an addition, never a precondition."""
        record, _ = run()

        assert len(frozen_inputs(record.deterministic_identity)) == len(
            frozen_inputs(
                record.deterministic_identity, record.blocking_reasons
            )
        )


class TestNoDeclaredNeedGoesSilentlyAbsentAtTheAddress:
    """The invariant T020A's worst defect produced, at this slice's grain.

    Every declared initial value is answered and frozen, or present with a
    blocking reason naming the same address. Never absent from both, and never
    explained by the sibling's reason.
    """

    def test_every_declared_initial_value_has_a_row(self) -> None:
        for document, site_record in (
            (twin_document(), twin_site()),
            (
                twin_document(
                    north_volume="example-stored-volume@missing-tank"
                ),
                twin_site(),
            ),
            (
                twin_document(),
                twin_site(components=twin_components(south_properties=None)),
            ),
        ):
            record, _ = run(document=document, site_record=site_record)
            definition = scenario(document)

            declared = {
                parameter.addressed_key
                for parameter in definition.public_parameters
                if parameter.ownership is not None
                and parameter.ownership.initializes
            }
            frozen = set(frozen_by_address(record))

            assert declared == frozen, document["scenario_id"]

    def test_one_tanks_reason_does_not_explain_the_others_hole(self) -> None:
        """The record refuses the shape, not just the service.

        Built by hand at the address grain: a run with two absent values and
        one reason. Keyed on the semantic state key this passed, because both
        holes share `example-stored-volume`; keyed on the address the second
        hole is unexplained and the record says so.
        """
        from dataclasses import replace

        from assetops_backend.runs.models import BlockingReason

        components = twin_components(south_properties=None)
        record, _ = run(site_record=twin_site(components=components))

        identity = record.deterministic_identity
        holed = replace(
            identity,
            initialization_inputs=tuple(
                replace(item, value=None, canonical_value=None)
                if item.addressed_key == NORTH_VOLUME
                else item
                for item in identity.initialization_inputs
            ),
        )

        with pytest.raises(ValueError) as raised:
            SimulationRun(
                run_id=record.run_id,
                lifecycle_status="DRAFT",
                execution_status="BLOCKED",
                created_at=record.created_at,
                deterministic_identity=holed,
                blocking_reasons=(
                    BlockingReason(
                        kind="INITIAL_VALUE_NOT_RESOLVED",
                        subject=SOUTH_VOLUME,
                        statement="Only the south tank is explained.",
                    ),
                ),
                unsupported_optional_inputs=(),
            )

        assert NORTH_VOLUME in str(raised.value)
        assert "no blocking reason about it" in str(raised.value)


class TestTheRepeatedLoadBinding:
    """The LOAD-RES and LOAD-MILL fixture the proof asks for.

    Addressability at setup only. Nothing here serves either feeder any power
    and nothing in this build could; the electrical world is T024's.
    """

    def test_two_feeders_are_two_declarations(self) -> None:
        definition = scenario(repeated_load_document())
        addresses = {
            entry.addressed_key
            for entry in definition.timeline
            if entry.execution_role == "FORCING_INPUT"
        }

        assert addresses == {
            f"example-demand@{LOAD_RES}",
            f"example-demand@{LOAD_MILL}",
        }

    def test_a_run_keeps_them_apart(self) -> None:
        record, _ = run(
            document=repeated_load_document(),
            model=twin_profile(demand_scope="COMPONENT"),
        )

        assert record.execution_status == "READY"
        from assetops_backend.runs.service import executable_inputs

        forced = {
            item.addressed_key
            for item in executable_inputs(scenario(repeated_load_document()))
            if item.execution_role == "FORCING_INPUT"
        }
        assert forced == {
            f"example-demand@{LOAD_RES}",
            f"example-demand@{LOAD_MILL}",
        }

    def test_per_feeder_demand_against_a_site_wide_model_blocks(self) -> None:
        """The scope check reaches a forcing input too.

        Without it the address would be silently dropped: the profile models
        one site-wide demand, the scenario forces two feeders, and a run would
        have reported READY for a question the model cannot answer.
        """
        record, _ = run(document=repeated_load_document())

        assert record.execution_status == "BLOCKED"
        subjects = reasons_by_subject(record)
        assert {
            f"example-demand@{LOAD_RES}",
            f"example-demand@{LOAD_MILL}",
        } <= set(subjects)
        assert "as a fact about one component" in subjects[
            f"example-demand@{LOAD_RES}"
        ]


class TestTheShippedContractIsMigrated:
    """Acceptance criterion 12, and what it deliberately does not claim."""

    def shipped(self):
        from pathlib import Path

        import yaml

        repo_root = Path(__file__).resolve().parents[2]
        return parse_scenario_document(
            yaml.safe_load(
                (
                    repo_root / "config" / "scenarios" / "fuel-loss-event.yaml"
                ).read_text(encoding="utf-8")
            ),
            source="the shipped definition",
            origin="SHIPPED",
        )

    def test_every_executable_declaration_names_what_it_is_about(
        self,
    ) -> None:
        """No unqualified reference survives in the shipped document.

        Asserted as a property of every declaration rather than by listing the
        addresses: a list would pass while a declaration nobody thought about
        stayed bare, which is exactly the row that would later resolve to the
        wrong tank.
        """
        definition = self.shipped()

        declarations = (
            [
                entry.state_ref
                for entry in definition.timeline
                if entry.state_ref is not None
            ]
            + [
                parameter.state_ref
                for entry in definition.timeline
                for parameter in entry.parameters
                if parameter.state_ref is not None
            ]
            + [
                parameter.state_ref
                for parameter in definition.public_parameters
                if parameter.state_ref is not None
            ]
        )

        assert declarations, "nothing was walked, so this proves nothing"
        for ref in declarations:
            assert ref.is_addressed, ref.addressed_key

    def test_the_fuel_states_name_the_tank_and_the_generator(self) -> None:
        definition = self.shipped()
        addresses = {
            parameter.parameter_id: parameter.addressed_key
            for parameter in definition.public_parameters
        }

        assert addresses == {
            "tank-capacity": "fuel-tank-capacity@fuel-tank",
            "starting-fuel-level": "fuel-tank-volume@fuel-tank",
            "generator-specific-consumption": (
                "generator-specific-fuel-consumption@generator"
            ),
        }

    def test_the_bound_declaration_is_addressed_to_the_same_tank(self) -> None:
        """A capacity bounds the volume in ITS OWN tank."""
        capacity = next(
            parameter
            for parameter in self.shipped().public_parameters
            if parameter.parameter_id == "tank-capacity"
        )

        assert capacity.bounds is not None
        assert capacity.bounds.state_ref.component_id == "fuel-tank"
        assert capacity.bounds.bound_kind == "UPPER"

    def test_the_site_wide_states_claim_no_component(self) -> None:
        definition = self.shipped()
        site_wide = {
            entry.addressed_key
            for entry in definition.timeline
            if entry.state_ref is not None and entry.state_ref.scope == "SITE"
        }

        assert site_wide == {
            "site:site-load-demand",
            "site:plane-of-array-irradiance",
        }

    def test_it_still_claims_nothing_about_readiness(self) -> None:
        """Addressing is not readiness, and this says so out loud.

        The three states the first profile does not model are still
        unmodelled, and widening it is T020B's. A slice that quietly made the
        shipped scenario READY would be claiming the next slice's outcome.
        """
        from assetops_backend.runs.profiles import MINIMAL_FUEL_TANK_MODEL

        unmodelled = {
            entry.state_key
            for entry in self.shipped().timeline
            if entry.state_key is not None
            and MINIMAL_FUEL_TANK_MODEL.supported(entry.state_key) is None
        }

        assert unmodelled == {
            "site-load-demand",
            "plane-of-array-irradiance",
            "fuel-level-reporting-availability",
        }


class TestTheExecutionContractMovedAndOldRunsAreKept:
    """Acceptance criterion 13."""

    def test_a_run_frozen_under_this_build_may_execute(self) -> None:
        from assetops_backend.scenarios.execution import (
            EXECUTION_CONTRACT_VERSION,
            refuse_incompatible_execution,
        )

        assert (
            refuse_incompatible_execution(EXECUTION_CONTRACT_VERSION) is None
        )

    def test_a_run_frozen_under_another_contract_is_refused_execution(
        self,
    ) -> None:
        from assetops_backend.scenarios.execution import (
            EXECUTION_CONTRACT_VERSION,
            ExecutionContractIncompatible,
            refuse_incompatible_execution,
        )

        with pytest.raises(ExecutionContractIncompatible) as raised:
            refuse_incompatible_execution(EXECUTION_CONTRACT_VERSION - 1)

        assert "preserved exactly as it was frozen" in str(raised.value)
        assert "it is not executed" in str(raised.value)

    def test_the_run_detail_says_so_on_the_contract_row(self) -> None:
        """Refusal as a fact on the run, not a rule to remember later.

        Nothing in this build executes anything, so a guard with no caller
        would be a declaration nothing checks - the defect an independent
        review found in `FoundationBinding.unit`. This is the caller.
        """
        from dataclasses import replace

        record, _ = run()
        identity = record.deterministic_identity

        current = {row.field: row for row in frozen_inputs(identity)}[
            "Execution contract"
        ]
        assert current.blocking_statement is None

        stale = replace(
            identity,
            profiles=replace(
                identity.profiles,
                execution_contract_version=(
                    identity.profiles.execution_contract_version - 1
                ),
            ),
        )
        older = {row.field: row for row in frozen_inputs(stale)}[
            "Execution contract"
        ]

        assert older.blocking_statement is not None
        assert "stays readable" in older.blocking_statement

    def test_the_version_that_moved_is_the_one_a_new_draft_carries(
        self,
    ) -> None:
        from assetops_backend.scenarios.execution import (
            EXECUTION_CONTRACT_VERSION,
        )

        record, _ = run()

        assert (
            record.deterministic_identity.profiles.execution_contract_version
            == EXECUTION_CONTRACT_VERSION
        )


class TestComponentControlsStayWithTheirComponent:
    """Acceptance criterion 14: the T020A carrier, addressed, and no more.

    A control property is a typed property on a component like any other, so
    addressing gives it the same treatment: two batteries have two reserves
    and a run freezes each against the battery that declares it. Nothing here
    introduces a site-scoped Controls capability - a site's Controls section
    still shows the declared assumptions and the typed properties T020A put
    there, and the first controller is T024's.
    """

    def battery_site(self, *, second_reserve: float = 40.0):
        return site(
            components=(
                SiteComponent(
                    component_id="north-battery",
                    component_type="BATTERY",
                    display_name="North battery",
                    rating=Rating(value=215.0, unit="kWh"),
                    properties=(
                        component_property(
                            property_key="reserve-state-of-charge",
                            value=25.0,
                            unit="%",
                        ),
                    ),
                ),
                SiteComponent(
                    component_id="south-battery",
                    component_type="BATTERY",
                    display_name="South battery",
                    rating=Rating(value=215.0, unit="kWh"),
                    properties=(
                        component_property(
                            property_key="reserve-state-of-charge",
                            value=second_reserve,
                            unit="%",
                        ),
                    ),
                ),
            )
        )

    def control_run(self):
        document = twin_document(
            north_volume="example-stored-volume@north-battery",
            south_volume="example-stored-volume@south-battery",
        )
        # A reserve state of charge is a percentage, and the three units have
        # to agree: the scenario's, the binding's and the property's. Stating
        # it here rather than leaving the fixture's litres is the difference
        # between testing the control carrier and testing the unit check,
        # which has its own tests above.
        for parameter in document["public_parameters"]:
            if parameter["parameter_id"].endswith("-capacity"):
                parameter["unit"] = "%"
        return run(
            document=document,
            site_record=self.battery_site(),
            model=twin_profile(
                binding=FoundationBinding(
                    component_type="BATTERY",
                    property_key="reserve-state-of-charge",
                    unit="%",
                )
            ),
        )

    def test_each_battery_freezes_its_own_reserve(self) -> None:
        record, _ = self.control_run()
        frozen = frozen_by_address(record)

        north = frozen["example-stored-volume@north-battery"]
        south = frozen["example-stored-volume@south-battery"]

        assert north.value == 25.0
        assert south.value == 40.0
        assert (
            "component north-battery property reserve-state-of-charge"
            in north.answered_by_detail
        )
        assert (
            "component south-battery property reserve-state-of-charge"
            in south.answered_by_detail
        )

    def test_the_control_property_is_the_same_carrier(self) -> None:
        """No second field, no second table, no controller.

        A control property reaches a run through the one property list a
        component declares, and `kind` is what says it is a control.
        """
        from assetops_backend.sites.models import (
            COMPONENT_PROPERTY_DEFINITIONS,
        )

        definition = COMPONENT_PROPERTY_DEFINITIONS["reserve-state-of-charge"]
        assert definition.kind == "CONTROL"

        component = self.battery_site().foundation.components[0]
        assert [item.property_key for item in component.properties or ()] == [
            "reserve-state-of-charge"
        ]
