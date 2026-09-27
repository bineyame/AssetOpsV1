"""The five defects T021's independent review returned, through the real path.

Every reproduction here is built the way the review built its own: a document
parsed by the real scenario parser, a Site instantiated by `SiteCreationService`,
a Draft frozen by `RunSetupService`, and execution through the host leaf. None is
a hand-built record, because the point of each is that an ORDINARY accepted
`READY` run reached a wrong answer.

`.agent/T021-guard-probes.py` reverts each fix and asserts the matching test
fails, which is how the first fourteen guards were proved and is what stops these
five from being tests that pass against the thing they were written to catch.

R1's reproductions live in `test_host_execution.py` beside the reconstruction
class they belong to. The other four are here.
"""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction

import pytest

from fixtures import draft, scenario, shipped_document

from execution_adapter import run_to_end

TANK = "fuel-tank-volume@fuel-tank"
GENERATOR = "generator-output-power@generator"
COEFFICIENT = "generator-specific-fuel-consumption@generator"
AFTER_DISPATCH = Fraction(18701, 50)
PER_STEP_ENERGY = Fraction(45, 4)


class TestR2AdjacentWindowsShareAStepWithoutBeingAmbiguous:
    """Criterion 7, and the case T020B spent four rounds settling.

    `window-active-span` states it: two windows meeting end to start share no
    INSTANT, may still concern one STEP, and each applies over its own portion of
    it with nothing stretched across the rest and nothing blended. The kernel read
    the phase order from the contract and called the contract's own overlap
    predicate, and then refused this.
    """

    def _split_dispatch(self, *, first_length: int = 5) -> dict:
        """The shipped dispatch, split into two adjacent entries.

        The join falls at 1085, which is INSIDE the step beginning at 1080 at a
        fifteen-minute timestep. That is the whole point: a join on a step
        boundary would never have exercised the defect.
        """
        document = shipped_document()
        first = next(
            entry
            for entry in document["timeline"]
            if entry["event_id"] == "generator-run-window"
        )
        second = deepcopy(first)
        total = first["timing"]["duration_minutes"]
        first["timing"]["duration_minutes"] = first_length
        second["event_id"] = "second-generator-window"
        second["offset_minutes"] = first["offset_minutes"] + first_length
        second["timing"]["duration_minutes"] = total - first_length
        for parameter in second["parameters"]:
            parameter["parameter_id"] += "-second"
        document["timeline"].append(second)
        document["timeline"].sort(key=lambda entry: entry["offset_minutes"])
        for index, entry in enumerate(document["timeline"], 1):
            entry["sequence"] = index
        return document

    def test_the_split_dispatch_produces_the_identical_trajectory(self) -> None:
        """The strongest form the claim can take.

        Both entries force 45 kW, and together they cover exactly what the single
        window covered, so a kernel that apportions each exposure over its own
        part of the shared step must produce the same numbers to the last
        rational. It failed outright before.
        """
        single = scenario()
        split = scenario(self._split_dispatch())

        original = run_to_end(draft(definition=single)).trajectory
        divided = run_to_end(draft(definition=split)).trajectory

        assert divided.outcome == "COMPLETED", divided.failure
        assert divided.stock_series(TANK) == original.stock_series(TANK)
        assert divided.boundary_at(1320).stock(TANK) == AFTER_DISPATCH

    def test_the_shared_step_records_both_exposures_separately(self) -> None:
        """"outputs distinguish the two exposures", measured.

        The step beginning at 1080 is exposed to the first window over
        [1080, 1085) and to the second over [1085, 1095). Two rows, each with its
        own span and its own event, and the step's delivered energy is their sum.
        """
        split = scenario(self._split_dispatch())
        trajectory = run_to_end(draft(definition=split)).trajectory

        shared = trajectory.boundary_at(1080)
        exposures = shared.exposures_of(GENERATOR)
        assert len(exposures) == 2
        assert [
            (exposure.event_id, exposure.from_offset, exposure.to_offset)
            for exposure in exposures
        ] == [
            ("generator-run-window", 1080, 1085),
            ("second-generator-window", 1085, 1095),
        ]
        assert [exposure.exposed_minutes for exposure in exposures] == [5, 10]

        # The next step sees only the second window, over its whole length.
        after = trajectory.boundary_at(1095).exposures_of(GENERATOR)
        assert len(after) == 1
        assert after[0].event_id == "second-generator-window"
        assert after[0].exposed_minutes == 15

    def test_the_interval_energy_of_the_shared_step_is_the_two_added(
        self,
    ) -> None:
        split = scenario(self._split_dispatch())
        trajectory = run_to_end(draft(definition=split)).trajectory

        # 45 kW over 5 minutes plus 45 kW over 10 minutes is 45 kW over 15, which
        # is the same 45/4 kWh the undivided window delivered.
        assert trajectory.boundary_at(1095).interval_measurement(
            GENERATOR
        ) == PER_STEP_ENERGY
        assert Fraction(45) * Fraction(5, 60) + Fraction(45) * Fraction(
            10, 60
        ) == PER_STEP_ENERGY

    def test_a_single_value_accessor_refuses_to_answer_for_two_exposures(
        self,
    ) -> None:
        """No accessor returns one of two values, and none returns None either.

        `None` would be indistinguishable from the forcing being unavailable,
        which is the one thing the record must not blur.
        """
        split = scenario(self._split_dispatch())
        trajectory = run_to_end(draft(definition=split)).trajectory
        with pytest.raises(ValueError) as raised:
            trajectory.boundary_at(1080).forcing(GENERATOR)
        assert "no single value" in str(raised.value)

    def test_genuinely_overlapping_declarations_are_still_refused(self) -> None:
        """The honest refusal stays, which is what keeps the fix from being a
        blanket permission.

        Two windows that OVERLAP share a stretch of the step of non-zero length,
        and nothing says whether they are the ends of a ramp or two named levels.
        Here the second starts one minute before the first ends.
        """
        document = self._split_dispatch(first_length=10)
        second = next(
            entry
            for entry in document["timeline"]
            if entry["event_id"] == "second-generator-window"
        )
        second["offset_minutes"] -= 1
        second["timing"]["duration_minutes"] += 1
        trajectory = run_to_end(
            draft(definition=scenario(document))
        ).trajectory

        assert trajectory.outcome == "FAILED"
        assert trajectory.failure.kind == "FORCING_VALUE_AMBIGUOUS"
        assert trajectory.failure.at_offset_minutes == 1080
        assert "which is inside the first" in trajectory.failure.detail[1]


