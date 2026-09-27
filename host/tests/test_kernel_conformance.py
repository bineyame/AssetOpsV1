"""The falsifier for `supported_states`, and what it retires.

The backlog's first entry says `MINIMAL_FUEL_TANK_MODEL` declares that
`fuel-tank-volume` supports `CAUSAL_INPUT` and `REPORTED_OBSERVATION` while
"nothing in this build can cause or report anything", so the declaration is a
promise about a kernel that does not exist and `READY` is computed from it. It
also says what would change the answer: descoping the conformance test that
derives the set from the kernel. This module is that test.

**It has to derive rather than agree, and it has to derive at least what it
claims.** The single most repeated defect across T020A, T020A1 and T020B was a
claim that overstated what a guard covered, and a conformance test comparing two
hand-written tables would be that defect one layer deeper. So there are three
legs, and each is checked for non-vacuity:

1. the advertised set is built by grouping the kernel's handler table, which is
   the only place a role can be spelled;
2. every advertised `(state, role)` pair is reached by executing a real frozen
   Draft, recorded by the execution ledger - so a handler nothing calls fails
   this rather than counting as coverage;
3. the derived set and the product profile's declaration are equal, in both
   directions, over state key, scope and roles.

**What it does NOT establish is stated here rather than left to be assumed.** The
`REPORTED_OBSERVATION` role is verified at the model's grain: the world can
answer what a stock is at an instant, after that instant's events. Nothing here
publishes that answer - there is no device, no cadence, no sampling error, no
dropout and no envelope - and the publication profile's `supported_reporting_states`
remains unverified, which is why the readiness disclosure keeps its second half.
"""

from __future__ import annotations

from dataclasses import fields

from fixtures import draft, scenario

from assetops_backend.runs.models import (
    BLOCKING_REASON_KINDS,
    READY_DISCLOSURE,
    readiness_disclosure,
)
from assetops_backend.runs.profiles import (
    LAB_PUBLICATION_PROFILE,
    MINIMAL_FUEL_TANK_MODEL,
    ModelProfile,
    PublicationProfile,
)
from assetops_backend.runs.refusals import RUN_SETUP_REFUSAL_KINDS
from assetops_contracts.failures import EXECUTION_FAILURE_KINDS
from assetops_simulator.packs.fuel import MINIMAL_FUEL_MODEL

from execution_adapter import run_to_end


def _declared_pairs(profile: ModelProfile) -> set[tuple[str, str]]:
    return {
        (state.state_key, role)
        for state in profile.supported_states
        for role in state.supported_roles
    }


def _executed():
    definition = scenario()
    return run_to_end(draft(definition=definition))


