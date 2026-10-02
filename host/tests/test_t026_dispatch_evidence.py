"""T026 phase 1: dispatch-capable evidence staged through the gateway.

Healthy (`kobo-mini-grid-evening`), prolonged-runtime (`kobo-mini-grid-prolonged`)
and degraded-evidence (`kobo-mini-grid-degraded-evidence`) Drafts, each built in
process on a Site created from the current Kobo template (v3), run on
`mini-grid` v3 under publication profile 5, staged and read back.

Criteria (task file): AC1-AC9, AC11, AC12. Proof rows: sensor dropout, delayed
publication, missing capability, missing override record, policy effective at a
boundary; gap and delay change publication only.
"""

from __future__ import annotations

import copy
import re
from collections import Counter
from fractions import Fraction

import pytest

from assetops_backend.runs.refusals import RunSetupRefused
from assetops_contracts.execution_contract import EXECUTION_CONTRACT_VERSION
from assetops_contracts.observation import observation_series_digest
from assetops_contracts.source_envelope import (
    canonical_envelope_json,
    parse_canonical_envelope_json,
)
from assetops_contracts.source_stage import stage_text
from assetops_simulator.gateway.mappings import (
    SIMULATOR_LAB_DISPATCH_MAPPINGS,
    SIMULATOR_LAB_GATEWAY_MAPPINGS,
    gateway_mapping_for,
)
from assetops_simulator.observation.transform import generate_observations
from kobo import kobo_document, kobo_draft

PROLONGED = dict(start_time="2026-09-22T03:00:00Z", end_time="2026-09-22T11:00:00Z")
EVENING = dict(start_time="2026-09-22T09:00:00Z", end_time="2026-09-22T17:00:00Z")
DEGRADED = "kobo-mini-grid-degraded-evidence"


def draft(name, *, window=PROLONGED, model_version=3, profile_version=5, **kwargs):
    return kobo_draft(
        name,
        model_profile="mini-grid",
        model_profile_version=model_version,
        timestep_minutes=5,
        publication_profile_version=profile_version,
        **window,
        **kwargs,
    )


def without(*event_ids):
    def edit(document):
        document["timeline"] = [
            entry
            for entry in document["timeline"]
            if entry["event_id"] not in event_ids
        ]

    return edit


def with_entry(entry):
    def edit(document):
        document["timeline"].append(copy.deepcopy(entry))

    return edit


def executed(run, tmp_path_factory):
    from lab_execution import HostLabExecution, YamlExecutionArtifacts
    from source_stages import JsonSourceStages

    root = tmp_path_factory.mktemp("t026")
    lab = HostLabExecution(
        artifacts=YamlExecutionArtifacts(root),
        stages=JsonSourceStages(root / "stages"),
    )
    lab.start(run)
    lab.run_to_end(run)
    session = lab._sessions[run.run_id]
    return lab, session, lab.staged_envelopes(run)


@pytest.fixture(scope="module")
def prolonged(tmp_path_factory):
    return executed(draft("kobo-mini-grid-prolonged"), tmp_path_factory)


@pytest.fixture(scope="module")
def healthy(tmp_path_factory):
    return executed(draft("kobo-mini-grid-evening", window=EVENING), tmp_path_factory)


@pytest.fixture(scope="module")
def degraded(tmp_path_factory):
    return executed(draft(DEGRADED), tmp_path_factory)


@pytest.fixture(scope="module")
def undegraded(tmp_path_factory):
    """The degraded world with its three reporting-path conditions removed."""
    return executed(
        draft(
            DEGRADED,
            document_edit=without(
                "override-record-missing",
                "discharge-capability-gap",
                "soc-publication-delay",
            ),
        ),
        tmp_path_factory,
    )


def envelopes(view, device=None, signal=None, family=None):
    return [
        item
        for item in view.stage.envelopes
        if (device is None or item.device_id == device)
        and (signal is None or item.signal_id == signal)
        and (family is None or item.family == family)
    ]


# --- AC11: healthy, prolonged and degraded runs stage reconstructible sets ----


