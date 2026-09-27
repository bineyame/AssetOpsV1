"""T020B: who answers for a state, and what a conflict does.

The declarative half of this slice - the boundary cycle, the reading
conventions, the window ramp and the bound policies - is protected in
`test_scenario_execution_contract.py`, beside the rules it is about. This
module is the run-setup half: which profile is asked, what a requirement
conflict does, and the two diagnoses T020A1 left inverted.

Three things it exists to keep true.

**One authority per state, decided by the state.** A reporting-path condition
is the publication profile's to answer and a world state is the model
profile's, and neither may claim the other's. The interesting failure is not
two profiles disagreeing - it is a reader being sent to widen a kernel over
something no kernel does.

**A requirement conflict refuses, at the earliest layer that can decide it.**
The authored grain needs only the document, so the scenario parser refuses it;
the alias grain needs a Foundation, so run setup does. Nothing anywhere takes
the stricter level, which is what made the lowering in this slice observable.

**F5, carried out of T020A1.** An unqualified reference to a state the profile
models site-wide was diagnosed as a missing binding and told the author to add
one that could never exist. Its repair is `site:` in front of the key, and
three functions now say so through one statement.
"""

from __future__ import annotations

from dataclasses import fields, replace
from pathlib import Path
from typing import Any

import pytest
import yaml
from run_fixtures import (
    FakeRuns,
    FakeScenarios,
    FakeSites,
    foundation_bound_states,
    model_profile,
    publication_profile,
    setup_request,
    site,
)
from scenario_fixtures import scenario_document

from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.profiles import (
    LAB_PUBLICATION_PROFILE,
    MINIMAL_FUEL_TANK_MODEL,
    REPORTING_PATH_STATES,
    STATE_AUTHORITIES,
    FoundationBinding,
    ModelProfile,
    SupportedReportingState,
    SupportedState,
    state_authority,
)
from assetops_backend.runs.refusals import RunSetupRefused
from assetops_backend.runs.service import (
    RunSetupService,
    UnresolvedRequirementConflict,
    executable_inputs,
)
from assetops_backend.scenarios.parsing import parse_scenario_document
from assetops_backend.scenarios.ports import ScenarioConfigurationInvalid

REPORTING_STATE = "fuel-level-reporting-availability"
REPORTING_ADDRESS = f"{REPORTING_STATE}@example-store"


def scenario(document: dict | None = None):
    return parse_scenario_document(
        scenario_document() if document is None else document,
        source="a test",
        origin="SHIPPED",
    )


def reporting_document() -> dict[str, Any]:
    """The example scenario, plus a forcing on the reporting path.

    Addressed explicitly, because a publication profile can never declare a
    foundation binding - it cannot see a Foundation - so an unqualified
    reporting reference has nothing to resolve a component from. That is a
    property this module asserts rather than works around.
    """
    document = scenario_document()
    document["timeline"].append(
        {
            "event_id": "reporting-gap",
            "sequence": 5,
            "offset_minutes": 180,
            "entry_kind": "EVENT",
            "category": "DATA_QUALITY",
            "description": "The level sensor reports nothing for a while.",
            "execution_role": "FORCING_INPUT",
            "state_key": REPORTING_ADDRESS,
            "execution_requirement": "REQUIRED",
            "timing": {"shape": "WINDOW", "duration_minutes": 60},
        }
    )
    return document


def reporting_states() -> tuple[SupportedReportingState, ...]:
    return (
        SupportedReportingState(
            state_key=REPORTING_STATE,
            scope="COMPONENT",
            supported_roles=frozenset({"FORCING_INPUT"}),
            statement="The reporting path can be forced unavailable.",
        ),
    )


