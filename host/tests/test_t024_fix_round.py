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
        # A RUN_OVERRIDE declaration at the address is reached by supplying
        # the value through run_inputs, which setup accepts for a run-owned
        # parameter. The Foundation owns the need, so setup still blocks.
        run = kobo_draft(
            document_edit=scenario_supplies_capacity("RUN_OVERRIDE"),
            run_inputs=[
                {"parameter_id": "scenario-capacity", "value": 1000, "unit": "kWh"}
            ],
        )
        assert run.execution_status == "BLOCKED"
        assert ("INITIAL_VALUE_NOT_RESOLVED", CAPACITY) in reasons_of(run)
        need = need_at(run, CAPACITY)
        assert need.value == 200
        assert need.answered_by == "SITE_FOUNDATION"

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


# ---------------------------------------------------------------------------
# R2: the declared topology constrains execution and is frozen
# ---------------------------------------------------------------------------

import dataclasses  # noqa: E402

from assetops_backend.runs.parsing import (  # noqa: E402
    parse_run_document,
    render_run_document,
)
from execution_adapter import frozen_world_inputs, model_for, run_to_end  # noqa: E402


def without_connection(connection_id: str):
    def edit(document):
        topology = document["foundation"]["topology"]
        topology["connections"] = [
            item
            for item in topology["connections"]
            if item["connection_id"] != connection_id
        ]

    return edit


def attachments_of(run):
    return {
        (item.role, item.component_id, item.via_component_id)
        for item in run.deterministic_identity.bus_attachments
    }


class TestTheDeclaredTopologyMustConnectWhatTheModelServes:
    def test_the_connected_site_freezes_every_attachment(self) -> None:
        run = kobo_draft()
        assert run.execution_status == "READY"
        assert attachments_of(run) == {
            ("PV_SOURCE", "pv-array", "pv-inverter"),
            ("STORAGE", "battery", "battery-pcs"),
            ("LOAD", "load-res", None),
            ("LOAD", "load-clinic", None),
            ("LOAD", "load-mill", None),
        }
        assert {
            item.bus_component_id
            for item in run.deterministic_identity.bus_attachments
        } == {"ac-bus"}

    def test_a_disconnected_clinic_blocks_and_names_it(self) -> None:
        run = kobo_draft(site_edit=without_connection("bus-to-clinic"))
        assert run.execution_status == "BLOCKED"
        assert reasons_of(run) == {
            ("ELECTRICAL_TOPOLOGY_NOT_CONNECTED", "load-clinic")
        }
        # The connected loads are still attached; only the clinic is refused.
        assert ("LOAD", "load-res", None) in attachments_of(run)
        assert ("LOAD", "load-clinic", None) not in attachments_of(run)

    def test_a_disconnected_conversion_component_blocks_its_source(self) -> None:
        run = kobo_draft(site_edit=without_connection("pv-inverter-to-bus"))
        assert reasons_of(run) == {
            ("ELECTRICAL_TOPOLOGY_NOT_CONNECTED", "pv-array")
        }
        run = kobo_draft(site_edit=without_connection("battery-to-pcs"))
        assert reasons_of(run) == {
            ("ELECTRICAL_TOPOLOGY_NOT_CONNECTED", "battery")
        }

    def test_two_buses_or_none_is_not_the_supported_arrangement(self) -> None:
        def second_bus(document):
            import copy

            from kobo import component

            second = copy.deepcopy(component(document, "ac-bus"))
            second["component_id"] = "ac-bus-2"
            document["foundation"]["components"].append(second)
            topology = document["foundation"]["topology"]
            topology["nodes"].append(
                {"node_id": "bus-2", "component_id": "ac-bus-2", "node_role": "BUS"}
            )

        assert reasons_of(kobo_draft(site_edit=second_bus)) == {
            ("ELECTRICAL_TOPOLOGY_NOT_CONNECTED", "topology")
        }

        def second_bus(document):
            import copy

            from kobo import component

            second = copy.deepcopy(component(document, "ac-bus"))
            second["component_id"] = "ac-bus-2"
            document["foundation"]["components"].append(second)
            document["foundation"]["topology"]["nodes"].append(
                {"node_id": "bus-2", "component_id": "ac-bus-2", "node_role": "BUS"}
            )

        run = kobo_draft(site_edit=second_bus)
        assert not run.deterministic_identity.bus_attachments
        row = self.row_of(run)
        assert row.value == "none frozen"
        assert row.answered_by == "SITE_FOUNDATION"
        assert row.blocking_statement

    def test_a_profile_that_needs_none_still_says_so(self) -> None:
        from assetops_backend.runs.provenance import frozen_inputs
        from fixtures import draft

        run = draft()
        row = next(
            row
            for row in frozen_inputs(run.deterministic_identity, run.blocking_reasons)
            if row.identity_field == "bus_attachments"
        )
        assert row.value == "none needed by this profile"
        assert row.answered_by == "MODEL_PROFILE"