@pytest.mark.parametrize("world", ["healthy", "prolonged", "degraded"])
def test_each_world_stages_a_complete_reconstructible_dataset(world, request) -> None:
    lab, session, view = request.getfixturevalue(world)
    assert view.status == "STAGED"
    assert view.release_blockers == ()
    stage = view.stage
    assert stage.mapping == SIMULATOR_LAB_DISPATCH_MAPPINGS
    assert stage.mapping.envelope_schema_version == 2
    # Byte for byte: every staged envelope is its own canonical text, and the
    # persisted stage re-reads to the same stage.
    for item in stage.envelopes:
        text = canonical_envelope_json(item)
        assert parse_canonical_envelope_json(text) == item
    path = lab._stages.path(stage.run_id)
    assert path.read_text(encoding="utf-8") == stage_text(stage)
    # Every C-required signal family is present, with its unit.
    present = {
        (item.device_id, item.signal_id, item.unit)
        for item in stage.envelopes
        if item.family == "MEASUREMENT" and item.quality == "GOOD"
    }
    for required in [
        ("pv-inverter-controller", "ac-power", "kW"),
        ("pv-inverter-controller", "available-power", "kW"),
        ("battery-pcs-controller", "state-of-charge", "%"),
        ("battery-pcs-controller", "ac-power", "kW"),
        ("battery-pcs-controller", "discharge-capability", "kW"),
        ("generator-controller", "ac-power", "kW"),
        ("generator-controller", "status", "state"),
        ("residential-meter", "active-power", "kW"),
        ("clinic-meter", "active-power", "kW"),
        ("mill-meter", "active-power", "kW"),
    ]:
        assert required in present, required
    policies = {item.signal_id for item in envelopes(view, family="POLICY")}
    assert policies == {
        "policy-start-soc-threshold",
        "policy-stop-soc-threshold",
        "policy-minimum-runtime",
        "policy-reserve-soc",
        "policy-source-priority",
        "policy-critical-load-priority",
    }


def test_a_shipped_run_stages_a_real_interval_mean_and_unavailable(prolonged) -> None:
    _, _, view = prolonged
    kinds = Counter(
        (item.measurement, item.quality)
        for item in envelopes(view, family="MEASUREMENT")
    )
    assert kinds[("INTERVAL_MEAN", "GOOD")] > 0
    assert kinds[("INTERVAL_MEAN", "UNAVAILABLE")] > 0
    first = envelopes(view, "pv-inverter-controller", "ac-power")[0]
    assert first.quality == "UNAVAILABLE"
    assert first.unavailable_reason == "NO_COMPLETED_INTERVAL"
    later = envelopes(view, "pv-inverter-controller", "ac-power")[1]
    assert later.interval_end == later.source_time
    assert later.interval_start < later.interval_end


# --- AC2: observed output and available capability are distinct -------------


def test_capability_is_reported_beside_output_and_not_equal_by_construction(
    prolonged,
) -> None:
    _, _, view = prolonged
    used = {e.source_time: e.value for e in envelopes(view, "pv-inverter-controller", "ac-power") if e.value is not None}
    able = {e.source_time: e.value for e in envelopes(view, "pv-inverter-controller", "available-power") if e.value is not None}
    assert used.keys() == able.keys()
    assert all(able[t] >= used[t] for t in used)
    # The shipped worlds never curtail PV, so its two signals agree in value;
    # the battery's show the distinction: what it could discharge is not what
    # it did (it charges for most of the run).
    power = {e.source_time: e.value for e in envelopes(view, "battery-pcs-controller", "ac-power") if e.value is not None}
    capability = {e.source_time: e.value for e in envelopes(view, "battery-pcs-controller", "discharge-capability") if e.value is not None}
    assert power.keys() == capability.keys()
    assert any(capability[t] != power[t] for t in power)
    assert all(capability[t] >= max(power[t], 0) for t in power)


