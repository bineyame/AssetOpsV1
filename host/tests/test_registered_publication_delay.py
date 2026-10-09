"""S2-01c phase 2: a selectable delayed registered run on the virtual publication clock.

`D-2026-10-09-s2-simulated-publication-clock`. A real registered KOBO-001 Draft
selects `registered-kobo-publication` v2 and the shipped
`kobo-daytime-delayed-publication` scenario; the Lab host publishes it through a
real gateway process. Two state-of-charge reports are held by frozen windows:
the 07:00 sample is due at 07:10 and released by the world step that reaches
07:15 (stamped 07:15, never backdated); the 15:00 sample is due at 15:10, after
the world run ends, and is released only by explicit advancement.

Also the local fault fixtures through the real path: link loss and reconnect,
and injected disk-pressure STOP.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend" / "tests"))

import test_s2_registered_basis as registered  # noqa: E402
from gateway_process import GatewayProcess, provisioning_from_snapshot, write_config  # noqa: E402
from gateway_publication import RegisteredGatewayPublisher  # noqa: E402
from lab_execution import HostLabExecution, YamlExecutionArtifacts  # noqa: E402
from publication_schedule import PENDING, RELEASED  # noqa: E402
from source_stages import JsonSourceStages  # noqa: E402

from assetops_backend.runs.profiles import (  # noqa: E402
    LAB_PUBLICATION_PROFILE,
    REGISTERED_KOBO_PUBLICATION_PROFILE,
    REGISTERED_KOBO_PUBLICATION_PROFILE_V2,
)
from assetops_contracts.lab_projection import LabControlRefused  # noqa: E402
from assetops_contracts.source_envelope_v3 import parse_canonical_envelope_v3_text  # noqa: E402

V2 = REGISTERED_KOBO_PUBLICATION_PROFILE_V2
MANIFEST = json.loads(
    (Path(__file__).resolve().parents[1] / "fixtures" / "gateway-fault-scenarios.v1.json").read_text(encoding="utf-8")
)
SOC = ("battery-pcs-controller", "state-of-charge")
MIDDAY, MIDDAY_DUE, MIDDAY_STEP = "2026-09-30T07:00:00Z", "2026-09-30T07:10:00Z", "2026-09-30T07:15:00Z"
CLOSING, CLOSING_DUE, END = "2026-09-30T14:45:00Z", "2026-09-30T15:00:00Z", "2026-09-30T15:00:00Z"
DELAY_SCENARIO = registered.parse_scenario_document(
    yaml.safe_load(
        (registered.REPOSITORY / "config" / "scenarios" / "kobo-daytime-delayed-publication.yaml").read_text(
            encoding="utf-8"
        )
    ),
    source="kobo-daytime-delayed-publication",
    origin="SHIPPED",
)


def setup_service(store):
    registry = registered.ImportedSiteRegistry(registered.FoundationService(store, "demo", registered.Clock(registered.NOW)))
    return registered.RunSetupService(
        registered.FakeRuns(),
        registered.FakeSites(()),
        registered.FakeScenarios((registered.SCENARIO, DELAY_SCENARIO)),
        model_profiles=(registered.DAYTIME_MINI_GRID_MODEL,),
        publication_profiles=(LAB_PUBLICATION_PROFILE, REGISTERED_KOBO_PUBLICATION_PROFILE, V2),
        now=lambda: registered.text(registered.NOW),
        registered_bases=registered.RegisteredLabBasis(registry),
    )


def delay_request(profile=V2) -> dict:
    return registered.request(
        scenario_id=DELAY_SCENARIO.scenario_id,
        scenario_version=DELAY_SCENARIO.version.scenario_version,
        publication_profile={
            "profile_id": profile.publication_profile_id,
            "profile_version": profile.publication_profile_version,
        },
    )


@pytest.fixture(scope="module")
def draft():
    store, _, _ = registered.converted()
    run = setup_service(store).create_draft_run(delay_request())
    assert run.execution_status == "READY" and run.blocking_reasons == (), (run.execution_status, run.blocking_reasons)
    return run


class RecordingLink:
    def __init__(self, link) -> None:
        self.link = link
        self.requests: list[tuple[str, dict]] = []

    def call(self, op, body=None):
        self.requests.append((op, json.loads(json.dumps(body or {}))))
        return self.link.call(op, body)


def gateway_for(root: Path, run) -> GatewayProcess:
    process = GatewayProcess(write_config(root, provisioning_from_snapshot(run.registered_basis.snapshot_canonical)))
    assert process.ready, process.first_line
    return process


def host(root: Path, link) -> HostLabExecution:
    return HostLabExecution(
        artifacts=YamlExecutionArtifacts(root),
        stages=JsonSourceStages(root / "stages"),
        gateway=RegisteredGatewayPublisher(link),
    )


def soc_envelopes(view) -> dict[str, object]:
    """SOC envelopes by source time, parsed."""
    found = {}
    for e in view.envelopes:
        envelope = parse_canonical_envelope_v3_text(e.envelope_text)
        if (envelope.device_id, envelope.signal_id) == SOC:
            found[envelope.source_time] = envelope
    return found


def stored_diagnostics(database: Path) -> list[tuple]:
    """The gateway's stored diagnostic reports, exact bytes and digests."""
    import sqlite3

    db = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    try:
        return db.execute(
            "SELECT gateway_id, sequence_epoch, diagnostic_sequence, cadence_slot, payload_text, sha256 "
            "FROM diagnostic_outbox ORDER BY diagnostic_sequence"
        ).fetchall()
    finally:
        db.close()


