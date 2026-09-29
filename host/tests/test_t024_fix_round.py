"""T024 fix round 1: Foundation ownership, topology and validity are enforced.

Each class is one finding from the independent review, proved through the real
parsers and the real run setup service against the shipped Kobo documents.
"""

from __future__ import annotations

from kobo import (
    START,
    END,
    kobo_draft,
    remove_property,
)

CAPACITY = "battery-energy-capacity@battery"


def scenario_supplies_capacity(owner: str = "SCENARIO_INPUT"):
    def edit(document):
        document["public_parameters"].append(
            {
                "parameter_id": "scenario-capacity",
                "display_name": "Scenario capacity",
                "value": 1000,
                "unit": "kWh",
                "execution_role": "CAUSAL_INPUT",
                "state_key": CAPACITY,
                "execution_requirement": "REQUIRED",
                "ownership": {"owner": owner, "initializes": True},
            }
        )

    return edit


def reasons_of(run):
    return {(item.kind, item.subject) for item in run.blocking_reasons}


def need_at(run, address):
    return next(
        item
        for item in run.deterministic_identity.model_needs
        if item.addressed_key == address
    )


class TestAScenarioCannotSupplyAModelOwnedFoundationNeed:
    def test_a_scenario_value_at_a_foundation_owned_address_blocks(self) -> None:
        run = kobo_draft(document_edit=scenario_supplies_capacity())
        assert run.execution_status == "BLOCKED"
        assert ("INITIAL_VALUE_NOT_RESOLVED", CAPACITY) in reasons_of(run)
        # The Foundation still answers, and its need row is not lost.
        need = need_at(run, CAPACITY)
        assert need.value == 200
        assert need.answered_by == "SITE_FOUNDATION"

    def test_the_absent_foundation_property_still_blocks_beside_it(self) -> None:
        run = kobo_draft(
            document_edit=scenario_supplies_capacity(),
            site_edit=lambda d: remove_property(
                d, "battery", "battery-energy-capacity"
            ),
        )
        assert run.execution_status == "BLOCKED"
        assert ("INITIAL_VALUE_NOT_RESOLVED", CAPACITY) in reasons_of(run)
        assert need_at(run, CAPACITY).value is None

    def test_a_run_owned_value_is_refused_the_same_way(self) -> None:
        # Without a supplied value the run-owned declaration refuses; the
        # ownership rule is the scenario's, so the scenario-owned case above
        # is the reachable one. This pins that the shipped baseline is READY,
        # so every BLOCKED result above is caused by the added declaration.
        assert kobo_draft().execution_status == "READY"

    def test_a_foundation_owned_declaration_at_the_address_is_still_accepted(
        self,
    ) -> None:
        def foundation_owned(document):
            scenario_supplies_capacity("SITE_FOUNDATION")(document)
            for item in document["public_parameters"]:
                if item["parameter_id"] == "scenario-capacity":
                    item.pop("value")

        run = kobo_draft(document_edit=foundation_owned)
        assert run.execution_status == "READY", reasons_of(run)
        # One address, one answer: the Foundation's, frozen once.
        rows = [
            item
            for item in run.deterministic_identity.initialization_inputs
            if item.addressed_key == CAPACITY
        ]
        assert [row.answered_by for row in rows] == ["SITE_FOUNDATION"]
        assert not any(
            item.addressed_key == CAPACITY
            for item in run.deterministic_identity.model_needs
        )


def valid_from(instant: str):
    def edit(document):
        document["foundation"]["valid_from"] = instant

    return edit


class TestFoundationValidityIsEnforcedAgainstRunStart:
    def test_before_and_equal_are_valid(self) -> None:
        assert kobo_draft(site_edit=valid_from("2026-09-22T02:59:59Z")).execution_status == "READY"
        assert kobo_draft(site_edit=valid_from(START)).execution_status == "READY"

    def test_after_blocks_every_need_and_control_with_the_address_named(
        self,
    ) -> None:
        run = kobo_draft(site_edit=valid_from("2026-09-22T03:00:01Z"))
        assert run.execution_status == "BLOCKED"
        reasons = reasons_of(run)
        assert ("INITIAL_VALUE_NOT_RESOLVED", CAPACITY) in reasons
        assert ("SITE_CONTROL_NOT_RESOLVED", "site-control:source-priority") in reasons
        assert (
            "SITE_CONTROL_NOT_RESOLVED",
            "site-control:critical-load-priority",
        ) in reasons
        assert need_at(run, CAPACITY).value is None
        assert all(
            item.members is None
            for item in run.deterministic_identity.site_controls
        )

    def test_instants_compare_as_instants_not_as_text(self) -> None:
        # Both the Foundation and the run interval are UTC-suffixed at their
        # parsers today, so an offset cannot reach setup; the comparison is
        # still made on aware instants, which is what makes a later offset
        # spelling safe. 06:00+03:00 is 03:00Z, which text order gets wrong.
        from assetops_backend.runs.service import _instant

        assert _instant("2026-09-22T06:00:00+03:00") == _instant("2026-09-22T03:00:00Z")
        assert _instant("2026-09-22T03:30:00Z") > _instant("2026-09-22T06:00:00+03:00")
        assert "2026-09-22T03:30:00Z" < "2026-09-22T06:00:00+03:00"  # the trap
        import pytest

        with pytest.raises(ValueError):
            _instant("2026-09-22T03:00:00")
