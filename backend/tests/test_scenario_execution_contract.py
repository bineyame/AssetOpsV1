"""The executable meaning of a scenario, over the shipped Fuel Loss Event.

`test_scenario_parsing.py` proves what the parser refuses. This file proves
what the contract SAYS once a document is accepted, and it is deliberately
written against the shipped definition rather than against the fixture,
because the acceptance criterion T018 carries is about that document: every
public value in it is accounted for, and no reported value reaches
initialization or a private-state transition.

The fixture appears here too, and for one reason worth stating. Its numbers
reconcile exactly and the shipped document's do not, so running both is what
makes the reconciliation assertions two-sided: a reconciliation that could
only ever answer `NOT_ACCOUNTED_FOR` would pass on a function that always said
so.

Every scan here asserts its own input is non-empty before asserting anything
about it. A scan over an empty set passes on a tree where the thing it
protects has been deleted, which is the failure shape this project has now
shipped nine times.
"""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pytest
import yaml
from scenario_fixtures import scenario_document

from assetops_backend.scenarios.execution import (
    BOUND_CASES,
    BOUND_POLICIES,
    CANONICAL_UNITS,
    DISPATCH_RULES,
    NON_NEGATIVE_DIMENSIONS,
    RATE_INTEGRALS,
    canonical_quantity,
    initialization_inputs,
    reconcile_reported_observations,
    state_transition_inputs,
    unaccounted_observations,
)
from assetops_backend.scenarios.models import (
    EXECUTABLE_ROLES,
    EXECUTION_ROLES,
    PARAMETER_UNITS,
    ROLES_BY_ENTRY_KIND,
    STATE_CHANGING_ROLES,
    TIMELINE_ENTRY_KINDS,
)
from assetops_backend.scenarios.parsing import parse_scenario_document
from assetops_backend.sites.models import DeviceSignal

REPO_ROOT = Path(__file__).resolve().parents[2]
SHIPPED_FUEL_LOSS_EVENT = (
    REPO_ROOT / "config" / "scenarios" / "fuel-loss-event.yaml"
)


def shipped_document() -> dict:
    return yaml.safe_load(
        SHIPPED_FUEL_LOSS_EVENT.read_text(encoding="utf-8")
    )


def shipped_scenario():
    return parse_scenario_document(
        shipped_document(), source="the shipped definition", origin="SHIPPED"
    )


def fixture_scenario():
    return parse_scenario_document(
        scenario_document(), source="a test", origin="SHIPPED"
    )


class TestCanonicalUnits:
    """A consumer converts a quantity without parsing what a screen shows."""

    def test_every_authored_unit_has_a_canonical_conversion(self) -> None:
        assert PARAMETER_UNITS, "the authoring unit vocabulary is empty"
        assert set(CANONICAL_UNITS) == set(PARAMETER_UNITS), (
            "The authoring unit vocabulary and the canonical conversion table "
            "have drifted apart. A unit an author may write with no canonical "
            "form reaches a consumer as text to parse, which is exactly what "
            "a canonical unit exists to prevent."
        )

    def test_a_rate_integrates_to_the_number_an_author_would_write(self) -> None:
        """Fourteen litres an hour for four hours is fifty-six litres.

        Computed through binary floats it is fifty-six point zero zero zero
        zero zero zero zero zero zero zero one, and a screen showing that
        would state a precision the scenario does not have.
        """
        rate, unit, dimension = canonical_quantity(14.0, "L/h")

        assert unit == "L/min"
        assert dimension == "VOLUME_RATE"
        assert rate * 240 == pytest.approx(56.0)

        transitions = {
            transition.event_id: transition
            for transition in state_transition_inputs(shipped_scenario())
        }
        assert "generator-run-window" in transitions
        assert transitions["generator-run-window"].applied_value == 56.0
        assert transitions["generator-run-window"].applied_unit == "L"

    def test_every_rate_dimension_can_be_accumulated(self) -> None:
        assert RATE_INTEGRALS
        for rate_dimension, quantity_dimension in RATE_INTEGRALS.items():
            assert any(
                canonical.dimension == rate_dimension
                for canonical in CANONICAL_UNITS.values()
            )
            assert any(
                canonical.dimension == quantity_dimension
                for canonical in CANONICAL_UNITS.values()
            )

    def test_the_non_negative_dimensions_are_real_dimensions(self) -> None:
        declared = {
            canonical.dimension for canonical in CANONICAL_UNITS.values()
        }
        assert NON_NEGATIVE_DIMENSIONS
        assert NON_NEGATIVE_DIMENSIONS <= declared