def stage_bytes(view):
    return (
        [(e.message_id, e.sequence, e.envelope_text, e.sha256) for e in view.envelopes],
        [(b.batch_id, b.payload_text, b.sha256) for b in view.batches],
    )


def refused(kind: str, action) -> LabControlRefused:
    with pytest.raises(LabControlRefused) as error:
        action()
    assert error.value.kind == kind
    return error.value


def test_the_manifest_describes_the_draft_it_runs(draft) -> None:
    setup = MANIFEST["run_setup"]
    profiles = draft.deterministic_identity.profiles
    assert (MANIFEST["schema"], MANIFEST["version"]) == ("assetops.lab-gateway-fault-scenarios", 1)
    assert (profiles.publication_profile_id, profiles.publication_profile_version) == (
        setup["publication_profile"]["profile_id"], setup["publication_profile"]["profile_version"],
    )
    assert (profiles.model_profile_id, profiles.model_profile_version) == (
        setup["model_profile"]["profile_id"], setup["model_profile"]["profile_version"],
    )
    assert setup["publication_clock"] == V2.publication_clock
    # The public part and the private oracle are separate keys; no public
    # expectation names a delay cause or a scheduled release.
    public = json.dumps([MANIFEST["public_expected"], MANIFEST["delayed_cases"]])
    for window in MANIFEST["private_oracle"]["delay_windows"]:
        assert window["event_id"] not in public


def test_the_delay_profile_and_scenario_freeze_two_windows(draft, tmp_path) -> None:
    port = host(tmp_path / "h", RecordingLink(None))
    reporting = port._reporting_for(draft)
    assert [(w.event_id, w.key, w.start_offset_minutes, w.end_offset_minutes) for w in reporting.delays] == [
        ("soc-publication-delay-midday", SOC, 240, 250),
        ("soc-publication-delay-closing", SOC, 705, 720),
    ]
    assert port._publication_clock_of(draft) == "RUN_VIRTUAL"