def test_a_model_that_measures_no_capability_publishes_none(tmp_path_factory) -> None:
    """mini-grid v2 under profile 5: capability is left unreported, not inferred."""
    _, _, view = executed(
        draft("kobo-mini-grid-prolonged", model_version=2), tmp_path_factory
    )
    signals = {(e.device_id, e.signal_id) for e in view.stage.envelopes}
    assert ("pv-inverter-controller", "available-power") not in signals
    assert ("battery-pcs-controller", "discharge-capability") not in signals
    assert ("pv-inverter-controller", "ac-power") in signals


# --- AC3: policy evidence: version, effective interval, source ----------------


def test_policy_records_carry_version_effective_time_and_source(prolonged) -> None:
    lab, session, view = prolonged
    run_foundation = session.records.policies[0].policy_version
    for record in envelopes(view, family="POLICY"):
        assert record.policy_source == "FOUNDATION"
        assert record.policy_version == run_foundation
        assert record.effective_start == "2026-09-01T00:00:00Z"
        assert record.effective_end is None
        assert record.source_time == "2026-09-22T03:00:00Z"
    stop = envelopes(view, "generator-controller", "policy-stop-soc-threshold")[0]
    assert (stop.control, stop.component_id, stop.value, stop.unit) == (
        "generator-stop-soc-threshold",
        "generator",
        Fraction(90),
        "%",
    )
    order = envelopes(view, "site-controller", "policy-source-priority")[0]
    assert order.members == ("pv-array", "battery", "generator")
    assert order.component_id is None and order.unit == "order"


# --- AC4: operator override records, present, missing and delayed -------------


def test_an_override_record_is_present_with_occurrence_effective_time_and_actor(
    undegraded,
) -> None:
    _, _, view = undegraded
    (record,) = envelopes(view, family="OPERATIONAL_RECORD")
    assert record.record_kind == "OVERRIDE_COMMAND"
    assert record.actor == "OPERATOR"
    assert (record.device_id, record.signal_id) == (
        "generator-controller",
        "override-command",
    )
    assert record.control == "generator-stop-soc-threshold"
    assert record.value == Fraction(60)
    # Policy effective at a boundary: offset 120 of a 5-minute run.
    assert record.source_time == "2026-09-22T05:00:00Z"
    assert record.effective_start == "2026-09-22T05:00:00Z"
    assert record.effective_end == "2026-09-22T09:00:00Z"
    assert record.published_at == "2026-09-22T05:00:03Z"


def test_a_missing_override_record_is_none_observed_not_no_override(
    degraded,
) -> None:
    _, session, view = degraded
    assert envelopes(view, family="OPERATIONAL_RECORD") == []
    # The override held in the world all the same.
    effective = [
        control
        for boundary in session.execution.boundaries
        if boundary.control_step is not None
        for control in boundary.control_step.accepted.effective_controls
        if control.address == "generator-stop-soc-threshold@generator"
        and control.from_offset == 120
    ]
    assert effective and effective[0].value == Fraction(60)
    assert effective[0].origin == "OVERRIDE"


def test_an_override_record_has_its_own_delayed_case(tmp_path_factory) -> None:
    delay = {
        "event_id": "override-record-delay",
        "sequence": 15,
        "offset_minutes": 120,
        "entry_kind": "EVENT",
        "category": "DATA_QUALITY",
        "description": "The override record is held five minutes.",
        "execution_role": "FORCING_INPUT",
        "state_key": "override-record-publication-delay@generator",
        "execution_requirement": "REQUIRED",
        "timing": {"shape": "WINDOW", "duration_minutes": 5},
    }

    def edit(document):
        without("override-record-missing")(document)
        with_entry(delay)(document)

    _, _, view = executed(draft(DEGRADED, document_edit=edit), tmp_path_factory)
    (record,) = envelopes(view, family="OPERATIONAL_RECORD")
    assert record.source_time == "2026-09-22T05:00:00Z"
    assert record.effective_start == "2026-09-22T05:00:00Z"
    assert record.published_at == "2026-09-22T05:05:03Z"


# --- AC6/AC7 and the proof table: one gap, one delay ---------------------------