def run(
    *,
    document: dict | None = None,
    site_record=None,
    model=None,
    publication=None,
) -> tuple[SimulationRun, FakeRuns]:
    store = FakeRuns()
    setup = RunSetupService(
        store,
        FakeSites((site() if site_record is None else site_record,)),
        FakeScenarios((scenario(document),)),
        model_profiles=(model or model_profile(),),
        publication_profiles=(publication or publication_profile(),),
        now=lambda: "2026-09-21T09:00:00Z",
    )
    return setup.create_draft_run(setup_request()), store


def reasons_by_subject(record: SimulationRun) -> dict[str, str]:
    return {
        reason.subject: reason.statement for reason in record.blocking_reasons
    }


class TestOneAuthorityPerState:
    """Criterion 3: reporting support resolves from the publication profile."""

    def test_the_two_authorities_are_the_only_two(self) -> None:
        assert STATE_AUTHORITIES == {"MODEL_PROFILE", "PUBLICATION_PROFILE"}

    def test_a_model_profile_may_not_claim_a_reporting_path_state(
        self,
    ) -> None:
        """Refused at construction, not remembered by a convention.

        This is the half of the split that cannot be enforced by asking
        politely: a model profile that declared the reporting path would make
        two profiles answer for one state, and the dangerous case is not the
        disagreement but the silent agreement that hides which was consulted.
        """
        with pytest.raises(ValueError) as raised:
            ModelProfile(
                model_profile_id="overreaching-model",
                model_profile_version=1,
                display_name="Overreaching model",
                statement="Claims the reporting path.",
                supported_states=(
                    SupportedState(
                        state_key=REPORTING_STATE,
                        scope="COMPONENT",
                        supported_roles=frozenset({"FORCING_INPUT"}),
                        foundation_binding=None,
                        statement="It should not be able to say this.",
                    ),
                ),
            )

        assert "fact about the reporting path" in str(raised.value)
        assert "publication profile declares it" in str(raised.value)

    def test_a_publication_profile_may_not_claim_a_world_state(self) -> None:
        """And the other direction, which is the same rule."""
        with pytest.raises(ValueError) as raised:
            SupportedReportingState(
                state_key="example-stored-volume",
                scope="COMPONENT",
                supported_roles=frozenset({"CAUSAL_INPUT"}),
                statement="It should not be able to say this either.",
            )

        assert "not a reporting-path state" in str(raised.value)
        assert "belongs to a model profile" in str(raised.value)

    def test_the_authority_is_read_from_the_state_not_from_who_replied(
        self,
    ) -> None:
        """The distinction that makes the absent case reportable.

        "Ask the model profile, and if it says nothing ask the publication
        profile" would make a world state the model profile has not got round
        to look like a reporting-path state - and send the reader to the wrong
        profile, which is the defect the move exists to fix. So a
        reporting-path state is answered by the publication profile WHETHER OR
        NOT that profile declares it.
        """
        silent = publication_profile(reporting_states=())

        authority = state_authority(
            REPORTING_STATE, model_profile(), silent
        )

        assert authority.answerer == "PUBLICATION_PROFILE"
        assert authority.models_it is False
        assert "publication profile example-publication" in authority.detail

        # And a world state the model profile does not model stays the model
        # profile's question.
        unmodelled = state_authority(
            "never-modelled-state", model_profile(), silent
        )
        assert unmodelled.answerer == "MODEL_PROFILE"
        assert unmodelled.models_it is False

    def test_a_declared_reporting_capability_reaches_ready(self) -> None:
        """Criterion 3's positive case, and it is not vacuous.

        The state is in neither collection afterwards: not blocking, and not an
        unsupported optional input either. Asserted against both, because "not
        blocking" alone would also hold if it had quietly become an optional
        the model profile disowned.
        """
        record, store = run(
            document=reporting_document(),
            publication=publication_profile(
                reporting_states=reporting_states()
            ),
        )

        assert record.execution_status == "READY"
        assert record.blocking_reasons == ()
        assert REPORTING_ADDRESS not in {
            item.addressed_key for item in record.unsupported_optional_inputs
        }
        assert store.written == [record]

    def test_an_absent_reporting_capability_blocks_with_a_publication_reason(
        self,
    ) -> None:
        """The proof table's "reporting capability absent" row.

        The explanation has to be publication-specific, and the assertion is
        two-sided: it names the publication profile AND it says the model
        profile cannot answer. Naming the right profile while leaving the old
        sentence in place would send a reader to widen a kernel anyway.
        """
        record, _ = run(
            document=reporting_document(),
            publication=publication_profile(reporting_states=()),
        )

        assert record.execution_status == "BLOCKED"
        statement = reasons_by_subject(record)[REPORTING_ADDRESS]

        assert "publication profile example-publication version 1" in statement
        assert "condition on the reporting path rather than on the world" in (
            statement
        )
        assert "A model profile cannot answer for this" in statement
        assert "the publication profile is the one to change" in statement
        # And it does not send the reader to the model profile, which is the
        # sentence this replaced.
        assert "model profile example-model" not in statement

    def test_the_shipped_pair_puts_the_reporting_state_on_the_right_profile(
        self,
    ) -> None:
        """The shipped declarations, so the vocabulary is not only a test's.

        `REPORTING_PATH_STATES` has one member because this build knows one
        reporting-path state. If it ever has none, the routing above is
        unreachable and this fails rather than passing over an empty set.
        """
        assert REPORTING_PATH_STATES
        assert REPORTING_STATE in REPORTING_PATH_STATES

        declared = {
            state.state_key
            for state in LAB_PUBLICATION_PROFILE.supported_reporting_states
        }
        assert declared == {REPORTING_STATE}
        assert MINIMAL_FUEL_TANK_MODEL.supported(REPORTING_STATE) is None