class TestR3AMissingLawOperandIsAClassifiedFailure:
    """Criteria 3 and 12. Neither silence nor a dictionary exception.

    Both reproductions are documents the parser accepts and run setup calls
    `READY`, which is the point: the run was permitted to attempt execution and
    the kernel then had to say something true about what it could not do.
    """

    def test_a_missing_consumption_coefficient_stops_the_run(self) -> None:
        """It reported COMPLETED with zero law events and 430 L at 1320.

        Missing consumption was treated as zero consumption, which is the
        difference between this and the supported zero-coefficient endpoint: no
        coefficient was supplied at all.
        """
        document = shipped_document()
        document["public_parameters"] = [
            parameter
            for parameter in document["public_parameters"]
            if parameter["parameter_id"] != "generator-specific-consumption"
        ]
        definition = scenario(document)
        run = draft(definition=definition)
        assert run.execution_status == "READY", run.blocking_reasons

        trajectory = run_to_end(run).trajectory

        assert trajectory.outcome == "FAILED"
        assert trajectory.failure.kind == "INITIAL_STATE_UNANSWERED"
        assert trajectory.failure.subject == COEFFICIENT
        assert "multiplies by" in trajectory.failure.detail[0]
        assert trajectory.boundaries == ()

    def test_a_missing_output_stock_stops_the_run_without_an_exception(
        self,
    ) -> None:
        """It raised a raw `KeyError` and returned no trajectory at all.

        The capacity still identifies the tank here, so this is not the
        `TOPOLOGY_INCONSISTENT` case where the run names no tank: the machine is
        there and its stored volume is not.
        """
        document = shipped_document()
        document["public_parameters"] = [
            parameter
            for parameter in document["public_parameters"]
            if parameter["parameter_id"] != "starting-fuel-level"
        ]
        document["timeline"] = [
            entry
            for entry in document["timeline"]
            if not entry.get("state_effect")
        ]
        for index, entry in enumerate(document["timeline"], 1):
            entry["sequence"] = index
        definition = scenario(document)
        run = draft(definition=definition)
        assert run.execution_status == "READY", run.blocking_reasons

        trajectory = run_to_end(run).trajectory

        assert trajectory.outcome == "FAILED"
        assert trajectory.failure.kind == "INITIAL_STATE_UNANSWERED"
        assert trajectory.failure.subject == TANK
        assert "moves that stock" in trajectory.failure.detail[0]
        assert trajectory.is_complete is False

    def test_an_explicitly_supplied_zero_coefficient_still_burns_nothing(
        self,
    ) -> None:
        """The control, and what makes the two tests above about ABSENCE.

        A generator declared to burn nothing is odd and not unphysical, and it
        completes. Without this the failure above could be read as the kernel
        refusing a zero.
        """
        document = shipped_document()
        for parameter in document["public_parameters"]:
            if parameter["parameter_id"] == "generator-specific-consumption":
                # Owned by the scenario rather than the Foundation, because a
                # Foundation-owned parameter states no value by design.
                parameter["ownership"]["owner"] = "SCENARIO_INPUT"
                parameter["value"] = 0
        definition = scenario(document)
        trajectory = run_to_end(draft(definition=definition)).trajectory

        assert trajectory.outcome == "COMPLETED", trajectory.failure
        assert trajectory.boundary_at(1320).stock(TANK) == Fraction(430)


