"""T024: the daytime mini-grid, proved against the task's criteria and proof table.

Every run here is a Draft frozen by the real run setup service from a Site
created from the shipped Kobo template and a shipped Kobo scenario, executed by
the real kernel through the host adapter. A variation is made by editing one
fact in the document or the Site before the product parses it.

The hand computations in `TestIndependentEnergyArithmetic` were done on paper
from the template's numbers before being written down, and are deliberately not
derived from the model's own code.
"""

from __future__ import annotations

import copy
from dataclasses import fields, replace
from fractions import Fraction

import pytest

from assetops_backend.runs.profiles import LAB_PUBLICATION_PROFILE
from assetops_contracts.control import (
    AcceptedFlowSet,
    ControllerView,
    ControlStep,
)
from assetops_contracts.observation import DeviceObservation
from assetops_contracts.trajectory import PrivateTrajectory
from assetops_simulator.kernel.execute import Execution, execute
from assetops_simulator.kernel.model import StepContext
from assetops_simulator.packs.minigrid import DAYTIME_MINI_GRID_MODEL
from assetops_simulator.observation.transform import generate_observations

from execution_adapter import (
    frozen_world_inputs,
    model_for,
    reporting_inputs,
    run_to_end,
)
from kobo import (
    component,
    kobo_document,
    kobo_draft,
    remove_property,
    set_property,
)

SOC = "battery-state-of-charge@battery"
LOADS = ("load-res", "load-clinic", "load-mill")
HUNDRED = Fraction(100)


def trajectory_of(run) -> PrivateTrajectory:
    assert run.execution_status == "READY", [
        (reason.kind, reason.subject) for reason in run.blocking_reasons
    ]
    return run_to_end(run, model_for(run)).trajectory


def steps_of(trajectory: PrivateTrajectory) -> list[tuple[int, ControlStep]]:
    found = [
        (boundary.offset_minutes, boundary.control_step)
        for boundary in trajectory.boundaries
        if boundary.control_step is not None
    ]
    assert found, "no control step was recorded, so every assertion is vacuous"
    return found


def energy(accepted: AcceptedFlowSet, flow_id: str) -> Fraction:
    return accepted.energy(flow_id)


def set_window(document, event_prefix: str, index: int, value) -> None:
    for entry in document["timeline"]:
        if entry["event_id"] == f"{event_prefix}-{index}":
            entry["parameters"][0]["value"] = value
            return
    raise KeyError(f"{event_prefix}-{index}")


@pytest.fixture(scope="module")
def sunny() -> PrivateTrajectory:
    return trajectory_of(kobo_draft("kobo-daytime"))


@pytest.fixture(scope="module")
def overcast() -> PrivateTrajectory:
    return trajectory_of(kobo_draft("kobo-daytime-overcast"))


@pytest.fixture(scope="module")
def larger_mill() -> PrivateTrajectory:
    return trajectory_of(kobo_draft("kobo-daytime-larger-mill"))


@pytest.fixture(scope="module")
def tight_pcs() -> PrivateTrajectory:
    """The third controlled variation: a 15 kW PCS on the sunny day."""

    def tighten(document):
        set_property(document, "battery-pcs", "pcs-charge-limit", 15)
        set_property(document, "battery-pcs", "pcs-discharge-limit", 15)

    return trajectory_of(kobo_draft("kobo-daytime", site_edit=tighten))


# --- The healthy interval and the three variations ---------------------------