class TestARequirementConflictIsRefusedAndNeverResolved:
    """Criterion 4, at all three layers it could have been defeated at."""

    def test_two_levels_on_one_authored_address_refuse_at_parse(self) -> None:
        document = scenario_document()
        document["timeline"][0]["parameters"][0][
            "execution_requirement"
        ] = "OPTIONAL"

        with pytest.raises(ScenarioConfigurationInvalid) as raised:
            scenario(document)

        assert "two answers to whether an executor must model" in str(
            raised.value
        )

    def test_the_same_address_in_two_roles_is_not_a_conflict(self) -> None:
        """The case that must NOT refuse, so the rule is not too wide.

        `example-stored-volume@example-store` is a `CAUSAL_INPUT` in the public
        parameters and a `REPORTED_OBSERVATION` on the third entry. Lowering
        only the observation side leaves one address at two levels in two
        different roles, and that is not a contradiction: a profile may model a
        state it can cause and cannot report, so the two are two questions.
        """
        document = scenario_document()
        lowered = 0
        for entry in document["timeline"]:
            for position in (entry, *entry.get("parameters", ())):
                if position.get("execution_role") != "REPORTED_OBSERVATION":
                    continue
                position["execution_requirement"] = "OPTIONAL"
                lowered += 1
        # Every position naming that role, because lowering some of them is the
        # authored-grain conflict the parser refuses - which is the rule above,
        # not this one.
        assert lowered >= 2

        definition = scenario(document)
        levels = {
            (item.addressed_key, item.execution_role): (
                item.execution_requirement
            )
            for item in executable_inputs(definition)
        }

        # The pair survives as a pair, at two levels, rather than being
        # collapsed or refused.
        assert levels[
            ("example-stored-volume@example-store", "CAUSAL_INPUT")
        ] == "REQUIRED"
        assert levels[
            ("example-stored-volume@example-store", "REPORTED_OBSERVATION")
        ] == "OPTIONAL"

    def test_the_refusal_names_every_conflict_not_only_the_first(self) -> None:
        """F7 from the review: it reported `conflicts[0]`.

        An author with two alias conflicts fixed one, resubmitted and met the
        next - a round trip per problem, when the refusal already knew both.

        Two conflicts on ONE state in two ROLES, rather than two states: the
        alias only exists where the profile declares a binding for the bare
        reference to resolve through, and this fixture's profile binds one state.
        The document already declares that state addressed as both a
        `CAUSAL_INPUT` and a `REPORTED_OBSERVATION` at `REQUIRED`, so a bare
        `OPTIONAL` declaration in each role produces exactly two conflicting
        `(address, role)` pairs.
        """
        document = scenario_document()
        document["public_parameters"].append(
            {
                "parameter_id": "unqualified-draw",
                "display_name": "A draw named without its component",
                "value": 3,
                "unit": "L",
                "execution_role": "CAUSAL_INPUT",
                "state_key": "example-stored-volume",
                "execution_requirement": "OPTIONAL",
                "ownership": {"owner": "SCENARIO_INPUT", "initializes": False},
            }
        )
        document["public_parameters"].append(
            {
                # No ownership: a reported value carrying one could be named as
                # the source of an initial world state, which the parser refuses.
                "parameter_id": "unqualified-reading",
                "display_name": "A reading named without its component",
                "value": 188,
                "unit": "L",
                "execution_role": "REPORTED_OBSERVATION",
                "state_key": "example-stored-volume",
                "execution_requirement": "OPTIONAL",
            }
        )

        store = FakeRuns()
        setup = RunSetupService(
            store,
            FakeSites((site(),)),
            FakeScenarios((scenario(document),)),
            model_profiles=(
                model_profile(supported_states=foundation_bound_states()),
            ),
            publication_profiles=(publication_profile(),),
            now=lambda: "2026-09-21T09:00:00Z",
        )

        with pytest.raises(RunSetupRefused) as raised:
            setup.create_draft_run(setup_request())

        message = raised.value.message
        assert raised.value.kind == "EXECUTION_REQUIREMENT_CONFLICT"
        assert "2 addresses and roles" in message
        # Both roles named, so the author sees the whole job rather than half.
        assert "example-stored-volume@example-store as a CAUSAL_INPUT" in message
        assert (
            "example-stored-volume@example-store as a REPORTED_OBSERVATION"
            in message
        )
        assert store.written == []

    def test_nothing_resolves_a_conflict_that_bypasses_the_parser(
        self,
    ) -> None:
        """The enforcement, proved by handing setup what the parser refuses.

        The old rule took `REQUIRED` here and it is gone rather than kept as a
        harmless fallback: a fallback is what made lowering a requirement
        unobservable wherever a second position was still strict, which is
        every state this slice lowered.

        Built by mutating a PARSED definition, because the parser will not
        produce one. That is the point - if this raised only for documents the
        parser already refuses, it would be a check that cannot fire.
        """
        definition = scenario()
        entry = definition.timeline[0]
        assert entry.execution_requirement == "REQUIRED"
        lowered = replace(
            entry,
            parameters=tuple(
                replace(parameter, execution_requirement="OPTIONAL")
                for parameter in entry.parameters
            ),
        )
        smuggled = replace(
            definition, timeline=(lowered,) + definition.timeline[1:]
        )

        with pytest.raises(UnresolvedRequirementConflict) as raised:
            executable_inputs(smuggled)

        assert "at both REQUIRED and OPTIONAL" in str(raised.value)
        assert "Nothing here picks the stricter level" in str(raised.value)