class TestEveryPublicValueIsAccountedFor:
    """The criterion, stated over the document rather than over the record.

    Reading the raw YAML rather than the parsed record matters: the parser is
    the thing under test here, and asserting over its output would be asking
    it whether it agreed with itself.
    """

    def public_values(self) -> list[tuple[str, dict]]:
        document = shipped_document()
        values: list[tuple[str, dict]] = [
            (f"public_parameters.{parameter['parameter_id']}", parameter)
            for parameter in document["public_parameters"]
        ]
        for entry in document["timeline"]:
            values.append((f"timeline.{entry['event_id']}", entry))
            for parameter in entry.get("parameters", []):
                values.append(
                    (
                        f"timeline.{entry['event_id']}."
                        f"{parameter['parameter_id']}",
                        parameter,
                    )
                )
        return values

    def test_the_document_has_public_values_to_account_for(self) -> None:
        values = self.public_values()

        assert len(values) > 15, [name for name, _ in values]

    def test_every_public_value_declares_exactly_one_execution_role(
        self,
    ) -> None:
        missing = [
            name
            for name, value in self.public_values()
            if value.get("execution_role") not in EXECUTION_ROLES
        ]

        assert not missing, (
            f"Public values {missing} in the shipped Fuel Loss Event declare "
            "no supported execution role. Every authored value says what an "
            "executor may do with it, because a value that does not can be "
            "read as a cause and as its own expected result at the same time."
        )

    def test_the_shipped_definition_exercises_every_execution_role(
        self,
    ) -> None:
        """Otherwise a role could be dead vocabulary nothing has ever used."""
        used = {value["execution_role"] for _, value in self.public_values()}

        assert used == EXECUTION_ROLES


class TestNoObservationReachesPrivateState:
    """The headline guarantee, asserted in both directions.

    A reported observation and a non-executable condition may not appear in
    the inputs a kernel would initialize or transition private world state
    from. Both sides are checked for emptiness first: if the shipped document
    carried no reported value, or produced no transition inputs, the
    disjointness below would hold for the wrong reason.
    """

    def test_only_a_causal_input_may_change_private_state(self) -> None:
        assert STATE_CHANGING_ROLES == {"CAUSAL_INPUT"}
        assert STATE_CHANGING_ROLES < EXECUTABLE_ROLES

    def test_an_evidence_condition_can_never_be_a_cause(self) -> None:
        """The ambiguity T018 exists to remove, as a rule over the taxonomy."""
        assert set(ROLES_BY_ENTRY_KIND) == set(TIMELINE_ENTRY_KINDS)

        for kind, roles in ROLES_BY_ENTRY_KIND.items():
            assert roles <= EXECUTION_ROLES, kind

        assert "CAUSAL_INPUT" not in ROLES_BY_ENTRY_KIND["EVIDENCE_CONDITION"]
        assert "FORCING_INPUT" not in ROLES_BY_ENTRY_KIND["EVIDENCE_CONDITION"]
        assert (
            "REPORTED_OBSERVATION" not in ROLES_BY_ENTRY_KIND["EVENT"]
        )

    def test_the_shipped_definition_really_carries_reported_values(
        self,
    ) -> None:
        scenario = shipped_scenario()

        reported = [
            parameter.parameter_id
            for entry in scenario.timeline
            for parameter in entry.parameters
            if parameter.execution_role == "REPORTED_OBSERVATION"
        ]

        assert sorted(reported) == [
            "hand-recorded-level",
            "level-after-the-gap",
        ]

    def test_no_reported_or_descriptive_value_initializes_or_transitions(
        self,
    ) -> None:
        scenario = shipped_scenario()

        not_executable_on_state = {
            parameter.parameter_id
            for parameter in _every_parameter(scenario)
            if parameter.execution_role
            in {"REPORTED_OBSERVATION", "NON_EXECUTABLE_CONDITION"}
        }
        assert not_executable_on_state, (
            "the shipped definition declares no reported or descriptive "
            "value, so the disjointness below is over an empty set"
        )

        initialization = initialization_inputs(scenario)
        transitions = state_transition_inputs(scenario)
        assert initialization, "no initialization inputs to check against"
        assert transitions, "no state transition inputs to check against"

        reached = {item.parameter_id for item in initialization} | {
            item.parameter_id for item in transitions
        }

        assert not (reached & not_executable_on_state), (
            f"Values {sorted(reached & not_executable_on_state)} reach "
            "initialization or a private-state transition although they are "
            "reported observations or descriptions. A reported value that "
            "can initialize private state is an authored trajectory wearing "
            "an observation's name."
        )

    def test_a_reported_value_carries_no_ownership_record_at_all(self) -> None:
        """The structural half: there is no field it could arrive in."""
        scenario = shipped_scenario()

        reported = [
            parameter
            for parameter in _every_parameter(scenario)
            if parameter.execution_role == "REPORTED_OBSERVATION"
        ]
        assert reported

        for parameter in reported:
            assert parameter.ownership is None, parameter.parameter_id

        for entry in scenario.timeline:
            if entry.execution_role == "REPORTED_OBSERVATION":
                assert entry.state_effect is None, entry.event_id

    def test_every_initial_world_value_has_exactly_one_owner(self) -> None:
        scenario = shipped_scenario()
        inputs = initialization_inputs(scenario)

        assert inputs
        state_keys = [item.state_key for item in inputs]
        assert len(state_keys) == len(set(state_keys))

        owners = {item.state_key: item.owner for item in inputs}
        assert owners == {
            "fuel-tank-capacity": "SITE_FOUNDATION",
            "fuel-tank-volume": "SCENARIO_INPUT",
        }