class TestTheHealthyIntervalAndThreeVariations:
    """Proof: a healthy sunny interval and three controlled variations, each
    with exact balances and SOC bounds inspected over every accepted step."""

    @pytest.mark.parametrize(
        "name", ["sunny", "overcast", "larger_mill", "tight_pcs"]
    )
    def test_every_step_balances_exactly_and_soc_stays_in_bounds(
        self, name: str, request
    ) -> None:
        trajectory = request.getfixturevalue(name)
        assert trajectory.outcome == "COMPLETED", trajectory.failure
        for offset, step in steps_of(trajectory):
            accepted = step.accepted
            pv = energy(accepted, "pv_potential")
            assert pv == (
                energy(accepted, "pv_to_load")
                + energy(accepted, "pv_to_battery")
                + energy(accepted, "curtailed_pv")
                + energy(accepted, "inverter_clipping")
            ), offset
            demand = energy(accepted, "load_demand")
            assert demand == (
                energy(accepted, "pv_to_load")
                + energy(accepted, "battery_to_load")
                + energy(accepted, "unserved_load")
            ), offset
            for load in LOADS:
                service = accepted.load(f"load-demand@{load}")
                assert service.demand_energy == (
                    service.served_energy + service.unserved_energy
                )
                assert service.unserved_energy >= 0
            # Stored energy moves by exactly what was stored less what was
            # taken out, at 2 kWh per percent of a 200 kWh battery.
            account = accepted.stock_accounts[0]
            assert account.delta * 2 == energy(
                accepted, "battery_charge_stored"
            ) - energy(accepted, "battery_discharge_taken")
        socs = [
            boundary.stock(SOC) for boundary in trajectory.boundaries
        ]
        assert all(0 <= value <= 100 for value in socs)

    def test_the_healthy_interval_serves_every_load(self, sunny) -> None:
        unserved = sum(
            (energy(step.accepted, "unserved_load") for _, step in steps_of(sunny)),
            Fraction(0),
        )
        assert unserved == 0

    def test_lower_irradiance_reaches_the_reserve_and_leaves_load_unserved(
        self, sunny, overcast
    ) -> None:
        def unserved(trajectory):
            return sum(
                (
                    energy(step.accepted, "unserved_load")
                    for _, step in steps_of(trajectory)
                ),
                Fraction(0),
            )

        assert unserved(sunny) == 0
        assert unserved(overcast) > 0
        # Before the evening override the battery never goes below the 30 %
        # baseline reserve.
        before_override = [
            boundary.stock(SOC)
            for boundary in overcast.boundaries
            if boundary.offset_minutes <= 600
        ]
        assert min(before_override) == 30

    def test_a_larger_mill_leaves_sibling_demand_intact(
        self, sunny, larger_mill
    ) -> None:
        """Criterion 1: changing one profile leaves sibling demand intact."""
        for (_, base), (_, bigger) in zip(steps_of(sunny), steps_of(larger_mill)):
            for sibling in ("load-res", "load-clinic"):
                address = f"load-demand@{sibling}"
                assert (
                    base.accepted.load(address).demand_energy
                    == bigger.accepted.load(address).demand_energy
                )
        mill = "load-demand@load-mill"
        assert any(
            base.accepted.load(mill).demand_energy
            != bigger.accepted.load(mill).demand_energy
            for (_, base), (_, bigger) in zip(
                steps_of(sunny), steps_of(larger_mill)
            )
        )

    def test_a_tighter_pcs_limit_binds_and_is_named(
        self, sunny, tight_pcs
    ) -> None:
        for _, step in steps_of(tight_pcs):
            accepted = step.accepted.controls[0].accepted
            assert -15 <= accepted <= 15
        bound = [
            step
            for _, step in steps_of(tight_pcs)
            if any(
                "pcs-charge-limit 15 kW" in reason
                for reason in step.accepted.controls[0].limited_by
            )
        ]
        assert bound, "the tighter limit never bound, so this proves nothing"
        assert sunny.final.stock(SOC) != tight_pcs.final.stock(SOC)


# --- The proof table -----------------------------------------------------------


class TestTwoSameTypeLoadsWithDifferentProfiles:
    def test_three_loads_have_independent_addresses_demand_and_service(
        self, overcast
    ) -> None:
        offset, step = steps_of(overcast)[20]
        addresses = {item.address for item in step.accepted.loads}
        assert addresses == {f"load-demand@{load}" for load in LOADS}
        demands = {
            item.address: item.demand_power for item in step.accepted.loads
        }
        assert len(set(demands.values())) == 3, demands