class TestTheInvertedDiagnosisIsRighted:
    """F5, carried out of T020A1 and settled here.

    An unqualified reference to a state the answering profile models site-wide
    got the no-binding refusal, because a binding is only read when the scopes
    agree and a site-wide state has no binding by construction. The statement
    told the author to add an address or find a profile that declares the
    binding; the repair is to write `site:` before the key.
    """

    def _site_wide_demand_unqualified(self) -> SimulationRun:
        """The example demand, addressed to a component instead of the site.

        `example-demand` is modelled `SITE` by the fixture profile, and this
        writes it unqualified - which means COMPONENT. One character of scope
        marker apart from correct.
        """
        document = scenario_document()
        for position in (document["timeline"][0], *document["timeline"][0]["parameters"]):
            position["state_key"] = "example-demand"
        record, _ = run(document=document)
        return record

    def test_the_repair_is_the_scope_marker_and_the_reason_says_so(
        self,
    ) -> None:
        record = self._site_wide_demand_unqualified()

        assert record.execution_status == "BLOCKED"
        statement = reasons_by_subject(record)["example-demand"]

        # The repair, spelled as something an author can type.
        assert "write site:example-demand to claim it site-wide" in statement
        # And the diagnosis it replaced is gone rather than sitting beside it.
        assert "declares no binding" not in statement
        assert "a profile that declares the binding" not in statement

    def test_the_missing_binding_diagnosis_still_fires_where_it_is_true(
        self,
    ) -> None:
        """The other branch, so the fix is a reorder and not a deletion.

        A state the profile does not model AT ALL, referenced unqualified, has
        genuinely no binding to choose a component with - and that is what it
        is told. If this passed only because the branch had been removed, the
        F5 repair would have swapped one wrong diagnosis for another.
        """
        document = scenario_document()
        document["public_parameters"].append(
            {
                "parameter_id": "unmodelled-draw",
                "display_name": "A draw on a state nothing models",
                "value": 4,
                "unit": "L",
                "execution_role": "CAUSAL_INPUT",
                "state_key": "never-modelled-state",
                "execution_requirement": "REQUIRED",
                "ownership": {"owner": "SCENARIO_INPUT", "initializes": False},
            }
        )

        record, _ = run(document=document)
        statement = reasons_by_subject(record)["never-modelled-state"]

        assert "declares no binding saying which kind of component" in statement
        assert "either an address in the scenario or a profile that declares" in (
            statement
        )
        # And it is NOT told to write `site:`, which would be a repair that
        # does not work: the profile does not model this state either way.
        assert "write site:" not in statement

    def test_the_foundation_lookup_gives_the_same_repair(self) -> None:
        """The two functions agree, which is the other half of F5.

        `_resolve_foundation_value` ordered scope before binding and said so in
        its docstring while the address pass did the opposite, so one function
        contradicted the other's stated rule. They share one statement now, and
        this reaches the Foundation lookup rather than the address pass.

        Getting there needs the address to RESOLVE, so the reference is
        addressed explicitly: an explicit selector naming a component this
        Foundation declares meets the address obligation, and the scope
        disagreement is then the Foundation lookup's to report. An unqualified
        spelling would be refused by the address pass first and this would be
        testing that function twice.
        """
        document = scenario_document()
        for parameter in document["public_parameters"]:
            if parameter["parameter_id"] != "starting-level":
                continue
            # Site-wide in the profile, addressed to a component here, and the
            # Foundation is asked to answer for it.
            parameter["state_key"] = "example-demand@example-store"
            parameter["unit"] = "kW"
            parameter.pop("value", None)
            parameter["ownership"] = {
                "owner": "SITE_FOUNDATION",
                "initializes": True,
            }

        record, _ = run(
            document=document,
            model=model_profile(supported_states=foundation_bound_states()),
        )

        initial = {
            reason.subject: reason.statement
            for reason in record.blocking_reasons
            if reason.kind == "INITIAL_VALUE_NOT_RESOLVED"
        }
        statement = initial["example-demand@example-store"]

        assert "write site:example-demand to claim it site-wide" in statement
        # And the row it is about is frozen absent rather than dropped, which
        # is what keeps the reason beside a value a reader can see.
        frozen = {
            item.addressed_key: item
            for item in record.deterministic_identity.initialization_inputs
        }
        assert frozen["example-demand@example-store"].value is None

    def test_failing_both_obligations_yields_one_reason_per_address(
        self,
    ) -> None:
        """F5's related item: a reader met two rows with the same subject.

        The obligations are genuinely independent and a declaration can fail
        both - but a reference that names no asset has nothing for a profile to
        be asked about, and the second row added no repair the first did not
        state. The address reason is the one that has to be fixed first,
        because resolving it does not depend on the requirement level.

        Asserted as a count on the subject, which is what a reader counts.
        """
        record = self._site_wide_demand_unqualified()

        rows = [
            reason
            for reason in record.blocking_reasons
            if reason.subject == "example-demand"
        ]
        assert len(rows) == 1
        # Still BLOCKED, so nothing was traded for the tidier report.
        assert record.execution_status == "BLOCKED"


