"""The shipped document's computed trajectory, its oracles, and the reconciler.

Three things this file settles.

**The document's private expectations are checked against the computed world.**
One of the four was inconsistent with it - `refuelling-is-not-a-loss` assumed the
300 litre delivery is a clean rise, and the tank fills at its capacity so 54.02
litres of it never arrive - and the correction is asserted here rather than only
written into the document. The other three are consistent, and the assertions say
why each one is.

**The reconciliation reference implementation has lost its authority.**
`D-2026-09-21-specification-reference-implementation` says it stops being an
authority the moment a kernel exists to be compared against. The two are run
against the same document and compared: the reconciler reports 310 litres at both
readings and the kernel computes 254.02, and the 55.98 between them is exactly the
fuel the model law burns and the document no longer declares. The kernel is right;
the reconciler is still right about the narrower question it asks, which is why it
stays until its last product-path caller goes.

**A second installation.** The capacity bound and the consumption coefficient are
taken from a second Site's Foundation - an 800 litre tank and a 0.285 L/kWh
generator - so a bound that matched by accident on the first Site cannot pass.
"""

from __future__ import annotations

from fractions import Fraction

from fixtures import (
    TWIN_TANK_TEMPLATE,
    draft,
    scenario,
    shipped_document,
    site_from_template,
)
from second_site import (
    SECOND_SITE_ID,
    SOUTH_CAPACITY,
    SOUTH_COEFFICIENT,
    SOUTH_TANK,
    second_site_document,
)

from assetops_backend.scenarios.execution import (
    reconcile_reported_observations,
)

from execution_adapter import run_to_end

TANK = "fuel-tank-volume@fuel-tank"
AFTER_DISPATCH = Fraction(18701, 50)
AFTER_REMOVAL = Fraction(12701, 50)
DISPATCH_TOTAL = Fraction(2799, 50)
REFUSED_AT_CAPACITY = Fraction(2701, 50)


def _shipped_trajectory():
    definition = scenario()
    return definition, run_to_end(draft(definition=definition))