class TestObservationSourcesAndCadence:
    def test_each_reported_entry_names_the_source_it_arrives_through(
        self,
    ) -> None:
        scenario = shipped_scenario()
        sources = {
            source.source_id: source
            for source in scenario.observation_sources
        }
        assert sources

        bindings = {
            entry.event_id: entry.observation
            for entry in scenario.timeline
            if entry.observation is not None
        }
        assert set(bindings) == {
            "fuel-level-after-the-gap",
            "operator-tank-inspection",
        }

        device = sources[bindings["fuel-level-after-the-gap"].source_id]
        assert device.source_kind == "DEVICE_SIGNAL"
        assert device.device_id == "fuel-level-sensor"
        assert device.signal_id == "fuel-level"

        hand = sources[bindings["operator-tank-inspection"].source_id]
        assert hand.source_kind == "OPERATOR_RECORD"
        assert hand.device_id is None
        assert hand.signal_id is None

    def test_no_source_declares_a_cadence(self) -> None:
        scenario = shipped_scenario()

        assert scenario.observation_sources
        for source in scenario.observation_sources:
            assert source.cadence_ownership in {
                "NOT_DECLARED",
                "NOT_APPLICABLE",
            }

    def test_the_foundation_signal_record_has_nowhere_to_put_a_cadence(
        self,
    ) -> None:
        """The claim "Foundation declares no cadence", checked rather than said.

        `DeviceSignal` is what a Foundation declares about a signal. If a
        cadence, a period, a rate or an interval ever became a field on it,
        this product would have a cadence to infer from and the prohibition
        T018 carries would quietly stop meaning anything.
        """
        declared = {field.name for field in fields(DeviceSignal)}

        assert declared == {"signal_id", "display_name", "unit"}

    def test_nothing_in_the_scenario_schema_spells_a_cadence(self) -> None:
        document = shipped_document()
        banned = ("cadence_minutes", "period", "interval", "sample_rate")

        found = sorted(
            key
            for key in _every_key(document)
            if any(term in key for term in banned)
        )

        assert not found, (
            f"The shipped definition declares {found}. A reporting cadence is "
            "owned by a versioned observation profile, not by a scenario: a "
            "site's foundation declares that a signal can report and declares "
            "no rate."
        )


class TestTimingAndDispatch:
    def test_every_entry_declares_a_validated_timing_shape(self) -> None:
        scenario = shipped_scenario()

        shapes = {entry.event_id: entry.timing for entry in scenario.timeline}
        assert shapes

        for event_id, timing in shapes.items():
            if timing.shape == "POINT":
                assert timing.duration_minutes is None, event_id
            elif timing.shape == "WINDOW":
                assert timing.duration_minutes is not None, event_id
                assert timing.duration_minutes >= 1, event_id
            else:
                assert timing.duration_minutes is None, event_id

    def test_the_shipped_definition_uses_both_dispatch_shapes(self) -> None:
        """Otherwise "point and window have distinct semantics" is untested."""
        scenario = shipped_scenario()
        used = {entry.timing.shape for entry in scenario.timeline}

        assert {"POINT", "WINDOW"} <= used

    def test_the_dispatch_rules_state_the_boundary_case(self) -> None:
        assert DISPATCH_RULES
        by_id = {rule.rule_id: rule for rule in DISPATCH_RULES}

        assert "point-applied-once" in by_id
        assert "window-active-span" in by_id
        assert "half-open-interval" in by_id

        for rule in DISPATCH_RULES:
            assert rule.statement.strip()
            assert rule.display_name.strip()