class TestSurplusChargesThenCurtails:
    def test_surplus_charges_within_limits_then_curtails_once_full(
        self, sunny
    ) -> None:
        curtailing = [
            (offset, step)
            for offset, step in steps_of(sunny)
            if energy(step.accepted, "curtailed_pv") > 0
        ]
        assert curtailing, "no step curtailed, so this proves nothing"
        for offset, step in curtailing:
            boundary = sunny.boundary_at(offset)
            soc_end = boundary.stock(SOC) + step.accepted.stock_accounts[0].delta
            # Curtailment happens only when the battery took everything it
            # could: it finished the step full.
            assert soc_end == 100, offset
        charging = [
            step
            for _, step in steps_of(sunny)
            if energy(step.accepted, "pv_to_battery") > 0
        ]
        assert charging
        assert all(
            step.accepted.controls[0].accepted >= -30 for step in charging
        )


class TestDemandExceedsCapability:
    def test_a_shortage_serves_the_critical_priority_first(
        self, overcast
    ) -> None:
        short = [
            step
            for _, step in steps_of(overcast)
            if energy(step.accepted, "unserved_load") > 0
        ]
        assert short, "no step was short, so this proves nothing"
        for step in short:
            ranked = sorted(step.accepted.loads, key=lambda item: item.priority_rank)
            # Served in order: a load gets nothing unless every load above it
            # was served in full.
            seen_short = False
            for item in ranked:
                if seen_short:
                    assert item.served_energy == 0 or item.demand_energy == 0
                if item.unserved_energy > 0:
                    seen_short = True
        clinic = sum(
            (
                step.accepted.load("load-demand@load-clinic").unserved_energy
                for step in short
            ),
            Fraction(0),
        )
        mill = sum(
            (
                step.accepted.load("load-demand@load-mill").unserved_energy
                for step in short
            ),
            Fraction(0),
        )
        assert clinic == 0
        assert mill > 0

    def test_the_critical_priority_is_a_site_control_the_resolver_consumes(
        self,
    ) -> None:
        """Criterion 4: reverse the priority and the unserved load moves."""

        def mill_first(document):
            for control in document["foundation"]["site_controls"]:
                if control["control_key"] == "critical-load-priority":
                    control["members"] = ["load-mill", "load-res", "load-clinic"]
                    control["source"] = "SITE"

        run = kobo_draft("kobo-daytime-overcast", site_edit=mill_first)
        controls = {
            item.control_key: item.members
            for item in run.deterministic_identity.site_controls
        }
        assert controls["critical-load-priority"] == (
            "load-mill",
            "load-res",
            "load-clinic",
        )
        trajectory = trajectory_of(run)
        clinic = sum(
            (
                step.accepted.load("load-demand@load-clinic").unserved_energy
                for _, step in steps_of(trajectory)
            ),
            Fraction(0),
        )
        assert clinic > 0

    def test_the_source_priority_is_a_site_control_the_resolver_consumes(
        self, sunny
    ) -> None:
        def battery_first(document):
            for control in document["foundation"]["site_controls"]:
                if control["control_key"] == "source-priority":
                    control["members"] = ["battery", "pv-array", "generator"]
                    control["source"] = "SITE"

        trajectory = trajectory_of(kobo_draft(site_edit=battery_first))
        # 06:00-06:15 on the sunny day: 9 kW of PV against 13 kW of demand.
        # PV first serves 9 kW from PV and asks the battery for the 4 kW
        # deficit. Battery first asks the battery for the whole 13 kW, PV
        # serves nothing, and with the battery discharging the 9 kW of PV
        # cannot charge it, so all of it is curtailed.
        base = dict(steps_of(sunny))[0].accepted
        first = dict(steps_of(trajectory))[0].accepted
        assert energy(base, "pv_to_load") == Fraction(9, 4)
        assert energy(base, "battery_to_load") == 1
        assert energy(first, "battery_to_load") == Fraction(13, 4)
        assert energy(first, "pv_to_load") == 0
        assert energy(first, "curtailed_pv") == Fraction(9, 4)