class TestTheAuthoredExpectationsAgainstTheComputedWorld:
    def test_the_document_records_the_computed_trajectory_as_an_oracle(
        self,
    ) -> None:
        """Criterion 16: a TRAJECTORY expectation, and it stays private.

        Recorded in the document so the corrections beside it can be checked
        against something rather than taken. It is a private validation input like
        every other expectation - no executable path reads an oracle - which is
        why adding the kind moves no contract version.
        """
        definition, _ = _shipped_trajectory()
        trajectory_oracles = [
            expectation
            for expectation in definition.private_expectations
            if expectation.oracle_kind == "TRAJECTORY"
        ]
        assert len(trajectory_oracles) == 1
        statement = trajectory_oracles[0].statement
        for number in ("430", "3.49875", "374.02", "254.02", "54.02", "55.98"):
            assert number in statement, number

    def test_every_number_in_that_oracle_is_the_number_the_kernel_computes(
        self,
    ) -> None:
        """Otherwise the oracle would be prose beside an arithmetic nobody ran.

        The document states the trajectory; the kernel produces one; and these are
        the values both have to agree on. A kernel tuned to the oracle would not
        be caught by this, which is why the kernel's numbers were derived by hand
        in `simulator/tests/test_fuel_trajectory.py` first and the oracle was
        written from them.
        """
        _, executed = _shipped_trajectory()
        trajectory = executed.trajectory
        assert trajectory.boundary_at(0).stock(TANK) == Fraction(430)
        assert trajectory.boundary_at(1095).stock(TANK) == Fraction(430) - (
            Fraction("3.49875")
        )
        assert trajectory.boundary_at(1320).stock(TANK) == Fraction("374.02")
        assert trajectory.boundary_at(1545).stock(TANK) == Fraction("254.02")
        assert trajectory.boundary_at(2400).stock(TANK) == Fraction(500)
        assert trajectory.bounded_transitions[0].refused == Fraction("54.02")
        assert (
            sum(
                (
                    event.declared
                    for event in trajectory.applied_events
                    if event.origin == "MODEL_LAW"
                ),
                Fraction(0),
            )
            == Fraction("55.98")
        )

    def test_the_removal_magnitude_expectation_is_consistent(self) -> None:
        """"within 10 litres of the 120 litres this scenario removes".

        The computed world removes exactly 120, so the expectation is right and
        stays. Worth asserting rather than assuming: with the old 155 litre
        reading an analysis comparing the start level to the reading would have
        attributed about 275 litres, and no analysis of that evidence could have
        satisfied this expectation at all. Correcting the reading is what made it
        reachable.
        """
        _, executed = _shipped_trajectory()
        removed = sum(
            (
                event.declared
                for event in executed.trajectory.applied_events
                if event.event_id == "unaccounted-fuel-removal"
            ),
            Fraction(0),
        )
        assert removed == Fraction(120)
        assert abs(removed - Fraction(120)) <= 10

    def test_the_removal_is_separable_from_the_consumption_in_time(self) -> None:
        """The DETECTION expectation, against the trajectory rather than a hope.

        The two causes occupy disjoint spans and move the tank by different
        amounts per step, so nothing about the world makes them inseparable. What
        a later analysis can actually do with the evidence path is T028's.
        """
        _, executed = _shipped_trajectory()
        consumption = {
            event.at_offset_minutes
            for event in executed.trajectory.applied_events
            if event.origin == "MODEL_LAW"
        }
        removal = {
            event.at_offset_minutes
            for event in executed.trajectory.applied_events
            if event.event_id == "unaccounted-fuel-removal"
        }
        assert consumption & removal == set()
        assert max(consumption) < min(removal)

    def test_the_gap_does_not_hide_the_step_in_the_world(self) -> None:
        """The TIMING expectation's world half.

        The reporting gap covers [1490, 1580) and the removal [1500, 1545), so the
        removal is entirely inside it. In the world the level is 374.02 at 1490 and
        254.02 at 1580, so the step is there to be seen from either side; whether
        a reading exists at those instants is the reporting path's and T022's.
        """
        _, executed = _shipped_trajectory()
        assert executed.trajectory.boundary_at(1490 - 5).stock(TANK) == (
            AFTER_DISPATCH
        )
        assert executed.trajectory.boundary_at(1580 + 10).stock(TANK) == (
            AFTER_REMOVAL
        )
        assert AFTER_DISPATCH - AFTER_REMOVAL == Fraction(120)

    def test_the_delivery_expectation_now_names_the_bounded_half(self) -> None:
        """The one expectation the computed trajectory made inconsistent.

        It assumed a clean 300 litre rise. The tank holds 254.02 at offset 2400
        against a 500 litre capacity, so 245.98 enters and 54.02 is refused - and
        an analysis comparing a 300 litre delivery record against the level rise
        finds 54.02 litres that never appear in the tank. The old wording did not
        forbid attributing that to the removal because it did not know it existed.
        """
        definition, executed = _shipped_trajectory()
        statement = next(
            expectation.statement
            for expectation in definition.private_expectations
            if expectation.expectation_id == "refuelling-is-not-a-loss"
        )
        assert "the volume the tank accepts" in statement
        assert "did not fit" in statement
        assert "bounded delivery and not a loss" in statement

        bounded = executed.trajectory.bounded_transitions[0]
        assert bounded.requested - bounded.accepted == REFUSED_AT_CAPACITY
        accepted_of_the_delivery = Fraction(300) - REFUSED_AT_CAPACITY
        assert accepted_of_the_delivery == Fraction("245.98")
        assert (
            executed.trajectory.boundary_at(2400).stock(TANK)
            - executed.trajectory.boundary_at(2385).stock(TANK)
            == accepted_of_the_delivery
        )


