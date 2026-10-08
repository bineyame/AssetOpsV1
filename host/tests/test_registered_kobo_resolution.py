"""S2-01b phase 3a: `registered-kobo-publication` v1 through the real gateway.

`D-2026-10-08-s2-simulated-device-resolution-and-delay-boundary`. Two Drafts of
the same registered KOBO-001 basis, one selecting `simulator-lab-publication`
v3 and one the new profile, run in the Lab host against real gateway processes.
Under v3 the 41 non-terminating readings stay `INVALID_VALUE` holds, exactly as
phase 2 pinned. Under the new profile the simulated device publishes them at
0.000001 in their own unit, rounded half to even, so all 293 public reports are
admitted, replay keeps identity and bytes, and no exact private value crosses
the channel.

Also the Q3 regression: a registered run whose reporting holds a publication
delay window stages nothing and says so.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend" / "tests"))

import test_s2_registered_basis as registered  # noqa: E402
import test_s2_registered_resolution as resolution  # noqa: E402
from gateway_process import GatewayProcess, provisioning_from_snapshot, write_config  # noqa: E402
from gateway_publication import RegisteredGatewayPublisher  # noqa: E402
from lab_execution import HostLabExecution, YamlExecutionArtifacts, generate_observations  # noqa: E402
from source_stages import JsonSourceStages  # noqa: E402

from assetops_backend.runs.profiles import LAB_PUBLICATION_PROFILE, REGISTERED_KOBO_PUBLICATION_PROFILE  # noqa: E402
from assetops_contracts.observation import (  # noqa: E402
    PublicationDelayWindow,
    exact_decimal_text,
    quantize_half_even,
)
from assetops_contracts.source_envelope_v3 import parse_canonical_envelope_v3_text  # noqa: E402

MICRO = Fraction(1, 1_000_000)
CANONICAL_DECIMAL = re.compile(r"^-?(0|[1-9][0-9]*)(\.[0-9]{0,5}[1-9])?$")


@pytest.fixture(scope="module")
def drafts():
    """A v3 and a new-profile Draft over one registered basis (same snapshot bytes)."""
    store, _, _ = registered.converted()
    service = resolution.setup_service(store)
    old = service.create_draft_run(registered.request())
    new = service.create_draft_run(registered.request(**resolution.SELECTED))
    assert old.registered_basis.snapshot_sha256 == new.registered_basis.snapshot_sha256
    return old, new


class RecordingLink:
    def __init__(self, link) -> None:
        self.link = link
        self.requests: list[tuple[str, dict]] = []

    def call(self, op, body=None):
        self.requests.append((op, json.loads(json.dumps(body or {}))))
        return self.link.call(op, body)


def gateway_for(root: Path, draft) -> GatewayProcess:
    config = write_config(root, provisioning_from_snapshot(draft.registered_basis.snapshot_canonical))
    process = GatewayProcess(config)
    assert process.ready, process.first_line
    return process


def host(root: Path, link, cls=HostLabExecution) -> HostLabExecution:
    return cls(
        artifacts=YamlExecutionArtifacts(root),
        stages=JsonSourceStages(root / "stages"),
        gateway=RegisteredGatewayPublisher(link),
    )


def complete(draft, root: Path, link) -> HostLabExecution:
    port = host(root, link)
    port.start(draft)
    assert port.run_to_end(draft).status == "COMPLETED"
    return port


def published_reports(port, draft):
    session = port._sessions[draft.run_id]
    return [
        o for o in generate_observations(session.execution.boundaries, session.reporting)
        if o.outcome == "REPORTED"
    ]


def key(item) -> tuple[str, str, str]:
    return (item.device_id, item.signal_id, item.source_time if hasattr(item, "source_time") else item.source_sample_time)


def test_the_new_profile_admits_every_report_the_old_one_held(drafts, tmp_path) -> None:
    old, new = drafts
    assert old.deterministic_identity.signal_resolutions == ()
    assert len(new.deterministic_identity.signal_resolutions) == len(REGISTERED_KOBO_PUBLICATION_PROFILE.device_signals)
    old_gateway, new_gateway = gateway_for(tmp_path / "g-old", old), gateway_for(tmp_path / "g-new", new)
    try:
        old_port = complete(old, tmp_path / "h-old", old_gateway.link)
        new_port = complete(new, tmp_path / "h-new", new_gateway.link)
        old_view, new_view = old_port.registered_stage(old), new_port.registered_stage(new)
    finally:
        old_gateway.kill()
        new_gateway.kill()

    # The old profile is unchanged: 252 envelopes and 41 ratio holds, as pinned in phase 2.
    assert len(old_view.envelopes) == 252 and len(old_view.holds) == 41
    assert {(h.kind, h.field) for h in old_view.holds} == {("INVALID_VALUE", "value")}

    # The new profile: every public report is a reading; no hold rule was hidden.
    old_reports, new_reports = published_reports(old_port, old), published_reports(new_port, new)
    # 293 public reports: the valued readings plus the explicit UNAVAILABLE ones.
    assert len(new_reports) == len(old_reports) == 293 - len(
        [e for e in new_view.envelopes if parse_canonical_envelope_v3_text(e.envelope_text).value is None]
    )
    assert len(new_view.envelopes) == 293 and new_view.holds == ()
    assert new_view.queue_depth_by_state == {"STAGED": 293}

    # Same world, same draws: each new reading is the old exact value rounded
    # half to even to 0.000001, and nothing else about the report differs.
    exact = {key(o): o for o in old_reports}
    held = {(h.device_id, h.signal_id, h.source_time) for h in old_view.holds}
    by_time_value: dict[str, list[str]] = {}
    for e in new_view.envelopes:
        envelope = parse_canonical_envelope_v3_text(e.envelope_text)
        by_time_value.setdefault(e.source_time, []).append(envelope.value)
    ratio_count = 0
    for report in new_reports:
        before = exact[key(report)]
        assert report.reported_value == quantize_half_even(before.reported_value, MICRO)
        assert replace(report, reported_value=before.reported_value) == before
        text = exact_decimal_text(report.reported_value)
        assert CANONICAL_DECIMAL.match(text), text
        assert text in by_time_value[report.source_sample_time]
        if key(report) in held:
            ratio_count += 1
            assert "/" in exact_decimal_text(before.reported_value)
    # The 41 phase-2 holds are exactly the readings that changed into admitted values.
    assert ratio_count == 41


def test_replay_and_restart_keep_the_quantized_identity_and_bytes(drafts, tmp_path) -> None:
    _, new = drafts
    gateway = gateway_for(tmp_path / "g", new)
    try:
        port = complete(new, tmp_path / "h", gateway.link)
        before = port.registered_stage(new)
        session = port._sessions[new.run_id]
        replay = RegisteredGatewayPublisher(gateway.link).publish(
            new.run_id, new.registered_basis,
            generate_observations(session.execution.boundaries, session.reporting),
            interval_minutes=15,
        )
        assert replay.admitted == 0 and replay.already_admitted == 293 and replay.held == 0
        gateway.kill()
        restarted = GatewayProcess(gateway.config)
        try:
            assert restarted.ready
            after = host(tmp_path / "h", restarted.link).registered_stage(new)
        finally:
            restarted.kill()
    finally:
        gateway.kill()
    assert [(e.message_id, e.sequence, e.envelope_text, e.sha256) for e in after.envelopes] == [
        (e.message_id, e.sequence, e.envelope_text, e.sha256) for e in before.envelopes
    ]
    assert [(b.batch_id, b.payload_text, b.sha256) for b in after.batches] == [
        (b.batch_id, b.payload_text, b.sha256) for b in before.batches
    ]


def test_no_exact_private_value_crosses_the_channel(drafts, tmp_path) -> None:
    old, new = drafts
    gateway = gateway_for(tmp_path / "g", new)
    recording = RecordingLink(gateway.link)
    try:
        port = complete(new, tmp_path / "h", recording)
    finally:
        gateway.kill()
    # The exact ratios the old profile would have published, which only the
    # kernel and the old reading hold.
    session = port._sessions[new.run_id]
    unrounded = replace(session.reporting, signals=tuple(replace(s, resolution=None) for s in session.reporting.signals))
    exact_texts = {
        exact_decimal_text(o.reported_value)
        for o in generate_observations(session.execution.boundaries, unrounded)
        if o.outcome == "REPORTED" and isinstance(o.reported_value, Fraction)
        and o.reported_value != quantize_half_even(o.reported_value, MICRO)
    }
    assert len(exact_texts) >= 41
    reports = [json.loads(text) for op, body in recording.requests if op == "admit" for text in body["reports"]]
    assert reports
    for report in reports:
        assert report["value"] is None or CANONICAL_DECIMAL.match(report["value"]), report
        assert report["value"] not in exact_texts
    # The run id travels only as the admit request's local provenance
    # reference, never inside a report text.
    texts = [text for op, body in recording.requests if op == "admit" for text in body["reports"]]
    assert all(new.run_id not in text for text in texts)
    assert "/" not in "".join(r["value"] or "" for r in reports)


class DelayedHost(HostLabExecution):
    """The registered run's reporting with a publication-delay window on its SOC path."""

    def _reporting_for(self, run):
        reporting = super()._reporting_for(run)
        return replace(
            reporting,
            delays=(
                PublicationDelayWindow(
                    event_id="soc-delay",
                    device_id="battery-pcs-controller",
                    signal_id="state-of-charge",
                    start_offset_minutes=120,
                    end_offset_minutes=135,
                ),
            ),
        )


