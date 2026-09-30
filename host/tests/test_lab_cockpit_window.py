"""T025d phase 2: the integrated proof of one short, independently derived window.

The policy-varied Kobo recipe the frontend fixtures are generated from
(`make_history_fixtures.document()`: `kobo-mini-grid-stop-60`, mini-grid v2,
5-minute step, the generator controller's status silenced for 30 minutes from
offset 60) is executed through the Lab's own host, and the window
[55, 135) is checked against values derived HERE from the declared inputs -
the scenario's load events, the Kobo template's battery and PCS properties -
rather than read back from the engine that produced them:

- an applied scenario event (the mill's demand steps 0 -> 40 kW at offset 60)
  seen in state-at-T at 60 and in the interval [60, 65), not at 55;
- a reporting gap [60, 90) that suppresses the generator status samples and
  is not a physical outage (the generator stays RUNNING through it);
- two numeric constrained requests: discharge 46 kW limited to the PCS
  discharge limit at [60, 65), and to the energy above the reserve at [65, 70);
- a charge/discharge reversal on the battery branch ([60, 65) discharges,
  [130, 135) charges, limited by the PCS charge limit);
- exact balance at every interval of the window, and each load addressed.

It then exercises the controls the browser's auto-play drives: a duplicate or
late step, a restart, pacing (step sizes), and a reload with the executor made
unreachable.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import pytest
import yaml

import lab_execution
from assetops_backend.simulator_lab_api import history_payload
from assetops_simulator.kernel.execute import Execution
from lab_execution import LabControlRefused
from make_history_fixtures import document
from test_generator_observation import draft
from test_lab_history import a_lab, records

TEMPLATE = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "site-templates"
    / "kobo-mini-grid-60kw.yaml"
)
BATTERY = "battery-state-of-charge@battery"
GENERATOR = "generator-state@generator"
STEP_HOURS = Fraction(5, 60)


def template_property(component_id: str, key: str) -> Fraction:
    """A property of the shipped Kobo template, read as the YAML declares it."""

    def walk(node):
        if isinstance(node, dict):
            if node.get("component_id") == component_id:
                for item in node.get("properties", []):
                    if item["property_key"] == key:
                        return Fraction(str(item["value"]))
            for value in node.values():
                found = walk(value)
                if found is not None:
                    return found
        elif isinstance(node, list):
            for value in node:
                found = walk(value)
                if found is not None:
                    return found
        return None

    found = walk(yaml.safe_load(TEMPLATE.read_text(encoding="utf-8")))
    assert found is not None, (component_id, key)
    return found


def declared_demand(state_key: str, offset: int) -> Fraction:
    """The recipe's declared demand for one load at an offset (its WINDOW event)."""
    for entry in document()["timeline"]:
        if entry["state_key"] != state_key:
            continue
        start = entry["offset_minutes"]
        end = start + entry["timing"]["duration_minutes"]
        if start <= offset < end:
            return Fraction(str(entry["parameters"][0]["value"]))
    raise AssertionError((state_key, offset))


def interval_at(history, offset):
    matches = [i for i in history.intervals if i.from_offset == offset]
    assert len(matches) == 1, offset
    return matches[0]


def sample(history, address, offset, phase="POST_EVENT"):
    matches = [
        s
        for s in history.samples
        if s.address == address and s.offset_minutes == offset and s.phase == phase
    ]
    assert len(matches) == 1, (address, offset, phase)
    return matches[0].value


def flow(interval, flow_id) -> Fraction:
    for item in interval.step.accepted.flows:
        if item.flow_id == flow_id:
            return item.mean_power
    raise AssertionError(flow_id)


@pytest.fixture(scope="module")
def window(tmp_path_factory):
    """One boundary at a time, the way auto-play steps, then to the end."""
    root = tmp_path_factory.mktemp("cockpit-window")
    run = draft(document=document())
    lab = a_lab(root)
    projection = lab.start(run)
    while projection.status == "RUNNING":
        projection = lab.step(
            run, boundaries=1, from_boundary=projection.boundaries_completed
        )
    assert projection.status == "COMPLETED"
    return run, root, projection, lab.history(run)


