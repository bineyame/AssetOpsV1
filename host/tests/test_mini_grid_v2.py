"""T025b phase 1: `mini-grid` v2, the prolonged-runtime recipe and the
separately frozen changed-policy scenario.

Every expected number is computed independently of the resolver - from the
flows the kernel accepted, the Foundation's own coefficients and the
transitions it recorded - in exact rational arithmetic.
"""

from __future__ import annotations

import copy
from fractions import Fraction

import pytest

from assetops_backend.runs.profiles import MINI_GRID_MODEL as V1_PROFILE
from assetops_backend.runs.profiles import MINI_GRID_V2_MODEL as V2_PROFILE
from assetops_contracts.trajectory import PrivateTrajectory

from execution_adapter import model_for, run_to_end
from kobo import kobo_document, kobo_draft, set_property

START = "2026-09-22T03:00:00Z"  # 06:00 in Africa/Addis_Ababa
END = "2026-09-22T11:00:00Z"  # 14:00
PROLONGED = "kobo-mini-grid-prolonged"
CHANGED = "kobo-mini-grid-stop-60"
GEN = "generator-state@generator"
SOC = "battery-state-of-charge@battery"
FUEL = "fuel-tank-volume@fuel-tank"
STOP = "generator-stop-soc-threshold@generator"
RESERVE = "battery-reserve-state-of-charge@battery"
SFC = Fraction(3, 10)
HUNDRED = Fraction(100)