class TestTheShippedFuelLossEventReachesReadyThroughTheProductPath:
    """Criteria 2, 11 and 12, against the shipped documents.

    The Site is instantiated from the shipped template through the product's own
    create path rather than written as a run record, which is criterion 12: a
    fixture run proved `READY` in T020 because nothing else could, and that is
    no longer the primary demonstration.
    """

    def _shipped(self):
        root = Path(__file__).resolve().parents[2]
        return parse_scenario_document(
            yaml.safe_load(
                (
                    root / "config" / "scenarios" / "fuel-loss-event.yaml"
                ).read_text(encoding="utf-8")
            ),
            source="the shipped definition",
            origin="SHIPPED",
        )

    def _instantiated_site(self):
        from assetops_backend.sites.parsing import parse_site_template
        from assetops_backend.sites.service import SiteCreationService
        from assetops_backend.sites.site_parsing import CreateSiteRequest

        root = Path(__file__).resolve().parents[2]
        template = parse_site_template(
            yaml.safe_load(
                (
                    root
                    / "config"
                    / "site-templates"
                    / "hybrid-mini-grid-100kw.yaml"
                ).read_text(encoding="utf-8")
            ),
            source="the shipped template",
        )
        created: list[Any] = []

        class Recording:
            def create_site(self, record):
                created.append(record)
                return record

        class Catalog:
            def list_templates(self) -> tuple:
                return (template,)

            def get_template(self, template_id: str):
                return template

        SiteCreationService(Recording(), Catalog()).create_site_from_template(
            CreateSiteRequest(
                template_id="hybrid-mini-grid-100kw",
                # The scenario declares MG-001 and a run is not the place to
                # retarget a scenario, so the in-memory fixture carries that
                # identity. The MG-001 in `var/` is untouched and is the
                # blocked case the runs API suite reads.
                site_id="MG-001",
                display_name="Kalangala mini-grid",
                country="Uganda",
                locality="Kalangala",
                timezone="Africa/Kampala",
            )
        )
        return created[0]

    def _draft(self) -> tuple[SimulationRun, FakeRuns]:
        store = FakeRuns()
        setup = RunSetupService(
            store,
            FakeSites((self._instantiated_site(),)),
            FakeScenarios((self._shipped(),)),
            model_profiles=(MINIMAL_FUEL_TANK_MODEL,),
            publication_profiles=(LAB_PUBLICATION_PROFILE,),
            now=lambda: "2026-09-21T09:00:00Z",
        )
        record = setup.create_draft_run(
            {
                "site_id": "MG-001",
                "foundation_version": 1,
                "scenario_id": "fuel-loss-event",
                "scenario_version": 1,
                "interval": {
                    "start_time": "2026-09-21T00:00:00Z",
                    "end_time": "2026-09-22T17:00:00Z",
                },
                "timestep_minutes": 15,
                "seed": 20260921,
                "model_profile": {
                    "profile_id": "minimal-fuel-tank",
                    "profile_version": 1,
                },
                "publication_profile": {
                    "profile_id": "simulator-lab-publication",
                    "profile_version": 1,
                },
                "run_inputs": [],
            }
        )
        return record, store

    def test_the_shipped_document_reaches_ready(self) -> None:
        record, store = self._draft()

        assert record.execution_status == "READY"
        assert record.blocking_reasons == ()
        assert store.written == [record]

    def test_the_unsupported_optional_inputs_are_recorded_not_implied_away(
        self,
    ) -> None:
        """Criterion 1. READY does not mean the profile models these.

        Exactly the two, with the role each was declared in. Both are
        `FORCING_INPUT`s of one profile, so a one-sided assertion would pass on
        either alone.
        """
        record, _ = self._draft()

        assert {
            (item.addressed_key, item.execution_role)
            for item in record.unsupported_optional_inputs
        } == {
            ("site:site-load-demand", "FORCING_INPUT"),
            ("site:plane-of-array-irradiance", "FORCING_INPUT"),
        }

    def test_a_recorded_optional_input_does_not_claim_the_scenario_needs_it(
        self,
    ) -> None:
        """The review's finding 1, kept as a guard rather than only corrected.

        One sentence served both of `_support_for`'s answers and ended "which
        this scenario needs it to" - true of a REQUIRED input, false of an
        OPTIONAL one. So a READY run's own disclosure panel said the scenario
        needed something it had just declared it could do without, which
        contradicts the argument the lowering rests on.

        Asserted from both sides, because a one-sided version passes on the
        wrong fix: the optional row must not claim a need AND must say what
        being optional actually means for this run.
        """
        record, _ = self._draft()

        assert record.execution_status == "READY"
        assert record.unsupported_optional_inputs
        for item in record.unsupported_optional_inputs:
            # The false clause, in either spelling it could come back as.
            assert "needs it to" not in item.statement, item.addressed_key
            assert "requires it" not in item.statement, item.addressed_key
            # And the consequence that is actually true, which is the whole
            # reason lowering these two hides nothing.
            assert "declares it optional" in item.statement, item.addressed_key
            assert "recorded here rather than blocking" in item.statement
            assert "Nothing about this run models it" in item.statement

    def test_a_required_unmodelled_input_still_says_the_run_is_blocked(
        self,
    ) -> None:
        """The other side of the same statement, so the fix is a branch.

        Had the consequence clause simply been deleted, the test above would
        pass and a reader of a BLOCKED run would lose the sentence telling them
        why the run cannot proceed.
        """
        document = scenario_document()
        document["public_parameters"].append(
            {
                "parameter_id": "required-unmodelled",
                "display_name": "A required state nothing models",
                "value": 7,
                "unit": "L",
                "execution_role": "CAUSAL_INPUT",
                "state_key": "site:never-modelled-state",
                "execution_requirement": "REQUIRED",
                "ownership": {"owner": "SCENARIO_INPUT", "initializes": False},
            }
        )

        record, _ = run(document=document)
        statement = reasons_by_subject(record)["site:never-modelled-state"]

        assert "does not model that state at all" in statement
        assert "This scenario requires it, so the run is blocked" in statement

    def test_the_dispatched_output_is_a_forcing_the_profile_supports(
        self,
    ) -> None:
        """Criterion 2, and it is the reason nothing computes the dispatch.

        The generator's output is forced by the scenario, not solved for - so a
        profile that supports it as a `FORCING_INPUT` and in no other role is
        what makes the two lowered states unnecessary rather than ignored.
        """
        supported = MINIMAL_FUEL_TANK_MODEL.supported("generator-output-power")

        assert supported is not None
        assert supported.scope == "COMPONENT"
        assert supported.supported_roles == frozenset({"FORCING_INPUT"})

        record, _ = self._draft()
        inputs = {
            item.addressed_key: item.execution_role
            for item in executable_inputs(self._shipped())
        }
        assert inputs["generator-output-power@generator"] == "FORCING_INPUT"
        assert record.execution_status == "READY"

    def test_the_foundation_and_the_scenario_each_answer_their_own_values(
        self,
    ) -> None:
        """Criterion 2's second half: properties and dynamic initialization.

        Two Foundation-owned numbers resolved through the profile's addressed
        bindings, and one the scenario owns because a Foundation says how large
        a tank is and never how full it is.
        """
        record, _ = self._draft()
        frozen = {
            item.addressed_key: item
            for item in record.deterministic_identity.initialization_inputs
        }

        capacity = frozen["fuel-tank-capacity@fuel-tank"]
        assert capacity.value == 500.0
        assert capacity.answered_by == "SITE_FOUNDATION"
        assert "component fuel-tank property tank-capacity" in (
            capacity.answered_by_detail
        )

        coefficient = frozen["generator-specific-fuel-consumption@generator"]
        assert coefficient.value == 0.311
        assert coefficient.answered_by == "SITE_FOUNDATION"

        level = frozen["fuel-tank-volume@fuel-tank"]
        assert level.value == 430.0
        assert level.answered_by == "SCENARIO"

    def test_ready_still_says_what_it_does_not_assert(self) -> None:
        """Criterion 12's second half, kept rather than retired.

        The disclosure goes when T021's conformance test derives the supported
        states from a kernel, not when the first `READY` run appears through the
        product path.
        """
        from assetops_backend.runs.models import readiness_disclosure

        record, _ = self._draft()
        disclosure = readiness_disclosure(record.execution_status)

        assert disclosure is not None
        assert disclosure.strip()

    def test_the_draft_freezes_this_build_s_contract_version(self) -> None:
        """Criterion 10, on the run that reaches READY."""
        from assetops_backend.scenarios.execution import (
            EXECUTION_CONTRACT_VERSION,
        )

        record, _ = self._draft()

        assert (
            record.deterministic_identity.profiles.execution_contract_version
            == EXECUTION_CONTRACT_VERSION
        )