def test_a_delayed_report_waits_then_is_admitted_at_the_actual_virtual_instant(draft, tmp_path) -> None:
    gateway = gateway_for(tmp_path / "g", draft)
    recording = RecordingLink(gateway.link)
    port = host(tmp_path / "h", recording)
    try:
        port.start(draft)
        port.step(draft, boundaries=17, from_boundary=0)  # world at 07:00
        schedule = port.publication_schedule(draft)
        assert schedule.clock_instant == MIDDAY and schedule.world_reached_instant == MIDDAY
        [pending] = schedule.pending()
        assert (pending.source_time, pending.scheduled_release_at) == (MIDDAY, MIDDAY_DUE)
        view = port.registered_stage(draft)
        assert MIDDAY not in soc_envelopes(view), "a pending report has no envelope"
        assert "2026-09-30T06:45:00Z" in soc_envelopes(view), "unrelated due reports were admitted"
        sequences_before = {e.sequence for e in view.envelopes}

        # The clock cannot pass the world while it runs, nor move backward;
        # the same instant again is accepted and releases nothing.
        refused("PUBLICATION_AHEAD_OF_WORLD", lambda: port.advance_publication(draft, MIDDAY_DUE))
        refused("PUBLICATION_CLOCK_BACKWARD", lambda: port.advance_publication(draft, "2026-09-30T06:00:00Z"))
        refused("PUBLICATION_INSTANT_INVALID", lambda: port.advance_publication(draft, "07:00"))
        assert port.advance_publication(draft, MIDDAY)["schedule"].pending() == (pending,)
        assert {e.sequence for e in port.registered_stage(draft).envelopes} == sequences_before

        port.step(draft, boundaries=1, from_boundary=17)  # world at 07:15, past the 07:10 due instant
        midday = soc_envelopes(port.registered_stage(draft))[MIDDAY]
        assert (midday.source_time, midday.published_at) == (MIDDAY, MIDDAY_STEP)  # not backdated to 07:10
        released = [d for d in port.publication_schedule(draft).delayed if d.source_time == MIDDAY][0]
        assert (released.state, released.released_at_clock, released.message_id) == (
            RELEASED, MIDDAY_STEP, midday.message_id,
        )

        port.step(draft, boundaries=30, from_boundary=18)  # world at 14:45
        [closing] = port.publication_schedule(draft).pending()
        assert (closing.source_time, closing.scheduled_release_at) == (CLOSING, CLOSING_DUE)
        assert CLOSING not in soc_envelopes(port.registered_stage(draft))
        refused("PUBLICATION_AHEAD_OF_WORLD", lambda: port.advance_publication(draft, "2026-09-30T14:50:00Z"))

        assert port.run_to_end(draft).status == "COMPLETED"  # world at 15:00, exactly the due instant
        schedule = port.publication_schedule(draft)
        assert schedule.world_complete and schedule.clock_instant == END and schedule.pending() == ()
        view = port.registered_stage(draft)
        late = soc_envelopes(view)[CLOSING]
        assert (late.source_time, late.published_at) == (CLOSING, CLOSING_DUE)
        expected = MANIFEST["public_expected"]
        assert (len(view.envelopes), len(view.holds)) == (expected["admitted_envelopes_after_release"], expected["held_reports"])
        for case in MANIFEST["delayed_cases"]:
            assert soc_envelopes(view)[case["source_time"]].published_at == case["expected_published_at"]
        oracle = {w["scheduled_release_at"] for w in MANIFEST["private_oracle"]["delay_windows"]}
        assert {d.scheduled_release_at for d in port.publication_schedule(draft).delayed} == oracle

        # After the world run: the clock advances past its end without a
        # kernel step, and releases nothing that was not due.
        beyond = port.advance_publication(draft, "2026-09-30T16:00:00Z")
        assert beyond["publication_refused"] is None and beyond["schedule"].clock_instant == "2026-09-30T16:00:00Z"
        assert stage_bytes(port.registered_stage(draft)) == stage_bytes(view)
        assert port._sessions[draft.run_id].execution.boundaries[-1].offset_minutes == 720  # no kernel step
        for e in view.envelopes:
            envelope = parse_canonical_envelope_v3_text(e.envelope_text)
            assert envelope.published_at >= envelope.source_time
        delayed_values = {soc_envelopes(view)[t].value for t in (MIDDAY, CLOSING)}
        assert None not in delayed_values

        # Restart both processes: same identities and bytes; a repeated or
        # later advance allocates nothing new.
        before = stage_bytes(view)
        gateway.kill()
        restarted = GatewayProcess(gateway.config)
        try:
            assert restarted.ready
            again = host(tmp_path / "h", restarted.link)
            assert again.publication_schedule(draft).clock_instant == "2026-09-30T16:00:00Z"
            assert again.advance_publication(draft, "2026-09-30T16:00:00Z")["publication_refused"] is None
            assert again.advance_publication(draft, "2026-09-30T18:00:00Z")["publication_refused"] is None
            assert stage_bytes(again.registered_stage(draft)) == before
        finally:
            restarted.kill()
    finally:
        gateway.kill()

    # No Lab-private scheduling fact crossed the channel.
    sent = json.dumps(recording.requests)
    for private in ("soc-publication-delay", "scheduled_release", MIDDAY_DUE, "delay_event"):
        assert private not in sent
    reports = [text for op, body in recording.requests if op.startswith("admit") for text in body["reports"]]
    assert reports and all(draft.run_id not in text for text in reports)
    assert {op for op, _ in recording.requests} <= {
        "identity", "activate", "advance_publication_clock", "admit_at_run_clock", "seal", "run_stage",
    }


def test_pause_and_restart_release_nothing(draft, tmp_path) -> None:
    gateway = gateway_for(tmp_path / "g", draft)
    try:
        port = host(tmp_path / "h", gateway.link)
        port.start(draft)
        port.step(draft, boundaries=17, from_boundary=0)
        port.forget(draft.run_id)  # host restart: the run is interrupted
        gateway.kill()
        restarted = GatewayProcess(gateway.config)
        try:
            again = host(tmp_path / "h", restarted.link)
            schedule = again.publication_schedule(draft)
            assert schedule.clock_instant == MIDDAY and len(schedule.pending()) == 1
            refused("PUBLICATION_AHEAD_OF_WORLD", lambda: again.advance_publication(draft, MIDDAY_DUE))
            assert MIDDAY not in soc_envelopes(again.registered_stage(draft))
        finally:
            restarted.kill()
    finally:
        gateway.kill()