class TestRequestedAgainstAccepted:
    def test_a_30_kw_request_through_a_22_kw_pcs_keeps_both_numbers(self) -> None:
        """Criterion 7 and v4 section 25.5."""

        def deficit_of_30(document):
            # 06:00-08:00: PV 150 W/m2 -> 9 kW. Demand 25 + 8 + 6 = 39 kW.
            set_window(document, "residential-demand", 1, 25)
            set_window(document, "clinic-demand", 1, 8)
            set_window(document, "mill-demand", 1, 6)

        def pcs_22(document):
            set_property(document, "battery-pcs", "pcs-discharge-limit", 22)

        trajectory = trajectory_of(
            kobo_draft(document_edit=deficit_of_30, site_edit=pcs_22)
        )
        _, step = steps_of(trajectory)[0]
        request = step.intent.request(SOC, "battery-power")
        accepted = step.accepted.control(SOC, "battery-power")
        assert request.requested == 30
        assert accepted.requested == 30
        assert accepted.accepted == 22
        assert "pcs-discharge-limit 22 kW" in accepted.limited_by
        # Only the accepted 22 kW moves the battery: 22 kW for a quarter hour
        # is 5.5 kWh AC, 5.5 / 0.95 = 110/19 kWh stored energy, and at 2 kWh
        # per percent the state of charge falls by 55/19 %.
        assert step.accepted.stock_accounts[0].delta == Fraction(-55, 19)
        assert energy(step.accepted, "unserved_load") == Fraction(8, 4)
        # And the later reading reports the accepted power, not the request.
        next_boundary = trajectory.boundaries[1]
        assert next_boundary.interval_measurement(
            "battery-ac-power@battery-pcs"
        ) == Fraction(22, 4)


class TestReportingDropoutChangesNoPhysics:
    def test_a_dropout_changes_the_reports_and_not_the_world_or_the_controller(
        self,
    ) -> None:
        run = kobo_draft("kobo-daytime-overcast")
        model = model_for(run)
        trajectory = run_to_end(run, model).trajectory
        lossy = replace(
            LAB_PUBLICATION_PROFILE,
            device_signals=tuple(
                replace(signal, dropout_per_thousand=1000)
                if signal.state_key == "battery-state-of-charge"
                else signal
                for signal in LAB_PUBLICATION_PROFILE.device_signals
            ),
        )
        clean = generate_observations(
            trajectory.boundaries, reporting_inputs(run, LAB_PUBLICATION_PROFILE)
        )
        dropped = generate_observations(
            trajectory.boundaries,
            reporting_inputs(
                run,
                replace(
                    lossy,
                    publication_profile_version=(
                        LAB_PUBLICATION_PROFILE.publication_profile_version
                    ),
                ),
            ),
        )
        soc_clean = [
            item.outcome for item in clean if item.signal_id == "state-of-charge"
        ]
        soc_dropped = [
            item.outcome for item in dropped if item.signal_id == "state-of-charge"
        ]
        assert set(soc_dropped) == {"DROPPED"}
        assert "REPORTED" in soc_clean
        # The world and every controller decision are one execution; the
        # reporting path is not an input to either.
        again = run_to_end(run, model).trajectory
        assert again.content_digest == trajectory.content_digest

    def test_the_controller_context_has_no_field_for_the_reporting_path(
        self,
    ) -> None:
        names = {field.name for field in fields(StepContext)}
        assert names == {
            "from_offset",
            "to_offset",
            "stocks",
            "coefficients",
            "exposures",
            "site_controls",
        }
        view_names = {field.name for field in fields(ControllerView)}
        assert view_names == {"at_offset_minutes", "for_until_offset", "entries"}