class TestTheWindowIsWhatTheInputsDeclare:
    def test_the_mill_event_is_in_state_at_t_and_the_interval_after_it(
        self, window
    ) -> None:
        _, _, _, history = window
        mill = "load-demand@load-mill"
        assert declared_demand(mill, 55) == 0
        assert declared_demand(mill, 60) == 40
        # The event takes effect for the interval that starts at its boundary,
        # [60, 65), not the one that ends there; the served-power reading of
        # the preceding interval therefore moves at 65, not at 60.
        before = {
            load.address: load for load in interval_at(history, 55).step.accepted.loads
        }
        assert before[mill].demand_power == 0
        served_reading = "load-served-power@load-mill"
        assert sample(history, served_reading, 60, "PRECEDING_INTERVAL") == 0
        # The reading is the interval's energy (40 kW for 5 minutes).
        assert sample(history, served_reading, 65, "PRECEDING_INTERVAL") == 40 * STEP_HOURS
        served = {
            load.address: load
            for load in interval_at(history, 60).step.accepted.loads
        }
        assert set(served) == {
            "load-demand@load-clinic",
            "load-demand@load-mill",
            "load-demand@load-res",
        }
        for address, load in served.items():
            assert load.demand_power == declared_demand(address, 60), address
            assert load.served_power == load.demand_power, address

    def test_a_discharge_request_is_limited_by_the_pcs(self, window) -> None:
        _, _, _, history = window
        interval = interval_at(history, 60)
        demand = sum(
            declared_demand(key, 60)
            for key in (
                "load-demand@load-res",
                "load-demand@load-clinic",
                "load-demand@load-mill",
            )
        )
        pv = flow(interval, "pv_to_load")
        control = interval.step.accepted.control(BATTERY, "battery-power")
        limit = template_property("battery-pcs", "pcs-discharge-limit")
        assert control.requested == demand - pv == 46
        assert control.accepted == min(control.requested, limit) == 30
        assert control.limited_by == (f"pcs-discharge-limit {limit} kW",)
        # The generator covers what the battery was not allowed to.
        assert flow(interval, "generator_to_load") == demand - pv - control.accepted

    def test_the_next_request_is_limited_by_the_energy_above_the_reserve(
        self, window
    ) -> None:
        _, _, _, history = window
        interval = interval_at(history, 65)
        capacity = template_property("battery", "battery-energy-capacity")
        reserve = template_property("battery", "reserve-state-of-charge")
        efficiency = template_property("battery-pcs", "pcs-conversion-efficiency") / 100
        soc = sample(history, BATTERY, 65)
        above = (soc - reserve) / 100 * capacity * efficiency / STEP_HOURS
        control = interval.step.accepted.control(BATTERY, "battery-power")
        assert control.requested == 46
        assert control.accepted == above == 18
        assert control.limited_by == (
            f"energy above the reserve in effect ({reserve} %)",
        )
        # The stock at the far instant is the reserve, exactly.
        assert sample(history, BATTERY, 70) == reserve

    def test_the_battery_branch_reverses_and_charging_is_limited(
        self, window
    ) -> None:
        _, _, _, history = window
        discharge = interval_at(history, 60).step.accepted.control(
            BATTERY, "battery-power"
        )
        charge = interval_at(history, 130).step.accepted.control(
            BATTERY, "battery-power"
        )
        limit = template_property("battery-pcs", "pcs-charge-limit")
        assert discharge.accepted > 0 > charge.accepted
        assert charge.accepted == -limit
        assert charge.limited_by == (f"pcs-charge-limit {limit} kW",)
        into = interval_at(history, 130)
        assert flow(into, "pv_to_battery") + flow(into, "generator_to_battery") == limit

    def test_the_gap_is_evidence_loss_not_an_outage(self, window) -> None:
        _, _, _, history = window
        status = [a for a in history.attempts if a.address == GENERATOR]
        suppressed = {
            a.at_offset_minutes for a in status if a.outcome == "SUPPRESSED_BY_GAP"
        }
        assert suppressed, "the gap suppressed nothing, so this check is vacuous"
        assert all(60 <= offset < 90 for offset in suppressed)
        assert not any(
            a.outcome == "SUPPRESSED_BY_GAP"
            for a in status
            if not 60 <= a.at_offset_minutes < 90
        )
        # The world kept running through it.
        for offset in range(60, 95, 5):
            assert sample(history, GENERATOR, offset) == "RUNNING"

    def test_every_interval_in_the_window_balances_exactly(self, window) -> None:
        run, _, _, history = window
        payload = history_payload(history, run)
        checked = 0
        for interval in payload["intervals"]:
            if not 55 <= interval["from_offset"] < 135:
                continue
            identities = interval["balance_identities"]
            assert identities, interval["from_offset"]
            for identity in identities:
                assert identity["residual"] is not None
                assert Fraction(identity["residual"]) == 0
                assert Fraction(identity["source_energy"]) == Fraction(
                    identity["sink_energy"]
                )
                checked += 1
        assert checked >= 16, checked