def test_link_loss_keeps_the_report_pending_and_reconnect_releases_it_once(draft, tmp_path) -> None:
    gateway = gateway_for(tmp_path / "g", draft)
    try:
        port = host(tmp_path / "h", gateway.link)
        port.start(draft)
        port.step(draft, boundaries=17, from_boundary=0)
        before = stage_bytes(port.registered_stage(draft))
        gateway.link.call("emit_diagnostic", {})
        diagnostics_before = stored_diagnostics(gateway.database)
        assert diagnostics_before, "the measured set is not empty"
        gateway.kill()  # link loss
        port.step(draft, boundaries=1, from_boundary=17)  # the world goes on: 07:15, past due
        notes = port._sessions[draft.run_id].staging_notes
        assert any(n.startswith("registered publication refused") for n in notes), notes
        lost = port.publication_schedule(draft)
        assert lost.clock_instant == MIDDAY_STEP
        assert [d.state for d in lost.delayed if d.source_time == MIDDAY] == [PENDING]
        assert port.gateway_diagnostics()["status"] == "GATEWAY_UNAVAILABLE"
        assert port.registered_stage(draft).status == "GATEWAY_UNAVAILABLE"
        restarted = GatewayProcess(gateway.config)  # reconnect
        try:
            again = port.advance_publication(draft, MIDDAY_STEP)  # same instant: the retry
            assert again["publication_refused"] is None and again["schedule"].pending() == ()
            view = port.registered_stage(draft)
            assert set(before[0]) <= set(stage_bytes(view)[0]), "earlier envelopes byte-identical"
            assert set(before[1]) <= set(stage_bytes(view)[1]), "earlier batches byte-identical"
            assert soc_envelopes(view)[MIDDAY].published_at == MIDDAY_STEP
            count = len(view.envelopes)
            port.advance_publication(draft, MIDDAY_STEP)
            assert len(port.registered_stage(draft).envelopes) == count
            # S2-01c carry C2: stored diagnostics survive the real reconnect byte for byte.
            restarted.link.call("emit_diagnostic", {})
            assert set(diagnostics_before) <= set(stored_diagnostics(restarted.database)),                 "earlier diagnostics byte-identical"
        finally:
            restarted.kill()
    finally:
        gateway.kill()


def test_injected_stop_refuses_acquisition_and_keeps_bytes(draft, tmp_path) -> None:
    gateway = gateway_for(tmp_path / "g", draft)
    try:
        publisher = RegisteredGatewayPublisher(gateway.link)
        port = host(tmp_path / "h", gateway.link)
        port.start(draft)
        port.step(draft, boundaries=4, from_boundary=0)
        before = stage_bytes(port.registered_stage(draft))
        publisher.inject_fault("DISK_PRESSURE", "WARN")
        port.step(draft, boundaries=1, from_boundary=4)
        warned = port.gateway_diagnostics()["diagnostics"]
        assert (warned["disk_pressure"]["level"], warned["acquisition"]) == ("WARN", "ACCEPTING")
        assert len(port.registered_stage(draft).envelopes) > len(before[0])
        before = stage_bytes(port.registered_stage(draft))
        publisher.inject_fault("DISK_PRESSURE", "STOP")
        port.step(draft, boundaries=4, from_boundary=5)
        notes = port._sessions[draft.run_id].staging_notes
        assert any("DISK_PRESSURE_STOP" in n for n in notes), notes
        assert stage_bytes(port.registered_stage(draft)) == before
        read = port.gateway_diagnostics()
        assert read["status"] == "AVAILABLE"
        assert read["diagnostics"]["disk_pressure"]["level"] == "STOP"
        assert read["diagnostics"]["disk_pressure"]["provenance"] == "INJECTED_FAULT_FIXTURE"
        assert read["diagnostics"]["acquisition"] != "ACCEPTING"
        publisher.inject_fault("DISK_PRESSURE", None)
        port.step(draft, boundaries=1, from_boundary=9)
        after = port.registered_stage(draft)
        assert set(before[0]) <= set(stage_bytes(after)[0]) and set(before[1]) <= set(stage_bytes(after)[1])
        assert len(after.envelopes) > len(before[0])  # the replay admitted what STOP refused
    finally:
        gateway.kill()


def test_a_gateway_clock_profile_still_refuses_a_delay(tmp_path) -> None:
    """S2-01b's safe refusal stays for a profile on the gateway's real clock."""
    store, _, _ = registered.converted()
    service = setup_service(store)
    run = service.create_draft_run(delay_request(REGISTERED_KOBO_PUBLICATION_PROFILE))
    # v1 declares no delay state, so the Draft is BLOCKED and never executes;
    # an injected window on a v1 run is refused by the host
    # (test_registered_kobo_resolution's DelayedHost regression).
    assert run.execution_status == "BLOCKED"
    assert any("battery-soc-publication-delay" in repr(r) for r in run.blocking_reasons), run.blocking_reasons