def test_the_gap_leaves_no_fresh_reading_and_no_replacement(degraded) -> None:
    _, _, view = degraded
    times = {
        e.source_time
        for e in envelopes(view, "battery-pcs-controller", "discharge-capability")
    }
    for hour in ("06:00", "06:15", "06:30", "06:45"):
        assert f"2026-09-22T{hour}:00Z" not in times
    assert "2026-09-22T07:00:00Z" in times
    assert "2026-09-22T05:45:00Z" in times


def test_the_delay_moves_publication_time_only(degraded, undegraded) -> None:
    _, _, late = degraded
    _, _, timely = undegraded
    pick = lambda view: next(  # noqa: E731
        e
        for e in envelopes(view, "battery-pcs-controller", "state-of-charge")
        if e.source_time == "2026-09-22T07:00:00Z"
    )
    held, normal = pick(late), pick(timely)
    assert held.published_at == "2026-09-22T07:10:03Z"
    assert normal.published_at == "2026-09-22T07:00:03Z"
    assert held.source_time != held.published_at
    assert (held.value, held.message_id, held.sequence) == (
        normal.value,
        normal.message_id,
        normal.sequence,
    )
    # Exactly one delayed publication in the whole stage.
    delayed = [
        e
        for e in late.stage.envelopes
        if e.family == "MEASUREMENT"
        and e.published_at[:-3] != e.source_time[:-3]
    ]
    assert delayed == [held]


def test_gap_and_delay_change_publication_only(degraded, undegraded) -> None:
    _, worse, _ = degraded
    _, better, _ = undegraded
    a, b = worse.execution.boundaries, better.execution.boundaries
    assert len(a) == len(b)
    for left, right in zip(a, b):
        assert left.stocks == right.stocks
        assert left.discrete == right.discrete
        assert left.interval_measurements == right.interval_measurements
        assert left.control_step == right.control_step


def test_the_delay_alone_leaves_the_reading_series_identical(
    undegraded, tmp_path_factory
) -> None:
    _, timely, _ = undegraded
    _, held, view = executed(
        draft(
            DEGRADED,
            document_edit=without("override-record-missing", "discharge-capability-gap"),
        ),
        tmp_path_factory,
    )
    series = lambda s: observation_series_digest(  # noqa: E731
        generate_observations(s.execution.boundaries, s.reporting)
    )
    assert series(held) == series(timely)
    assert held.reporting.delays and not timely.reporting.delays


# --- AC8: a discrete status is an enum, never numerically noised ---------------


def test_generator_status_is_staged_as_a_member(prolonged) -> None:
    _, _, view = prolonged
    statuses = envelopes(view, "generator-controller", "status")
    assert statuses
    assert {e.value for e in statuses} <= {"STOPPED", "STARTING", "RUNNING", "FAILED"}
    assert "RUNNING" in {e.value for e in statuses}
    for e in statuses:
        assert e.measurement == "STATE_AT_INSTANT" and e.unit == "state"
        assert e.interval_start is None
        assert '"value":"' + e.value + '"' in canonical_envelope_json(e)


# --- Setup: profile answers, a reordering hold is refused ----------------------


def test_an_earlier_profile_blocks_the_degraded_world_naming_itself() -> None:
    run = draft(DEGRADED, profile_version=4)
    assert run.execution_status == "BLOCKED"
    reasons = [r for r in run.blocking_reasons if r.kind == "STATE_NOT_SUPPORTED"]
    subjects = {r.subject for r in reasons}
    assert any("discharge-capability-reporting-availability" in s for s in subjects)
    assert any("simulator-lab-publication" in r.statement for r in reasons)


def test_a_hold_that_would_batch_publications_is_refused_at_setup() -> None:
    def edit(document):
        for entry in document["timeline"]:
            if entry["event_id"] == "soc-publication-delay":
                entry["timing"]["duration_minutes"] = 20

    with pytest.raises(RunSetupRefused) as refused:
        draft(DEGRADED, document_edit=edit)
    assert refused.value.kind == "PUBLICATION_DELAY_REFUSED"


# --- AC12 and the contract-version reading -----------------------------------


