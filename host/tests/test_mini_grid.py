"""T025a: the `mini-grid` v1 model, a healthy full site with a generator.

Every expected number below is computed independently of the resolver: from
the flows the kernel accepted and the Foundation's own coefficient, in exact
rational arithmetic, never by re-reading the resolver's totals.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest
import yaml

from assetops_backend.runs.profiles import MINI_GRID_MODEL as MINI_GRID_PROFILE
from assetops_backend.simulator_lab_api import electrical_payload
from assetops_contracts.control import DISCRETE_UNIT
from assetops_contracts.trajectory import PrivateTrajectory
from assetops_simulator.kernel.execute import execute
from assetops_simulator.packs.mini_grid import (
    GENERATOR_LIFECYCLE,
    MINI_GRID_MODEL,
    TransitionRequest,
)

from execution_adapter import frozen_world_inputs, model_for, run_to_end
from kobo import component, kobo_draft, set_property
from lab_execution import (
    EXECUTION_ARTIFACT_SCHEMA_VERSION,
    HostLabExecution,
    YamlExecutionArtifacts,
)
from source_stages import JsonSourceStages

START = "2026-09-22T09:00:00Z"  # 12:00 in Africa/Addis_Ababa
END = "2026-09-22T17:00:00Z"
GEN = "generator-state@generator"
SOC = "battery-state-of-charge@battery"
FUEL = "fuel-tank-volume@fuel-tank"
SFC = Fraction(3, 10)
RATED = Fraction(40)


def mini_draft(*, document_edit=None, site_edit=None, timestep_minutes=5):
    return kobo_draft(
        "kobo-mini-grid-evening",
        document_edit=document_edit,
        site_edit=site_edit,
        timestep_minutes=timestep_minutes,
        model_profile="mini-grid",
        start_time=START,
        end_time=END,
    )


def trajectory_of(run) -> PrivateTrajectory:
    assert run.execution_status == "READY", [
        (reason.kind, reason.subject) for reason in run.blocking_reasons
    ]
    return run_to_end(run, model_for(run)).trajectory


def steps_of(trajectory):
    found = [b for b in trajectory.boundaries if b.control_step is not None]
    assert found, "no control step was recorded, so every assertion is vacuous"
    return found


def flows(boundary) -> dict[str, Fraction]:
    return {item.flow_id: item.energy for item in boundary.control_step.accepted.flows}


def control(boundary, quantity: str):
    return next(
        item
        for item in boundary.control_step.accepted.controls
        if item.quantity == quantity
    )


def request(boundary, quantity: str):
    return next(
        item
        for item in boundary.control_step.intent.requests
        if item.quantity == quantity
    )


def set_parameter(value, unit=None, parameter_id="starting-generator-state"):
    def edit(document):
        for item in document["public_parameters"]:
            if item["parameter_id"] == parameter_id:
                item["value"] = value
                if unit is not None:
                    item["unit"] = unit
                return
        raise KeyError(parameter_id)

    return edit


def blocking(run) -> set[tuple[str, str]]:
    return {(reason.kind, reason.subject) for reason in run.blocking_reasons}


@pytest.fixture(scope="module")
def healthy() -> PrivateTrajectory:
    return trajectory_of(mini_draft())


class TestTheHealthySunnyToLowPvRun:
    def test_it_completes_with_every_load_served(self, healthy) -> None:
        assert healthy.outcome == "COMPLETED"
        unserved = sum((flows(b)["unserved_load"] for b in steps_of(healthy)), Fraction(0))
        assert unserved == 0
        served_by_generator = sum(
            (flows(b)["generator_to_load"] for b in steps_of(healthy)), Fraction(0)
        )
        assert served_by_generator > 0, "the generator must carry part of the evening"

    def test_sources_hand_over_from_pv_to_battery_to_generator(self, healthy) -> None:
        first_pv = next(b for b in steps_of(healthy) if flows(b)["pv_to_load"] > 0)
        first_battery = next(b for b in steps_of(healthy) if flows(b)["battery_to_load"] > 0)
        first_generator = next(
            b for b in steps_of(healthy) if flows(b)["generator_to_load"] > 0
        )
        assert (
            first_pv.offset_minutes
            < first_battery.offset_minutes
            < first_generator.offset_minutes
        )

    def test_per_load_service_is_inspectable(self, healthy) -> None:
        loads = steps_of(healthy)[-1].control_step.accepted.loads
        assert {item.address for item in loads} == {
            "load-demand@load-clinic",
            "load-demand@load-res",
            "load-demand@load-mill",
        }
        assert all(item.unserved_energy == 0 for item in loads)


class TestTheSitePolicyAloneStartsTheGenerator:
    def test_the_start_request_happens_only_at_or_below_the_start_threshold(
        self, healthy
    ) -> None:
        starts = [
            b
            for b in steps_of(healthy)
            if b.discrete_state(GEN) == "STOPPED"
            and request(b, "generator-run").requested == "RUN"
        ]
        assert starts, "no start request, so the policy was never exercised"
        assert all(b.stock(SOC) <= 35 for b in starts)
        stopped_above = [
            b
            for b in steps_of(healthy)
            if b.discrete_state(GEN) == "STOPPED" and b.stock(SOC) > 35
        ]
        assert stopped_above
        assert all(request(b, "generator-run").requested == "STOP" for b in stopped_above)

    def test_the_request_is_visible_before_running_and_output(self, healthy) -> None:
        first, second = healthy.discrete_transitions[:2]
        assert (first.previous, first.next, first.phase) == (
            "STOPPED",
            "STARTING",
            "physical-acceptance",
        )
        assert first.controller_ref == f"control-intent@{first.at_offset_minutes}:generator-run"
        assert (second.previous, second.next, second.phase) == (
            "STARTING",
            "RUNNING",
            "apply-events",
        )
        assert second.controller_ref is None
        assert second.at_offset_minutes - first.at_offset_minutes == 5
        at_request = healthy.boundary_at(first.at_offset_minutes)
        # The snapshot at T is the state a sample at T saw; the step's state
        # is what the request just caused. Three records, three answers.
        assert at_request.discrete_state(GEN) == "STOPPED"
        assert at_request.discrete_state_for_step(GEN) == "STARTING"
        assert request(at_request, "generator-run").requested == "RUN"
        assert control(at_request, "generator-run").accepted == "STARTING"
        assert flows(at_request)["generator_output"] == 0
        running = healthy.boundary_at(second.at_offset_minutes)
        assert running.discrete_state(GEN) == "RUNNING"

    def test_typed_values_are_never_numbers(self, healthy) -> None:
        boundary = steps_of(healthy)[-1]
        entry = next(
            item for item in boundary.control_step.view.entries if item.name == "generator-state"
        )
        assert entry.unit == DISCRETE_UNIT and isinstance(entry.value, str)
        assert isinstance(control(boundary, "generator-run").accepted, str)


class TestEnergyAndFuelBalanceExactly:
    def test_every_step_balances_independently(self, healthy) -> None:
        for b in steps_of(healthy):
            f = flows(b)
            assert f["generator_output"] == f["generator_to_load"] + f["generator_to_battery"]
            assert f["load_demand"] == (
                f["pv_to_load"] + f["battery_to_load"] + f["generator_to_load"] + f["unserved_load"]
            )
            assert f["pv_to_battery"] + f["generator_to_battery"] == (
                f["battery_charge_stored"] + f["charge_loss"]
            )
            # No simultaneous charge and discharge.
            assert f["battery_to_load"] == 0 or (
                f["pv_to_battery"] + f["generator_to_battery"] == 0
            )
            hours = Fraction(b.control_step.accepted.to_offset - b.offset_minutes, 60)
            assert f["generator_output"] <= RATED * hours

    def test_fuel_follows_accepted_generator_energy_at_the_foundation_coefficient(
        self, healthy
    ) -> None:
        energy = sum((flows(b)["generator_output"] for b in steps_of(healthy)), Fraction(0))
        assert energy > 0
        assert healthy.boundaries[0].stock(FUEL) - healthy.final.stock(FUEL) == energy * SFC
        for b in steps_of(healthy):
            account = next(
                item for item in b.control_step.accepted.stock_accounts if item.address == FUEL
            )
            assert account.delta == -flows(b)["generator_output"] * SFC

    def test_generator_charging_goes_to_the_battery_only_within_headroom(
        self, healthy
    ) -> None:
        charging = [b for b in steps_of(healthy) if flows(b)["generator_to_battery"] > 0]
        assert charging, "the generator never charged the battery; the case is vacuous"
        limit = next(
            Fraction(item.value)
            for item in mini_draft().deterministic_identity.model_needs
            if item.state_key == "pcs-charge-limit"
        )
        hours = Fraction(5, 60)
        at_rating = 0
        for b in charging:
            taken = flows(b)["pv_to_battery"] + flows(b)["generator_to_battery"]
            assert taken <= limit * hours
            at_rating += flows(b)["generator_output"] == RATED * hours
        # Here the rating binds (40 kW less load is below the 30 kW PCS).
        assert at_rating, "the rating never bound, so the ceiling is untested"

    def test_the_pcs_limit_bounds_generator_charging_when_it_is_lower(self) -> None:
        def site(document):
            set_property(document, "battery-pcs", "pcs-charge-limit", 10)

        trajectory = trajectory_of(mini_draft(site_edit=site))
        hours = Fraction(5, 60)
        charging = [b for b in steps_of(trajectory) if flows(b)["generator_to_battery"] > 0]
        assert charging
        assert all(
            flows(b)["pv_to_battery"] + flows(b)["generator_to_battery"] <= 10 * hours
            for b in charging
        )
        assert any(flows(b)["generator_to_battery"] == 10 * hours for b in charging)
        assert any(
            "pcs-charge-limit 10 kW" in control(b, "battery-power").limited_by
            for b in charging
        )

    def test_the_linear_fuel_law_is_disclosed(self, healthy) -> None:
        assert any(
            "no idle or start fuel" in note
            for note in steps_of(healthy)[0].control_step.accepted.notes
        )


class TestTheFuelBound:
    def test_accepted_energy_stops_exactly_at_an_empty_tank(self) -> None:
        trajectory = trajectory_of(
            mini_draft(document_edit=set_parameter(2, parameter_id="starting-fuel"))
        )
        assert trajectory.outcome == "COMPLETED"
        energy = sum(
            (flows(b)["generator_output"] for b in steps_of(trajectory)), Fraction(0)
        )
        assert energy * SFC == 2
        assert trajectory.final.stock(FUEL) == 0
        assert any(
            "fuel in tank" in reason
            for b in steps_of(trajectory)
            for reason in control(b, "generator-run").limited_by
        )


class TestMinimumRuntimeHoldsAgainstTheStopThreshold:
    @pytest.fixture(scope="class")
    def early_start(self) -> PrivateTrajectory:
        """The generator starts at midday with PV surplus charging the battery,
        so the state of charge crosses a low stop threshold long before the
        30-minute minimum runtime has elapsed."""

        def site(document):
            set_property(document, "generator", "stop-soc-threshold", 36)

        return trajectory_of(
            mini_draft(
                document_edit=set_parameter(34, parameter_id="starting-state-of-charge"),
                site_edit=site,
            )
        )

    def test_running_persists_until_the_site_policy_permits_a_stop(
        self, early_start
    ) -> None:
        transitions = early_start.discrete_transitions
        running = next(t for t in transitions if t.next == "RUNNING")
        stopped = next(t for t in transitions if t.previous == "RUNNING")
        held = [
            b
            for b in steps_of(early_start)
            if running.at_offset_minutes <= b.offset_minutes < stopped.at_offset_minutes
            and b.stock(SOC) >= 36
        ]
        assert held, "the stop threshold was never reached before the minimum runtime"
        assert all(request(b, "generator-run").requested == "RUN" for b in held)
        assert any("below the minimum runtime" in request(b, "generator-run").reason for b in held)
        # Counted from actual RUNNING, not from the start request.
        assert stopped.at_offset_minutes - running.at_offset_minutes == 30
        assert stopped.phase == "physical-acceptance"
        assert early_start.boundary_at(stopped.at_offset_minutes).stock(SOC) >= 36


class TestFailedAndUnsupportedInitialization:
    def test_an_initial_failed_generator_is_inert_and_not_an_execution_failure(
        self,
    ) -> None:
        trajectory = trajectory_of(mini_draft(document_edit=set_parameter("FAILED")))
        assert trajectory.outcome == "COMPLETED"
        assert trajectory.discrete_transitions == ()
        assert all(flows(b)["generator_output"] == 0 for b in steps_of(trajectory))
        asked = [
            b for b in steps_of(trajectory) if request(b, "generator-run").requested == "RUN"
        ]
        assert asked, "the policy never asked, so inertness was never tested"
        assert all(control(b, "generator-run").accepted == "FAILED" for b in asked)

    @pytest.mark.parametrize("value", ["RUNNING", "STARTING"])
    def test_a_start_needing_timer_history_blocks(self, value) -> None:
        run = mini_draft(document_edit=set_parameter(value))
        assert ("INITIAL_VALUE_NOT_RESOLVED", GEN) in blocking(run)
        assert "timer history" in " ".join(r.statement for r in run.blocking_reasons)

    def test_a_number_standing_in_for_a_state_blocks(self) -> None:
        run = mini_draft(document_edit=set_parameter(1, unit="%"))
        assert ("INITIAL_VALUE_NOT_RESOLVED", GEN) in blocking(run)

    def test_an_authored_failure_cause_is_refused_until_t035(self) -> None:
        def cause(document):
            document["timeline"].append(
                {
                    "event_id": "generator-start-failure",
                    "sequence": 99,
                    "offset_minutes": 60,
                    "entry_kind": "EVENT",
                    "category": "EQUIPMENT",
                    "description": "The generator fails to start.",
                    "execution_role": "FORCING_INPUT",
                    "state_key": GEN,
                    "execution_requirement": "REQUIRED",
                    "timing": {"shape": "WINDOW", "duration_minutes": 30},
                    "parameters": [
                        {
                            "parameter_id": "start-failure-level",
                            "display_name": "Start failure",
                            "value": 1,
                            "unit": "%",
                            "execution_role": "FORCING_INPUT",
                            "state_key": GEN,
                            "execution_requirement": "REQUIRED",
                            "ownership": {"owner": "SCENARIO_INPUT", "initializes": False},
                        }
                    ],
                }
            )

        run = mini_draft(document_edit=cause)
        assert run.execution_status == "BLOCKED"
        assert ("STATE_NOT_SUPPORTED", GEN) in blocking(run)
        assert "T035" in " ".join(r.statement for r in run.blocking_reasons)


class TestLifecycleTimingIsStepAligned:
    def test_a_start_delay_the_step_cannot_express_blocks(self) -> None:
        run = mini_draft(timestep_minutes=15)
        assert ("LIFECYCLE_TIMING_NOT_ALIGNED", "generator-start-delay@generator") in blocking(run)
        assert not any(
            subject == "generator-minimum-runtime@generator"
            for _, subject in blocking(run)
        )

    def test_a_minimum_runtime_off_the_step_blocks(self) -> None:
        def site(document):
            set_property(document, "generator", "minimum-runtime", 32)

        run = mini_draft(site_edit=site)
        assert (
            "LIFECYCLE_TIMING_NOT_ALIGNED",
            "generator-minimum-runtime@generator",
        ) in blocking(run)

    def test_the_site_policy_and_physical_needs_freeze_with_provenance(self) -> None:
        run = mini_draft()
        needs = {item.addressed_key: item for item in run.deterministic_identity.model_needs}
        for key, value, unit in (
            ("generator-start-soc-threshold@generator", 35, "%"),
            ("generator-stop-soc-threshold@generator", 90, "%"),
            ("generator-minimum-runtime@generator", 30, "min"),
            ("generator-start-delay@generator", 5, "min"),
            ("generator-rated-power@generator", 40, "kW"),
            ("generator-specific-fuel-consumption@generator", 0.3, "L/kWh"),
            ("fuel-tank-capacity@fuel-tank", 400, "L"),
        ):
            assert needs[key].value == value and needs[key].unit == unit
            assert needs[key].answered_by == "SITE_FOUNDATION"
            assert needs[key].declared_by == "model profile mini-grid version 1"
        attachments = {
            (item.role, item.component_id, item.via_component_id)
            for item in run.deterministic_identity.bus_attachments
        }
        assert ("GENERATION", "generator", None) in attachments
        assert ("FUEL_SUPPLY", "fuel-tank", "generator") in attachments

    def test_a_generator_the_topology_does_not_connect_blocks(self) -> None:
        def unplug(document):
            topology = document["foundation"]["topology"]
            topology["connections"] = [
                item
                for item in topology["connections"]
                if item["connection_id"] != "generator-to-bus"
            ]

        run = mini_draft(site_edit=unplug)
        assert ("ELECTRICAL_TOPOLOGY_NOT_CONNECTED", "generator") in blocking(run)


class TestADelayEndingAtTheRunEndIsApplied:
    """A due lifecycle transition is applied at the terminal boundary too."""

    CUT = 200  # 195 STARTING plus the 5-minute delay: exactly the run end

    def _short(self) -> PrivateTrajectory:
        cut = self.CUT

        def trim(document):
            kept = []
            for entry in document["timeline"]:
                if entry["offset_minutes"] >= cut:
                    continue
                timing = entry["timing"]
                if "duration_minutes" in timing:
                    timing["duration_minutes"] = min(
                        timing["duration_minutes"], cut - entry["offset_minutes"]
                    )
                kept.append(entry)
            document["timeline"] = kept

        return trajectory_of(
            kobo_draft(
                "kobo-mini-grid-evening",
                document_edit=trim,
                timestep_minutes=5,
                model_profile="mini-grid",
                start_time=START,
                end_time="2026-09-22T12:20:00Z",
            )
        )

    def test_the_final_snapshot_and_the_persisted_transition_show_running(
        self, healthy
    ) -> None:
        # The reference run makes the same transition at the same instant.
        assert any(
            t.at_offset_minutes == self.CUT
            and (t.previous, t.next) == ("STARTING", "RUNNING")
            for t in healthy.discrete_transitions
        )
        short = self._short()
        assert short.outcome == "COMPLETED"
        final = short.boundaries[-1]
        assert final.offset_minutes == self.CUT
        assert final.discrete_state(GEN) == "RUNNING"
        landed = [
            t
            for t in short.discrete_transitions
            if t.at_offset_minutes == self.CUT
        ]
        assert [(t.previous, t.next, t.controller_ref) for t in landed] == [
            ("STARTING", "RUNNING", None)
        ]
        assert final.control_step is None, "no new intent at the terminal boundary"


class TestTheKernelOwnsTransitions:
    def test_an_undeclared_edge_fails_the_run_typed(self) -> None:
        run = mini_draft()
        inputs = frozen_world_inputs(run)

        def jump(context, intent):
            return (TransitionRequest(GEN, "RUNNING", "a pack skipping STARTING"),)

        model = replace(
            MINI_GRID_MODEL, coupling=replace(MINI_GRID_MODEL.coupling, commit=jump)
        )
        trajectory = execute(inputs, model)
        assert trajectory.outcome == "FAILED"
        assert trajectory.failure.kind == "PHYSICAL_RESOLUTION_FAILURE"
        assert trajectory.failure.subject == GEN

    def test_the_profile_and_the_model_declare_one_lifecycle(self) -> None:
        declared = MINI_GRID_PROFILE.discrete_states[0]
        assert declared.state_key == GENERATOR_LIFECYCLE.state_key
        assert declared.allowed_values == GENERATOR_LIFECYCLE.allowed_values
        assert declared.initial_values_supported == GENERATOR_LIFECYCLE.initial_values_supported
        advertised = {
            (item.state_key, role)
            for item in MINI_GRID_MODEL.advertised_supported_states()
            for role in item.supported_roles
        }
        profile = {
            (item.state_key, role)
            for item in MINI_GRID_PROFILE.supported_states
            for role in item.supported_roles
        }
        assert advertised == profile


class TestReproductionAndReadback:
    def test_the_same_frozen_run_reproduces_its_trajectory(self) -> None:
        run = mini_draft()
        first = trajectory_of(run)
        second = trajectory_of(run)
        assert first.inputs_identity == second.inputs_identity
        assert first.content_digest == second.content_digest
        again = trajectory_of(mini_draft())
        assert again.inputs_identity == first.inputs_identity

    def test_the_lifecycle_state_is_part_of_the_identity(self) -> None:
        stopped = trajectory_of(mini_draft())
        failed = trajectory_of(mini_draft(document_edit=set_parameter("FAILED")))
        assert stopped.inputs_identity != failed.inputs_identity

    def test_the_lab_persists_and_reads_back_state_and_transitions(
        self, tmp_path: Path
    ) -> None:
        run = mini_draft()

        def lab():
            return HostLabExecution(
                artifacts=YamlExecutionArtifacts(tmp_path),
                stages=JsonSourceStages(tmp_path / "stages"),
            )

        port = lab()
        port.start(run)
        finished = port.run_to_end(run)
        port.forget(run.run_id)
        reloaded = lab().projection(run)
        generator = finished.electrical.generator
        assert generator is not None
        assert reloaded.electrical == finished.electrical
        assert reloaded.content_digest == finished.content_digest
        assert [t.next for t in generator.transitions][:2] == ["STARTING", "RUNNING"]
        document = yaml.safe_load(
            (tmp_path / f"{run.run_id}.yaml").read_text(encoding="utf-8")
        )
        assert document["artifact_schema_version"] == EXECUTION_ARTIFACT_SCHEMA_VERSION == 4
        # Service includes the generator's share, which T024's projection
        # would have dropped.
        row = next(
            r for r in finished.electrical.steps if r.from_offset == generator.transitions[1].at_offset_minutes
        )
        assert row.unserved == 0 and row.served == row.demand
        payload = electrical_payload(finished.electrical)["generator"]
        assert payload["reported_status"].startswith("Reported generator status is pending T025b")
        assert {rule["rule_id"] for rule in payload["discrete_state_rules"]} >= {
            "site-policy-owns-generator-control"
        }
        assert payload["transitions"][0]["phase"] == "physical-acceptance"


def _generator_section(document):
    return document["electrical"]["generator"]


def _discrete_view_entry(document):
    return next(
        item for item in document["electrical"]["latest_view"] if item["unit"] == "state"
    )


#: Each place a lifecycle member or a request lives in the artifact, and the
#: vocabulary it belongs to.
_ENUM_SLOTS = {
    "state_at_t": (lambda d: _generator_section(d)["steps"][0], "state_at_t", "STATE"),
    "state_for_step": (
        lambda d: _generator_section(d)["steps"][0],
        "state_for_step",
        "STATE",
    ),
    "transition_next": (
        lambda d: _generator_section(d)["transitions"][0],
        "next",
        "STATE",
    ),
    "transition_previous": (
        lambda d: _generator_section(d)["transitions"][0],
        "previous",
        "STATE",
    ),
    "latest_view": (_discrete_view_entry, "value", "STATE"),
    "step_request": (
        lambda d: _generator_section(d)["steps"][0],
        "requested",
        "REQUEST",
    ),
}


class TestClosedTypedEnumsSurviveReadback:
    @staticmethod
    def _written(tmp_path: Path):
        run = mini_draft()
        port = HostLabExecution(
            artifacts=YamlExecutionArtifacts(tmp_path),
            stages=JsonSourceStages(tmp_path / "stages"),
        )
        port.start(run)
        port.run_to_end(run)
        path = tmp_path / f"{run.run_id}.yaml"
        return run, path, yaml.safe_load(path.read_text(encoding="utf-8"))

    def test_a_valid_artifact_round_trips_every_slot(self, tmp_path: Path) -> None:
        run, path, document = self._written(tmp_path)
        for name, (locate, key, _) in _ENUM_SLOTS.items():
            assert isinstance(locate(document)[key], str), name
        reread = YamlExecutionArtifacts(tmp_path).read(run.run_id)
        assert reread is not None
        generator = reread.electrical.generator
        assert generator.steps[0].state_at_t == "STOPPED"
        assert generator.steps[0].requested in {"RUN", "STOP"}
        assert generator.transitions[0].next == "STARTING"

    @pytest.mark.parametrize("slot", sorted(_ENUM_SLOTS))
    @pytest.mark.parametrize("bad", [1, "BANANA"], ids=["numeric", "unknown"])
    def test_a_numeric_or_unknown_member_is_refused(
        self, tmp_path: Path, slot: str, bad: object
    ) -> None:
        run, path, document = self._written(tmp_path)
        locate, key, _ = _ENUM_SLOTS[slot]
        locate(document)[key] = bad
        path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
        with pytest.raises(ValueError):
            YamlExecutionArtifacts(tmp_path).read(run.run_id)

    @pytest.mark.parametrize(
        ("slot", "member"),
        [("step_request", "RUNNING"), ("state_at_t", "RUN")],
    )
    def test_the_two_vocabularies_are_kept_apart(
        self, tmp_path: Path, slot: str, member: str
    ) -> None:
        run, path, document = self._written(tmp_path)
        locate, key, _ = _ENUM_SLOTS[slot]
        locate(document)[key] = member
        path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
        with pytest.raises(ValueError):
            YamlExecutionArtifacts(tmp_path).read(run.run_id)