class TestPlaybackControlsAgainstTheHost:
    def test_a_duplicate_or_late_step_advances_nothing(self, tmp_path) -> None:
        run = draft(document=document())
        lab = a_lab(tmp_path)
        projection = lab.start(run)
        first = lab.step(run, boundaries=1, from_boundary=projection.boundaries_completed)
        before = records(lab.history(run))
        # The same request again (a second tab, a replayed POST, a step that
        # answered after the browser's timeout and was re-sent) is refused.
        with pytest.raises(LabControlRefused) as refused:
            lab.step(run, boundaries=1, from_boundary=projection.boundaries_completed)
        assert refused.value.kind == "STEP_ALREADY_APPLIED"
        assert lab.projection(run).boundaries_completed == first.boundaries_completed
        assert records(lab.history(run)) == before

    def test_a_restart_interrupts_and_refuses_to_resume(self, tmp_path) -> None:
        run = draft(document=document())
        lab = a_lab(tmp_path)
        projection = lab.start(run)
        lab.step(run, boundaries=3, from_boundary=projection.boundaries_completed)
        restarted = a_lab(tmp_path)
        assert restarted.projection(run).status == "INTERRUPTED"
        with pytest.raises(LabControlRefused) as refused:
            restarted.step(run, boundaries=1, from_boundary=4)
        assert refused.value.kind == "INTERRUPTED"
        assert restarted.history(run).status == "INTERRUPTED"

    def test_pacing_changes_nothing_physical_or_observed(
        self, window, tmp_path
    ) -> None:
        run, _, stepped, stepped_history = window
        chunked = a_lab(tmp_path / "chunked")
        projection = chunked.start(run)
        for size in (1, 4, 9, 2):
            projection = chunked.step(
                run, boundaries=size, from_boundary=projection.boundaries_completed
            )
        projection = chunked.run_to_end(run)
        whole = a_lab(tmp_path / "whole")
        whole.start(run)
        at_once = whole.run_to_end(run)
        for other in (projection, at_once):
            assert other.content_digest == stepped.content_digest
            assert (
                other.observation_series_digest
                == stepped.observation_series_digest
            )
        assert records(chunked.history(run)) == records(stepped_history)
        assert records(whole.history(run)) == records(stepped_history)

    def test_a_reload_with_the_executor_unreachable_reruns_nothing(
        self, window, monkeypatch
    ) -> None:
        run, root, _, live = window
        path = root / f"{run.run_id}.yaml"
        before = path.read_bytes()

        def refuse(*_args, **_kwargs):
            raise AssertionError("a reload executed the kernel")

        monkeypatch.setattr(lab_execution, "start", refuse)
        monkeypatch.setattr(Execution, "advance", refuse)
        monkeypatch.setattr(Execution, "run_to_end", refuse)
        reloaded = a_lab(root)
        assert reloaded.projection(run).status == "COMPLETED"
        history = reloaded.history(run)
        assert history.source == "PERSISTED"
        live_wire = history_payload(live, run)
        reload_wire = history_payload(history, run)
        # Only the provenance differs: where it was read from, what that
        # means, and the integrity digest a persisted history carries.
        for wire in (live_wire, reload_wire):
            for key in ("source", "statement", "history_digest"):
                wire.pop(key)
        assert reload_wire == live_wire
        assert path.read_bytes() == before