class TestAnEarlierFrozenRunKeepsItsOwnIdentity:
    """Criterion 10: old frozen runs retain their old identity."""

    def test_a_version_four_run_is_readable_and_refused_execution(
        self,
    ) -> None:
        """Readable is not executable, and the run says which it is.

        Twenty of the local Drafts are at version four. Reading one is never
        refused - a run that cannot be executed is still a run somebody needs
        to inspect to find out why - and executing one is, because the rules
        behind its frozen inputs have changed.
        """
        from assetops_backend.runs.parsing import (
            parse_run_document,
            render_run_document,
        )
        from assetops_backend.scenarios.execution import (
            EXECUTION_CONTRACT_VERSION,
            ExecutionContractIncompatible,
            refuse_incompatible_execution,
        )

        record, _ = run()
        document = render_run_document(record)
        document["deterministic_identity"]["profiles"][
            "execution_contract_version"
        ] = 4

        reloaded = parse_run_document(document, source="an earlier run")
        frozen = reloaded.deterministic_identity.profiles

        assert frozen.execution_contract_version == 4
        assert EXECUTION_CONTRACT_VERSION == 6

        with pytest.raises(ExecutionContractIncompatible) as raised:
            refuse_incompatible_execution(frozen.execution_contract_version)

        assert "version 4" in str(raised.value)
        assert "stays readable" in str(raised.value)


def test_a_foundation_binding_still_names_a_kind_and_never_an_instance() -> None:
    """Three strings, asserted as the whole field list.

    Criterion 2 resolves Foundation properties through these bindings, and it
    only stays true across Sites because a binding names a component TYPE. A
    fourth field carrying a component id would make the profile a fixture, and
    the same simulator build could not be selected for a second Site -
    T020A1's criterion 3. `hasattr` would not catch it; the field list does.
    """
    names = {field.name for field in fields(FoundationBinding)}

    assert names == {"component_type", "property_key", "unit"}