class TestR4ADeclaredCauseSurvivesEitherFrozenCarrier:
    """Criterion 4. A parameter that initializes still causes what it declares.

    A run freezes a parameter once: as an initialization input if it initializes a
    state, and as a resolved parameter otherwise. The projection read only the
    second, so a timeline entry whose effect named a parameter frozen in the first
    lost its cause and the removal simply stopped happening.
    """

    def _initializing_removal(self) -> dict:
        """The shipped document with the removal's own parameter initializing.

        An already-valid route through the split frozen collections: the parser
        accepts it, setup returns `READY`, and initializing from a parameter does
        not cancel the state effect that names it.
        """
        document = shipped_document()
        document["public_parameters"] = [
            parameter
            for parameter in document["public_parameters"]
            if parameter["parameter_id"] != "starting-fuel-level"
        ]
        removal = next(
            entry
            for entry in document["timeline"]
            if entry["event_id"] == "unaccounted-fuel-removal"
        )
        removal["parameters"][0]["ownership"]["initializes"] = True
        return document

    def test_the_cause_is_frozen_even_though_its_parameter_initializes(
        self,
    ) -> None:
        definition = scenario(self._initializing_removal())
        run = draft(definition=definition)
        assert run.execution_status == "READY", run.blocking_reasons

        # Frozen in the OTHER collection, which is the whole premise.
        initial = {
            item.parameter_id
            for item in run.deterministic_identity.initialization_inputs
        }
        resolved = {
            item.parameter_id
            for item in run.deterministic_identity.scenario.resolved_parameters
        }
        assert "volume-removed" in initial
        assert "volume-removed" not in resolved

        causes = {
            cause.event_id: cause
            for cause in run.deterministic_identity.causes
        }
        assert "unaccounted-fuel-removal" in causes
        assert causes["unaccounted-fuel-removal"].canonical_value == 120.0

    def test_the_removal_is_applied_and_reaches_the_insufficient_fuel_policy(
        self,
    ) -> None:
        """What should happen, and did not.

        The tank starts at the 120 L the removal declares, the dispatch burns
        55.98 L to 64.02 L, and the still-declared 120 L removal then takes it
        below zero - which is `insufficient-fuel` and `FAIL_RUN`. Before the fix
        the run COMPLETED at 64.02 L with no removal applied at all.
        """
        definition = scenario(self._initializing_removal())
        trajectory = run_to_end(draft(definition=definition)).trajectory

        applied = [
            event
            for event in trajectory.applied_events
            if event.event_id == "unaccounted-fuel-removal"
        ]
        assert applied, "the declared removal was not applied at all"
        assert trajectory.boundary_at(1500).stock(TANK) == Fraction("64.02")
        assert trajectory.outcome == "FAILED"
        assert trajectory.failure.kind == "INTEGRATION_BOUND_FAILURE"
        assert "insufficient-fuel" in trajectory.failure.detail[0]

    def test_the_ordinary_carrier_still_works(self) -> None:
        """The non-empty control for the other half of the same lookup."""
        run = draft()
        resolved = {
            item.parameter_id
            for item in run.deterministic_identity.scenario.resolved_parameters
        }
        assert "volume-removed" in resolved
        trajectory = run_to_end(run).trajectory
        assert trajectory.boundary_at(1545).stock(TANK) == Fraction("254.02")