class TestTheReconciliationReferenceImplementation:
    def test_the_two_disagree_and_the_difference_is_the_model_law(self) -> None:
        """Criterion 17, as a measurement rather than an assertion of authority.

        The reconciler reads the document and only the document. The document no
        longer declares what the generator burns, so what the reconciler cannot
        see is exactly the model law's 55.98 litres - and that is the whole of the
        disagreement, at both readings, to the litre.
        """
        definition, executed = _shipped_trajectory()
        results = {
            result.event_id: result
            for result in reconcile_reported_observations(definition)
        }
        assert set(results) == {
            "fuel-level-after-the-gap",
            "operator-tank-inspection",
        }

        world_at_1590 = executed.trajectory.boundary_at(1590).stock(TANK)
        world_at_1800 = executed.trajectory.boundary_at(1800).stock(TANK)
        assert world_at_1590 == AFTER_REMOVAL
        assert world_at_1800 == AFTER_REMOVAL

        for result in results.values():
            assert result.declared_value == 310.0
            assert result.reported_value == 254.02
            assert result.state == "NOT_ACCOUNTED_FOR"
            assert (
                Fraction(str(result.declared_value)) - world_at_1590
                == DISPATCH_TOTAL
            )
            assert Fraction(str(result.difference)) == -DISPATCH_TOTAL

    def test_the_kernel_is_the_one_that_accounts_for_the_difference(
        self,
    ) -> None:
        """Where they disagree the kernel is right, and this is why.

        The reconciler's 310 is the start level minus the removal. The kernel's
        254.02 is the same, minus the fuel the generator burnt - a quantity the
        Site declares and the document does not. So the reconciler is not wrong
        about what a document declares; it is answering a narrower question, and
        the wider one is the kernel's.
        """
        _, executed = _shipped_trajectory()
        assert Fraction(430) - Fraction(120) == Fraction(310)
        assert Fraction(310) - DISPATCH_TOTAL == AFTER_REMOVAL
        coefficient = executed.inputs.initial_value(
            "generator-specific-fuel-consumption@generator"
        )
        assert coefficient.value == Fraction(311, 1000)
        assert coefficient.answered_by == "SITE_FOUNDATION"

    def test_the_reconciler_cannot_see_the_bound_the_kernel_applies(
        self,
    ) -> None:
        """The other half of what it has stopped being an authority about.

        `declared_bounds` reports no upper number for the tank volume, which is
        the correct answer for a projection of a document that no longer carries
        the capacity. So nothing document-level can notice the delivery overfilling
        the tank, and the kernel is the first thing that can.
        """
        from assetops_backend.scenarios.execution import declared_bounds

        definition, executed = _shipped_trajectory()
        assert declared_bounds(definition)[TANK] == (0.0, None)
        assert executed.trajectory.bounded_transitions
        assert executed.trajectory.bounded_transitions[0].bound_value == (
            Fraction(500)
        )