class TestBoundCases:
    def test_the_four_bound_cases_the_task_names_are_declared(self) -> None:
        declared = {case.case_id for case in BOUND_CASES}

        assert declared == {
            "fuel-tank-capacity",
            "delivery-overflow",
            "insufficient-fuel",
            "invalid-rate",
        }

    def test_no_bound_policy_is_a_silent_one(self) -> None:
        assert BOUND_CASES
        for case in BOUND_CASES:
            assert case.policy in BOUND_POLICIES, case.case_id
            assert case.statement.strip()

        for policy in BOUND_POLICIES:
            assert "SILENT" not in policy
            assert "CLAMP" not in policy
            assert "IGNORE" not in policy
            assert "DISCARD" not in policy

    def test_the_declared_causes_reach_the_capacity_bound(self) -> None:
        """The capacity case is not hypothetical for this scenario.

        Starting level, less the dispatch window's consumption, less the
        removal, plus the scheduled delivery, is above the capacity the
        scenario assumes. That is why a policy for it has to exist before a
        kernel does, and why "clamp quietly" is not one of the options.
        """
        scenario = shipped_scenario()
        initial = {
            item.state_key: item.canonical_value
            for item in initialization_inputs(scenario)
        }
        level = initial["fuel-tank-volume"]
        for transition in state_transition_inputs(scenario):
            if transition.state_key != "fuel-tank-volume":
                continue
            level += (
                transition.applied_value
                if transition.direction == "INCREASE"
                else -transition.applied_value
            )

        assert level > initial["fuel-tank-capacity"]


class TestReconciliation:
    """Two-sided on purpose: one document reconciles and one does not."""

    def test_the_fixture_reconciles_exactly(self) -> None:
        results = reconcile_reported_observations(fixture_scenario())

        assert results
        assert [result.state for result in results] == [
            "ACCOUNTED_FOR",
            "ACCOUNTED_FOR",
        ]
        assert not unaccounted_observations(results)

    def test_one_changed_value_makes_the_fixture_stop_reconciling(self) -> None:
        document = scenario_document()
        document["timeline"][2]["parameters"][0]["value"] = 180

        results = reconcile_reported_observations(
            parse_scenario_document(document, source="a test", origin="SHIPPED")
        )

        unaccounted = unaccounted_observations(results)
        assert [result.event_id for result in unaccounted] == ["second-entry"]
        assert unaccounted[0].difference == -14.0

    def test_the_shipped_readings_are_not_reached_by_the_declared_causes(
        self,
    ) -> None:
        """The 254 L against 155 L and 150 L conflict, stated rather than hidden.

        Neither reading prescribes private tank state: both are reported
        observations from a named source and neither appears in the
        initialization or transition inputs, which the tests above assert. So
        the contract is internally coherent. What it also says, out loud, is
        that the causes it declares do not reach either reading - and it says
        it with the quantity and the sign rather than leaving a reader to
        subtract.
        """
        results = {
            result.event_id: result
            for result in reconcile_reported_observations(shipped_scenario())
        }

        assert set(results) == {
            "fuel-level-after-the-gap",
            "operator-tank-inspection",
        }

        after_the_gap = results["fuel-level-after-the-gap"]
        assert after_the_gap.declared_value == 254.0
        assert after_the_gap.reported_value == 155.0
        assert after_the_gap.difference == -99.0
        assert after_the_gap.state == "NOT_ACCOUNTED_FOR"
        assert after_the_gap.accounted_by == (
            "generator-run-window",
            "unaccounted-fuel-removal",
        )

        inspection = results["operator-tank-inspection"]
        assert inspection.declared_value == 254.0
        assert inspection.reported_value == 150.0
        assert inspection.difference == -104.0
        assert inspection.state == "NOT_ACCOUNTED_FOR"

    def test_a_reading_inside_an_open_causal_window_is_not_guessed_at(
        self,
    ) -> None:
        """Apportioning part of a window would be a transition rule.

        Transition rules belong to the kernel. The contract says it cannot
        answer rather than inventing half an effect.
        """
        document = scenario_document()
        document["timeline"][2]["offset_minutes"] = 90

        results = reconcile_reported_observations(
            parse_scenario_document(document, source="a test", origin="SHIPPED")
        )
        by_event = {result.event_id: result for result in results}

        assert by_event["second-entry"].state == "NOT_RECONCILABLE"
        assert by_event["second-entry"].declared_value is None


def _every_parameter(scenario):
    for parameter in scenario.public_parameters:
        yield parameter
    for entry in scenario.timeline:
        for parameter in entry.parameters:
            yield parameter


def _every_key(node):
    pending = [node]
    while pending:
        current = pending.pop()
        if isinstance(current, dict):
            for key, child in current.items():
                if isinstance(key, str):
                    yield key
                pending.append(child)
        elif isinstance(current, list):
            pending.extend(current)