class TestR5AnExcludedInputNeitherActsNorInventsAMachine:
    """Criterion 13's exclusion obligation, at the state/scope/role grain.

    The run explicitly records these addresses as unsupported optional inputs.
    The kernel consulted the model before consulting that record, and its handler
    lookup ignored scope, so a site-wide declaration matched a component-scoped
    handler and a second machine was invented out of it.
    """

    def _with_optional_at_site_scope(
        self, state_key: str, unit: str, value: float
    ) -> dict:
        document = shipped_document()
        document["public_parameters"].append(
            {
                "parameter_id": "an-optional-site-wide-value",
                "display_name": "An optional site-wide value",
                "value": value,
                "unit": unit,
                "execution_role": "CAUSAL_INPUT",
                "state_key": state_key,
                "execution_requirement": "OPTIONAL",
                "ownership": {
                    "owner": "SCENARIO_INPUT",
                    "initializes": True,
                },
            }
        )
        return document

    def test_a_site_wide_coefficient_does_not_invent_a_second_generator(
        self,
    ) -> None:
        definition = scenario(
            self._with_optional_at_site_scope(
                "site:generator-specific-fuel-consumption", "L/kWh", 0.9
            )
        )
        run = draft(definition=definition)
        assert run.execution_status == "READY", run.blocking_reasons
        # The non-empty control: the run really does record this exclusion, so the
        # test is about the cross-reference being honoured rather than about an
        # address nobody declared.
        assert "site:generator-specific-fuel-consumption" in {
            item.addressed_key for item in run.unsupported_optional_inputs
        }

        trajectory = run_to_end(run).trajectory

        assert trajectory.outcome == "COMPLETED", trajectory.failure
        assert trajectory.boundary_at(1320).stock(TANK) == AFTER_DISPATCH
        assert any(
            "site:generator-specific-fuel-consumption" in note
            for note in trajectory.notes
        )

    def test_a_site_wide_volume_does_not_invent_a_second_tank(self) -> None:
        definition = scenario(
            self._with_optional_at_site_scope("site:fuel-tank-volume", "L", 20)
        )
        run = draft(definition=definition)
        assert run.execution_status == "READY", run.blocking_reasons
        assert "site:fuel-tank-volume" in {
            item.addressed_key for item in run.unsupported_optional_inputs
        }

        trajectory = run_to_end(run).trajectory

        assert trajectory.outcome == "COMPLETED", trajectory.failure
        assert trajectory.final.stock(TANK) == Fraction(500)

    def test_the_excluded_value_is_not_used_either(self) -> None:
        """Neither manufacture topology nor act. Both halves.

        0.9 L/kWh is three times the generator's real coefficient, so a kernel
        that had used the excluded value instead of ignoring it would show it: the
        dispatch would burn 162 L rather than 55.98 L.
        """
        definition = scenario(
            self._with_optional_at_site_scope(
                "site:generator-specific-fuel-consumption", "L/kWh", 0.9
            )
        )
        executed = run_to_end(draft(definition=definition))

        assert "site:generator-specific-fuel-consumption" not in {
            address for address, _ in executed.trajectory.final.stocks
        }
        burnt = sum(
            (
                event.declared
                for event in executed.trajectory.applied_events
                if event.origin == "MODEL_LAW"
            ),
            Fraction(0),
        )
        assert burnt == Fraction("55.98")
        assert burnt != Fraction("162")

    def test_the_same_state_at_component_scope_is_still_modelled(self) -> None:
        """The control that stops the exclusion becoming a blanket skip.

        `generator-specific-fuel-consumption@generator` is the same semantic key
        at the scope this model claims, and it is consumed: the dispatch burns
        55.98 L. A kernel that had started ignoring the key would pass every test
        above and fail this one.
        """
        executed = run_to_end(draft())
        coefficient = executed.inputs.initial_value(COEFFICIENT)
        assert coefficient is not None
        assert coefficient.value == Fraction(311, 1000)
        assert executed.trajectory.boundary_at(1320).stock(TANK) == (
            AFTER_DISPATCH
        )