def test_only_allowlisted_channels_cross(prolonged) -> None:
    _, _, view = prolonged
    allowed = {entry.key for entry in SIMULATOR_LAB_DISPATCH_MAPPINGS.entries}
    assert {(e.device_id, e.signal_id) for e in view.stage.envelopes} <= allowed
    # The irradiance sensor is configured and observed, and not allowlisted.
    assert ("pv-irradiance-sensor", "irradiance") not in allowed


def test_earlier_profiles_keep_the_fuel_only_schema_1_mapping() -> None:
    assert EXECUTION_CONTRACT_VERSION == 9
    for version in (3, 4):
        mapping = gateway_mapping_for("simulator-lab-publication", version)
        assert mapping is SIMULATOR_LAB_GATEWAY_MAPPINGS
        assert mapping.envelope_schema_version == 1
    assert (
        gateway_mapping_for("simulator-lab-publication", 5)
        is SIMULATOR_LAB_DISPATCH_MAPPINGS
    )


def test_the_override_states_agree_between_setup_and_host() -> None:
    from assetops_backend.runs.service import OVERRIDE_COMMAND_STATES
    from execution_adapter import OVERRIDE_CHANNEL_OF_STATE

    assert set(OVERRIDE_CHANNEL_OF_STATE) == OVERRIDE_COMMAND_STATES


def _override_ids(run):
    from execution_adapter import record_inputs

    return [item.event_id for item in record_inputs(run).overrides]


def test_an_override_publishes_only_when_its_entry_declares_the_operator() -> None:
    # T026 C1: the same stop-threshold override shape publishes a record when the
    # scenario says an operator issued it, and none when it does not.
    assert _override_ids(draft(DEGRADED)) == ["stop-threshold-override"]

    def undeclare(document):
        for entry in document["timeline"]:
            entry.pop("issued_by", None)

    assert _override_ids(draft(DEGRADED, document_edit=undeclare)) == []


def test_stop_60_publishes_no_override_record_under_profile_5() -> None:
    run = draft("kobo-mini-grid-stop-60")
    assert any(
        item.state_key == "generator-stop-soc-threshold" for item in run.deterministic_identity.forcings
    )
    assert _override_ids(run) == []


def test_an_issuer_is_refused_outside_the_operator_commandable_forcings() -> None:
    from assetops_backend.scenarios.ports import ScenarioConfigurationInvalid

    def declare(document):
        for entry in document["timeline"]:
            if entry["event_id"] == "irradiance-1":
                entry["issued_by"] = "OPERATOR"

    with pytest.raises(ScenarioConfigurationInvalid, match="issued_by"):
        draft(DEGRADED, document_edit=declare)

    def wrong_value(document):
        for entry in document["timeline"]:
            if entry["event_id"] == "stop-threshold-override":
                entry["issued_by"] = "TECHNICIAN"

    with pytest.raises(ScenarioConfigurationInvalid, match="issued_by"):
        draft(DEGRADED, document_edit=wrong_value)


def test_the_degraded_scenario_names_no_site() -> None:
    document = kobo_document(DEGRADED)
    assert "target_site" not in document
    assert document["version"]["scenario_version"] == 1


# --- AC5 absorbed carry: review R2 (corrupt stage gave HTTP 500) ---------------


@pytest.mark.parametrize(
    "damage",
    [
        lambda text: b"\xff" + text.encode("utf-8"),
        lambda text: re.sub(r'\\"value\\":\\"[0-9.]+\\"', r'\\"value\\":\\"1/0\\"', text, count=1).encode("utf-8"),
    ],
)
def test_a_corrupt_stage_reads_as_unreadable_not_an_error(
    damage, prolonged, tmp_path
) -> None:
    from source_stages import JsonSourceStages

    _, _, view = prolonged
    stages = JsonSourceStages(tmp_path)
    stages.path(view.stage.run_id).parent.mkdir(parents=True, exist_ok=True)
    stages.path(view.stage.run_id).write_bytes(damage(stage_text(view.stage)))
    from assetops_contracts.source_stage import StageUnreadable

    with pytest.raises(StageUnreadable):
        stages.read(view.stage.run_id)