class TestMissingLawRequiredFoundationProperty:
    def test_an_undeclared_but_law_required_property_blocks_with_its_address(
        self,
    ) -> None:
        def no_limit(document):
            remove_property(document, "battery-pcs", "pcs-discharge-limit")

        run = kobo_draft(site_edit=no_limit)
        assert run.execution_status == "BLOCKED"
        reasons = {(item.kind, item.subject) for item in run.blocking_reasons}
        assert reasons == {
            ("INITIAL_VALUE_NOT_RESOLVED", "pcs-discharge-limit@battery-pcs")
        }
        # The scenario declares no such value and was not asked to: the need
        # is the model's, frozen absent with who declared it.
        need = next(
            item
            for item in run.deterministic_identity.model_needs
            if item.addressed_key == "pcs-discharge-limit@battery-pcs"
        )
        assert need.value is None
        assert need.declared_by == "model profile daytime-mini-grid version 1"
        document = kobo_document()
        assert "pcs-discharge-limit" not in str(document)

    def test_a_missing_site_control_blocks_by_name(self) -> None:
        def no_controls(document):
            document["foundation"]["site_controls"] = None

        run = kobo_draft(site_edit=no_controls)
        reasons = {(item.kind, item.subject) for item in run.blocking_reasons}
        assert reasons == {
            ("SITE_CONTROL_NOT_RESOLVED", "site-control:source-priority"),
            ("SITE_CONTROL_NOT_RESOLVED", "site-control:critical-load-priority"),
        }

    def test_two_same_type_components_resolve_independently(self) -> None:
        def second_battery(document):
            foundation = document["foundation"]
            battery = copy.deepcopy(component(document, "battery"))
            battery["component_id"] = "battery-2"
            battery["display_name"] = "Second battery"
            for item in battery["properties"]:
                if item["property_key"] == "battery-energy-capacity":
                    item["value"] = 150
            foundation["components"].append(battery)
            for control in foundation["site_controls"]:
                if control["control_key"] == "source-priority":
                    control["members"] = [
                        "pv-array",
                        "battery",
                        "battery-2",
                        "generator",
                    ]

        run = kobo_draft(site_edit=second_battery)
        capacities = {
            item.addressed_key: item.value
            for item in run.deterministic_identity.model_needs
            if item.state_key == "battery-energy-capacity"
        }
        assert capacities == {
            "battery-energy-capacity@battery": 200.0,
            "battery-energy-capacity@battery-2": 150.0,
        }
        # The second battery has no state of charge stated, so it blocks by
        # its own address and the first battery's row is unaffected.
        reasons = {(item.kind, item.subject) for item in run.blocking_reasons}
        assert (
            "INITIAL_VALUE_NOT_RESOLVED",
            "battery-state-of-charge@battery-2",
        ) in reasons

    def test_a_frozen_run_executes_its_frozen_answer_not_the_live_site(
        self,
    ) -> None:
        """Execution reads only the frozen run. Changing the frozen answer
        changes the trajectory; nothing else is consulted."""
        run = kobo_draft("kobo-daytime-overcast")
        base = trajectory_of(run)
        identity = run.deterministic_identity
        edited = replace(
            run,
            deterministic_identity=replace(
                identity,
                model_needs=tuple(
                    replace(item, value=20.0, canonical_value=20.0)
                    if item.state_key == "pcs-discharge-limit"
                    else item
                    for item in identity.model_needs
                ),
            ),
        )
        assert trajectory_of(edited).content_digest != base.content_digest
        assert frozen_world_inputs.__code__.co_argcount == 1


class TestRunStartSocAbsent:
    def test_an_absent_run_start_soc_blocks_and_is_never_inferred(self) -> None:
        def drop(document):
            document["public_parameters"] = [
                item
                for item in document["public_parameters"]
                if item["parameter_id"] != "starting-state-of-charge"
            ]

        run = kobo_draft(document_edit=drop)
        assert run.execution_status == "BLOCKED"
        assert {(item.kind, item.subject) for item in run.blocking_reasons} == {
            ("INITIAL_VALUE_NOT_RESOLVED", SOC)
        }


# --- Criterion 5: a temporary reserve override over the frozen baseline ------