class TestASecondSiteWithADifferentCapacity:
    def _executed(self):
        document = second_site_document()
        definition = scenario(document)
        site = site_from_template(
            TWIN_TANK_TEMPLATE,
            site_id=SECOND_SITE_ID,
            display_name="Twin-tank mini-grid",
        )
        run = draft(
            definition=definition,
            site=site,
            start_time="2026-09-21T00:00:00Z",
            end_time="2026-09-22T01:00:00Z",
            timestep_minutes=15,
        )
        assert run.execution_status == "READY", run.blocking_reasons
        return definition, run, run_to_end(run)

    def test_the_frozen_answers_are_this_site_s_and_not_the_other_one_s(
        self,
    ) -> None:
        _, run, executed = self._executed()
        frozen = {
            item.addressed_key: item
            for item in run.deterministic_identity.initialization_inputs
        }
        assert frozen[SOUTH_CAPACITY].value == 800.0
        assert frozen[SOUTH_CAPACITY].answered_by == "SITE_FOUNDATION"
        assert "component south-tank" in frozen[SOUTH_CAPACITY].answered_by_detail
        assert frozen[SOUTH_COEFFICIENT].value == 0.285
        assert "component south-generator" in (
            frozen[SOUTH_COEFFICIENT].answered_by_detail
        )

        assert executed.inputs.bound(SOUTH_TANK, "UPPER").value == Fraction(800)
        assert executed.inputs.bound(SOUTH_TANK, "UPPER").source_address == (
            SOUTH_CAPACITY
        )

    def test_the_trajectory_is_the_one_derived_for_this_installation(
        self,
    ) -> None:
        """Hand-derived in `second_site.py`, against 800 L and 0.285 L/kWh."""
        _, _, executed = self._executed()
        trajectory = executed.trajectory
        assert trajectory.outcome == "COMPLETED", trajectory.failure

        assert trajectory.boundary_at(0).stock(SOUTH_TANK) == Fraction(700)
        assert trajectory.boundary_at(615).stock(SOUTH_TANK) == Fraction(700) - (
            Fraction("4.275")
        )
        assert trajectory.boundary_at(720).stock(SOUTH_TANK) == Fraction("665.8")
        assert trajectory.boundary_at(960).stock(SOUTH_TANK) == Fraction("565.8")
        assert trajectory.boundary_at(1200).stock(SOUTH_TANK) == Fraction(800)
        assert trajectory.final.stock(SOUTH_TANK) == Fraction(800)

    def test_the_bound_it_reaches_is_this_tank_s_own(self) -> None:
        """65.8 litres refused against 800, not 54.02 against 500.

        Neither the capacity nor the coefficient nor the refused quantity appears
        anywhere in the kernel, so a bound that had been hard-wired to the first
        Site's numbers could not produce this.
        """
        _, _, executed = self._executed()
        bounded = executed.trajectory.bounded_transitions
        assert len(bounded) == 1
        assert bounded[0].address == SOUTH_TANK
        assert bounded[0].bound_value == Fraction(800)
        assert bounded[0].refused == Fraction("65.8")
        assert bounded[0].at_offset_minutes == 1200
        assert bounded[0].refused != REFUSED_AT_CAPACITY

    def test_the_other_tank_on_the_same_site_is_untouched(self) -> None:
        """One addressed fuel run, and the second one is not in the world at all.

        The Site declares a north tank of 500 litres and a north generator, and
        this document addresses neither. A kernel that resolved "the tank" rather
        than the addressed one would have picked one of two.
        """
        _, _, executed = self._executed()
        addresses = {
            address for address, _ in executed.trajectory.final.stocks
        }
        assert addresses == {SOUTH_TANK}
        assert "north-tank" not in str(addresses)

    def test_its_own_trajectory_oracle_matches_what_ran(self) -> None:
        definition, _, executed = self._executed()
        statement = next(
            expectation.statement
            for expectation in definition.private_expectations
            if expectation.oracle_kind == "TRAJECTORY"
        )
        for number in ("700", "665.8", "565.8", "800", "65.8"):
            assert number in statement, number
        assert executed.trajectory.final.stock(SOUTH_TANK) == Fraction(800)


class TestTheTwoShippedBoundCasesCarryOneBehaviour:
    def test_a_tank_capacity_and_a_delivery_overflow_are_the_same_policy(
        self,
    ) -> None:
        """So nothing turns on which of the two a bounded record names.

        The shipped delivery overfilling the tank is `delivery-overflow`'s case as
        much as `fuel-tank-capacity`'s, and the kernel names the case the declared
        bound carries. That is only safe because the two policies agree, and this
        is where that is checked rather than assumed.
        """
        from assetops_contracts.execution_contract import BOUND_CASES

        policies = {
            case.case_id: case.policy
            for case in BOUND_CASES
            if case.case_id in {"fuel-tank-capacity", "delivery-overflow"}
        }
        assert policies == {
            "fuel-tank-capacity": "BOUNDED_AND_RECORDED",
            "delivery-overflow": "BOUNDED_AND_RECORDED",
        }