class TestTheAdvertisedSetIsDerivedFromExecutableHandlers:
    def test_the_derived_set_equals_the_product_profile_s_declaration(
        self,
    ) -> None:
        derived = {
            (state.state_key, state.scope, state.supported_roles)
            for state in MINIMAL_FUEL_MODEL.advertised_supported_states()
        }
        declared = {
            (state.state_key, state.scope, state.supported_roles)
            for state in MINIMAL_FUEL_TANK_MODEL.supported_states
        }
        assert derived == declared
        assert len(derived) == 4

    def test_the_two_profile_identities_are_the_same_profile(self) -> None:
        """A kernel conforming to a different profile would prove nothing."""
        assert (
            MINIMAL_FUEL_MODEL.model_profile_id
            == MINIMAL_FUEL_TANK_MODEL.model_profile_id
        )
        assert (
            MINIMAL_FUEL_MODEL.model_profile_version
            == MINIMAL_FUEL_TANK_MODEL.model_profile_version
        )

    def test_the_derived_set_comes_from_the_handlers_and_nothing_else(
        self,
    ) -> None:
        """Remove a handler and the advertised set narrows with it.

        Without this the equality above could hold between two tables somebody
        keeps in step by hand, and nothing would show that one is computed from
        the other.
        """
        from dataclasses import replace

        without_sampling = replace(
            MINIMAL_FUEL_MODEL,
            handlers=tuple(
                handler
                for handler in MINIMAL_FUEL_MODEL.handlers
                if handler.role != "REPORTED_OBSERVATION"
            ),
        )
        narrowed = {
            (state.state_key, state.supported_roles)
            for state in without_sampling.advertised_supported_states()
        }
        assert ("fuel-tank-volume", frozenset({"CAUSAL_INPUT"})) in narrowed
        assert (
            "fuel-tank-volume",
            frozenset({"CAUSAL_INPUT", "REPORTED_OBSERVATION"}),
        ) not in narrowed

    def test_every_advertised_pair_is_reached_by_a_real_execution(self) -> None:
        """The evidence leg. A handler nothing calls is not a capability.

        The Draft is created by the real setup service from the shipped document
        against a Site instantiated from the shipped template, so what the ledger
        records is what executing the product's own content actually called.
        """
        executed = _executed()
        assert executed.trajectory.outcome == "COMPLETED", (
            executed.trajectory.failure
        )

        reached = {
            (
                MINIMAL_FUEL_MODEL.handler_by_id(handler_id).state_key,
                MINIMAL_FUEL_MODEL.handler_by_id(handler_id).role,
            )
            for handler_id in executed.trajectory.handlers_exercised
        }
        advertised = MINIMAL_FUEL_MODEL.advertised_pairs()

        assert advertised == _declared_pairs(MINIMAL_FUEL_TANK_MODEL)
        assert advertised - reached == set()
        assert len(advertised) == 5

    def test_the_ledger_records_what_ran_rather_than_what_exists(self) -> None:
        """Otherwise the leg above would be satisfied by the table it checks.

        A model with an extra handler nothing exercises must come back with that
        pair missing from the ledger, which is what makes the subset assertion a
        measurement.
        """
        from dataclasses import replace

        from assetops_simulator.kernel.model import StateHandler

        # Site-scoped, because a component-scoped state now has to belong to a
        # declared component relation and the model refuses one that does not.
        # That refusal is a second guard and not the one under test here: what
        # this measures is the LEDGER, so the handler has to be constructible and
        # simply never reached.
        never_called = StateHandler(
            handler_id="a-state-nothing-reaches",
            state_key="ambient-temperature",
            scope="SITE",
            role="CAUSAL_INPUT",
            kind="COEFFICIENT",
            statement="declared and never consumed by any law or any input",
            consume=lambda value: value,
        )
        wider = replace(
            MINIMAL_FUEL_MODEL,
            handlers=MINIMAL_FUEL_MODEL.handlers + (never_called,),
        )
        definition = scenario()
        executed = run_to_end(draft(definition=definition), wider)
        reached = {
            (
                wider.handler_by_id(handler_id).state_key,
                wider.handler_by_id(handler_id).role,
            )
            for handler_id in executed.trajectory.handlers_exercised
        }
        assert ("ambient-temperature", "CAUSAL_INPUT") in wider.advertised_pairs()
        assert ("ambient-temperature", "CAUSAL_INPUT") not in reached
        assert wider.advertised_pairs() - reached == {
            ("ambient-temperature", "CAUSAL_INPUT")
        }

    def test_the_law_that_makes_two_of_the_roles_mean_something_also_ran(
        self,
    ) -> None:
        executed = _executed()
        assert executed.trajectory.handlers_exercised
        consumption = [
            event
            for event in executed.trajectory.applied_events
            if event.origin == "MODEL_LAW"
        ]
        assert len(consumption) == 16


class TestWhatThisProfileStillDoesNotModel:
    def test_demand_and_irradiance_have_no_handler_in_any_role(self) -> None:
        """Criterion 13's second half, from both sides.

        Neither state is in the kernel's handler table, so the derived set cannot
        advertise them; neither is in the product profile's declaration either;
        and the frozen run records both as unsupported optional inputs rather than
        leaving them out.
        """
        for state_key in ("site-load-demand", "plane-of-array-irradiance"):
            assert MINIMAL_FUEL_MODEL.models_state(state_key) is False
            assert MINIMAL_FUEL_TANK_MODEL.supported(state_key) is None

    def test_the_run_records_them_rather_than_dropping_them(self) -> None:
        run = draft()
        recorded = {
            item.addressed_key for item in run.unsupported_optional_inputs
        }
        assert recorded == {
            "site:plane-of-array-irradiance",
            "site:site-load-demand",
        }

    def test_the_kernel_says_it_did_not_model_them(self) -> None:
        executed = _executed()
        notes = " ".join(executed.trajectory.notes)
        assert "site:site-load-demand" in notes
        assert "site:plane-of-array-irradiance" in notes
        assert "nothing about this run models it" in notes

    def test_neither_reaches_the_world_the_kernel_evolves(self) -> None:
        executed = _executed()
        addresses = {address for address, _ in executed.trajectory.final.stocks}
        assert addresses == {"fuel-tank-volume@fuel-tank"}