class TestTheReserveOverride:
    def test_the_override_replaces_the_baseline_inside_its_window_and_reverts(
        self, overcast
    ) -> None:
        origins = {}
        for offset, step in steps_of(overcast):
            for item in step.accepted.effective_controls:
                origins[item.from_offset] = (item.origin, item.value)
        assert origins[585] == ("BASELINE", 30)
        assert origins[600] == ("OVERRIDE", 15)
        assert origins[705] == ("OVERRIDE", 15)
        assert all(
            origin == ("BASELINE", 30)
            for offset, origin in origins.items()
            if offset < 600
        )

    def test_the_baseline_applies_again_at_the_end_of_the_window(self) -> None:
        """The window ends before the interval does, and the baseline is back."""

        def shorter(document):
            for entry in document["timeline"]:
                if entry["event_id"] == "evening-reserve-override":
                    entry["timing"]["duration_minutes"] = 60

        trajectory = trajectory_of(
            kobo_draft("kobo-daytime-overcast", document_edit=shorter)
        )
        origins = {
            item.from_offset: (item.origin, item.value)
            for _, step in steps_of(trajectory)
            for item in step.accepted.effective_controls
        }
        assert origins[645] == ("OVERRIDE", 15)
        assert origins[660] == ("BASELINE", 30)

    def test_the_override_changes_service_with_unchanged_initial_conditions(
        self, overcast
    ) -> None:
        def no_override(document):
            document["timeline"] = [
                entry
                for entry in document["timeline"]
                if entry["event_id"] != "evening-reserve-override"
            ]

        without = trajectory_of(
            kobo_draft("kobo-daytime-overcast", document_edit=no_override)
        )

        def evening_served(trajectory):
            return sum(
                (
                    energy(step.accepted, "battery_to_load")
                    for offset, step in steps_of(trajectory)
                    if offset >= 600
                ),
                Fraction(0),
            )

        assert overcast.boundaries[0].stock(SOC) == without.boundaries[0].stock(SOC)
        assert evening_served(overcast) > evening_served(without) == 0

    def test_a_change_inside_a_step_splits_its_evaluation(self) -> None:
        def off_grid(document):
            for entry in document["timeline"]:
                if entry["event_id"] == "evening-reserve-override":
                    entry["offset_minutes"] = 607
                    entry["timing"]["duration_minutes"] = 90

        trajectory = trajectory_of(
            kobo_draft("kobo-daytime-overcast", document_edit=off_grid)
        )
        step = dict(steps_of(trajectory))[600]
        assert step.accepted.segments == ((600, 607), (607, 615))
        reserve = [
            (item.from_offset, item.to_offset, item.origin, item.value)
            for item in step.accepted.effective_controls
        ]
        assert reserve == [
            (600, 607, "BASELINE", 30),
            (607, 615, "OVERRIDE", 15),
        ]

    def test_genuinely_overlapping_overrides_are_refused(self) -> None:
        def overlap(document):
            override = next(
                entry
                for entry in document["timeline"]
                if entry["event_id"] == "evening-reserve-override"
            )
            second = copy.deepcopy(override)
            second["event_id"] = "second-override"
            second["sequence"] = override["sequence"] + 1
            second["offset_minutes"] = 630
            second["timing"]["duration_minutes"] = 60
            second["parameters"][0]["parameter_id"] = "second-override-level"
            second["parameters"][0]["value"] = 20
            document["timeline"].append(second)

        trajectory = trajectory_of(
            kobo_draft("kobo-daytime-overcast", document_edit=overlap)
        )
        assert trajectory.outcome == "FAILED"
        assert trajectory.failure.kind == "FORCING_VALUE_AMBIGUOUS"
        assert trajectory.failure.subject == "battery-reserve-state-of-charge@battery"

    def test_adjacent_overrides_are_valid_even_inside_one_step(self) -> None:
        def adjacent(document):
            override = next(
                entry
                for entry in document["timeline"]
                if entry["event_id"] == "evening-reserve-override"
            )
            override["timing"]["duration_minutes"] = 7
            second = copy.deepcopy(override)
            second["event_id"] = "second-override"
            second["sequence"] = override["sequence"] + 1
            second["offset_minutes"] = 607
            second["timing"]["duration_minutes"] = 113
            second["parameters"][0]["parameter_id"] = "second-override-level"
            second["parameters"][0]["value"] = 20
            document["timeline"].append(second)

        trajectory = trajectory_of(
            kobo_draft("kobo-daytime-overcast", document_edit=adjacent)
        )
        assert trajectory.outcome == "COMPLETED", trajectory.failure
        step = dict(steps_of(trajectory))[600]
        assert [
            (item.from_offset, item.to_offset, item.value)
            for item in step.accepted.effective_controls
        ] == [(600, 607, 15), (607, 615, 20)]

    def test_a_reserve_above_the_current_soc_creates_no_energy(self) -> None:
        def morning_hold(document):
            override = next(
                entry
                for entry in document["timeline"]
                if entry["event_id"] == "evening-reserve-override"
            )
            override["offset_minutes"] = 0
            override["parameters"][0]["value"] = 90

        trajectory = trajectory_of(
            kobo_draft("kobo-daytime-overcast", document_edit=morning_hold)
        )
        first = steps_of(trajectory)[:8]
        for offset, step in first:
            assert energy(step.accepted, "battery_discharge_taken") == 0
            assert energy(step.accepted, "battery_charge_stored") == 0
            assert energy(step.accepted, "unserved_load") > 0
        assert trajectory.boundary_at(120).stock(SOC) == 55