def draft(
    name=PROLONGED, *, version=2, document_edit=None, site_edit=None, timestep_minutes=5
):
    return kobo_draft(
        name,
        document_edit=document_edit,
        site_edit=site_edit,
        timestep_minutes=timestep_minutes,
        model_profile="mini-grid",
        model_profile_version=version,
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


def total(trajectory, flow_id: str) -> Fraction:
    return sum((flows(b).get(flow_id, Fraction(0)) for b in steps_of(trajectory)), Fraction(0))


def request(boundary, quantity: str):
    return next(
        item
        for item in boundary.control_step.intent.requests
        if item.quantity == quantity
    )


def state_over(boundary) -> str:
    return dict(boundary.discrete_for_step)[GEN]


def stock(boundary, address: str) -> Fraction:
    return dict(boundary.stocks)[address]


def effective(boundary, address: str):
    return [
        item
        for item in boundary.control_step.accepted.effective_controls
        if item.address == address
    ]


def transitions(trajectory):
    return [
        (item.at_offset_minutes, item.previous, item.next)
        for item in trajectory.discrete_transitions
    ]


def running_minutes(trajectory) -> int:
    """Actual RUNNING time, from the recorded transitions alone."""
    minutes, since = 0, None
    for at, _, following in transitions(trajectory):
        if following == "RUNNING":
            since = at
        elif since is not None:
            minutes, since = minutes + at - since, None
    if since is not None:
        minutes += trajectory.boundaries[-1].offset_minutes - since
    return minutes


def blocking(run) -> set[tuple[str, str]]:
    return {(reason.kind, reason.subject) for reason in run.blocking_reasons}


def override_entry(offset: int, duration: int, value, event_id: str, sequence: int):
    """A stop-threshold override entry shaped like the shipped one."""
    document = kobo_document(CHANGED)
    entry = copy.deepcopy(
        next(e for e in document["timeline"] if e["event_id"] == "stop-threshold-override")
    )
    entry["event_id"] = event_id
    entry["sequence"] = sequence
    entry["offset_minutes"] = offset
    entry["timing"]["duration_minutes"] = duration
    entry["parameters"][0]["parameter_id"] = f"{event_id}-level"
    entry["parameters"][0]["value"] = value
    return entry


def with_overrides(*windows):
    """Replace the prolonged recipe's (absent) overrides with these windows."""

    def edit(document):
        base = max(e["sequence"] for e in document["timeline"])
        for index, (offset, duration, value) in enumerate(windows, start=1):
            document["timeline"].append(
                override_entry(offset, duration, value, f"stop-override-{index}", base + index)
            )

    return edit


@pytest.fixture(scope="module")
def prolonged() -> PrivateTrajectory:
    return trajectory_of(draft(PROLONGED))


@pytest.fixture(scope="module")
def changed() -> PrivateTrajectory:
    return trajectory_of(draft(CHANGED))


class TestTheRecipesAuthorCausesOnly:
    @pytest.mark.parametrize("name", [PROLONGED, CHANGED])
    def test_no_generator_output_state_or_conclusion_is_authored(self, name) -> None:
        document = kobo_document(name)
        keys = {
            ref
            for entry in document["timeline"]
            for ref in [entry["state_key"]]
            + [item["state_key"] for item in entry["parameters"]]
        }
        allowed = {
            "site:plane-of-array-irradiance",
            "load-demand@load-res",
            "load-demand@load-clinic",
            "load-demand@load-mill",
            STOP,
        }
        assert keys <= allowed, keys - allowed
        assert not any(key.startswith("generator-state") for key in keys)
        purpose = document["purpose"].lower()
        assert "avoidable" not in purpose and "wasted" not in purpose

    def test_the_two_documents_differ_only_by_the_stop_override(self) -> None:
        prolonged, changed = kobo_document(PROLONGED), kobo_document(CHANGED)
        assert prolonged["public_parameters"] == changed["public_parameters"]
        extra = [e for e in changed["timeline"] if e not in prolonged["timeline"]]
        assert [e["event_id"] for e in extra] == ["stop-threshold-override"]
        assert len(changed["timeline"]) == len(prolonged["timeline"]) + 1


class TestProlongedRuntimeUnderTheSitePolicy:
    def test_capability_recovers_while_the_policy_keeps_the_generator_requested(
        self, prolonged
    ) -> None:
        recovered = [
            b
            for b in steps_of(prolonged)
            if state_over(b) == "RUNNING"
            and flows(b)["pv_to_load"] == flows(b)["load_demand"]
            and flows(b)["battery_discharge_taken"] == 0
            and stock(b, SOC) > 35
            and request(b, "generator-run").requested == "RUN"
        ]
        # PV alone serves every load and the battery is charging well above the
        # start threshold, yet the generator is still requested: by the stop
        # policy, and by nothing the scenario authored.
        assert len(recovered) >= 40
        for b in recovered:
            assert "below the stop threshold 90" in request(b, "generator-run").reason
            assert flows(b)["generator_to_load"] == 0
            assert flows(b)["generator_to_battery"] > 0

    def test_it_stops_only_when_running_past_minimum_and_at_the_stop_threshold(
        self, prolonged
    ) -> None:
        assert transitions(prolonged) == [
            (40, "STOPPED", "STARTING"),
            (45, "STARTING", "RUNNING"),
            (375, "RUNNING", "STOPPED"),
        ]
        by_offset = {b.offset_minutes: b for b in prolonged.boundaries}
        assert stock(by_offset[375], SOC) >= 90 > stock(by_offset[370], SOC)
        assert stock(by_offset[40], SOC) <= 35 < stock(by_offset[35], SOC)

    def test_the_frozen_source_priority_is_executed_without_substitution(
        self, prolonged
    ) -> None:
        # While the battery is above its reserve and PV falls short, the
        # battery serves ahead of a RUNNING generator: [pv, battery, generator].
        step = next(b for b in steps_of(prolonged) if b.offset_minutes == 60)
        assert state_over(step) == "RUNNING"
        f = flows(step)
        assert f["battery_to_load"] > 0 and f["generator_to_load"] > 0
        assert f["battery_to_load"] * 12 == 30  # the PCS limit, taken first
        ranks = [
            (e.address, e.value)
            for e in step.control_step.view.entries
            if e.name == "source-priority-rank"
        ]
        assert [a for a, _ in sorted(ranks, key=lambda r: r[1])] == [
            "pv-array",
            "battery",
            "generator",
        ]


class TestTheChangedPolicyScenario:
    def test_the_same_causes_diverge_only_once_the_lower_stop_permits_a_stop(
        self, prolonged, changed
    ) -> None:
        first = {b.offset_minutes: b for b in prolonged.boundaries}
        second = {b.offset_minutes: b for b in changed.boundaries}
        for offset in range(0, 250, 5):
            assert first[offset].stocks == second[offset].stocks, offset
        assert transitions(changed) == [
            (40, "STOPPED", "STARTING"),
            (45, "STARTING", "RUNNING"),
            (250, "RUNNING", "STOPPED"),
        ]
        assert stock(second[250], SOC) >= 60 > stock(second[245], SOC)
        assert first[255].stocks != second[255].stocks

    def test_runtime_energy_fuel_and_flows_change_by_hand(self, prolonged, changed) -> None:
        assert running_minutes(prolonged) == 330
        assert running_minutes(changed) == 205
        results = {}
        for name, trajectory in (("prolonged", prolonged), ("changed", changed)):
            energy = total(trajectory, "generator_output")
            assert energy == total(trajectory, "generator_to_load") + total(
                trajectory, "generator_to_battery"
            )
            final = trajectory.boundaries[-1]
            assert stock(final, FUEL) == 300 - SFC * energy
            results[name] = energy
        assert results["prolonged"] == 134
        assert results["changed"] == Fraction(277, 3)
        assert results["changed"] < results["prolonged"]
        # Service and the reserve consequence are the same in both runs: the
        # policy difference changes runtime, fuel and charging, not service.
        assert total(prolonged, "unserved_load") == total(changed, "unserved_load") == 5
        # PV charges first in the Site's order either way, so the difference is
        # generator charging alone, and the battery ends lower.
        assert total(changed, "pv_to_battery") == total(prolonged, "pv_to_battery")
        assert total(prolonged, "generator_to_battery") - total(
            changed, "generator_to_battery"
        ) == results["prolonged"] - results["changed"]
        assert stock(changed.boundaries[-1], SOC) < stock(prolonged.boundaries[-1], SOC)

    def test_the_effective_policy_is_recorded_per_step(self, prolonged, changed) -> None:
        for b in steps_of(prolonged):
            (item,) = effective(b, STOP)
            assert (item.origin, item.value) == ("BASELINE", 90)
            assert "Foundation" in item.provenance
        for b in steps_of(changed):
            (item,) = effective(b, STOP)
            assert (item.from_offset, item.to_offset) == (
                b.offset_minutes,
                b.offset_minutes + 5,
            )
            assert (item.origin, item.value) == ("OVERRIDE", 60)
            assert "stop-threshold-override" in item.provenance
            # The reserve remains the first effective control.
            assert b.control_step.accepted.effective_controls[0].address == RESERVE


class TestMinimumRuntimeCountsActualRunningTime:
    def test_an_overridden_stop_still_waits_for_the_minimum_runtime(self) -> None:
        """A longer Site minimum runtime (a different Site fixture, not an edit
        of a stored Foundation) holds the generator past the 60 % stop."""

        def longer(document):
            set_property(document, "generator", "minimum-runtime", 240)

        trajectory = trajectory_of(draft(CHANGED, site_edit=longer))
        by_offset = {b.offset_minutes: b for b in trajectory.boundaries}
        assert stock(by_offset[250], SOC) >= 60  # the stop threshold alone would stop here
        assert transitions(trajectory)[-1] == (285, "RUNNING", "STOPPED")  # 45 + 240
        assert running_minutes(trajectory) == 240
        held = [b for b in steps_of(trajectory) if 250 <= b.offset_minutes < 285]
        assert held and all(
            "below the minimum runtime 240" in request(b, "generator-run").reason
            for b in held
        )


class TestTheStopThresholdOverride:
    def test_it_replaces_the_baseline_on_its_window_then_reverts(self) -> None:
        trajectory = trajectory_of(draft(document_edit=with_overrides((120, 120, 60))))
        seen = {
            b.offset_minutes: (effective(b, STOP)[0].origin, effective(b, STOP)[0].value)
            for b in steps_of(trajectory)
        }
        assert seen[115] == ("BASELINE", 90)
        assert seen[120] == ("OVERRIDE", 60)
        assert seen[235] == ("OVERRIDE", 60)
        assert seen[240] == ("BASELINE", 90)
        assert all(v == ("OVERRIDE", 60) for o, v in seen.items() if 120 <= o < 240)
        assert all(v == ("BASELINE", 90) for o, v in seen.items() if not 120 <= o < 240)

    def test_adjacent_windows_are_valid(self) -> None:
        trajectory = trajectory_of(
            draft(document_edit=with_overrides((0, 120, 70), (120, 360, 60)))
        )
        assert trajectory.outcome == "COMPLETED", trajectory.failure
        seen = {b.offset_minutes: effective(b, STOP)[0].value for b in steps_of(trajectory)}
        assert seen[115] == 70 and seen[120] == 60

    def test_genuinely_overlapping_windows_are_refused(self) -> None:
        trajectory = trajectory_of(
            draft(document_edit=with_overrides((0, 240, 70), (120, 360, 60)))
        )
        assert trajectory.outcome == "FAILED"
        assert trajectory.failure.kind == "FORCING_VALUE_AMBIGUOUS"
        assert trajectory.failure.subject == STOP

    @pytest.mark.parametrize(
        "offset,duration", [(7, 113), (0, 122), (120, 3)]
    )
    def test_a_window_off_the_step_blocks(self, offset, duration) -> None:
        run = draft(document_edit=with_overrides((offset, duration, 60)))
        assert ("LIFECYCLE_TIMING_NOT_ALIGNED", STOP) in blocking(run)

    def test_a_window_aligned_to_a_longer_step_is_accepted(self) -> None:
        run = draft(document_edit=with_overrides((120, 120, 60)), timestep_minutes=15)
        assert ("LIFECYCLE_TIMING_NOT_ALIGNED", STOP) not in blocking(run)

    def test_a_stop_below_the_start_threshold_is_refused(self) -> None:
        trajectory = trajectory_of(draft(document_edit=with_overrides((0, 480, 30))))
        assert trajectory.outcome == "FAILED"
        assert trajectory.failure.subject == STOP

    def test_v1_does_not_accept_a_stop_override(self) -> None:
        run = draft(CHANGED, version=1)
        assert (
            "ROLE_NOT_SUPPORTED",
            f"{STOP} as FORCING_INPUT",
        ) in blocking(run)

    @pytest.mark.parametrize(
        "key",
        [
            "generator-start-soc-threshold@generator",
            "generator-minimum-runtime@generator",
            "generator-rated-power@generator",
        ],
    )
    def test_only_declared_controls_are_overridable(self, key) -> None:
        def edit(document):
            with_overrides((0, 480, 60))(document)
            entry = document["timeline"][-1]
            entry["state_key"] = key
            entry["parameters"][0]["state_key"] = key

        run = draft(document_edit=edit)
        assert run.execution_status == "BLOCKED"
        assert ("ROLE_NOT_SUPPORTED", f"{key} as FORCING_INPUT") in blocking(run)

    def test_the_profile_declares_exactly_two_overridable_controls(self) -> None:
        def overridable(profile):
            return {
                s.state_key
                for s in profile.supported_states
                if s.foundation_binding is not None
                and "FORCING_INPUT" in s.supported_roles
            }

        assert overridable(V1_PROFILE) == {"battery-reserve-state-of-charge"}
        assert overridable(V2_PROFILE) == {
            "battery-reserve-state-of-charge",
            "generator-stop-soc-threshold",
        }
        assert V2_PROFILE.step_aligned_forcings == ("generator-stop-soc-threshold",)

    def test_baseline_and_override_freeze_separately_without_editing_the_foundation(
        self,
    ) -> None:
        run = draft(CHANGED)
        identity = run.deterministic_identity
        needs = {n.addressed_key: n for n in identity.model_needs}
        assert needs[STOP].value == 90 and needs[STOP].unit == "%"
        assert needs[STOP].answered_by == "SITE_FOUNDATION"
        assert needs[STOP].declared_by == "model profile mini-grid version 2"
        (forcing,) = [f for f in identity.forcings if f.state_ref.addressed_key == STOP]
        assert (
            forcing.event_id,
            forcing.canonical_value,
            forcing.offset_minutes,
            forcing.duration_minutes,
        ) == ("stop-threshold-override", 60, 0, 480)
        assert identity.site.foundation_version == draft(PROLONGED).deterministic_identity.site.foundation_version


class TestReserveAndServiceConsequences:
    def test_the_mill_peak_is_constrained_by_reserve_and_rating(self, prolonged) -> None:
        constrained = [
            b for b in steps_of(prolonged) if flows(b)["unserved_load"] > 0
        ]
        assert constrained and all(60 <= b.offset_minutes < 120 for b in constrained)
        for b in constrained:
            f = flows(b)
            assert state_over(b) == "RUNNING"
            assert f["generator_to_load"] * 12 == 40  # at its rating
            assert f["battery_discharge_taken"] == 0
            assert stock(b, SOC) == 30  # held at the reserve

    def test_a_raised_reserve_creates_no_energy_and_permits_no_discharge(self) -> None:
        def raise_reserve(document):
            document["timeline"].append(
                {
                    **copy.deepcopy(document["timeline"][0]),
                    "event_id": "raised-reserve",
                    "sequence": 99,
                    "offset_minutes": 0,
                    "category": "EQUIPMENT",
                    "state_key": RESERVE,
                    "timing": {"shape": "WINDOW", "duration_minutes": 60},
                    "parameters": [
                        {
                            **copy.deepcopy(document["timeline"][0]["parameters"][0]),
                            "parameter_id": "raised-reserve-level",
                            "display_name": "Raised reserve",
                            "value": 50,
                            "unit": "%",
                            "state_key": RESERVE,
                        }
                    ],
                }
            )

        trajectory = trajectory_of(draft(document_edit=raise_reserve))
        assert trajectory.outcome == "COMPLETED", trajectory.failure
        first_hour = [b for b in steps_of(trajectory) if b.offset_minutes < 60]
        for b in first_hour:
            f = flows(b)
            assert f["battery_discharge_taken"] == 0
            assert f["unserved_load"] == f["load_demand"]  # nothing else is there
            assert stock(b, SOC) == 40
        # Below the raised reserve the state of charge never reaches the start
        # threshold in that hour, so the generator is not started by it either.
        assert all(state_over(b) == "STOPPED" for b in first_hour)


class TestReproductionAndCompatibility:
    def test_the_same_frozen_runs_reproduce(self, prolonged, changed) -> None:
        for name, reference in ((PROLONGED, prolonged), (CHANGED, changed)):
            run = draft(name)
            first, second = trajectory_of(run), trajectory_of(run)
            assert first.content_digest == second.content_digest
            again = trajectory_of(draft(name))
            assert again.inputs_identity == reference.inputs_identity
            assert again.boundaries == reference.boundaries
            assert again.discrete_transitions == reference.discrete_transitions
        assert prolonged.inputs_identity != changed.inputs_identity

    def test_initial_state_and_policy_are_reconstructible(self, changed) -> None:
        first = changed.boundaries[0]
        assert stock(first, SOC) == 40 and stock(first, FUEL) == 300
        assert dict(first.discrete)[GEN] == "STOPPED"
        policy = [
            (item.from_offset, item.to_offset, item.value, item.origin)
            for b in steps_of(changed)
            for item in effective(b, STOP)
        ]
        assert policy[0] == (0, 5, 60, "OVERRIDE")
        assert policy[-1] == (475, 480, 60, "OVERRIDE")
        assert len(policy) == 96

    def test_v2_without_an_override_behaves_as_v1(self) -> None:
        """v2 adds the effective stop threshold record and nothing else."""
        v1 = trajectory_of(draft(PROLONGED, version=1))
        v2 = trajectory_of(draft(PROLONGED, version=2))
        assert transitions(v1) == transitions(v2)
        for a, b in zip(steps_of(v1), steps_of(v2)):
            assert a.stocks == b.stocks
            assert a.control_step.accepted.flows == b.control_step.accepted.flows
            assert effective(a, STOP) == []
            assert a.control_step.accepted.effective_controls == tuple(
                item
                for item in b.control_step.accepted.effective_controls
                if item.address != STOP
            )

    def test_an_initial_failed_generator_is_still_inert_under_v2(self) -> None:
        def failed(document):
            for item in document["public_parameters"]:
                if item["parameter_id"] == "starting-generator-state":
                    item["value"] = "FAILED"

        trajectory = trajectory_of(draft(document_edit=failed))
        assert trajectory.outcome == "COMPLETED"
        assert transitions(trajectory) == []
        assert total(trajectory, "generator_output") == 0


class TestTheGuardsBehindSetup:
    def test_the_pack_refuses_a_window_inside_a_step_setup_did_not_see(self) -> None:
        """Defence in depth: kernel input built past setup still cannot split
        a generator-policy window inside a step."""
        from dataclasses import replace

        from assetops_simulator.kernel.execute import execute
        from assetops_simulator.packs.mini_grid import MINI_GRID_V2_MODEL

        from execution_adapter import frozen_world_inputs

        inputs = frozen_world_inputs(draft(document_edit=with_overrides((120, 120, 60))))
        moved = tuple(
            replace(item, offset_minutes=122) if item.address == STOP else item
            for item in inputs.forcings
        )
        trajectory = execute(replace(inputs, forcings=moved), MINI_GRID_V2_MODEL)
        assert trajectory.outcome == "FAILED"
        assert trajectory.failure.subject == STOP
        assert trajectory.failure.at_offset_minutes == 120

    def test_a_profile_cannot_align_a_control_it_does_not_let_scenarios_override(
        self,
    ) -> None:
        from dataclasses import replace

        with pytest.raises(ValueError, match="overridable"):
            replace(V1_PROFILE, step_aligned_forcings=("generator-stop-soc-threshold",))


class TestTheLabPersistsAV2Run:
    def test_a_changed_policy_run_persists_and_reads_back(self, tmp_path) -> None:
        from lab_execution import HostLabExecution, YamlExecutionArtifacts
        from source_stages import JsonSourceStages

        run = draft(CHANGED)

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
        assert reloaded.electrical == finished.electrical
        assert reloaded.content_digest == finished.content_digest
        stops = [
            item
            for item in finished.electrical.latest_effective_controls
            if item.address == STOP
        ]
        assert [(item.value, item.origin) for item in stops] == [(60, "OVERRIDE")]
        assert [t.next for t in finished.electrical.generator.transitions] == [
            "STARTING",
            "RUNNING",
            "STOPPED",
        ]
