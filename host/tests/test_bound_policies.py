"""The three bound policies, each exercised at the phase that owns it.

Criterion 10. `BOUND_POLICIES` has three members and deliberately no fourth
meaning "clamp quietly", and the three are decided at three different moments:

- `REFUSED_AT_PARSE` when the definition is read, so no run setup and no kernel
  ever sees the value. It is the only one of the three that can be decided
  without executing anything, and it is the product parser's;
- `FAIL_RUN` during execution, naming the entry that reached the bound;
- `BOUNDED_AND_RECORDED` during execution, applying the transition up to the
  bound, recording the quantity refused, and CONTINUING - which is the part
  T020B had to pin, because a bound that ended the run would be a disguised run
  failure and the policy set already has a separate member for that.

Only a composing test can show all three, because the first belongs to the
backend's parser and the other two to the kernel. This is that test, and it also
asserts that the fourth policy does not exist rather than only that three do.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction

import pytest
from fixtures import draft, scenario, shipped_document

from assetops_backend.scenarios.ports import ScenarioConfigurationInvalid
from assetops_contracts.execution_contract import (
    BOUND_CASES,
    BOUND_POLICIES,
    BOUND_POLICY_STATEMENTS,
)

from execution_adapter import run_to_end

TANK = "fuel-tank-volume@fuel-tank"


class TestThePolicySetItself:
    def test_there_are_three_and_each_says_what_it_commits_a_kernel_to(
        self,
    ) -> None:
        assert set(BOUND_POLICY_STATEMENTS) == BOUND_POLICIES
        assert len(BOUND_POLICIES) == 3

    def test_no_policy_means_clamp_quietly(self) -> None:
        """The absent fourth is the one that matters."""
        for policy in BOUND_POLICIES:
            assert "clamp" not in policy.lower()
        assert "no silent clamp" in (
            BOUND_POLICY_STATEMENTS["BOUNDED_AND_RECORDED"].lower()
        )

    def test_every_declared_case_carries_one_of_the_three(self) -> None:
        for case in BOUND_CASES:
            assert case.policy in BOUND_POLICIES, case.case_id


class TestRefusedAtParse:
    def test_a_negative_quantity_never_reaches_run_setup(self) -> None:
        """The `invalid-rate` case, at the phase it names.

        Refused where the definition is read, so there is no Draft to execute and
        no kernel involved at all. Asserted by catching the parser rather than by
        checking that a run was not created, because a refusal that happened later
        would also leave no run.
        """
        document = shipped_document()
        for entry in document["timeline"]:
            for parameter in entry.get("parameters", []):
                if parameter["parameter_id"] == "volume-removed":
                    parameter["value"] = -120

        with pytest.raises(ScenarioConfigurationInvalid) as raised:
            scenario(document)
        assert "cannot be negative" in str(raised.value)

        case = next(
            item for item in BOUND_CASES if item.case_id == "invalid-rate"
        )
        assert case.policy == "REFUSED_AT_PARSE"

    def test_the_valid_control_reaches_a_draft(self) -> None:
        """Otherwise the refusal above could be about anything in the document."""
        run = draft(definition=scenario(shipped_document()))
        assert run.execution_status == "READY"


class TestFailRun:
    def test_a_draw_the_tank_cannot_supply_fails_the_run_and_names_the_entry(
        self,
    ) -> None:
        """The `insufficient-fuel` case, during execution.

        The starting level is lowered to 100 litres, which the dispatch and the
        removal together take below zero. The run fails and names the tank; it
        does not empty the tank quietly, because that would invent the missing
        quantity out of the model instead of reporting the contradiction.
        """
        document = shipped_document()
        for parameter in document["public_parameters"]:
            if parameter["parameter_id"] == "starting-fuel-level":
                parameter["value"] = 100
        definition = scenario(document)

        executed = run_to_end(draft(definition=definition))

        assert executed.trajectory.outcome == "FAILED"
        assert executed.trajectory.failure.kind == "INTEGRATION_BOUND_FAILURE"
        assert executed.trajectory.failure.subject == TANK
        assert "insufficient-fuel" in executed.trajectory.failure.detail[0]
        assert "FAIL_RUN" in executed.trajectory.failure.detail[0]

        case = next(
            item for item in BOUND_CASES if item.case_id == "insufficient-fuel"
        )
        assert case.policy == "FAIL_RUN"

    def test_the_partial_result_is_labelled_failed_and_cannot_pass_for_a_run(
        self,
    ) -> None:
        """Criterion 12's second half, on a real Draft.

        The trajectory has boundaries - the run got some way in - and every one of
        the three things a reader would use to decide whether it is a complete run
        says it is not.
        """
        document = shipped_document()
        for parameter in document["public_parameters"]:
            if parameter["parameter_id"] == "starting-fuel-level":
                parameter["value"] = 100
        definition = scenario(document)
        executed = run_to_end(draft(definition=definition))

        assert executed.trajectory.boundaries
        assert executed.trajectory.is_complete is False
        assert executed.trajectory.outcome == "FAILED"
        assert executed.trajectory.failure is not None
        assert executed.trajectory.final.offset_minutes < 2460

        with pytest.raises(ValueError) as raised:
            replace(executed.trajectory, outcome="COMPLETED")
        assert "may not be labelled a whole one" in str(raised.value)


class TestBoundedAndRecorded:
    def test_the_delivery_is_bounded_and_the_run_continues(self) -> None:
        """The `fuel-tank-capacity` case, and the part T020B pinned.

        The tank fills, the refused quantity is recorded with its number, and the
        run reaches the end of its interval. A bound that ended the run would be a
        `FAIL_RUN` wearing another name.
        """
        definition = scenario()
        executed = run_to_end(draft(definition=definition))

        assert executed.trajectory.outcome == "COMPLETED"
        assert executed.trajectory.final.offset_minutes == 2460

        bounded = executed.trajectory.bounded_transitions
        assert len(bounded) == 1
        assert bounded[0].refused == Fraction("54.02")
        assert bounded[0].accepted == Fraction(500)
        assert bounded[0].requested == Fraction("554.02")

        case = next(
            item
            for item in BOUND_CASES
            if item.case_id == "fuel-tank-capacity"
        )
        assert case.policy == "BOUNDED_AND_RECORDED"

    def test_every_later_cause_applies_to_the_bounded_value(self) -> None:
        """"every later cause applies to the bounded value rather than to the
        unbounded one it would have reached", measured.

        A second draw is added after the delivery. The tank is at 500 after the
        bound, so a 100 litre draw leaves 400. Had the run continued from the
        unbounded 554.02 it would leave 454.02, and that is the number this test
        exists to rule out.
        """
        document = shipped_document()
        document["timeline"].append(
            {
                "event_id": "a-later-draw",
                "sequence": 9,
                "offset_minutes": 2430,
                "entry_kind": "EVENT",
                "category": "LOSS_OR_FRAUD",
                "description": "A draw after the tank reached its capacity.",
                "execution_role": "CAUSAL_INPUT",
                "state_key": TANK,
                "execution_requirement": "REQUIRED",
                "timing": {"shape": "POINT"},
                "state_effect": {
                    "direction": "DECREASE",
                    "quantity_parameter_id": "later-volume-drawn",
                },
                "parameters": [
                    {
                        "parameter_id": "later-volume-drawn",
                        "display_name": "Volume drawn afterwards",
                        "value": 100,
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
        definition = scenario(document)
        executed = run_to_end(draft(definition=definition))

        assert executed.trajectory.outcome == "COMPLETED"
        assert executed.trajectory.boundary_at(2400).stock(TANK) == Fraction(500)
        assert executed.trajectory.boundary_at(2430).stock(TANK) == Fraction(400)
        assert executed.trajectory.final.stock(TANK) == Fraction(400)
        assert executed.trajectory.final.stock(TANK) != Fraction("454.02")