# --- Criterion 10: boundary samples and batching --------------------------------


class TestBoundarySamplesAndBatching:
    def test_soc_is_the_state_at_t_and_power_describes_the_preceding_step(
        self, sunny
    ) -> None:
        boundaries = sunny.boundaries
        for previous, current in zip(boundaries, boundaries[1:]):
            step = previous.control_step
            assert current.state_sample(SOC) == current.stock(SOC)
            assert current.stock(SOC) == (
                previous.stock(SOC) + step.accepted.stock_accounts[0].delta
            )
            assert current.interval_measurement(
                "battery-ac-power@battery-pcs"
            ) == energy(step.accepted, "battery_to_load") - energy(
                step.accepted, "pv_to_battery"
            )
        assert boundaries[0].interval_measurements == ()

    def test_changing_step_batching_leaves_the_trajectory_unchanged(
        self,
    ) -> None:
        run = kobo_draft("kobo-daytime-overcast")
        inputs = frozen_world_inputs(run)
        digests = set()
        for batch in (1, 3, 7, 48):
            execution = Execution(inputs, DAYTIME_MINI_GRID_MODEL)
            while not execution.is_terminal:
                execution.advance(batch)
            digests.add(execution.trajectory().content_digest)
        digests.add(execute(inputs, DAYTIME_MINI_GRID_MODEL).content_digest)
        assert len(digests) == 1


# --- Criterion 12: electrical device observations ------------------------------


class TestElectricalDeviceObservations:
    def test_the_electrical_signals_generate_readings_separate_from_flows(
        self,
    ) -> None:
        run = kobo_draft("kobo-daytime")
        trajectory = run_to_end(run, model_for(run)).trajectory
        reporting = reporting_inputs(run)
        paths = {
            (item.device_id, item.signal_id, item.address)
            for item in reporting.signals
        }
        assert paths == {
            ("battery-pcs-controller", "state-of-charge", SOC),
            ("battery-pcs-controller", "ac-power", "battery-ac-power@battery-pcs"),
            ("pv-inverter-controller", "ac-power", "pv-ac-power@pv-inverter"),
            ("residential-meter", "active-power", "load-served-power@load-res"),
            ("clinic-meter", "active-power", "load-served-power@load-clinic"),
            ("mill-meter", "active-power", "load-served-power@load-mill"),
        }
        observations = generate_observations(trajectory.boundaries, reporting)
        reported = [item for item in observations if item.outcome == "REPORTED"]
        assert {item.signal_id for item in reported} == {
            "state-of-charge",
            "ac-power",
            "active-power",
        }
        # A reading carries no accepted-flow object and no true value.
        names = {field.name for field in fields(DeviceObservation)}
        assert not names & {"accepted", "flows", "control_step", "true_value"}
        # The PCS reading one step in is the accepted mean power, signed.
        pcs = next(
            item
            for item in reported
            if item.signal_id == "ac-power"
            and item.device_id == "battery-pcs-controller"
            and item.at_offset_minutes == 15
        )
        assert pcs.reported_value == 4

    def test_a_fuel_run_grows_no_electrical_column(self) -> None:
        from fixtures import draft

        run = draft()
        reporting = reporting_inputs(run)
        assert {item.device_id for item in reporting.signals} == {
            "fuel-level-sensor",
            "generator-controller",
        }