def test_a_registered_run_with_a_delay_window_stages_nothing_and_says_so(drafts, tmp_path) -> None:
    """Q3: S2-01b refuses delayed admission; S2-01c owns it."""
    _, new = drafts
    gateway = gateway_for(tmp_path / "g", new)
    recording = RecordingLink(gateway.link)
    try:
        port = host(tmp_path / "h", recording, DelayedHost)
        port.start(new)
        assert port._sessions[new.run_id].reporting.delays, "the window must be in force"
        assert port.run_to_end(new).status == "COMPLETED"
        view = port.registered_stage(new)
    finally:
        gateway.kill()
    notes = port._sessions[new.run_id].staging_notes
    assert "registered publication refused: publication-delay windows are not supported by the gateway path" in notes
    assert not any(op in {"activate", "admit", "seal"} for op, _ in recording.requests)
    assert view.envelopes == () and view.batches == () and view.holds == ()
    assert not (tmp_path / "h" / "stages" / f"{new.run_id}.json").exists()


def test_the_host_publishes_at_the_frozen_resolution_or_refuses(drafts) -> None:
    from execution_adapter import FrozenRunNotReconstructible, frozen_resolutions

    old, new = drafts
    assert frozen_resolutions(old, LAB_PUBLICATION_PROFILE) == {}
    assert set(frozen_resolutions(new, REGISTERED_KOBO_PUBLICATION_PROFILE).values()) == {MICRO}
    coarser = replace(
        REGISTERED_KOBO_PUBLICATION_PROFILE,
        device_signals=tuple(replace(d, resolution="0.001") for d in REGISTERED_KOBO_PUBLICATION_PROFILE.device_signals),
    )
    with pytest.raises(FrozenRunNotReconstructible, match="resolution it froze"):
        frozen_resolutions(new, coarser)
    unfrozen = replace(new, deterministic_identity=replace(new.deterministic_identity, signal_resolutions=()))
    with pytest.raises(FrozenRunNotReconstructible):
        frozen_resolutions(unfrozen, REGISTERED_KOBO_PUBLICATION_PROFILE)