class TestTheReportingPathIsStillUnverified:
    def test_the_publication_profile_declares_a_state_nothing_here_exercises(
        self,
    ) -> None:
        """The half of the disclosure this slice does not retire.

        `LAB_PUBLICATION_PROFILE` declares it can model the fuel level reporting
        path being unavailable. Nothing in this build can suppress a reading or
        deliver one, and this kernel does not try: the condition reaches it as an
        address it is told to leave alone, and it changes no world quantity.
        """
        declared = {
            state.state_key
            for state in LAB_PUBLICATION_PROFILE.supported_reporting_states
        }
        assert declared == {"fuel-level-reporting-availability"}
        executed = _executed()
        assert executed.inputs.reporting_path_addresses == (
            "fuel-level-reporting-availability@fuel-tank",
        )
        assert any(
            "publication profile" in note
            for note in executed.trajectory.notes
        )

    def test_no_profile_record_can_declare_an_initial_historical_window(
        self,
    ) -> None:
        """`no-interval-signal-at-the-first-boundary` says its exception is
        unreachable in this build, and this is the half of that claim only a
        composing test can make: neither profile record carries such a field."""
        names = {field.name for field in fields(ModelProfile)} | {
            field.name for field in fields(PublicationProfile)
        }
        assert not [
            name
            for name in names
            if "historical" in name or "initial_window" in name
        ]


class TestWhatTheDisclosureSaysNow:
    def test_it_no_longer_claims_the_model_profile_is_unverified(self) -> None:
        """Criterion 14. The condition closed, so the claim went with it.

        `D-2026-09-22-expiry-follows-the-condition`: a claim that has become
        false goes in the slice that falsifies it, and leaving it is shipping a
        false statement rather than being cautious.
        """
        assert "no causal runtime exists" not in READY_DISCLOSURE
        assert (
            "supported states have not been compared" not in READY_DISCLOSURE
        )
        assert "conformance test deriving" not in READY_DISCLOSURE
        # And the positive form, because the absence of a phrase is also
        # satisfied by the statement having gone silent about the model profile
        # altogether, which is not what this slice did.
        assert (
            "model profile's supported states have been derived from an "
            "executable kernel" in READY_DISCLOSURE
        )

    def test_it_still_names_the_limitation_that_is_still_honest(self) -> None:
        assert "publication profile" in READY_DISCLOSURE
        assert "reporting-path states" in READY_DISCLOSURE
        assert "suppress a reading or deliver one" in READY_DISCLOSURE

    def test_it_names_its_own_remaining_condition_and_no_slice_number(
        self,
    ) -> None:
        assert "the transform that produces readings" in READY_DISCLOSURE
        for slice_number in ("T021", "T022", "T020"):
            assert slice_number not in READY_DISCLOSURE

    def test_it_says_what_has_been_verified_rather_than_going_silent(
        self,
    ) -> None:
        """Narrowed, not removed. A `READY` run still tells a reader which half
        of the advertised support has been compared against something
        executable, because otherwise retiring the first half would read as
        nothing having been unverified in the first place."""
        assert "kernel conformance" in READY_DISCLOSURE

    def test_a_ready_run_carries_it_and_a_blocked_run_does_not(self) -> None:
        assert readiness_disclosure("READY") == READY_DISCLOSURE
        assert readiness_disclosure("BLOCKED") is None


class TestTheThreeVocabulariesAreDistinct:
    def test_setup_refusal_draft_blocking_and_execution_failure_are_disjoint(
        self,
    ) -> None:
        """Criterion 12, and only a composing test can make this comparison.

        The three live in packages that may not import each other, so no
        architecture check can compare them. A shared member would be one name
        for two phases, and a reader could not tell from it whether a run was
        refused before it existed, blocked after it was frozen, or stopped while
        it executed.
        """
        assert RUN_SETUP_REFUSAL_KINDS & BLOCKING_REASON_KINDS == frozenset()
        assert RUN_SETUP_REFUSAL_KINDS & EXECUTION_FAILURE_KINDS == frozenset()
        assert BLOCKING_REASON_KINDS & EXECUTION_FAILURE_KINDS == frozenset()
        assert len(RUN_SETUP_REFUSAL_KINDS) >= 1
        assert len(BLOCKING_REASON_KINDS) >= 1
        assert len(EXECUTION_FAILURE_KINDS) >= 1