# --- Criterion 8: a failure is typed ---------------------------------------------


class TestAnInvariantFailureIsTyped:
    def test_a_resolver_that_creates_energy_fails_as_a_balance_violation(
        self,
    ) -> None:
        from assetops_contracts.control import AcceptedFlow

        coupling = DAYTIME_MINI_GRID_MODEL.coupling

        def leaky(context, intent):
            accepted = coupling.resolve(context, intent)
            flows = tuple(
                AcceptedFlow(
                    item.flow_id,
                    item.from_address,
                    item.to_address,
                    item.energy + Fraction(1, 1000),
                    item.mean_power,
                )
                if item.flow_id == "pv_to_load"
                else item
                for item in accepted.flows
            )
            return replace(accepted, flows=flows)

        model = replace(
            DAYTIME_MINI_GRID_MODEL, coupling=replace(coupling, resolve=leaky)
        )
        trajectory = execute(frozen_world_inputs(kobo_draft()), model)
        assert trajectory.outcome == "FAILED"
        assert trajectory.failure.kind == "BALANCE_IDENTITY_VIOLATION"
        assert trajectory.failure.at_offset_minutes == 0


# --- Independent energy arithmetic ------------------------------------------------


class TestIndependentEnergyArithmetic:
    """Worked on paper from the template: 60 kWp array, 50 kW inverter,
    200 kWh battery (2 kWh per %), 95 % one-way efficiency, start at 55 %."""

    def test_one_discharge_interval(self, sunny) -> None:
        # 06:00-06:15: 150 W/m2 -> 9 kW of PV. Demand 8 + 5 + 0 = 13 kW. The
        # battery supplies the 4 kW deficit: 1 kWh AC over the quarter hour,
        # taking 1 / 0.95 = 20/19 kWh out of storage and losing 1/19 kWh. The
        # state of charge falls by (20/19) / 2 = 10/19 %.
        step = dict(steps_of(sunny))[0]
        accepted = step.accepted
        assert energy(accepted, "pv_potential") == Fraction(9, 4)
        assert energy(accepted, "pv_to_load") == Fraction(9, 4)
        assert energy(accepted, "battery_to_load") == 1
        assert energy(accepted, "battery_discharge_taken") == Fraction(20, 19)
        assert energy(accepted, "discharge_loss") == Fraction(1, 19)
        assert sunny.boundary_at(15).stock(SOC) == 55 - Fraction(10, 19)

    def test_one_charge_interval(self, sunny) -> None:
        # 08:00-08:15: 550 W/m2 -> 33 kW. Demand 6 + 6 + 15 = 27 kW. The 6 kW
        # surplus charges: 1.5 kWh AC, 1.425 kWh stored, 0.075 kWh lost, and
        # the state of charge rises by 1.425 / 2 = 0.7125 %.
        step = dict(steps_of(sunny))[120]
        accepted = step.accepted
        assert energy(accepted, "pv_to_battery") == Fraction(3, 2)
        assert energy(accepted, "battery_charge_stored") == Fraction(57, 40)
        assert energy(accepted, "charge_loss") == Fraction(3, 40)
        assert accepted.stock_accounts[0].delta == Fraction(57, 80)

    def test_inverter_clipping_at_noon(self, sunny) -> None:
        # 12:00-12:15: 950 W/m2 -> 57 kW offered, 50 kW passed, 7 kW clipped.
        step = dict(steps_of(sunny))[360]
        assert step.accepted.flow("pv_potential").mean_power == 57
        assert step.accepted.flow("inverter_clipping").mean_power == 7
